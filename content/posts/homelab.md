+++
title = 'Homelab'
date = 2025-01-30T15:18:26+01:00
draft = true
+++
There are some open-source services that I would really like to self-host, that's where
the idea of creating a homelab from my old laptop came from. In the series of posts I 
will try my best to document the process of setting up the homelab, so the process is 
easy to reproduce.

# Hardware
I have an old laptop, a thinkpad T470s that I bought second-hand on olx.
I don't use it anymore but the time has come to bring new life into it.

## Wake On LAN
In order to be able to power on server remotely Wake On LAN (WOL) can be used. First you need to enable WOL in the BIOS (in my case: Config->Network->Wake On LaAN->AC Only, and I also enabled WOL from Dock). Now booting the server if it was shut down is as easy as sending a magic packet as a UDP broadcast with MAC address of the destination server's NIC. There is a helper script in debian repository just install the package and run `wakeonlan [MAC ADDRESS]` from any device in the network to boot the server. I also had to change the setting in Network Boot to NVMe to prevent my server from trying to PXE boot after WOL.

# Main OS
There are multiple options when it comes to choosing the root OS, one of the best options
would be to use **Proxmox**, which delivers a all-in-one solution for virtualization, 
with a nice web interface and a lot of functionalities. However in my case I decided to
go for simplicity, I am going to be using my favourite OS which is **Debian**, most of
my services will be hosted in containers but if I ever need to use a VM I can always use
**QEMU**. Debian is incredibly stable OS (I don't think it ever broke for me) and has
great community.

## Installation
1. Go into debian webpage and download the latest stable version (at the time of writing it
is *Debian 12 - bookworm*).
2. Flash the `.iso` file onto the USB drive: `dd if=path_to.iso of=/dev/sdX`
3. When turning on the destination laptop press `Enter` and select temporary boot 
device to be the USB
4. Install debian according to the instructions in the installer
- I won't perform full disk encryption just to setup Wake on LAN later.
- When selecting software to install I only selected `SSH server`.

## Network setup
We won't be using DHCP as server is something that should have a static IP, let's first
reserve some IP in my home "router" settings, and then run some commands on the server:
```bash
sudo ip link set enp0s... up
sudo ip addr add dev enp0s... [RESERVED_IP]/24
sudo ip route add default via [RESERVED_IP] dev enp0s...
```

## Debloating
I will create an ansible script to debloat the debian installation by removing unnecessary
packages from it. Let's check how many packages are installed on a fresh install:
 ```bash
apt list --installed | wc -l
282
```
I had to install python3 which increased number of packages a little but later after removing
unnecessary packages with my ansible playbook i managed to go down to `257` packages, which
is a nice improvement.

After rebooting I hope to see less services being run, right now I can enter the command:
```bash
systemctl --type=service --state=running
ps -A
```
I can see `7` loaded units which all seem to be important and `98` processes running.



