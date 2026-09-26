    .PHONY: install-dev test test-integration lint up down logs restart ps smoke htpasswd clean

    install-dev:
    	pip install -r app/requirements-dev.txt

test:
	cd app && python -m pytest --cov=app --cov-report=term-missing

test-integration:
	python -m pytest tests_integration -m integration -v

    lint:
    	ruff check app/

    up:
    	docker compose up -d --build

    down:
    	docker compose down

    logs:
    	docker compose logs -f

    restart:
    	docker compose restart

    ps:
    	docker compose ps

    smoke:
    	curl -s http://localhost/health

    htpasswd:
    	@echo "Сгенерировать пароль:"
    	@echo "  docker run --rm httpd:alpine htpasswd -nbB admin yourpassword > nginx/.htpasswd"

    clean:
    	docker compose down -v
    	rm -rf data/*
