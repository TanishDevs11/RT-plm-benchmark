# Task B dataset survey: HIV-1 RT sequence to phenotype

Written 2026-10-03, before anything was downloaded. This is the Gate G0 artifact.

Every number below was read from the source pages during the survey rather than carried
over from the brief, and where the two disagree that is recorded as a finding.

## First, the thing to rule out

**There is no published deep mutational scan of HIV-1 reverse transcriptase.** This was
checked rather than assumed, because the brief asks that if one exists the work stops and
reports it.

ProteinGym's substitution benchmark, 217 assays, was searched for any reverse
transcriptase or HIV entry. It contains four HIV-1 assays and all four are **envelope**:

| ProteinGym assay | protein | length | selection |
| --- | --- | --- | --- |
| `A0A192B1T2_9HIV1_Haddox_2018` | Env | 852 | viral replication |
| `Q2N0S5_9HIV1_Haddox_2018` | Env | 860 | viral replication |
| `ENV_HV1BR_Haddox_2016` | Env | 861 | viral replication |
| `ENV_HV1B9_DuenasDecamp_2016` | Env | 853 | viral replication |

Two further checks: no ProteinGym target sequence begins with the HIV-1 RT consensus
`PISPIETVPVKLKPGMDGPKV`, and no target in the collection has the RT length of 560 residues
with an HIV taxon. The indels benchmark, 66 assays, contains none either; its only
`RT`-matching row is a human tankyrase entry matched on a PDB code.

So the task is **not** variant effect prediction and must never be described as one. It is
**prediction of drug susceptibility phenotype from HIV-1 RT sequence in clinical
isolates**, which is a different problem with different confounds.

## Candidate 1: Stanford HIV Drug Resistance Database genotype-phenotype datasets

**Recommended.**

| field | value |
| --- | --- |
| source | `https://hivdb.stanford.edu/_wrapper/pages/genopheno.dataset.html` |
| release date, as printed on the page | **2026-04-22** |
| what is measured | in vitro drug susceptibility of clinical and laboratory HIV-1 isolates |
| assay | PhenoSense, Monogram Biosciences, South San Francisco (Zhang 2005); the unfiltered sets also contain other assay methods |
| label | fold resistance of each drug relative to wild type |
| availability | public, direct HTTP download, no registration |
| terms | "maintained by Stanford University as a benefit to the research and education community", provided "as is", "intended for research and educational purposes". Last updated 2023-01-10 |
| citation required | Rhee et al. 2003, Nucleic Acids Research 31(1):298-303; Shafer 2006, J Infect Dis 194 Suppl 1:S51-8 |

### The RT-relevant drug classes, with current counts

Only NRTI and NNRTI target reverse transcriptase. PI targets protease, INI integrase, CAI
capsid; none of those is in scope.

| class | filtered: results | filtered: isolates | unfiltered: results | unfiltered: isolates |
| --- | --- | --- | --- | --- |
| NRTI | 10666 | 1867 | 29505 | 5369 |
| NNRTI | 5659 | 2272 | 11545 | 4913 |

**These disagree with the brief, and the brief is out of date rather than wrong.** It
expects filtered NRTI at roughly 12739 results from 2219 isolates and filtered NNRTI at
roughly 5731 from 2344. The current release has NRTI at 10666 from 1867 and NNRTI at 5659
from 2272. The NRTI set in particular is **2073 results and 352 isolates smaller** than the
brief expects. Both numbers move between releases, which is itself the reason the release
date has to be pinned in provenance and the reason the brief's figures must not be used as
an acceptance test.

The unfiltered sets are also smaller than the brief's expectation for NRTI, 29505 against
roughly 30331, and larger for NNRTI, 11545 against roughly 11776. Same cause.

### What the filtering removes, stated by the source

Two exclusions, both relevant to the benchmark's design:

1. "Redundant viruses obtained from the same individual that contained the same pattern of
   major drug resistance mutations were excluded to minimize bias that would result from
   over-representing highly similar viruses."
2. "Viruses with sequences containing mixtures at these major drug resistance mutation
   positions were also excluded because the presence of mixtures at these positions may
   confound genotype-phenotype correlations."

The major positions used for that filtering are published on the page. For NRTI: 41, 65,
70, 74, 75, 151, 184, 210, 215. For NNRTI: 100I, 101P, 103N, 106A/M, 181C/I/A, 188C/L/H,
190A/E/S/Q, 230L.

**Exclusion 1 is a partial, source-side version of the de-duplication this benchmark needs
to do anyway**, and it is partial in a way that matters: it removes same-patient viruses
sharing a major-DRM pattern, not all same-patient viruses. So patient-level structure
survives the filtering and must still be controlled in the splits.

### Fields, read from the source

Filtered sets: `SeqID`, one `Drug Fold` column per drug, `P1` through `Pn` giving the amino
acid at each position, and `CompMutList`.

Unfiltered sets add: `PtID` (patient identifier), `Subtype`, `Method` (phenotype assay),
`RefID`, `Type` (clinical versus lab isolate, where lab isolates are site-directed mutants
or in vitro passage products), `IsolateName`, and `SeqType` (complete versus
`PartialMutationList`).

Position encoding, verbatim: "'-' indicates consensus; '.' indicates no sequence; '#'
indicates an insertion; '~' indicates a deletion; '*' indicates a stop codon and a letter
indicates one letter Amino Acid substitution. Two and more amino acid codes indicates a
mixture."

Four of those are ambiguity categories needing an explicit, uniform rule in Phase 1:
no sequence, insertion, deletion, stop codon, and mixture.

### Three structural facts that drive the design, all confirmed from the fields

1. **The data gives per-position amino acids directly, not only a mutation list.** That
   removes one class of reconstruction risk, though the positions are still relative to
   consensus B and the wild-type assertion is still required.
2. **The unfiltered sets carry `PtID`, and the filtered sets do not.** Multiple isolates
   come from one patient, so the strongest available grouping is patient, not isolate. The
   brief mandates isolate-level grouping; patient-level is strictly stronger and is
   available only in the unfiltered sets. This is a specific, actionable finding and is
   taken up in Phase 3.
3. **The unfiltered sets mix assay methods.** For NRTI, 3256 isolates are PhenoSense and
   2113 are "Other"; for NNRTI, 2733 against 2180. Pooling methods pools measurement
   scales, so the unfiltered sets are for quantifying what filtering removes, not for the
   primary analysis.

### Reference sequence, already located

The consensus B RT amino acid sequence is published directly at
`https://hivdb.stanford.edu/_wrapper/pages/documentPage/consensus_amino_acid_sequences.html`
and begins `PISPIETVPVKLKPGMDGPKVKQWPLTEEKIKALVEICTEMEKEGKISKI`. It is the frame the
`P1...Pn` columns are numbered against, so the reference question that dominated the
previous Task B is comparatively well posed here.

### Exact download URLs

| file | URL |
| --- | --- |
| NRTI filtered | `https://hivdb.stanford.edu/download/GenoPhenoDatasets/NRTI_DataSet.txt` |
| NRTI unfiltered | `https://hivdb.stanford.edu/download/GenoPhenoDatasets/NRTI_DataSet.Full.txt` |
| NNRTI filtered | `https://hivdb.stanford.edu/download/GenoPhenoDatasets/NNRTI_DataSet.txt` |
| NNRTI unfiltered | `https://hivdb.stanford.edu/download/GenoPhenoDatasets/NNRTI_DataSet.Full.txt` |
| references | `https://hivdb.stanford.edu/download/GenoPhenoDatasets/references.txt` |

## Candidate 2: Hinkley et al. 2011, Nature Genetics

**Not recommended as a label source.**

| field | value |
| --- | --- |
| what is measured | in vitro replicative capacity of over 70000 virus samples |
| what is reported | effects of 1859 single amino acid variants in protease and RT |
| **critical** | **those per-variant effects are regression estimates from multi-mutation genotypes, not direct measurements of single variants** |
| underlying data | commercial Monogram Biosciences material; redistribution terms would have to be established before use |

The estimates are the problem, not the sample size. Each is a coefficient fitted to
genotypes carrying many substitutions at once, under a model whose additivity assumption
is exactly what a benchmark of this kind would want to test. Using them as labels would
mean evaluating representations against the output of another model, and any agreement
would be partly agreement with that model's assumptions rather than with biology.

If used at all it is as a secondary comparison, with "these are estimated effects, not
measurements" stated in every table that contains them. It is not the primary dataset.

## Candidate 3: ProteinGym and similar public collections

**Ruled out, definitively.** No reverse transcriptase assay of any kind, as set out at the
top of this document. This was checked by searching all 217 substitution assays and all 66
indel assays, by sequence prefix, and by length and taxon.

## Recommendation

**Use Candidate 1, the Stanford HIVDB genotype-phenotype datasets, NRTI and NNRTI, both
filtered and unfiltered.**

Reasoning:

1. It is the only candidate that supplies **measured** phenotypes for reverse
   transcriptase. Candidate 3 has no RT data; Candidate 2's per-variant values are model
   estimates.
2. It is public, directly downloadable, versioned by release date, and carries a clear
   citation requirement that this repository can meet.
3. The filtered sets are the primary analysis because they are single-assay, PhenoSense
   only, and source-deduplicated. The unfiltered sets are acquired alongside to quantify
   what the filtering removes and to recover `PtID` and `Subtype`, which the filtered sets
   do not carry.

**One qualification on the recommendation.** The terms of use grant research and education
use and say nothing explicit about redistribution. The files are small, public and
unauthenticated, and the resource exists to be used this way, so committing them to `raw/`
with full attribution is defensible; but it is a judgement rather than an explicit licence
grant, and the alternative of committing only the fetch script and the checksums is
available. Recorded so a human can override.

## What this dataset is not, to be repeated in every downstream report

- **Not a deep mutational scan.** No artifact in this task may describe it as one.
- **Not single-variant effects.** Each isolate carries many substitutions at once, so
  correlation here is not causal attribution of effect to individual mutations.
- **Not independent samples.** Isolates are related by descent and transmission, and
  resistance mutations travel in treatment-selected packages such as the thymidine
  analogue mutations 41L, 67N, 210W and 215Y. A model can learn the package without
  learning any causal contribution, which is the reason the leakage analysis in Phase 7 is
  the contribution rather than the predictive numbers.
- **Not novel ground.** Rules-based interpretation systems have used these data for two
  decades, and many machine learning papers use these exact files. Predictive performance
  alone demonstrates nothing here.
