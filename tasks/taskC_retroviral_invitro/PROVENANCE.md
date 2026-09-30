# Provenance: In vitro retroviral RT kinetics

Task identifier: `C_retroviral`
Directory: `tasks/taskC_retroviral_invitro/`
Status: **BLOCKED, NOT BUILT**

Blocked by the Gate G1 ruling of 2026-09-30. `raw/` is empty and stays empty. No
`curated.csv` exists and none is planned.

## Why

Comparative in vitro measurements across retroviral RTs exist, but no single study was found
supplying one assay across a usable number of enzymes. The values are spread across decades,
laboratories, templates, buffers, and quantity definitions, and specific activity,
processivity, misinsertion efficiency, and error rate are not one label.

The small n matters less than the structure. Compiling values from many papers into one column
would reintroduce, one level down, exactly the incommensurability the task partition exists to
prevent: the confound would move from which family to which laboratory in which decade. A
leave-one-family-out split over such a column would silently be a leave-one-publication-out
split, which is the defect this benchmark was rebuilt to remove.

If a single-study panel is later identified, it gets its own task with that study's own units,
and it is still never pooled.

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
