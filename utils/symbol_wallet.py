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
        return response.status

    def _build_req_tx_msg(self, tx):
        signature = self._km.compute_signature(tx)
        json_payload = self._facade.transaction_factory.attach_signature(tx, signature)
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