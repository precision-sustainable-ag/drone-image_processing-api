#!/bin/bash

sudo apt -y install nodejs npm git nginx python3-venv

# clean up
sudo rm -rf /var/www/drone-image_processing-api
sudo rm -rf /var/www/drone-image-manipulation
sudo rm -rf /etc/nginx/sites-enabled/*
sudo rm -rf /etc/nginx/sites-available/*
sudo rm -rf /etc/systemd/system/drone-image_processing-api.service

mkdir -p /var/www/
sudo chown -R $USER /var/www

cd /var/www/
#cd /home/jbshah/
git clone https://github.com/precision-sustainable-ag/drone-image-manipulation.git
git clone https://github.com/precision-sustainable-ag/drone-image_processing-api.git



cd /var/www/drone-image-manipulation
#cd /home/jbshah/drone-image-manipulation
npm install
npm run build

sudo chown -R $USER /var/www/drone-image-manipulation/
sudo chmod -R 755 /var/www/drone-image-manipulation/
#sudo rm -rf /etc/nginx/sites-enabled/default
#sudo rm -rf /etc/nginx/sites-enabled/drone_image_mainpulation.nginx

sudo cp /var/www/drone-image-manipulation/prod.nginx /etc/nginx/sites-available/drone_image_manipulation.nginx
sudo ln -s /etc/nginx/sites-available/drone_image_manipulation.nginx /etc/nginx/sites-enabled/drone_image_manipulation.nginx
#sudo cp /home/jbshah/drone-image-manipulation/prod.nginx /etc/nginx/sites-available/drone_image_manipulation.nginx
#sudo ln -s /etc/nginx/sites-available/drone_image_manipulation.nginx /etc/nginx/sites-enabled/drone_image_manipulation.nginx

cd /var/www/drone-image_processing-api
#cd /home/jbshah/drone-image_processing-api

python3 -m venv /var/www/drone-image_processing-api/venv
source /var/www/drone-image_processing-api/venv/bin/activate
#python3 -m venv /home/jbshah/drone-image_processing-api/venv
#source /home/jbshah/drone-image_processing-api/venv/bin/activate

/var/www/drone-image_processing-api/venv/bin/python3 -m pip install -r /var/www/drone-image_processing-api/requirements.txt

sudo chown -R $USER /var/www/drone-image_processing-api/
sudo chmod -R 755 /var/www/drone-image_processing-api/
#/home/jbshah/drone-image_processing-api/venv/bin/python3 -m pip install -r /home/jbshah/drone-image_processing-api/requirements.txt

sudo cp /var/www/drone-image_processing-api/gunicorn.service /etc/systemd/system/drone-image_processing-api.service
sudo cp /var/www/drone-image_processing-api/file-server.service /etc/systemd/system/drone-flight-server.service
#sudo cp /home/jbshah/drone-image_processing-api/gunicorn.service /etc/systemd/system/drone-image_processing-api.service

sudo setenforce 0
sudo systemctl reload nginx
sudo systemctl daemon-reload
sudo systemctl start drone-image_processing-api