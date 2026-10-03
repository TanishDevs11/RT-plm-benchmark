# Provenance: HIV-1 RT drug susceptibility phenotype

Task identifier: `B_hivrt`
Directory: `tasks/taskB_hivrt/`
Status: **ACQUIRED AND RECONSTRUCTED.** Reference confirmed at 229531 wild-type
assertions with zero mismatches.

## What this task is, and what it is not

**It is prediction of drug susceptibility phenotype from HIV-1 reverse transcriptase
sequence, in clinical and laboratory isolates.**

**It is not a deep mutational scan, and no artifact in this task may describe it as
one.** There is no published DMS of HIV-1 RT. That was verified rather than assumed:
ProteinGym's 217 substitution assays and 66 indel assays contain four HIV-1 entries, all
of them envelope at 852 to 861 residues; no target in the collection begins with the HIV-1
RT consensus `PISPIETVPVKLKPGMDGPKV`, and none is a 560-residue HIV protein. Full survey in
`reports/taskB_hivrt/dataset_survey.md`.

Three consequences that drive every later design decision:

1. **Each isolate carries many substitutions at once**, a median of 15 to 17 depending on
   the dataset. Effects are not separable into single-variant contributions without
   assumptions this benchmark does not make, so correlation here is **not** causal
   attribution of effect to individual mutations.
2. **Isolates are related by descent and transmission**, so sequences are not independent
   samples. Phylogenetic structure is the dominant confound.
3. **Resistance mutations travel in treatment-selected packages**, for example the
   thymidine analogue mutations 41L, 67N, 210W and 215Y. A model can learn the package
   without learning any causal contribution.

## Source

| field | value |
| --- | --- |
| source | Stanford HIV Drug Resistance Database, genotype-phenotype datasets |
| page | `https://hivdb.stanford.edu/_wrapper/pages/genopheno.dataset.html` |
| **database release, as printed on that page** | **2026-04-22** |
| access date | 2026-10-03 |
| assay | PhenoSense, Monogram Biosciences (Zhang 2005), in the filtered sets; the unfiltered sets mix PhenoSense with other methods |
| label | fold resistance of each drug relative to wild type |
| citation required | Rhee SY, Gonzales MJ, Kantor R, Betts BJ, Ravela J, Shafer RW. Human immunodeficiency virus reverse transcriptase and protease sequence database. Nucleic Acids Research. 2003;31(1):298-303. And: Shafer RW. Rationale and Uses of a Public HIV Drug-Resistance Database. J Infect Dis. 2006;194 Suppl 1:S51-8 |
| terms of use, verbatim | "maintained by Stanford University as a benefit to the research and education community", provided "as is" without warranty, "intended for research and educational purposes". Last updated 2023-01-10 |
| redistribution | **not explicitly granted.** The files are public, unauthenticated and small, and the resource exists to be used this way, so they are committed to `raw/` with full attribution. That is a judgement rather than a licence grant, and the alternative of keeping only the fetch script and the checksums remains available |

## Files obtained

Checksums in `raw/CHECKSUMS.txt`. Only the two reverse transcriptase drug classes were
fetched; PI targets protease, INI integrase and CAI capsid.

| file | role | isolates | phenotype results |
| --- | --- | --- | --- |
| `NRTI_DataSet.txt` | filtered, primary | 1867 | 10666 |
| `NRTI_DataSet.Full.txt` | unfiltered | 5369 | 29505 |
| `NNRTI_DataSet.txt` | filtered, primary | 2272 | 5659 |
| `NNRTI_DataSet.Full.txt` | unfiltered | 4913 | 11545 |
| `references.txt` | publication references | 294 | n/a |

**Every one of those eight counts reconciles exactly against the figures the source page
advertises for this release.** The parse asserts them and would halt otherwise.

### The brief's expected counts are from an earlier release

Recorded because it is the kind of discrepancy that gets silently absorbed. The brief
expects filtered NRTI at roughly 12739 results from 2219 isolates and filtered NNRTI at
roughly 5731 from 2344. The 2026-04-22 release has NRTI at 10666 from 1867, which is
**2073 results and 352 isolates smaller**, and NNRTI at 5659 from 2272. Both counts move
between releases. The release date is pinned here for that reason, and the brief's figures
are not used as an acceptance test; the source page's own figures are.

## Reference sequence

| field | value |
| --- | --- |
| file | `reference.fasta` |
| what it is | HIVDB consensus B reverse transcriptase amino acid sequence |
| source | `https://hivdb.stanford.edu/_wrapper/pages/documentPage/consensus_amino_acid_sequences.html` |
| length | **560 residues** |
| first 21 residues | `PISPIETVPVKLKPGMDGPKV` |
| residue range the phenotype data covers | positions **1 to 560**, with the caveat below |

The fetcher asserts the prefix and the length before writing the file, because the page
carries protease, RT and integrase and taking the wrong block would misnumber every
position in the task.

### The position columns do not cover all of RT in the filtered sets

A finding that changes how the sequences must be reconstructed:

| dataset | position columns reported |
| --- | --- |
| NRTI filtered | `P1` to `P240`, 240 of 560 |
| NNRTI filtered | `P1` to `P318`, 318 of 560 |
| both unfiltered | `P1` to `P560`, all |

This is consistent with the biology, NRTI resistance clustering in the polymerase domain
and NNRTI in the binding pocket, but it means that for the filtered sets the position
columns alone would assert consensus at positions where `CompMutList` records a mutation.
`CompMutList` covers the whole 560 in every file, so the reconstruction uses the position
columns within their range and `CompMutList` beyond it. 5491 NRTI and 493 NNRTI mutations
fall beyond the reported columns and would have been lost otherwise.

## The wild-type assertion, and the cross-check

**229531 wild-type residues stated by the source were asserted against the reference.
Zero mismatches. No offset is required.**

The parser halts on the first mismatch, reports the first ten, tests whether one constant
offset in the range -10 to +10 resolves all of them, states that offset as a finding, and
stops without applying it. `data_acquisition/test_parse_hivdb.py` holds it to that with
ten tests, including a reference shifted by one residue, which is detected at over 90
percent of positions and still halts.

Separately, the two encodings are cross-checked against each other. Within the reported
position-column range, `CompMutList` and the position columns both describe the same
isolate, and **0 conflicts were found across all four datasets**. Two independent
encodings agreeing on 229531 statements is a far stronger check than either alone.

## Ambiguity rules, stated once and applied uniformly

Every position cell falls into exactly one category and every category is counted in
`parse_report.json`. `X` means "not a determinate single residue"; it is not a residue and
not a guess.

| cell | meaning | rule | NRTI filtered | NNRTI filtered |
| --- | --- | --- | --- | --- |
| `-` | consensus | take the reference residue | 418747 | 621944 |
| a letter | substitution | take that residue | 19093 | 26569 |
| `.` | not sequenced | `X` | 6086 | 68054 |
| two or more letters | a mixture | `X`, **never coerced to a single residue** | 3979 | 5661 |
| `X` | the source's own ambiguity code | `X` | 168 | 267 |
| `~` | a deletion | `X` | 7 | 1 |
| `*` | a stop codon | `X` | 0 | 0 |
| `#` | an insertion | `X` | 0 | 0 |
| beyond the columns | not reported by this file | from `CompMutList`, else the reference | 5491 | 493 |

Mutation-list tokens carry three source formatting artefacts, repaired explicitly rather
than discarded: an internal space as in `R211 K`, a trailing period as in `K102K.`, and
the literal `NULL`. Insertions appear as `T69S_SG`, the T69 insertion complex, and are kept
as their own category with the wild-type residue still asserted; 124 NRTI and 79 NNRTI
insertion tokens appear in the unfiltered sets.

## Censoring: none found

The brief warns that fold-resistance values are frequently reported at assay limits and
that treating a censored bound as a point measurement is the most common error in analyses
of this dataset. **Every label value in all four files was checked for `>` and `<` markers
and none was found.** All values are plain decimal numbers or `NA`. The check is in the
parse and would report any that appeared in a future release.

## Outputs

| file | rows | what it is |
| --- | --- | --- |
| `curated_isolates.csv` | 14421 | one row per isolate per dataset: the reconstructed 560-residue sequence and its metadata |
| `curated.csv` | 57375 | one row per isolate-drug measurement: the label, joined by `isolate_id` |
| `parse_report.json` | n/a | every count, category and checksum the parse produced |

The two are separated deliberately. Each isolate carries up to six NRTI or five NNRTI
measurements, so a flat table would repeat a 560-residue sequence six times and, worse,
would invite a split that separates an isolate's own rows. Keeping the sequence in an
isolate table makes the isolate the unit of grouping structurally rather than by
convention.

**Labels are never pooled across drugs.** `curated.csv` carries a `drug` column as a
grouping key, and the modelling phase fits one model per drug. Fold resistance for 3TC and
for TDF are different quantities and a single target column mixing them would be
meaningless.

## Open items

1. **Patient-level grouping is available only in the unfiltered sets.** They carry `PtID`;
   the filtered sets do not. Multiple isolates come from one patient, so patient is a
   stronger grouping than isolate. The source's own filtering removes same-patient viruses
   sharing a major-DRM pattern, which is partial: patient structure survives it. Taken up
   in Phase 3.
2. **The unfiltered sets mix assay methods**, 3256 PhenoSense against 2113 other for NRTI.
   Pooling methods pools measurement scales, so they are used to quantify what the
   filtering removes, not as the primary analysis.
3. **Subtype is available only in the unfiltered sets**, which bounds any subtype-held-out
   regime to those.
