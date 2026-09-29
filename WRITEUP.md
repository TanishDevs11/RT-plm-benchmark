# What a 57-enzyme benchmark can and cannot tell you

## Summary

I submitted a model that scored CLS 0.9754 on 57 reverse transcriptases under
leave-one-family-out validation. That number is not a generalization estimate. It
is the value of an objective function that I maximized directly against the labels
it was scored on.

This repository is the rebuild. Its headline result is that **no method I tested,
including every protein language model representation, beats using
`protein_length_aa` as the score with no training at all**, and that **no method
clears the score its own selection procedure reaches on pure noise**.

That is a worse number than 0.9754 and a better piece of work.

## Why the previously reported 0.975 is not a result

I wrote `fast_opt.py`. It builds an objective that returns the negation of
`compute_cls(seq["active"], y_score, seq["pe_efficiency_pct"])` evaluated over all
57 rows, and hands that objective to `scipy.optimize.differential_evolution` with
29 blend weights plus a power exponent. The labels in that call are the labels the
score is reported against. There is no held-out set anywhere in the loop.

It is worse than a single pass. The script seeds its starting point by parsing the
previously fitted constants back out of `experiments/calibrated_lofo_predictions.py`,
so every run resumes the previous run's hill climb. The commit history records the
climb directly: 20 commit messages quote a CLS, rising from 0.4380 to 0.9754. The
winning parameters are frozen into source at 16 significant figures, which is the
signature of a fitted constant rather than a chosen one.

Here is the number that settles it. I ran that exact search, unchanged, on vectors
of pure Gaussian noise containing no information about activity whatsoever:

| Free parameters in the search | CLS reached on pure noise (p95) |
| --- | --- |
| 5 | 0.5606 |
| 10 | 0.6536 |
| 20 | 0.8637 |
| 29 | 0.9340 |
| 50 | **0.9727** |

The stored search artifacts in this repository contain up to **62** fitted
parameters. At 50 parameters the search reaches 0.9727 on noise. My submission
scored 0.9754. The margin over what the procedure manufactures from nothing is
about 0.025, and the bootstrap 95 percent interval on that submission spans 0.079.
The reported score sits inside its own noise floor.

I am not claiming the underlying model learned nothing. I am claiming that this
experiment cannot distinguish whether it did, and that I presented the number as
though it could.

## The instrument: search-capacity null

The contribution I would defend in any room is not a model. It is a routine
instrument for small-n benchmarks.

Given a selection procedure with K free parameters and budget B, run it unchanged
on K vectors of pure noise and record the score it reaches. That is the
search-capacity null. It measures how much of a reported score the procedure can
manufacture from nothing on this dataset with this metric. Every score in this
repository is printed next to its null, and a score that does not clear its null
has reported nothing.

The capacity curve, in `bench/figures/search_null_capacity.png`, does not saturate
over the range tested. Five free parameters already reach 0.50 on noise, which
matches the best trained baseline here. The budget sweep shows most of the
manufacturable score is available almost immediately: ten iterations of
differential evolution at K=29 already reach a mean of 0.6809.

### One number I did not force to agree

The project brief I worked from expected the K=29 noise null to land near 0.848. My
single reference draw at seed 42 came out 0.9121, and the self-check I had written
reported FAIL. I did not adjust the budget, the bounds, or the tolerance to close
that gap.

The distribution resolved it honestly. Across 20 repeats the reference null has
mean 0.8662 and median 0.8702. The expected 0.848 was correct; it describes the
centre of the distribution, and my single draw was simply a high one compared
against the wrong statistic. The fix was to report the right quantity, not to
change the procedure. The self-check in continuous integration now verifies the
properties that make the instrument trustworthy, which are determinism at a fixed
seed, a noise score well above zero, and capacity growing with K. It deliberately
does not assert a specific published value, because an instrument that is tuned
until it reproduces an expected number is no longer an instrument.

## What the metric can resolve

Before comparing any two methods, it is worth knowing whether this benchmark can
tell them apart. It largely cannot.

| Quantity | Value |
| --- | --- |
| Rows | 57, of which 21 active |
| Kish effective sample size of the weighted Spearman weights | **11.338** |
| MMLV-RT share of total weight | 15.56 percent |
| Top 5 RTs share of total weight | 56.17 percent |
| All 36 inactives combined | 0.137 percent |
| Bootstrap 95 percent CI width on a fixed prediction vector | 0.0794 |
| **Minimum resolvable CLS difference at 80 percent power** | **0.3419** |

The nominal sample size is 57. The weighted Spearman term behaves like about 11
independent points, and 30 to 62 free parameters were fitted against it. The
inactives, which are 36 of the 57 enzymes, carry about a tenth of one percent of
that term between them, so half the metric is decided by a handful of
high-efficiency enzymes.

The last row is the one that governs every comparison in this repository. A
difference smaller than 0.34 CLS is not resolvable here at 80 percent power. Almost
nothing I measured differs by that much, so almost nothing I measured is a win for
either side. The pairwise tables report the probability that A beats B under a
paired bootstrap, and mark anything below the threshold as not resolvable rather
than dressing a point difference as a result.

## Results

### Baseline ladder

All rows run through the nested protocol in `bench/protocol.py`.

| Method | CLS | PR-AUC | wSpearman | Beats length |
| --- | --- | --- | --- | --- |
| 3-mer cosine to nearest training active, no training | 0.4576 | 0.5309 | 0.4021 | yes |
| `protein_length_aa`, no training | 0.4416 | 0.5102 | 0.3893 | reference |
| handcrafted + RandomForest | 0.4284 | 0.7810 | 0.3755 | no |
| family prior by nearest training family, no training | 0.4160 | 0.4304 | 0.4025 | no |
| handcrafted + ExtraTrees | 0.1802 | 0.6830 | 0.0856 | no |
| negative `protein_length_aa` | 0.0000 | 0.3128 | 0.0000 | no |
| amino acid composition PC1 | 0.0000 | 0.4595 | 0.0000 | no |
| handcrafted + logistic regression | 0.0000 | 0.6427 | 0.0000 | no |
| raw ESM-2 mean-pooled + logistic regression | 0.0000 | 0.2877 | 0.0000 | no |

The two best rows are zero-training baselines. Not one trained model beats a single
number that was already sitting in the input file.

Several rows score exactly zero. That is real metric behaviour, not a bug: weighted
Spearman is floored at zero, and CLS is a harmonic mean, so a model that misranks
the high-efficiency enzymes scores zero no matter how well it separates active from
inactive. Handcrafted plus logistic regression reaches PR-AUC 0.6427, well above
chance, and still scores CLS 0.0000. A metric that can do that deserves to be
reported alongside its components, never alone.

### Representations

One nested protocol, one pair of inner-selected heads, only the representation
varies.

| Representation | CLS | PR-AUC | Margin vs null | Family accuracy |
| --- | --- | --- | --- | --- |
| ESM-2 150M mean-pooled | 0.3052 | 0.3666 | -0.1861 | 0.802 |
| ESM-2 35M mean-pooled | 0.1394 | 0.2985 | -0.3520 | 0.782 |
| ESM-2 8M mean-pooled | 0.0074 | 0.3242 | -0.4840 | 0.745 |
| handcrafted, sequence and physicochemical | 0.0000 | 0.6436 | -0.4914 | 0.712 |
| structure, pLDDT cleft and topology | 0.0000 | 0.3391 | -0.4914 | 0.659 |
| ESM-2 650M mean-pooled | 0.0000 | 0.2870 | -0.4914 | 0.800 |
| ESM-2 650M, length-residualized | 0.0000 | 0.3205 | -0.4914 | 0.800 |
| ESM-2 650M, family-residualized | 0.0000 | 0.4016 | -0.4914 | 0.800 |
| ESM-2 650M, catalytic-core pooled | 0.0000 | 0.2781 | -0.4914 | **0.818** |
| ESM-2, attention-weighted core pooling | 0.0000 | 0.2808 | -0.4914 | **0.818** |

**Every margin is negative.** No representation clears the score its own selection
procedure reaches on noise. On this task, at this sample size, none of them has
demonstrated signal.

Three things in that table are worth stating plainly.

First, the scale series is non-monotonic and the largest model is the worst.
ESM-2 goes 0.0074 at 8M, 0.1394 at 35M, 0.3052 at 150M, and 0.0000 at 650M. I have
no mechanism to offer for that, and at a minimum resolvable difference of 0.34 I
cannot claim the ordering is real. It is reported because suppressing it would be
the same error as before.

Second, every correction I was asked to test failed. Length residualization,
family residualization, catalytic-core pooling, and attention-weighted core pooling
all left the score at 0.0000. The two that specifically target the catalytic core
produced the **highest** lineage accuracy of any representation, 0.818. Restricting
attention to the catalytic machinery made the representation better at predicting
evolutionary family and no better at predicting function. That is the opposite of
the intended effect and it is the most interesting negative result here.

Third, the confound is direct. Across the table, family accuracy is high and stable
near 0.80 while CLS is near zero. The representation reliably knows what an enzyme
is related to, and reliably does not know what it does.

### The three representation findings, independently verified

- ESM-2 mean-pooled embeddings classify RT family at **0.8000** five-fold accuracy
  against a **0.3214** majority baseline. Measured on families with at least five
  members, since smaller ones cannot be stratified.
- Embedding PC1 tracks `protein_length_aa` at Spearman **-0.7681**. The dominant
  axis of the representation is measuring size.
- Raw ESM-2 embeddings plus logistic regression score **0.0000** out of family,
  far below the length-only baseline of 0.4416.

## An inherited data defect that changed a conclusion

While building the representation tables I found that `topology_features.csv` omits
the `-RT` suffix that `rt_sequences.csv` carries. A join on `rt_name` therefore
matched zero rows and fed nine entirely missing columns into the handcrafted
feature table. No error was raised. The model trained on nothing and reported a
number.

Repairing the join changed a result in the unflattering direction: handcrafted plus
RandomForest fell from 0.5072 to **0.4284**, below the length baseline, with a
negative margin against its own null. The higher score had come from training on
empty columns. `bench/names.py` now asserts full coverage and fails loudly instead
of returning empty columns, and records two further defects: `Line1-RT` has no
predicted structure, and `Vp-96.pdb` duplicates `Vp96-RT.pdb`, so 57 structure
files cover 56 enzymes.

I am recording this because it is the same class of failure as the original one. A
pipeline that cannot fail loudly will eventually report a number that means
nothing, and it will look exactly like a number that means something.

## Protocol

```
outer loop: for each of the 7 families F
    test  = F, train = the other 6
    inner loop: LOFO over the 6 training families
        select head, hyperparameters and preprocessing using inner scores only
    refit the selected configuration on all 6, predict F
pool the 57 outer predictions, compute CLS once
```

Selection is a pure function of the training families by construction, because
`select_configuration` never receives the test fold. `bench/test_protocol.py`
verifies this by corrupting every held-out label and requiring the selected
configuration to be byte-identical, and it includes a deliberate peeking positive
control that the check must reject. The control is the load-bearing test: a green
suite in which peeking also passed would mean the check is inert. It currently
detects peeking on 5 of 7 families.

CLS is computed on pooled predictions and never per fold. That is what makes the
three zero-active families and the single-member family tractable without dropping
rows, and it matches the competition evaluator, so the honest number stays
comparable to the dishonest one.

## Limitations

- **The benchmark cannot resolve its own comparisons.** At a minimum resolvable
  difference of 0.3419 CLS, nearly every ordering in this document is provisional.
  The correct reading of the representation table is not "150M is best" but "no
  representation is distinguishable from any other, and none clears its null".
- **Exact zeros dominate.** Seven of ten representations score exactly 0.0000
  because weighted Spearman floors at zero. The metric compresses a lot of
  genuinely different behaviour into one value, which limits what any comparison
  can say.
- **One label distribution, one assay.** Everything here is 57 enzymes measured one
  way. The scale projection in `bench/results/scale_projection.json` estimates what
  more data would buy, and it assumes new RTs resemble these, which is optimistic.
- **Blocked experiments** are listed below and were not estimated.

## Blocked experiments

| Item | Status | Blocker |
| --- | --- | --- |
| ProtT5-XL-U50 | NOT RUN | `transformers` and `sentencepiece` unavailable in this environment |
| Inverse folding, ESM-IF or ProteinMPNN | NOT RUN | not installed; ESM-IF needs a geometric stack with no Python 3.14 wheels |
| Zero-shot ESM-1v masked marginals | NOT RUN | about 30000 forward passes of a 650M model on a CPU-only torch |

No blocked row was given an estimated, interpolated, or literature-quoted score.

## Conclusions

1. **The 0.9754 is not a measurement.** A 62-parameter search on an effective
   sample of 11 reaches 0.9727 on pure noise. The submitted score does not clear
   that, and I optimized it against its own test labels.
2. **Mean-pooled protein language model embeddings encode lineage and length, not
   function, on this task.** Family accuracy near 0.80, PC1 to length at -0.77, and
   out-of-family CLS at or below a zero-training length baseline.
3. **The obvious corrections do not work.** Residualizing length, removing
   family-predictive components, and pooling over the catalytic core all failed,
   and the core-focused variants became more lineage-predictive, not less.
4. **Nothing beats a single column of the input file.** The two best scores in the
   entire benchmark are zero-training baselines.
5. **The real limit is n, and the real problem may be the metric.** With an
   effective sample size of 11.3 and a minimum resolvable difference of 0.34 CLS,
   this benchmark cannot support the comparisons people want to make with it. If
   the search-capacity null stays high as n grows, the metric should be replaced
   rather than the panel enlarged.

The contribution is the search-capacity null as routine practice for small-n
protein benchmarks, plus a concrete demonstration that mean-pooled embeddings track
lineage rather than catalysis on a 57-enzyme out-of-family task. A lower number
with an interval, a null, and a mechanism is worth more than a higher number with
none of those.

## Reproducing

```
make reproduce
```

Retrains everything from `data/` and reads no stored result. Seed 42 throughout.

Environment used for every number in this document: Python 3.14.2 on Windows 11,
numpy 2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0, matplotlib 3.10.8,
torch 2.11.0+cpu with zero CUDA devices, fair-esm 2.0.0.

One reproducibility caveat, stated rather than hidden: `data/esm2_embeddings.npz`
is inherited and no script in the tree generates it. The rebuild does not depend on
it, since `bench/embeddings.py` regenerates ESM-2 embeddings from
`data/rt_sequences.csv`, but the inherited file itself cannot be reproduced from
this repository.

The original submission repository, `TanishDevs11/RT-Activity-Predictor`, is
unmodified by this work.
