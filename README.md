# Genomic Data Services

Flask based web service providing genomic region search, based on regulomedb.org.

Installation Requirements:

* python 3.7+
* postgres


## Region Indexer Installation

* sudo apt-get install python3-pip python3-psycopg2 redis-server nginx apache2-utils
* sudo pip3 install -r requirements.txt

* Deploying Flower:
    * ln -s genomic-data-service/deploy/flower.service /etc/systemd/system/flower.service # or your specific systemd path, for ubuntu: /etc/systemd/system and specific deploy path
    * sudo systemctl daemon-reload
    * sudo service flower start
    * Flower server should be running on port 5555. Check via `curl localhost:5555`.
    * (OPTIONAL) Nginx config:
        * sudo mkdir -p /etc/apache2
        * sudo htpasswd -c /etc/apache2/.htpasswd admin # replace ‘admin’ by any username
        * sudo cp genomic-data-service/deploy/flower_nginx /etc/nginx/sites-available/
        * ln -s /etc/nginx/sites-available/flower_nginx /etc/nginx/sites-enabled/flower
        * sudo service nginx reload
* Deploying Celery:
    * ln -s /home/ubuntu/genomic-data-service/deploy/celery.service /etc/systemd/system/celery.service # or your specific systemd path, for ubuntu: /etc/systemd/system and specific deploy path
    * sudo systemctl daemon-reload
    * sudo service celery start
    * Check worker health via Flower (localhost:5555)


