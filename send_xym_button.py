#!/usr/bin/env python

import sys
import pathlib
import os
import evdev
import time
import numpy as np
import base64
import binascii

import datetime
import http.client
import requests
import json
import configparser

from binascii import hexlify
from symbolchain.facade.SymbolFacade import SymbolFacade

from utils.symbol_wallet import Wallet
from utils.utils import get_node_properties
from utils.utils import is_valid_symbol_address
from utils.utils import read_addresslist
from utils.utils import aliasToRecipient

class SendXymButton():
    # 初期化
    def __init__(self, network_type='', is_aggregate=False, amount_limit=100):
        # 設定ファイル読み込み
        config = configparser.ConfigParser()
        config.read('./config/config.ini')
        self._wallet_config = config['Wallet']
        self._send_config = config['SendXymParam']
        # パラメータセット       
        self._network_type = network_type
        self._is_aggregate = is_aggregate
        self._amount_limit = amount_limit
        # ウォレット生成
        self._epoch_adjustment = ''
        self._xym_mosaic_id = ''
        self._wallet = self._make_wallet()

    # Symbolウォレット生成
    def _make_wallet(self):

        # ノードからプロパティ情報取得
        node_properties = get_node_properties( self._wallet_config.get('node_url') )
        NETWORK_TYPE = node_properties[0]
        NETWORK_TYPE_INT = 104 if NETWORK_TYPE == 'mainnet' else 152
        EPOCH_ADJUSTMENT = node_properties[1]
        MOSAICID = node_properties[2]
        GENERATOIN_HASH = node_properties[3]
        NODE_URL = node_properties[4]

        # プロパティ確認用
        """
        print("Network type => " + str(NETWORK_TYPE))
        print("Epoch ajustment => " + str(EPOCH_ADJUSTMENT))
        print("Mosaic ID => " + str(hex(MOSAICID)).upper())
        print("Generation hash => " + str(GENERATOIN_HASH))
        print("Using node url => " + str(NODE_URL))
        """

        # 送信用パラメータの保持
        self._xym_mosaic_id = MOSAICID
        self._epoch_adjustment = EPOCH_ADJUSTMENT

        # ウォレット生成
        return Wallet(  NETWORK_TYPE, self._wallet_config.get('node_url'), self._wallet_config.get('pem_file'),  self._wallet_config.get('pass_phrase') )

    # CSVからアドレス一覧を生成 
    def _make_address_book(self):
        address_book = []
        page = 0
        total_count = 0
        fname = 'addresses_' + str(self._network_type) + '.csv'
        print('******** Load and validate address lists ********')
        with open('addresses/'+fname) as f:
            try:
                address_list = []
                count = 0
                for line in f: 
                    recipient = line.replace('\n', '')
                    # 送信先としての有効性チェック
                    address = self._check_recipient(recipient)
                    if address == '':
                        continue
                    # 有効な宛先ならアドレス帳に追加
                    address_list.append(address)
                    count+=1
                    # 100件超えたらページ切り替え(アグボンの上限）
                    if count > 99:
                        total_count += count
                        count = 0
                        address_book.append(address_list)
                        address_list = []
                total_count += count
                address_book.append(address_list)
            except FileNotFoundError as err:  
                print(err)  # errの中身を表示
        return (address_book, total_count)

    # 対象アドレスの受信制限有無確認
    def _is_restrictions_address(self, address):
        restrictions_info = json.loads(self._wallet.check_restrictions_info_with_address(address))
        restrictions_str = str(restrictions_info)
        if 'ResourceNotFound' in restrictions_str:
            return False
        if "accountRestrictions" in restrictions_str:
            print(f'{address}:受信制限あり')
        else:
            print(f'{address}:その他エラー')
        return True

    # 対象アドレスは有効か？
    def _is_target_address_valid(self, address):
        account_info = json.loads(self._wallet.check_account_info_with_address(address))
        if len(account_info) == 0:
            print(f'Err {address}:無効なアドレス')
            return False
        return True

    # 送信先アカウントの有効性チェック
    def _check_recipient(self, recipient):

        # 宛先のフォーマットがアドレスの場合
        if is_valid_symbol_address(recipient) == True:
            # アドレス情報の取得成否
            if self._is_target_address_valid(recipient) == False:
                return ''
            # 受け取り制限の有無確認
            if self._is_restrictions_address(recipient) == False:
                # 受信制限無しの場合はアドレスを返して終了
                return recipient
            else:
                return ''

        # 宛先のフォーマットがアドレス以外の場合：ネームスペースとして扱う
        # ネームスペース情報の取得
        namespaceId = hex(self._wallet.get_namespaceid(recipient))[2:]
        namespace_info = json.loads(self._wallet.check_namespace_info(namespaceId))        
        # ネームスペース情報該当無しなら終了
        if 'ResourceNotFound' in str(namespace_info):
            print(f'Err {recipient}:無効なアドレスまたはネームスペース')
            return ''
        elif 'InvalidArgument' in str(namespace_info):
            print(f'Err {recipient}:不正なフォーマット')
            return ''
        
        # 宛先として使えるかのチェック
        if namespace_info['meta']['active'] == False:
            print(f'Err {recipient}:無効なネームスペース')
            return ''

        alias = namespace_info['namespace']['alias']
        if alias['type'] == 2:
            # アドレス形式を変換(Hex to base32)
            raw_address = alias['address']
            address = base64.b32encode(binascii.unhexlify(raw_address)).decode('utf-8')[:-1]
            # 受信制限チェック
            if self._is_restrictions_address(address) == False:
                return address
            else:
                return ''

    # Blutoothボタンが押されたら繰り返しXYMを投げる
    def run( self, recipient_address='' ):

        # 送信元アカウント情報取得
        account_info = json.loads(self._wallet.check_my_account_info_with_pubkey())
        mosaic_infos = account_info[0]['account']['mosaics']

        # 送金設定
        fee = int(float(self._send_config.get('max_fee')) * 1000000)    
        amount = float(self._send_config.get('amount'))
        total_amount = amount
        mosaics =  [{'mosaic_id':self._xym_mosaic_id,'amount':int(amount * 1000000)}]

        # アグリゲートトランザクションの場合 -> アドレスリスト取得
        address_book = []
        if self._is_aggregate == True:
            # アドレス一覧の読み込み
            (address_book, total_count) = self._make_address_book()
            if total_count == 0:
                print('Failed to load address list')
                return
            # 合計送金料の再計算
            total_amount = amount * total_count
        else:
            # 単発送信の場合 -> 宛先チェック
            if recipient_address == '':
                recipient_address = self._send_config.get('recipient_address')
            res = self._check_recipient(recipient_address)
            if res == '':
                print(f'{res} is an invalid recipirnt')
                return
            recipient_address = res

        # 送金量セーフティチェック
        if total_amount > self._amount_limit:
            print('ERROR:Amount is Over the limit. limit is ' + str(self._amount_limit) + ' XYM.')
            return      

        # 残高チェック
        for mosaic_info in mosaic_infos:
            if mosaic_info['id'] == self._xym_mosaic_id:
                if total_amount > mosaic_info['amount']:
                    print('ERROR:Insufficient balance.')
                    print('Remittance amount is ' + str(total_amount))
                    print('Your account`s XYM amount is ' + str( mosaic_info['amount']))
                    print('Check your Account and Selected Network Type')

        # Blutoothボタンの入力待ち受け開始
        print('******** Start waiting for input ******** ')
        while True:
            try:
                # ls /dev/input でevent番号要確認
                device = evdev.InputDevice('/dev/input/event0')
                print('device = ' + str(device))

                for event in device.read_loop():
                    if event.type == evdev.ecodes.EV_KEY:
                        if event.value == 1: # 0:KEYUP, 1:KEYDOWN
                            print('event code = ' + str(event.code)) # KEY_ENTER->28

                            if event.code == evdev.ecodes.KEY_ENTER:

                                # XYM送金(アグリゲートトランザクション)
                                if is_aggregate == True:
                                    print('Send Aggregate Transaction!')
                                    print('my address :' + self._wallet.get_my_address())
                                    page = 0
                                    for addresses in address_book:
                                        print('Address Book page ' + str(page) )
                                        print(addresses)
                                        # アグリゲートトランザクション送信
                                        deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - self._epoch_adjustment) * 1000
                                        status = self._wallet.send_mosaic_aggregate_transacton(deadline, fee, addresses, mosaics, self._send_config.get('msg_txt'))
                                        print('status = ' + str(status) )
                                        page += 1
                                        time.sleep(3)
                                    # アグリゲートトランザクションの場合はワンポチで終了
                                    print('Finish')
                                    return
                                else:
                                    # XYM送金(単発)
                                    deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - self._epoch_adjustment) * 1000
                                    status = self._wallet.send_mosaic_transacton(deadline, fee, recipient_address, mosaics, self._send_config.get('msg_txt'))
                                    print('Send ' + str(amount) +'XYM to [' + str(recipient_address) + '] status = ' + str(status) )
                                
                                print('waiting for input... (Ctr + Z to exit)')
                                time.sleep(3)
            except:
                print('Exception! Retry....')
                time.sleep(1)

    # ネームスペース名からNamespaceIdのバイト列を生成
    def _namespace_to_idbytes(namespace):
        # namespaceをバイト配列に変換
        print(hex(wallet.get_namespaceid(namespace)))
        byte_array = self._wallet.get_namespaceid(namespace).to_bytes(8, 'big')
        narray = np.frombuffer(byte_array, dtype=np.uint8)
        # namespaceIdの形に変換(24byte)
        namespaceid = aliasToRecipient(narray, NETWORK_TYPE_INT)
        return namespaceid.tobytes()
        
if __name__ == '__main__':

    network_type = 'testnet'
    is_aggregate = False

    # コマンドライン引数受け取り
    args = sys.argv
    if len(args)>1:
        is_aggregate = (args[1] == '--aggregate') 
        print('isAggregate = ' + str(is_aggregate))
    
    # BlutoothボタンでXYM送金
    button = SendXymButton(network_type, is_aggregate)
    button.run()
    