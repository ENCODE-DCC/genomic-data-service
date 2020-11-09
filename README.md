# Genomic Data Service

Flask based web service providing genomic region search, based on regulomedb.org.

Installation Requirements:

* pyenv (https://www.liquidweb.com/kb/how-to-install-pyenv-on-ubuntu-18-04/)
* python 3.7+
* postgres


## Region Indexer Installation

* sudo apt-get update
* git clone https://github.com/ENCODE-DCC/genomic-data-service.git
* sudo apt-get install python3-pip python3-psycopg2 redis-server nginx
* sudo pip3 install -r requirements.txt
* Deploying Flower:
    * ln -s /home/ubuntu/genomic-data-service/deploy/flower.service /etc/systemd/system/flower.service # or your specific systemd path, for ubuntu: /etc/systemd/system and specific deploy path
    * sudo systemctl daemon-reload
    * sudo service flower start
    * You can test by running: curl localhost:5555, it should respond. Otherwise, check sudo service flower status for logs.
    * (OPTIONAL) Nginx config:
        * sudo apt-get install apache2-utils (or httpd-tools for other distributions)
        * sudo mkdir -p /etc/apache2
        * Create a password: sudo htpasswd -c /etc/apache2/.htpasswd admin # replace ‘admin’ by any username
        * sudo cp flower_nginx /etc/nginx/sites-available/
        * ln -s /etc/nginx/sites-available/flower_nginx /etc/nginx/sites-enabled/flower
        * sudo service nginx reload
* Deploying Celery:
    * ln -s /home/ubuntu/genomic-data-service/deploy/celery.service /etc/systemd/system/celery.service # or your specific systemd path, for ubuntu: /etc/systemd/system and specific deploy path
    * sudo systemctl daemon-reload
    * sudo service celery start
    * Check service status and Flower for errors
    * Logs live in ~/log/



