# Task B HIV-1 RT baseline feature dictionary

Written by `features/taskB_hivrt/build_baselines.py`. No scaling, no imputation,
no feature selection: raw values plus column names, with scaling and imputation
left to the inner loop of the modelling phase.

Dataset: `filtered`, 4139 isolate rows. Rows are keyed by
`drug_class:isolate_id`, because an isolate id can appear in both drug classes with
a class-specific reconstructed sequence.

## Blocks

| block | shape | median pairwise cosine | what it is |
| --- | --- | --- | --- |
| `mutation_onehot` | (4139, 853) | 0.1296 | one binary indicator per observed position-and-residue; the classic baseline for this dataset and the one every other representation has to beat |
| `drm` | (4139, 24) | 0.9708 | indicators and counts over the major drug resistance positions HIVDB publishes, plus the TAM1 and TAM2 package counts |
| `physicochemical` | (4139, 11) | 0.7925 | whole-sequence descriptors plus summed physicochemical changes across the mutated positions |
| `kmer3` | (4139, 2624) | 0.8894 | 3-mer frequencies over the reconstructed sequence, skipping any k-mer containing an indeterminate position |

## Why these are baselines here and controls in the M-MLV task

In the M-MLV saturated mutagenesis task every row is a single substitution in one
protein, so k-mer and whole-sequence features have a median pairwise cosine
similarity of 0.9840 and 0.999998 respectively: they cannot distinguish the
variants at all, and a near-zero score from them says nothing about the
representation.

That does not hold here. Isolates differ at many positions at once, so the same
blocks carry real variation, as the median cosine column above shows. They are
legitimate competitors rather than labelled controls, and a near-zero score from
one of them would be a finding about the representation.

## The one-hot vocabulary rule

The full space is 560 positions by 20 residues, 11200 columns, of which most are
never observed. Only observed position-and-residue combinations get a column.

Dropping a column that is zero in every row is **provably inert**: it is zero in
every training and test subset too, so no model fitted on any fold can predict
differently with it present. It is not feature selection. No frequency threshold is
applied, because a threshold would discard columns carrying signal on the basis of
a statistic computed over all rows including the held-out ones.

## Column definitions

| column | units | computation |
| --- | --- | --- |
| `<position><residue>` | binary | 1 if the isolate carries that residue at that position |
| `major_<class>_<position>` | binary | 1 if the isolate is mutated at a published HIVDB major resistance position for that drug class |
| `n_major_NRTI`, `n_major_NNRTI` | count | number of major positions mutated |
| `n_mutations_total` | count | mutations relative to consensus B |
| `tam1_count`, `tam2_count` | count | members of each thymidine analogue mutation package present |
| `tam1_complete`, `tam2_complete` | binary | 1 if the whole package is present |
| `n_unknown_positions` | count | positions encoded X; a sequencing-coverage proxy, not biology |
| `mean_hydropathy`, `mean_volume` | Kyte-Doolittle units, cubic angstroms | averaged over determinate residues |
| `net_charge`, `fraction_polar`, `fraction_aromatic` | charges, fractions | over determinate residues |
| `sum_delta_*` | per-mutation sums | change from wild-type to mutant residue, summed over the isolate's mutations |
| `mean_abs_delta_hydropathy` | Kyte-Doolittle units | mean absolute hydropathy change per mutation |

The HIVDB major resistance positions, reproduced from the source's own dataset page:

| class | positions |
| --- | --- |
| NRTI | 41, 65, 70, 74, 75, 151, 184, 210, 215 |
| NNRTI | 100, 101, 103, 106, 181, 188, 190, 230 |

`n_unknown_positions` deserves a warning. It is a count of positions the assay did
not resolve, so it measures sequencing coverage rather than biology. If it turns out
to carry predictive weight, that is a property of how the data was collected and
must be reported as such rather than as a finding about resistance.
