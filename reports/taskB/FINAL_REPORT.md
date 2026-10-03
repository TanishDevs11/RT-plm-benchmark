# Task B final report: M-MLV RT variant effect

**Status: blocked at acquisition. No benchmark result exists, and none can be computed
from the public record.**

This report is written to the structure the Task B brief specifies. Sections 1, 2, 3 and 7
are complete, because they concern the dataset's construction and the benchmark's design,
both of which are fully determined by the preprint. Sections 4, 5, 6 and 8 state what they
would contain and why they are empty. That is the honest form of this document, and
filling them would require inventing the measurements they report on.

## The direct answer, section 8 brought forward

**Unanswerable from the public record.** Whether protein language models predict mutation
effects better than traditional representations on this dataset cannot be determined,
because the per-variant activity values were never deposited and are not available from
any of the eleven routes attempted.

This is a result about availability, not about representations. It is reported as the
outcome rather than worked around, because every available workaround, a simulated deep
mutational scan, values digitized from a figure, or a different protein's screen, would
produce numbers indistinguishable in form from real ones and meaningless in content.

## 1. Dataset construction, the reference resolution, and the numbering outcome

### The source

| field | value |
| --- | --- |
| citation | Li H, Wang Y, Zhang C, Tun TT, Yu S, Hu C, Yu H. Saturated mutagenesis screen of M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency. bioRxiv, posted 2026-07-07 |
| DOI, resolved | `10.64898/2026.07.06.736660` |
| DOI in the brief | `10.1101/2026.07.06.736660`, which does **not** resolve; the bioRxiv API returns "no posts found". The PDF's own header carries the `10.1101` form, so this is a defect in the preprint |
| version | 1, still, as of 2026-10-03 |
| published journal version | none; the bioRxiv API reports "no articles found for published version" |
| licence | CC BY-NC 4.0 |
| obtained | `raw/preprint.pdf`, 23 pages, SHA256 `5a13f7763987116c49f76c4aad9ce1aff6d78468a6b951b41cbbcc9609730cf3` |
| not obtained | Supplementary Tables S6 and S7, the per-variant activity values; Supplementary Sequence 1, the construct sequence |

### The reference resolution, the highest-risk item in the task

The parent construct is PE2dR, which the preprint defines verbatim as "a compact prime
editor, PE2dR, by deleting the RNase H domain of the MMLV reverse transcriptase
(MMLV-RT)". So the reference is a truncated RT, not full-length M-MLV RT, and the
numbering question is which of the two the paper's positions refer to.

Resolved as UniProt **P03355 sequence version 5, residues 660 to 1157**, which is RT
positions 1 to 498. `data_acquisition/resolve_mmlv_reference.py` establishes the frame and
`data_acquisition/parse_mmlv_dms.py` asserts it.

**The numbering outcome: no offset is required.** The paper's positions refer directly to
the truncated construct, position 1 being the first residue of the retained RT. Seven
residue identities the preprint states were asserted against the frame and all seven pass:

| position | source states | reference has | source of the claim |
| --- | --- | --- | --- |
| 60 | S | S | stretch 1 boundary, "S60-Q84" |
| 61 | I | I | reported mutation I61R |
| 67 | S | S | reported mutation S67W |
| 84 | Q | Q | stretch 1 boundary, "S60-Q84" |
| 95 | N | N | stretch 2 boundary, "N95-D124" |
| 101 | V | V | reported mutation V101R |
| 124 | D | D | stretch 2 boundary, "N95-D124" |

A second, independent confirmation: the derived library sizes are 475 and 570, which are
exactly the counts the preprint reports. 25 positions from S60 to Q84 and 30 from N95 to
D124, at 19 non-wild-type substitutions each.

**The parser halts rather than adapts.** On any wild-type residue mismatch it reports the
first ten, tests whether a single constant offset would resolve them, states that offset
as a finding, and stops without applying it.
`data_acquisition/test_parse_mmlv_dms.py` holds it to that with eight positive controls
for refusal, including a reference shifted by exactly one residue, which the parser
detects, diagnoses as a +1 offset, and still refuses to proceed on.

This matters more than its length here suggests. A one-residue offset produces 1045
variant sequences each wrong at two positions, raises nothing, and leaves no downstream
symptom except a benchmark that quietly measures noise, because every variant stays
internally consistent with every other.

### One question the reference resolution leaves open

**The construct's substitution content is undetermined.** The strings `pentamutant`,
`D200N`, `T306K`, `W313F`, `T330P` and `L603W` appear **nowhere** in the preprint. The name
PE2dR implies a PE2 lineage, which conventionally carries the M-MLV RT pentamutant, but
the paper describes the construct only as deleting the RNase H domain of MMLV-RT and names
no point substitution.

So the reference committed to `raw/` is named
`reference_candidate_unconfirmed.fasta` and carries no substitutions. It is not promoted
to `reference.fasta`, because four positions of difference across 498 residues would
silently corrupt every one of the 1045 variant sequences. Resolving it requires
Supplementary Sequence 1.

## 2. Why identity and cluster splits are undefined here, and what replaced them

Full argument in `reports/taskB/split_design.md`. In short:

Every row is a single amino acid substitution in the same 498-residue protein. Two
variants differ at no more than two positions, so pairwise identity is at least 496 of 498,
and a variant against the wild type is 497 of 498. **All 1046 rows collapse into one
cluster at any threshold a sequence-identity tool can express.**

That makes the regime **undefined rather than difficult**. A leave-one-cluster-out split
over one cluster has a fold whose training set is empty; a 90, 70, 50 or 30 percent
threshold does not partition the set at all. Reporting "no cluster spans the split" would
be true and entirely vacuous.

There is no MMseqs2 clustering anywhere in Task B, and
`curation/test_splits.py::test_task_b_has_no_identity_or_cluster_split` guards against its
reintroduction. That guard exists because Task A does use identity clustering and
`curation/cluster_redundancy.py` is one import away, so the plausible failure is a later
contributor adding Task B to its sources for consistency.

**What replaced it:** redundancy in this dataset is position identity, not sequence
identity, and the splits control that instead.

## 3. Benchmark design and what each split regime controls for

Four frozen regimes, all verified to cover all 1046 identifiers, test each exactly once,
and keep train and test disjoint.

| regime | folds | prevents | does not prevent |
| --- | --- | --- | --- |
| `position_held_out`, primary | 5 over 55 positions | learning a position's mean effect from its other 18 substitutions, then being scored on the 19th | transfer from the immediate structural neighbours of a held-out position |
| `stretch_held_out`, headline | 2 | the above, plus any transfer from the local sequence neighbourhood; the stretches are separated by ten residues | **crossing two normalizations**, if the -1 to 1 scaling was computed per library. The preprint does not say which |
| `aa_held_out`, secondary | 20, one per target residue | learning the chemistry of a substitution type from other examples of it | position identity; each fold spans both stretches by design, to isolate chemistry from position |
| `random_variant_LEAKY_DO_NOT_REPORT` | 5 | **nothing** | everything; it exists only to quantify the optimism a naive split buys |

The leaky split is labelled in its filename and in two columns on every one of its 5230
rows. The gap between it and `position_held_out` is itself a reportable finding, and the
position-mean baseline makes the same point more sharply: predicting each variant as the
mean of the other variants at its position should score very highly under the random split
and is **undefined** under `position_held_out`, because no other variant at that position
is in training.

## 4. Main results table across representations and split regimes

**Empty. No model has been trained.**

The table would carry twelve or more representations across four split regimes. What is
ready and waiting for the labels: the frozen splits, the reference frame, the 1046 derived
identifiers, and a parser that will reconcile whatever arrives against them and log any
variant present in one and not the other.

What is deliberately **not** written: the table parser for Tables S6 and S7, the feature
builders, the embedding extractors, and the modelling harness adaptation. Their column
layouts and shapes depend on files that do not exist. Writing them speculatively would
produce untested code whose first execution is also its first validation, on the one
dataset in this repository that nobody can check.

## 5. Statistical validation with every null

**Empty, necessarily.** A null is a comparison for a score, and there are no scores.

## 6. Representation analysis

**Empty.** The six questions the brief poses, whether model size helps, whether structure
helps, whether ProtT5 beats ESM-2, whether zero-shot beats trained, whether extraction
strategy dominates model choice, and where everything fails, each require measured
variant effects.

One of them deserves a note, because it is the question Task B exists to answer and the
reason the blocker matters. **Zero-shot masked-marginal likelihood requires no labels to
compute, only to evaluate.** ESM-1v and ESM-2 masked-marginal scores for all 1045 variants
could be computed today against the candidate reference. They are not, for two reasons:
the reference's substitution content is unconfirmed, so the scores would be computed on a
sequence that may be wrong at four positions; and a zero-shot score with no labels to
correlate against is not a result, it is a column of numbers. Computing them would look
like progress without being any.

## 7. Limitations

These apply to the task as designed, and would apply to any result it eventually produces.

| limitation | value |
| --- | --- |
| variants | 1045, plus 1 or 2 wild types; the count is open |
| protein | **one**. Every row is a substitution in the same 498-residue RT |
| regions | **two stretches of one domain**: S60 to Q84 and N95 to D124, both in the Fingers domain, 55 of 498 positions |
| assay | one: log2 enrichment of GFP-positive over GFP-negative cells, in a lentiviral eGFP reporter screen |
| cell type | one |
| label transform | normalized and scaled to the interval from -1 to 1 with wild type at 0; whether that was computed per library or across both is **not stated** |
| reference | unconfirmed in its substitution content |
| generalization across RT families | **none, by construction.** Nothing measured here transfers to another RT family, because nothing here varies between families |

The last row is the important one and is the reason Task A and Task B are separate tasks
with separate labels and separate metrics rather than one merged dataset.

## What would unblock this

One of three things, in descending likelihood:

1. **The corresponding author shares Tables S6 and S7 and Supplementary Sequence 1.**
   `data_acquisition/AUTHOR_REQUEST.md` is a drafted request, written at an earlier gate
   and still accurate. Nothing has been sent; sending it is a human action. If the files
   arrive privately they go in `raw/` locally and the provenance records that they must not
   be committed, because a file shared privately carries whatever terms the author sets
   regardless of the preprint's CC BY-NC licence.
2. **A later preprint version deposits them.** Version 1 is still current after three
   months.
3. **The peer-reviewed publication appears with its supplement.** No journal version
   exists yet.

`make pipeline-taskB-source` re-attempts acquisition by all eleven routes and records
every attempt, so re-checking costs one command.
