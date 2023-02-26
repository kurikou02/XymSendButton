"""
秘密鍵ファイルの生成
XYM送金に使用するアカウントの秘密鍵とパスフレーズを入力してください
"""

from utils import genarate_private_key_file

# ---------------------------
# # テストネット向け設定
# ---------------------------
def testnet_pem():
    pk = '****************************************************************'
    pass_phrase = '**********'
    filepath = './TestnetAccount'
    genarate_private_key_file(filepath, pk, pass_phrase)
    

# ---------------------------
# メインネット向け設定
# ---------------------------
def mainnet_pem():
    pk = '****************************************************************'
    pass_phrase = '**********'
    filepath = './MainnetAccount'
    genarate_private_key_file(filepath, pk, pass_phrase)


testnet_pem()
mainnet_pem()