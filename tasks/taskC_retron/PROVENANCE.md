# Provenance: Retron RT activity

Task identifier: `C_retron`
Directory: `tasks/taskC_retron/`
Status: **BLOCKED, NOT BUILT**

Blocked by the Gate G1 ruling of 2026-09-30. `raw/` is empty and stays empty. No
`curated.csv` exists and none is planned.

## Why

The retron literature does not supply a quantified panel of many retron reverse
transcriptases measured under one assay. The best-confirmed material found is four
experimentally validated E. coli retrons, Ec48, Ec73, Ec86, and Ec107, assayed for msDNA
production in human cells. That is n near 4: it cannot be split, cannot support a metric with
a usable interval, and would add a third label scale for no return.

One source that looks larger is not. Retron library recombineering, as in Schubert et al.
PNAS 2021, varies the donor sequence while holding one RT fixed. It is a large dataset about
donors, and carries no cross-RT label at all.

Note that five retron RTs already appear as active rows inside Task A, measured as prime
editing efficiency. That is the assay Task A uses, and those rows stay in Task A. A retron
msDNA yield is a different physical quantity and is not convertible into it.

## What was done to establish this

Literature search in this session, recorded in `reports/acquisition_plan.md` with the network
log. No primary source was opened, so the finding is that no suitable panel was *found*, which
is a weaker claim than proving none exists. It is stated that way deliberately.

## What would change this

A single publication measuring a usable number of distinct reverse transcriptases under one
assay, with the label definition stated in the paper's own units. If one is identified, this
directory is opened as its own task, with its own split and its own reported metric, and it is
never pooled with Task A, Task B, or another Task C set.

## Status in the report

This negative finding is carried into `reports/data_pipeline_report.md` as a gap, not as a
workaround. Per the brief, negative results and gaps are preserved.
