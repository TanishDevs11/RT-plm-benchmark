# Compute feasibility

Probed on the rebuild machine, 2026-09-29. Every row below is an observed import
result or an observed device query, not a declaration copied from
`requirements.txt`. Declared dependencies are not evidence of installation, so the
declaration file is not used as a source here.

## Environment, observed

| Item | Observed value |
| --- | --- |
| Python | 3.14.2 |
| Platform | Windows 11, 10.0.26200 |
| numpy | 2.4.2 |
| scipy | 1.17.1 |
| pandas | 3.0.1 |
| scikit-learn | 1.8.0 |
| torch | 2.11.0+cpu |
| fair-esm (`esm`) | 2.0.0 |
| xgboost | 3.2.0 |
| matplotlib | 3.10.8 |
| biopython | 1.86 |
| transformers | NOT INSTALLED |
| shap | NOT INSTALLED |
| CUDA available | False |
| CUDA device count | 0 |

The single most consequential observation is `torch 2.11.0+cpu` with zero CUDA
devices. All model work is CPU bound. The second is that `transformers` is absent,
which is the loader for ProtT5-XL-U50.

## Consequences for the planned phases

Phases 1, 2, and 3 (audit, nested protocol, search-capacity null) are unaffected.
They are numpy, scipy, and scikit-learn work on 57 rows, and the search-capacity
null is a differential evolution run over stored vectors. These are the phases that
carry the central claim of the project, and they are fully runnable here.

The representation benchmark is where CPU-only bites. Classification per planned
representation:

| Representation | Status | Reason |
| --- | --- | --- |
| Handcrafted, sequence and structure descriptors | RUNNABLE | CSVs already in `data/` |
| ESM-2 8M, 35M, 150M mean-pooled | RUNNABLE | small models, 57 sequences, CPU is adequate |
| ESM-2 650M mean-pooled | RUNNABLE, SLOW | one forward pass per sequence, CPU minutes not hours |
| ESM-1v mean-pooled | RUNNABLE, SLOW | same shape of cost as ESM-2 650M |
| Length, family, and PCA corrected pooling variants | RUNNABLE | operates on cached embeddings |
| Catalytic-core and attention-weighted pooling | RUNNABLE | needs per-residue embeddings cached once |
| ProtT5-XL-U50 | BLOCKED | `transformers` and `sentencepiece` not installed |
| Zero-shot ESM-1v masked-marginal pseudo-likelihood | LIKELY INFEASIBLE | see cost note below |
| Inverse folding, ESM-IF or ProteinMPNN | BLOCKED | neither package installed, ESM-IF additionally needs a geometric stack |

### Cost note on masked marginals

Masked-marginal pseudo-likelihood requires one forward pass per residue per
sequence, not one per sequence. For 57 reverse transcriptases at roughly 500 to
1500 residues each, that is on the order of 50,000 forward passes of a 650M
parameter model. On CPU this is a multi-hour to multi-day job. It is listed as
LIKELY INFEASIBLE rather than BLOCKED because it is a wall-clock problem and not a
missing dependency: it becomes routine on a GPU, and it can also be approximated by
a single unmasked forward pass, which is a different quantity and will be named
differently if it is ever reported.

## Reporting rule

Any representation that is not executed is reported as NOT RUN in the results
tables. It is never given an estimated, interpolated, or literature-quoted score.
A benchmark whose honesty claim rests on invented numbers would be a worse artifact
than the one it sets out to correct, so the blocked rows stay visibly blocked.

## Unverified inherited artifact

`data/esm2_embeddings.npz` is present and is 1280 dimensional, which is consistent
with ESM-2 650M. The script that generated it has not been located in the
repository. Until that is resolved, the file is treated as an inherited artifact of
unknown provenance rather than as a reproducible input, and the `make reproduce`
target cannot claim to regenerate it. This is recorded as a reproducibility gap in
the audit.
