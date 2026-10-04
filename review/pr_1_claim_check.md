# PR #1 claim check

Every factual claim added by PR #1, verified against an artifact in this repository.
Nothing here is verified against recollection, against the PR description, or against
the review brief.

Verdicts used: CORRECT, OVERSTATED, UNDERSTATED, UNSUPPORTED, CONTRADICTED, AMBIGUOUS.

**Result: 31 claims checked. 23 CORRECT, 6 UNDERSTATED, 1 UNSUPPORTED, 1 AMBIGUOUS, 0
OVERSTATED, 0 CONTRADICTED.** The AMBIGUOUS one, C30, was put to the project owner at
the merge gate and resolved: see the ruling at the end of this document. No number in this PR is fabricated, rounded favourably,
or misattributed to the wrong split regime. The failures are omissions of caveat, which
on this project are treated with the same seriousness as overclaims and were corrected
in the same direction: toward the stronger caveat.

---

## Numbers

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C14a | 4-mer composition PR-AUC **0.6212** | 0.6212 | `bench/results/taskA_representations.md`, classification table, `kmer4` row; `reports/statistical_validation.md:57` | CORRECT |
| C14b | ESM-2 650M PR-AUC 0.4220 | 0.4220 | same table, `esm2_650M` row; `statistical_validation.md:58` | CORRECT |
| C14c | ESM-2 8M PR-AUC 0.3706 | 0.3706 | same table, `esm2_8M` row; `statistical_validation.md:59` | CORRECT |
| C14d | Physicochemical PR-AUC 0.3623 | 0.3623 | same table, `physicochemical` row; `statistical_validation.md:60` | CORRECT |
| C14e | Protein length PR-AUC 0.2599 | 0.2599 | same table, `length` row; `statistical_validation.md:68` | CORRECT |
| C14f | 4-mer permutation p95 0.5398 | 0.5398 | `reports/statistical_validation.md:135`, `kmer4` classification PR-AUC row | CORRECT |
| C14g | ESM-2 650M permutation p95 0.5217 | 0.5217 | `statistical_validation.md:128` | CORRECT |
| C14h | ESM-2 8M permutation p95 0.5676 | 0.5676 | `statistical_validation.md:150` | CORRECT |
| C14i | Physicochemical permutation p95 0.4254 | 0.4254 | `statistical_validation.md:147` | CORRECT |
| C14j | Protein length permutation p95 0.4111 | 0.4111 | `statistical_validation.md:140` | CORRECT |
| C15 | "dataset prevalence is approximately **0.3684**, which is the chance-level reference for PR-AUC" | 0.3684, and it is exactly the stated chance level | `reports/statistical_validation.md:48` ("The chance level for PR-AUC is the positive prevalence, 0.3684") | CORRECT |

**Split-regime attribution, checked specifically.** Every number in C14 is an
out-of-fold value pooled over all 57 rows from the nested leave-one-family-out
protocol, which is the regime the new README's own framing sentence names ("under
family-held-out evaluation", line 120). No figure from the leaky reference split
appears anywhere in the PR. Checked explicitly against
`tasks/taskA_crossfamily/splits/`, which contains a split file labelled leaky, and
against `curation/test_splits.py::test_the_leaky_split_is_labelled_as_leaky_in_the_file`,
which passes. **No leaky-split number is presented as a headline, and no number is
missing its regime.** This was the primary risk the review was set up to catch, and it
did not occur.

**Precision, checked specifically.** All eleven figures are quoted at the four-decimal
precision at which the artifacts store them. None is rounded, and none is rounded in a
favourable direction.

### Numbers the PR omits, where the omission changes the reading

These are not false claims. They are listed here because Phase 2 requires that a
finding carry whatever caveat its artifact carries, and these do not.

| # | What the artifact says | Source | Verdict on the PR's treatment |
| --- | --- | --- | --- |
| C14k | Gaussian noise control column: 0.4458, 0.2889, 0.2581, 0.2643, 0.2474 for the five tabled representations | `reports/statistical_validation.md:57-68` | UNDERSTATED. The column is dropped, which leaves C21 without its numbers. Restored. |
| C14l | **No representation under either head clears the CLS gate.** Highest CLS 0.3739 against search-capacity null p95 0.4433 at one free parameter, and every CLS bootstrap interval includes zero | `bench/results/taskA_representations.md` closing section; `reports/statistical_validation.md:19,21,78` | UNDERSTATED, and this is the most serious single omission in the PR. Restored. |
| C14m | Median minimum resolvable CLS difference **0.4816**, larger than every CLS in the table, so "the CLS ordering is not resolvable on this panel at all" | `reports/statistical_validation.md:162,166` | UNDERSTATED. Absent from the PR. Restored. |
| C14n | Kish effective sample size **11.34** | `audit/metric_report.md:18` (11.338 at `reports/FINAL_REPORT.md:308`) | UNDERSTATED. Absent. Restored. |

The combined effect of C14k through C14n is the one place where the PR, read on its
own, leaves a reader better impressed than the evidence warrants. The table shows
`kmer4` at 0.6212 marked "Survives permutation control: Yes" and nothing anywhere says
that on the composite metric the project actually reports, nothing survives at all and
the ordering cannot be resolved. Corrected by restoration rather than by rewording,
since the PR's own sentences are not wrong.

---

## The 57-enzyme dataset description

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C1 | "**57 experimentally assayed reverse transcriptases**" | 57 | `tasks/taskA_crossfamily/curated.csv`, 57 rows (counted); `reports/reconciliation.md:16-17` | CORRECT |
| C2 | "**21 active RTs**" | 21 | `curated.csv`, `active` sums to 21 (counted); `reports/reconciliation.md:52-53` | CORRECT |
| C3 | "RTs spanning multiple evolutionary families" | 7 families: Retroviral 18, Retron 12, LTR_Retrotransposon 11, CRISPR-associated 5, Group_II_Intron 5, Other 5, Unclassified 1 | `bench/results/taskA_representations.md`, per-family breakdown | CORRECT, though vague where a count was available |
| C4 | "full amino-acid sequences verified against the primary-source supplementary material" | 57 of 57 byte-identical by SHA256 to Table S1 | `reports/reconciliation.md:102-106`; `reports/FINAL_REPORT.md:75` | CORRECT |
| C5 | "binary activity as the primary reproducible target" | Gate G2 ruling: "classification is the primary result", because the binary label is read from Table S1's fill and is reproducible from the file | `bench/results/taskA_representations.md`, preamble | CORRECT |
| C6 | `pe_efficiency_pct` retained but "its provenance is treated as a limitation because the per-enzyme numerical values were not available as a published supplementary table" | Table S1 contains no efficiency values at all; all six supplementary workbooks scanned, none carries them. The column is a digitization of Figure S1A, flagged in-value as `..._UNVERIFIED_DIGITIZED` | `reports/reconciliation.md:118-144` | CORRECT, and carefully phrased |

**The 57-versus-59 and 21-versus-20 question, addressed as required.**
`reports/reconciliation.md:25-47` records that the article's prose says 59 enzymes
while Table S1's assayed block holds 57, and rules that "the panel must be described as
the 57 enzymes Table S1 lists, not as the 59 the paper says". Lines 48 to 92 record
that Table S1's green activity fill gives 21 actives while the prose gives 20, that
both are correct under their own definition, that the difference is M-MLV RT as the PE1
comparator rather than a survey candidate, and that `curated.csv` carries the 21-active
labelling.

**The PR uses the repository's ruled values, 57 and 21. Both correct.** What it does
not do is say which definition it is using, which the review brief requires and which
matters because a reader meeting 59 and 20 in the source paper will otherwise think the
README is wrong. A one-line note naming Table S1's definition and pointing at
`reconciliation.md` was added. The counts themselves were not touched.

---

## Evaluation safeguards

Each of the nine bullets at new README lines 100 to 111, checked against what the code
actually does. This is the category where a README describing a safeguard the
repository does not implement would be the worst possible error, so every bullet was
traced to an implementation, not to a report.

| # | Claim as written | Verified against | Source | Verdict |
| --- | --- | --- | --- | --- |
| C12a | "**Leave-one-family-out evaluation**" | `bench/protocol.py` groups by family at run time; 7 outer folds | `bench/protocol.py`; `bench/test_protocol.py` run in this review, "57 pooled predictions across 7 outer folds" | CORRECT |
| C12b | "Frozen evaluation splits" | `tasks/taskA_crossfamily/splits/` committed; `curation/test_splits.py` proves the frozen file still matches what the harness derives, 13 tests, 0 failures when run in this review | `curation/test_splits.py:228` | CORRECT |
| C12c | "Out-of-fold predictions" | pooled metric computed once over all 57 rows from out-of-fold predictions | `bench/results/taskA_representations.md`, per-family section | CORRECT |
| C12d | "Bootstrap confidence intervals" | 95 percent CI column present for every representation; `N_BOOTSTRAP = 10000` | `bench/protocol.py:48`; `reports/statistical_validation.md:57-110` | CORRECT |
| C12e | "**Dimensionality-matched Gaussian noise controls**" | noise control column per representation, matched on feature count | `reports/statistical_validation.md:57-68` | CORRECT |
| C12f | "Label-permutation controls" | 20 repeats, `active` and `pe_efficiency_pct` permuted together, run on 6 of 12 representations with the subset stated rather than silent | `reports/statistical_validation.md:112-124` | CORRECT |
| C12g | "Search-capacity null experiments" | `bench/search_null.py`; self-check run in this review and passes, including that capacity grows with K | `bench/search_null.py --self-check`; `bench/results/search_null.json` | CORRECT |
| C12h | "Fixed random seeds" | `SEED = 42` in the harness; determinism asserted by test and verified in this review | `bench/protocol.py:46`; `bench/test_protocol.py` "PASS deterministic at seed 42" | CORRECT |
| C12i | "Dataset and artifact checksums" | `sequence_sha256` per row in `curated.csv`; curated-dataset SHA256 in the final report; `reference_sha256` and `plasmid_sha256` in the Task B resolution | `reports/FINAL_REPORT.md:8`; `tasks/taskB_mmlv_dms/reference_resolution.json` | CORRECT |
| C12j | "No selection decisions based on held-out family labels" | the inner loop receives training families only, and the deliberate-peeking positive control is **required to be rejected** | `bench/test_protocol.py`, 6 of 6 passing in this review | CORRECT |

**All nine safeguards are implemented. None is described that does not exist.** This is
the single most important negative result in the claim check.

**One safeguard the repository implements and the PR does not mention:** the peeking
positive control itself, which is the test that proves the leakage check is not inert.
C12j describes the property it protects, but the control is what makes the claim
checkable, and the original README gave it its own section. UNDERSTATED. Restored.

---

## Key findings

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C13 | "PLM embeddings did not improve RT activity prediction over simpler representations under family-held-out evaluation on this dataset" | The best PLM PR-AUC is 0.4220 and fails permutation; the only survivor is `kmer4`, not a language model; on CLS nothing clears its null | `bench/results/taskA_representations.md`; `reports/statistical_validation.md` | CORRECT, and correctly limited to "on this dataset" |
| C16 | "the 4-mer representation was the only one in the reported comparison to survive the permutation control" | `kmer4` classification PR-AUC 0.6212 against permuted p95 0.5398 is the only "yes" among the 6 representations permuted. The hedges "among the tested representations" and "in the reported comparison" are exactly right, because only 6 of 12 were permuted | `reports/statistical_validation.md:112-124,135` | CORRECT. The hedging is precise and was left alone |
| C17 | the 4-mer result is "not evidence that the model discovered a catalytic sequence motif"; predictions correlated with length and family structure; attribution distributed across a high-dimensional space | out-of-fold score against length Spearman **+0.5212**, p 3.23e-05; attribution mass in top 1 percent of features **0.0656** against a 0.0100 feature share; top decile of family-explained features carries 0.1638 against a 0.1000 share | `reports/interpretation.md:75-77` | CORRECT in substance, UNDERSTATED in that all three figures are available and none is quoted. Figures restored |
| C18 | "ESM-2 embeddings strongly captured RT family information, but this did not translate into reliable family-held-out activity prediction" | family accuracy **0.8197** against a **0.3214** majority baseline, rising monotonically 0.7652 / 0.7833 / 0.8030 / 0.8197 with scale; PC1 against length Spearman **-0.7681**; the same 650M representation predicts activity at PR-AUC 0.4220 and fails its own permuted labels | `reports/representation_diagnostics.md:29-32,36,63,76`; `reports/interpretation.md:173-174` | CORRECT but UNDERSTATED. A precisely quantified three-part finding is rendered as "strongly captured". Figures restored |
| C21 | "Some ESM-2 representations exceeded dimensionality-matched Gaussian noise controls but subsequently failed label-permutation tests" | `esm2_650M` margin over noise +0.0535 and `esm2_8M` +0.0022, both "yes" on the noise control; both then fail permutation at 0.4220 against 0.5217 and 0.3706 against 0.5676 | `reports/statistical_validation.md:58,59,128,150` | CORRECT. This is the PR's sharpest methodological point and it is right |
| C31 | Core takeaway: "larger protein language models encoded evolutionary lineage strongly but did not provide evidence of better family-held-out RT activity prediction than simpler sequence representations. Rigorous null and permutation controls were essential" | supported by C18 and C21 above | as above | CORRECT |

**Checked specifically: is any finding stated more strongly than its confidence
interval allows?** No. Every CI in the classification table includes zero for CLS, and
the PR makes no CLS claim at all, so it cannot overstate one. On PR-AUC the PR's only
positive claim is C16, which is hedged to the permuted subset. **No finding in the PR
exceeds its interval.**

**Checked specifically: is any comparison smaller than the minimum resolvable
difference described as a win?** This is the one place the PR comes close. It describes
`kmer4` as surviving the permutation control, which is true and is a pass against a
null rather than a pairwise comparison, so it is not a "win" claim in the prohibited
sense. But the PR nowhere states that the median minimum resolvable CLS difference of
0.4816 exceeds every CLS observed, nor that `reports/statistical_validation.md:254`
records pairwise comparisons as **not resolvable**. Omitting that lets the table read as
a ranking. UNDERSTATED, corrected by restoring C14l through C14n.

---

## The M-MLV variant-effect task

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C27 | "the planned M-MLV RT variant-effect benchmark remains blocked because the required per-variant experimental labels were not publicly available during data acquisition" | "**Status: blocked on the labels, and on nothing else. No benchmark result exists, and none can be computed from the public record.**" The values "were never deposited and are not available from any of the 30 attempts across six route families now logged" | `reports/taskB_mmlv_dms/FINAL_REPORT.md:3-4,27-31` | UNDERSTATED. "Not publicly available during data acquisition" leaves open that they exist and were missed. The artifact says never deposited, and that none can be computed from the public record. Strengthened to the artifact's wording |
| C28 | "The sequence construction, reference resolution, and split design for this task have been prepared, but modelling is intentionally paused until the experimental per-variant labels can be obtained from a verifiable source" | reference resolved and confirmed against a second deposit; **all 1046 variant sequences constructed**; splits frozen; Phase 4 deliberately not run per the G1 ruling | `reports/taskB_mmlv_dms/FINAL_REPORT.md:6-16`; `tasks/taskB_mmlv_dms/variants_unlabelled.csv` | CORRECT. "Intentionally paused" matches the G1 ruling exactly. UNDERSTATED only in omitting the 1046 count, which was added |

**Required check: does the PR state that labels are not obtained and that no result
exists?** Yes, in three separate places (Limitations line 259, Future Work line 276,
Project Status line 331). **Required check: does it imply the task is complete or quote
any number for it?** No. No Task B number appears anywhere in the PR. The phrase
"performance modelling is paused" is accurate and not evasive. This is handled
correctly.

**Reference resolution, checked against `tasks/taskB_mmlv_dms/reference_resolution.json`
as required:**

| brief's stated value | artifact value | field | match |
| --- | --- | --- | --- |
| 498 aa | 498 | `reference_length`, and `rt_frame.pe2dr_length` | yes |
| Addgene 132775 | `addgene_132775_pCMV-PE2.fasta`, with five named substitutions D200N, T306K, W313F, T330P, L603W | `plasmid_fasta`, `addgene_named_substitutions` | yes |
| cross-checked against 174820 | plasmid 174820, pCMV-PEmax, protein identity over the retained region **498/498** | `independent_crosscheck` | yes |

All three confirm. The PR does not state any of them, which is an omission rather than
an error; the specifics were added, since a reader cannot otherwise tell that the
reference question is settled while the label question is not.

**One further omission.** `survey/DATASET_SURVEY.md:11-19` records the measurement that
**no reverse transcriptase deep mutational scan exists in either standardized
collection**: 0 of 217 ProteinGym substitution assays and 0 of 2894 MaveDB target
genes. The PR's Future Work says "A saturated M-MLV RT mutagenesis dataset would allow
a complementary question", which is true but reads as though the dataset is merely
awaited. UNDERSTATED. The survey finding was added, because it is the reason the task is
blocked rather than queued.

---

## Contributors, acknowledgements, and the data source

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C29a | "**Tanish N.**: project design, data pipeline, modelling, benchmarking, statistical analysis, and interpretation" | 108 of 109 commits across all branches are authored by `TanishDevs11` / `Tanish`, covering acquisition, curation, features, embeddings, bench, audit and reports | `git log --all --format="%an"` | CORRECT |
| C29b | "**Hemalakshmi P.**: documentation, README development, and project presentation" | 1 commit, `41871b9f`, touching `README.md` only | `git log --all --author=Hema`; `git show --stat 41871b9` | CORRECT as to documentation and README development. "Project presentation" is not the kind of thing git records either way; it is a self-description of a non-code contribution and is left as written |
| C30 | "built on work originally developed for the **Mandrake Bio Open Challenge**" | The repository corroborates a competition and a "Mandrake CLS Score" at `src/compute_cls_score.py:10`. The full name "Mandrake Bio Open Challenge" appears in **no** artifact; `ORIGIN.md`, `WRITEUP.md` and `CITATION.cff` say "competition" and name no organiser | `src/compute_cls_score.py:10`; absence confirmed by a repository-wide search for "mandrake" | AMBIGUOUS. Flagged at the merge gate rather than altered, see below |
| C30b | data credited only as "experimental reverse-transcriptase datasets produced by the corresponding research groups", with no study, authors, DOI or licence | Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. "Phage-assisted evolution and protein engineering yield compact, efficient prime editors." *Cell* 2023, 186(18):3983-4002.e26. DOI `10.1016/j.cell.2023.07.039`. Redistributed under **CC BY 4.0**, which "permits redistribution **with attribution**" | `tasks/taskA_crossfamily/PROVENANCE.md:80,81,96,97`; `reports/doman2023_source_facts.md:11,18-24` | UNSUPPORTED as an adequate attribution. See below |

**C30, the challenge name.** The repository does not contain the string "Mandrake Bio
Open Challenge". It does contain "Mandrake CLS Score" in the scoring script, so
"Mandrake" is corroborated as the challenge's name and the contributor is a project
member who plausibly knows its full styling. Hard rule 1 forbids inventing a fact to
make a sentence work, and it equally forbids my asserting a proper noun no artifact
supports. But it is a name, not a figure, and deleting a probably-correct attribution
would be its own error. **Left exactly as the contributor wrote it and raised at the
merge gate for the project owner to confirm.** Not treated as blocking, because no
result depends on it.

**C30b, the data attribution.** This is the one UNSUPPORTED verdict and it is a licence
matter, not a style matter. `PROVENANCE.md:97` records that the supplementary files are
committed to this repository **because** the licence was checked and found to be CC BY
4.0, where the earlier plan had assumed Elsevier terms would forbid it. CC BY 4.0's
operative condition is attribution. The PR's acknowledgement names no study, no
authors and no DOI, and it also removed the `LICENSE` and `CITATION.cff` links (D14).
The README is the front page of a repository that redistributes CC BY material, so the
attribution belongs there. The full citation with its DOI and licence was added, and
the licence section restored.

**Research Den.** The review brief asks that Research Den be described accurately. The
PR does not mention it, and **no artifact in this repository defines a Research Den
relationship**. Nothing was invented to fill the gap. Raised at the merge gate for the
project owner to supply if an acknowledgement is wanted.

---

## Reproducibility claims, executed

The brief requires that a command the README says reproduces something be run.

| # | Claim as written | Executed | Result | Verdict |
| --- | --- | --- | --- | --- |
| C24 | "The Task A pipeline can be reproduced using the repository's provided reproduction workflow. Individual benchmark stages have also been validated independently." | `reproduce.py` exists at the repository root with the documented `--quick` flag and nine declared stages | Entry point and flag confirmed present (`reproduce.py` docstring and `STAGES`) | CORRECT but names no command, so there is nothing for a reader to run. UNDERSTATED. Concrete commands restored |
| C23 | the pipeline records seeds, provenance, sequence and artifact checksums, frozen splits, model metadata, and explicit missing or blocked experiments | each element located: `SEED = 42`; `PROVENANCE.md` per task; `sequence_sha256`; curated-dataset SHA256; committed split files; `embeddings/MANIFEST.json`; NOT RUN markers in `WRITEUP.md` | all seven present | CORRECT |

Three load-bearing claims were executed rather than inspected:

```
$ python bench/test_protocol.py
PASS  pure selection is unaffected by held-out labels
PASS  peeking detected on 5 of 7 families
PASS  pure and peeking selectors disagree on 2 of 7 families
PASS  57 pooled predictions across 7 outer folds, CLS 0.4207
PASS  zero-active families and the single-member family are handled
PASS  deterministic at seed 42
all 6 tests passed

$ python bench/search_null.py --self-check
PASS  deterministic at seed 42: 0.4809
PASS  noise search reaches 0.4809, well above zero
PASS  capacity grows with K: K=2 0.2128 <= K=20 0.6615
search-null self-check passed

$ python curation/test_splits.py
tests: 13, failures: 0
```

**No reproducibility claim fails when executed.** The full `reproduce.py` run is
multi-hour by its own documentation and was not run; what was executed is every claim
the README makes that is executable in reasonable time, plus the exact test that CI was
failing on.

The PR also dropped the original's disclosure that the `Makefile` is **provided
untested** because `make` is not installed on the machine the results were produced on.
That is a volunteered limitation, and removing it widens the reproducibility claim
beyond what the original author asserted. UNDERSTATED. Restored verbatim.

---

## Remaining added claims

| # | Claim as written | Verified value | Source artifact and line | Verdict |
| --- | --- | --- | --- | --- |
| C7 | assays are not merged; prime editing, retron, DGR and in vitro retroviral kinetics are different assays and units; each must remain an independent task | correct, and enforced mechanically: `task_schema.py` rejects a two-task table, rejects inconsistent units, and refuses to concatenate tables whose `label_units` or `label_assay` differ | `schemas/task_schema.py`; `schemas/test_task_schema.py`, first step of the CI `pipeline` job | CORRECT, UNDERSTATED on enforcement. Mechanism restored |
| C8 | baselines are protein length, amino-acid composition, k-mer composition | `length` (1 feature), `aa_composition` (20), `kmer3` (6256), `kmer4` (20115) | `bench/results/taskA_representations.md` | CORRECT |
| C9 | handcrafted features are physicochemical, sequence-derived, and "structural descriptors where available" | `physicochemical` 13 features; `handcrafted` 789; structural block 12 columns, present for 56 of 57 rows, with Line1-RT's 12 columns missing and **masked rather than zero-filled** | `features/handcrafted/FEATURE_DICTIONARY_TASKA.md:26`; `FEATURE_DICTIONARY.md:112-156` | CORRECT, and "where available" is precisely the right hedge |
| C10 | ESM-2 evaluated at 8M, 35M, 150M, 650M | all four present in the benchmark | `bench/results/taskA_representations.md`, all four rows | CORRECT |
| C11 | alternative pooling investigated, including catalytic-core-focused representations | `ESM-2 650M, catalytic-core pooled` and `ESM-2, attention-weighted core pooling`, plus length- and family-residualized variants | `bench/results/representations.md:17-22` | CORRECT, UNDERSTATED: the PR never says what happened, which is that all four remedies failed and the two core-focused variants became the **most** lineage-predictive of all at 0.818. Restored |
| C19 | "the original high-scoring ensemble involved extensive optimization against the available labels"; the prediction layer "could not be treated as an unbiased estimate of generalization performance" | True, and far more specific in the artifact: `fast_opt.py` maximizes `compute_cls` over all 57 rows with 29 blend weights plus a power exponent and reseeds from its own fitted constants; 20 commits carry a CLS in the subject, first 0.4380, last **0.9754** | `audit/leakage_report.md:51,57,66,79,80` | UNDERSTATED, and the most serious wording issue in the PR. See below |
| C20 | search-capacity null experiments applied the same optimization procedure to noise-generated prediction vectors, demonstrating that flexible searches on small datasets can generate "surprisingly high scores" | At the matched count of 29 free parameters the p95 on pure Gaussian noise is **0.9340**; at 50 it is 0.9727 | `bench/results/search_null_log.txt:19-20`; `bench/results/search_null.json:177,200` | UNDERSTATED. "Surprisingly high" where 0.9340 is available. Restored |
| C22 | the repository structure tree | `data/`, `tasks/taskA_crossfamily/`, `tasks/taskB_mmlv_dms/`, `NEXT_STEPS.md` and all listed directories exist. Omits `curation/`, `data_acquisition/`, `evaluation/`, `src/`, `survey/`, `PROGRESS.md`, `ORIGIN.md`, `WRITEUP.md`, `reproduce.py`, `LICENSE`, `CITATION.cff`, and 5 of 7 task directories | directory listing | CORRECT as far as it goes, incomplete. Completed |
| C25 | only 57 RTs available; family structure strong relative to sample size; "some held-out families contain few or no positive examples" | exactly **three of seven** folds contain no active enzyme: CRISPR-associated, Other, Unclassified. 21 positives. Kish effective sample size 11.34 | `bench/results/taskA_representations.md` per-family table; `bench/protocol.py:49` `ZERO_ACTIVE_FAMILIES`; `audit/metric_report.md:18` | UNDERSTATED. "Some" and "few or no" where the exact counts are known and are worse than "some" suggests. Quantified |
| C26 | "not every possible PLM architecture, layer, or pooling strategy was searched, deliberately avoiding another large model-selection search" | correct, and the deliberateness is corroborated: the benchmark uses two heads and one free parameter from a 6-value grid fixed a priori, chosen in the inner loop | `bench/results/taskA_representations.md` preamble | CORRECT, and a good faith limitation to volunteer |

**C19, the leakage disclosure wording.** This is the claim that matters most on this
project. What the PR says is not false. What it loses is the first person: the original
read "**I optimized the competition metric directly against the labels it was scored
on**", and the PR reads "A retrospective audit found that the original high-scoring
ensemble involved extensive optimization". It also drops 0.9754, drops the matched null
of 0.9340, drops the 20-commit ladder, and drops the dated **Corrected 2026-10-03**
note recording that the repository's own earlier framing of this comparison was invalid
and that correcting it did **not** favour the repository.

The disclosure's value is inseparable from its voice and its figures. Restored in the
first person with 0.9754 and 0.9340 beside each other, and with the correction note
intact, per hard rule 3.

---

## Claims still unverified after this review

One, and it is not a number:

**"project presentation"** in C29b. Not the kind of contribution git records either
way. Accepted as a contributor's own description of their non-code work.

**No numeric claim remains unverified.** Every figure in the merged README traces to a
named artifact and line.

## Ruling on C30, the challenge name

Raised at the merge gate rather than decided here, because no artifact could settle it
and inventing or deleting a proper noun are both errors.

**The project owner ruled that the name be dropped**, and the three occurrences now
read "an earlier competition submission", "an earlier competition pipeline of my own"
and "a competition submission". This matches `ORIGIN.md`, `WRITEUP.md` and
`CITATION.cff`, which all describe the work as a competition and name no organiser.

C30's verdict is therefore closed as **resolved by removal**: the README now asserts
only what the repository's own artifacts support. The partial corroboration that
prompted the flag, "Mandrake CLS Score" at `src/compute_cls_score.py:10`, remains in
the code and is untouched; it simply is no longer used in the README to assert an
organiser's full name that nothing else records.
