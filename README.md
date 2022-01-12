[![CircleCI](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev.svg?style=svg)](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev)
[![Coverage Status](https://coveralls.io/repos/github/ENCODE-DCC/genomic-data-service/badge.svg?branch=dev)](https://coveralls.io/github/ENCODE-DCC/genomic-data-service?branch=dev)
# Genomic Data Services

Flask based web service providing genomic region search, based on regulomedb.org.

Installation Requirements:

* python 3.8+
* postgres (only for RNAGet?)
* elasticsearch (5.6 currently)


## Application Installation

1. Create a virtual env in your work directory.
    This example uses the python module venv. Other options would also work, like conda or pyenv
    ```
    $ cd your-work-dir
    $ python3 -m venv genomic-venv
    $ source genomic-venv/bin/activate
    ```

2. Clone the repo and install requirements
    ```
    # Make sure you are in the genomic-venv
    $ cd genomic-data-service
    $ pip3 install -e .
    ```

3. Download our machine learning models
    ```
    $ python3 ./utils/download_ml_models.py
    ```

4. Run the application:
    ```
    $ make run
    ```
    It will be available on port 5000.

5. (Optional) Run the indexer (independent of flask application):
    ```
    $ brew services start redis (if redis not running)

    in separate windows, with virtualenv
    $ python3 ./utils/dev_server/dev_server.py (start local ES)
    $ make worker
    $ make flower
    $ make index
    ```
    Monitoring via flower will be available on port 5555 (localhost unless otherwise set).


## Deployment

In addition to the steps above, and assuming the application is located on: /home/ubuntu/genomic-data-service/:

1. Install the following packages:
    ```
    $ sudo apt-get update
    $ sudo apt-get install python3-psycopg2 redis-server apache2-utils nginx
    ```

2. Create a password for accessing the indexer:
    ```
    $ sudo mkdir -p /etc/apache2
    $ sudo htpasswd -c /etc/apache2/.htpasswd admin   # replace 'admin' by any username
    ```

3. Edit and copy the services for systemctl:
    ```
    $ sudo ln -s /home/ubuntu/genomic-data-service/deploy/flower.service /etc/systemd/system/flower.service
    $ sudo ln -s /home/ubuntu/genomic-data-service/deploy/celery.service /etc/systemd/system/celery.service
    $ sudo ln -s /home/ubuntu/genomic-data-service/deploy/genomic.servie /etc/systemd/system/genomic.service
    $ sudo systemctl daemon-reload
    ```

4. Start each service and verify they are running correctly:
    ```
    $ sudo service celery start
    $ sudo service flower start
    $ sudo service genomic start
    ```

5. Apply the nginx configuration. We provide a working example in our `deploy` folder. If your instance will contain a single installation of the Genomic Data Service, you can just simply use it as:
    ```
    $ sudo cp /home/ubuntu/genomic-data-service/deploy/nginx /etc/nginx/sites-available/default
    $ sudo service nginx restart
    ```

