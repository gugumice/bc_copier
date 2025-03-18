#!/bin/bash

systemctl disable bluetooth.service
systemctl disable hciuart.service
apt-get update && apt-get -y upgrade

mkdir /var/log/bc
touch /var/log/bc/bc.log
chown -R pi:kiosk /var/log/kiosk

ln -s /var/log/bc/bc.log /home/pi/bc.log
ln /opt/bc/barcode.service /lib/systemd/system/barcode.service
ln /opt/bc/firstboot.service /lib/systemd/system/firstboot.service
ln /opt/bc/bc.ini /home/pi/bc.ini
ln /opt/bc/label_template.txt /home/pi/label_template.txt

systemctl enable firstboot.service
timedatectl set-timezone Europe/Riga
sed -i '/^# Additional overlays.*/a dtoverlay=pi3-disable-wifi\ndtoverlay=pi3-disable-bt' /boot/config.txt
sed -i '/^\[all\].*/a gpu_mem=16' /boot/config.txt
sleep 3
apt-get --yes install libcups2-dev cups cups-bsd
cupsctl --remote-admin --remote-any
usermod -a -G lpadmin pi
addgroup watchdog
usermod -a -G watchdog pi
service cups restart
apt-get --yes install python3-pip
apt-get --yes install python3-venv
python3 -m venv /opt/bc
source /opt/bc/bin/activate
pip3 --no-input install pyserial
pip3 --no-input install pycups
echo 'KERNEL=="watchdog", MODE="0660", GROUP="watchdog"' > /etc/udev/rules.d/60-watchdog.rules
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf
echo '10.100.20.104   laiks.egl.local' >> /etc/hosts
#/usr/sbin/shutdown -r now