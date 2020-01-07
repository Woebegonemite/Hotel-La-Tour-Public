#!/usr/bin/env bash

apt update
apt upgrade -y

apt install zsh
sh -c "$(curl -fsSl https://raw.github.com/robbyrussel/oh-my-zsh/master/tools/install.sh)"

sudo apt-get install -y -q build-essential git unzip zip nload tree
sudo apt-get install -y -q python3-pip python3-dev python3-venv
sudo apt-get install -y -q nginx
sudo apt-get install --no-install-recommends -y -q libqcre3-dev libz-dev
sudo apt install fail2ban -y

ufw allow 22
ufw allow 80
ufw allow 443
ufw enable

git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=720000'

git config --global user.email 'lewis.stuart11@yahoo.co.uk'
git config --global user.name 'woebegonemite'

mkdir /apps
chmod 777 /apps
mkdir /apps/logs
mkdir /apps/logs/hotel-la-tour
mkdir /apps/logs/hotel-la-tour/app_log
cd /apps

cd /apps
python3 -m venv venv
source /apps/venv/bin/activate
pip install --upgrade pip setuptools
pip install --upgrade httpie glances
pip install --upgrade uwsgi

cd /apps
git clone https://github.com/Woebegonemite/Hotel-La-Tour-Public app_repo

cd /apps/app_repo
pip install -r requirements.txt

cp /apps/app_repo/server/HotelServ.service /etc/systemd/system/HotelServ.service

systemctl start LDogServ
systemctl status LDogServ
systemctl enable LDogServ

apt install nginx

rm /etc/nginx/sites-enabled/default

cp /apps/app_repo/server/HotelServ.nginx /etc/systemd/system/HotelServ.nginx
update-rc.d nginx enable
service nginx restart
