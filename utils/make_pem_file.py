"""
秘密鍵ファイルの生成
"""

from utils import genarate_private_key_file

# プライベートキー
pk = '***'
# パスフレーズ
pass_phrase = '***'
# 保存先パス
filepath = './***'

# 秘密鍵ファイルの生成
genarate_private_key_file(filepath, pk, pass_phrase)