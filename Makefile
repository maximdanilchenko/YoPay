###########
# Constants
###########
COMPOSE_RUN_DEV = docker-compose -f docker-compose-dev.yaml run --rm
COMPOSE_BUILD_DEV = docker-compose -f docker-compose-dev.yaml build --no-cache yopay

###############
# DB migrations
###############
db_upgrade:
	$(COMPOSE_RUN_DEV) yopay alembic upgrade head

db_migrate:
	$(COMPOSE_RUN_DEV) yopay alembic revision --autogenerate

############
# Dev server
############
dev-build:
	$(COMPOSE_BUILD_DEV)

dev-run: db_upgrade
	$(COMPOSE_RUN_DEV) --service-ports yopay adev runserver main.py --no-livereload --port=8765

dev-stop:
	docker-compose -f docker-compose-dev.yaml stop

dev-down:
	docker-compose -f docker-compose-dev.yaml down

format:
	isort -y
	black .
