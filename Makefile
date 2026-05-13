.PHONY: install test run demo
install:
	pip install -e '.[dev]'

test:
	pytest -q

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

demo:
	python scripts/demo_cli.py --mode defense --question "Analyze these nginx logs and recommend response" --evidence samples/logs/nginx_suspicious.log
