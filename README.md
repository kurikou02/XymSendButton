[README（日本語版）はこちら](https://github.com/kurikou02/XymSendButton/blob/main/README-ja.md)

# XymSendButton
Send XYM with Bluetooth button

## Program Overview
- This is a program to transfer XYM via Bluetooth button
- Uses Raspberry Pi (or Linux device) and Bluetooth button
- Uses Symbol blockchain

## Use Case
- Chip remittance button for engineers and artists
- Record and traceability of activities

## Environment
- Device Raspberry Pi 3+
- OS raspbian 10.12
- [Button ELECOM P-SRBBK](https://www.elecom.co.jp/products/P-SRBBK.html)
    - Like a button for a shutter release on a smartphone
- Lang Python 3.7.3

## SDK
- [symbol-sdk-python 3.0.3](https://pypi.org/project/symbol-sdk-python/)

## Usage

### Step1 Prepare Symbol wallet

#### If you have Symbol wallet
1. Creating a private key file
    1. Enter your private key in `utils/make_pem_file` to generate a private key file

#### If you don't have Symbol wallet
1. Creating a Symbol Wallet

    Create a Symbol wallet by following the instructions here

    https://docs.symbol.dev/ja/wallets.html

    We also recommend using Arcana Wallet if you are a first time user.

    https://note.com/babymoney721/n/n4120d75488f9

### Step2 make config file

Enter the information of the private key file you created, as well as the wallet's network information, connection node information, XYM destination address, and other configuration information in  `utils/make_config_file`.

We recommend using a test network environment first. Please refer to this [node list page](https://symbolnodes.org/nodes_testnet/) for the node to connect to.

### Step3 Connection settings with Bluetooth button

Please set up the connection between your device and the Bluetooth button.
Please confirm the device information of the button to be connected with the following command.

```
bluetoothctl
[bluetooth]#
[bluetooth]# scan on
```

Confirm the MAC address of the button you wish to connect and set up pairing

```
[bluetooth]# pair XX:XX:XX:XX:XX:XX
[bluetooth]# connect XX:XX:XX:XX:XX:XX
[bluetooth]# trust XX:XX:XX:XX:XX:XX
```

Finally, check the Event number of the paired Bluetooth button. The newly increased number after pairing is the Event number of the button you added this time.

```
ls /dev/input
```

Modify a part of the source code according to the Event number of the button.

```
send_xym_button.py

            # ls /dev/input でevent番号要確認
            device = evdev.InputDevice('/dev/input/event0')
            print(device)
```

## Caution
- (There is a possibility that this function may not work properly due to changes in the SDK specifications, etc.)
- Please be careful with the private key file.
- Please modify the source code of the connection part with the Bluetooth button according to your device and environment.