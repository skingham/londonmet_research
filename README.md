# LondonMet Blockchain Forensics Research Project

## Blockchain Regtest Environment setup

Inital Bitcoin Blockchain setup details were cadged from: 

* [Bitcoin devtool's README.md](https://github.com/bitcoin/bitcoin/blob/master/contrib/devtools/README.md);

* [Ruan Bekker's Ultimate Guide to Bitcoin Testnet Fullnode Setup](https://ruanbekker.hashnode.dev/ultimate-guide-to-bitcoin-testnet-fullnode-setup-in-linux); and

* [System Glitch's Tutorial for bitcoin regtest](https://gist.github.com/System-Glitch/cb4e87bf1ae3fec9925725bb3ebe223a).

### Virtual Box VM Setup

We will use two VMs to create a bitcoin development environment and a Regtest environment.

1. Download [Ubuntu Server 22.04.3 LTS](https://releases.ubuntu.com/22.04.3/ubuntu-22.04.3-live-server-amd64.iso?_ga=2.140164016.2039168415.1698079272-97665322.1698079272).

2. Create VM images, using `Ubuntu Server (minimised)`, installing OpenSSH on both using:

   * Machine name `bitcoin-regnet` and user `bc-regnet` as our our base image for investigations.

   * Machine name `bitcoin-devel` and user `bc-devel` as or this will have bitcoin source and

3. Set up the network cards.  

   * For installation and connection to internet for install, both machines need the VM's network settings set-up to NAT addressing.  Enabling port forwarding to guest port 22 to `ssh` into the machines from the host.  Set the host port to

      * VBox 6: Set a SSH to to map from host port 127.0.0.1:2522 to the guest 10.0.2.15:22.  

         * Guest IP can be discovered with command `VBoxManage guestproperty get "bitcoin-regnet" "/VirtualBox/GuestInfo/Net/0/V4/IP"`
  
      * VBox 7: Set a SSH rule to just map host port 2522 to guest port 22. VBox will then map from the host IP address specified in the 'Host Network Manager' host only network address (default IP address is `192.168.56.1`).

   * For communicating between the two VMs for running scenarios, setup a second adapter using 'Host Only'.  Ensure that a host-only network is configured within VBox.

      * The default host IP address for this adapter is 192.168.56.1 and 192.168.56.100 is the DHCP server on the Host-only network.  Within each machine, bring up the second adapter interface (check the name of the second interface with `ip addr show`):

   ```sh
   sudo ip addr show
   sudo dhclient enp0s8
   ```

   ```sh
   cat > 00-installer-config.yaml.tmp << EOF
   network:
     version: 2
     ethernets:
       enp0s3:
         dhcp4: true
       enp0s8:
         dhcp4: true
   EOF
   sudo mv  00-installer-config.yaml.tmp /etc/netplan/00-installer-config.yaml
   sudo chmod 644 /etc/netplan/00-installer-config.yaml
   sudo chown root:root /etc/netplan/00-installer-config.yaml
   ```

4. Test Ubuntu is running Openssh `sudo systemctl status ssh` and reboot the server.

5. Test `ssh` works:

   * From the host machine, connecting to the either the local loopback address `127.0.0.1:2522` or the VirtualBox host-only adapter `192.168.56.1:22`.

   ```sh
   ssh -p 2522 -l bc-regnet 192.168.56.1
   ```

   * From bc-devel guest to first VM other:

   ```sh
   ssh -p 2622 -l bc-devel 192.168.56.1
   ssh -p 22 -l bc-regnet 192.168.56.101
   ```

### Install Bitcoin Core

```sh
export ARCH=x86_64
export BITCOIN_VERSION=25.1
export BITCOIN_URL=https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz
export BITCOIN_DATA_DIR=/blockchain/bitcoin/data
```

```sh
sudo groupadd -r bitcoin
sudo useradd -r -m -g bitcoin -s /bin/bash bitcoin
```

```sh
sudo apt update 
sudo apt install ca-certificates gnupg gpg wget jq --no-install-recommends -y
```

Download bitcoin-core and verify that the package matches the sha hash:

```sh
cd /tmp
wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS
wget -qO bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz "${BITCOIN_URL}"
cat SHA256SUMS | grep bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz
sha256sum bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz
```

```sh
sudo mkdir -p /opt/bitcoin/${BITCOIN_VERSION}
sudo tar -xzvf bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz -C /opt/bitcoin/${BITCOIN_VERSION} --strip-components=1 --exclude=*-qt
sudo ln -s /opt/bitcoin/${BITCOIN_VERSION} /opt/bitcoin/current
sudo mkdir -p ${BITCOIN_DATA_DIR}
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
sudo rm -rf /tmp/*
```

### Create a bitcoin.conf file

By default, the bitcoin daemon will look for the config in `bitcoin.conf` in the data directory and may be changed using the `-datadir` and `-conf` command-line options.  

The default data directory, for Linux systems, is `${HOME}/.bitcoin`.  We will set the data directory location in the config file, and set the config file to be in `${HOME}/.bitcoin/bitcoin.conf` and the data directory to be the above `${BITCOIN_DATA_DIR}`.

#### Default Ports for Bitcoin Environments

We are setting up a _regtest_ environment and will set ports expicitly to the defaults below:

| Var/Environment    | Live       | testnet     | signet      | regtest     |
|--------------------|------------|-------------|-------------|-------------|
| Listen on: bind=   | 8334=onion | 18334=onion | 38334=onion | 18445=onion |
| Connection: port=  | 8333       | 18333       | 38333       | 18444       |
| JSON-RPC: rpcport= | 8332       | 18332       | 38332       | 18443       |

#### Additional Nodes

The second machine needs to know the address of the first.  Set 'NODE2_IP' when creating the config on the second VM.

```sh
NODE2_IP=192.168.56.10x
```

#### Create RPC auth and passwords

Set `BITCOIN_RPC_PASSWORD` and `BITCOIN_RPC_AUTH` to the results of `rcpauth.py`:

```sh
cd /tmp
wget https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py
$(python3 rpcauth.py bitcoin \
 | awk -F= '\
      /String/ {} \
      /rpcauth/ { split($2,vals,":") ; printf "export %s=%s export %s=%s ", "BITCOIN_RPC_USER", vals[1], "BITCOIN_RPC_AUTH", vals[2] } \
      /Your/ {} \
      ENDFILE { printf "export %s=%s ", "BITCOIN_RPC_PASSWORD", $0 }')
```

The variables should look like:

* `BITCOIN_RPC_USER=bitcoin`

* `BITCOIN_RPC_AUTH='0dd2730e0a234604e9dfc57e572c12c8$3f4dd55976016630e21eace2a651d008d50c4c47b493f6a15bb28eedc8e67d2c'`

* `BITCOIN_RPC_PASSWORD='00IaRY3jU_AabvucNFvL6MdFkjMZJTbc3V934pZddTc'`

To set the three environments variables from a previously generated config file:

```sh
unset BITCOIN_RPC_USER BITCOIN_RPC_AUTH BITCOIN_RPC_PASSWORD
$(sudo cat /home/bitcoin/.bitcoin/bitcoin.conf \
 | awk -F= '\
      /rpcauth/ { split($2,vals,":") ; printf "export %s=%s export %s=%s ", "BITCOIN_RPC_USER", vals[1], "BITCOIN_RPC_AUTH", vals[2] } \
      /rpcpassword/ { printf "export %s=%s ", "BITCOIN_RPC_PASSWORD", $2 } \
      /addnode/ { split($2,vals,":") ; printf "export %s=%s ", "NODE2_IP", vals[1] }')
```

#### Generate a new config file

* __`regtest`__ must be set to 1

* __`fallbackfee`__

* To allow remote devices to connection, set __`rpcallowip`__`=192.168.56.0/24` __`rpcbind`__`=0.0.0.0`.  More secure is `rpcallowip=192.168.56.rmt` `rpcbind=192.168.56.btc`, or `rcpallowip=127.0.0.1` & `rpcbind=127.0.0.1` if no connection from external devices is needed.


```sh
cat > bitcoin.conf.tmp << EOF
datadir=${BITCOIN_DATA_DIR}
fallbackfee=0.00001
printtoconsole=1
# rpcuser=${BITCOIN_RPC_USER:-bitcoin}
# rpcpassword=${BITCOIN_RPC_PASSWORD:-$(openssl rand -hex 24)}
rpcauth=${BITCOIN_RPC_USER:-bitcoin}:${BITCOIN_RPC_AUTH:-$(openssl rand -hex 16)'$'$(openssl rand -hex 32)}
regtest=1
[regtest]
rpcallowip=192.168.56.0/24
rpcbind=0.0.0.0
rpcport=18443
$(if [ -z "${NODE2_IP}" ]; then echo "# addnode" ; else echo "addnode=${NODE2_IP}:18444" ; fi)
EOF
```

Move file into place, linking our data directory to the default location:

```sh
sudo sudo mkdir -p /home/bitcoin/.bitcoin
sudo mv /tmp/bitcoin.conf.tmp /home/bitcoin/.bitcoin/bitcoin.conf
sudo chmod 644 /home/bitcoin/.bitcoin/bitcoin.conf
sudo chown bitcoin:bitcoin /home/bitcoin/.bitcoin/bitcoin.conf
sudo chmod 744 /home/bitcoin/.bitcoin
sudo chown -R bitcoin:bitcoin /home/bitcoin/.bitcoin
```

Link into the data directory:

```sh
sudo ln -sfn /home/bitcoin/.bitcoin/bitcoin.conf ${BITCOIN_DATA_DIR}/bitcoin.conf
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
```

#### Create the systemd unit-file for bitcoind

```sh
cat > bitcoind.service << EOF
[Unit]
Description=Bitcoin Core Regnet
After=network.target
[Service]
User=bitcoin
Group=bitcoin
WorkingDirectory=${BITCOIN_DATA_DIR}
Type=simple
ExecStart=/opt/bitcoin/current/bin/bitcoind -conf=${BITCOIN_DATA_DIR}/bitcoin.conf
[Install]
WantedBy=multi-user.target
EOF
```

Move the systemd unit files into place:

```sh
sudo mv bitcoind.service /etc/systemd/system/bitcoind.service
sudo systemctl daemon-reload
sudo systemctl enable bitcoind
sudo systemctl status bitcoind
```

Update profile of `bitcoin` user to have the bitcoin core bin in their path.

```sh
sudo su - bitcoin
echo '[[ -d /opt/bitcoin/current/bin && ":$PATH:" != *":/opt/bitcoin/current/bin:"* ]] && PATH=/opt/bitcoin/current/bin:$PATH' >> ${HOME}/.profile
exit
```

### Clear Data and Start Fresh Genisis Block

Just blast the data directory and recreate:

```sh
sudo systemctl stop bitcoind
sudo rm -rf ${BITCOIN_DATA_DIR}
sudo mkdir -p ${BITCOIN_DATA_DIR}
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
sudo ln -sfn /home/bitcoin/.bitcoin/bitcoin.conf ${BITCOIN_DATA_DIR}/bitcoin.conf
sudo chown -h bitcoin:bitcoin ${BITCOIN_DATA_DIR}/bitcoin.conf
```

### Install Bitcoin Core & Developer

On a separate development machine, we need to create a configuration file and password.

An initial config file can be generated using `gen-bitcoin-conf.sh` using bitcoin devtools on a different machine, or copied taken from the install.

```sh
cd ${HOME}
sudo apt install build-essential iputils-ping git
git clone https://github.com/bitcoin/bitcoin.git
git checkout --track origin/25.x
cd bitcoin/contrib/devtools
gen-bitcoin-conf.sh
```

### Start Nodes and Test

### Start Daemon

```sh
sudo systemctl start bitcoind
```

#### Check nodes are connected

Check if your nodes are connected.  From the second machine: 

```sh
$ sudo su - bitcoin
$ bitcoin-cli getaddednodeinfo
[
  {
    "addednode": "192.168.56.10x:18444",
    "connected": true,
    "addresses": [
      {
        "address": "192.168.56.10x:18444",
        "connected": "outbound"
      }
    ]
  }
]
```

## Forensic Setup

### Wireshark

On each Ubuntu VM:

* Add the stable official PPA and install wireshark:

```sh
sudo add-apt-repository ppa:wireshark-dev/stable
sudo apt-get update
sudo apt-get install wireshark
```

* Run wireshark and answer 'yes' to the allowing non-root users to capture packers: 

```sh
sudo wireshark
```

* Add the user to the wireshark group:

```sh
sudo adduser $USER wireshark
```

* If there are file permissions problems, `sudo dpkg-reconfigure wireshark-common` may be needed.

## Operations on the Blockchain

To check that the network is synchronised, from node 2, create a wallet, address and transaction.  
Then check both nodes have the same block count

### Create a wallet on node 2

```sh
$ bitcoin-cli createwallet "regtestwallet"
{
  "name": "regtestwallet"
}
```

### Create an address for new transactions:

```sh
$ REGTEST_ADDRESS=$(bitcoin-cli getnewaddress)
$ echo $REGTEST_ADDRESS
bc1q376fg348dzuzeysl2p7qfjyaghm8cgdlwvlt2h
```

### Generate a new block

```sh
$ bitcoin-cli generatetoaddress 1 $REGTEST_ADDRESS
[
   "3d8c67420921deaaaf561e3b5f5d12e9f1e6ff4f7683a451ea66e1b24a5cffdb"
]
```

### Check the block count on both nodes:

```sh
$ bitcoin-cli getblockcount
1
```

```sh
$ curl --user bitcoin --data-binary '{"jsonrpc": "1.0", "id": "0", "method": "getblockcount", "params": []}' -H 'content-type: text/plain;' localhost:18443/
Enter host password for user 'bitcoin':
{"result":1,"error":null,"id":"0"}
```

### Generate Blocks

```sh
#!/bin/bash

# Script to generate a new block every minute
# Put this script at the root of your unpacked folder
echo "Generating a block every minute. Press [CTRL+C] to stop.."

address=$(/opt/bitcoin/current/bin/bitcoin-cli getnewaddress)

while :
do
    echo "Generate a new block `date '+%d/%m/%Y %H:%M:%S'`"
    /opt/bitcoin/current/bin/bitcoin-cli generatetoaddress 1 $address
    sleep 60
done
```

### Adding nodes manually

```sh
bitcoin-cli addnode 192.168.58.101:18444
```

Let's mine some blocks and check if everything is synchronized:

```sh
bitcoin-cli generatetoaddress 25 "<your_address>"
bitcoin-cli getblockcount # Should return 75
bitcoin-cli -rpcport=18443 getblockcount # Should return 75 
```

### Transfer funds

We got some funds from mining the first blocks. We will transfer them to our wallet on the second node.

```sh
address=$(bitcoin-cli -rpcport=18443 getnewaddress)
bitcoin-cli sendtoaddress "$1" 10
```

### Check the funds have been received

```sh
bitcoin-cli -rpcport=18443 getwalletinfo
```

### Double spend

As we only have two nodes in the network, it's easy to make a 51% attack. We're going to double spend some bitcoin.

#### Get a unspent output with a non-zero output

```sh
bitcoin-cli listunspent
```

#### Create a raw transaction and sign it

__Don't forget to set the amount of your vout a little bit lower than the amount of your utxo so your tx has fees__

```sh
transaction=$(bitcoin-cli createrawtransaction '[{"txid":"<TX_ID>","vout":0}]' '{"$address":12.49}')
bitcoin-cli signrawtransactionwithwallet "$transaction"
```

Keep the generated hex of the signed transaction. We need to disconnect both nodes and broadcast the transaction from the other node.

#### Disconnect nodes

```sh
bitcoin-cli disconnectnode "127.0.0.1:18444"
bitcoin-cli -rpcport=18443 disconnectnode "127.0.0.1:18444"
```

#### Broadcast from other node

```sh
bitcoin-cli -rpcport=18443 sendrawtransaction "<HEX>"
```

To make a double spend, we need to create another transaction with the same utxo and broadcast it on the chain where the first one wasn't broadcasted.

#### Generate a second address to make it easier to differenciate both transactions

```sh
address=`bitcoin-cli -rpcport=18443 getnewaddress`
```

```sh
transaction=`bitcoin-cli createrawtransaction '[{"txid":"<TX_ID>","vout":0}]' '{"$address":12.49}'`
bitcoin-cli signrawtransactionwithwallet "$transaction"
bitcoin-cli sendrawtransaction "<HEX>"
```

We need to mine some blocks so when we join the two nodes, the longest chain is kept. (In our case, the one with the second transaction).

```sh
bitcoin-cli generate 50
```

#### Join

```sh
bitcoin-cli addnode "127.0.0.1:18444" add
```

Check that the first transaction doesn't exist anymore:

```sh
bitcoin-cli -rpcport=18443 listtransactions
```

The last one should have the address we used for the second transaction. The double-spend worked!