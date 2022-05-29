#!/usr/bin/env python

import pathlib
import os
import evdev
import time

import datetime
import urllib.request
import json
import configparser

from binascii import hexlify
from symbolchain.facade.SymbolFacade import SymbolFacade

from utils.symbol_wallet import Wallet

# 送金量リミット
AMOUNT_LIMIT = 50

# Blutoothボタンが押されたら繰り返しXYMを投げる
def run():

    # 設定ファイル読み込み
    config = configparser.ConfigParser()
    config.read('./config/config.ini')
    wallet_config = config['Wallet']
    send_config = config['SendXymParam']

    # ネットワークに応じたパラメータセット
    mosaic_id, birthtime = None, None
    if wallet_config.get('network_name') == 'testnet':
        # テストネットの場合
        mosaic_id = 0x3A8416DB2D53B6C8
        birthtime =  1637848847
    elif  wallet_config.get('network_name') == 'mainnet':
        # メインネットの場合
        mosaic_id = 0x6BED913FA20223F8
        birthtime =  1615853185
    else:
        print('ERROR:Incorrect network configuration.( "testnet" or "mainnet" )')
        return

    # Symbolウォレット生成
    wallet = Wallet(  wallet_config.get('network_name'), wallet_config.get('node_url'), wallet_config.get('pem_file'),  wallet_config.get('pass_phrase') )

    # 送金設定
    fee = int(float(send_config.get('max_fee')) * 1000000)    
    amount = float(send_config.get('amount'))
    # 送金量セーフティチェック
    if amount > AMOUNT_LIMIT:
        print('ERROR:Amount is Over the limit. limit is ' + str(AMOUNT_LIMIT) + ' XYM.')
        return      
    mosaics =  [{'mosaic_id':mosaic_id,'amount':int(amount * 1000000)}]

    # Blutoothボタンの入力待ち受け開始
    print('******** Start waiting for input ******** ')
    while True:
        try:
            # ls /dev/input でevent番号要確認
            device = evdev.InputDevice('/dev/input/event0')
            print(device)

            for event in device.read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    if event.value == 1: # 0:KEYUP, 1:KEYDOWN
                        print(event.code) # KEY_ENTER->28

                        if event.code == evdev.ecodes.KEY_ENTER:
                            # XYM送金
                            print('Send XYM')
                            deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - birthtime) * 1000
                            status = wallet.send_mosaic_transacton(deadline, fee, send_config.get('recipient_address'), mosaics, send_config.get('msg_txt'))
                            print(status)
                            time.sleep(5)
        except:
            print('Retry...')
            time.sleep(1)

if __name__ == '__main__':
    
    # BlutoothボタンでXYM送金
    run()
    