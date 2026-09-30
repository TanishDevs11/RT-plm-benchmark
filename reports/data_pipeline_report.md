# Data and representation pipeline report

Phase 6. Written 2026-09-30, at Gate G3.

**No model has been trained, no predictive performance has been measured, and no performance
number appears anywhere in this document.** Everything below describes data, features, and
representations. Nothing here is a result.

## 1. Final per-task state

| task | n sequences | n labelled | label definition | units | assay term | positives | splits defined |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A, cross-family | 57 | 57, unprovenanced | percent precise prime edits at a genomic locus in HEK293T | percent | `prime_editing_pct_HEK293T` | 21 of 57 | leave-one-family-out, 7 folds |
| A2, evolved | 0 | 0 | percent precise prime edits, evolved editors in their own scaffolds | percent | `prime_editing_pct_HEK293T_evolved_editor` | n/a | none; evaluation only, so no folds |
| B, M-MLV DMS | 0 | 0 | wild-type-centred normalized editing efficiency, scaled to the interval from -1 to 1 | `normalized_-1_1` | `prime_editing_normalized_wt_centred` | n/a, continuous | position-held-out 5 folds, stretch-held-out 2 folds, random labelled leaky |
| C retron | 0 | 0 | not built | | | | none |
| C DGR | 0 | 0 | not built | | | | none |
| C retroviral | 0 | 0 | not built | | | | none |

**No `curated.csv` exists for any task.** Task A has sequences and labels but cannot pass the
schema validator, because every row lacks `source_doi`, `source_table`, and
`reference_accession`. Task B has a fully determined identifier set and a resolved reference
frame but no labels. The three Task C tasks were ruled out at Gate G1.

Task B's split files were nonetheless written and are complete, because the identifier set is
fully determined by the reference frame and the two saturating libraries without any activity
data. See section 3.

## 2. Sources

### Obtained

| source | file | licence | SHA256, first 12 |
| --- | --- | --- | --- |
| Li et al. 2026, bioRxiv, DOI `10.64898/2026.07.06.736660`, main text | `tasks/taskB_mmlv_dms/raw/preprint.pdf` | CC-BY-NC 4.0, read from the PDF's own per-page banner | `5a13f7763987` |
| UniProt `P03355`, `SV=5`, Gag-Pol of Moloney murine leukemia virus | `tasks/taskB_mmlv_dms/raw/uniprot_P03355.fasta` | CC-BY 4.0 | `418f1e426db3` |
| UniProt entries for Task A accession resolution | `.uniprot_cache/`, not committed | CC-BY 4.0 | per entry |

The Task B licence permits redistribution with attribution for non-commercial use, so the
preprint is committed rather than only referenced by a download script.

### Attempted and failed

| source | what was wanted | why it failed |
| --- | --- | --- |
| Li et al. 2026 supplementary material | Supplementary Sequence 1 (the PE2dR construct) and Tables S6 and S7 (per-variant activity) | **not publicly deposited.** Four independent routes agree, listed below |
| Doman et al. 2023, Cell, DOI `10.1016/j.cell.2023.07.039`, Supplementary Table S1 | the 59-enzyme panel, its 14-class assignment, per-locus efficiencies, and accessions for all 57 Task A rows | Elsevier supplementary file behind the article interstitial; not scriptable, and a human has not yet fetched it |
| Addgene 132775, pCMV-PE2 | the parent RT's substitution content, as a fallback for Supplementary Sequence 1 | the sequences page returns HTTP 200 but embeds no sequence in static HTML; the GenBank file derived from the map image path returns HTTP 404 |
| ESM-1v checkpoint | masked-marginal variant effect scores | the locally cached checkpoint is a partial download; deferred with Task B, whose variants are its only use here |
| ProtT5-XL-U50 | a third representation family | the `transformers` package is not installed |
| ESM-IF, ProteinMPNN | inverse-folding likelihoods | not run; structures exist for 56 of 57 Task A rows but their modelling provenance is undocumented, so a likelihood over them would carry an unknown dependency. See section 5 |
| retron, DGR, and in vitro retroviral activity panels | Task C label sets | no single-study panel of usable size found for any of the three. Ruled out at Gate G1; reasons per task in each `PROVENANCE.md` |

**Evidence that the Task B supplementary material is not deposited**, rather than merely not
found:

1. the supplementary-material page returns HTTP 200 and lists no files, with no occurrence of
   the word "supplement" in its rendered text
2. the full-text page offers downloads for Supplementary Figures 1 to 4 only, and those are
   already pages 20 to 23 of the committed main PDF
3. Europe PMC, which systematically harvests preprint supplementary material, indexes the
   preprint as `PPR1272147` with `hasSuppl = N`, and its `supplementaryFiles` endpoint returns
   HTTP 404
4. every legacy bioRxiv adjunct path and all twenty highwire filestream combinations tried
   return HTTP 404 or another non-200

The preprint also carries no Data Availability and no Code Availability statement: the strings
"availability", "Data availability", and "Data Availability" do not appear anywhere in it. That
is consistent with the files never having been deposited.

## 3. The Task B numbering resolution

This was identified in Phase 1 as the single most likely failure mode in the pipeline, because a
numbering offset would displace every variant in both libraries without producing any visible
error. It is resolved.

### The conflict

The preprint removes the RNase H domain at "residues L499 to P677", which implies a 677-residue
reverse transcriptase. UniProt `P03355` annotates the chain "Reverse transcriptase/ribonuclease
H (p80)" at Gag-Pol residues 660 to 1330, which is 671 residues. Six residues of disagreement.

### The reference adopted

| quantity | value |
| --- | --- |
| reference accession plus version | `P03355.5`, that is `SV=5`, dated 2018-01-31 |
| parent entry | `sp|P03355|POL_MLVMS`, Gag-Pol polyprotein, Moloney murine leukemia virus, isolate Shinnick, 1738 residues |
| RT frame | Gag-Pol 660 to 1336, so RT residues 1 to 677 |
| Gag-Pol offset | 659; RT position n is Gag-Pol position n plus 659 |
| RNase H deleted | RT 499 to 677, 179 residues |
| PE2dR RT retained | RT 1 to 498, so Gag-Pol 660 to 1157, 498 residues, 1494 base pairs |
| diversified stretch 1 | RT 60 to 84, 25 positions, `SIKQYPMSQEARLGIKPHIQRLLDQ` |
| diversified stretch 2 | RT 95 to 124, 30 positions, `NTPLLPVKKPGTNDYRPVQDLREVNKRVED` |

### Wild-type residue assertions: nine of nine passed

Every residue identity the preprint states was checked. These are the assertions, and the
parser halts on any one of them failing rather than adjusting an offset.

| RT position | required | observed in `P03355.5` | source of the requirement |
| --- | --- | --- | --- |
| 60 | S | S | stretch 1 start, "S60-Q84" |
| 61 | I | I | reported mutation I61R |
| 67 | S | S | reported mutation S67W |
| 84 | Q | Q | stretch 1 end, "S60-Q84" |
| 95 | N | N | stretch 2 start, "N95-D124" |
| 101 | V | V | reported mutation V101R |
| 124 | D | D | stretch 2 end, "N95-D124" |
| 499 | L | L | deletion start, "residues L499 to P677" |
| 677 | P | P | deletion end, "residues L499 to P677" |

Additionally, all five PE2 substitution positions carry their expected wild-type residue in this
frame: D200, T306, W313, T330, L603. So fourteen residue identities agree in total.

### Three further confirmations, independent of the anchors

1. **The preprint's own arithmetic.** It states the retained RT is "encoded by 1,494bp" and
   "26.4% smaller than the wild-type MMLV-RT". Under this frame, residues 1 to 498 give 498
   times 3, so 1494 base pairs exactly; and 179 deleted of 677 gives 0.2644, which rounds to
   26.4 percent.
2. **The identifier set.** Generating every variant from this frame and the two stretch
   boundaries produced 475 variants for stretch 1, 570 for stretch 2, and 1045 in total,
   matching all three figures the preprint states.
3. **The inherited Task A data.** The Task A `MMLV-RT` row is 677 residues long, the same frame,
   and differs from `P03355` residues 660 to 1336 at exactly one position. Two unrelated
   datasets agree on the 677-residue frame.

### Resolution of 671 against 677

Both numbers are correct, about different things. The preprint's reverse transcriptase extends
six residues past the annotated p80 chain, to Gag-Pol 1336, into the region UniProt assigns to
integrase. RT residues 672 to 677 are `IENSSP`, ending in the P the preprint calls P677. There
is no offset and no error in either source.

### What remains unresolved about the reference

PE2dR was built by deleting RNase H from the RT of pCMV-PE2, Addgene 132775, whose RT carries
D200N, T306K, W313F, T330P, and L603W. L603 falls inside the deleted region, so if PE2dR
inherits that RT it is a **tetramutant truncation** carrying the first four and not L603W.

That is a derivation, not a reading. The strings "pentamutant", "D200N", and "L603W" appear
nowhere in the preprint. The file written is therefore
`tasks/taskB_mmlv_dms/raw/reference_candidate_unconfirmed.fasta`, carries no substitutions, and
**no parser may consume it**: a reference wrong at four positions would be wrong at four
positions in all 1046 rows. All four candidate positions lie outside both diversified stretches,
so no variant identity is affected, only the reference's own residues.

One further reason the candidate is not usable as a reference: the inherited Task A `MMLV-RT`
differs from `P03355` at RT position 8, which is Y in the inherited sequence and H in `P03355`.
A reference built from `P03355` would be wrong at position 8 relative to the sequence actually
used in the prime editing literature.

Reproduce with `python data_acquisition/resolve_mmlv_reference.py`. Six tests in
`data_acquisition/test_resolve_mmlv_reference.py` prove the resolver refuses rather than adapts,
including a positive control that removes six residues ahead of the RT start.

## 4. Identity clustering

MMseqs2 commit `8cc5ce367b5638c4306c2d7cfc652dd099a4643f`. Parameters fixed a priori:
thresholds 90, 70, 50 percent identity; `-c 0.8`; `--cov-mode 1`, coverage over the target;
`-s 7.5`.

Coverage over the target rather than the default bidirectional coverage, because these are
excised domains with different boundaries: the Task A M-MLV RT row is 677 residues and the Task
B parent is the same protein at 498, giving bidirectional coverage of 0.74, so at `-c 0.8` the
most important cross-task duplicate would have gone unreported.

| threshold | sequences | clusters | size distribution |
| --- | --- | --- | --- |
| 90 percent | 57 | 53 | 49 singletons, 4 pairs |
| 70 percent | 57 | 49 | 44 singletons, 3 pairs, 1 triple, 1 quadruple |
| 50 percent | 57 | 44 | 39 singletons, 3 pairs, 1 quadruple, 1 cluster of 8 |

Four findings, with the full argument in `reports/split_design.md`:

1. **No cluster crosses a family boundary at any threshold.** Leave-one-family-out therefore
   prevents identity leakage as well as family leakage. This was not guaranteed.
2. **The redundancy that exists is concentrated where the positives are.** At 50 percent, 12 of
   the 18 retroviral sequences sit in just 2 clusters, and the retroviral fold holds 12 of the
   21 positives. Its 18 rows are worth far fewer than 18 independent observations.
3. **A 90-percent-identical pair carries opposite activity calls**: `ASLV-RT` active and
   `RSVSB-RT` inactive. At 70 percent, `BAEMV-RT` active, `FENV1-RT` inactive, and `MMLV-RT`
   active cluster together.
4. **Three of the seven Task A folds contain no positive at all**: CRISPR-associated, Other,
   and Unclassified, 15 rows between them. Held out, each yields an all-negative test set on
   which a ranking correlation is undefined. Such folds must be reported as undefined, never
   scored as zero and never silently dropped.

### Cross-task near-duplicates: not yet measurable

Only Task A has sequences, so the cross-task clustering has not been run. **This is an open item,
not a clean result.**

The specific duplicate the brief names is known to exist by direct inspection rather than by
clustering: the Task A `MMLV-RT` row is the same protein as the Task B parent, at 677 residues
against 498. Any future statement that a representation transfers between Task B and Task A has
to account for the Task B parent also being a Task A row.

A second observation from the accession work belongs here, because it bears on the cross-family
framing: the Task A row named `HIVpol+MMLVRNaseH_RT` is, by its own name, an engineered chimera
of HIV pol and the M-MLV RNase H domain. It is not a natural ortholog, which is why no single
database entry contains it as a substring. At least one of the 57 rows is therefore a
construct rather than a member of any RT family, and its family assignment in the inherited
table should be treated as a label of convenience.

## 5. Feature and embedding inventory

### Handcrafted features

`features/handcrafted/`, 788 feature columns by 57 rows. No scaling, no imputation, no feature
selection; raw values plus a missingness mask. Full definitions in `FEATURE_DICTIONARY.md`.

| file | bytes | SHA256, first 12 |
| --- | --- | --- |
| `taskA_features.csv` | 628560 | `5ea3e66782bc` |
| `taskA_missing_mask.csv` | 96712 | `0fe5766e04f6` |

Composition: length 1; amino acid composition 20; dipeptide composition 400; reduced-alphabet
tripeptide frequencies 343; biophysical 12; structural 12.

The k-mer selection rule is structural rather than statistical, because any rule that chose
tripeptides by their distribution in this dataset would be feature selection and would leak the
dataset's distribution into the feature definition. k is 3, the 20-residue alphabet is reduced to
7 physicochemical groups covering all 20 exactly once, and all 343 resulting features are
emitted.

**Missing values.** Exactly 12 cells in one row: `A_Line1-RT` has no structure file, so all 12
structural columns are missing and the mask marks them. Every other cell is present. 56 of 57
rows are structurally complete.

**Three structure-to-sequence correspondence problems, handled explicitly:**

- `Vp96-RT` has no file of that name. `Vp-96.pdb` was confirmed sequence-identical to it at all
  312 residues, so the correspondence is established by sequence and not by filename similarity.
- `Gs-RT` has a 426-residue model against a 419-residue sequence. Only aggregate structural
  features are computed, so nothing is misaligned, and `struct_n_residues` makes the discrepancy
  visible in the matrix. The accession work independently placed this sequence at `E2GM63.1`
  residues 2 to 420, which is 419 residues, consistent with the model being built on a slightly
  longer construct.
- `Line1-RT` has no structure at all.

**On the structures' provenance.** The brief describes these as AlphaFold models. Their
provenance is undocumented in this repository, the files carry a `PARENT N/A` header, and the
global maximum B-factor across all 57 files is 0.99, so the column holds a confidence on a zero
to one scale rather than a pLDDT on a zero to one hundred scale. The feature is therefore named
`struct_confidence_mean` and not `plddt`. Calling it pLDDT would assert a provenance nobody has
established. This is also why no inverse-folding likelihood was computed over them.

### Embeddings

`embeddings/`, 16 matrices, float16, each with a parallel identifier file. `MANIFEST.json`
records per file the model, checkpoint SHA256, pooling strategy, layer index and role, dtype,
shape, file SHA256, generation timestamp, and library versions.

| file | shape | SHA256, first 12 |
| --- | --- | --- |
| `esm2_8M/taskA_mean_full_layer6.npz` | 57 by 320 | `0c2d66b72ef9` |
| `esm2_8M/taskA_mean_full_layer3.npz` | 57 by 320 | `8a4ffd18839e` |
| `esm2_8M/taskA_catalytic_core_layer6.npz` | 50 by 320 | `09111504765a` |
| `esm2_8M/taskA_catalytic_core_layer3.npz` | 50 by 320 | `aeccd4e7bcf8` |
| `esm2_35M/taskA_mean_full_layer12.npz` | 57 by 480 | `e753734b2570` |
| `esm2_35M/taskA_mean_full_layer6.npz` | 57 by 480 | `d9ec037cb283` |
| `esm2_35M/taskA_catalytic_core_layer12.npz` | 50 by 480 | `45138f10f6a9` |
| `esm2_35M/taskA_catalytic_core_layer6.npz` | 50 by 480 | `eff70817bb86` |
| `esm2_150M/taskA_mean_full_layer30.npz` | 57 by 640 | `a91acd286d7d` |
| `esm2_150M/taskA_mean_full_layer15.npz` | 57 by 640 | `9e29108aa46f` |
| `esm2_150M/taskA_catalytic_core_layer30.npz` | 50 by 640 | `01b701e729ff` |
| `esm2_150M/taskA_catalytic_core_layer15.npz` | 50 by 640 | `abba1f25c905` |
| `esm2_650M/taskA_mean_full_layer33.npz` | 57 by 1280 | `c7ed4bc4b6f3` |
| `esm2_650M/taskA_mean_full_layer16.npz` | 57 by 1280 | `41736691b6fc` |
| `esm2_650M/taskA_catalytic_core_layer33.npz` | 50 by 1280 | `0b01d37df595` |
| `esm2_650M/taskA_catalytic_core_layer16.npz` | 50 by 1280 | `40de287d5540` |

Total 1.03 MiB on disk. `python embeddings/verify_manifest.py` recomputes every checksum,
checks every shape and dtype, checks for non-finite values, and checks that each matrix's row
order matches its task table: 4 runs, 24 artifacts, 0 problems.

Layers are fixed a priori, two per model: the final layer and a mid-depth layer at
floor(n_layers / 2), giving 6 and 3, 12 and 6, 30 and 15, 33 and 16. There is no layer sweep
here, because choosing a layer by how it scores is a selection decision.

Pooling strategies are stored separately and never averaged. `catalytic_core` pools over
`[y - 200, y + 140)` anchored on the first YXDD match, offsets derived from M-MLV RT where the
motif begins at residue 222 and the polymerase domain runs to roughly 360.

**The motif is absent in 7 of 57 sequences**: `FuRT-Cas1-RT`, `ROSE-CRISPR-RT`, `CHLRE`,
`Line1-RT`, `Ngaro-RT`, `Ty1B-RT`, `Ec48-RT`. They are excluded from the catalytic-core matrices
rather than pooled over a guessed window, which is why those matrices have 50 rows. Every
exclusion is logged by name and recorded per sequence in
`taskA_catalytic_core_windows.json`. `Abi-RT` has more than one YXDD match and the first is
used, also recorded.

### Zero-shot scores

Sequence log-likelihood from a single unmasked forward pass, for all four scales, in
`taskA_zeroshot_singlepass_loglik.csv` per model directory. Both the sum over positions and the
per-residue mean are recorded.

These are named `singlepass` and not pseudo-log-likelihood, because that is what they are. The
per-residue values improve monotonically with scale, at -0.4304, -0.3722, and -0.3125 for 8M,
35M and 150M, but sit near -0.3, which corresponds to roughly 74 percent probability on the
residue actually present. That is the signature of the model reading the token it is scoring
rather than predicting it. A true masked-marginal pseudo-log-likelihood is being computed for the
8M model so that the size of this inflation is measured rather than assumed; the 650M model is
not viable for it on this CPU, needing roughly 25,000 forward passes.

### Compute cost per representation

57 sequences, Task A, CPU only, torch 2.11.0+cpu with zero CUDA devices.

| model | output dim | load, s | inference, s | s per sequence | peak RSS, MiB |
| --- | --- | --- | --- | --- | --- |
| `esm2_t6_8M_UR50D` | 320 | 0.2 | 4.0 | 0.07 | 491 |
| `esm2_t12_35M_UR50D` | 480 | 0.3 | 10.8 | 0.19 | 643 |
| `esm2_t30_150M_UR50D` | 640 | 1.3 | 39.0 | 0.68 | 1486 |
| `esm2_t33_650M_UR50D` | 1280 | 8.9 | 138.9 | 2.44 | 3405 |

Inference cost rises by a factor of about 35 from the smallest to the largest model, and peak
resident memory by a factor of about 7.

## 6. Task A accession resolution

Task A's blocking defect is that no row carries a `source_doi`, a `source_table`, or a
`reference_accession`, so all 57 rows fail the schema validator on three fields at once. The RT
names are paper-internal labels and cannot be looked up by name.

`data_acquisition/resolve_taskA_accessions.py` resolves what it can from sequence: two probes
per sequence are submitted to UniProt peptide search, the candidate sets are intersected, and
each survivor is then verified by fetching its full sequence and testing the inherited sequence
as an exact substring. Results are in `tasks/taskA_crossfamily/raw/accession_resolution.tsv`.

| status | count |
| --- | --- |
| resolved, exactly one entry contains the sequence | 22 |
| resolved but ambiguous, several entries contain it | 6 |
| unresolved | 23 |
| service error, retryable | 6 |

So 28 of 57 rows now carry a verified accession plus version and the exact residue range of the
excision, 17 of them from reviewed entries. Examples: `Tf1-RT` at `Q01910.1` residues 349 to 853;
`Line1-RT` at `O00370.1` residues 238 to 1061; `BAEMV-RT` at `P10272.2` residues 660 to 1348.

**An accession found this way is a verifiable provenance anchor, not proof of what the original
authors used.** Supplementary Table S1 of Doman et al. remains the authority, and these values
are a fallback and a cross-check, not a substitute.

Two informative failures:

- `MMLV-RT` is **not** claimed for `P03355`, correctly, because it differs at RT position 8. The
  tool refuses a near match rather than rounding it off.
- `HIVpol+MMLVRNaseH_RT` cannot resolve to any single entry because it is an engineered chimera.

## 7. What this pipeline does not establish

Stated plainly, because the temptation to read an inventory as a result is real.

1. **No model has been trained.** Not one.
2. **No predictive performance has been measured**, and no performance number appears anywhere in
   this document.
3. **No feature or representation has been shown to be useful.** A 1280-dimensional embedding
   existing says nothing about whether it predicts anything.
4. **No scaler, no dimensionality reduction, no feature selection has been fitted.** All three
   are fits and all three belong inside a cross-validation fold in the modelling phase.
5. **The zero-shot scores are not baselines yet.** They are numbers attached to sequences. No
   one has correlated them with a label.
6. **Task A is not a valid task table yet**, because 57 of 57 rows fail the schema on provenance
   fields.
7. **Task B does not exist as a labelled task**, and the honest current answer is that its
   labels are not publicly available.
8. **The cross-task redundancy is unmeasured**, so no claim about transfer between tasks is
   supportable from what is here.

## 8. Open questions and blocked items for the modelling phase

### Blocking, in dependency order

1. **Task B activity values.** Tables S6 and S7 are not publicly deposited. Without them Task B
   has no labels and the A-against-B contrast, which is the scientific point of the multi-task
   design, cannot be run. The only routes are the corresponding author, a later preprint version,
   or the peer-reviewed publication.
2. **Task B reference substitution content.** Supplementary Sequence 1. Needed before any variant
   sequence is constructed, even though the frame is settled.
3. **Task A provenance.** Supplementary Table S1 of Doman et al. 2023, for accessions and the
   14-class assignment. 28 of 57 accessions are resolved independently; 29 remain, 6 of them
   only because of retryable service errors.
4. **The Task A label's own definition.** The inherited table holds one scalar per enzyme. If
   Figure 1C or Table S1 reports efficiency at more than one locus, that scalar is an aggregate
   computed by an unknown rule. This is the most important unresolved fact about the Task A
   label.
5. **Task A2 efficiencies**, from the same Cell supplementary set.

### Reconciliations still open

6. The paper tested 59 enzymes; the inherited table has 57. Which two are absent, and why.
7. The paper reports 20 actives; the inherited table has 21. Either `MMLV-RT` at 41 percent is
   the benchmark control rather than one of the 59 surveyed, or `Ne144-RT` at 0.5 percent sits
   below the paper's detection threshold and was called active by a rule applied later. If the
   second, the binary label in this repository is not the paper's binary label and must be
   labelled as such wherever it is used.
8. Whether the Task B normalization to the interval was computed within each library or across
   both. This is entangled with the headline stretch-held-out regime: if the libraries were
   scaled separately, that split also crosses two normalizations.
9. The provenance of the 57 structures under `data/structures/`, which program produced them
   and what the B-factor column means.
10. The family assignment of `HIVpol+MMLVRNaseH_RT`, which is an engineered chimera rather than a
    member of any family.

### Carried forward as constraints on interpretation, not as blockers

11. Three of seven Task A folds have no positive, so the leave-one-family-out evaluation rests on
    4 folds, one of which has a single member. All-negative folds must be reported as undefined.
12. Redundancy is concentrated in the retroviral fold, which holds 12 of 21 positives, so its 18
    rows carry far fewer than 18 independent observations.
13. `ASLV-RT` and `RSVSB-RT` are above 90 percent identical with opposite labels. No
    similarity-based method can get both right, and 21 positives cannot determine whether this is
    sharp biology or label noise.
14. No split prevents lineage signal that correlates with activity across families. That needs the
    family-classification control in the modelling phase, not a partition.

### Representations not generated

15. ESM-1v, ProtT5-XL-U50, and inverse-folding likelihoods, with reasons in section 2 and in
    `MANIFEST.json` under `not_generated`. The ESM-1v masked-marginal variant effect score the
    brief requires for every Task B variant cannot exist until Task B does.

## Reproduction

    python schemas/test_task_schema.py
    python data_acquisition/check_inputs.py --allow-missing
    python data_acquisition/resolve_mmlv_reference.py --fetch
    python data_acquisition/test_resolve_mmlv_reference.py
    python data_acquisition/resolve_taskA_accessions.py
    python curation/cluster_redundancy.py --mmseqs <path to mmseqs>
    python curation/define_splits.py
    python curation/test_splits.py
    python features/build_handcrafted.py
    python embeddings/build_embeddings.py
    python embeddings/verify_manifest.py

Every script prints the shared seed, its library versions, and the SHA256 of each input.
