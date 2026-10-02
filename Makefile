PYTHON ?= python

.PHONY: all audit test null bench figures reproduce clean selfcheck scale
.PHONY: pipeline-test pipeline-reference pipeline-accessions pipeline-taskA-source pipeline-taskA-parse
.PHONY: pipeline-taskA-overview pipeline-clusters pipeline-splits pipeline-features pipeline-embeddings pipeline

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

# ---------------------------------------------------------------------------
# Multi-task data and representation pipeline (Phases 0 to 6).
# Separate from the targets above, which drive the earlier single-task benchmark.
# ---------------------------------------------------------------------------

## Every pipeline guard: schema, reference resolver, frozen splits, input preflight
pipeline-test:
	$(PYTHON) schemas/test_task_schema.py
	$(PYTHON) data_acquisition/test_resolve_mmlv_reference.py
	$(PYTHON) data_acquisition/test_fetch_doman_s1.py
	$(PYTHON) data_acquisition/test_parse_taskA.py
	$(PYTHON) curation/test_splits.py
	$(PYTHON) data_acquisition/check_inputs.py --allow-missing

## Resolve the Task B reference frame against UniProt and assert every anchor
pipeline-reference:
	$(PYTHON) data_acquisition/resolve_mmlv_reference.py --fetch

## Resolve Task A accessions from sequence; needs network, and is resumable
pipeline-accessions:
	$(PYTHON) data_acquisition/resolve_taskA_accessions.py

## Acquire Doman et al. Supplementary Table S1, then inventory every sheet of it.
## The inventory must be read by a human before anything is parsed: Table S1 holds
## both the 59 assayed enzymes and the 543 unassayed phylogenetic sequences.
pipeline-taskA-source:
	$(PYTHON) data_acquisition/fetch_doman_s1.py
	$(PYTHON) data_acquisition/extract_doman_fulltext_facts.py
	$(PYTHON) data_acquisition/inventory_tableS1.py

## Parse Table S1's assayed block into curated.csv, and reconcile it. Needs the Gate G1
## ruling on reports/tableS1_inventory.md to have been given; the parser asserts the
## structure that was ruled on and halts if the workbook no longer matches it.
pipeline-taskA-parse:
	$(PYTHON) data_acquisition/resolve_taskA_near_matches.py
	$(PYTHON) data_acquisition/parse_taskA.py

## Identity clustering. Needs MMseqs2: set MMSEQS_BIN to its path.
pipeline-clusters:
	$(PYTHON) curation/cluster_redundancy.py --mmseqs $(MMSEQS_BIN)

## Descriptive overview of the Task A panel, plus its figures. Needs the clusters.
pipeline-taskA-overview:
	$(PYTHON) curation/dataset_overview_taskA.py

## Rewrite the frozen split definition files, then verify them against every
## leakage condition. The verification is a separate step because the splits are data:
## nothing else in the pipeline would notice if one were edited.
pipeline-splits:
	$(PYTHON) curation/define_splits.py
	$(PYTHON) curation/verify_splits_taskA.py

## Handcrafted feature matrices and missingness masks
pipeline-features:
	$(PYTHON) features/build_handcrafted.py

## ESM-2 representations at four scales, then verify every manifest checksum
pipeline-embeddings:
	$(PYTHON) embeddings/build_embeddings.py
	$(PYTHON) embeddings/verify_manifest.py

## The whole pipeline, in dependency order. Stops early if a guard fails.
pipeline: pipeline-test pipeline-reference pipeline-taskA-parse pipeline-taskA-overview pipeline-splits pipeline-features pipeline-embeddings
	@echo "Pipeline complete. Reports in reports/. No model has been trained."
