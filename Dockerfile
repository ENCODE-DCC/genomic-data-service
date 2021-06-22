FROM python:3.7.10-buster

ENV PYTHONUNBUFFERED 1

ENV VIRTUAL_ENV=/opt/venv/gds

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/genomic-data-service

COPY requirements.txt .

RUN pip install -r requirements.txt
