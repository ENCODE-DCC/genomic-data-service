FROM python:3.8.12-buster

ENV PYTHONBUFFERED 1

ENV VIRTUAL_ENV=/opt/venv

RUN apt-get update && apt-get install -y curl 

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements-docker.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR /opt/genomic_data_service

COPY . .

EXPOSE 5000

CMD ["sleep", "600"]

