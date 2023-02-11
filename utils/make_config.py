import pathlib
import os
import configparser

# 変数初期化
config = configparser.ConfigParser()
node_url =  ''
pem_file = ''
recipient_address = ''

# テストネット/メインネットのモード選択
NETWORK_TYPE = 'testnet'
#NETWORK_TYPE = 'mainnet'

# 共通設定
max_fee = 0.4
amount = 0.00001
pass_phrase = 'password'
msg_txt = 'Send XYM by Bluetooth Button!'

# テストネット向け設定
if NETWORK_TYPE == 'testnet':
    node_url =  'sym-test-04.opening-line.jp'
    pem_file = 'TestnetAccount'
    recipient_address = '***************************************'

# メインネット向け設定
if NETWORK_TYPE == 'mainnet':
    node_url =  'marrons-xym-farm001.com'
    pem_file = 'MainnetAccount'
    recipient_address = '***************************************'

# Symbol wallet config
config['Wallet'] = {
    'node_url': node_url,
    'pem_file': pem_file,
    'pass_phrase' : pass_phrase
    }

config['SendXymParam'] = {
    'recipient_address':recipient_address, 
    'max_fee': max_fee,
    'amount': amount,
    'msg_txt': msg_txt
    }
    
p = pathlib.Path('./config/config.ini')
with open(p.resolve(), 'w') as file:
    config.write(file)