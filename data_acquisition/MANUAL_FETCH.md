# Manual fetch checklist

Files a human has to download, because they sit behind a publisher interstitial or a
JavaScript page that a script cannot get through. Nothing here has been fetched yet.

Read `reports/acquisition_plan.md` first: it says what each file is expected to contain and
what question each one answers. This file says only where to get it and where to put it.

## Rules for handling a downloaded file

1. **Place the file exactly as downloaded.** Do not open and re-save a spreadsheet. Excel
   can rewrite a numeric cell to its displayed precision on save, and a silently rounded
   activity value is an invented activity value.
2. **Rename, do not convert.** Use the target filename given below so the parsers can find
   it. Changing the extension or exporting to CSV by hand is a conversion; let the parser do
   it, so the conversion is code that can be inspected and rerun.
3. **Record the licence.** For each file, note on the publisher page whether redistribution
   is permitted, and write that into the task's `PROVENANCE.md`. This decides whether the
   file may be committed to `raw/` or whether only a fetch script may be.
4. **Do not fill a gap.** If a file is not obtainable, leave it absent and say so. The
   parsers are written to fail loudly on a missing input. That failure is the correct
   outcome, and it goes in the report.
5. After placing files, run the checksum pass so every file is pinned:
   `python schemas/task_schema.py --help` is not the tool for this; the Phase 2 parsers print
   each input's SHA256 on every run, and those hashes are what `PROVENANCE.md` records.

## Priority 1: Task B, the saturated mutagenesis screen

This is the priority source in the brief, and item 1 on the blocking list. The reference
sequence in particular gates all 1046 Task B rows.

**Article page:** `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1`

Note the DOI prefix is `10.64898`, not `10.1101`. The `10.1101` form does not resolve.

| what | where | save to | why it is needed |
| --- | --- | --- | --- |
| Supplementary material bundle | the article page, "Supplementary Material" tab: `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material` | `tasks/taskB_mmlv_dms/raw/` keeping each file's original name, then note the mapping in `PROVENANCE.md` | holds Tables S1 to S7 and Supplementary Sequences 1 to 5 |
| Supplementary Sequences 1 to 5, whichever file contains them | same bundle | `tasks/taskB_mmlv_dms/raw/supplementary_sequences.pdf` or the original extension | **the PE2ΔR RT protein sequence.** This is the single most important file in the whole pipeline. Everything in Task B is built on it |
| Tables S6 and S7 | same bundle | `tasks/taskB_mmlv_dms/raw/table_s6.xlsx` and `table_s7.xlsx`, or the original names if they arrive as one workbook | the per-variant activity values for the two libraries |
| Main text PDF | `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.full.pdf` | `tasks/taskB_mmlv_dms/raw/preprint.pdf` | so the verbatim label definition and the stretch boundaries can be re-checked offline |
| Licence line | the article page sidebar | record in `PROVENANCE.md` | decides whether the above may be committed |

**When you have the sequences file, check these before anything else.** They are the
anchors the parser will assert, and they are what Gate G2 asks a human to confirm:

- residue 60 is S, 61 is I, 67 is S, 84 is Q
- residue 95 is N, 101 is V, 124 is D
- residue 499 is L, and the residue the paper calls P677 is P
- whether the sequence carries D200N, T306K, W313F, T330P, and whether L603W is present or
  was removed with the RNase H domain
- the total length of the retained RT

If the numbering in the file disagrees with the paper's stated stretch boundaries, stop and
say so. Do not adjust an offset to make it fit.

### Supporting fetch, for the pentamutant question

| what | where | save to |
| --- | --- | --- |
| pCMV-PE2 deposited full sequence | `https://www.addgene.org/132775/sequences/` | `tasks/taskB_mmlv_dms/raw/addgene_132775_pCMV-PE2.gb` |

Only needed if the supplementary sequences do not settle which substitutions the parent RT
carries.

## Priority 2: Task A, the cross-family survey

Needed to resolve four reconciliation questions and, above all, to supply the accessions and
DOIs that all 57 inherited rows currently lack.

**Article:** Doman JL, Pandey S, Neugebauer ME, et al. Cell 186(18):3983-4002.e26, 2023.
DOI `10.1016/j.cell.2023.07.039`.

**Article page:** `https://www.cell.com/cell/fulltext/S0092-8674(23)00854-1`
Supplementary section: same URL with `#supplementaryMaterial`.

| what | where | save to | why it is needed |
| --- | --- | --- | --- |
| Supplementary Table S1 | the article's supplementary material list; Cell serves these as `mmc1.xlsx`, `mmc2.xlsx` and so on, so check which one is S1 | `tasks/taskA_crossfamily/raw/doman2023_table_s1.xlsx`, keeping the original `mmcN` name recorded in `PROVENANCE.md` | the RT panel: names, classes, and prime editing efficiencies |
| Any supplementary table holding RT protein sequences or accessions | same list | `tasks/taskA_crossfamily/raw/` with a descriptive name | the accessions the inherited table is missing |
| Figure 1C source data, if the journal provides it separately | same list | `tasks/taskA_crossfamily/raw/` | the per-locus efficiencies, which decide whether the inherited scalar is an aggregate |
| Main text PDF | `https://www.cell.com/cell/pdf/S0092-8674(23)00854-1.pdf` | `tasks/taskA_crossfamily/raw/doman2023.pdf` | the verbatim label definition and the activity threshold |
| Licence and redistribution terms | the article page | record in `PROVENANCE.md` | Elsevier terms are likely to forbid committing the raw file, in which case `raw/` holds a note and a fetch script instead |

**When you have Table S1, answer these four questions and write the answers into
`tasks/taskA_crossfamily/PROVENANCE.md`:**

1. Which 2 of the 59 surveyed enzymes are absent from the inherited 57, and why.
2. Is `MMLV-RT` one of the 59, or the benchmark control? Is `Ne144-RT` at 0.5 percent called
   active by the paper? One of these explains 21 actives against the paper's 20.
3. What is the paper's 14-class assignment for each enzyme, so the coarsening to 7 families
   is recorded rather than assumed.
4. Does the table report one efficiency per enzyme or several, one per target locus? If
   several, what rule produced the single inherited number?

## Priority 3: PE6, only after Gate G1

Do not fetch until Tanish has ruled on the PE6 join question in
`reports/acquisition_plan.md`. The recommendation there is not to join Task A, and to open a
separate transfer cohort if these rows are wanted at all.

The values live in the same Cell supplementary set as Task A, so if that set is downloaded
for Priority 2 nothing further needs fetching; only the ruling is needed.

## Not manual: fetches a script can do

Listed here so nobody downloads them by hand.

| what | how |
| --- | --- |
| UniProt P03355, Gag-Pol of Moloney murine leukemia virus | `https://rest.uniprot.org/uniprotkb/P03355.fasta`, scriptable; the RT/RNase H p80 chain is residues 660 to 1330 |
| Any UniProt or NCBI accession resolved for a Task A row | the respective REST API, scriptable |

These are fetched by a Phase 2 script that records each accession's version and SHA256, not
by hand.

## Task C: nothing to fetch

All three Task C sets are recommended as blocked in `reports/acquisition_plan.md`: the retron
panel is about four enzymes, no cross-RT DGR activity panel is established to exist, and the
in vitro retroviral measurements are scattered across many studies with incompatible label
definitions. Compiling the last of these would move the confound from "which family" to
"which laboratory", which is the same defect the task partition exists to prevent.

If a human wants one of them opened anyway, the two unopened DGR candidates named in the
acquisition plan are the place to start, and whatever is opened gets its own task and its own
units.
