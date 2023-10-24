# londonmet_research
LondonMet Blockchain Forensics Research Project

## Blockchain Regtest Environment setup

Inital Bitcoin Blockchain setup details were cadged from: [Bitcoin devtool's README.md](https://github.com/bitcoin/bitcoin/blob/master/contrib/devtools/README.md); [Ruan Bekker's Ultimate Guide to Bitcoin Testnet Fullnode Setup](https://medium.com/coinmonks/ultimate-guide-to-bitcoin-testnet-fullnode-setup-b83da1bb22e); and [System Glitch's Tutorial for bitcoin regtest](https://gist.github.com/System-Glitch/cb4e87bf1ae3fec9925725bb3ebe223a).

### Virtual Box VM Setup

1. Download [Ubuntu Server 22.04.3 LTS](https://releases.ubuntu.com/22.04.3/ubuntu-22.04.3-live-server-amd64.iso?_ga=2.140164016.2039168415.1698079272-97665322.1698079272).
2. Create VM image using machine name `bitcoin-regnet` and user `rc-regnet`, selecting the option to install OpenSSH.
3. In the VM's network settings, enable port forwarding for port 22 (both host and guest ports.)
4. Test ubutu is running Openssh `sudo systemctl status ssh` and reboot the server.
5. Test `ssh` works from the host machine, connecting to the default Virtual Box host-only adapter, 192.168.56.1:
   ```sh
   ssh -l bc-regnet 192.168.56.1
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
wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS.asc
wget -qO bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz "${BITCOIN_URL}"
cat SHA256SUMS.asc | grep bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz | awk ‘{ print $1 }’
```

```
sudo mkdir -p /opt/bitcoin/${BITCOIN_VERSION}
sudo mkdir -p ${BITCOIN_DATA_DIR}
sudo tar -xzvf bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz -C /opt/bitcoin/${BITCOIN_VERSION} — strip-components=1 — exclude=*-qt
sudo ln -s /opt/bitcoin/${BITCOIN_VERSION} /opt/bitcoin/current
sudo rm -rf /tmp/*
sudo chown -R bitcoin:bitcoin ${BITCOIN_DATA_DIR}
```

### Regnet configuration

Create initial config
```
gen-bitcoin-conf.sh
```

