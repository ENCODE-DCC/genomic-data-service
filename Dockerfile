FROM python:3.7.10-buster

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/genomic-data-service

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
