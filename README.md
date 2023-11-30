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

   * Machine name `bitcoin-devel` and user `bc-devel`; this will have bitcoin source and

   * Machine name `bitcoin-regnet` and user `bc-regnet`; this will be our base image for investigations.

3. Set up the network cards.  

   * For installation and connection to internet for install, both machines need the VM's network settings set-up to NAT addressing.  Enabling port forwarding to guest port 22 to `ssh` into the machines from the host.  Set the host port to
  
   ** VBox 6: Set a SSH to to map from host port 127.0.0.1:2522 to the guest 10.0.2.15:22.  
   
   *** Guest IP can be discovered with command `VBoxManage guestproperty get "bitcoin-regnet" "/VirtualBox/GuestInfo/Net/0/V4/IP" `
  
   ** VBox 7: Set a SSH rule to just map host port 2522 to guest port 22. VBox will then map from the host IP address specified in the 'Host Network Manager' host only network address (default IP address is `192.168.56.1`).

   * For communicating between the two VMs for running scenarios, setup a second adapter using 'Host Only'.  Ensure that a host-only network is configured within VBox.

   ** The default host IP address for this adapter is 192.168.56.1 and 192.168.56.100 is the DHCP server on the Host-only network.  Within each machine, bring up the second adapter interface (check the name of the second interface with `ip addr show`):

   ```sh
   sudo ip addr show
   sudo dhclient enp0s8
   ```

4. Test ubutu is running Openssh `sudo systemctl status ssh` and reboot the server.

5. Test `ssh` works:

   * from the host machine, connecting to the either the local loopback address `127.0.0.1:2522` or the VirtualBox host-only adapter `192.168.56.1:22`.

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
sudo mkdir -p ${BITCOIN_DATA_DIR}
sudo tar -xzvf bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz -C /opt/bitcoin/${BITCOIN_VERSION} --strip-components=1 --exclude=*-qt
sudo ln -s /opt/bitcoin/${BITCOIN_VERSION} /opt/bitcoin/current
sudo rm -rf /tmp/*
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
```

### Create a bitcoin.conf file

By default, the bitcoin daemon will look for the config in `bitcoin.conf` in the data directory and may be changed using the `-datadir` and `-conf` command-line options.  

The data directory, for Linux systems, is `${HOME}/.bitcoin`.

#### Create RPC auth and passwords

Set `BITCOIN_RPC_PASSWORD` and `BITCOIN_RPC_AUTH` to the results of `rcpauth.py`:

```sh
cd /tmp
wget https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py
BITCOIN_RPC_USER=bitcoin
python3 rpcauth.py ${BITCOIN_RPC_USER}
```

The variables should look like:

* `BITCOIN_RPC_AUTH='0dd2730e0a234604e9dfc57e572c12c8$3f4dd55976016630e21eace2a651d008d50c4c47b493f6a15bb28eedc8e67d2c'`

* `BITCOIN_RPC_PASSWORD='00IaRY3jU_AabvucNFvL6MdFkjMZJTbc3V934pZddTc'`

* Set `NODE2_IP=192.168.56.102` or `NODE2_IP=192.168.56.101`

```sh
cat > bitcoin.conf.tmp << EOF
datadir=${BITCOIN_DATA_DIR}
printtoconsole=1
rpcallowip=127.0.0.1
rpcuser=${BITCOIN_RPC_USER:-bitcoin}
rpcpassword=${BITCOIN_RPC_PASSWORD:-$(openssl rand -hex 24)}
rpcauth=${BITCOIN_RPC_USER:-bitcoin}:${BITCOIN_RPC_AUTH:-$(openssl rand -hex 16)'$'$(openssl rand -hex 32)}
`if [ -z "${NODE2_IP}" ]; then echo "# addnode" ; else echo "addnode=${NODE2_IP}:18444" ; fi`
regnet=1
[regtest]
rpcbind=127.0.0.1
rpcport=8332
EOF
```

Move file into place, linking our data directory to the default location:

```sh
sudo mkdir -p /home/bitcoin/.bitcoin
sudo mv bitcoin.conf.tmp /home/bitcoin/.bitcoin/bitcoin.conf
sudo ln -sfn /home/bitcoin/.bitcoin/bitcoin.conf ${BITCOIN_DATA_DIR}/bitcoin.conf
sudo chown -R bitcoin:bitcoin /home/bitcoin
sudo chown -h bitcoin:bitcoin ${BITCOIN_DATA_DIR}/bitcoin.conf
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

Start the bitcoind daemon:

```sh
sudo systemctl start bitcoind
```

### Clear Data and Start Fresh Genisis Block

Just blast the data directory and recreate:

```sh
sudo rm -rf ${BITCOIN_DATA_DIR}
sudo mkdir -p ${BITCOIN_DATA_DIR}
sudo ln -sfn /home/bitcoin/.bitcoin/bitcoin.conf ${BITCOIN_DATA_DIR}/bitcoin.conf
sudo chown -h bitcoin:bitcoin ${BITCOIN_DATA_DIR}/bitcoin.conf
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
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

#### Wireshark

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
sudo adduser $USER wireshark`
```

* If there are file permissions problems, `sudo dpkg-reconfigure wireshark-common` may be needed.

## Transactions

```json
bc-regnet@bitcoin-regnet:/tmp$ bitcoin-cli createwallet "testwallet"
{
  "name": "testwallet"
}

bc-regnet@bitcoin-regnet:/tmp$ bitcoin-cli getnewaddress
bc1q376fg348dzuzeysl2p7qfjyaghm8cgdlwvlt2h
```

### Forensic Setup