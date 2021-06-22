FROM python:3.7.10-buster

ENV VIRTUAL_ENV=/opt/venv/gds
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/genomic-data-service

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
