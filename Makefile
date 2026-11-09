.PHONY: setup test lint eval-sample api db-up

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check src tests

eval-sample:
	python -m src.ir.eval --corpus data/processed/sample_regs.jsonl \
	  --queries data/eval/queries_sample.tsv --qrels data/eval/qrels_sample.tsv \
	  --out results/sample_results.md

api:
	uvicorn src.api.main:app --reload

db-up:
	docker compose up -d
