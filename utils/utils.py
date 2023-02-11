from binascii import unhexlify
from pathlib import Path
import requests
import json
import re

from symbolchain.CryptoTypes import PrivateKey
from symbolchain.PrivateKeyStorage import PrivateKeyStorage
from symbolchain.symbol.KeyPair import KeyPair

def read_contents(filepath) -> str:
	with open(filepath, 'rt', encoding='utf8') as infile:
		return infile.read()


def read_private_key(filepath, password=None) -> KeyPair:
	if not isinstance(filepath, Path):
		filepath = Path(filepath)

	if filepath.suffix == '.txt':
		return KeyPair(PrivateKey(unhexlify(read_contents(filepath).strip())))

	storage = PrivateKeyStorage(filepath.parent, password)
	return KeyPair(storage.load(filepath.stem))

# 秘密鍵ファイルの生成
def genarate_private_key_file(filepath, private_key='', pass_phrase=''):
	if len(private_key) != 64:
		print('The number of digits in the private key is incorrect.')
		return

	if not isinstance(filepath, Path):
		filepath = Path(filepath)
	
	b = unhexlify( private_key )	
	prikey = PrivateKey(b)
	_p_storage = PrivateKeyStorage(filepath.parent, pass_phrase)
	_p_storage.save(filepath.stem, prikey )

# ノードからプロパティを取得
def get_node_properties( node ):
    """
    network type, epock ajustment, currency mosaic id, generation hashを取得する
    """
    node_url = "https://" + node + ":3001"
    node_url_properties = node_url + "/network/properties"
    response = requests.get(node_url_properties)
    if response.status_code != 200:
        raise Exception("status code is {}".format(response.status_code))
    contents = json.loads(response.text)
    network = str(contents["network"]["identifier"].replace("'", ""))
    epoch_adjustment = int(contents["network"]["epochAdjustment"].replace("s", ""))
    currency_mosaic_id = int(contents["chain"]["currencyMosaicId"].replace("'", ""), 16)
    generation_hash_seed = str(contents["network"]["generationHashSeed"].replace("'", ""))
    return network, epoch_adjustment,currency_mosaic_id, generation_hash_seed, node_url 


# Symbolアドレスバリデーションチェック
def is_valid_symbol_address(address):
	symbol_address_regex = re.compile('^([N|T][A-Za-z0-9]{38})$')
	return True if symbol_address_regex.match(address) else False