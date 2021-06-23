export APP_NAME := genomic_data_service

build:
	python3 -m venv venv
	source venv/bin/activate
	pip3 install -e .
	deactivate & source venv/bin/activate
	python3 ./utils/download_ml_models.py

clean:
	rm -rf genomic_data_service.egg-info/

worker:
	celery -A genomic_data_service.region_indexer_task worker --loglevel=INFO

flower:
	flower -A genomic_data_service.region_indexer_task --address=127.0.0.1 --port=5555 --persistent=True --db=indexer_logs --max_tasks=1000000

index:
	python3 genomic_data_service/region_indexer.py

db:
	FLASK_APP=$(APP_NAME) FLASK_ENV=development python3 migrate.py db init
	FLASK_APP=$(APP_NAME) FLASK_ENV=development python3 migrate.py db migrate
	FLASK_APP=$(APP_NAME) FLASK_ENV=development python3 migrate.py db upgrade

dev:
	docker-compose --file docker-compose.yml --file ./docker/development.yml --env-file ./docker/compose/development.env up

test:
	docker-compose --file docker-compose.yml --file ./docker/development.yml --env-file ./docker/compose/test.env up

prod:
	docker-compose --file docker-compose.yml --file ./docker/production.yml --env-file ./docker/compose/production.env up
