# Provenance: evolved and engineered prime editor RTs, transfer cohort

Task identifier: `A2`
Directory: `tasks/taskA2_evolved/`
Status: **NOT ACQUIRED**

## Why this task exists separately

Opened by the Gate G1 ruling of 2026-09-30. The PE6 series was considered for inclusion in
Task A and kept out, for reasons recorded in `reports/acquisition_plan.md`:

1. These enzymes were selected for the label. They are the product of continuous evolution
   under selection for prime editing activity, so the cohort is enriched for actives by
   construction. Pooling them into Task A would move its base rate away from 21 of 57 for a
   reason that has nothing to do with any model.
2. They collide with rows already in Task A. PE6b and PE6c descend from Tf1, and PE6d
   through PE6g from M-MLV RT; both parents are already Task A rows. Under
   leave-one-family-out an evolved descendant lands in the same fold as its parent, where it
   is near-identical to a sequence already there. That adds redundancy inside folds and
   lowers effective sample size rather than raising it.
3. They are point variants of two proteins, which is Task B's shape, not a test of
   cross-family transfer.
4. Efficiency was measured in each evolved editor's own scaffold, guide format, and locus
   panel, not in the survey's context. Same units is not the same measurement.

So this cohort carries its own assay term, `prime_editing_pct_HEK293T_evolved_editor`, and
the schema refuses to stack it onto Task A. `schemas/test_task_schema.py` proves that
refusal in `test_evolved_cohort_cannot_be_stacked_onto_task_a`.

**Intended use: evaluation only.** A Task A model may be evaluated on this cohort as a
transfer check. It is never training data for Task A, and no Task A metric is computed over
a pool that includes it.

## How descent is recorded

`derived_from_rt` names the Task A enzyme each row descends from, as text. It is not a
`parent_id`, because `parent_id` must resolve inside its own table and a cross-task pointer
would be the first step of a merge. The near-duplicate relationship with Task A is surfaced
instead by the Phase 3 cross-task identity clustering, which is where it belongs, because
that measures the redundancy rather than asserting it.

`mutations` is left empty. Each evolved RT carries many substitutions relative to its parent
and is treated as its own protein, not as a variant row.

## Sources

Expected from the same publication and the same supplementary set as Task A: Doman JL,
Pandey S, Neugebauer ME, et al., Cell 186(18):3983-4002.e26, 2023, DOI
`10.1016/j.cell.2023.07.039`. Nothing further needs downloading beyond the Task A
supplementary material.

Expected rows: PE6a through PE6g, so 7. Note the series runs to PE6g; the brief said PE6d.

| field | value |
| --- | --- |
| parent RTs | PE6a from Ec48 retron RT; PE6b and PE6c from Tf1 retrotransposon RT; PE6d from M-MLV RT, RNase H truncated; PE6e to PE6g from M-MLV RT with evolved Cas9 domains |
| verification | read from the PMC copy of the article in this session, one page only; confirm against the article |
| efficiencies | not read; `UNVERIFIED` |
| licence | Elsevier, same as Task A; `UNVERIFIED` |

## Open questions

1. The measured efficiencies, and which table or figure holds them.
2. Whether PE6e to PE6g differ from each other only in the Cas9 domain. If so their RT
   sequences may be identical, which the schema rejects as duplicate sequences. The correct
   response then is one row per distinct RT, with the editors sharing it recorded in
   `notes`, and never a duplicated sequence.
3. Whether the locus panel is stated per editor, since the label is only meaningful with it.
