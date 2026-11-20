# Review of RT-plm-benchmark

Review date: 2026-09-30. Reviewed at HEAD `a39e9a7`, working tree clean, on the same
machine and environment the published results came from: Python 3.14.2, Windows 11,
numpy 2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0.

**Number provenance convention used throughout.** Every number below carries one of two
labels. `[READ]` means the number was read from a file in this repository, with the path
and line given. `[RAN]` means the number was computed by me in this session, with the
command or script given. No number appears here from any other source. Where this
review's brief supplied a prior that the repository contradicts, both are shown and the
disagreement is reported rather than resolved.

**Scope.** This is a read and verify pass. No analysis code was modified. Three scripts
were executed to test whether they still run; each one rewrites its own output files, so
each output was restored to its committed state immediately afterwards and the working
tree was confirmed clean. One new file was written, `bench/results/null_distribution.csv`,
because section 5 of the review brief names it explicitly.

---

## 1. Where the project actually stands

The rebuild is substantially complete and its central instrument works. The nested
leave-one-family-out harness passes all six of its tests including the deliberate peeking
positive control `[RAN]`, the leakage audit reproduces byte-identically `[RAN]`, the
baseline ladder and the representation benchmark both rerun and change nothing but their
`seconds` fields `[RAN]`, and the search-capacity null reproduces its stored twenty-repeat
distribution exactly, value for value `[RAN]`. The five leakage-audit findings in section
4 of the brief are all confirmed. The project's honest negative results are real and
defensible. What is not yet defensible is the way two of the headline claims are worded
and one comparison is drawn. The README's headline sentence, that no method beats
`protein_length_aa` and no method clears its own null, is contradicted by the
repository's own baseline ladder three lines further down the same file, where a
zero-training 3-mer baseline scores 0.4576 against 0.4416 and clears its null by +0.0615
`[READ]`. The comparison that debunks the 0.9754 submission is drawn against a fifty
parameter null rather than the twenty-nine parameter one that matches the search actually
described in the same paragraph; at the correct null the submitted score clears the p95 by
+0.0252 `[RAN]` instead of failing to clear it, which weakens but does not overturn the
leakage conclusion, because that margin is well inside the 0.0794 bootstrap interval width
on the submitted vector `[READ]`. Separately, `reproduce.py` cannot succeed as written:
the null sweep stage returns exit 1 deterministically, so the verification criterion
`NEXT_STEPS.md` sets for itself is unreachable. None of this touches the measurements. All
of it touches the claims, and the claims are the deliverable.

---

## 2. Verification of `NEXT_STEPS.md`

| Item | Claimed state | Verified state | Evidence | Verdict |
| --- | --- | --- | --- | --- |
| L10: HEAD is `aa43c1c`, tree clean, local matches `origin/main` | current handoff state | HEAD is `a39e9a7`, the commit that added `NEXT_STEPS.md` itself; tree is clean | `git rev-parse HEAD` returns `a39e9a7312c0890aef0040576bc9d60052fdea73`; `git status` empty `[RAN]` | STALE |
| L11-12: source repo `RT-Activity-Predictor` has received no writes | untouched | Not checkable from this clone. No remote points at it, and the brief forbids touching it. `ORIGIN.md:14-19` records the intent | `git remote -v` shows only `origin https://github.com/TanishDevs11/RT-plm-benchmark.git` `[RAN]` | BLOCKED: needs a read of the source repository's `pushedAt`, which this review did not perform |
| L14-15: seed 42 throughout; a baseline ladder rerun changed only `seconds` | deterministic | Exactly right. Rerunning `bench/baselines.py` changed `bench/results/baseline_ladder.json` in three `seconds` fields and nothing else; `baseline_ladder.md` was byte-identical | `python bench/baselines.py` exit 0, then `git diff bench/results/baseline_ladder.json` shows only `seconds` `[RAN]` | CONFIRMED |
| L21-49: ESM-1v mean-pooled NOT RUN, blocked on host memory | not run | Not run. `bench/cache/pooled_esm1v.npz` is absent; `bench/results/representations.md:82` lists it blocked with exactly that reason | `ls bench/cache` shows only `pooled_esm2_{8M,35M,150M,650M}.npz` `[RAN]`; `bench/results/representations.md:82` `[READ]` | CONFIRMED |
| L51-65: ProtT5 NOT RUN; whether `transformers` installs on 3.14 was never determined | unknown | `transformers` is absent, recorded as observed in `bench/COMPUTE_FEASIBILITY.md:23`. Whether it installs is still unknown: this review did not attempt the install, since that modifies the environment | `bench/COMPUTE_FEASIBILITY.md:23` `[READ]` | CONFIRMED as to status; the install question remains BLOCKED and is still five minutes of work |
| L67-73: inverse folding NOT RUN; structures present | not run | Not run. `data/structures/` holds 57 PDB files | `ls data/structures \| wc -l` returns 57 `[RAN]` | CONFIRMED |
| L75-81: zero-shot masked marginals NOT RUN, wall clock not dependency | not run | Not run. No masked-marginal code exists in `bench/`; `bench/results/baseline_ladder.md:23` records it blocked | `grep -rn "masked" bench/*.py` returns nothing `[RAN]`; `bench/results/baseline_ladder.md:23` `[READ]` | CONFIRMED |
| L85-97: `reproduce.py` unverified end to end; "confirm it ends with `all stages completed`" | pending verification | The stated done-criterion is unreachable. `bench/search_null.py:267` returns `0 if self_check_passed else 1`, and `self_check_passed` is `abs(0.9121 - 0.848) <= 0.05`, which is false and deterministic. `reproduce.py:31` runs that script as a stage and `reproduce.py:51-58` records any non-zero exit as a failure, so the run will always end `FAILED search-capacity null sweep (exit 1)` | `bench/search_null.py:49,199-202,267` `[READ]`; `reproduce.py:31,49,51-58` `[READ]`; the 0.9121 single draw reproduced at `[RAN]` 0.9121351301 | CONTRADICTED |
| L99-101: `make` not installed, Makefile never exercised | untested | `make` is absent. Beyond untested, `make reproduce` and `python reproduce.py` are not the same sequence: `Makefile:40-44` omits `bench/search_null.py` entirely, while `reproduce.py:31` includes the full sweep | `make --version` not found `[RAN]`; `Makefile:40-44` vs `reproduce.py:25-35` `[READ]` | CONFIRMED that it is untested; the claim that it runs "the same sequence" (`README.md:95`, `PROGRESS.md:152`) is CONTRADICTED |
| L105-114: `bench/data_expansion.md` leaves every quantitative field `UNVERIFIED` | deliberate gaps | Exactly so. Nine `UNVERIFIED` markers across the five candidate sources | `grep -c UNVERIFIED bench/data_expansion.md` returns 9 `[RAN]` | CONFIRMED |
| L126-128: `topology_features.csv` omits the `-RT` suffix, harmonized at load | recorded, not fixed at source | Confirmed and documented in `bench/names.py:12-17`. The source CSV is unchanged | `bench/names.py:12-17` `[READ]` | CONFIRMED |
| L129-131: `Line1-RT` has no predicted structure | missing, imputed in fold | Confirmed. `NO_STRUCTURE = ("Line1-RT",)` at `bench/names.py:41` and no `Line1-RT.pdb` exists | `bench/names.py:41` `[READ]`; `ls data/structures` `[RAN]` | CONFIRMED |
| L131-132: `Vp-96.pdb` duplicates `Vp96-RT.pdb`, 57 files cover 56 RTs | duplicate skipped | Confirmed. Both files present, documented at `bench/names.py:20-23` | `bench/names.py:20-23` `[READ]`; both files present `[RAN]` | CONFIRMED |
| L134-138: `data/esm2_embeddings.npz` has no generator, but "the rebuild does not depend on it" | harmless orphan | Half right and half wrong. The file has no generator, confirmed. But `bench/baselines.py:62` loads it **unconditionally**, and it feeds two published ladder rows: baseline 5, the family prior, via `bench/baselines.py:169`, and baseline 10, raw ESM-2 plus logistic regression, via `bench/baselines.py:244,264`. `bench/representations.py:382` uses it only as a fallback that does not fire. So the rebuild does depend on it, and the suggested remedy of deleting it would break `bench/baselines.py` | `bench/baselines.py:62,169,244,264` `[READ]`; `bench/representations.py:380-384` `[READ]` | CONTRADICTED |
| L136-138 remedy: "locate the script or delete the file" | open choice | A third option is available and better: the inherited file is numerically the same array as the regenerated one. Max absolute elementwise difference between `data/esm2_embeddings.npz` and `bench/cache/pooled_esm2_650M.npz` is 2.38e-06 at float32, mean 6.57e-08, with identical name order | `[RAN]` numpy comparison of the two archives | UNSUPPORTED as stated: the file is effectively reproducible, which neither the claim nor `legacy_submission/README.md:36-39` allows for |
| L145-151 item 1: seven of ten representations score exactly 0.0000 while PR-AUC reaches 0.64 | metric pathology | Confirmed. `bench/results/representations.md:16-22` shows seven rows at CLS 0.0000, and the handcrafted row reaches PR-AUC 0.6436 at CLS 0.0000 | `bench/results/representations.md:16` `[READ]` | CONFIRMED |
| L147-149: noise null still 0.58 at n=200 | scale does not rescue | Confirmed. `bench/results/scale_projection.json` records `null_mean` 0.5794 and `null_p95` 0.6216 at n=200, at K=29 via `bench/scale_projection.py:31,84` | `bench/results/scale_projection.json` `[READ]` | CONFIRMED |
| L152-156 item 2: core-focused variants reached 0.818 family accuracy, the highest | corrections failed | Confirmed. `bench/results/representations.json` records `family_accuracy` 0.8182 for both core-pooled rows, the maximum in the table | `bench/results/representations.json` rows `[READ]`; reproduced by rerunning `bench/representations.py` `[RAN]` | CONFIRMED |
| L157-161 item 3: scale series 0.0074 / 0.1394 / 0.3052 / 0.0000, MRD 0.3419 | non-monotonic, unresolvable | Confirmed exactly, both the four values and the minimum resolvable difference | `bench/results/representations.md:13-18` and `:7` `[READ]`; reproduced `[RAN]` | CONFIRMED |
| L162-166 item 4: `bench/search_null.py` needs only labels, a weight vector, and a selection procedure | dataset-agnostic | Confirmed. `de_blend_null` takes `y_true`, `pe`, `k` and has no dataset-specific coupling; only `load_labels` at `bench/search_null.py:173-178` is repo-specific | `bench/search_null.py:64-102,173-178` `[READ]` | CONFIRMED |
| L170-174: host kills jobs; scripts write outputs only at the end | environment hazard | Not reproduced here. Three scripts ran to completion in this session, two of them concurrently, with no termination. The write-at-the-end design is confirmed by inspection | `[RAN]` `bench/baselines.py`, `bench/representations.py` and a 62-run null sweep all exit 0 | CONFIRMED as a design property; the hazard itself is UNSUPPORTED in this session, which is evidence of nothing either way |
| L182-186: gate G3 not observed, write-up pushed without endorsement | process gap | Consistent with the history. `d74441e` and `aa43c1c` land `README.md` and `WRITEUP.md` with no endorsement commit between them | `git log --oneline` `[RAN]` | CONFIRMED |
| L190-191: ten files classified UNCLEAR by regex-assisted scan, not by reading control flow | needs a second pass | Confirmed. `audit/leakage_report.md:39` totals `UNCLEAR 10`, and `audit/leakage_audit.py` matches on search-marker strings rather than analysing control flow | `audit/leakage_report.md:18-27,39` `[READ]` | CONFIRMED |
| L192-194: 0.4576 clears its own null by only 0.0615 | framing question | Confirmed, and this is the concession that contradicts `README.md:11-13`. `bench/results/baseline_ladder.md:12` shows CLS 0.4576, null p95 0.3961, margin +0.0615 | `bench/results/baseline_ladder.md:12` `[READ]` | CONFIRMED |
| L5-6: "Nothing here affects any number already reported: every result in `WRITEUP.md` was measured" | all write-up numbers measured | Not true of three of them. `WRITEUP.md:126,128,131` carry PR-AUC and weighted Spearman values from the **pre-join-repair** run, while the CLS column in the same rows is post-repair. See section 7 | `WRITEUP.md:126,128,131` against `bench/results/baseline_ladder.md:14-16` `[READ]`; pre-repair values recovered from `git show a2f7c79:bench/results/baseline_ladder.md` `[RAN]` | CONTRADICTED |

---

## 3. Repository inventory

### 3.1 Top-level directories

| Path | Tracked files | Purpose, as determined | Mentioned in `README.md` layout table |
| --- | --- | --- | --- |
| `audit/` | `leakage_audit.py`, `metric_properties.py`, two reports, one figure | Leakage audit and metric properties of the inherited tree | yes |
| `bench/` | protocol, null, baselines, representations, embeddings, names, scale projection, tests, results, figures, four pooled embedding caches, two scoping documents | The rebuild itself | partly: `results/` and five scripts are listed, `embeddings.py`, `scale_projection.py`, `test_protocol.py`, `cache/`, `figures/`, `COMPUTE_FEASIBILITY.md` and `data_expansion.md` are not |
| `data/` | 10 CSV or NPZ files plus 57 PDB structures | Raw inputs, plus two label-derived files the rebuild deliberately ignores | no |
| `evaluation/` | `evaluate.py` | The competition metric implementation, `compute_cls` | no |
| `features/` | `build_esm1v_features.py`, `extract_esm1v_depth.py` | Inherited ESM-1v feature scripts, unquarantined, unreferenced by `bench/` | no |
| `src/` | 26 inherited scripts | Inherited modelling code, unquarantined, unreferenced by `bench/` | no |
| `legacy_leaky/` | `fast_opt.py`, 33 files under `experiments/`, 60+ under `results/`, a README | Quarantined inherited code and artifacts, the object of study | yes |
| `legacy_submission/` | `submission.csv`, `WRITEUP.md`, `README.md` | The submitted artifact | yes |
| `brag-output/` | `brag.jpg`, `brag.mp4` | Promotional video assets inherited from `c162070` | no |
| `.github/workflows/` | `ci.yml` | CI: protocol tests plus the null self-check | referenced in prose at `README.md:112`, not in the table |

`bench/` imports only from `bench/` and `evaluation/`. It never imports from `src/` or
`features/` `[RAN]`, so the un-quarantined inherited code is inert with respect to every
published number. It is, however, still present, tracked, importable, and absent from the
layout table, and `legacy_leaky/README.md:40-44` describes the quarantine only as covering
`experiments/` and `results/`, which is accurate but leaves a reader with no account of
the 28 remaining inherited files.

### 3.2 Presence checklist from the brief

| Item | Present | Evidence |
| --- | --- | --- |
| `ORIGIN.md` | yes | `ORIGIN.md`, 30 lines |
| `provenance` tag | yes | annotated tag `f5ee54a` pointing at `c1620706685d1a29e874031abd62d88a763d241e` `[RAN]` |
| `legacy_leaky/` | yes | present with its own README |
| `legacy_submission/` | yes | present with its own README |
| `audit/` | yes | two scripts, two reports, one figure |
| `bench/` | yes | as above |
| `Makefile` | yes | 47 lines, never exercised, and not equivalent to `reproduce.py` |
| `CITATION.cff` | yes | 21 lines, CFF 1.2.0 |
| licence file | yes | `LICENSE`, MIT |
| `.github/workflows/ci.yml` | yes | runs `bench/test_protocol.py` and `bench/search_null.py --self-check` on Python 3.12 |

One note on CI. It pins Python 3.12 while every published number came from Python 3.14.2
`[READ]` `README.md:102-104`. A green CI badge therefore certifies the protocol tests on a
different interpreter from the one the results were produced on.

### 3.3 Commit log by phase

Rebuild commits, newest first. The inherited history below `c162070` is retained in full,
55 commits, per `ORIGIN.md:8`.

| Commit | Phase landed |
| --- | --- |
| `a39e9a7` | handoff notes, `NEXT_STEPS.md` |
| `aa43c1c` | Phases 6 and 7: scale projection, `reproduce.py`, final write-up |
| `d74441e` | Phase 7: `README.md` and `WRITEUP.md` rewritten on the honest results |
| `26f077b` | Phase 5 complete; baselines corrected after the join repair |
| `f8ceef3` | progress record; inherited RT name join defect repaired |
| `025dbcc` | Phase 3: search-capacity null sweep |
| `098469e` | ESM-2 caches at four scales |
| `90b9b12` | Phase 6 and 7 scaffolding: scale projection, data expansion scoping, CI, licence, Makefile |
| `a2f7c79` | Phases 2 to 4: nested protocol, search-capacity null, baseline ladder |
| `8350b38` | audit: artifacts recovered from the provenance tag |
| `499df30` | Phase 0 and Phase 1: provenance, leakage audit, metric properties, quarantine |
| `c162070` | last inherited commit, the provenance boundary |

All seven phases landed. Work stopped after the write-up, at the point where
`NEXT_STEPS.md` was written. The two things that did not land are end-to-end verification
of `reproduce.py` and the G3 endorsement gate.

### 3.4 Generated reports and results, with regeneration status

| File | Last commit to touch it | Generator | Reruns? |
| --- | --- | --- | --- |
| `audit/leakage_report.md` | `8350b38` 2026-09-29 | `audit/leakage_audit.py` | yes, exit 0, output byte-identical `[RAN]` |
| `audit/metric_report.md` | `499df30` 2026-09-29 | `audit/metric_properties.py` | yes, exit 0, output byte-identical `[RAN]` |
| `audit/figures/cls_ladder.png` | `499df30` 2026-09-29 | `audit/leakage_audit.py` | yes, regenerated `[RAN]` |
| `bench/results/baseline_ladder.md` and `.json` | `f8ceef3` / `aa43c1c` 2026-09-29 | `bench/baselines.py` | yes, exit 0; `.md` identical, `.json` differs only in `seconds` `[RAN]` |
| `bench/results/representations.md` and `.json` | `26f077b` 2026-09-29 | `bench/representations.py` | yes, exit 0; `.md` identical, `.json` differs in 10 lines, all timing `[RAN]` |
| `bench/figures/function_vs_lineage.png` | `26f077b` 2026-09-29 | `bench/representations.py` | yes `[RAN]` |
| `bench/results/search_null.json` | `025dbcc` 2026-09-29 | `bench/search_null.py` | the script runs, but `main()` returns exit 1 by design; the 20-repeat distribution reproduces value for value `[RAN]` |
| `bench/figures/search_null_capacity.png` | `025dbcc` 2026-09-29 | `bench/search_null.py` | same caveat |
| `bench/results/scale_projection.json` | `aa43c1c` 2026-09-30 | `bench/scale_projection.py` | not rerun in this session |
| `bench/results/*_log.txt` | never committed | the four benchmark scripts | **gitignored** by `.gitignore:18`, so they exist only on this machine and are absent from a fresh clone |
| `bench/cache/per_residue_esm2_650M.npz`, `attention_esm2_150M.npz` | never committed | `bench/embeddings.py` | **gitignored** by `.gitignore:14-15`. Without them `bench/representations.py` reports the two core-pooled rows as blocked, so `representations.md` as published cannot be regenerated on a fresh clone without first running the heavy extraction |

### 3.5 Candidate fitted constants outside `legacy_leaky/`

Scanning every `.py`, `.md`, `.yml`, `.cff`, `.txt`, `.toml` and `.cfg` file outside
`legacy_leaky/`, `.git/`, `__pycache__/`, `brag-output/` and `data/structures/` for a
floating point literal with five or more decimal places `[RAN]`:

| File | Line | Constant | Assessment |
| --- | --- | --- | --- |
| `ORIGIN.md` | 17 | 0.975372 | a quoted historical commit-message CLS, not a constant in code |
| `audit/leakage_report.md` | 68, 72, 74, 75, 76, 77, 78, 79, 80 | 0.652790, 0.911812, 0.962015, 0.965997, 0.972765, 0.973738, 0.974063, 0.975314, 0.975372 | quoted commit-message CLS values in the ladder table, generated by `audit/leakage_audit.py` |
| `legacy_submission/WRITEUP.md` | 57, 58, 59 | 0.985714, 0.965244, 0.975372 | the submitted artifact's own reported metrics; this file is the object of study, not rebuild code |

**Zero hits in any executable file of the rebuild.** `bench/`, `audit/`, `evaluation/`,
`src/`, `features/` and `reproduce.py` contain no high-precision float literal at all. The
one hardcoded decimal worth naming is not caught by that filter because it has only three
places: `REFERENCE_EXPECTED = 0.848` at `bench/search_null.py:49`. It is not a fitted
constant; it is an expectation inherited from the project brief, and section 5 shows it is
the entire source of the 0.848 versus 0.912 discrepancy.

---

## 4. Leakage audit verification

All five claims in the brief are confirmed.

**4.1 `fast_opt.py` optimizes `-compute_cls(seq["active"], y_score, seq["pe_efficiency_pct"])`
over all 57 rows. CONFIRMED.**
`legacy_leaky/fast_opt.py:45-69` defines `obj_func`, which at lines 61-66 calls
`compute_cls(seq["active"].values, y_score, seq["pe_efficiency_pct"].values)` and returns
`-res["cls"]` `[READ]`. `seq` is the full label table; no fold, mask or held-out split
appears anywhere in the file. Line 68 sets `bounds = [(-1.5, 1.5) for _ in branch_names] +
[(0.2, 1.5)]` and line 83 hands it to `differential_evolution` with `maxiter=260`,
`popsize=10`, `seed=42`. Worse than a single pass: lines 71-79 parse the previously fitted
`RANK_POWER` and `RANK_BLEND_WEIGHTS` back out of
`experiments/calibrated_lofo_predictions.py` and pass them as `x0`, so each run resumes the
previous run's hill climb on the test labels.

**4.2 `RANK_POWER` and a 29-entry `RANK_BLEND_WEIGHTS` at 16 significant figures.
CONFIRMED.**
`legacy_leaky/experiments/calibrated_lofo_predictions.py:39` reads
`RANK_POWER = 1.4906030108132808`, seventeen significant figures `[READ]`. The
`RANK_BLEND_WEIGHTS` dictionary immediately following holds exactly 29 entries `[RAN]`,
each at 16 or 17 significant figures, for example `"both_zsig_l1": 1.479724996815146` and
`"esm_subcluster": -0.035396069720866286`. The component names match the 29 keys of
`legacy_leaky/results/component_arrays.json` one for one `[RAN]`.

**4.3 `materialize_final_submission.py` retrains nothing and thresholds a stored CSV at
1.92. CONFIRMED.**
The entire file is 42 lines `[READ]`. Line 8 sets `ACTIVE_SCORE_THRESHOLD = 1.92`. Line 31
reads `results/calibrated_predictions_selected_features.csv`, lines 17-19 binarise
`predicted_score >= 1.92`, and lines 33-34 write the result back over the source CSV and
out to `submission.csv`. There is no model, no fit, no split, and no import of any learner.

**4.4 `shuffle_labels_test.py` shuffles labels only inside the base RandomForest, so it
cannot detect selection leakage in the downstream blend. CONFIRMED.**
Line 43 shuffles with `y.sample(frac=1, random_state=42)`, lines 57-79 run a
`LeaveOneGroupOut` loop over a single `RandomForestClassifier`, and line 99 scores the
result with `compute_cls` `[READ]`. The file is 116 lines and contains no reference to
`RANK_BLEND_WEIGHTS`, `differential_evolution`, `component_arrays`, or any blend `[RAN]`.
The blend search is downstream of everything this test perturbs, so a null result from it
carries no information about the leakage that produced 0.9754. `legacy_leaky/README.md:37-40`
already states this correctly: it is a real test of the wrong thing.

**4.5 The commit ladder from `CLS - 0.485` to `CLS - 0.975372` is intact and reachable.
CONFIRMED.**
`git merge-base --is-ancestor 1633ecd HEAD` and the same for `248a1d2` both succeed `[RAN]`.
`git log --oneline 1633ecd..248a1d2` returns 23 commits `[RAN]`.
`audit/leakage_report.md:57-80` tabulates the 20 commits carrying a CLS in the subject,
first 0.4380 at `839f70d`, last 0.9754 at `248a1d2` `[READ]`, and the audit script
regenerates that table byte-identically `[RAN]`.

**4.6 Two findings the audit did not make.**

First, **the submitted vector's provenance is not the artifact the audit's parameter table
points at.** I scored every prediction CSV under `legacy_leaky/results/` against the 57
labels `[RAN]`. `legacy_submission/submission.csv` scores CLS 0.9753718, and three stored
CSVs are elementwise identical to it: `calibrated_predictions_selected_features.csv`,
`lambdarank_residual_candidate.csv` and `quantum_listwise_candidate.csv`. The companion
`legacy_leaky/results/lambdarank_residual_candidate.json` records `cls`
0.9753717678425584 with seven per-fold configs, every one of them
`{"mode": "add", "lambda_weight": 0.0, ...}` `[RAN]`, meaning that stage selected a blend
weight of zero on all seven folds and passed the base vector through unchanged. That
artifact appears nowhere in `audit/leakage_report.md`'s free-parameter table.

Second, **the 62-parameter artifact the write-up leans on is not the submitted one.**
`audit/leakage_report.md:48` attributes 62 free parameters to
`legacy_leaky/results/de_best_weights.json` `[READ]`. That file's own recorded
`best_cls` is 0.8977959946535047 `[RAN]`, not 0.9754. Meanwhile the recovered
`component_weight_search_best.json` is recorded at 30 parameters, 29 weights plus one power
`[READ]` `audit/leakage_report.md:51`, which is the search `README.md:30-31`,
`WRITEUP.md:19-23` and `legacy_leaky/README.md:11-16` all describe as the one that produced
the submission. This matters for section 5.

For completeness: applying the frozen `RANK_BLEND_WEIGHTS` and `RANK_POWER` to
`component_arrays.json` reproduces CLS 0.8350, not 0.9754 `[RAN]`, so the constants frozen
into `calibrated_lofo_predictions.py` are an intermediate state of the climb rather than
its endpoint. The exact free-parameter count behind 0.9754 is therefore **not established
anywhere in this repository**, and no number in this review asserts one.

---

## 5. Search-capacity null: resolution

### 5.1 What the reported K=29 figure actually is

Reading `bench/search_null.py` end to end resolves the 0.848 versus 0.912 discrepancy
cleanly, and the answer is that neither is a contested measurement.

**0.848 is not a measurement in this repository at all.** It is
`REFERENCE_EXPECTED = 0.848`, a literal at `bench/search_null.py:49` `[READ]`, carried in
from the project brief as a prior. Lines 196-202 compare a single seed-42 draw against it
with `REFERENCE_TOLERANCE = 0.05` and print PASS or FAIL. The stored result of that
comparison is `"self_check_passed": false`, `"deviation": 0.0641...` `[READ]`
`bench/results/search_null.json`.

**0.912 is the single seed-42 draw**, stored as `observed_single_draw`
0.9121351300603567 `[READ]`. I reran it: 0.9121351301 `[RAN]`, exact to ten places.

**What the published documents report as "the K=29 null" is a p95 over 10 repeats.**
`README.md:39` and `WRITEUP.md:40` both give 0.9340 `[READ]`, which is the
`p95` field of the `k_sweep` entry for K=29, computed at `n_repeats=10` via
`main(sweep_repeats=10)` `[READ]` `bench/search_null.py:181,214-223`. A second and more
precise estimate exists in the same file, the 20-repeat `reference.distribution`, whose
p95 is 0.9501 `[READ]`. A third exists in `bench/results/scale_projection.json`, an 8-repeat
K=29 null at n=57 with p95 0.9061 `[READ]`. **Three different K=29 p95 values are in
circulation inside this repository: 0.9061, 0.9340 and 0.9501**, differing only by repeat
count. The documents quote the middle one without saying which.

### 5.2 Are the noise components rank-percentile transformed?

**Yes, and it matches the real procedure exactly.** `bench/search_null.py:82` builds
`ranks = np.vstack([_rank_percentile(noise[i], n) for i in range(k)])` before the objective
ever sees them, and `_rank_percentile` at lines 59-61 is
`rankdata(v, method="average") / (n + 1.0)` after `nan_to_num` `[READ]`. That is
character-for-character the same computation as `global_rank_percentile` at
`legacy_leaky/fast_opt.py:35-38`, which `fast_opt.py:40` applies to every real component
before blending `[READ]`. The null is faithful on this point.

The brief asserts that this choice changes the answer. **It does not, materially.** I ran
the same sweep on raw Gaussian components with no rank transform `[RAN]`: at K=29 the mean
moves from 0.8662 to 0.8635 and at K=50 from 0.9187 to 0.9221. Both shifts are far inside
one standard deviation. The transform is the right choice because it matches the procedure
under audit, not because it changes the conclusion.

Two deviations from `fast_opt.py` remain, both understating the null. The null searches
from scratch where `fast_opt.py:90` seeds `x0` from fitted constants, documented at
`bench/search_null.py:16-18`. And `fast_opt.py:50` skips zero-weight components, a
numerically irrelevant short-circuit the null omits.

### 5.3 The full distribution, measured in this session

All values `[RAN]`. Raw values in `bench/results/null_distribution.csv`, 62 rows.
Configuration is `bench/search_null.py` unchanged: bounds [-1.5, 1.5], power [0.2, 1.5],
`maxiter=260`, `popsize=10`, `tol=1e-4`, `polish=False`, `updating="deferred"`,
`workers=1`. Repeat `r` uses `de_seed = 42 + r` and `noise_seed = 1042 + r`, which is the
scheme `bench/search_null.py:117` already uses.

| Variant | K | n | mean | sd | min | median | p95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank-percentile | 29 | 20 | **0.8662** | 0.0534 | 0.7680 | 0.8702 | **0.9501** | 0.9503 |
| rank-percentile | 50 | 20 | 0.9187 | 0.0324 | 0.8653 | 0.9240 | 0.9716 | 0.9737 |
| raw Gaussian | 29 | 10 | 0.8635 | 0.0710 | 0.7697 | 0.8427 | 0.9627 | 0.9751 |
| raw Gaussian | 50 | 10 | 0.9221 | 0.0333 | 0.8758 | 0.9213 | 0.9597 | 0.9614 |

Single seed=42 draw, rank-percentile: **K=29 0.9121351301**, **K=50 0.9666228968**.

My twenty K=29 values are **identical** to the twenty stored in
`bench/results/search_null.json` under `reference.distribution.values` `[RAN]` verified by
`np.allclose` on the sorted arrays. The instrument is deterministic and the published
distribution reproduces.

Against this distribution, 0.848 sits 0.35 standard deviations below the mean and between
the 25th and 30th percentiles of the 20 draws. It is an unremarkable member of the
distribution, not its centre.

### 5.4 The corrected comparison

The brief's argument is sound and the repository's own evidence supports it. Every
document that describes the submitted search describes a 29-weight plus one-power blend:
`README.md:30-31`, `WRITEUP.md:19-23`, `legacy_leaky/README.md:11-16`, and the code at
`legacy_leaky/fast_opt.py:68` `[READ]`. That is **30 free parameters**, and it must be
compared against the K=29 null. The K=50 comparison is justified in the write-up by
`audit/leakage_report.md:48`'s 62-parameter count, and section 4.6 shows that count belongs
to `de_best_weights.json`, an artifact whose own recorded score is 0.8978, not the
submission.

**The honest sentence, with both numbers from my own run:**

> The submitted blend, a search over 29 weights and one power exponent, scored CLS 0.9754
> against a K=29 search-capacity null distribution whose mean is **0.8662** and whose p95 is
> **0.9501**. The margin over the p95 is **+0.0252**. None of 20 null draws reached 0.9754.

That is a positive margin, and the K=29 comparison is therefore **weaker** than the
published K=50 one, which shows the submission failing to clear. The leakage conclusion
nonetheless survives, for three reasons that should be stated together rather than replaced
by a larger K:

1. The margin of +0.0252 is roughly a third of the 0.0794 bootstrap interval width on the
   submitted vector `[READ]` `audit/metric_report.md:58`, and less than a tenth of the
   0.3419 minimum resolvable difference `[READ]` `bench/results/representations.md:7`. It
   is not a resolvable margin.
2. The null searches from scratch; `fast_opt.py` resumed from its own previous optimum
   across many runs. The null is a floor, not a fair match.
3. The submitted score is the value of an objective maximised against its own test labels.
   That is established by section 4.1 on its own and needs no null at all.

### 5.5 Every place the comparison is made incorrectly

| File | Line | Text | Problem |
| --- | --- | --- | --- |
| `README.md` | 37-40 | table "Free parameters / CLS on noise (p95)" with rows 29 and 50, 50 bolded | Sets a K=50 null beside a submission the same file describes at line 30-31 as a 29-weight plus power search |
| `README.md` | 42-45 | "stored search artifacts contain up to 62 fitted parameters ... The submission scored 0.9754. Its margin ... is about 0.025" | The 0.025 is 0.9754 minus the K=50 p95. At K=29 the margin is +0.0252 over the p95, a positive margin, not a shortfall |
| `WRITEUP.md` | 35-41 | table of p95 by K, ending at 50 bolded 0.9727 | same substitution |
| `WRITEUP.md` | 43-47 | "At 50 parameters the search reaches 0.9727 on noise. My submission scored 0.9754 ... The reported score sits inside its own noise floor" | The claim is carried by the K=50 row; at K=29 the submission sits above the p95 |
| `WRITEUP.md` | 294-296 | "A 62-parameter search on an effective sample of 11 reaches 0.9727 on pure noise. The submitted score does not clear that" | Attributes 62 parameters to the submitted search. The 62 belongs to `de_best_weights.json` at CLS 0.8978 |
| `PROGRESS.md` | 64, 70 | K=50 row, and "fifty reach the submitted score" | same substitution |
| `WRITEUP.md` | 286 | "drops what a **30-parameter** search can manufacture from noise from 0.86 to 0.58" | Correct and K=29-based, and therefore inconsistent with lines 43-47 of the same document, which use K=50 for the same submission |

---

## 6. Representation findings

### 6a. Family classification, with the missing control supplied

**The control does not exist in the repository.** No script computes family accuracy from
3-mer composition or from length alone; `lineage_confound` at
`bench/representations.py:277-299` classifies only the representation under test `[READ]`.
The 0.80 figure has been published at `README.md:59`, `WRITEUP.md:188` and
`PROGRESS.md:119` with only the majority baseline attached.

Reproduced here as the brief specifies: families with at least 5 members, which keeps 56 of
57 rows and drops the singleton `Unclassified` family `[RAN]`; stratified 5-fold;
`LogisticRegression(max_iter=5000)`; features standardized; `random_state=0`.

| Representation | 5-fold family accuracy, `random_state=0` | Brief's expectation | Same at `random_state=42` |
| --- | --- | --- | --- |
| ESM-2 650M mean-pooled embedding | **0.8212** `[RAN]` | 0.821 | 0.8000 `[RAN]` |
| 3-mer composition, frequency-normalized, standardized | **0.6242** `[RAN]` | 0.571 | 0.6091 `[RAN]` |
| Length only | **0.5197** `[RAN]` | 0.520 | 0.5182 `[RAN]` |
| Majority baseline | **0.3214** `[RAN]` | 0.321 | 0.3214 |

Three of four match the brief. The 3-mer row does not, and the cause is the encoding. I
tested four variants `[RAN]`: frequency-normalized and standardized gives 0.6242, raw
counts standardized gives **0.5697**, raw counts unstandardized gives 0.7152, frequencies
unstandardized gives 0.3212. The brief's 0.571 is reproduced by the raw-counts-standardized
variant. Reported as a disagreement rather than resolved: the repository specifies no 3-mer
encoding for this control, so there is no repository evidence to prefer one.

**The claim survives on every variant tested.** ESM-2 at 0.8212 clears the best 3-mer
variant by +0.106 and the brief's variant by +0.252. The statement that the embeddings
encode lineage beyond what raw sequence composition captures **is supported**, and should
be published with this control table attached rather than with the majority baseline alone.

Note that `README.md:59` reports 0.8000, not 0.8212. That is not an error: it is the same
measurement at `random_state=42`, which is the repository's seed, and it is backed by
`family_accuracy` 0.8000 in `bench/results/representations.json` `[READ]`. The gap between
0.8000 and 0.8212 is fold-assignment noise on 56 rows and should not be read as a
discrepancy.

**Embedding PC1 against `protein_length_aa`:** Spearman **-0.7681**, p = 3.1e-12 `[RAN]`,
on standardized ESM-2 650M embeddings with `PCA(random_state=0)`. This reproduces the
published -0.7681 exactly `[READ]` `README.md:61`. The sign is a PCA convention and the
magnitude is what carries. Two cautions. First, **no script in this repository computes
this number.** There is no `spearmanr` call in `bench/` or `audit/`, no results file records
it, and the only trace is a docstring at `bench/representations.py:62` `[RAN]`. It is an
orphan published in three documents, which contradicts `PROGRESS.md:4-5`, "Every number
here came from a script in this repository and can be regenerated." Second, it is
preprocessing-sensitive: on centred but unstandardized embeddings PC1 correlates at +0.6198
`[RAN]`. The published figure needs its preprocessing stated alongside it.

### 6b. Do PLM embeddings help activity prediction, and how strongly to say it

**The repository's own nested protocol supports the stronger phrasing, and by a wider
margin than the brief's 0.179 does.**

The exact number: raw mean-pooled ESM-2 through the nested protocol scores **CLS 0.0000**,
at PR-AUC 0.2877 and weighted Spearman 0.0000 `[READ]` `bench/results/baseline_ladder.md:17`,
row 10, and the same 0.0000 appears for ESM-2 650M in
`bench/results/representations.md:18`. The reference is `protein_length_aa` used directly as
the score with no training at all, CLS **0.4416** `[READ]`
`bench/results/baseline_ladder.md:9`. I reran both scripts and both values reproduce `[RAN]`.

So the accurate statement is the first of the two the brief offers: **out of family, raw
mean-pooled ESM-2 embeddings perform worse than a single scalar already present in the input
file, not merely fail to beat it.** "Did not convincingly beat" understates what was
measured. That phrase does not appear anywhere in this repository `[RAN]`; it belongs to the
external summary the brief quotes, and the repository's own wording at `README.md:62-63` is
already correct: "far below the length-only baseline of 0.4416."

On the brief's 0.179 figure: **it does not reproduce here, and neither does its
comparator.** Running a direct, non-nested LOFO logistic regression on raw mean-pooled
embeddings `[RAN]` gives CLS 0.0000 at every ESM-2 scale, 8M, 35M, 150M and 650M. Running
the same direct LOFO logistic regression on length alone gives CLS **0.1031**, not 0.442.
The 0.442 in the brief is length used as a score with no training; the 0.179 is a trained
model. Pairing them compares a trained representation against an untrained scalar. The
repository does that comparison correctly, by running both through the same protocol, and
its answer is 0.0000 against 0.4416.

One caveat that belongs with the strong phrasing whenever it is used. CLS is a harmonic
mean whose weighted Spearman term floors at zero, so 0.0000 is a floor value and not a
measured distance below the baseline. Seven of ten representations hit it `[READ]`
`bench/results/representations.md:16-22`, and the handcrafted row reaches PR-AUC 0.6436
while scoring exactly 0.0000. The defensible sentence is: *out of family, raw mean-pooled
ESM-2 embeddings score at the floor of this metric, below a zero-training length baseline,
on a benchmark whose minimum resolvable difference is 0.3419.* No file currently uses the
stronger claim without a number behind it; `README.md:62-63` and `WRITEUP.md:193-194` both
carry 0.0000 and 0.4416.

---

## 7. Claims not supported by this verification

Ordered by how much they affect what a reader concludes.

**7.1 `README.md:11-13` and `WRITEUP.md:10-13`. CONTRADICTED by the repository's own table.**
"No method tested beats using `protein_length_aa` as the score with no training at all, and
no method clears the score its own selection procedure reaches on pure noise." Both halves
fail. `bench/results/baseline_ladder.md:12` records 3-mer cosine to nearest training active
at CLS 0.4576 against length's 0.4416, marked `yes` in the "Beats length" column, with null
p95 0.3961 and margin **+0.0615** `[READ]`. Two further rows also clear their nulls: length
itself at +0.0455 and the family prior at +0.0199 `[READ]` `bench/results/baseline_ladder.md:9,13`.
`README.md:17` prints the 0.4576 row six lines below the sentence that denies it.
`NEXT_STEPS.md:192-194` shows the author is aware. The sentence as written is false, and
`WRITEUP.md:162`'s narrower claim, "Every margin is negative", is true of the representation
table only and should not have been generalized.

**7.2 `WRITEUP.md:43-47,294-296`, `README.md:42-45`, `PROGRESS.md:64,70`. UNSUPPORTED.**
The K=50 null is set against a submission the same documents describe as a 30-parameter
search, on the strength of a 62-parameter count that belongs to a different artifact scoring
0.8978. Detail and the corrected sentence in section 5.

**7.3 `WRITEUP.md:126,128,131,140` and `PROGRESS.md:79,80,83`. CONTRADICTED.**
The baseline ladder tables in both documents carry pre-join-repair PR-AUC and weighted
Spearman beside post-repair CLS values:

| Row | Write-up PR-AUC / wSp | `baseline_ladder.md:14-16` PR-AUC / wSp |
| --- | --- | --- |
| handcrafted + RandomForest | 0.7810 / 0.3755 | **0.8288 / 0.2888** |
| handcrafted + ExtraTrees | 0.6830 / 0.0856 | **0.6948 / 0.1036** |
| handcrafted + logistic regression | 0.6427 / 0.0000 | **0.6533 / 0.0000** |

The write-up's values are exactly those at `git show a2f7c79:bench/results/baseline_ladder.md:14-16`
`[RAN]`, the pre-repair snapshot. Only the CLS column was updated. `WRITEUP.md:140` repeats
the stale 0.6427 in prose. `PROGRESS.md:86` asserts "All rows are from the post-fix run",
which is false of its own table three lines above.

**7.4 `NEXT_STEPS.md:93-97`. CONTRADICTED.**
"`python reproduce.py` ... confirm it ends with `all stages completed`" is unreachable.
`bench/search_null.py:267` returns 1 whenever the self-check fails, the self-check compares
a deterministic 0.9121 against the hardcoded 0.848 at tolerance 0.05, and `reproduce.py:51-58`
turns any non-zero exit into a recorded failure. More memory will not change this.

**7.5 `WRITEUP.md:332-336`, `NEXT_STEPS.md:134-138`. CONTRADICTED.**
"The rebuild does not depend on it" is false of `data/esm2_embeddings.npz`.
`bench/baselines.py:62` loads it unconditionally and it feeds published ladder rows 5 and 10
via lines 169 and 244 `[READ]`. Deleting the file, offered as a remedy at
`NEXT_STEPS.md:137`, breaks `bench/baselines.py`. Related: `legacy_submission/README.md:36-39`
calls it an artifact of unknown provenance that `make reproduce` cannot regenerate. Unknown
provenance is right; irreproducible is not. It matches `bench/cache/pooled_esm2_650M.npz` to
2.38e-06 max elementwise difference at float32 `[RAN]`.

**7.6 `README.md:61`, `WRITEUP.md:191`, `PROGRESS.md:121`. UNSUPPORTED by any artifact.**
Spearman -0.7681 between embedding PC1 and `protein_length_aa` has no generator in the tree
`[RAN]`. I reproduce it exactly under one specific preprocessing and get +0.6198 under
another, so the figure is correct but its recipe is unrecorded. This also contradicts
`PROGRESS.md:4-5`.

**7.7 `README.md:95`, `PROGRESS.md:151-152`. CONTRADICTED.**
"`make reproduce` runs the same sequence" as `reproduce.py`. `Makefile:40-44` runs `test`,
`selfcheck`, `audit`, `embeddings`, then baselines, representations and scale projection.
`reproduce.py:25-35` additionally runs `bench/search_null.py`, the full sweep. The Makefile
target omits the project's central instrument.

**7.8 `README.md:52`. OVERSTATED.**
"Every score in this repository carries one, plus a bootstrap interval." True of
`bench/results/baseline_ladder.md` and `representations.md`. Not true of the three
representation findings at `README.md:59-63`, which carry neither a null nor an interval,
and not true of the family accuracies in the representation table.

**7.9 `WRITEUP.md:78-81`. OVERSTATED.**
"The expected 0.848 was correct; it describes the centre of the distribution." Against the
20-repeat distribution, mean 0.8662 and median 0.8702 `[RAN]`, 0.848 sits about 0.35
standard deviations below the mean, between the 25th and 30th percentiles. It is inside the
distribution, not at its centre. The reasoning in that section, that the fix is to report
the right quantity rather than tune the procedure, is correct and should be kept.

**7.10 `WRITEUP.md:100` against `WRITEUP.md:279`. AMBIGUOUS, not wrong.**
The same document gives "Bootstrap 95 percent CI width" as 0.0794 in one table and 0.2017 at
n=57 in another. They are different quantities: the first is on the fixed submitted vector
`[READ]` `audit/metric_report.md:50-58`, the second is a resampled quantity from
`bench/scale_projection.py`. Nothing labels the difference, and a reader comparing the two
tables will conclude one of them is wrong.

**7.11 `PROGRESS.md:4-5`. CONTRADICTED.**
"Every number here came from a script in this repository and can be regenerated." Falsified
by 7.6, and by the stale PR-AUC values in 7.3, which came from a superseded run.

**7.12 Inventory gaps, no claim violated.**
`README.md:72-83`'s layout table omits `src/` (26 tracked inherited scripts), `features/`
(2), `data/`, `evaluation/` and `brag-output/`. `bench/` is verified not to import from
`src/` or `features/` `[RAN]`, so nothing published is affected, but a reader auditing the
quarantine has no account of 28 inherited files sitting outside it.

**7.13 Reproducibility gap, no claim violated.**
`.gitignore:14-15,18` excludes the per-residue and attention caches and all four run logs.
A fresh clone can regenerate `baseline_ladder.md` but not `representations.md` as published,
because the two core-pooled rows and the attention-pooled row need caches that only
`bench/embeddings.py` produces, and that is the heavy stage.

---

## Appendix: what was executed in this session

| Command | Exit | Effect |
| --- | --- | --- |
| `python bench/test_protocol.py` | 0 | all 6 tests pass, peeking detected on 5 of 7 families |
| `python bench/search_null.py --self-check` | 0 | determinism, above-zero noise score, capacity grows with K |
| `python audit/leakage_audit.py` | 0 | report regenerated byte-identical, restored |
| `python audit/metric_properties.py` | 0 | report regenerated byte-identical, restored |
| `python bench/baselines.py` | 0 | `.md` identical, `.json` differs in `seconds` only, restored |
| `python bench/representations.py` | 0 | `.md` identical, `.json` differs in timing only, restored |
| null re-derivation, 62 differential evolution runs | 0 | wrote `bench/results/null_distribution.csv` |
| family-classification control, 4 representations x 2 seeds | 0 | section 6a table |
| direct LOFO logistic regression, 4 ESM-2 scales plus length | 0 | section 6b |
| CLS scoring of all `legacy_leaky/results/*.csv` against the 57 labels | 0 | section 4.6 |
| elementwise comparison of the two ESM-2 650M archives | 0 | section 7.5 |

Working tree after the review contains exactly one addition,
`bench/results/null_distribution.csv`, plus this file and `NEXT_ACTIONS.md`. Nothing else
was modified. Nothing was pushed.
