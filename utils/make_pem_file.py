"""
秘密鍵ファイルの生成
XYM送金に使用するアカウントの秘密鍵とパスフレーズを入力してください
"""

from utils import genarate_private_key_file

NETWORK_TYPE = 'testnet'
#NETWORK_TYPE = 'mainnet'

# テストネット用設定
if NETWORK_TYPE == 'testnet':
    pk = '****************************************************************'
    pass_phrase = '**********'
    filepath = './TestnetAcount'
    genarate_private_key_file(filepath, pk, pass_phrase)
    

# メインネット用設定
if NETWORK_TYPE == 'mainnet':
    pk = '****************************************************************'
    pass_phrase = '**********'
    filepath = './MainnetAccount'
    genarate_private_key_file(filepath, pk, pass_phrase)
