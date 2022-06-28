# Genomic Data Services

[![CircleCI](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev.svg?style=svg)](https://circleci.com/gh/ENCODE-DCC/genomic-data-service/tree/dev)
[![Coverage Status](https://coveralls.io/repos/github/ENCODE-DCC/genomic-data-service/badge.svg?branch=dev&kill_cache=1)](https://coveralls.io/github/ENCODE-DCC/genomic-data-service?branch=dev)

Flask based web service providing genomic region search, based on regulomedb.org.

Installation Requirements:

To run this application locally you will need to install Docker. To download the machine learning models you need python3.

## Application Installation

### Download machine learning models

This is required for running indexing. Tests can be run without.

In python3 virtual env, install boto3:

```bash
pip install boto3
```

Download machine learning models:

```bash
python utils/download_files
```

### Indexing

Using the compose file suitable for your machine:

```bash
docker-compose --file docker-compose-index-m1/intel.yml build
docker-compose --file docker-compose-index-m1/intel.yml up
```

After indexing has finished (takes about 5 minutes) tear down:

```bash
docker-compose --file dockeri-compose-index-m1/intel.yml down --remove-orphans
```

This command will index ES database, creating a directory `esdata` where it stores the indexes. This is reusable by the app (see instructions for running below).

### Running the app

Using the compose file suitable for your machine:

```bash
docker-compose --file docker-compose-m1/intel.yml build
docker-compose --file docker-compose-m1/intel.yml up
```

The application is available in `localhost:80`.

Tear down:

```bash
docker-compose --file docker-compose-m1/intel.yml down --remove-orphans
```

## Testing

Run tests using compose file suitable for your machine:

```bash
docker-compose --file docker-compose-test-m1/intel.yml --env-file ./docker_compose/test.env up --build
```

Tear down:

```bash
docker-compose --file docker-compose-test-m1/intel.yml down -v --remove-orphans
```

## AWS Deployment

A production grade data services deployment consists of three machines:

* Main machine that runs the flask app that sends the requests to the ES machines.
* Regulome search ES
* ENCODED region-search ES

### Connecting to the instances

The instances have EC2 Instance Connect installed. You need to [install](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-set-up.html) it to connect to the instances. Assume the instance-id of the instance you want to connect to is `i-foobarbaz123`. You would connect this instance with command:

```bash
mssh ubuntu@i-foobarbaz123 --profile regulome --region us-west-2
```

### Demo deployment

1. Make sure you have activated the virtual environment created above. if you need demo deployment for Regulome or Encoded region search, run the command below. This command will launch one machine for both GDS flask app and Elasticsearch server.

    ```bash
    python deploy/deploy.py --demo
    ```

2. Start indexing on the machine. For regulomeDB:

    ```bash
    cd /home/ubuntu/genomic-data-service
    source genomic-venv/bin/activate
    python genomic_data_service/region_indexer.py

3. Or for region search:

    ```bash
    cd /home/ubuntu/genomic-data-service
    source genomic-venv/bin/activate
    python genomic_data_service/region_indexer_encode.py

4. You can monitor the indexing progress using the flower dashboard at \<public IP of the machine/indexer>. For demo purpose, the username and passowrd for indexer is already set in deploy script.

### Production grade deployment

1. The command below will deploy three machines: GDS main machine, Reglulome ES machine and Encoded ES machine:

    ```bash
    python deploy/deploy.py
    ```

2. On each ES machine create a password for accessing the indexer:

    ```bash
    sudo mkdir -p /etc/apache2
    sudo htpasswd -c /etc/apache2/.htpasswd <your-user-name>
    ```

   You will use this login/password to access the flower dashboard on the machines. The dashboard is accessible at \<public IP of the ES machine/indexer>. This is accessible to the internet, so be prudent in choosing the login/password (admin is a bad username, it is quite easy to guess).

3. On the main machine add the IP addresses of the ES machines into `/home/ubuntu/genomic-data-service/config/production.cfg`. Set the value of `REGULOME_ES_HOSTS` to the private IP address of the regulome data service machine, and the value of `REGION_SEARCH_ES_HOSTS` to the private IP address of the region search data service machine (note that in the normal case these values are lists with one item).

4. Restart each service on the main machine:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start genomic
    sudo systemctl start nginx
    ```

5. Start regulome region indexer on the regulome ES machine:

    ```bash
    cd /home/ubuntu/genomic-data-service
    source genomic-venv/bin/activate
    python genomic_data_service/region_indexer.py
    ```

6. Start encoded region indexer on the encoded ES machine:

    ```bash
    cd /home/ubuntu/genomic-data-service
    source genomic-venv/bin/activate
    python genomic_data_service/region_indexer_encode.py
    ```

7. You can monitor the indexing progress using the flower dashboard. After indexing has finished (region-search machine indexes in few hours, regulome machine will take couple of days) the machines can be downsized. Good size for the regulome machine is `t3a.2xlarge` and for the region-search machine `t2.xlarge` is sufficient. Do not forget to restart the services after resize.

8. To deploy a regulome demo that uses your new deployment as backend, you need to edit <https://github.com/ENCODE-DCC/regulome-encoded/blob/dev/ini-templates/production-template.ini> and change the `genomic_data_service_url` to point to the instance running the flask app.

9. To deploy an encoded demo that uses your new deployment as the region-search backend, you need to edit <https://github.com/ENCODE-DCC/encoded/blob/dev/conf/pyramid/demo.ini> and change the `genomic_data_service` to point to the instance running the flask app.
