# PR #1 diff analysis

| field | value |
| --- | --- |
| PR | #1, `TanishDevs11/RT-plm-benchmark` |
| title | "Add files via uploaddocs: improve README with project overview, methodology, and findings" |
| author | `@Hemapushparaj` (Hema) |
| head | `H-branch` at `41871b9f` |
| base | `main` at `8d0d47a1`, which is also the merge base |
| files | `README.md` only, 335 additions, 235 deletions |
| commit | `41871b9f` "Add files via upload" |

**File scope confirmed clean.** `gh pr view 1 --json files` lists exactly one entry,
`README.md`, `changeType: MODIFIED`. `git show --stat 41871b9` agrees: one file
changed. The PR description's "documentation-only" claim is accurate as to which
files it touches. Nothing outside `README.md` is modified, so the review proceeds on
that basis.

**The commit is a web-interface whole-file upload.** The title "Add files via upload"
and a 235-line deletion against a 246-line original mean this is a replacement, not
an edit. The original README survives in this diff only where the new text happens to
restate it. Deletions are therefore analysed first and at greater length than
additions, which is the correct weighting for this commit shape.

The replacement is also a format change: the new file is hard-wrapped at roughly 70
columns and carries pandoc-style output conventions (a dash-ruled table, `-   ` list
bullets, a `------` rule). That is consistent with the text having been authored in a
different tool and exported, which also explains the table rendering defect in R1
below.

---

## 1. Removed lines, by block, with a judgement on each

Every removed block is listed. Line numbers are against the original `README.md` at
`8d0d47a1`.

### D1. The provenance header and the read-only guarantee, lines 1 to 7

```
# RT-plm-benchmark

This repository is a methodological rebuild of
[TanishDevs11/RT-Activity-Predictor](https://github.com/TanishDevs11/RT-Activity-Predictor).
The original holds the submitted competition artifact and is **not modified by this
work**: no push, no branch, no tag, no pull request. It was cloned once at commit
`c1620706685d1a29e874031abd62d88a763d241e`, tagged here as `provenance`.
```

**Removal not acceptable. Must be restored.** This is the single most consequential
deletion in the diff. Four separate things go with it:

1. the statement that `RT-Activity-Predictor` is **not modified by this work**,
2. the link to that repository,
3. the clone SHA `c1620706685d1a29e874031abd62d88a763d241e`,
4. the `provenance` tag that marks the inherited boundary.

The new README mentions no upstream repository at all. The read-only guarantee is a
standing commitment about another repository, and the README is where it is published.
Verified against `ORIGIN.md`, which carries the identical SHA, the identical clone
date of 2026-09-29, and the identical "no push, no branch, no tag, no pull request"
wording. Restored in correction commit, with an `ORIGIN.md` link added.

### D2. The project status table, lines 9 to 22

The `## Status` heading, the link to `reports/progress_2026-09-30.md`, and the
four-row task table covering **A** cross-family, **A2** evolved, **B** M-MLV DMS, and
**C** retron / DGR / retroviral, each with its assay, its status, and its report link.

**Removal not acceptable as executed.** The new README has a `## Project Status`
section, but it covers only Task A and Task B. Tasks **A2** and the three **C** tasks
vanish. A reader of the new README would conclude the project has two tasks. It has
seven task directories (`tasks/taskA2_evolved`, `tasks/taskC_dgr`,
`tasks/taskC_retron`, `tasks/taskC_retroviral_invitro` and `tasks/taskB_hivrt` are all
present on disk). Dropping the blocked and unacquired tasks makes the project look
tidier than it is, which is the wrong direction of error. The table is restored.

Also note the new README omits `tasks/taskB_hivrt/` entirely, which has a curated
table, an audit report, a split design and a split verification under
`reports/taskB_hivrt/`. That is a whole line of work absent from the diff on both
sides, so strictly it is an addition opportunity rather than a deletion, but it is
recorded here because the status picture is incomplete without it.

### D3. The A-versus-B contrast and the 0.3052 figure, lines 24 to 29

The paragraph explaining why A and B are run together, including "the audit in this
repository measured raw ESM-2 embeddings at CLS 0.3052 on the cross-family task,
below what protein length alone achieves with no training."

**Removal acceptable in part, with the figure restored elsewhere.** The rationale
prose is a design argument, and the new README's Background section covers similar
ground acceptably. But 0.3052 is a verified number
(`bench/results/representations.md:12`) and the comparison against the zero-training
length baseline of 0.4416 (`bench/results/baseline_ladder.md:9`) is the project's
headline finding in its sharpest form. The figure is restored in the results section
rather than here.

### D4. The merged-label enforcement mechanism, lines 31 to 54

The `## Why labels are never merged across assays` section, including the bolded
"There is no merged label column in this repository, and no code path that produces
one", the confounding argument, and the mechanical enforcement paragraph naming
`schemas/task_schema.py` and `schemas/test_task_schema.py`.

**Partly replaced, and the replacement is weaker.** The new `### Why assay labels are
not merged` keeps the principle and states it correctly. What it loses is that the
rule is **enforced mechanically rather than by convention**: that `task_schema.py`
rejects a two-task table, rejects inconsistent units inside a task, and refuses to
concatenate tables whose `label_units` or `label_assay` differ, and that
`test_task_schema.py` proves the refusal holds both through the helper and when a
merged frame is built by hand with plain pandas. The new text says each assay "must
remain an independent task", which reads as a policy. It is a check, and the CI
`pipeline` job runs it as its first step. The enforcement sentence is restored.

Also lost: the observation that assay type is almost perfectly confounded with RT
family, and that the audit already found mean-pooled embeddings on this panel carry
lineage signal, so a merged column would silently convert a leave-one-family-out
split into a leave-one-assay-out split. That is the reason behind the rule, and it is
restored.

### D5. The headline results table and its four conclusions, lines 56 to 98

The `## Headline result` section: the bolded question and its one-word answer, the
"twelve representations, two model heads, one free parameter" protocol sentence, the
links to `MANUSCRIPT_SUMMARY.md` and `FINAL_REPORT.md`, the five-row results table
**including its Gaussian noise control column**, the chance-PR-AUC line, and the four
numbered conclusions.

**Removal not acceptable. The most load-bearing numbers in the project are in here.**
The new README keeps the PR-AUC column and the permutation column, and drops:

- **the Gaussian noise control column** (0.4458, 0.2889, 0.2581, 0.2643, 0.2474, all
  verified at `reports/statistical_validation.md:57-68`). Without it the README's own
  later claim that some ESM-2 representations cleared a noise control and then failed
  permutation has no numbers behind it;
- **conclusion 4 in its entirety**, which is that nothing clears the composite CLS
  metric at all: highest CLS 0.3739 against a search-capacity null p95 of 0.4433,
  every CLS bootstrap interval includes zero, and the median minimum resolvable CLS
  difference of 0.4816 larger than every CLS observed. This is the most important
  caveat in the repository and it is **absent from the new README**;
- **the dataset-limits sentence**: 57 enzymes, 21 positives, Kish effective sample
  size 11.34, and three of seven folds containing no active enzyme at all;
- the attribution detail behind conclusion 3: Spearman +0.52 of the `kmer4`
  out-of-fold score against length, and only 6.6 percent of attribution mass in the
  top 1 percent of features;
- the explicit "two model heads and nothing else, one free parameter" statement,
  which is what makes the search-capacity null comparison at K equals 1 legitimate;
- both report links.

The consequence is serious and is treated as the central finding of this review. The
new README presents `kmer4` at PR-AUC 0.6212 with "Survives permutation control: Yes"
as the only surviving representation, and nowhere states that under CLS nothing
survives and that the CLS ordering is not resolvable on this panel at all. A reader
takes away a win. The artifact (`bench/results/taskA_representations.md`, closing
section) says the ordering "is not resolvable on this panel at all". All of the above
is restored.

### D6. The earlier single-task result table, lines 100 to 116

The `### The earlier single-task result, which stands` heading and its five-row CLS
table: 3-mer cosine 0.4576, `protein_length_aa` 0.4416, best trained model 0.4284,
best PLM representation 0.3052, minimum resolvable difference 0.3419. Plus the
sentence that the previously reported 0.9754 does not appear in that table, and the
pointer into `WRITEUP.md`.

**Removal not acceptable. Must be restored.** Every figure verifies
(`bench/results/baseline_ladder.md:9,12,15`; `bench/results/representations.md:12`;
`bench/results/representations_log.txt:17`). This table is the clearest single
statement of the project's result: no method tested beats using `protein_length_aa` as
the score with no training at all. It is also the table the 0.9754 is explicitly
absent from, and that absence is stated in the original and is load-bearing. Restored.

### D7. The leakage disclosure, lines 118 to 149

The entire `## Why the previously reported 0.975 is not a result` section. In the
first person: "**I optimized the competition metric directly against the labels it was
scored on.**" Then the mechanism (`fast_opt.py` maximizing `compute_cls` over all 57
rows with 29 blend weights plus a power exponent, reseeding from its own fitted
constants), the 20-commit ladder from 0.4380 to 0.9754, the noise table at K equals 29
and K equals 50, the dated **Corrected 2026-10-03** note, the matched-null arithmetic,
and the statement that the leakage finding does not depend on the comparison.

**Removal not acceptable. This is the deletion the project's hard rules exist to
prevent, and it is the reason this review was commissioned.**

The new README does have a `## Leakage Audit of the Original Challenge Pipeline`
section, and it is written in good faith and is not false. But it is softened on every
axis that matters:

| dimension | original | PR version |
| --- | --- | --- |
| voice | first person, "**I** optimized" | third person passive, "A retrospective audit found that the original high-scoring ensemble involved extensive optimization" |
| the number | 0.9754, named | absent |
| the null figure | 0.9340 at matched K equals 29, beside it | absent; "surprisingly high scores" instead |
| the mechanism | `fast_opt.py`, 29 weights plus a power exponent, reseeds from its own constants | "extensive optimization against the available labels" |
| the commit ladder | 20 commits, 0.4380 to 0.9754 | absent |
| the self-correction | "**Corrected 2026-10-03**", with what the earlier framing got wrong | absent |
| the honest verdict | not distinguishable from noise, and explicitly not shown to be inside the null either | "could not be treated as an unbiased estimate" |

"A retrospective audit found" does not say who did it or who wrote the code audited.
The first person is the point: the person who produced the number is the person
disclosing it. A project whose entire purpose is that a headline number was reported
which the procedure did not support cannot have that disclosure rewritten into the
passive voice by anyone, however well intentioned.

Restored in the first person with 0.9754 and the matched null p95 of 0.9340 beside it,
and with the dated correction intact. Verified: 0.9754 at `audit/leakage_report.md:57,80`;
0.9340 at `bench/results/search_null_log.txt:19` and `bench/results/search_null.json:177`;
0.9727 at K equals 50 at `search_null_log.txt:20`; the 29-weights-plus-power
parameterisation at `audit/leakage_report.md:51`; interval width 0.0794 at
`audit/metric_report.md:58`; the 0.8978 different-artifact note and the +0.0414 margin
at `reports/FINAL_REPORT.md:183-197`.

### D8. The instrument section and the capacity figure, lines 151 to 159

The `## The instrument` section defining the search-capacity null, the sentence "A
score that does not clear its null has reported nothing", and the embedded figure
`![capacity curve](bench/figures/search_null_capacity.png)`.

**Removal not acceptable.** The search-capacity null is described by the original as
"the contribution here", that is, the project's methodological contribution. The new
README lists "Search-capacity null experiments" as one bullet in a nine-item
safeguards list and explains it only inside the leakage section. The definition, the
"reported nothing" standard, and the figure are all gone. The figure file exists on
disk. Restored, figure included.

### D9. The three verified embedding findings, lines 161 to 180

The `## Three verified findings about protein language model embeddings` section: the
note that all three are now reproduced by scripts where two were previously published
without code, family classification at 0.8197 against a 0.3214 majority baseline, the
monotonic scale ladder 0.7652 / 0.7833 / 0.8030 / 0.8197, PC1 tracking length at
Spearman -0.7681, the 650M activity PR-AUC of 0.4220 that fails its own permuted
labels, the bolded contrast sentence, and the failed-remedies paragraph ending in the
two core-focused variants reaching 0.818.

**Removal not acceptable. Every number here verifies and every number here is gone.**
The new `## What the PLMs Learned` section states the same conclusion qualitatively:
"ESM-2 embeddings strongly captured RT family information, but this did not translate
into reliable family-held-out activity prediction." That is true, and it is an
understatement of a precisely quantified result. Per the review's rule that findings
and caveats are strengthened rather than weakened, the figures are restored: 0.8197
and 0.3214 at `reports/representation_diagnostics.md:32,36` and
`reports/interpretation.md:173`; the ladder at `representation_diagnostics.md:29-32`;
-0.7681 at `representation_diagnostics.md:63`, with the published value reproduced to
two decimals at line 76; 0.818 for both catalytic-core pooled and attention-weighted
core pooling at `bench/results/representations.md:21-22`.

Also lost: that length residualization, family residualization, catalytic-core pooling
and attention-weighted pooling were all tried and all failed to fix the problem, and
that the two core-focused variants became the **most** lineage-predictive of all. The
new README mentions "catalytic-core-focused representations" in its Representations
list but never says what happened when they were tried. Restored.

### D10. The layout table, lines 182 to 207

A 24-row table mapping each path to its contents, with `reports/CROSS_TASK_COMPARISON.md`,
`reports/MANUSCRIPT_SUMMARY.md` and `reports/FINAL_REPORT.md` bolded, and including
`bench/names.py` ("repairs an inherited RT-name join defect, fails loudly"),
`legacy_leaky/` ("not usable in any results table"), `legacy_submission/` ("the
submitted artifact, as the object of study"), `curation/`, `data_acquisition/`,
`evaluation/` and `PROGRESS.md`.

**Replacement acceptable in form, inaccurate in content.** A directory tree is a
legitimate stylistic choice and is arguably friendlier, so the tree is kept. But the
tree omits `curation/`, `data_acquisition/`, `evaluation/`, `src/`, `survey/`,
`PROGRESS.md`, `ORIGIN.md`, `WRITEUP.md`, `reproduce.py`, `Makefile`, `LICENSE` and
`CITATION.cff`, and under `tasks/` it shows two of the seven task directories. It also
loses the characterisation of `legacy_leaky/` as not usable in any results table,
which is a correctness-relevant label rather than decoration. The tree is completed
and that label restored.

### D11. The reproduction commands and the environment block, lines 209 to 228

The `## Reproducing` section: the fenced `python reproduce.py` and
`python reproduce.py --quick` commands, what they do, the seed-42 statement, the `make`
targets, **the disclosure that the Makefile is provided untested** because `make` is
not installed on the machine the results were produced on, the memory-constraint
warning, and the full environment specification (Python 3.14.2 on Windows 11, numpy
2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0, matplotlib 3.10.8, torch
2.11.0+cpu with zero CUDA devices, fair-esm 2.0.0).

**Removal not acceptable.** The new `## Reproducibility` section says "The Task A
pipeline can be reproduced using the repository's provided reproduction workflow",
which names no command. A reproducibility section that does not say what to type is
not actionable, and `reproduce.py` exists at the repository root with exactly the
documented `--quick` flag (`reproduce.py` docstring, lines 1 to 13).

More seriously, the **untested-Makefile disclosure is gone**. That is a volunteered
admission of a limitation, and deleting it makes the project's reproducibility claim
broader than the original author was willing to make. The exact-versions block is also
gone, and it is what makes "every number reported" checkable. Both restored.

### D12. Protocol integrity and the peeking positive control, lines 230 to 236

The `## Protocol integrity` section: `bench/test_protocol.py` corrupts every held-out
label and requires the selected configuration to be byte-identical, and includes a
deliberate **peeking positive control** that the check must reject, with the
explanation that the control is the load-bearing test because a green suite in which
peeking also passed would mean the check is inert.

**Removal not acceptable.** The new README's safeguards list has nine bullets and none
of them is this. The peeking positive control is the one safeguard in the repository
that tests the tests, and the original's explanation of why it matters is the sharpest
methodological sentence in the file. Verified by execution in this review:
`python bench/test_protocol.py` passes 6 of 6, reporting "peeking detected on 5 of 7
families" and "pure and peeking selectors disagree on 2 of 7 families". Restored.

### D13. Blocked experiments, lines 238 to 242

ProtT5-XL-U50, inverse-folding likelihoods and zero-shot ESM-1v masked marginals
marked **NOT RUN** with blockers recorded in `WRITEUP.md`, and the statement that
**none was given an estimated or literature-quoted score**.

**Removal not acceptable.** The new README lists "zero-shot variant-effect
prediction", "structure-aware representations" and "inverse-folding models" under
Future Work. That recasts three experiments that were attempted and blocked as things
nobody has got to yet, and it drops the commitment that none of them was ever given an
invented number. Given what this repository is about, that commitment is exactly the
kind of sentence that must survive. Restored.

### D14. Licence and citation, lines 244 to 246

`## Licence` / "MIT. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff)."

**Removal not acceptable.** Both files exist at the repository root. The new README has
no licence section and no citation pointer, and its Acknowledgements credit the data
source only as "experimental reverse-transcriptase datasets produced by the
corresponding research groups", naming no study, no authors and no DOI.

The underlying data is Doman et al. 2023, Cell, DOI `10.1016/j.cell.2023.07.039`,
redistributed in this repository under **CC BY 4.0**, a licence whose central condition
is attribution (`tasks/taskA_crossfamily/PROVENANCE.md:80,81,96,97`;
`reports/doman2023_source_facts.md:11,18-24`). The provenance record is explicit that
the files are committed **because** the licence was checked and permits it with
attribution. Dropping the attribution from the front page is therefore not merely an
omission of courtesy, it moves against a licence condition the repository relies on.
The licence section is restored and the source citation with its DOI is added.

### D15. Every hyperlink in the file

The original has 11 markdown links. **The new README has zero.** Counted mechanically.
No link in the new file is broken, because there is no link in the new file. Report
pointers survive only as a bare `reports/` in backticks.

**Not acceptable for a README whose job includes routing a reader to the evidence.**
The key links are restored.

---

## 2. Structural changes

| change | judgement |
| --- | --- |
| Title changed from `# RT-plm-benchmark` to `# Benchmarking Protein Language Models for Reverse Transcriptase Activity Prediction` | **Keep.** A descriptive title is an improvement and is accurate. |
| 12 headings removed (Status, Why labels are never merged, Headline result, The earlier single-task result, Why the previously reported 0.975 is not a result, The instrument, Three verified findings, Layout, Reproducing, Protocol integrity, Blocked experiments, Licence) | Content judged per block above. Most restored, some under the contributor's new headings. |
| 18 headings added (Research Question, Background, Dataset, Why assay labels are not merged, Representations, Evaluation Protocol, Main Result, What the PLMs Learned, Leakage Audit, Why Null Controls Matter, Repository Structure, Reproducibility, Limitations, Future Work, Reports, Contributors, Acknowledgements, Project Status, Core takeaway) | **Keep.** The new organisation is genuinely better: background before results, an explicit research question, and a real Limitations section the original lacked. This is the part of the PR worth having. |
| Results moved from near the top to the middle, behind Background / Dataset / Representations / Evaluation Protocol | **Keep.** Defensible ordering for a reader arriving cold. |
| Leakage section moved from fourth to ninth, after the main result | **Acceptable with the content restored.** The disclosure's position matters less than its wording and its figures. |
| Embedded figure `bench/figures/search_null_capacity.png` removed | Restored, see D8. |
| Hard wrap changed from roughly 88 to roughly 70 columns | **Keep.** Pure style. |
| List bullets changed from `- ` to `-   ` | **Keep.** Renders identically. |

## 3. Markdown that will not render

### R1. The main results table will not render as a table. Must fix.

New README lines 125 to 138 are a pandoc-style dash-ruled table, indented by two
spaces:

```
  ----------------------------------------------------------------------------
  Representation               PR-AUC   Permutation p95  Survives permutation
                                                               control
  ----------------- ----------------- ----------------- ----------------------
  4-mer composition        **0.6212**            0.5398          Yes
```

GitHub-flavored markdown has no such table syntax. Two spaces of indentation is below
the four needed for a code block, so this is parsed as ordinary content, and the result
on the repository front page is:

- line 125, a dash run after a blank line, becomes a thematic break (`<hr>`);
- line 128, a dash run immediately following the text of lines 126 and 127, makes those
  two lines a **setext level-2 heading**. The project's headline results table renders
  as the giant heading "Representation PR-AUC Permutation p95 Survives permutation
  control";
- the data rows collapse into run-together paragraphs with their column alignment lost,
  since markdown folds whitespace.

This is the project's primary results table rendering as a heading followed by prose.
Converted to a GFM pipe table, which is also what the original used and what every
other table in the repository uses.

### R2. Items checked and found sound

- `` ``` text `` fence at line 204 is valid; a space before the info string is
  permitted, and the tree renders.
- The `------` rule at line 338 sits between blank lines, so it is a thematic break and
  renders correctly as a horizontal rule. Intentional and fine.
- `NEXT_STEPS.md`, referenced at lines 218 and 239, **does exist** at the repository
  root. Not broken. Worth recording because `NEXT_ACTIONS.md` also exists and the
  similarity invited a false positive here.
- `data/` in the tree exists. `tasks/taskB_mmlv_dms/` exists.
- No unclosed code fences. Three backtick fences, all balanced.
- No malformed pipe tables, because the new file contains no pipe tables.

## 4. Added lines making a factual claim

Extracted and numbered for Phase 2. See `review/pr_1_claim_check.md` for the
verification of each against a repository artifact.

| # | claim, abbreviated | new README line |
| --- | --- | --- |
| C1 | 57 experimentally assayed reverse transcriptases | 43 |
| C2 | 21 active RTs | 44 |
| C3 | RTs spanning multiple evolutionary families | 45 |
| C4 | sequences verified against primary-source supplementary material | 46 to 47 |
| C5 | binary activity is the primary reproducible target | 48 |
| C6 | `pe_efficiency_pct` retained, provenance a limitation, no published supplementary table | 50 to 53 |
| C7 | assays not merged; each assay an independent task | 55 to 64 |
| C8 | baselines: protein length, aa composition, k-mer composition | 72 to 74 |
| C9 | handcrafted: physicochemical, sequence-derived, structural where available | 78 to 80 |
| C10 | ESM-2 evaluated at 8M, 35M, 150M, 650M | 84 to 90 |
| C11 | alternative pooling including catalytic-core-focused representations | 92 to 93 |
| C12 | nine evaluation safeguards, itemised | 100 to 111 |
| C13 | PLM embeddings did not improve over simpler representations under family-held-out evaluation | 119 to 121 |
| C14 | the five-row PR-AUC and permutation table | 125 to 138 |
| C15 | prevalence approximately 0.3684 is the chance level for PR-AUC | 140 to 141 |
| C16 | 4-mer was the only representation in the reported comparison to survive permutation | 143 to 144 |
| C17 | the 4-mer result is not a catalytic motif; correlated with length and family, attribution spread thin | 146 to 151 |
| C18 | ESM-2 captured family information but it did not transfer to activity prediction | 158 to 163 |
| C19 | the original high-scoring ensemble involved extensive optimization against available labels | 169 to 172 |
| C20 | search-capacity null experiments applied the same procedure to noise vectors | 174 to 180 |
| C21 | some ESM-2 representations beat Gaussian noise controls then failed permutation | 191 to 192 |
| C22 | the repository structure tree | 204 to 219 |
| C23 | the pipeline records seeds, provenance, sequence and artifact checksums, frozen splits, metadata, blocked experiments | 225 to 233 |
| C24 | the Task A pipeline can be reproduced using the provided workflow | 235 to 237 |
| C25 | only 57 RTs available; family structure strong; some folds few or no positives | 249 to 252 |
| C26 | not every PLM architecture, layer or pooling strategy was searched, deliberately | 257 to 258 |
| C27 | the M-MLV task remains blocked, labels not publicly available during acquisition | 259 to 261 |
| C28 | sequence construction, reference resolution and split design prepared; modelling paused | 276 to 279 |
| C29 | contributor roles | 309 to 312 |
| C30 | built on work for the Mandrake Bio Open Challenge | 316 to 318 |
| C31 | core takeaway: larger PLMs encoded lineage but gave no evidence of better held-out prediction | 342 to 346 |

## 5. Summary judgement on the diff

The reorganisation is a real improvement and is kept. The prose is careful, and where
the contributor states a number, **the number is right**: all five PR-AUC values, all
five permutation p95 values, the prevalence, the enzyme and active counts, and the
ESM-2 model scales verify exactly against artifacts. Nothing in this PR is fabricated
and nothing is rounded in the project's favour. That deserves saying plainly, because
it is the risk this review was set up to catch and it did not occur.

The problem is subtraction, which is the risk the commit shape created. A whole-file
upload replaced a file dense with verified figures, caveats and commitments with one
that keeps the conclusions and drops the evidence. Specifically: the leakage disclosure
lost its first person, its 0.9754 and its 0.9340; the CLS result that nothing survives
vanished entirely, leaving a PR-AUC table that reads as a win; the read-only guarantee
about `RT-Activity-Predictor` disappeared; and the licence attribution the data's CC BY
terms depend on went with it.

No claim is overstated by invention. Several are overstated by omission, which on this
project amounts to the same failure.
