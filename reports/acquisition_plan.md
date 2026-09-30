# Acquisition plan

Written before any data file was downloaded. This document is the specification that
Phase 2 parsers are checked against: rows expected here, rows parsed there, and every
difference logged as a drop with a reason.

Date written: 2026-09-30.

## How to read the status tags

Every factual field below carries one tag. The tags exist because the difference between
"I read this" and "this is plausible" is the difference this whole repository is about.

| tag | meaning |
| --- | --- |
| `READ` | quoted or taken from a page fetched in this session; the URL is listed in the network log below |
| `DERIVED` | arithmetic or cross-reference from `READ` facts, with the derivation shown so it can be checked |
| `MEASURED` | computed in this session from a file already in this repository |
| `UNVERIFIED` | not checked against any source; requires the actual file or a human |

No field is filled by recall. Where a number would have to be remembered rather than
read, it is tagged `UNVERIFIED` and left as a question.

## Network log for this session

Nothing was downloaded into any `tasks/*/raw/` directory. Every task's `raw/` is empty and
every `PROVENANCE.md` reads `NOT ACQUIRED`. The reads below were bibliographic: they
establish DOIs, table numbers, label definitions, and accessions so that this plan can be
written against sources rather than against memory.

- `api.biorxiv.org/details/biorxiv/10.1101/2026.07.06.736660` returned no posts found
- `biorxiv.org/content/10.64898/2026.07.06.736660v1.full` main text, read twice
- `biorxiv.org/content/10.1101/2021.11.05.467423v1.full` main text
- `rest.uniprot.org/uniprotkb/P03355.txt` UniProt flat file
- `pmc.ncbi.nlm.nih.gov/articles/PMC10482982/` Doman et al. 2023, PMC copy
- four web searches, for the Task B preprint and for Task C candidate sources

Fetched text came back as a summarizing model's reading of each page, not as the raw page.
Every quotation below is therefore tagged `READ` in the sense "read from that page in this
session", and each one is still to be checked against the published file when it is
obtained. Two independent confirmations are noted where they exist.

---

## Task A: cross-family ortholog activity

### Source A1, the survey the existing 57 rows come from

| field | value | tag |
| --- | --- | --- |
| citation | Doman JL, Pandey S, Neugebauer ME, et al. Phage-assisted evolution and protein engineering yield compact, efficient prime editors. Cell 186(18):3983-4002.e26, 2023 | `READ` |
| DOI | `10.1016/j.cell.2023.07.039` | `READ` |
| survey figure | Figure 1C | `READ`, single page, confirm against the article |
| survey table | Supplementary Table S1 | `READ`, single page, confirm against the article |
| sequences held in | not established; Table S1 may hold names and efficiencies without full protein sequences | `UNVERIFIED` |
| expected enzymes | 59, spanning 14 classes | `READ` |
| expected actives | 20, from four classes | `READ` |
| cell line | HEK293T, endogenous genomic sites | `READ` |
| licence | Elsevier, Cell; supplementary tables are presumed not redistributable | `UNVERIFIED` |
| automatable | no; publisher interstitial | `READ`, by the absence of a direct file URL |

Label definition, verbatim: "the frequency of the intended prime editing outcome with no
indels or other changes at the target site" (`READ`). Units: percent. Controlled
vocabulary term: `prime_editing_pct_HEK293T`.

### What the inherited table actually contains

Measured in this session from `data/rt_sequences.csv` and `data/family_splits.csv`
(`MEASURED`):

- 57 rows, 0 duplicate sequences, 0 duplicate names, alphabet is the standard 20 residues
  with no gaps and no unresolved positions
- `sequence_len` agrees with `len(sequence)` on every row
- 21 rows with `active == 1`
- efficiency range 0 to 41 percent
- 7 family labels: Retroviral 18 rows with 12 active, Retron 12 with 5, LTR_Retrotransposon
  11 with 2, Group_II_Intron 5 with 2, CRISPR-associated 5 with 0, Other 5 with 0,
  Unclassified 1 with 0
- actives occur in exactly 4 of those 7 families

### Reconciliation questions, to be answered in Phase 2 and not before

The last point is a real corroboration: the paper says actives came from four classes, and
the inherited table has actives in exactly four families. The counts do not line up as
cleanly, and the gaps are specific enough to be resolved by reading Table S1.

1. **57 rows against 59 enzymes.** Two enzymes are absent. Which two, and why. A plausible
   reason is that a protein sequence could not be resolved for them, but that is a guess
   and must be replaced by the actual reason per enzyme (`UNVERIFIED`).
2. **21 actives against 20.** One row more than the paper reports is called active. Two
   candidate explanations, neither confirmed: `MMLV-RT` at 41 percent may be the PE2
   benchmark control rather than one of the 59 surveyed enzymes, in which case the
   inherited table mixes a control into the panel; or `Ne144-RT` at 0.5 percent may sit
   below the paper's detectable-activity threshold and have been called active by a
   threshold applied later by someone else. If the second is true, the binary label in this
   repository is not the paper's binary label, and that must be stated wherever the binary
   label is used (`UNVERIFIED`).
3. **14 classes against 7 family labels.** The inherited family column is coarser than the
   paper's classification. Leave-one-family-out over 7 folds is therefore a coarser split
   than the source supports. Per the brief the existing 7-fold definition is preserved so
   the new work stays comparable to the audit, but the coarsening is recorded here and the
   14-class mapping should be captured as an additional column for later use.
4. **One scalar per enzyme against a figure that probably shows several loci.** The
   inherited table holds a single `pe_efficiency_pct` per RT. If Figure 1C or Table S1
   reports efficiency at more than one target site, then the inherited scalar is an
   aggregate computed by someone else, by an unknown rule. Which locus, or which
   aggregation, is the single most important unresolved fact about the Task A label
   (`UNVERIFIED`).

### The blocking defect in Task A

Searched in this session: no DOI string appears anywhere in the tracked repository outside
`legacy_` directories, and `data/rt_sequences.csv` has no accession column (`MEASURED`).

So all 57 Task A rows currently fail the schema validator on `source_doi`,
`source_table`, and `reference_accession`. Task A cannot produce a passing `curated.csv`
by reformatting the inherited file. Every row needs its accession plus version resolved,
which means matching 57 RT names to database entries. This is the largest single piece of
work in Phase 2, and it is work that the inherited dataset deferred rather than did.

The 57 PDB models under `data/structures/` are named by the same RT names, so whatever
pipeline produced them consumed a sequence per name. Those files may carry a clue to the
original accessions and are worth inspecting before hand-resolving 57 accessions
(`UNVERIFIED`).

---

## Task B: within-protein variant effect, the priority source

### Source B1

| field | value | tag |
| --- | --- | --- |
| citation | Li H, Wang Y, Zhang C, Thi TT, Shi Y, Cheng KY, Hu C, Yu H. Saturated mutagenesis screen of M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency. bioRxiv, posted 2026-07-07 | `READ` |
| DOI | `10.64898/2026.07.06.736660` | `READ` |
| activity values held in | Supplementary Tables S6 and S7 | `READ`; which table is which stretch is `UNVERIFIED` |
| reference protein sequence held in | Supplementary Sequences 1 to 5, described as containing protein sequences | `READ` |
| expected variant rows | 1045 | `READ` for the two library sizes, `DERIVED` for the sum |
| expected wild-type rows | 1 | see the wild-type question below |
| licence | bioRxiv author-selected licence; the specific licence line was not read | `UNVERIFIED` |
| automatable | main text yes; supplementary files are separate media downloads and probably need a human | `UNVERIFIED` |

**Correction to the brief.** The brief gives this preprint as bioRxiv 2026.07.06.736660,
which reads as DOI prefix `10.1101`. That form returns "no posts found" from the bioRxiv
API (`READ`). The preprint resolves under prefix `10.64898`, so the DOI is
`10.64898/2026.07.06.736660`. Recording the wrong prefix on 1045 rows would have made
every Task B row cite a DOI that does not resolve.

### Label definition, verbatim

"log2((abundance of variant in GFP positive cells)/(abundance of variant in GFP negative
cells)) was calculated for each variant and for the wild-type construct. The editing
efficiency of all variants were then normalized and scaled between -1 to 1, with the
wild-type sequence set as the baseline (effect=0)." (`READ`)

Units: `normalized_-1_1`. Controlled vocabulary term:
`prime_editing_normalized_wt_centred`.

Open: whether the scaling to the interval was computed within each library or across both
(`UNVERIFIED`). This is why `library_stretch` is a required column and why the
stretch-held-out split is the honest Task B test rather than a nicety: if the two
libraries were scaled separately, then training on one and testing on the other is also a
test across two normalizations, and that has to be said out loud when the result is
reported.

### The two diversified stretches, and an arithmetic check that passes

Verbatim: "Stretch 1 spanning residues S60-Q84 (green) and Stretch 2 spanning residues
N95-D124 (magenta)" (`READ`).

Verbatim: "Library Stretch 1 (475 variants + WT) and Library Stretch 2 (570 variants +
WT)" (`READ`).

Check (`DERIVED`): S60 to Q84 inclusive is 25 positions, and 25 times 19 non-wild-type
substitutions is 475. N95 to D124 inclusive is 30 positions, and 30 times 19 is 570. Both
library sizes are exactly saturating. So the stated stretch boundaries and the stated
library sizes are mutually consistent, the libraries are complete rather than sampled, and
the expected variant count is 1045 with no missing substitution.

This check matters beyond tidiness: it means any parsed table with fewer than 475 or 570
rows per stretch has dropped variants, most likely at a read-count filter, and the parser
must log every one of them rather than accept a short table as normal.

### The wild-type row question

Each library carries its own wild-type construct, so the source plausibly reports two
wild-type measurements, one per stretch. Both are zero by construction, since the wild type
is the baseline the scaling is defined against. Two wild-type rows would carry an identical
sequence, which the schema rejects as a duplicate.

Resolution, to be applied in Phase 2 and documented: keep one wild-type row, with
`library_stretch` recorded as covering both libraries and the per-library raw log2 values
preserved in `notes`. This loses nothing, because the two values are both fixed at zero by
definition and are not independent measurements of anything.

### The reference sequence, which is the one thing that must be right

Verbatim: "We constructed a truncated PE variant (PE2ΔR) by removing the RNase H domain
(residues L499 to P677)" (`READ`).

Verbatim: "The pCMV-PE2ΔR plasmid was constructed via deleting RNaseH domain from RT of
pCMV-PE2 (#132775, Addgene)" (`READ`).

Three consequences, and one arithmetic conflict.

**First: the reference is not wild-type M-MLV RT.** PE2ΔR RT is derived from pCMV-PE2, so
it inherits whatever substitutions PE2's RT carries. PE2's RT is the M-MLV RT pentamutant
D200N, T306K, W313F, T330P, L603W. The preprint does not state this explicitly
(`READ`: the construct's mutation content is not given in the text that was read), so it
is an open item, but building variants on unmutated M-MLV RT when the screen was performed
on the pentamutant would put four wrong residues into all 1046 sequences.

**Second: L603W is inside the deleted region.** 603 falls within 499 to 677, so if PE2ΔR
deletes 499 to 677 then PE2ΔR RT carries D200N, T306K, W313F, and T330P, and does not carry
L603W (`DERIVED`). The reference is therefore a tetramutant truncation, not a pentamutant
one. This must be confirmed against the supplementary protein sequence, not accepted from
this derivation.

**Third, the conflict: 671 against 677.** UniProt P03355, sequence version 5 dated
2018-01-31, Gag-Pol polyprotein of Moloney murine leukemia virus, total length 1738, carries
CHAIN "Reverse transcriptase/ribonuclease H (p80)" at 660 to 1330 (`READ`). That chain is
1330 minus 660 plus 1, so 671 residues (`DERIVED`). The preprint numbers the deleted RNase H
region to residue 677, which implies a 677-residue RT, six residues longer than the
canonical chain (`DERIVED`).

Six residues is exactly the size of offset that silently shifts a whole library. It must be
resolved before a single variant sequence is constructed, and it is resolvable, because the
source gives seven independent anchors:

| anchor | required residue | source of the requirement |
| --- | --- | --- |
| 60 | S | stretch 1 start, "S60" |
| 61 | I | reported mutation I61R |
| 67 | S | reported mutation S67W |
| 84 | Q | stretch 1 end, "Q84" |
| 95 | N | stretch 2 start, "N95" |
| 101 | V | reported mutation V101R |
| 124 | D | stretch 2 end, "D124" |
| 499 | L | deletion start, "L499" |
| 677 | P | deletion end, "P677" |

Nine, counting the two deletion boundaries. The Phase 2 parser asserts all of them against
whichever reference is adopted, and halts on any mismatch. The resolution order is:

1. take the PE2ΔR RT protein sequence from the preprint's Supplementary Sequences, which is
   the source's own statement of its own construct and therefore authoritative
2. cross-check it against P03355 residues 660 to 1330, recording the offset between the
   paper's numbering and the canonical chain explicitly, whatever it turns out to be
3. cross-check against the Addgene 132775 deposited sequence for the pentamutant question
4. record the adopted accession plus version, the truncation boundaries, and the offset in
   `tasks/taskB_mmlv_dms/PROVENANCE.md`, and store the sequence at
   `tasks/taskB_mmlv_dms/raw/reference.fasta`

Anchors 499 and 677 are the diagnostic pair. If the adopted sequence has L at 499 and P at
677 then the paper's numbering is internally consistent and the canonical chain is simply
not the right frame of reference. If it has L at 499 and ends at 671, then the paper's 677
is an error and the deletion boundary needs its own note. Either outcome is reportable; a
guess is not.

Until step 1 is done, no Task B sequence is constructed. This is what Gate G2 exists to
confirm.

---

## Task A extension candidates: the PE6 join question

The brief asks for the argument to be put in this report and for the human to rule at Gate
G1 rather than for the decision to be taken silently.

### What they are

From the same publication as Task A (`READ`, single page, needs confirmation): PE6a is an
evolved Ec48 retron RT; PE6b is an evolved Tf1 retrotransposon RT; PE6c is Tf1, evolved and
engineered; PE6d is M-MLV RT, evolved and engineered and RNase H truncated; PE6e through
PE6g are M-MLV RT paired with evolved Cas9 domains. Note that the brief says PE6a to PE6d;
the series runs to PE6g.

Their measured prime editing efficiencies were not read in this session and are
`UNVERIFIED`. They live in the same supplementary set as Task A.

### The case for joining Task A

The readout is the same class of quantity, percent precise editing in HEK293T, from the same
laboratory in the same paper. Of every candidate source considered here, this one has the
smallest assay gap to Task A. And n is the binding constraint on Task A: the audit measured
a Kish effective sample size of 11.3 against 57 nominal rows, so rows are worth a great
deal.

### The case against, which is stronger

1. **They were selected for the label.** PE6 variants are the product of phage-assisted
   continuous evolution under selection for prime editing activity. A panel of evolved
   variants is enriched for actives by construction. Task A's base rate is 21 of 57; adding a
   near-all-active cohort moves both the class balance and the label distribution for a
   reason that has nothing to do with any model. PR-AUC and the weighted Spearman would both
   shift, and the shift would be an artifact of who was selected into the panel.
2. **They are not orthologs, and they collide with rows already present.** PE6b and PE6c
   both descend from Tf1, and Tf1-RT is already a Task A row at 34 percent. PE6d through
   PE6g descend from M-MLV RT, already a Task A row at 41 percent. Under
   leave-one-family-out, evolved descendants land in the same fold as their parents, where
   they are near-identical to a sequence in that fold. That does not add independent
   information; it adds redundancy inside folds, which lowers effective sample size rather
   than raising it. Adding rows that reduce effective n is worse than adding nothing.
3. **They are variants of one protein, which is Task B's shape, not Task A's.** Task A asks
   whether a representation transfers across families. A handful of point-mutated
   descendants of two proteins already in the panel does not test that question.
4. **The assay context is close but not identical.** Efficiency is strongly dependent on
   target locus, editor scaffold, and guide format, and the PE6 characterization uses the
   evolved editors' own contexts rather than the survey's. Same units does not mean same
   measurement.

### Recommendation

Do not join Task A. If these rows are wanted, open `tasks/taskA2_evolved/` as its own task
with its own split, used as a transfer cohort that a Task A model is evaluated on but never
trained with. That keeps the existing 7-fold leave-one-family-out definition intact, which
the brief requires for comparability with the audit, and it keeps a selected panel out of a
natural panel.

**This is a recommendation, not a decision. Tanish rules at G1.**

---

## Task C group

Each Task C set was scoped by literature search in this session. The finding is the same in
all three cases and it is a negative one, so it is stated plainly here rather than worked
around.

### Task C, retron

No single-study quantified panel of many retron RTs was found. The best-confirmed material
is four experimentally validated E. coli retrons, Ec48, Ec73, Ec86, and Ec107, assayed for
msDNA production in human cells (`READ`, from a search result summary; the primary source
was not opened). That is n near 4.

One source that looks larger is not: retron library recombineering, as in Schubert et al.
PNAS 2021, varies the donor sequence while holding one RT fixed. It is a large dataset about
donors, not a panel of reverse transcriptases, so it carries no cross-RT label at all
(`UNVERIFIED` as to its exact design).

**Assessment: n is too small to support a task.** A four-row table cannot be split, cannot
support a metric with a usable confidence interval, and would add a third label scale for
no return. Recommend marking `taskC_retron` as blocked rather than building it. If it is
built at all, it is representation-analysis only and reports no performance number.

### Task C, DGR

The quantitative DGR literature is concentrated on a single reverse transcriptase, the BPP-1
bRT, rather than on a panel. Reported quantities include roughly 30 percent of template
adenines converted during mutagenic homing, which is a property of one element, not a
comparative activity measurement across enzymes (`READ`, from search result summaries).

Two candidates were seen but not opened (`UNVERIFIED`): a high-throughput analysis of a
reconstituted DGR, which from its title varies the element and target rather than the RT and
so is Task-B-shaped rather than Task-C-shaped; and a 2026 Nature Biotechnology paper on DGRs
for programmable targeted hypermutagenesis.

**Assessment: no cross-RT DGR activity panel is established to exist.** Recommend marking
`taskC_dgr` as blocked, with the two candidates recorded for a human to check.

### Task C, in vitro retroviral kinetics

Comparative in vitro measurements across retroviral RTs exist, but they are spread across
decades, laboratories, templates, buffers, and quantity definitions: specific activity,
processivity, misinsertion efficiency, and error rate are not one label. No single study
supplying one assay across a usable number of enzymes was found (`READ`, from search result
summaries).

This matters more than the small n. Compiling values from many papers into one column would
reintroduce, one level down, exactly the incommensurability that the whole multi-task design
exists to prevent. The confound would simply move from "which family" to "which laboratory
in which decade".

**Assessment: cannot be built as a single-assay task from a single publication.** Recommend
marking `taskC_retroviral` as blocked. If a single-study panel is later identified, it gets
its own task with the study's own units, and it is still never pooled.

---

## Expected row counts, as a checklist for Phase 2

| task | expected n | tag | status |
| --- | --- | --- | --- |
| A | 59 surveyed, 57 inherited, 20 or 21 active | `READ` and `MEASURED` | reconciliation needed, accessions missing for all 57 |
| B | 1045 variants plus 1 wild type | `READ` and `DERIVED` | blocked on the reference sequence |
| A2 evolved, if opened | PE6a to PE6g, so 7 | `READ` | blocked on a G1 ruling |
| C retron | near 4 | `READ` | recommend blocked, n too small |
| C DGR | not established | `UNVERIFIED` | recommend blocked |
| C retroviral | not established as one assay | `READ` | recommend blocked |

## Blocking items, in the order they must be resolved

1. The Task B reference sequence, including the 671 against 677 numbering conflict and the
   pentamutant question. Everything in Task B inherits this.
2. Task A accessions and DOIs for all 57 rows. Without them no Task A row passes the
   validator.
3. The Task A label's provenance: which locus, or which aggregation rule, produced one
   scalar per enzyme.
4. The 57 against 59 and 21 against 20 reconciliations.
5. Licences for both supplementary sets, which decide whether raw files may be committed or
   only fetched by a script.
6. The G1 ruling on PE6.

## What this plan does not contain

No activity value. No sequence. No performance number. No model. Nothing here has been
downloaded, and the correct response to a source that turns out to be unobtainable is a line
in `reports/data_pipeline_report.md`, not a workaround.

---

# Gate G1 outcome, 2026-09-30

Endorsed by Tanish. Three rulings, all recorded here as decisions taken rather than
defaults assumed.

## Ruling 1: PE6 becomes its own cohort

The recommendation was accepted. `tasks/taskA2_evolved/` is opened with task identifier
`A2`, its own assay term `prime_editing_pct_HEK293T_evolved_editor`, and evaluation-only
use. The existing Task A 7-fold leave-one-family-out definition is untouched, so the audit
comparison holds. The schema now refuses to stack `A2` onto `A`, and
`test_evolved_cohort_cannot_be_stacked_onto_task_a` proves it.

## Ruling 2: all three Task C sets are blocked

The recommendation was accepted. `tasks/taskC_retron/`, `tasks/taskC_dgr/`, and
`tasks/taskC_retroviral_invitro/` each carry a `PROVENANCE.md` with status BLOCKED, NOT
BUILT, the reason, and the condition that would change it. `raw/` stays empty in all three.
The finding is stated as "no suitable panel was found", which is weaker than "none exists",
because a literature search is not a proof of absence.

The benchmark is therefore Task A, Task A2, and Task B. That is where the scientific
contrast lives in any case: a cross-family transfer task against a within-protein variant
effect task, which is the comparison the deliverable rests on.

## Ruling 3: automated fetch attempted first

Attempted, with a partial result.

### Obtained

| file | task | licence | note |
| --- | --- | --- | --- |
| `preprint.pdf` | B | CC-BY-NC 4.0, read from the PDF's own per-page banner | committed to `raw/`; 23 pages; includes Supplementary Figures 1 to 4 |
| `uniprot_P03355.fasta` | B | CC-BY 4.0 | `SV=5`; the canonical RT frame |

The licence question for Task B is therefore closed: CC-BY-NC 4.0 permits redistribution
with attribution for non-commercial use, so the preprint is committed rather than only
scripted.

### Not obtained, and the attempts made

Supplementary Sequence 1 and Tables S5 to S7 are referenced in the preprint but are not in
the main PDF and were not reachable:

- the supplementary-material page returns HTTP 200, but its static HTML lists no files,
  contains no `media-N` reference, and contains no occurrence of the word "supplement" in
  its rendered text, which means the listing is either client-rendered or absent
- legacy bioRxiv adjunct paths under `.../DC1/embed/media-1.{pdf,xlsx}` return HTTP 404
- `highwire/filestream/5608071/field_highwire_adjunct_files/{0..4}/media-{1..5}.{pdf,xlsx,docx,zip}`,
  twenty combinations, all non-200
- the `.full-text` view returned HTTP 429, at which point probing stopped rather than
  continuing to hammer the host
- Addgene 132775 was tried as a fallback for the substitution question: the sequences page
  returns HTTP 200 but embeds no sequence in static HTML, and the GenBank file derived from
  the map image path returned HTTP 404

Cell's Table S1 was not attempted, because an Elsevier supplementary file behind the
article interstitial is not scriptable and the checklist already says so.

**So the manual fetch list shrinks but does not disappear.** What a human still has to get
is in `data_acquisition/MANUAL_FETCH.md`: the bioRxiv supplementary bundle, and Cell Table
S1.

## Blocking item 1 is now closed

The Task B numbering conflict is resolved, and the resolution is recorded in
`tasks/taskB_mmlv_dms/PROVENANCE.md` with a reproducing script at
`data_acquisition/resolve_mmlv_reference.py`.

Nine anchors, being every residue identity the preprint states, all match UniProt P03355
`SV=5` under the hypothesis that the preprint's RT residue 1 is the first residue of the
annotated p80 chain at Gag-Pol 660. A second confirmation, independent of the anchors,
reproduces the preprint's own two arithmetic statements exactly: retained residues 1 to 498
give 1494 base pairs as stated, and 179 deleted of 677 gives 0.2644, which rounds to the
stated 26.4 percent.

671 against 677 dissolves. Both are right about different things: the preprint's RT extends
six residues past the annotated p80 chain, to Gag-Pol 1336, into the region UniProt assigns
to integrase, and those residues are `IENSSP`, ending in the P the preprint calls P677.
There is no offset in either source.

One question on the reference stays open: whether PE2dR retains PE2's RT substitutions.
L603 falls inside the deleted region, so the reference is most likely a tetramutant
truncation carrying D200N, T306K, W313F, T330P and not L603W. That is a derivation, and the
strings "pentamutant", "D200N", and "L603W" appear nowhere in the PDF, so the file written
is named `reference_candidate_unconfirmed.fasta`, carries no substitutions, and no parser
may consume it.

## Revised blocking list

1. ~~The Task B reference frame.~~ Closed.
2. Task B substitution content, from Supplementary Sequence 1.
3. Task B activity values, from Tables S6 and S7. Without these Task B has no labels.
4. Task A accessions and DOIs for all 57 rows.
5. The Task A label's provenance: which locus, or which aggregation rule.
6. The 57 against 59 and 21 against 20 reconciliations.
7. Task A2 efficiencies, from the same Cell supplementary set.

Items 2, 3, 4, 5, 6, and 7 all depend on files a human must download. Phases 2 and 3 cannot
complete until then.
