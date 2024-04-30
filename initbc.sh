#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable barcode.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
CURRENT_HOSTNAME=$(cat /proc/sys/kernel/hostname)
if [ -e /sys/class/net/eth0 ]; then
      MAC=$(cat /sys/class/net/eth0/address | tr -d ":")
else
      MAC=$(cat /sys/class/net/wlan0/address | tr -d ":")
fi
NEW_HOSTNAME="rpi-bc1-"${MAC: -5}
echo $CURRENT_HOSTNAME to $NEW_HOSTNAME
sleep 1
hostnamectl set-hostname ${NEW_HOSTNAME} --static
echo $NEW_HOSTNAME > /etc/hostname
sed -i '/^127.0.0.1/s/.*/127.0.0.1\t'${NEW_HOSTNAME}'/g' /etc/hosts
sleep 1
/sbin/shutdown -r now
