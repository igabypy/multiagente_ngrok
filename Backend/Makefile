.PHONY: start stop logs test shell rebuild

# Start containers
start:
	docker compose -f ../docker-compose.yml up -d

# Stop containers
stop:
	docker compose -f ../docker-compose.yml down

# View backend logs
logs:
	docker compose -f ../docker-compose.yml logs -f backend

# Run tests inside container
test:
	docker compose -f ../docker-compose.yml exec backend pytest tests/ -v

# Open shell inside backend container
shell:
	docker compose -f ../docker-compose.yml exec backend bash

# Rebuild and restart
rebuild:
	docker compose -f ../docker-compose.yml up -d --build
