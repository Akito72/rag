up:
	docker compose up --build

test:
	docker compose run --rm api pytest

down:
	docker compose down

clean-docker:
	docker image rm -f rag-api || true
	docker builder prune -af
	docker container prune -f

migrate:
	docker compose run --rm api alembic upgrade head
