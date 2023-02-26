import pathlib
import os
import configparser

# 変数初期化
config = configparser.ConfigParser()
node_url =  ''
pem_file = ''
recipient_address = ''

# ---------------------------
# 共通設定
# ---------------------------
# 最大手数料 
max_fee = 1
# 送信XYM数量
amount = 1
# 秘密鍵ファイルの復号フレーズ
pass_phrase = 'password'
# 送信メッセージ
msg_txt = 'お世話になってる皆様へ感謝の気持ちです'

# ---------------------------
# # テストネット向け設定
# ---------------------------
def testnet_config():
    node_url =  'sym-test-04.opening-line.jp'
    pem_file = 'TestnetAccount'
    recipient_address = 'TBXFN2GVITXPEQPRLOJXDSZRC7G3XB5P6BSNOOI'
    
    # 設定ファイル作成
    fname = 'config_testnet'
    _make_config_file(node_url, pem_file, recipient_address, fname)

# ---------------------------
# メインネット向け設定
# ---------------------------
def mainnet_config():
    node_url =  'marrons-xym-farm001.com'
    pem_file = 'MainnetAccount'
    recipient_address = 'NCJDPHMEMK562CPYCJVZB3NX3HFYLQTVOYJCYVI'

    # 設定ファイル作成
    fname = 'config_mainnet'
    _make_config_file(node_url, pem_file, recipient_address, fname)

# 設定ファイル出力
def _make_config_file(node_url, pem_file, recipient_address, fname):

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
    
    p = pathlib.Path(f'./config/{fname}.ini')
    with open(p.resolve(), 'w') as file:
        config.write(file)

# 実行
testnet_config()
mainnet_config()
