# Handcrafted feature dictionary

Produced by `features/build_handcrafted.py`. 788 feature columns plus `id`.

Every column is a raw value. Nothing is scaled, imputed, or selected here, because each of
those is a fit and a fit belongs inside a cross-validation fold in the modelling phase. A
missing value is an empty cell, never a zero, and there is a parallel mask file marking it.

## Files

| file | contents |
| --- | --- |
| `taskA_features.csv` | 57 rows by 788 feature columns, keyed by `id` |
| `taskA_missing_mask.csv` | same shape and column order; 1 means the value is missing, 0 means present |

Row order matches the source table's row order. `id` is the join key and the only non-numeric
column.

**Provisional identifiers.** Task A has no `curated.csv` yet, because its 57 rows are blocked
on accessions and DOIs. Identifiers here are minted as `A_<rt_name>` from
`data/rt_sequences.csv`, the same rule the Task A parser will use and the same rule already
used by the cluster and split files. Only sequences were used, and the sequences are final, so
these values do not change when `curated.csv` arrives. They are not a result and no model has
been fitted to them.

## Column families

### 1. Length, 1 column

| column | definition | units |
| --- | --- | --- |
| `length` | number of residues in the sequence | residues |

### 2. Amino acid composition, 20 columns

`aac_<X>` for each `X` in `ACDEFGHIKLMNPQRSTVWY`, in that order.

Definition: count of residue `X` divided by sequence length. Units: fraction. The 20 columns
sum to 1 for any sequence over the standard alphabet.

### 3. Dipeptide composition, 400 columns

`dpc_<XY>` for every ordered pair from the same 20-letter alphabet, enumerated as the Cartesian
product of `ACDEFGHIKLMNPQRSTVWY` with itself in that order, so `dpc_AA`, `dpc_AC`, ... ,
`dpc_YY`.

Definition: count of overlapping occurrences of the two-residue window `XY` divided by the
number of two-residue windows counted, which is `length - 1` for a sequence over the standard
alphabet. Units: fraction, summing to 1.

### 4. Reduced-alphabet tripeptide frequencies, 343 columns

`rk3_<abc>` where each of `a`, `b`, `c` is one of seven physicochemical group letters,
enumerated as the Cartesian product of `abcdefg` three times in sorted order, so `rk3_aaa`,
`rk3_aab`, ... , `rk3_ggg`.

**Group definition, fixed a priori:**

| letter | residues | rationale |
| --- | --- | --- |
| `a` | A, G, V | small and aliphatic |
| `b` | I, L, F, P | hydrophobic |
| `c` | Y, M, T, S | polar, mixed character |
| `d` | H, N, Q, W | polar, nitrogen-bearing or aromatic |
| `e` | R, K | positively charged |
| `f` | D, E | negatively charged |
| `g` | C | cysteine, kept alone for disulfide chemistry |

All twenty residues appear exactly once across the seven groups.

Definition: the sequence is mapped residue by residue into the seven-letter alphabet, then the
count of each overlapping three-letter window is divided by the number of windows counted.
Units: fraction, summing to 1.

**Why the selection rule is structural rather than statistical.** The brief asks for selected
k-mer frequencies with k and the selection rule fixed a priori, and separately forbids feature
selection in this phase. Any rule that picked tripeptides by their frequency or variance in
this dataset would be feature selection, and would leak the dataset's distribution into the
feature definition. So the reduction is made in the alphabet instead of in the k-mer set: k is
3, the alphabet is reduced from 20 letters to 7 groups, and **all** 343 resulting features are
emitted. Nothing is chosen by looking at the data and nothing is dropped. The full 20-letter
tripeptide space would have been 8000 columns against 57 rows, which is why the reduction
exists at all.

### 5. Biophysical, 12 columns

Computed with Biopython `Bio.SeqUtils.ProtParam.ProteinAnalysis`.

| column | definition | units |
| --- | --- | --- |
| `bio_molecular_weight` | sum of residue masses plus one water | daltons |
| `bio_isoelectric_point` | pH at which net charge is zero, by the ProtParam method | pH units |
| `bio_aromaticity` | combined fraction of F, W, Y (Lobry and Gautier) | fraction |
| `bio_instability_index` | Guruprasad dipeptide instability index | index, dimensionless |
| `bio_gravy` | grand average of hydropathy, mean Kyte and Doolittle value | dimensionless |
| `bio_protparam_frac_helix` | composition-predicted helix fraction, ProtParam definition | fraction |
| `bio_protparam_frac_turn` | composition-predicted turn fraction | fraction |
| `bio_protparam_frac_sheet` | composition-predicted sheet fraction | fraction |
| `bio_flexibility_mean` | mean of the windowed Vihinen flexibility profile | dimensionless |
| `bio_flexibility_min` | minimum of that profile | dimensionless |
| `bio_flexibility_max` | maximum of that profile | dimensionless |
| `bio_flexibility_std` | population standard deviation of that profile | dimensionless |

The three `bio_protparam_frac_*` columns are predicted from composition alone and are **not**
the structural secondary structure in family 6. They are kept because they are cheap and
sequence-only, and they are named distinctly so the two cannot be confused.

Flexibility is a windowed profile rather than a scalar, so it is summarised. A sequence shorter
than the ProtParam window yields an empty profile, in which case all four columns are missing.
No sequence in Task A is that short.

### 6. Structural, 12 columns

Computed from the inherited models in `data/structures/`, one PDB per RT.

| column | definition | units |
| --- | --- | --- |
| `struct_n_residues` | residues in the model having an alpha carbon | residues |
| `struct_confidence_mean` | mean over residues of that residue's mean atomic B-factor | zero to one |
| `struct_confidence_min` | minimum of that per-residue value | zero to one |
| `struct_confidence_max` | maximum of that per-residue value | zero to one |
| `struct_confidence_std` | population standard deviation of that per-residue value | zero to one |
| `struct_ss_frac_helix` | fraction of residues assigned `H` | fraction |
| `struct_ss_frac_strand` | fraction assigned `E` | fraction |
| `struct_ss_frac_loop` | fraction assigned neither | fraction |
| `struct_rsa_mean` | mean relative solvent accessibility | fraction |
| `struct_rsa_std` | population standard deviation of relative accessibility | fraction |
| `struct_frac_exposed` | fraction of residues with relative accessibility above 0.25 | fraction |
| `struct_radius_of_gyration` | root mean square distance of alpha carbons from their centroid | angstroms |

The three secondary structure fractions sum to 1.

**Computation.** Secondary structure is assigned by `pydssp` from backbone N, CA, C, O
coordinates, three-state output. Solvent accessibility is computed by Biopython's Shrake and
Rupley implementation at residue level, then divided per residue by the theoretical maximum
accessible surface area of Tien et al. 2013 to give a relative value. A residue is called
exposed above a relative accessibility of 0.25, which is the conventional cutoff.

**Why this is not called pLDDT.** The brief describes these as AlphaFold models. Their
provenance is not documented anywhere in this repository, and two things argue against taking
the label at face value: the files carry a `PARENT N/A` header, and the global maximum B-factor
across all 57 files is 0.99, so the column holds a confidence on a zero to one scale rather
than a pLDDT on a zero to one hundred scale. The column is therefore named
`struct_confidence_*`. Calling it pLDDT would assert a provenance nobody has established. The
values are usable as a model-confidence covariate either way; what is unresolved is which
program produced them.

### Structure to sequence correspondence, three cases handled explicitly

| RT | situation | handling |
| --- | --- | --- |
| `Vp96-RT` | no file of that name; `Vp-96.pdb` exists | the correspondence was established by checking that `Vp-96.pdb` is sequence-identical to `Vp96-RT` at all 312 residues, not by filename similarity. Recorded as an alias in the script. |
| `Gs-RT` | model has 426 residues, sequence has 419 | only aggregate structural features are computed, so nothing is misaligned, but per-residue structural features cannot be aligned for this row without an alignment. `struct_n_residues` makes the discrepancy visible in the matrix itself. |
| `Line1-RT` | no structure file at all | all 12 structural columns are missing, and the mask marks them. Not zero-filled. |

So 56 of 57 rows carry structural features, and 1 of 57 has all 12 missing. Those are the only
missing values anywhere in the matrix.

## Features deliberately absent

**Variant-specific features** (source and target residue identity, BLOSUM62 substitution
score, change in hydrophobicity, charge and volume, position index, normalized position within
the stretch, per-position conservation from an alignment) are not emitted, because no task with
variant rows exists yet. Task B is blocked on its activity values. These are implemented when
Task B is built, not speculatively before.

**Distance from a mutated residue to the catalytic aspartates** likewise requires variant rows
and is absent for the same reason.

**Per-position conservation from an RT family alignment** is not emitted. Task A has 57
sequences spanning 7 families with identity mostly below 50 percent, so a single multiple
alignment across all of them would be low quality, and a per-position conservation value is a
per-residue feature that only has a use once there are variant rows to attach it to.

## Reproduction

    python features/build_handcrafted.py

The script prints the shared seed, the library versions, and the SHA256 of every input, and
reports the missing-value census per column.
