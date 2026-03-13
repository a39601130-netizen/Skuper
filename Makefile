SERVER := bot
SERVER_DIR := ~/Artur/Skuper

# ─── Локальная разработка ─────────────────────────────────────────────────────

.PHONY: run
run:
	python run.py

.PHONY: frontend
frontend:
	cd frontend && npm run dev

.PHONY: install
install:
	pip install -r requirements.txt
	cd frontend && npm install

# ─── Деплой на сервер ─────────────────────────────────────────────────────────

.PHONY: deploy
deploy:
	git push origin master
	ssh $(SERVER) "cd $(SERVER_DIR) && git pull && docker compose up --build -d"

.PHONY: restart
restart:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose restart budget_bot"

.PHONY: rebuild
rebuild:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose up --build -d budget_bot"

# ─── Логи и статус ────────────────────────────────────────────────────────────

.PHONY: logs
logs:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose logs -f --tail=50 budget_bot"

.PHONY: logs-all
logs-all:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose logs -f --tail=30"

.PHONY: status
status:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose ps"

# ─── База данных ──────────────────────────────────────────────────────────────

.PHONY: db-shell
db-shell:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose exec budget_postgres psql -U budget -d budget_bot"

.PHONY: db-backup
db-backup:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose exec budget_postgres pg_dump -U budget budget_bot" > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved locally"

# ─── Code Server ──────────────────────────────────────────────────────────────

.PHONY: code-server-start
code-server-start:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose up -d code_server"

.PHONY: code-server-stop
code-server-stop:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose stop code_server"

.PHONY: code-server-logs
code-server-logs:
	ssh $(SERVER) "cd $(SERVER_DIR) && docker compose logs -f code_server"

# ─── Git ──────────────────────────────────────────────────────────────────────

.PHONY: push
push:
	git add -A && git commit -m "$(m)" && git push origin master

.PHONY: pull-server
pull-server:
	ssh $(SERVER) "cd $(SERVER_DIR) && git pull"

.PHONY: sync
sync: push pull-server restart
	@echo "Deployed and restarted"

# ─── Помощь ───────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "Budget Bot — команды управления"
	@echo "================================="
	@echo ""
	@echo "  Локально:"
	@echo "    make run          — запустить backend + bot"
	@echo "    make frontend     — запустить frontend (Vite)"
	@echo "    make install      — установить зависимости"
	@echo ""
	@echo "  Деплой:"
	@echo "    make deploy       — build + deploy на сервер"
	@echo "    make restart      — перезапустить бота (без rebuild)"
	@echo "    make rebuild      — пересобрать и перезапустить"
	@echo "    make sync m='msg' — commit + push + restart"
	@echo ""
	@echo "  Логи:"
	@echo "    make logs         — логи бота (следить)"
	@echo "    make logs-all     — логи всех сервисов"
	@echo "    make status       — статус контейнеров"
	@echo ""
	@echo "  БД:"
	@echo "    make db-shell     — psql на сервере"
	@echo "    make db-backup    — сохранить дамп локально"
	@echo ""
	@echo "  Code Server (редактор в браузере):"
	@echo "    make code-server-start — запустить редактор"
	@echo "    make code-server-stop  — остановить редактор"
	@echo "    URL: https://code.budget-bot.duckdns.org"
	@echo ""
