PYTHON ?= python

.PHONY: all audit test null bench figures reproduce clean

all: audit test null bench

## Leakage audit and metric properties of the inherited tree
audit:
	$(PYTHON) audit/leakage_audit.py
	$(PYTHON) audit/metric_properties.py

## Protocol tests, including the deliberate peeking positive control
test:
	$(PYTHON) bench/test_protocol.py

## Fast instrument check for the search-capacity null
selfcheck:
	$(PYTHON) bench/search_null.py --self-check

## Full search-capacity null: reference run, K sweep, budget sweep
null:
	$(PYTHON) bench/search_null.py

## Embeddings, baseline ladder, representation benchmark
embeddings:
	$(PYTHON) bench/embeddings.py

bench: embeddings
	$(PYTHON) bench/baselines.py
	$(PYTHON) bench/representations.py

## Projected interval width and null at larger sample sizes
scale:
	$(PYTHON) bench/scale_projection.py

figures: null bench
	@echo "Figures written to audit/figures and bench/figures"

## Retrain everything from data/ to predictions. Reads no stored result.
reproduce: test selfcheck audit embeddings
	$(PYTHON) bench/baselines.py
	$(PYTHON) bench/representations.py
	$(PYTHON) bench/scale_projection.py
	@echo "Reproduced from data/. Results in bench/results/."

clean:
	rm -rf bench/cache/per_residue_*.npz bench/cache/attention_*.npz
