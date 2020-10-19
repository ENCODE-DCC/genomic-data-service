export APP_NAME := genomic_data_service

build:
	python3 -m venv venv
	source venv/bin/activate
	pip install -e .
	deactivate & source venv/bin/activate
	python3 ./utils/download_ml_models.py

run:
	FLASK_APP=$(APP_NAME) FLASK_ENV=development GENOMIC_DATA_SERVICE_SETTINGS=../config/development.cfg flask run -p 5000

clean:
	rm -rf genomic_data_service.egg-info/

test:
	FLASK_APP=$(APP_NAME) FLASK_ENV=test GENOMIC_DATA_SERVICE_SETTINGS=../config/test.cfg pytest

prod:
	GENOMIC_DATA_SERVICE_SETTINGS=../config/development.cfg gunicorn -w 4 -b 127.0.0.1:4000 wsgi:app
