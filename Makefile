.PHONY: up down status check traffic config
up:
	docker compose up -d

down:
	docker compose down

status:
	docker compose ps

check:
	sh scripts/smoke.sh

traffic:
	sh scripts/send-traffic.sh

config:
	docker compose config --quiet
