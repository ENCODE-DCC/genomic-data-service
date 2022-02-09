FROM  cimg/python@sha256:5280078dacde9c6093da25c5544d224483e89ac17b19404b8c348d00b7289bdf

RUN sudo apt-get update && sudo apt-get install -y \
    openjdk-11-jdk \
    libcurl4-openssl-dev \
    python3-dev \
    python3-pip

RUN sudo mkdir /software
WORKDIR /software

RUN sudo wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.16.deb && \
    sudo wget http://archive.ubuntu.com/ubuntu/pool/main/f/file/libmagic-dev_5.38-4_amd64.deb && \
    sudo wget http://archive.ubuntu.com/ubuntu/pool/main/f/file/libmagic1_5.38-4_amd64.deb && \
    sudo wget http://archive.ubuntu.com/ubuntu/pool/main/f/file/libmagic-mgc_5.38-4_amd64.deb && \
    sudo dpkg -i elasticsearch-5.6.16.deb && \
    sudo dpkg -i libmagic-mgc_5.38-4_amd64.deb && \
    sudo dpkg -i libmagic1_5.38-4_amd64.deb && \
    sudo dpkg -i libmagic-dev_5.38-4_amd64.deb && \
    sudo apt-get install -f && \
    sudo chown -R circleci /etc/elasticsearch

ENV PATH="/usr/share/elasticsearch/bin:${PATH}"
ENV ES_JAVA_OPTS="-Xms2g -Xmx3g"

RUN sudo wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/pg_gpg_key
RUN sudo apt-key add /etc/apt/pg_gpg_key
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" | sudo tee -a /etc/apt/sources.list
RUN sudo apt-get update && sudo apt-get install -y postgresql-11

