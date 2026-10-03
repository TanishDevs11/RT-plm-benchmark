# Task B final report: M-MLV RT variant effect

**Status: blocked on the labels, and on nothing else. No benchmark result exists, and
none can be computed from the public record.**

Revised 2026-10-03. The task had two missing inputs; one of them is no longer missing.
The reference is resolved, read out of the parent plasmid and confirmed against a second
deposit, and all 1046 variant sequences are constructed. Section 1 records that, including
the one residue the published record does not name and that the obvious construction would
have got wrong. The labels are still absent.

**Stop gate G1 was presented on 2026-10-03 and the reference was confirmed.** The ruling
was to confirm and stop there, not to go on and compute the Phase 4 representations that
need no labels, so none were computed. Section 6 gives the reason.

This report is written to the structure the Task B brief specifies. Sections 1, 2, 3 and 7
are complete, because they concern the dataset's construction and the benchmark's design,
both of which are now fully determined. Sections 4, 5, 6 and 8 state what they would
contain and why they are empty. That is the honest form of this document, and filling them
would require inventing the measurements they report on.

## The direct answer, section 8 brought forward

**Unanswerable from the public record.** Whether protein language models predict mutation
effects better than traditional representations on this dataset cannot be determined,
because the per-variant activity values were never deposited and are not available from
any of the 30 attempts across six route families now logged.

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
| not obtained | Supplementary Tables S6 and S7, the per-variant activity values. This is now the only missing input |
| no longer needed | Supplementary Sequence 1, the construct sequence. The reference was resolved from the parent plasmid instead; see below |

### The reference resolution, the highest-risk item in the task

The parent construct is PE2dR, which the preprint defines verbatim as "a compact prime
editor, PE2dR, by deleting the RNase H domain of the MMLV reverse transcriptase
(MMLV-RT)". So the reference is a truncated RT, not full-length M-MLV RT, and the
numbering question is which of the two the paper's positions refer to.

The frame is UniProt **P03355 sequence version 5, residues 660 to 1157**, which is RT
positions 1 to 498. `data_acquisition/resolve_mmlv_reference.py` establishes the frame and
`data_acquisition/parse_mmlv_dms.py` asserts it. The sequence itself is read from the
parent plasmid, which is a separate question answered further down.

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
`data_acquisition/test_parse_mmlv_dms.py` holds it to that with ten positive controls
for refusal, including a reference shifted by exactly one residue, which the parser
detects, diagnoses as a +1 offset, and still refuses to proceed on.

This matters more than its length here suggests. A one-residue offset produces 1045
variant sequences each wrong at two positions, raises nothing, and leaves no downstream
symptom except a benchmark that quietly measures noise, because every variant stays
internally consistent with every other.

### The construct's substitution content, resolved, and the one residue nobody published

The frame says where position 60 is. It does not say which RT this is. The strings
`pentamutant`, `D200N`, `T306K`, `W313F`, `T330P` and `L603W` appear **nowhere** in the
preprint, so that question could not be answered from the paper and was carried as a halt
condition rather than guessed.

It was answered from the parent plasmid. The preprint states the construction verbatim:
"The pCMV-PE2ΔR plasmid was constructed via deleting RNaseH domain from RT of pCMV-PE2
(#132775, Addgene)". Addgene 132775 publishes a verified full sequence, so the construct's
RT is a sequence to read rather than a substitution set to reason about.
`data_acquisition/fetch_pe2_plasmid.py` reconstructs the 9753 bp from the depositor's own
sequence-viewer payload under four assertions, and
`data_acquisition/resolve_pe2dr_reference.py` translates the RT reading frame, located by
scoring all six frames rather than by a probe peptide.

**Six differences from UniProt P03355 over 677 positions. Five were published. One was
not.**

| RT position | P03355 | plasmid | accounted for by |
| --- | --- | --- | --- |
| 8 | H | Y | **nothing in the published record** |
| 200 | D | N | Addgene's own insert field, `Cas9(H840A)-M-MLVrt(D200N, T306K, W313F, T330P, L603W)` |
| 306 | T | K | the same field |
| 313 | W | F | the same field |
| 330 | T | P | the same field |
| 603 | L | W | the same field, and inside the deleted region, so not carried |

**Why H8Y is the finding of this phase.** The obvious way to build this reference is to
take P03355, apply the documented PE2 pentamutant, and truncate at 498. That sequence
passes everything the preprint makes checkable: all seven stated residue identities, both
deletion boundaries, both stretch sequences, and the 1494 base pair and 26.4 percent
arithmetic. It is also wrong at position 8. It would have been wrong at position 8 in all
1046 variant sequences and in every embedding computed from them, and nothing in the
pipeline as it stood would have raised.

The parser now asserts construct identity as well as position numbering, at 8, 200, 306,
313 and 330, plus the reference length. Twelve assertions, all passing. The unmutated
candidate file is kept precisely so that
`test_the_unmutated_uniprot_frame_is_rejected` can feed it in and require a halt.

**Confirmed by an outside witness, not by self-consistency.** Everything above rests on one
deposited payload. pCMV-PEmax, Addgene 174820, is a separate deposit, and it is the parent
of the paper's best construct, PEmaxΔRM3. It encodes this reference **exactly, 498 of 498
residues**, while the two RT reading frames share only 1206 of 1494 nucleotides, 0.807.
Differently codon-optimized records cannot agree at the protein level by sharing a payload
or a rendering of one.

`tasks/taskB_mmlv_dms/reference.fasta`, SHA256
`070b5df7e3d6248f9dbd4213060f2d2cab9691a450a50e0de1281930f8f33cd7`, 498 residues, is the
adopted reference. It awaits stop gate G1.

### The 1046 variant sequences exist

The labels gate `curated.csv`. They do not gate the sequences: both libraries are exactly
saturating, so every variant's identity and full mutant sequence follow from the reference
and the two stretch boundaries with no activity value in the derivation.
`data_acquisition/build_mmlv_variant_sequences.py` writes all 1046 to
`tasks/taskB_mmlv_dms/variants_unlabelled.csv`, which carries **no** `efficiency` column
rather than an empty one, so it cannot be mistaken for `curated.csv` or joined by
accident.

Each row is checked to differ from the reference at exactly one position, all 1046
sequences are distinct, and the identifier set matches all four frozen split files
exactly. That last check matters: the splits were frozen before the reference was resolved
from the plasmid, so if the resolution had moved any residue inside a diversified stretch,
the identifiers at that position would have changed and the frozen splits would have been
silently invalid. They did not; H8Y falls outside both stretches.

## 2. Why identity and cluster splits are undefined here, and what replaced them

Full argument in `reports/taskB_mmlv_dms/split_design.md`. In short:

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
ready and waiting for the labels: the frozen splits, the resolved reference, the 1046
constructed sequences, and a parser that will reconcile whatever arrives against them and
log any variant present in one and not the other.

**One feature-space measurement was possible and was made.**
`reports/taskB_mmlv_dms/degeneracy.md` quantifies what the brief asks to be stated explicitly: that
k-mer frequencies and whole-sequence physicochemical descriptors are degenerate here by
construction. Across 199809 sampled pairs, 4-mer frequency vectors have a median pairwise
cosine similarity of 0.983968 and whole-sequence physicochemical vectors 0.999998, with
the latter's six dimensions collapsing to a numeric rank of 5 and 98.2 percent of variance
in a single direction.

That measurement needed no labels, and it did not need the reference to be settled
either: whatever the construct's substitution content is, all 1045 variants share it, so
changing the reference changes every variant identically. The script demonstrated that
rather than asserting it, by recomputing the whole distribution against a reference
perturbed at the then-unconfirmed positions; the median cosine similarity moved by exactly
0. The reference has since been resolved, and H8Y is one more position shared by every
variant, so the measurement stands unchanged.

The consequence for any future results table: when a whole-sequence block scores near zero
on this task, that is the representation being unable to distinguish the variants at all,
not the representation failing to capture variant effects. The same degeneracy applies to
mean-pooled language model embeddings, which is why the brief makes mean pooling a labelled
control and never the primary condition.

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
compute, only to evaluate.** With the reference now resolved, ESM-1v and ESM-2
masked-marginal scores for all 1045 variants could be computed against a sequence that is
confirmed rather than candidate, and the compute is modest: all 1045 variants are single
substitutions at 55 positions on one background, so a masked-marginal pass costs 55
forward passes per model, not 1045.

They are still not computed, now for one reason rather than two. A zero-shot score with no
labels to correlate against is not a result, it is a column of numbers, and the brief gates
feature computation behind stop gate G1 precisely so that a human rules on the reference
before anything is built on it. The one thing that is cheap and not yet earned is
computing 1045 numbers nobody can evaluate.

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
| reference | resolved, and cross-checked against a second deposit; awaiting stop gate G1 |
| generalization across RT families | **none, by construction.** Nothing measured here transfers to another RT family, because nothing here varies between families |

The last row is the important one and is the reason Task A and Task B are separate tasks
with separate labels and separate metrics rather than one merged dataset.

## What would unblock this

One of three things, in descending likelihood:

1. **The corresponding author shares Tables S6 and S7.** Supplementary Sequence 1 is no
   longer needed; it would now be a check on a settled answer.
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
