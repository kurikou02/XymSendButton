import pathlib
import os
import configparser

config = configparser.ConfigParser()

config['Wallet'] = {
    'network_name': 'testnet',
    'node_url': 'sym-test-01.opening-line.jp',
    'pem_file': 'XymDevTest01',
    'pass_phrase' : 'Kurikou0816'
}

"""
メインネットの場合
    'network_name': 'mainnet',
    'node_url': 'marrons-xym-farm001-test.com',
"""

config['SendXymParam'] = {
    'recipient_address':'TBXFN2GVITXPEQPRLOJXDSZRC7G3XB5P6BSNOOI',
    'max_fee': 0.4,
    'amount': 0.1,
    'msg_txt': 'Send XYM by Bluetooth Button'
}

p = pathlib.Path('./config/config.ini')
with open(p.resolve(), 'w') as file:
    config.write(file)
