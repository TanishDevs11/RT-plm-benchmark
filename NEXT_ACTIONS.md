# Next actions

Derived from `REVIEW.md`, 2026-09-30, at HEAD `a39e9a7`. Every number cited here is either
read from a file in this repository or measured during that review; `REVIEW.md` says which
for each one.

---

## Blocking-progress checklist

| Item | State | Evidence |
| --- | --- | --- |
| Nested LOFO harness exists; deliberate-peek positive control passes | **done** | `python bench/test_protocol.py` exits 0 with all 6 tests passing, including "peeking detected on 5 of 7 families" |
| Baseline ladder complete, every trained model marked as beating or not beating `protein_length_aa` | **done** | `bench/results/baseline_ladder.md:7-17`, "Beats length" column populated on all 9 rows; script reruns exit 0 with only `seconds` changing |
| Representation benchmark reports paired-bootstrap win probabilities, not point differences | **done** | `bench/results/representations.md:30-76`, 45 comparisons each with `P(A beats B)` and a resolvability verdict |
| Minimum resolvable CLS difference at 80 percent power computed and stated | **done** | 0.3419, `bench/results/representations.md:7`, reproduced on rerun |
| `make reproduce` regenerates predictions from `data/` on a fresh clone | **not started** | `make` has never been run here; separately, `Makefile:40-44` omits `bench/search_null.py`, so it is not the sequence `reproduce.py:25-35` runs; and `reproduce.py` cannot report success because `bench/search_null.py:267` returns 1 deterministically |
| Data expansion scoping document written | **partial** | `bench/data_expansion.md` exists and is structurally sound, but 9 `UNVERIFIED` markers cover every n, assay readout and licence term |
| README states the leakage finding in the first person and does not present 0.975 as a result | **partial** | First person is correct: `README.md:29`, "I optimized the competition metric directly against the labels it was scored on." 0.975 is correctly excluded from the headline table at `README.md:23`. But the headline claim two lines above it is contradicted by the repository's own baseline ladder, so the section is not yet defensible |

---

## 1. Correct the two headline claims, and say what the evidence actually supports

**This outranks everything else, and it is not close.** The whole point of this rebuild is
that a claim was previously stated more strongly than its evidence allowed. Two of the
three sentences a reader will quote from `README.md` currently repeat that exact failure,
and the contradicting evidence is in this repository, in one case six lines below the claim.
Every other action on this list makes the work more complete. Only this one stops the work
from being wrong in the same way it was wrong before. Until it is done, no other result can
be circulated, because a reader who checks the first table will stop reading.

**What to do, specifically.**

1. `README.md:11-13` and `WRITEUP.md:10-13`. The sentence "no method clears the score its
   own selection procedure reaches on pure noise" is false. `bench/results/baseline_ladder.md:9,12,13`
   shows three rows with positive margins: length +0.0455, 3-mer cosine +0.0615, family
   prior +0.0199. The sentence "no method tested beats using `protein_length_aa`" is also
   false: 3-mer cosine scores 0.4576 against 0.4416 and is marked `yes` in the table
   `README.md:17` prints immediately below. Replace both with what is true and still
   striking: *the only things that clear their own nulls are three zero-training baselines,
   and they clear them by 0.02 to 0.06 CLS against a benchmark that cannot resolve a
   difference below 0.3419. Not one trained model clears its null, and not one beats a
   single column of the input file.* `WRITEUP.md:162`, "Every margin is negative", is true
   of the representation table only; keep it there and stop generalizing it.
2. `README.md:37-45`, `WRITEUP.md:35-47,294-296`, `PROGRESS.md:64,70`. Replace the K=50
   null with the K=29 one throughout, and say the comparison honestly. `REVIEW.md` section
   5.4 gives the sentence and the numbers: mean 0.8662, p95 0.9501, margin +0.0252, none of
   20 draws reaching 0.9754. Then carry the three reasons the leakage conclusion survives
   anyway, which are in the same section. Note that `WRITEUP.md:286` already uses
   30-parameter language for the scale projection, so the document is currently
   inconsistent with itself.
3. Say which statistic each null figure is. Three different K=29 p95 values are published
   in this repository, 0.9061, 0.9340 and 0.9501, differing only by repeat count, and no
   document names the repeat count. Quote the 20-repeat p95, 0.9501, and label it.
4. `WRITEUP.md:126,128,131,140` and `PROGRESS.md:79,80,83`. Replace the pre-join-repair
   PR-AUC and weighted Spearman values with the ones in `bench/results/baseline_ladder.md:14-16`.
   The table in `REVIEW.md` section 7.3 gives all six substitutions. Then either remove or
   correct `PROGRESS.md:86`, "All rows are from the post-fix run."
5. `WRITEUP.md:78-81`. "The expected 0.848 was correct; it describes the centre of the
   distribution" overstates it; 0.848 sits about 0.35 standard deviations below the mean.
   Say it is an ordinary member of the distribution. Keep the surrounding reasoning intact,
   which is the strongest paragraph in the document.

**Why it matters.** It makes the headline claim defensible instead of falsifiable from the
next table down, and it removes a parameter-count substitution that a reviewer who reads
`audit/leakage_report.md:48` will find in one minute.

**What it unblocks.** Circulating anything. It also unblocks the G3 endorsement gate at
`NEXT_STEPS.md:182-194`, which cannot sensibly be run against claims that are known to be
wrong.

**Effort:** hours. It is editing, and every replacement number already exists.

**Done criterion:** no sentence in `README.md`, `WRITEUP.md` or `PROGRESS.md` asserts
something that `bench/results/baseline_ladder.md`, `bench/results/representations.md`,
`bench/results/search_null.json` or `bench/results/null_distribution.csv` contradicts, and
every null figure quoted names its K and its repeat count.

**Alternatives rejected, and why.** *Fixing `reproduce.py`* (action 2) is cheaper and more
satisfying, but a pipeline that exits cleanly while publishing a false headline is worse
than one that exits 1. *Establishing the true parameter count* (action 3) would let action
1 be stated more precisely, but action 1 can be stated correctly today, because every
document already describes the submitted search as 29 weights plus a power, and action 3
may turn out to have no answer. *Publishing the family-classification control* (action 4)
strengthens a claim that is already true; action 1 repairs claims that are currently false,
and false beats incomplete. *Running ESM-1v* (action 7) is explicitly recorded at
`NEXT_STEPS.md:47-49` as unable to change any conclusion.

---

## 2. Make `reproduce.py` able to succeed, and make `make reproduce` mean what the README says

**What to do.** `bench/search_null.py:267` returns `0 if self_check_passed else 1`, and
`self_check_passed` compares a deterministic 0.9121 single draw against the hardcoded
`REFERENCE_EXPECTED = 0.848` at `bench/search_null.py:49` with tolerance 0.05. It is false
every time, so `reproduce.py:31` will always record `FAILED search-capacity null sweep
(exit 1)` and the done-criterion `NEXT_STEPS.md:97` sets for itself can never be met. The
decision to make is whether a single draw disagreeing with an inherited prior should fail a
build at all. It should not: the same script already has a principled self-check at
`bench/search_null.py:305-333` that tests determinism, above-zero noise, and capacity
growth without asserting a published value, and `WRITEUP.md:82-86` argues correctly for
exactly that design. Make `main()` report the deviation without returning non-zero, and
leave the assertion to `--self-check`. Separately, add `bench/search_null.py` to the
`reproduce` target at `Makefile:40-44`, or change `README.md:95` and `PROGRESS.md:151-152`
to stop claiming the two entry points run the same sequence.

**Why it matters.** It makes the reproduction claim testable. Right now nobody can confirm
or refute `README.md:92`, because the only way to run the whole thing reports a failure that
is not a failure.

**What it unblocks.** The end-to-end verification at `NEXT_STEPS.md:85-97`, which is
currently blocked on a criterion rather than on memory.

**Effort:** hours, plus one full run of several hours to verify.

**Done criterion:** `python reproduce.py` on a fresh clone ends with `all stages completed`,
and either `make reproduce` runs the same stage list or the README stops saying it does.

---

## 3. Establish, or record as unestablished, the free-parameter count behind 0.9754

**What to do.** `audit/leakage_report.md:48` attributes 62 free parameters to
`legacy_leaky/results/de_best_weights.json`, whose own recorded `best_cls` is 0.8978, not
the submitted 0.9754. The submitted vector is elementwise identical to
`calibrated_predictions_selected_features.csv`, `lambdarank_residual_candidate.csv` and
`quantum_listwise_candidate.csv`; the lambdarank stage selected `lambda_weight` 0.0 on all
seven folds and passed the base through unchanged. Applying the frozen `RANK_BLEND_WEIGHTS`
to `component_arrays.json` reproduces 0.8350, not 0.9754, so the constants in
`calibrated_lofo_predictions.py` are an intermediate state. Trace which script last wrote
`calibrated_predictions_selected_features.csv` and count the parameters fitted along that
path, counting each repair, residual and midband stage that touched the 57 labels. Extend
`audit/leakage_audit.py` to walk that chain rather than globbing for JSON files with
weight-shaped fields. If the chain cannot be reconstructed, say so in
`audit/leakage_report.md` in those words.

**Why it matters.** It is the difference between "a search with this much capacity produced
0.9754" and "a search of unknown capacity produced 0.9754." The second is still damning,
and it is the one the evidence currently supports.

**What it blocks.** Nothing, once action 1 lands. It upgrades action 1's statement from
correct to precise, and it removes the last place where the write-up's parameter count is
borrowed from the wrong artifact.

**Effort:** a day. The chain runs through several quarantined scripts that overwrite the
same CSV.

**Done criterion:** `audit/leakage_report.md` either names the parameter count on the path
that produced `submission.csv`, with the scripts listed, or states explicitly that the path
cannot be reconstructed from the retained history.

---

## 4. Publish the family-classification control

**What to do.** Add the three controls to `bench/representations.py` beside
`lineage_confound` at lines 277-299: 3-mer composition, length alone, and the majority
baseline, on the same stratified 5-fold split. Write them into
`bench/results/representations.md` and replace the bare "0.8000 against a 0.3214 majority
baseline" at `README.md:59`, `WRITEUP.md:188` and `PROGRESS.md:119` with the full table.
`REVIEW.md` section 6a has the measured values. State the 3-mer encoding explicitly: it
moves the number from 0.5697 to 0.7152 depending on normalization, so an unlabelled 3-mer
row is not a control, it is a choice.

While there, give the PC1-to-length figure a generator. Spearman -0.7681 is published in
three documents and computed by no script in the tree, which contradicts `PROGRESS.md:4-5`.
It is preprocessing-sensitive: standardized embeddings give -0.7681, centred-only give
+0.6198. Compute it in `bench/representations.py`, write it to
`bench/results/representations.json`, and state the preprocessing where it is quoted.

**Why it matters.** "ESM-2 classifies family at 0.80" against a majority baseline says only
that the embeddings are not noise. Against 3-mer composition at 0.62 and length at 0.52, it
says the embeddings carry lineage information beyond raw sequence composition, which is the
claim the project actually wants to make. The control supports it.

**What it unblocks.** The lineage-versus-function argument, which is the project's second
contribution after the null.

**Effort:** hours.

**Done criterion:** `bench/results/representations.md` contains the four-row control table
and the PC1 correlation with its preprocessing named, and every document quoting either
number cites that file.

---

## 5. Decide what to do about `data/esm2_embeddings.npz`, which the rebuild does depend on

**What to do.** `WRITEUP.md:332-336` and `NEXT_STEPS.md:134-138` both say the rebuild does
not depend on this file. `bench/baselines.py:62` loads it unconditionally, and it feeds
published ladder rows 5 and 10 through lines 169 and 244. The remedy offered at
`NEXT_STEPS.md:137`, delete it, would break `bench/baselines.py`. The good news is that the
file is not actually irreproducible: it matches `bench/cache/pooled_esm2_650M.npz` to a max
elementwise difference of 2.38e-06 at float32, with identical name order. Point
`bench/baselines.py` at the regenerated cache with the inherited file as an explicit
fallback, mirroring what `bench/representations.py:380-384` already does, then correct the
three documents and `legacy_submission/README.md:36-39`.

**Why it matters.** It closes the last place where an inherited artifact of unknown
provenance is a silent input to a published table, which is the class of defect this project
exists to find. `bench/names.py` already applies exactly this standard to the join.

**What it unblocks.** A clean statement that every published number derives from `data/`
through code in the tree.

**Effort:** hours.

**Done criterion:** `bench/baselines.py` prefers the regenerated cache, the ladder
reproduces unchanged, and no document claims a dependency that exists or an
irreproducibility that does not.

---

## 6. Resolve the ten UNCLEAR leakage classifications by reading control flow

**What to do.** `audit/leakage_report.md:18-27` lists ten files as UNCLEAR. The
classification came from a regex-assisted scan for search markers, not from control-flow
analysis, which `NEXT_STEPS.md:190-191` already flags as needing a second pair of eyes. Read
each of the ten and decide leak or clean on the question of whether a metric value computed
on held-out labels reaches a selection decision. Two of them,
`lambdarank_residual_ranker.py` and `nested_residual_ranker.py`, sit directly on the path to
the submitted vector, so start there.

**Why it matters.** The leakage audit is the project's primary factual claim about the
inherited work. Ten of twenty-three files unclassified is a large hole in it, and the two
named above bear on action 3.

**What it unblocks.** A defensible total in `audit/leakage_report.md:39`, and part of the
evidence action 3 needs.

**Effort:** a day.

**Done criterion:** the UNCLEAR count is zero, or each remaining UNCLEAR carries a written
reason why control flow does not settle it.

---

## 7. Finish the blocked representations, in the order the blockers allow

**What to do.** In this order: (a) attempt `pip install transformers sentencepiece` and
record whether it works on Python 3.14, which `NEXT_STEPS.md:54-56` says was never
determined and costs five minutes; (b) run `python bench/embeddings.py` for ESM-1v when
memory allows, then `python bench/representations.py`; (c) treat ProtT5 and inverse folding
as genuinely open, gated on (a) and on a ProteinMPNN install respectively.

**Why it matters.** It completes the scale series. `NEXT_STEPS.md:47-49` states the case
against its importance accurately: every ESM-2 row already has a negative margin, so one
more 650M row is very unlikely to move a conclusion.

**What it unblocks.** One row of a table. Nothing depends on it.

**Effort:** (a) minutes. (b) hours on a machine with more memory. (c) more than a day.

**Done criterion:** `bench/results/representations.md`'s blocked table shrinks, or each
remaining row's blocker is restated as a tested fact rather than an assumption.

---

## Polish, not substance

These do not compete with anything above. They are listed so they stop occupying attention.

- **Account for `src/` and `features/` in the layout table.** 28 tracked inherited files sit
  outside the quarantine and outside `README.md:72-83`. `bench/` is verified not to import
  from either, so no published number is affected. One paragraph in
  `legacy_leaky/README.md` saying why they were left in place would close it.
- **Commit or explain the gitignored run logs.** `.gitignore:18` excludes
  `bench/results/*_log.txt`, so the four logs exist only on this machine. They are the
  per-stage timing and progress record.
- **Note the CI interpreter gap.** `.github/workflows/ci.yml:14` pins Python 3.12; every
  published number came from 3.14.2. Worth one line in the README so a green badge is not
  read as certifying the result environment.
- **Distinguish the two bootstrap interval widths.** `WRITEUP.md:100` gives 0.0794 and
  `WRITEUP.md:279` gives 0.2017 at n=57, both labelled as a bootstrap CI width. They are
  different quantities. A four-word clarification on each row is enough.
- **Update the stale handoff facts in `NEXT_STEPS.md`.** Line 10 names HEAD `aa43c1c`; HEAD
  is `a39e9a7`, the commit that added the file.
- **Add the family-accuracy seed to its quoted figures.** 0.8000 at `random_state=42` and
  0.8212 at `random_state=0` are the same measurement under different fold assignments on 56
  rows. Naming the seed prevents a future reader from reporting a discrepancy that is not
  one.
