#!/usr/bin/env python

import sys
import pathlib
import os
import evdev
import time
import numpy as np

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

# 送金量リミット
AMOUNT_LIMIT = 1

# Blutoothボタンが押されたら繰り返しXYMを投げる
def run(is_aggregate=False):

    # 設定ファイル読み込み
    config = configparser.ConfigParser()
    config.read('./config/config.ini')
    wallet_config = config['Wallet']
    send_config = config['SendXymParam']

    # ノードからプロパティ情報取得
    node_properties = get_node_properties( wallet_config.get('node_url') )
    NETWORK_TYPE = node_properties[0]
    NETWORK_TYPE_INT = 104 if NETWORK_TYPE == 'mainnet' else 152
    EPOCH_ADJUSTMENT = node_properties[1]
    MOSAICID = node_properties[2]
    GENERATOIN_HASH = node_properties[3]
    NODE_URL = node_properties[4]

    # プロパティ確認用
    print("Network type => " + str(NETWORK_TYPE))
    print("Epoch ajustment => " + str(EPOCH_ADJUSTMENT))
    print("Mosaic ID => " + str(hex(MOSAICID)).upper())
    print("Generation hash => " + str(GENERATOIN_HASH))
    print("Using node url => " + str(NODE_URL))

    # Symbolウォレット生成
    wallet = Wallet(  NETWORK_TYPE, wallet_config.get('node_url'), wallet_config.get('pem_file'),  wallet_config.get('pass_phrase') )
    # 所有モザイク情報の取得
    account_info = json.loads(wallet.check_my_account_info_with_pubkey())
    mosaic_infos = account_info[0]['account']['mosaics']

    # 送金設定
    fee = int(float(send_config.get('max_fee')) * 1000000)    
    amount = float(send_config.get('amount'))
    total_amount = amount
    mosaics =  [{'mosaic_id':MOSAICID,'amount':int(amount * 1000000)}]

    # アグリゲートトランザクションの場合はアドレスリスト取得
    address_book = []
    if is_aggregate == True:
        (address_book, total_count) = read_addresslist(NETWORK_TYPE)
        # 合計送金料の再計算
        total_amount = amount * total_count
        print('total count = ' + str(total_count))
        print('total amount = ' + str(total_amount))
    else:
        # それ以外の場合は単発の送信先セット
        recipient_address = send_config.get('recipient_address')
        # ネームスペースの場合はアドレスに変換
        if is_valid_symbol_address(recipient_address) == False:
            namespace = recipient_address
            # namespaceをバイト配列に変換
            byte_array = wallet.get_namespaceid(namespace).to_bytes(8, 'big')
            narray = np.frombuffer(byte_array, dtype=np.uint8)
            # namespaceIdの形に変換(24byte)
            namespaceid = aliasToRecipient(narray, NETWORK_TYPE_INT)
            recipient_address = namespaceid.tobytes()


    # 送金量セーフティチェック
    if total_amount > AMOUNT_LIMIT:
        print('ERROR:Amount is Over the limit. limit is ' + str(AMOUNT_LIMIT) + ' XYM.')
        return      

    # 残高チェック
    for mosaic_info in mosaic_infos:
        if mosaic_info['id'] == MOSAICID :
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
                                print('my address :' + wallet.get_my_address())
                                page = 0
                                for address_list in address_book:
                                    print('Address Book page ' + str(page) )
                                    # ネームスペースが混じっていたらアドレスに変換
                                    for i, x in enumerate(address_list):
                                        if is_valid_symbol_address(address_list[i]) == True:
                                            continue
                                        # namespaceをバイト配列に変換
                                        byte_array = wallet.get_namespaceid(address_list[i]).to_bytes(8, 'big')
                                        narray = np.frombuffer(byte_array, dtype=np.uint8)
                                        # namespaceIdの形に変換(24byte)
                                        namespaceid = aliasToRecipient(narray, NETWORK_TYPE_INT)
                                        address_list[i] = namespaceid.tobytes()
                                    # アグリゲートトランザクション送信
                                    deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - EPOCH_ADJUSTMENT) * 1000
                                    status = wallet.send_mosaic_aggregate_transacton(deadline, fee, address_list, mosaics, send_config.get('msg_txt'))
                                    print('Send ' + str(total_amount) + 'XYM status = ' + str(status) )
                                    page += 1
                                    time.sleep(3)
                                # アグリゲートトランザクションの場合はワンポチで終了
                                print('Finish')
                                return
                            else:
                                # XYM送金(単発)
                                deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - EPOCH_ADJUSTMENT) * 1000
                                status = wallet.send_mosaic_transacton(deadline, fee, recipient_address, mosaics, send_config.get('msg_txt'))
                                print('Send ' + str(amount) +'XYM to [' + str(recipient_address) + '] status = ' + str(status) )
                            
                            print('waiting for input... (Ctr + Z to exit)')
                            time.sleep(3)
        except:
            print('Exception! Retry....')
            time.sleep(1)

if __name__ == '__main__':

    is_aggregate = False

    # コマンドライン引数受け取り
    args = sys.argv
    if len(args)>1:
        is_aggregate = (args[1] == '--aggregate') 
        print('isAggregate = ' + str(is_aggregate))
    
    # BlutoothボタンでXYM送金
    run( is_aggregate )
    