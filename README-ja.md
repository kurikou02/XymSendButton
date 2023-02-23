# XymSendButton
SymbolブロックチェーンのネイティブトークンであるXYMを、Buluetoothボタンで送金するプログラムです。

## プログラムの概要
- デバイスには、Raspberry Pi (または、BLE接続可能なLinuxマシン) と、Bluetoothボタンを使用します。
    - Bluetoothボタンは100均などの安価なもので大丈夫です
- Symbolブロックチェーンを使用します
    - テストネットを使う場合は、暗号資産の購入等は不要です。無料で試す事ができます。

## ユースケース
- 推しのエンジニアやアーテイストへの投げXYMボタンとして
- 作業記録やブロックチェーンを活用したトレサビのPoCとして

## 開発環境やデバイス仕様
- Device Raspberry Pi 3+
- OS raspbian 10.12
- [Button ELECOM P-SRBBK](https://www.elecom.co.jp/products/P-SRBBK.html)
- Lang Python 3.7.3

## SDK
- [symbol-sdk-python 3.0.3](https://pypi.org/project/symbol-sdk-python/)

## 本プログラムの使い方

### Step1 Symbolのウォレットをすでに持っている場合
1. プライベートキーファイルを生成します
    1. `utils/make_pem_file` に、今回使用するsymbolウォレットの秘密鍵と復号化パスを入力し、実行してください。暗号化された秘密鍵ファイルが生成されます。

### Step1 Symbolウォレットを持っていない場合
1. まずは以下のいずれかの方法で、Symbolブロックチェーンのウォレットを生成しましょう。
    
    Symbolデスクトップウォレットを利用した手順はこちら

    https://docs.symbol.dev/ja/wallets.html

    コミュニティ有志が開発した「Arcana」ウォレットは初心者に特にオススメの方法です。

    https://note.com/babymoney721/n/n4120d75488f9

### Step2 送信設定ファイルの生成

`utils/make_config_file` ファイルに、接続するノードのURLや、送信先アドレス情報などを入力して実行してください。
設定ファイルが自動で生成されます。

使用するネットワーク（メインネット or テストネット）については、接続先ノードから自動で判定します。
テストネットで送信したい場合はテストネットのノードを、メインネットで送信したい場合はメインネットのノードを指定してください。

接続先ノードについては、以下のノード一覧から適当なノードを選択してください。

※テストネットのノードを選ぶ際には、ハッシュシードが下記の値になっているノードを選択してください。
（XYM testnet ＝　49D6E1CE276A85B70EAFE52349AACCA389302E7A9754BCF1221E79494FC665A4）

 [node list （テストネット）](https://symbolnodes.org/nodes_testnet/) 
 [node list （メインネット）](https://symbolnodes.org/nodes/) 
 

### Step3 Bluetooth ボタンの接続設定（ラズパイ）

事前に、プログラムを実行するマシンとBluetoothボタンのペアリングを行ってください。
例）ラズパイの場合の、Bluetoothボタンの接続手順

```
bluetoothctl
[bluetooth]#
[bluetooth]# scan on
```

使用するBluetoothボタンのMACアドレスを確認して、ペアリングの設定を行ってください。

```
[bluetooth]# pair XX:XX:XX:XX:XX:XX
[bluetooth]# connect XX:XX:XX:XX:XX:XX
[bluetooth]# trust XX:XX:XX:XX:XX:XX
```

最後に、ペアリングしたBluetoothボタンのEvent Numberを確認します。Blueoothボタンを新たにペアリングすると、下記フォルダに新しいフォルダが追加されるので、そのフォルダの名前を確認してください。

```
ls /dev/input
```

フォルダ名を確認したら、下記プログラムファイルの中に、対象のBluetoothボタンのEvent Numberを追記してください。


```
send_xym_button.py

            # ls /dev/input でevent番号要確認
            device = evdev.InputDevice('/dev/input/event0')
            print(device)
```

## テストネットで送金が上手くいかない場合
- SDKに書かれているネットワークアドレスやジェネレーションハッシュの情報が古い可能性があります。下記手順で修正してください。

STEP1 symbol-sdk-pythonのインストールパスを下記コマンドで調べる

```

pip3 show symbol-sdk-python
Name: symbol-sdk-python
Version: 3.0.3
Summary: Symbol SDK
Home-page: https://github.com/symbol/symbol/tree/main/sdk/python
Author: Symbol Contributors
Author-email: contributors@symbol.dev
License: UNKNOWN
Location: /usr/local/lib/python3.7/dist-packages
Requires: cryptography, mnemonic, Pillow, pysha3, PyYAML, pyzbar, qrcode
Required-by: 

```

STEP2 `symbolchain/symbol/Network.py` に書かれているテストネットのジェネレーションハッシュ値を修正する

```

Network.TESTNET = Network('testnet', 0x98, Hash256('49D6E1CE276A85B70EAFE52349AACCA389302E7A9754BCF1221E79494FC665A4'))

```

## CSVファイルによる複数アドレス一括送金

### 使い方

`/addresse` フォルダにある2つのCSVファイルに、送りたいアドレスを1行ずつ入力してください。それぞれテストネットとメインネットに対応しています。

`send_xym_button.py`を実行する際に、`--aggregate` オプションを指定すると一括送金モードで実行されます。

一括送金する場合は、手数料の設定にご注意ください。接続先ノードに設定に対して、指定の手数料が安すぎると上手く送金されません。また、送金量の指定ミス等にも十分ご注意ください。送金量とメッセージを宛先ごとに変更する機能は対応していません（今後追加するかもです）


## Caution
- 秘密鍵の取り扱いには十分ご注意ください。メインネット環境で使う場合は、テスト用のアドレスに少量のXYMを移して使うことをオススメします。
- Bluetoothボタンとの接続部分のソースコードは、お使いの端末や環境に応じて変更してください。