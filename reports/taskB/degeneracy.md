# Task B: whole-sequence feature degeneracy, quantified

Written by `features/taskB/quantify_degeneracy.py`. This is the one Task B
measurement that needs no activity values, because it is a property of the feature
space rather than of the labels.

Reference: `reference_candidate_unconfirmed.fasta`, SHA256 `61fdd3473f598a2e2b01e1527d9036ee0470c32246e17462604e003b465c050c`.
1046 sequences, the wild type plus 1045 single substitutions.

## Why this has to be stated before any score

Every row in Task B is a single amino acid substitution in the same 498-residue
protein. A substitution changes at most k of the 495 4-mer positions and shifts a
whole-sequence average by one residue's worth out of 498. So the feature vectors
for all 1046 sequences are nearly identical **by construction**, before any
modelling choice is made.

The consequence matters for how a results table is read. When a k-mer or
whole-sequence physicochemical representation scores near zero on this task, that
is not the representation failing to capture variant effects. It is the
representation being unable to distinguish the variants at all. Those are
different findings, and reporting the first when the second is true would
misattribute a property of the task to a property of the method.

## Pairwise cosine similarity

Sampled over 199,809 random pairs, seed 1729.

| block | dimensions | minimum | median | 99th percentile | maximum | standard deviation |
| --- | --- | --- | --- | --- | --- | --- |
| 4-mer frequencies | 4578 | 0.983968 | 0.983968 | 0.991984 | 0.992034 | 1.69e-03 |
| whole-sequence physicochemical | 6 | 0.999970 | 0.999998 | 1.000000 | 1.000000 | 2.92e-06 |

A cosine similarity of 1 means two vectors are identical. The least similar pair
in any block here sits 0.0160 from identical, which is 1.60 percent.

The distributions are tight and right-skewed: the minimum and the median agree to
six decimal places in the 4-mer block while the standard deviation is 1.69e-03,
because most pairs differ at two positions and sit at the floor, while the pairs
that share a mutated position sit in a thin upper tail.

## Effective dimensionality

| block | dimensions | numeric rank after centring | variance in the leading component | variance in the leading three |
| --- | --- | --- | --- | --- |
| 4-mer frequencies | 4578 | 1045 | 0.0376 | 0.1097 |
| whole-sequence physicochemical | 6 | 5 | 0.9819 | 1.0000 |

## The invariance check, so this result does not depend on the open question

The reference's substitution content is unconfirmed: whether the construct retains
PE2's D200N, T306K, W313F and T330P is undetermined from the preprint. That would
normally block any computation on the variant sequences.

It does not block this one, and the script demonstrates why rather than asserting
it. Whatever the reference's substitution content turns out to be, **all 1045
variants share it**, so changing the reference changes every variant identically
and leaves the pairwise geometry essentially untouched.

Recomputing the whole distribution against a reference deliberately perturbed at
all four unconfirmed positions moves the median cosine similarity by 0.00e+00:

| | median cosine similarity |
| --- | --- |
| against the candidate reference | 0.98396794 |
| against a reference perturbed at all four unconfirmed positions | 0.98396794 |
| absolute difference | 0.00e+00 |

So this measurement stands regardless of how the reference question is resolved.

## What follows for the benchmark design

1. **Whole-sequence representations are controls, not competitors, in Task B.**
   They are included for completeness and must be labelled degenerate in any
   results table, with this measurement cited.
2. **The same applies to mean-pooled language model embeddings.** Mean pooling over
   a sequence that differs at one position produces the same degeneracy, which is
   why the Task B brief makes mean pooling a labelled control and never the primary
   protein language model condition. The primary conditions are the embedding at
   the mutated position, the mutant minus wild-type difference at that position,
   and a local window around it.
3. **A near-zero score from a degenerate block may not even be fittable.** With a
   numeric rank far below the nominal dimension and variance concentrated in one
   direction, a regularized linear model may return a constant. If that happens it
   is reported as the outcome, not as a representation score.

## What this does not measure

Nothing about variant effects. There are no labels; see
`reports/taskB/FINAL_REPORT.md`. This file quantifies the geometry of the feature
space and nothing else.
