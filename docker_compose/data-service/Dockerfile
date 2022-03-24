FROM python:3.8.12-buster

ENV PYTHONBUFFERED 1

ENV VIRTUAL_ENV=/opt/venv

RUN apt-get update && apt-get install -y curl

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --upgrade pip

WORKDIR /opt/genomic_data_service

COPY . /opt/genomic_data_service

RUN pip install -e .[test]

RUN adduser -u 5678 --disabled-password --gecos "" gdsuser && chown -R gdsuser /opt/genomic_data_service

EXPOSE 5000
