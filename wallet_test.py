#!/usr/bin/env python

import pathlib
import os
import evdev
import time

import datetime
import http.client
import requests
import json
import configparser

from binascii import hexlify
from symbolchain.facade.SymbolFacade import SymbolFacade

from utils.symbol_wallet import Wallet
from utils.utils import get_node_properties

# 送金量リミット
AMOUNT_LIMIT = 1

"""
ウォレットの動作テスト関数
========================================================
ハッシュ値によるトランザクション状態の調べ方
https://sym-test-01.opening-line.jp:3001/transactionStatus/<hash>
https://marrons-xym-farm001.com:3001/transactionStatus/<hash>
"""
def wallet_test():

    # 設定ファイル読み込み
    config = configparser.ConfigParser()
    config.read('./config/config.ini')
    wallet_config = config['Wallet']
    send_config = config['SendXymParam']

    # ノードからプロパティ情報取得
    node_properties = get_node_properties( wallet_config.get('node_url') )
    NETWORK_TYPE = node_properties[0]
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
    mosaics =  [{'mosaic_id':MOSAICID,'amount':int(amount * 1000000)}]

    # 送信先アドレス
    recipient_address = send_config.get('recipient_address')

    # 送金量セーフティチェック
    if amount > AMOUNT_LIMIT:
        print('ERROR:Amount is Over the limit. limit is ' + str(AMOUNT_LIMIT) + ' XYM.')
        return      

    # 残高チェック
    for mosaic_info in mosaic_infos:
        if mosaic_info['id'] == MOSAICID :
            if amount > mosaic_info['amount']:
                print('ERROR:Insufficient balance.')
                print('Remittance amount is ' + str(amount))
                print('Your account`s XYM amount is ' + str( mosaic_info['amount']))
                print('Check your Account and Selected Network Type')

    # XYM送金
    print('my address :' + wallet.get_my_address())
    print('to address :' + recipient_address)
    deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - EPOCH_ADJUSTMENT) * 1000
    status = wallet.send_mosaic_transacton(deadline, fee, recipient_address, mosaics, send_config.get('msg_txt'))
    print('status:' + str(status) )

if __name__ == '__main__':

    # テスト送金
    wallet_test()