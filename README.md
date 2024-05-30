# drone-image_processing-api
This is the codebase for the backend of drone image processing tool (app 2)

## Tech stack
- API: Flask
- Database: mongodb

### Prod setup
- Clone the repo
- Execute `./run.sh`
> `run.sh` will create and configure both the frontend (https://github.com/precision-sustainable-ag/drone-image-manipulation) and the backend 

### Dev/Test setup
- Create a python 3.9 virtual env
- Install the required libaries using requirements.txt (`pip install -r requirements.txt`)
- Change `config.py` to match your local database credentials and flight data storage path
- Get dev data from Jinam
    - Copy flight data to your local flight data storage location
    - Import the corresponding database entries to your database collection
