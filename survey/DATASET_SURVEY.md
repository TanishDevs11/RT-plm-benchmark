# Task B dataset feasibility survey

Written 2026-10-03. A survey and verification exercise: nothing was built, no features, no
embeddings, no models, no splits, and nothing was written into any `tasks/` directory.

Evidence base: 61 requests made for this survey, plus the 30 M-MLV label routes and the 5
reference-resolution requests already logged, all restated in `survey/acquisition_log.md`:
96 in all.
Ten sample files were downloaded and read, under `survey/candidates/<slug>/sample/`.

## The one measurement that decides this

**No reverse transcriptase deep mutational scan exists in either standardized collection.**

| collection | scope searched | reverse transcriptase entries |
| --- | --- | --- |
| ProteinGym v1.3 | all 217 substitution assays, searched over `DMS_id`, `molecule_name`, `title`, `source_organism` and `UniProt_ID` | **0** |
| MaveDB | the complete target-gene list, 2894 entries | **0** |

Searched terms returning nothing in ProteinGym: `reverse transcript`, `telomer`, `retron`,
`retrotranspos`, `intron`, `lentivir`, `moloney`, `murine leukemia`. The six assays whose
metadata mentions HIV are envelope glycoprotein and accessory proteins, not RT. The three
mentioning prime editing are prime-editing readouts on human disease genes, BRCA2 and
NPC1, not on the editor's RT. MaveDB's four `TERT` entries are promoter assays, categorised
`regulatory`, not protein-coding.

This reframes the whole question. The choice is not "M-MLV RT or a better-available RT
dataset", because there is no other RT dataset of this shape. It is "the first RT variant
effect benchmark, blocked on one file, or a non-RT benchmark that is available today".

A second measurement constrains the alternative. ProteinGym publishes per-assay scores for
98 zero-shot and 11 supervised models, and across its 717 repository paths there is **no
null, permutation, noise or search-capacity control anywhere**. The only uncertainty it
publishes is a bootstrap standard error on each model's cross-assay average, not on any
per-assay score. So the machinery this repository already has is the thing that collection
is missing.

## What had already been tried, so it was not repeated

From `tasks/taskB_mmlv_dms/PROVENANCE.md` and the two acquisition logs, read before
starting:

| already established | by |
| --- | --- |
| preprint obtained, DOI resolves under prefix `10.64898`, not the brief's `10.1101` | bioRxiv API, 2026-09-30 |
| supplementary material not deposited: the supplementary-material page lists nothing, the publisher's own JATS XML declares zero `supplementary-material` blocks, Europe PMC reports `hasSuppl=N` | 4 routes |
| no journal version: Crossref's record carries an empty `relation`, OpenAlex lists one location, the bioRxiv API reports no published version | 4 independent indexes |
| not in Zenodo, Dryad, OSF, GitHub, BioProject, GEO or SRA | 18 queries |
| PE2dR reference resolved, 498 aa, including the unpublished H8Y difference | Addgene 132775, cross-checked 498 of 498 against Addgene 174820 |
| 1046 variant sequences constructed, 4 splits frozen, 10 parser tests pass | this repository |

Four routes had never been tried, and were tried here: **figshare** (three queries, POST
search API, 0 hits), **reuse by a citing paper** (OpenAlex reports `cited_by_count` 0, and
the citing-works query returns 0, so no later paper has reused the table), a **version
recheck** (still version 1, `published: NA`), and **MaveDB** (0 RT entries). Candidate 0 is
now exhausted. The only remaining route is the corresponding author.

## Scoring summary

Availability is the gating criterion, and it means a file downloaded and read in this
session. `L` marks that the labels themselves were read, not just metadata.

| | candidate | labels read in session | n singles | n multis | label | RT through-line | days to first honest result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | M-MLV RT saturated mutagenesis | **no** | 1045 expected | 0 | prime editing enrichment, scaled -1 to 1 | **kept, and it would be the first** | 4 to 6, but only after labels arrive |
| 1 | ProteinGym v1.3 | **yes, L** | 217 assays, about 2.7M variants | varies | varies by assay | **lost** | 8 to 11 |
| 2 | TEM-1 beta-lactamase | **yes, L** | 4996 (Stiffler), 4783 (Firnberg) | 0 | growth or MIC under ampicillin | **lost** | 5 to 7 |
| 3 | GFP | **yes, L** | 1084 | 50630 | log fluorescence, FACS | **lost** | 6 to 8 |
| 4 | AAV2 capsid | **yes, L** | 532 | 41796 | capsid packaging viability | **lost** | 6 to 8 |
| 5 | other RT variant data | **no new dataset exists** | see below | see below | see below | kept, but nothing new | n/a |
| 6 | methods contribution over standardized assays | **yes, L**, uses candidate 1's files | chosen subset | chosen subset | varies by assay | **lost, and this is the real cost** | 8 to 11 |

## Candidate 0: M-MLV RT saturated mutagenesis, the incumbent

**Availability.** Labels downloaded and read: **no.** There is no URL. The preprint is
`10.64898/2026.07.06.736660`, version 1, posted 2026-07-07, CC BY-NC 4.0, and its
Supplementary Tables S6 and S7 were never deposited. Licence for the labels if they
arrive: unknown; if they arrive privately they carry whatever terms the author sets
regardless of the preprint's licence, so the repository would keep the parser and the
checksums only. Realistic route: the corresponding author, `bchhaoy@nus.edu.sg`. Expected
latency: unknown and author-dependent. A reply within two to six weeks is plausible; no
reply is also plausible, and 45 logged attempts say nothing else will produce the file. A
published journal version would carry the supplement, and the median bioRxiv to journal
interval is on the order of six months, so a realistic second date is 2027-01 onward.

**Scale and structure.** 1045 single substitutions plus 1 wild type, derived and frozen; 0
multi-mutants. 55 positions, two restricted stretches of the Fingers domain, RT 60 to 84
and RT 95 to 124, each **exactly saturating** at 19 non-wild-type substitutions per
position. One score per variant.

**Label quality.** Measured: log2 of variant abundance in eGFP-positive over eGFP-negative
cells in a lentiviral reporter screen, then normalized and scaled to the interval -1 to 1
with wild type at 0. Wild-type baseline: defined at 0 by construction. Censoring: unknown
until the tables exist. Replicates: unknown, so **no reproducibility ceiling can be
estimated**, which matters given that the HIVDB dataset already in this repository has one
of 0.8622 and the Cas9 panel examined under candidate 5 turns out to have one near 0.44.
Dynamic range: stated as -1 to 1; the preprint reports 176 of 1045 variants above wild
type, so roughly 17 percent beneficial. Fraction dead or saturated: unknown.

**Reference and construction.** **Resolved.** 498 aa, `reference.fasta`, SHA256
`070b5df7...f33cd7`, read out of Addgene 132775 by translation and confirmed 498 of 498
against Addgene 174820, whose RT reading frame shares only 1206 of 1494 nucleotides.
Numbering convention: stated by the preprint and independently confirmed; no offset.
Reconstruction effort remaining: **zero**. This is the one candidate where the week that
reference resolution cost has already been spent.

**Structure availability.** `4MH8`, X-ray, 3.0 Angstrom, monomeric M-MLV RT. Its polymer
entity aligns to P03355 from Gag-Pol residue 683 for 648 residues, which is RT 24 to RT
671, so it **covers both diversified stretches**. ESM-IF and ProteinMPNN are therefore
feasible, with a documented three-way numbering mapping. Also 1D0E, 1QAI, 1QAJ, 1D1U, 1I6J
and 50 further entries.

**Evaluation design.** Definable: position-held-out, stretch-held-out, target-amino-acid
held-out, and a labelled leaky random reference. All four are already frozen as CSV files.
Multi-mutant held-out: not definable, there are no multi-mutants. Identity and cluster
splits: **undefined**; all 1046 rows fall in one cluster at any usable threshold, and the
repository already guards against their reintroduction.

**Scientific positioning.** Papers benchmarking on it: **zero**. Its OpenAlex
`cited_by_count` is 0 and the citing-works query returns 0 records. Published baselines to
calibrate against: **none**, which is a real cost and the mirror image of its novelty. What
remains unanswered: everything. It would be the first variant-effect benchmark on any
reverse transcriptase. RT through-line: **kept, and uniquely so.** Choosing anything else
converts the project from "when do protein language models help for RT function" into a
generic DMS benchmark.

**Effort.** 0 days can usefully be spent now. 4 to 6 days once the labels arrive: a
regression harness, the feature and embedding builders, the zero-shot scores, the nulls and
the report. Everything upstream of that is done.

## Candidate 1: ProteinGym v1.3

**Availability.** Labels downloaded and read: **yes.** 217 substitution assays, about 2.7M
missense variants, plus an indel benchmark of about 300k across 74 assays. The assay
archive is at
`https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`,
43,021,128 bytes, `Accept-Ranges: bytes`, 218 members. Rather than download it whole, its
central directory and four members were fetched by HTTP range request. Licence: the
repository is **MIT**, which covers the reference and benchmark files fetched from it; no
licence file was located at the Harvard host, two probes returning 404, and the per-assay
data derive from the original publications with varying terms. So the conservative route
for the assay CSVs is a download script, while the small reference and benchmark CSVs can
be committed under MIT.

**Scale and structure.** 217 assays. Taxa: 96 human, 50 prokaryote, 40 eukaryote, 31 viral.
Selection types: 64 cDNA display proteolysis, 58 growth, 21 FACS, 6 binding, 4 flow
cytometry, 4 complementation, 3 survival, 19 unstated, the remainder other. Positions
covered and saturation vary by assay and are stated per assay in
`reference_files/DMS_substitutions.csv`. One `DMS_score` per variant, plus a binarized
`DMS_score_bin`.

**Label quality.** Each assay's measurement, units and scale are the original paper's.
ProteinGym's own transform is a per-assay normalization plus a binarization cutoff, both
recorded in the reference file. Wild-type baseline: **not uniformly defined**; the scores
are not wild-type-centred across assays, which is a real difference from the M-MLV label.
Censoring: assay-specific, and quantified below for the three individual candidates.
Replicates: **not shipped**, so a reproducibility ceiling cannot be computed from
ProteinGym alone for any assay; it would have to come from the original paper's
supplement. Dynamic range: assay-specific.

**Reference and construction.** **Solved, and this is ProteinGym's single greatest value
here.** The reference file carries a `target_seq` for every one of the 217 assays, and the
per-variant files carry a `mutated_sequence` as well as the `mutant` identifier.
Reconstruction effort: effectively zero, against the week the M-MLV reference cost. The
wild-type residue assertion was run against `target_seq` on 100 randomly sampled single
substitutions from each of four assays, seed 1729: **100 of 100 passed in every case.**

**Structure availability.** `ProteinGym_AF2_structures.zip`, 84MB, is published for the DMS
assays, and ESM-IF1 and ProteinMPNN already appear as scored baselines, so
structure-conditioned conditions are supported collection-wide.

**Evaluation design.** `cv_folds_singles_substitutions.zip`, 13,412,036 bytes, 218 members,
ships frozen per-variant fold assignments: `fold_random_5`, `fold_modulo_5` and
`fold_contiguous_5`. Verified on `BLAT_ECOLX_Firnberg_2014`: 4783 rows, five balanced folds
in each scheme. `fold_modulo_5` and `fold_contiguous_5` both hold out **whole positions**,
so a position-held-out regime already exists here and is already benchmarked by 11
supervised baselines. Mutation-type held-out: definable, not shipped. Multi-mutant
held-out: definable for the assays that include multi-mutants. Identity and cluster splits:
meaningless within an assay, as for M-MLV, but meaningful **across** assays.

**Scientific positioning.** Saturation in the literature: very high; it is the field's
reference collection and its leaderboard carries 98 zero-shot entries. Published baselines
exist and are directly usable for calibration. Read out of the files in this session,
cross-assay average Spearman with ProteinGym's own bootstrap standard error:

| model | average Spearman | se | rank of 97 |
| --- | --- | --- | --- |
| best overall, AIDO Protein-RAG | 0.518 | 0.000 | 1 |
| ESM-IF1 | 0.422 | 0.011 | 40 |
| ESM2 650M | 0.414 | 0.012 | 45 |
| ESM-1v ensemble | 0.407 | 0.013 | 47 |
| ESM2 3B | 0.406 | 0.011 | 50 |
| ESM2 15B | 0.400 | 0.010 | 52 |
| ESM2 150M | 0.387 | 0.013 | 62 |
| Site-Independent | 0.359 | 0.012 | 76 |
| ESM2 35M | 0.321 | 0.015 | 84 |
| ProteinMPNN | 0.257 | 0.010 | 91 |
| ESM2 8M | 0.226 | 0.015 | 93 |

That table is worth more than its size suggests. It is a published answer to two of the six
questions the Task B brief poses: ESM-2 scaling rises to 650M and then **turns over**, 0.414
to 0.406 to 0.400, and whether structure helps depends entirely on which structure model,
ESM-IF1 at rank 40 against ProteinMPNN at rank 91. It is also the yardstick against which
this repository's own pipeline can be validated before it is trusted on anything new.

What remains unanswered: not "do PLMs predict variant effects", which is answered many
times over, but whether the published rankings survive the controls this repository
applies. Verified in this session: across all 717 paths in the ProteinGym repository there
is **no null, no permutation test, no dimensionality-matched noise control and no
search-capacity null**. The single path matching "noise" is a diffusion noise schedule
inside a baseline model. Per-assay scores are point estimates with no interval of any kind;
the only published uncertainty is a bootstrap standard error on each model's cross-assay
average.

**RT through-line: lost.** ProteinGym contains no RT assay, so adopting it as Task B makes
the project a generic DMS benchmark with an RT study attached. The cost is set out under the
open questions.

**Effort.** 8 to 11 days: 2 to 3 for a regression harness, 2 to 3 for features and
embeddings across several assays, 2 for the nulls, 2 for the report.

## Candidate 2: TEM-1 beta-lactamase

**Availability.** Labels downloaded and read: **yes**, two screens, both complete assays
rather than extracts.

| screen | rows | bytes | SHA256 | saved as |
| --- | --- | --- | --- | --- |
| `BLAT_ECOLX_Stiffler_2015` | 4996 | 1,540,539 | `82835aee...d94f35` | `survey/candidates/2_tem1_betalactamase/sample/BLAT_ECOLX_Stiffler_2015.csv` |
| `BLAT_ECOLX_Firnberg_2014` | 4783 | 1,443,286 | `cfb814a5...e5e54f` | `survey/candidates/2_tem1_betalactamase/sample/BLAT_ECOLX_Firnberg_2014.csv` |

Both via range request from the ProteinGym archive. ProteinGym lists three further TEM-1
screens that were not downloaded: `BLAT_ECOLX_Deng_2012` (4996, MIC), `BLAT_ECOLX_Jacquier_2013`
(989, MIC), and a related `A4GRB6_PSEAI_Chen_2020` (5004, a different beta-lactamase).
Licence: as candidate 1; the underlying data are from the original papers.

**Scale and structure.** Stiffler 4996 singles, Firnberg 4783 singles, 0 multi-mutants in
either. Reference length 286. Both cover **263 positions**, span 24 to 286.
Saturation: Stiffler **0.9998** of the 4997 possible single substitutions at those
positions, Firnberg 0.9572. Stiffler 2015 is, on this measure, the most completely
saturated single-substitution DMS in the collection. One score per variant per screen; four
to five independent screens of the same protein exist, which is itself a rare asset.

**Label quality.** Firnberg 2014: growth-derived fitness over 0.25 to 1024 ug/mL
ampicillin, scores 0.0008 to 2.9024, median 0.4257, sd 0.4489. **Floor censored**: 2.84
percent of variants sit exactly at the minimum, and the two values 0.0008 and 0.0009 recur
136 and 100 times, which is a detection floor rather than a measurement. Stiffler 2015:
growth over 10 to 2500 ug/mL ampicillin, scores -3.7433 to 0.3558, median -1.1595, sd
1.1515, and **essentially no ties**, the most repeated value occurring twice. Wild-type
baseline: not centred at 0 in either file. Replicates: not in the ProteinGym file; the
original supplements would have to be fetched. Dynamic range: Stiffler spans 4.1 log units
with 5 percent of variants below -3.03, so the dead tail is large but resolved rather than
clipped.

**Reference and construction.** `target_seq` shipped, 286 aa, UniProt `P62593`. Wild-type
residue assertion: **100 of 100 passed** on each screen. Numbering: Ambler numbering is
standard for TEM-1 and the files' positions start at 24, consistent with it; the convention
is implicit in the data rather than stated in the file, but the assertion passing on 200
sampled variants settles it. Reconstruction effort: under a day.

**Structure availability.** RCSB full-text search returns 159 entries; `1NY0`, `1NXY`,
`1NYM`, `1YT4`, `4GKU`, `5HVI` among them. Coverage of the mutated region is effectively
complete, since the whole mature protein is crystallised. Best-resolution entry not
determined in this session, marked unknown, but 159 entries makes a sub-2-Angstrom
structure near-certain.

**Evaluation design.** Position-held-out: definable and already shipped as `fold_modulo_5`
and `fold_contiguous_5`. Region-held-out: definable by domain or by secondary structure,
not shipped. Mutation-type held-out: definable, not shipped. Multi-mutant held-out: not
definable. Identity and cluster splits: meaningless, one protein. A regime unavailable to
M-MLV **is** available here: **cross-screen held-out**, training on Stiffler and testing on
Firnberg, which tests transfer across two independent measurements of the same protein
under different selection pressure. That is a genuinely interesting split and nothing in
ProteinGym reports it.

**Scientific positioning.** Saturation in the literature: very high. It is one of the
canonical DMS datasets, in ProteinGym since v1, and used in a large fraction of
variant-effect papers; an exact paper count was not determined and is marked unknown, but
it is in the tens at least. Published baselines: yes, and strong. Zero-shot best 0.795
(S3F-MSA) on Firnberg and 0.788 on Stiffler. Supervised best, read from the three fold
files: random 0.909 (Kermut) on Firnberg and 0.914 (ProteinNPT) on Stiffler; contiguous
0.821 and 0.806; modulo 0.836 and 0.826. **The leaky-split gap is therefore already
published**: 0.909 random against 0.821 contiguous on Firnberg is a 0.088 drop, so the
finding the Task B brief expects to report for M-MLV is, for this assay, already in the
literature. What remains unanswered: the controls, as for candidate 1. RT through-line:
**lost entirely**; a bacterial hydrolase has no relationship to reverse transcription.

**Effort.** 5 to 7 days.

## Candidate 3: GFP

**Availability.** Labels downloaded and read: **yes.** `GFP_AEQVI_Sarkisyan_2016`, avGFP,
51,714 rows, full member 14,347,114 bytes, SHA256 `05b97d36...3a0838`. Rule 3 says sample
rather than bulk, so the committed file is a trimmed sample: all 1084 single substitutions
plus the first 500 multi-mutants, 1584 rows, 425,991 bytes, SHA256 `ec195c2a...bf15441`,
at `survey/candidates/3_gfp/sample/GFP_AEQVI_Sarkisyan_2016_sample.csv`. ProteinGym carries
four further fluorescent-protein screens: `D7PM05_CLYGR_Somermeyer_2022` (24515),
`Q6WV12_9MAXI_Somermeyer_2022` (31401), `Q8WTC7_9CNID_Somermeyer_2022` (33510), and
`PHOT_CHLRE_Chen_2023` (167529). Licence: as candidate 1.

**Scale and structure.** **The labels cover both, and overwhelmingly multi-mutants.** 1084
single substitutions against 50,630 multi-mutants, up to **15 simultaneous mutations** in
one variant. Reference length 238; the 1084 singles touch 233 distinct positions, span 3 to
237, so position coverage is broad but saturation is **poor**: 233 positions admit 4427
single substitutions and only 1084 are present, about 24 percent. One score per variant.

**Label quality.** Measured: log10 fluorescence from a FACS sort. Over the sampled rows,
scores run 1.2989 to 4.1136, median 3.6102, sd 0.8572. **Floor censored, visibly**: the
value 1.30103 is exactly log10(20) and recurs 57 times in a 1584-row sample, so the dark
variants are pinned at a reporting floor rather than measured. Wild-type baseline: not
centred at 0. Replicates: the original paper reports them; not in this file. Dynamic range:
about 2.8 log units, with the lower 5 percent at the floor.

**Reference and construction.** `target_seq` shipped, 238 aa. Wild-type residue assertion:
**100 of 100 passed** on sampled singles. Numbering: implicit, settled by the assertion.
Reconstruction effort: under a day.

**Structure availability.** 749 RCSB entries; `1EMA`, `1EMB`, `1RMM`, `1RMP`, `1RM9`,
`1RMO` among them. Coverage complete. Best resolution not determined, marked unknown.

**Evaluation design.** Position-held-out: definable, and shipped, but with only 1084 singles
the per-fold single-substitution n is about 217, which is small. Multi-mutant held-out:
**definable and interesting here, uniquely among the candidates**, because 98 percent of
the rows are multi-mutants; training on singles and testing on multi-mutants is a real
generalization question. Mutation-type held-out: definable. Identity and cluster splits:
meaningless within the assay.

**Scientific positioning.** Saturation in the literature: extremely high; Sarkisyan 2016 is
one of the two or three most-benchmarked DMS datasets in existence. An exact count was not
determined, marked unknown, but it is the standard epistasis example. Published baselines:
yes, and notably weak, which is interesting in itself. Zero-shot best 0.737 (RSALOR), with
S3F-MSA at 0.735. Supervised best: random 0.583 (ProteinNPT), contiguous 0.525, modulo
0.525. **Supervised performance is worse than zero-shot on this assay**, the only one of
the four examined where that holds, which is a published anomaly worth knowing about but
also a crowded place to stand. What remains unanswered: little that is cheap. RT
through-line: **lost entirely.**

**Effort.** 6 to 8 days, the extra over TEM-1 being multi-mutant representation and the
decision about how to encode a 15-mutation variant.

## Candidate 4: AAV capsid

**Availability.** Labels downloaded and read: **yes.** `CAPSD_AAV2S_Sinai_2021`, 42,328
rows, full member 33,124,725 bytes, SHA256 `fb05b6e8...e24c55`. Committed as a trimmed
sample: all 532 single substitutions plus the first 500 multi-mutants, 1032 rows, 794,260
bytes, SHA256 `19ff7fd1...08ee152`, at
`survey/candidates/4_aav_capsid/sample/CAPSD_AAV2S_Sinai_2021_sample.csv`. Licence: as
candidate 1.

**Scale and structure.** 532 single substitutions against 41,796 multi-mutants, up to **28
simultaneous mutations**. Reference length 735. The singles touch **28 distinct positions,
span 561 to 588**, and 28 positions admit 532 single substitutions, so the window is
**exactly saturated at 1.0000**. That makes this design the closest existing analogue to
the M-MLV task: a short contiguous diversified window, fully saturated, inside a much
larger protein.

**Label quality.** Measured: **capsid packaging viability**, a fitness score from a
selection on virus production. Over the sampled rows, scores run -7.8112 to 5.2547, median
-1.3594, sd 2.6759; over the full file, -9.5447 to 9.5365, mean -1.2259, sd 3.0446. Not
visibly censored; the extreme values are singletons. Wild-type baseline: not centred at 0.
Replicates: not in this file. Dynamic range: wide, about 19 units.

**What the label means, which is the problem.** The brief flags this and the flag is
correct. Packaging viability is a property of an assembled 60-mer capsid under a production
and selection protocol, not a protein-intrinsic property of a monomer. A substitution can
score as dead because the capsid fails to assemble, because it packages poorly, or because
it is cleared in selection, and the assay does not distinguish these. A model predicting
this is predicting an assembly and production phenotype. That is a legitimate target but it
is a different kind of claim from "does this substitution help the enzyme work", which is
what both Task A and the M-MLV task ask.

**Reference and construction.** `target_seq` shipped, 735 aa. Wild-type residue assertion:
**100 of 100 passed**. Numbering: VP1 numbering, implicit; settled by the assertion.
Reconstruction effort: under a day.

**Structure availability.** 86 RCSB entries; `3RA2`, `6JCR`, `2QA0`, `3OAH`, `6IH9`, `9RRS`
among them. Whether the 561 to 588 variable region is **ordered** in any of them was not
determined and is marked unknown; variable loops in AAV capsids are frequently
poorly resolved, so this is a real risk for the ESM-IF and ProteinMPNN conditions and would
need checking before those conditions were promised.

**Evaluation design.** Position-held-out: definable, but with 532 singles over 28 positions
a 5-fold position split leaves about 106 single substitutions per test fold. Region-held-out:
**not definable**, there is only one region. Mutation-type held-out: definable. Multi-mutant
held-out: definable and the dominant regime by row count. Identity and cluster splits:
meaningless.

**Scientific positioning.** Saturation in the literature: moderate; it is in ProteinGym and
is used in capsid-engineering machine learning work, but it is far less benchmarked than
TEM-1 or GFP. An exact count was not determined, marked unknown. Published baselines: yes.
Zero-shot best 0.592 (ProSST K=4096), with Protriever at 0.577. Supervised: random 0.856
(MSA Transformer embeddings), contiguous 0.668, modulo 0.704. **The random-to-contiguous gap
here is 0.188**, the largest of the four examined, which makes this the best existing
demonstration of exactly the leakage the Task B brief is designed around. What remains
unanswered: more than for TEM-1 or GFP, because it is less worked over. RT through-line:
**lost entirely.**

**Effort.** 6 to 8 days.

## Candidate 5: other reverse transcriptase variant data

**Availability.** No new dataset. This was searched systematically rather than by
recollection, and every result is a verified negative.

| where | what was searched | result |
| --- | --- | --- |
| ProteinGym v1.3 | all 217 assays over five metadata fields | **0 RT assays** |
| MaveDB | complete target-gene list, 2894 entries | **0 RT entries**; the 4 `TERT` hits are promoter assays, `regulatory` |
| Europe PMC | 6 queries over RT plus deep mutational scanning, saturation mutagenesis, telomerase, retrons, group II introns, prime editing variant libraries | no RT protein variant dataset; the M-MLV preprint is the only direct hit |
| NCBI BioProject, GEO, SRA | 12 queries, logged earlier | 0 relevant |

**The one lead that looked real, and what it turned out to be.** "High throughput variant
libraries and machine learning yield design rules for retron gene editors", Nucleic Acids
Research 2025, `10.1093/nar/gkae1199`, PMC11754653, open access with supplement. Its
supplementary archive was downloaded, 4,279,619 bytes, and read: Supplemental Tables 6 to 8
vary donor length, PAM position and donor direction; Tables 9 to 18 vary the retron's
**msd and msr non-coding RNA** regions. **There is no reverse transcriptase protein variant
anywhere in it.** It is a nucleic-acid library, so it cannot serve as a protein
variant-effect dataset.

**The other thing found, which is real but not RT.** `tasks/taskA_crossfamily/raw/mmc5.xlsx`,
already on disk from the Task A acquisition, is Doman 2023 Table S17, "Editing efficiency of
mutants". Read in this session: **163 single substitutions plus one wild type**, measured in
PEmax-delta-RNaseH, with **triplicate measurements at two loci**, RNF2 and PCSK9. Saved as
`survey/candidates/5_other_rt/sample/doman2023_tableS17_cas9_point_panel.csv`, 20,800
bytes, SHA256 `097e26e2...2623a82c`.

It is a **Cas9** panel, not RT: the editor IDs are prefixed `Cas`, and the 163 positions
span 23 to 1322 across 96 distinct positions, consistent with SpCas9 rather than a
498-residue RT. And it has a disqualifying property that only replicates could reveal:

| quantity | value |
| --- | --- |
| RNF2 mean editing, range | 10.63 to 48.94 percent, median 42.60 |
| PCSK9 mean editing, range | 15.72 to 41.10 percent, median 33.80 |
| **replicate Spearman within RNF2** | **0.2982, 0.4434, 0.6768** for the three replicate pairs |
| cross-locus Spearman, RNF2 against PCSK9 means | 0.6703 |

A reproducibility ceiling near 0.44 means almost nothing in this panel is measurable above
its own noise. This is the single most useful thing the survey found about label quality,
and it is an argument for insisting on replicates in any candidate: the ceiling is invisible
until you compute it, and a model scoring 0.5 here would be at the assay's limit, not good.

**The RT data this repository already has.** `tasks/taskB_hivrt/curated.csv`, 57,375 rows,
Stanford HIVDB genotype-phenotype, obtained, parsed, audited and split, with a replicate
reproducibility ceiling of **0.8622** over 292 replicate pairs. It is **not** a deep
mutational scan: each row is a clinical isolate carrying many substitutions at once, so
correlation is not attribution of effect to individual mutations. It is scoped in its own
prompt and is not a candidate here, but it is the live proof that an unblocked RT track
already exists in this repository.

**The PE6 evolved cohort.** `tasks/taskA2_evolved/`, status NOT ACQUIRED. Point variants of
Tf1 and M-MLV RT from Doman 2023, deliberately excluded from Task A for four recorded
reasons: selected for the label, colliding with Task A rows under leave-one-family-out,
being Task B's shape rather than Task A's, and measured in each editor's own scaffold. n is
small and unquantified here, marked unknown. It preserves the RT framing but is a selected
cohort, not a scan.

**Every other field.** Scale, label quality, reference, structure and evaluation design are
**not applicable**: there is no dataset to score. RT through-line: kept by construction, but
nothing new is available to keep it with. Effort: not applicable.

## Candidate 6: the methods contribution over standardized assays

Not a dataset. Keep Task A as the completed RT study, and make Task B the application of
this repository's null machinery to assays that are already standardized, already
benchmarked, and have no such machinery applied to them. "Dataset" here means the
collection used, which is candidate 1's files.

**Availability.** Labels downloaded and read: **yes**, via candidate 1. Everything needed
is in hand: 217 assays with `target_seq`, frozen 5-fold assignments in three schemes, 98
published zero-shot scores per assay and 11 published supervised scores per assay per
scheme. Licence: MIT for the benchmark and reference files; a download script for the assay
archives. Latency: **zero**. This is the only candidate that could start today.

**Scale and structure.** Chosen, not given. A defensible subset is 3 to 6 assays selected on
stated criteria rather than convenience: `BLAT_ECOLX_Stiffler_2015` for its 0.9998
saturation, `BLAT_ECOLX_Firnberg_2014` as the same protein under different selection,
`CAPSD_AAV2S_Sinai_2021` for its saturated 28-residue window and its 0.188 random-to-contiguous
gap, `GFP_AEQVI_Sarkisyan_2016` for multi-mutants, and two cDNA-display stability assays as
a contrasting selection type.

**Label quality.** Inherited per assay, and quantified above for four of them. The honest
weakness: **no assay in the collection ships replicates**, so a reproducibility ceiling
has to be recovered from each original supplement or stated as unknown. After what the Cas9
panel showed, stating it as unknown would be a real gap, so recovering it is part of the
work rather than optional.

**Reference and construction.** Solved by `target_seq`; 400 of 400 wild-type assertions
passed across the four assays sampled. Effort: under a day per assay, against the week
M-MLV cost.

**Structure availability.** `ProteinGym_AF2_structures.zip` covers the collection, and
experimental structures exist for all three individual candidates examined.

**Evaluation design.** The strongest point. ProteinGym's own `fold_random_5`,
`fold_modulo_5` and `fold_contiguous_5` are frozen and published, so results are directly
comparable to 11 supervised baselines without reimplementing anybody's split. New regimes
that nothing in the collection reports: cross-screen held-out on TEM-1, and
singles-to-multi-mutants on GFP and AAV.

**Scientific positioning. This is where the candidate earns its place or does not.**

Not a contribution: "benchmark PLMs on ProteinGym". Done to exhaustion, 98 entries deep.

A contribution, and concretely: ProteinGym publishes 98 zero-shot and 11 supervised
per-assay scores as **bare point estimates**, and its repository contains no null,
permutation, noise or search-capacity control in any of 717 paths. The questions that
follow are unanswered and answerable with what this repository already has:

1. **How many of the published per-assay rankings are resolvable at all?** Compute the
   minimum resolvable Spearman difference at each assay's n and report how many adjacent
   leaderboard pairs fall inside it. If a large fraction of the leaderboard is inside noise,
   that is a finding about the field's primary benchmark.
2. **Do the published scores clear a dimensionality-matched noise control?** A 1280-dimensional
   embedding and 1280 dimensions of Gaussian noise have the same capacity to be searched.
3. **What does the search-capacity null reach on these assays?** This is the repository's
   distinctive instrument and it has never been pointed at ProteinGym.
4. **Does the random-to-position-held-out gap behave as the collection's aggregates
   suggest?** Published per-assay: 0.088 on Firnberg, 0.188 on AAV. Those are large and
   nobody reports them as the headline.

**RT through-line: lost, and this is the real cost, not a footnote.** Task A becomes a
standalone RT paper and Task B becomes a methods paper about benchmark statistics. The
"when do PLMs help for RT function" framing, which was the reason the two tasks were
designed as a contrasting pair, does not survive. What survives is arguably a better paper
in isolation and a worse study as a whole.

**Effort.** 8 to 11 days for a 3-to-6-assay version; 5 to 7 days for a single-assay version
on TEM-1.

## Verification evidence

Ten files on disk, each downloaded and read in this session. This table is the checksum
record for the samples, which is why no separate checksum file is added.

| candidate | file under `survey/candidates/` | bytes | SHA256 | what was confirmed |
| --- | --- | --- | --- | --- |
| 1 | `1_proteingym/sample/zero_shot_spearman.csv` | 141,235 | `f432423b87f79ac9` | 217 assays, 98 model columns of published per-assay Spearman |
| 1 | `1_proteingym/sample/supervised_spearman_random.csv` | 20,404 | `9ec9288d0f5e1530` | 217 assays, 11 supervised models, random folds |
| 1 | `1_proteingym/sample/supervised_spearman_modulo.csv` | 20,486 | `4a4e97c335917206` | the same, position-modulo folds |
| 1 | `1_proteingym/sample/supervised_spearman_contiguous.csv` | 20,506 | `94f0c739b3dd55a8` | the same, contiguous-position folds |
| 1 | `1_proteingym/sample/cv_folds_BLAT_ECOLX_Firnberg_2014.csv` | 1,472,030 | `4c633405d16b3a16` | 4783 rows with three frozen fold columns, five balanced folds each |
| 2 | `2_tem1_betalactamase/sample/BLAT_ECOLX_Stiffler_2015.csv` | 1,540,539 | `82835aeecc2001c7` | 4996 singles, 263 positions, 0.9998 saturation, 100/100 WT assertions |
| 2 | `2_tem1_betalactamase/sample/BLAT_ECOLX_Firnberg_2014.csv` | 1,443,286 | `cfb814a5a5f81ad3` | 4783 singles, floor censoring at 2.84 percent, 100/100 WT assertions |
| 3 | `3_gfp/sample/GFP_AEQVI_Sarkisyan_2016_sample.csv` | 425,991 | `ec195c2a012f0899` | 1084 singles plus 500 multis, floor at log10(20), 100/100 WT assertions |
| 4 | `4_aav_capsid/sample/CAPSD_AAV2S_Sinai_2021_sample.csv` | 794,260 | `19ff7fd10512f177` | 532 singles saturating 28 positions, 100/100 WT assertions |
| 5 | `5_other_rt/sample/doman2023_tableS17_cas9_point_panel.csv` | 20,800 | `097e26e2cad832fe` | 163 Cas9 singles with triplicates; replicate Spearman 0.2982 to 0.6768 |

Full-member checksums for the two files trimmed to samples, so the trim is auditable:
`GFP_AEQVI_Sarkisyan_2016.csv`, 51,714 rows, 14,347,114 bytes, SHA256
`05b97d36a23363331b271edc56f1496b9a539109fd006e65532f91e9903a0838`;
`CAPSD_AAV2S_Sinai_2021.csv`, 42,328 rows, 33,124,725 bytes, SHA256
`fb05b6e80081005d2850e312b8dac907ea880009d487698bfcccab8187e24c55`.

**The wild-type residue assertion, the check that cost the most on M-MLV.** Run early and
cheaply here, as the brief asks. 100 single substitutions sampled per assay, seed 1729,
parsed into wild-type residue, position and mutant residue, and checked against the
assay's own `target_seq`:

| assay | sampled | passed | failures |
| --- | --- | --- | --- |
| `BLAT_ECOLX_Firnberg_2014` | 100 | **100** | none |
| `BLAT_ECOLX_Stiffler_2015` | 100 | **100** | none |
| `GFP_AEQVI_Sarkisyan_2016` | 100 | **100** | none |
| `CAPSD_AAV2S_Sinai_2021` | 100 | **100** | none |

400 of 400. The reason is structural, not luck: ProteinGym ships the reference sequence
alongside the variants in the same release, so the numbering convention cannot drift
between them. That single design choice is what makes these candidates days of work instead
of the week M-MLV took, and it is the strongest practical argument for the collection.

Two candidates are **unverified** and marked so regardless of what any paper claims:
candidate 0, because no label file exists, and candidate 5, because no dataset exists to
verify.

## Compatibility with existing machinery

Assessed by reading `bench/protocol.py`, 317 lines, and `bench/search_null.py`, 339 lines.

**The finding that matters: compatibility does not discriminate between candidates.** There
is no regression harness in this repository. `ProtocolResult` carries `cls`, `pr_auc` and
`w_spearman`; `run_nested_lofo` groups the outer loop on `data["rt_family"]` and reads
`data["active"]` and `data["pe_efficiency_pct"]`; the metric comes from `compute_cls`.
`search_null` and `de_blend_null` optimize the same CLS objective, and `signal_margin`
takes a CLS value against a null p95. Every candidate here is a single-protein regression
task, so every one of them needs the same adaptation. Reuse is a heavily weighted factor in
the brief, and it is one that cannot break the tie.

| component | transfers unchanged | needs rewriting |
| --- | --- | --- |
| `Method` abstraction: `candidates()` plus `fit_predict(config, train, test, rng)` with all preprocessing fitted inside the call | **yes, entirely.** It is metric-agnostic, and its contract is exactly what rule 7 of the Task B brief demands | nothing |
| `select_configuration`, the inner loop | structure yes | its scoring call, which is CLS-bound |
| `assert_selection_is_pure` and `PeekingHarnessMethod`, the deliberate-peek positive control | **yes, the construction transfers** and it is the thing most worth keeping | the metric it compares on |
| `run_nested_lofo`, the outer loop | the nesting pattern | the grouping, hard-wired to `rt_family`, becomes fold columns from a split file; the metric block becomes Spearman, Pearson, RMSE, MAE, precision at k and NDCG |
| `bootstrap_ci`, 10000 draws | the resampling structure | it calls `compute_cls`; needs a metric argument |
| label permutation control | concept yes | not currently a reusable function; lives inside the Task A scripts |
| `search_null` and `de_blend_null`, differential evolution against a rank objective | **the instrument transfers**, and it is the repository's distinctive asset | the objective, CLS to Spearman; `signal_margin` likewise |
| embedding extraction: mutated-position, mutant minus wild-type, local window, mean-pooled control | **not written yet for any task.** Task A's extractors are whole-sequence and catalytic-window, which is a different problem | all four, new work, 2 to 3 days |
| zero-shot scoring | `embeddings/esm2_*/taskA_zeroshot_singlepass_loglik.csv` shows a single-pass log-likelihood exists for whole sequences | masked-marginal at a position, and the wild-type-marginal and mutant-marginal variants, are new |
| `schemas/task_schema.py`, the row schema and run header | **yes** | a task entry per new dataset |
| split machinery in `curation/` | the frozen-CSV pattern and `curation/test_splits.py` guards | per-dataset definitions |

One genuine asymmetry in M-MLV's favour: its four split files are **already frozen and
already guarded by passing tests**, and its reference is resolved. For any ProteinGym assay
the splits come free from `cv_folds`, which is equally good and arrives differently.

A second asymmetry, in ProteinGym's favour and larger: it supplies **published numbers to
validate the rewritten harness against**. A regression harness written for M-MLV would have
nothing to check itself against, and its first execution would also be its first
validation, on a dataset nobody else has. Writing it against TEM-1, where the published
supervised Spearman is 0.909 random and 0.821 contiguous, means an error in the harness
shows up as a disagreement with the literature rather than as a plausible-looking number.
**That is a strong argument for doing a ProteinGym assay first even if M-MLV is the goal.**

## Open questions answered

**Does keeping the RT through-line matter enough to wait on M-MLV labels?**

For waiting: the survey's central measurement is that no RT deep mutational scan exists
anywhere, in 217 ProteinGym assays or 2894 MaveDB target genes. The within-protein half of
an RT study is therefore achievable with M-MLV or not at all. Everything expensive is
already paid: the reference is resolved including a difference nobody published, 1046
sequences are built, four splits are frozen, 10 tests pass, and a 3.0-Angstrom structure
covers both diversified stretches. It would be the first variant-effect benchmark on any
reverse transcriptase, and the contrast with Task A's cross-family result is the whole
reason the pair was designed.

Against waiting: the labels depend on one person answering one email, and 45 logged attempts
across six route families have established that nothing else will produce them. The dataset
has zero citations and zero prior baselines, so there is nothing to calibrate a new harness
against. No replicates are known to exist, so the reproducibility ceiling may turn out to be
unknowable, and the Cas9 panel found in this survey is a concrete example of a dataset whose
ceiling near 0.44 would have invalidated it. Waiting with nothing else running converts a
blocked task into a blocked project.

**The date by which waiting stops being rational.** Waiting is only irrational if it is
idle. Concretely:

| date | what it is |
| --- | --- |
| this week | send the corrected `AUTHOR_REQUEST.md`. Nothing has been sent; this is the only untried route |
| **2026-11-14** | six weeks after sending. If no usable reply, stop treating M-MLV as pending work and stop reserving the Task B slot for it |
| 2027-01-07 | six months after posting, the point at which a journal version becomes likely. Re-check the bioRxiv API and Crossref `relation` then, and quarterly after |

The brief asks for a date and that is 2026-11-14. But the recommendation below makes the
date much less costly, because it does not ask anyone to wait idly.

**Is there a candidate that preserves the RT framing at acceptable cost, even at small n?**

No new one. Searched exhaustively: ProteinGym 0, MaveDB 0, Europe PMC across six query
forms 0, NCBI 0. The retron lead was downloaded and read and is a nucleic-acid library. The
Cas9 panel found on disk is not RT and has a reproducibility ceiling near 0.44. The two RT
options that exist are both already in the repository and neither is a scan: the HIVDB
genotype-phenotype data, unblocked and at Phase 4a with a 0.8622 ceiling, and the PE6
evolved cohort, not acquired, small, and selected for the label.

**If the best candidate is a saturated benchmark such as TEM-1 or GFP, what is the
contribution?**

Concretely, and verified as unclaimed: ProteinGym publishes 98 zero-shot and 11 supervised
per-assay scores as bare point estimates, and its repository contains no null, permutation,
noise or search-capacity control in any of 717 paths. The contribution is to ask how much
of that leaderboard is resolvable: the minimum resolvable Spearman difference at each
assay's n, how many adjacent leaderboard pairs fall inside it, whether the scores clear a
dimensionality-matched noise control, and what a search-capacity null reaches at matched K.
That is "apply the search-capacity null to a benchmark where nobody has", and it is a real
answer. "Benchmark PLMs" is not, and would be the 99th entry on a 98-entry leaderboard.

**Can two candidates run together?**

Yes, and this is the answer the evidence actually supports. The two tracks share one
dependency, a regression harness, and share it in a way that favours doing the available
one first. Building that harness against TEM-1, where the published numbers are 0.909
random and 0.821 contiguous, validates it against the literature. The same harness then
runs on M-MLV unchanged the day the tables arrive, because its splits and reference are
already frozen. The marginal cost of folding M-MLV in later is then 1 to 2 days of feature
extraction, not 4 to 6, and the benchmark gains its RT half without the project ever having
been blocked.

## Ranking and recommendation

| rank | candidate | why here |
| --- | --- | --- |
| 1 | **6, the methods contribution, anchored on TEM-1** | available today and verified today; a contribution that is specifically unclaimed; supplies published numbers to validate a new harness against; and the harness it needs is the same one M-MLV needs |
| 2 | **0, M-MLV, kept pending with a deadline** | the only way to keep the RT through-line, everything expensive already paid, blocked on one email |
| 3 | 2, TEM-1 alone | the cleanest single assay anywhere: 0.9998 saturation, 4996 singles, uncensored, two independent screens of one protein. As a standalone target it is too well worked over to carry a new predictive claim |
| 4 | 1, ProteinGym as a dataset | the same files as rank 1 with a weaker question attached |
| 5 | 4, AAV capsid | closest structural analogue to M-MLV and the largest published leakage gap, but its label is an assembly and production phenotype and only 532 rows are single substitutions |
| 6 | 3, GFP | the most benchmarked DMS in existence, 24 percent saturation among singles, a visible reporting floor, and supervised performance below zero-shot |
| 7 | 5, other RT data | nothing exists |

**Recommendation: candidate 6, anchored on `BLAT_ECOLX_Stiffler_2015` with
`BLAT_ECOLX_Firnberg_2014` as its second screen, and candidate 0 kept pending until
2026-11-14.**

**Second choice: candidate 0 alone**, if the judgment is that the RT through-line is the
project and a methods paper is a different project. That is a defensible call and it is
Tanish's to make; it costs an unknown wait with no fallback.

**The decisive criterion: availability verified in this session, combined with a
contribution that is specifically unclaimed.** Those two together, and not either alone.
Availability alone would pick TEM-1 or GFP and produce a 99th leaderboard entry.
Unclaimed-contribution alone would pick M-MLV and produce nothing until an email is
answered. The one option that satisfies both is to apply the null machinery to a collection
that has none, on assays whose published numbers let the harness be checked, while the RT
dataset stays pending behind a sent request and a deadline.

**The candidate rejected most reluctantly: 4, AAV capsid.** Its 532 single substitutions
exactly saturate a 28-residue contiguous window inside a 735-residue protein, which is the
same experimental design as the M-MLV screen's two saturated stretches. Nothing else in the
collection is shaped like that, so it would have been the ideal rehearsal: the splits, the
local-window extraction and the position-held-out regime built for it would carry over to
M-MLV almost unchanged, and its published random-to-contiguous gap of 0.188 is the best
existing demonstration of the leakage the Task B brief is designed around. It is rejected
because its label is capsid packaging viability, which is a property of an assembled 60-mer
under a production protocol rather than of the protein, so a result on it would not be
comparable with Task A's enzyme-activity claim; because 98.7 percent of its rows are
multi-mutants of up to 28 substitutions; and because whether the 561 to 588 variable region
is ordered in any of its 86 structures is unverified, which puts the structure-conditioned
conditions at risk. If the AAV label were an enzyme activity, it would have been the
recommendation.

## STOP GATE

The ranked recommendation above is presented for Tanish's ruling. No work has begun on any
candidate, nothing was written into any `tasks/` directory, and `AUTHOR_REQUEST.md` has been
corrected but not sent. Sending it remains Tanish's action.
