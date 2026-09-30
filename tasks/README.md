# Task partition

One directory per task. One assay per task. One label column per task, in that assay's
own units. There is no directory here that holds a merged label, and there is no code
path in this repository that produces one.

| directory | task id | assay | label |
| --- | --- | --- | --- |
| `taskA_crossfamily/` | `A` | prime editing in HEK293T, percent precise edits | `pe_efficiency_pct` |
| `taskA2_evolved/` | `A2` | prime editing in HEK293T, evolved editors in their own scaffolds | percent, evaluation only |
| `taskB_mmlv_dms/` | `B` | prime editing, normalized so wild type is zero | normalized variant effect |
| `taskC_retron/` | `C_retron` | msDNA production or recombineering efficiency | per source |
| `taskC_dgr/` | `C_dgr` | mutagenic homing or adenine mutagenesis rate | per source |
| `taskC_retroviral_invitro/` | `C_retroviral` | in vitro polymerase kinetics | per source |

Status as of 2026-09-30: Task A is inherited but blocked on accessions; Task B has its
reference frame resolved but is blocked on activity values; `taskA2_evolved/` was opened by
the Gate G1 ruling and is not yet acquired; all three Task C directories are blocked, with
the reason in each `PROVENANCE.md`.

Each directory holds:

- `raw/` unmodified source files exactly as downloaded, or a note saying why a file could
  not be committed
- `curated.csv` the task table, which must pass `schemas/task_schema.py`
- `splits/` frozen split definition files, written once and not regenerated at model time
- `PROVENANCE.md` every source, with DOI, access date, and the reconciliation from the
  parser run

## Why the labels are never merged

Assay type is almost perfectly confounded with RT family. Prime editing efficiency,
retron msDNA yield, DGR mutagenesis rate, and in vitro nucleotide incorporation are four
different physical quantities. If they shared a column, a leave-one-family-out split
would silently become a leave-one-assay-out split, and a model fitted on it could score
well by learning which publication a sequence came from. The schema validator enforces
this: it rejects a table carrying two tasks, rejects inconsistent units inside a task, and
refuses to concatenate tables whose `label_units` differ.

Cross-task comparisons are still scientifically interesting, and they are the point of
running Task A and Task B together. They happen in explicitly labelled
representation-analysis code that keeps the label columns separate, never by stacking
rows.
