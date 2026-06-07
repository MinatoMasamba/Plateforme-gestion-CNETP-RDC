PYTHON = mon_env/bin/python
DAPHNE = mon_env/bin/daphne

dev:
	redis-cli ping > /dev/null 2>&1 || sudo systemctl start redis-server
	-fuser -k 8000/tcp 2>/dev/null
	$(PYTHON) manage.py migrate --noinput
	$(DAPHNE) -b 0.0.0.0 -p 8000 config.asgi:application

migrate:
	$(PYTHON) manage.py migrate

shell:
	$(PYTHON) manage.py shell
