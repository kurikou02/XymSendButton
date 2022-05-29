#!/usr/bin/env python

import sys
import json
import datetime
import http.client
import argparse
from pathlib import Path
import configparser

from binascii import hexlify
from symbolchain.facade.SymbolFacade import SymbolFacade

from utils.key_manager import KeyManager

class Wallet:
    def __init__(self, network_name, node_url, key_file_name=None, pass_phrase=None):
        print('Initializing Wallet...')
        self._facade = SymbolFacade(network_name)
        self._km = KeyManager(self._facade, '', pass_phrase, key_file_name) 
        self._node_url = node_url       

    def get_my_address(self):
       """
       表示用アドレス
       """
       my_address = self._facade.network.public_key_to_address(self._get_my_pubkey())
       return str(my_address)
    
    def _get_my_pubkey(self):
       return self._km.get_my_pubkey()

    def get_my_pubkey_string(self):
       pubkey = self._km.get_my_pubkey()
       return str(pubkey)

    def save_my_key(self, key_file_name):
       self._km.export_my_key(key_file_name)

    def check_my_account_info_with_pubkey(self):
       req_msg = {
           "publicKeys": [
               self.get_my_pubkey_string()
           ]
       }
       return self._send_accounts_req(req_msg)

    def check_my_account_info_with_address(self):
       req_msg = {
           "addresses": [
               self.get_my_address()
           ]
       }
       return self._send_accounts_req(req_msg)

    def _send_accounts_req(self, req_msg):
        json_req_msg = json.dumps(req_msg)
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection(self._node_url,3000) 
        conn.request("POST", "/accounts", json_req_msg, headers)
        response = conn.getresponse()
        data = response.read()
        return data.decode()
    
    """
    ・typeが'transfer'ではなく'transfer_transaction'に変更
    ・mosaicsの書き方もタプルの配列ではなく、Dic型の配列に変更
    """
    def _build_mosaic_tx(self, deadline, fee, recipient_address, mosaics, msg_txt):

        tx2 = self._facade.transaction_factory.create({
            'type': 'transfer_transaction', 
            'signer_public_key': self._km.get_my_pubkey(),
            'fee': fee,
            'deadline': deadline,
            'recipient_address': recipient_address,
            'mosaics': mosaics,
            'message': bytes(1) + msg_txt.encode('utf8')
        })
        return tx2
        
    def _send_tx(self, json_payload):
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection(self._node_url,3000) 
        conn.request("PUT", "/transactions", json_payload, headers)
        response = conn.getresponse()
        #print(response.status, response.reason)
        return response.status

    """
    ・Signatureの埋め込み方が変更に       
        #signature = facade.sign_transaction(key_pair, aggregate_transaction)
        #tx.signature = signature.bytes
    ・Payloadの生成、jsonダンプも不要に
        #payload = {"payload": hexlify(tx.serialize()).decode('utf8').upper()}
        #json_payload = json.dumps(payload)
    """
    def _build_req_tx_msg(self, tx):
        signature = self._km.compute_signature(tx)
        json_payload = self._facade.transaction_factory.attach_signature(tx, signature)

        #print("*** tx ***")
        #print(tx)
        #print(hexlify(tx.serialize()))
        #print('---- ' * 20)        
        #print(f'Hash: {self._facade.hash_transaction(tx)}')

        return json_payload

    def send_mosaic_transacton(self, deadline, fee, recipient_address, mosaics, msg_txt):
        tx2 = self._build_mosaic_tx(deadline, fee, recipient_address, mosaics, msg_txt)
        json_payload = self._build_req_tx_msg(tx2)
        status = self._send_tx(json_payload)
        return status

    def get_transactions_to_my_address(self, my_address):
        req_path = '/transactions/confirmed?recipientAddress=' + my_address
        conn = http.client.HTTPConnection(self._node_url,3000) 
        conn.request("GET", req_path)
        response = conn.getresponse()
        data = response.read()
        return data.decode()

"""
ウォレットの動作テスト関数
========================================================
ハッシュ値によるトランザクション状態の調べ方
https://sym-test-01.opening-line.jp:3001/transactionStatus/<hash>
https://marrons-xym-farm001.com:3001/transactionStatus/<hash>
"""
def wallet_test(param, pass_phrase, max_fee=0.1, amount=0.1, msg_txt=''):

    # 秘密鍵ファイルからウォレット生成
    wallet = Wallet( param['nw'], param['node_url'], param['pem_file'], pass_phrase )
    print('check account info by address')
    print(wallet.check_my_account_info_with_pubkey())

    # XYM送金テスト(メインネットで1XYM送金) ※モザイクID, deadline計算用のSymbol誕生時刻(UTC)の違いに注意
    deadline = (int((datetime.datetime.today() + datetime.timedelta(hours=2)).timestamp()) - param['birthtime']) * 1000
    fee = int(max_fee * 1000000)
    mosaics =  [{'mosaic_id':param['mosaic_id'],'amount':int(amount * 1000000)}]

    print('my address :' + wallet.get_my_address())
    print('to address :' + param['recipient_address'])
    status = wallet.send_mosaic_transacton(deadline, fee, param['recipient_address'], mosaics, msg_txt)

if __name__ == '__main__':

    _testnet_param = {
        'recipient_address':'TBXFN2GVITXPEQPRLOJXDSZRC7G3XB5P6BSNOOI',
        'nw': 'testnet',
        'node_url': 'sym-test-01.opening-line.jp',
        'pem_file': '../XymDevTest01',
        'birthtime': 1637848847,
        'mosaic_id': 0x3A8416DB2D53B6C8
    }
    _mainnet_param = {
        'recipient_address':'NBCOSHTAB7NKJ6O6EJ2VD45FTRQ3I3TKMQ56A2I',
        'nw': 'mainnet',
        'node_url': 'marrons-xym-farm001-test.com',
        'pem_file': '../SubAccount',
        'birthtime': 1615853185,
        'mosaic_id': 0x6BED913FA20223F8
    }

    _pass_phrase = 'Kurikou0816'
    _max_fee = 0.4
    _amount = 0.1
    _msg_txt = 'test'

    # テストネットのテスト
    #wallet_test(_testnet_param, _pass_phrase, _max_fee, _amount, _msg_txt)

    # メインネットのテスト
    #MainNet()