#!/usr/bin/env python

import base64
import pathlib
import os
import evdev
import time
import csv
import numpy as np

import datetime
import http.client
import requests
import json
import configparser

from binascii import hexlify

from utils.symbol_wallet import Wallet
from utils.utils import get_node_properties
from utils.utils import is_valid_symbol_address
from utils.utils import read_addresslist
from utils.utils import aliasToRecipient

# 送金量リミット
AMOUNT_LIMIT = 1

"""
ウォレットの動作テスト関数
========================================================
ハッシュ値によるトランザクション状態の調べ方
https://sym-test-01.opening-line.jp:3001/transactionStatus/<hash>
https://marrons-xym-farm001.com:3001/transactionStatus/<hash>
"""
def wallet_test(recipient_address='', is_aggregate=False):

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

    # ウォレット生成
    wallet = Wallet(  NETWORK_TYPE, wallet_config.get('node_url'), wallet_config.get('pem_file'),  wallet_config.get('pass_phrase') )
    print('check account info by address')
    account_info = json.loads(wallet.check_my_account_info_with_pubkey())
    print(account_info)
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
        print(address_book)
        print(total_amount)
    else:
        # それ以外の場合は単発送信
        if recipient_address == '':
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

    # 送金時間セット
    deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - EPOCH_ADJUSTMENT) * 1000

    # XYM送金(アグリゲートトランザクション)
    if is_aggregate == True:
        print('Send Aggregate Transaction')
        print('my address :' + wallet.get_my_address())
        page = 0
        for addresses in address_book:
            print('Address Book page ' + str(page) )
            print(addresses)
            # ネームスペースが混じってたらアドレスに変換
            for i, x in enumerate(addresses):
                if is_valid_symbol_address(addresses[i]) == True:
                    continue
                # namespaceをバイト配列に変換
                byte_array = wallet.get_namespaceid(addresses[i]).to_bytes(8, 'big')
                narray = np.frombuffer(byte_array, dtype=np.uint8)
                # namespaceIdの形に変換(24byte)
                namespaceid = aliasToRecipient(narray, NETWORK_TYPE_INT)
                addresses[i] = namespaceid.tobytes()
            status = wallet.send_mosaic_aggregate_transacton(deadline, fee, addresses, mosaics, send_config.get('msg_txt'))
            print('status:' + str(status) )
            page+=1
        return

    # XYM送金（単発）
    print('my address :' + wallet.get_my_address())
    print('to address :' + str(recipient_address))
    status = wallet.send_mosaic_transacton(deadline, fee, recipient_address, mosaics, send_config.get('msg_txt'))
    print('status:' + str(status) )

if __name__ == '__main__':

    # テスト送金(単発)
    #wallet_test('kuri_dev_test')

    # テスト送金(単発)
    #wallet_test('TBXFN2GVITXPEQPRLOJXDSZRC7G3XB5P6BSNOOI')

    # テスト送金（アグリゲート）
    #wallet_test('',True)