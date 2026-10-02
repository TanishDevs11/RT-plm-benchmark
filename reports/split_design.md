# Split design and redundancy control

Phase 3. Written 2026-09-30. Covers the identity clustering, the frozen split files, and what
leakage each split regime does and does not prevent.

Reproduce with:

    python curation/cluster_redundancy.py --mmseqs <path>
    python curation/define_splits.py

## Redundancy control

### Tool and parameters, fixed a priori

MMseqs2, commit `8cc5ce367b5638c4306c2d7cfc652dd099a4643f`, Windows build obtained from the
project's GitHub releases. The Windows build runs through a busybox compatibility layer whose
helper tools must be installed before `easy-cluster` will run; that is a packaging detail, not
a methodological one, and it is recorded so the run reproduces.

| parameter | value | why |
| --- | --- | --- |
| thresholds | 90, 70, 50 percent identity | as the brief specifies |
| `-c` | 0.8 | coverage fraction required |
| `--cov-mode` | 1, coverage over the target | see below; this is not the default and the choice is load bearing |
| `-s` | 7.5 | high sensitivity; the panel is tiny so speed is irrelevant, and a missed homology would understate leakage |

**Why coverage over the target rather than the default bidirectional coverage.** These
sequences are excised domains with different boundaries. The Task A M-MLV RT row is 677
residues; the Task B parent is the same protein truncated to 498. Their bidirectional coverage
is 498 divided by 677, which is 0.74, so under the default at `-c 0.8` they would not cluster
and the single most important cross-task duplicate in this benchmark would go unreported.
Coverage over the target detects containment, which is what redundancy between differently
excised domains actually looks like.

### Task A cluster structure

57 sequences. Assignments are in `tasks/taskA_crossfamily/splits/clusters_{90,70,50,30}.tsv`.

| threshold | clusters | size distribution | clusters crossing a family boundary |
| --- | --- | --- | --- |
| 90 percent | 53 | 49 singletons, 4 pairs | 0 |
| 70 percent | 49 | 44 singletons, 3 pairs, one triple, one quadruple | 0 |
| 50 percent | 44 | 39 singletons, 3 pairs, one quadruple, one cluster of 8 | 0 |
| 30 percent | 24 | 14 singletons, 2 pairs, 4 triples, one quadruple, one of 5, one of 8, one of 10 | **4** |

### Finding 1, corrected 2026-10-03: no cluster crosses a family boundary above 50 percent, but four do at 30

**This section previously claimed that no cluster crosses a family boundary at any
threshold. That claim was threshold-limited and is now known to be false at 30 percent.**
It was written when only 90, 70 and 50 percent had been computed. 30 percent was added in
the Phase 2 rerun, and it is the threshold at which the claim fails.

At 90, 70 and 50 percent the original finding holds: every multi-member cluster lies
entirely inside one family, so holding out a family also holds out an identity cluster and
there is no train-test pair above 50 percent identity across a fold boundary.

At 30 percent, four clusters cross a family boundary:

- `CaMV-RT` (Other) with `Tf1-RT` and `Ty3-RT` (LTR_Retrotransposon)
- `AFY36037.1-RT` (Unclassified) with `DRG2-RT` and `Drg-RT` (Other)
- `A.platensis-Cas1-RT`, `FuRT-Cas1-RT`, `Med-CasRT` (CRISPR-associated) with `Gs-RT`
  (Group_II_Intron) and `Rs-RT` (Retron)
- `CRISPRRT2-RT` (CRISPR-associated) with `Er-RT`, `GroupII_CLA-RT` and `Tel4c-RT`
  (Group_II_Intron)

So leave-one-family-out does **not** hold out an identity cluster at 30 percent, and 30
percent is the conventional line below which two proteins are not assumed homologous. For
the families involved, holding out the family still leaves relatives above 30 percent
identity in the training set.

These look like genuine phylogeny rather than labelling errors. Three of the four join
bacterial families to each other, which is consistent with CRISPR-associated RTs being
derived from group II intron RTs; the fourth joins a caulimovirus RT to LTR retrotransposon
RTs, and caulimoviruses are pararetroviruses. Two of the four involve `Other` or
`Unclassified`, which are catch-all labels rather than clades, so part of what the 30
percent clustering exposes is that the 7-way labelling is not purely phylogenetic.

What this changes: the leave-one-family-out result may be read as holding out a clade at
the 50 percent level, which is still a meaningful cross-lineage test, but not as holding
out all detectable homology. The leave-one-cluster-out split at 70 percent is the stricter
control, and the remote homology at 30 percent is a stated limitation rather than something
either split removes.

### Finding 2: the redundancy is concentrated in the family that carries the signal

The redundancy that exists is almost entirely inside `Retroviral`, which is also the largest
fold and holds 12 of the 21 actives.

At 50 percent identity, 8 of the 18 retroviral sequences form one cluster: AVIRE, BAEMV,
FENV1, GALV, KORV, MMLV, PERV, WMSV, of which 7 are active. A further 4 form a second cluster:
MMTV, MPMV, POL11ERV, SRV2, all active. So 12 of 18 retroviral rows sit in just 2 clusters.

The consequence is that the retroviral fold's 18 rows are worth far fewer than 18 independent
observations. When it is held out, the test set is a handful of independent items wearing 18
row labels; when it is in training, it contributes correspondingly less independent
information than its row count suggests. This is a sequence-level explanation for the audit's
Kish effective sample size of 11.3 against 57 nominal rows: the shortfall is not spread
evenly, it is concentrated exactly where the positives are.

### Finding 3: a near-duplicate pair with opposite activity calls

`ASLV-RT` and `RSVSB-RT` cluster together at 90 percent identity and carry opposite binary
labels, active and inactive. At 70 percent, `BAEMV-RT` (active), `FENV1-RT` (inactive), and
`MMLV-RT` (active) cluster together.

Two readings, and the data here cannot separate them: either prime editing activity turns on
a small number of residues, so that highly similar RTs genuinely differ, or one of these
calls is noise. Either way, no method that works by sequence similarity can get both members
of such a pair right, and a benchmark with 21 positives is not going to resolve which reading
is correct. This belongs in the interpretation of any Task A result and is recorded here so it
is not discovered afterwards.

### Cross-task clustering: not yet possible

Only Task A has sequences. Task B is blocked on its activity values and Task A2 has not been
acquired, so the cross-task comparison has not been run.

**This is an open item, not a clean bill of health.** The specific duplicate the brief names,
M-MLV RT appearing both as a Task A row and as the Task B parent, is known to exist by
inspection: the inherited Task A `MMLV-RT` sequence is 677 residues and is the same protein as
the 498-residue Task B parent, differing from UniProt P03355 at exactly one position, RT
position 8, which is Y in the inherited sequence and H in P03355. It has not been measured by
clustering because Task B does not exist yet. When it does,
`curation/cluster_redundancy.py` writes `reports/clusters_cross_task_{90,70,50}.tsv` and prints
every cluster spanning more than one task.

The practical consequence to carry forward: any statement of the form "the representation
transfers from Task B to Task A" has to account for the fact that Task B's parent protein is
itself a Task A row, and the most active one at 41 percent.

## Split definitions

All frozen as files. Nothing regenerates a split at model time.

### Task A: leave-one-family-out, 7 folds

`tasks/taskA_crossfamily/splits/leave_one_family_out.csv`, 399 assignment rows, being 57 ids
times 7 folds, each row carrying `id`, `fold`, `role`.

The inherited family definition is preserved exactly, as the brief requires, so the new work
stays comparable to the existing audit. Note from Phase 1 that the source publication spans 14
classes while the inherited column has 7 labels, so this is a coarser split than the source
supports; the coarsening is inherited deliberately, not chosen.

| fold | n | positives |
| --- | --- | --- |
| Retroviral | 18 | 12 |
| Retron | 12 | 5 |
| LTR_Retrotransposon | 11 | 2 |
| CRISPR-associated | 5 | 0 |
| Group_II_Intron | 5 | 2 |
| Other | 5 | 0 |
| Unclassified | 1 | 0 |

**Finding 4: three of the seven folds contain no positive.** When `CRISPR-associated`, `Other`,
or `Unclassified` is the held-out fold, the test set is all-negative. A ranking correlation is
undefined on it and a precision-recall measurement is degenerate. So the leave-one-family-out
evaluation really rests on 4 folds, not 7, and one of those 4 (`Unclassified`) has a single
member in it.

This is a property of the split and the label distribution, not of any model, and it bounds
what Task A can ever demonstrate. It must be stated wherever a Task A metric is reported,
including how all-negative folds are handled: they should be reported as undefined rather than
scored as zero or silently dropped, because dropping them changes the denominator and scoring
them as zero invents a measurement.

**What this split prevents:** train-test pairs from the same RT family, and, as Finding 1
establishes, train-test pairs above 50 percent identity.

**What it does not prevent, at the identity level:** remote homology. Four clusters cross a
family boundary at 30 percent identity, so for the families named in Finding 1 the training
set still holds relatives of the held-out family at that level. The split holds out a clade
at the 50 percent level, not all detectable homology.

**What it does not prevent, at the label level:** nothing stops a model from learning coarse lineage signal that
correlates with the label across families, because family and activity are genuinely
associated in these data (12 of 18 retroviral RTs are active against 0 of 15 across
CRISPR-associated, Other, and Unclassified). A model that predicts "retroviral, therefore
active" will score well without knowing anything about catalysis. That is the confound the
existing audit already identified, and no split can remove it, because it is in the biology
and in the panel's construction. The only defence is the family-classification control, which
belongs in the modelling phase.

### Task B: three regimes

The Task B id set is fully determined without the activity data. Both libraries are exactly
saturating: stretch 1 covers residues 60 to 84, so 25 positions, and stretch 2 covers 95 to
124, so 30 positions, with all 19 non-wild-type substitutions at each, giving 475 plus 570,
so 1045. The wild-type residue at each of those 55 positions comes from the resolved reference
frame, and none of the four unresolved PE2 substitution positions (200, 306, 313, 330) falls
inside either stretch, so the variant identities are certain even though the parent
construct's substitution content is not.

Generating the ids from the frame reproduced 475, 570, and 1045 exactly. That is a third
independent confirmation of the reference frame resolution, alongside the nine residue anchors
and the two arithmetic statements recorded in `tasks/taskB_mmlv_dms/PROVENANCE.md`.

It also makes these files a reconciliation check. When the parser reads Tables S6 and S7, any
variant it produces that is not in these files, and any id here it does not produce, is a
discrepancy to be logged rather than absorbed.

The wild-type row `B_wt` is `train` in every fold of every regime. It is the reference the
labels are defined against, fixed at zero by construction, so it is not a test item in any
regime.

#### 1. `position_held_out.csv`, 5 folds

All variants at a given position share a fold. Positions are assigned round robin within each
stretch, so every fold draws from both libraries and folds stay balanced at 209 test items
each. The `group` column records the position, so the grouping is auditable from the file.

**Prevents:** memorizing a position's mean effect. Since all 19 substitutions at a held-out
position are in the test set together, a model cannot see any substitution at that position
during training.

**Does not prevent:** learning from immediately adjacent positions, which are structurally
correlated. A stricter form would assign contiguous blocks of positions to folds, withholding
each test position's structural neighbourhood as well. That is a harder regime; it is not used
here because the brief asks for one position-held-out regime and this is its standard grouped
form, but it is the obvious next tightening if the position-held-out result looks suspiciously
strong. Also does not prevent learning the wild-type residue identity at a held-out position,
which is available from the reference sequence and is not leakage in any meaningful sense.

#### 2. `stretch_held_out.csv`, 2 folds, the headline Task B result

Train on library 1 and test on library 2, and the reverse.

**Prevents:** everything the position regime prevents, plus any transfer through positional
proximity, since the two stretches are separated by residues 85 to 94. This is the honest
generalization test: it asks whether what the model learned about one DNA-interacting stretch
says anything about a different one.

**Does not prevent, and this must be reported alongside the number:** if the two libraries
were normalized separately, then this split also crosses two normalizations, and a poor result
would be partly a scale mismatch rather than a failure to generalize. Whether the scaling to
the interval was computed per library or across both is an open question recorded in
`tasks/taskB_mmlv_dms/PROVENANCE.md`. Until it is answered, the stretch-held-out number
carries that caveat. This is why `library_stretch` is a required column in the Task B schema.

The two folds are also not symmetric: 475 train against 570 test in one direction and 570
against 475 in the other, over stretches of different length and different structural context.
The two directions are reported separately and not averaged.

#### 3. `random_variant_LEAKY_DO_NOT_REPORT.csv`, 5 folds

Random assignment of individual variants, seeded with `GLOBAL_SEED = 1729`.

**This is not a result and must never be reported as one.** It is labelled in three places: in
the filename, in a `leaky` column set to `yes` on every row, and in a `never_report` column
that states the reason on every row.

**What it leaks:** position identity. With 19 substitutions per position scattered at random
across 5 folds, roughly 15 of the 19 substitutions at any test variant's position are in the
training set. A model can therefore learn that position's mean effect and apply it, which is
most of the predictable signal in a deep mutational scan.

**Its only legitimate use:** quantifying how much optimism the easier split buys. The gap
between this number and the stretch-held-out number is the measurement of interest, and it is
reported as a gap, never as a performance figure.

### Task A2: no folds

The evolved cohort is evaluation only, per the Gate G1 ruling. It has no split because it is
never trained on: it is scored whole by a model trained on Task A alone. Recorded here so its
absence from `splits/` is not read as an oversight.

## Summary of what remains unprotected

No split in this benchmark prevents the following, and each has to be handled by a control in
the modelling phase rather than by a partition:

1. Task A: lineage signal that correlates with activity across families. Needs the
   family-classification control.
2. Task A: three all-negative folds, which must be reported as undefined rather than scored.
3. Task A: redundancy concentrated in the retroviral fold, so its 18 rows are worth far fewer
   independent observations.
4. Task B: a possible normalization difference between the two libraries, which is entangled
   with the headline stretch-held-out result.
5. Across tasks: the Task B parent protein is also the most active Task A row, and the
   cross-task clustering that would quantify this cannot run until Task B exists.
