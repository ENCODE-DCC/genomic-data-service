[![CircleCI](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev.svg?style=svg)](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev)
[![Coverage Status](https://coveralls.io/repos/github/ENCODE-DCC/genomic-data-service/badge.svg?branch=dev)](https://coveralls.io/github/ENCODE-DCC/genomic-data-service?branch=dev)
# Genomic Data Services

Flask based web service providing genomic region search, based on regulomedb.org.

Installation Requirements:

* python 3.8 (locally 3.9 and 3.10 work as well)
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

## Testing

1. Install test requirment:
    ```
    $ pip install -e '.[test]'
    ```

2. Run tests:
    ```
    $ make unit_test
    $ make integration_test
    ```

## AWS Deployment

A production grade data services deployment consists of three machines:
* Main machine that runs the flask app that sends the requests to the ES machines.
* Regulome search ES
* ENCODED region-search ES

1. Deploy the machines. Make sure you have activated the virtual environment created above.:
    ```
    $ python deploy/deploy.py -b <branch> -n <data-service-name>  --profile-name regulome --instance-type r5.2xlarge --volume-size 500
    $ python deploy/deploy.py -b <branch> -n <data-service-regulome-ES-name> --profile-name regulome --instance-type r5.2xlarge --volume-size 500
    $ python deploy/deploy.py -b <branch> -n <test-data-service-encoded-ES-name> --profile-name regulome --instance-type r5.2xlarge --volume-size 500
    ```

2. On each machine create a password for accessing the indexer:
    ```
    $ sudo mkdir -p /etc/apache2
    $ sudo htpasswd -c /etc/apache2/.htpasswd <your-user-name>
    ```

   You will use this login/password to access the flower dashboard on the machines. The dashboard is accessible in `http://<public-IP>/indexer`. This is accessible to the internet, so be prudent in choosing the login/password (admin is a bad username, it is quite easy to guess).

3. On the main machine add the IP addresses of the ES machines into `/home/ubuntu/genomic-data-service/config/production.cfg`. Set the value of `REGULOME_ES_HOSTS` to the private IP address of the regulome data service machine, and the value of `REGION_SEARCH_ES_HOSTS` to the private IP address of the region search data service machine (note that in the normal case these values are lists with one item).

4. Create a security group allowing the main application the access to ES hosts on port 9201. This security group consists of one inbound rule with IP version `IPv4`, Type `Custom TCP`, Protocol `TCP`, Port Rance `9201` with the source <private IP of the main machine>/32. Both regulome and region-search machines need to be in this security group.

5. Start each service and verify they are running correctly:
    On the main machine:
    ```
    $ sudo systemctl daemon-reload
    $ sudo service celery start
    $ sudo service flower start
    $ sudo service genomic start
    $ chmod 777 /home/ubuntu/genomic-data-service/genomic.sock
    $ sudo service nginx restart
    ```

    On the ES machines:
    ```
    $ sudo systemctl daemon-reload
    $ sudo service elasticsearch start
    $ sudo service celery start
    $ sudo service flower start
    $ sudo service nginx restart
    ```

6. Start regulome region indexer on the regulome ES machine:
    ```
    $ cd /home/ubuntu/genomic-data-service
    $ source genomic-venv/bin/activate
    $ python genomic_data_service/region_indexer.py
    ```

7. Start encoded region indexer on the encoded ES machine:
    ```
    $ cd /home/ubuntu/genomic-data-service
    $ source genomic-venv/bin/activate
    $ python genomic_data_service/region_indexer_encode.py
    ```

You can monitor the indexing progress using the flower dashboard. After indexing has finished (region-search machine indexes in few hours, regulome machine will take couple of days) the machines can be downsized. Good size for the regulome machine is `t3a.2xlarge` and for the region-search machine `t2.xlarge` is sufficient. Do not forget to restart the services after resize.

8. To deploy a regulome demo that uses your new deployment as backend, you need to edit https://github.com/ENCODE-DCC/regulome-encoded/blob/dev/ini-templates/production-template.ini and change the `genomic_data_service_url` to point to the instance running the flask app.

9. To deploy an encoded demo that uses your new deployment as the region-search backend, you need to edit https://github.com/ENCODE-DCC/encoded/blob/dev/conf/pyramid/demo.ini and change the `genomic_data_service` to point to the instance running the flask app.
