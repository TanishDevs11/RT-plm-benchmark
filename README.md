# RT-plm-benchmark

This repository is a methodological rebuild of
[TanishDevs11/RT-Activity-Predictor](https://github.com/TanishDevs11/RT-Activity-Predictor).
The original holds the submitted competition artifact and is **not modified by this
work**: no push, no branch, no tag, no pull request. It was cloned once at commit
`c1620706685d1a29e874031abd62d88a763d241e`, tagged here as `provenance`.

## Headline result

**No method tested beats using `protein_length_aa` as the score with no training at
all, and no method clears the score its own selection procedure reaches on pure
noise.**

| | CLS |
| --- | --- |
| 3-mer cosine to nearest training active, zero training | **0.4576** |
| `protein_length_aa`, zero training | **0.4416** |
| Best trained model (handcrafted + RandomForest) | 0.4284 |
| Best protein language model representation (ESM-2 150M) | 0.3052 |
| Minimum difference this benchmark can resolve at 80 percent power | **0.3419** |

The previously reported 0.9754 does not appear in this table. The reasons are in
[WRITEUP.md](WRITEUP.md), in the section titled "Why the previously reported 0.975
is not a result", and are summarised next.

## Why the previously reported 0.975 is not a result

I optimized the competition metric directly against the labels it was scored on.
`fast_opt.py` maximizes `compute_cls` over all 57 rows with 29 blend weights plus a
power exponent, and reseeds itself from its own previously fitted constants, so
each run resumes the prior hill climb. The commit history records 20 messages
quoting a CLS, climbing 0.4380 to 0.9754.

Running that same search on **pure Gaussian noise**:

| Free parameters | CLS on noise (p95) |
| --- | --- |
| 29 | 0.9340 |
| 50 | **0.9727** |

The stored search artifacts contain up to **62** fitted parameters, against a Kish
effective sample size of **11.34**. The submission scored 0.9754. Its margin over
what the procedure manufactures from nothing is about 0.025, inside the 0.079
bootstrap interval width. The reported score sits within its own noise floor.

## The instrument

The contribution here is the **search-capacity null**: run a selection procedure,
unchanged, on K vectors of pure noise and record the score it reaches. That is how
much of a reported score the procedure can manufacture from nothing on this dataset
with this metric. Every score in this repository carries one, plus a bootstrap
interval. A score that does not clear its null has reported nothing.

![capacity curve](bench/figures/search_null_capacity.png)

## Three verified findings about protein language model embeddings

- ESM-2 embeddings classify RT **family** at **0.8000** five-fold accuracy against a
  **0.3214** majority baseline.
- Embedding **PC1 tracks sequence length** at Spearman **-0.7681**.
- Raw ESM-2 embeddings score **0.0000** out of family, far **below** the length-only
  baseline of 0.4416.

The representation knows what an enzyme is related to. It does not know what it
does. Length residualization, family residualization, catalytic-core pooling and
attention-weighted pooling all failed to fix this, and the two core-focused
variants became the **most** lineage-predictive of all at 0.818 family accuracy.

## Layout

| Path | Contents |
| --- | --- |
| `audit/` | Leakage audit and metric properties of the inherited tree |
| `bench/protocol.py` | The nested LOFO harness every experiment calls |
| `bench/search_null.py` | Search-capacity null, the central instrument |
| `bench/baselines.py` | Baseline ladder |
| `bench/representations.py` | Representation benchmark |
| `bench/names.py` | Repairs an inherited RT-name join defect, fails loudly |
| `bench/results/` | All measured results |
| `legacy_leaky/` | Quarantined inherited code. Not usable in any results table |
| `legacy_submission/` | The submitted artifact, as the object of study |
| `PROGRESS.md` | Dated execution record |

## Reproducing

```
make reproduce
```

Retrains everything from `data/` to predictions and reads no stored result. Seed 42
throughout; every script prints its seed and library versions.

Other targets: `make audit`, `make test`, `make null`, `make bench`, `make scale`.

Environment for every number reported: Python 3.14.2 on Windows 11, numpy 2.4.2,
scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0, matplotlib 3.10.8, torch
2.11.0+cpu with zero CUDA devices, fair-esm 2.0.0.

## Protocol integrity

`bench/test_protocol.py` corrupts every held-out label and requires the selected
configuration to be byte-identical, and includes a deliberate **peeking positive
control** that the check must reject. The control is the load-bearing test: a green
suite in which peeking also passed would mean the check is inert. Continuous
integration runs it on every push, alongside a self-check on the null instrument.

## Blocked experiments

ProtT5-XL-U50, inverse-folding likelihoods, and zero-shot ESM-1v masked marginals
are marked **NOT RUN** with their exact blockers recorded in
[WRITEUP.md](WRITEUP.md). None was given an estimated or literature-quoted score.

## Licence

MIT. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
