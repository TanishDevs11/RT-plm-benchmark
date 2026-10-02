# Task A handcrafted feature dictionary

Written by `features/build_handcrafted_taskA.py`. Every column emitted is defined
here, with its units and its computation. A column that matters enough to compute
is a column that matters enough to define.

Source: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`.

Row order is the order of `curated.csv`, and the key is `rt_name`. No scaling, no
imputation and no feature selection are applied: these are raw values plus a
missingness mask of the same shape.

## Representation blocks

Phase 6 benchmarks several of these blocks separately, so each is listed with the
column prefix that selects it.

| block | columns | prefix | dimensionality |
| --- | --- | --- | --- |
| length | 1 | `length` | 1 |
| amino acid composition | 20 | `aac_` | 20 |
| dipeptide composition | 400 | `dpc_` | 400 |
| reduced-alphabet 3-mer | 343 | `rk3_` | 343 |
| physicochemical | 13 | `bio_` | 13 |
| structural | 12 | `struct_` | 12 |
| full 3-mer frequency | 6256 | separate `.npz` | 6256 of 8000 possible |
| full 4-mer frequency | 20115 | separate `.npz` | 20115 of 160000 possible |

## Column definitions

| column | units | computation | missing rows |
| --- | --- | --- | --- |
| `rt_name` | identifier | the Table S1 laboratory label, the join key | 0 |
| `length` | residues | `len(sequence)` | 0 |
| `aac_X` | fraction | count of residue X divided by length, for each of the 20 standard residues | 0 |
| `dpc_XY` | fraction | count of the ordered pair XY divided by the number of adjacent pairs, length minus 1, for all 400 pairs | 0 |
| `rk3_GGG` | fraction | 3-mer frequency over a 7-group physicochemical alphabet rather than the 20 residues, all 343 emitted | 0 |
| `bio_aromaticity` | fraction | Lobry aromaticity, the summed fraction of F, W and Y | 0 |
| `bio_flexibility_max` | Vihinen flexibility units | maximum of that profile | 0 |
| `bio_flexibility_mean` | Vihinen flexibility units | mean of the windowed flexibility profile | 0 |
| `bio_flexibility_min` | Vihinen flexibility units | minimum of that profile | 0 |
| `bio_flexibility_std` | Vihinen flexibility units | standard deviation of that profile | 0 |
| `bio_gravy` | Kyte-Doolittle units | grand average of hydropathy, the mean per-residue hydropathy | 0 |
| `bio_instability_index` | index, dimensionless | Guruprasad instability index; above 40 is conventionally called unstable | 0 |
| `bio_isoelectric_point` | pH | Biopython `ProteinAnalysis.isoelectric_point` | 0 |
| `bio_molecular_weight` | daltons | Biopython `ProteinAnalysis.molecular_weight` | 0 |
| `bio_net_charge_ph74` | elementary charges | Biopython `ProteinAnalysis.charge_at_pH(7.4)`, at physiological pH | 0 |
| `bio_protparam_frac_helix` | fraction | ProtParam secondary structure fraction, helix-favouring residues; a composition statistic, not a structural prediction | 0 |
| `bio_protparam_frac_sheet` | fraction | ProtParam sheet-favouring fraction | 0 |
| `bio_protparam_frac_turn` | fraction | ProtParam turn-favouring fraction | 0 |
| `struct_n_residues` | residues | residue count in the structure file, emitted so a sequence-structure length mismatch is visible in the matrix | 1 |
| `struct_confidence_mean` | zero to one | mean of the PDB B-factor column. **Not named pLDDT**: the files carry a `PARENT N/A` header and the column's global maximum across all 57 files is 0.99, so it is a per-atom confidence on a zero-to-one scale, and calling it pLDDT would assert a provenance nobody has established | 1 |
| `struct_confidence_min` | zero to one | minimum of that column | 1 |
| `struct_confidence_max` | zero to one | maximum of that column | 1 |
| `struct_confidence_std` | zero to one | standard deviation of that column | 1 |
| `struct_ss_frac_helix` | fraction | fraction of residues assigned helix by the geometric assignment in `build_handcrafted.py` | 1 |
| `struct_ss_frac_strand` | fraction | fraction assigned strand | 1 |
| `struct_ss_frac_loop` | fraction | fraction assigned neither | 1 |
| `struct_rsa_mean` | fraction | mean relative solvent accessibility over residues | 1 |
| `struct_rsa_std` | fraction | standard deviation of relative solvent accessibility | 1 |
| `struct_frac_exposed` | fraction | fraction of residues above the exposure cutoff used in `build_handcrafted.py` | 1 |
| `struct_radius_of_gyration` | angstroms | radius of gyration of the model | 1 |

## The k-mer vocabulary rule

Fixed a priori: **keep every k-mer that occurs at least once anywhere in the
panel, and drop only the never-observed ones.** The vocabularies are frozen to
`taskA_kmer3_vocabulary.txt` and `taskA_kmer4_vocabulary.txt` so they are not
re-derived on a later run.

- k = 3: 6256 of 8000 possible k-mers occur in the panel, so 1744 columns are identically zero and are dropped.
- k = 4: 20115 of 160000 possible k-mers occur in the panel, so 139885 columns are identically zero and are dropped.

Dropping those columns is not feature selection. A column that is zero in all 57
rows is zero in every training subset and every test subset of those rows, so no
model fitted on any fold can predict differently with it present than without it.
The drop is provably inert: it uses the full row set, but only to establish that
fact, and it never looks at a label.

What is deliberately not done is thresholding on how many sequences a k-mer
appears in. A rule such as keeping only k-mers present in at least six sequences
would cut the 3-mer block from 6256 columns to 1618 and the 4-mer block from
20115 to 274. Those cuts are not inert: they discard columns that carry signal,
selected by a statistic computed over all rows including the held-out fold. That
is feature selection outside a fold, which the brief forbids, and it is one of the
mechanisms behind the artifact this repository exists to correct.

Values are frequencies rather than counts: each row is divided by its own number
of k-mer positions, so a long sequence does not dominate by length alone. Length
is available as its own feature for any model that wants it.

## Missingness

`taskA_missing_mask_v2.csv` has the same shape and column order as the feature
file, with 1 where a value could not be computed and 0 where it could. Nothing is
imputed, so a consumer can tell a real zero from an absent value.

Columns with any missing value:

- `struct_n_residues`: 1 row(s)
- `struct_confidence_mean`: 1 row(s)
- `struct_confidence_min`: 1 row(s)
- `struct_confidence_max`: 1 row(s)
- `struct_confidence_std`: 1 row(s)
- `struct_ss_frac_helix`: 1 row(s)
- `struct_ss_frac_strand`: 1 row(s)
- `struct_ss_frac_loop`: 1 row(s)
- `struct_rsa_mean`: 1 row(s)
- `struct_rsa_std`: 1 row(s)
- `struct_frac_exposed`: 1 row(s)
- `struct_radius_of_gyration`: 1 row(s)

### Structure correspondence notes

Carried from `features/build_handcrafted.py`, which resolved these rather than
letting them pass silently.

- Line1-RT: no structure file

Two further correspondence facts, recorded in `features/build_handcrafted.py` and
repeated here because they change what the structural block means:

- `Vp96-RT` has no file of that name; `Vp-96.pdb` is sequence-identical to it at
  all 312 residues, so the correspondence is established by sequence rather than
  by guessing a filename.
- `Gs-RT` has a 426-residue structure against a 419-residue sequence. Only
  aggregate structural features are computed, so nothing is corrupted, but
  per-residue structural features cannot be aligned for that row without an
  alignment. `struct_n_residues` is emitted so the discrepancy is visible in the
  matrix itself.
