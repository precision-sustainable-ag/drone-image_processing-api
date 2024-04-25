#!/bin/bash

sudo apt -y install nodejs npm git nginx python3-venv

cd /var/www/
sudo rm -rf /var/www/drone-image_processing
sudo rm -rf /var/www/drone-image-manipulation

git clone https://github.com/precision-sustainable-ag/drone-image-manipulation.git
git clone https://github.com/precision-sustainable-ag/drone-image_processing-api.git

cd /var/www/drone-image-manipulation
sudo npm install
sudo npm build

sudo rm -rf /etc/nginx/sites-enabled/default
sudo rm -rf /etc/nginx/sites-enabled/drone_image_mainpulation.nginx

sudo cp /var/www/drone-image-manipulation/prod.nginx /etc/nginx/sites-enabled/drone_image_manipulation.nginx
sudo ln -s /etc/nginx/sites-available/drone_image_manipulation.nginx /etc/nginx/sites-enabled/drone_image_manipulation.nginx

sudo systemctl reload nginx

cd /var/www/drone-image_processing-api


sudo chown -R azureuser /var/www/

sudo python3 -m venv /var/www/drone-image_processing-api/venv
source /var/www/drone-image_processing-api/venv/bin/activate
/var/www/drone-image_processing-api/venv/bin/python3 -m pip install -r /var/www/drone-image_processing-api/requirements.txt

sudo cp /var/www/drone-image_processing-api/gunicorn.service /etc/systemd/system/drone-image_processing-api.service

sudo systemctl daemon-reload
sudo systemctl start drone-image_processing-api