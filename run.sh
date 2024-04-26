#!/bin/bash

sudo apt -y install nodejs npm git nginx python3-venv

# clean up
sudo rm -rf /var/www/drone-image_processing-api
sudo rm -rf /var/www/drone-image-manipulation
sudo rm -rf /etc/nginx/sites-enabled/*
sudo rm -rf /etc/nginx/sites-available/*
sudo rm -rf /etc/systemd/system/drone-image_processing-api.service

sudo chown -R $USER /var/www

cd /var/www/
git clone https://github.com/precision-sustainable-ag/drone-image-manipulation.git
git clone https://github.com/precision-sustainable-ag/drone-image_processing-api.git

cd /var/www/drone-image-manipulation
npm install
npm run build

#sudo rm -rf /etc/nginx/sites-enabled/default
#sudo rm -rf /etc/nginx/sites-enabled/drone_image_mainpulation.nginx

sudo cp /var/www/drone-image-manipulation/prod.nginx /etc/nginx/sites-available/drone_image_manipulation.nginx
sudo ln -s /etc/nginx/sites-available/drone_image_manipulation.nginx /etc/nginx/sites-enabled/drone_image_manipulation.nginx

sudo systemctl reload nginx

cd /var/www/drone-image_processing-api

python3 -m venv /var/www/drone-image_processing-api/venv
source /var/www/drone-image_processing-api/venv/bin/activate
/var/www/drone-image_processing-api/venv/bin/python3 -m pip install -r /var/www/drone-image_processing-api/requirements.txt

sudo cp /var/www/drone-image_processing-api/gunicorn.service /etc/systemd/system/drone-image_processing-api.service

sudo systemctl daemon-reload
sudo systemctl start drone-image_processing-api