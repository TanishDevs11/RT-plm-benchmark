# Task A reconciliation

Written by `data_acquisition/parse_taskA.py`. This is the Gate G2 artifact.

Source: Doman et al. 2023, `10.1016/j.cell.2023.07.039`, Table S1 (mmc2.xlsx), sheet 'Table S1', assayed block, rows 6 to 118.
Workbook SHA256 `16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c`.
Parsed 2026-10-02.

No discrepancy below is resolved by choosing a side. Each is stated with the
evidence for both readings, for a human to rule on.

## 1. Which of the surveyed RTs are in the inherited file

| quantity | value |
| --- | --- |
| entries in Table S1's assayed block | 57 |
| rows in `data/rt_sequences.csv` | 57 |
| names in Table S1 but not inherited | [] |
| names inherited but not in Table S1 | [] |

**The two sets are identical.** So there is no enzyme to name as missing from the
inherited file, and the brief's expectation that 2 of the surveyed enzymes would
be absent from it does not hold.

### The 57 against 59 discrepancy

The article's prose says the authors tested 59 enzymes. Table S1's assayed
block holds 57. The gap of 2 is therefore **inside the primary source**: between the
article's text and the article's own supplementary table. It is not a gap between
this repository and the paper.

Both readings, neither adopted:

- **Reading A, the table is complete and the prose is wrong.** The table is the
  itemised artifact, it is internally consistent, its index runs 1 to 57 without a
  gap, and 57 is also exactly what the inherited dataset contains. Under this
  reading the number 59 in the text is an error.
- **Reading B, the prose is right and the table omits two.** 59 enzymes were
  assayed and two were left out of the deposited table. Under this reading two
  measured enzymes are missing from every downstream analysis, and nothing in the
  published record names them, so nothing can be done about it either way.

Neither reading changes the benchmark, because under both of them the 57 rows that
exist are the only 57 that can be used. What it changes is the claim: the panel
must be described as the 57 enzymes Table S1 lists, not as the 59 the paper says
were tested.

## 2. The 21 against 20 actives discrepancy

| quantity | value |
| --- | --- |
| entries carrying the green activity fill | 21 |
| rows marked `active = 1` in the inherited file | 21 |
| the two sets are identical | yes |
| the article's prose count | 20 |

Highlighted entries by inherited family: Group_II_Intron 2, LTR_Retrotransposon 2, Retron 5, Retroviral 12.

**The enzyme that accounts for the difference is M-MLV RT, and the evidence is in
the article's own class breakdown.** The Figure S1A caption states that of the
enzymes supporting detectable mammalian PE activity, 11 are closely related to the
M-MLV RT and are encoded by retroviruses, two are encoded by LTR retrotransposons,
and seven are bacterial RTs. That is 11 plus 2 plus 7, which is 20.

The highlighted set matches that breakdown in every class except one:

| class | prose | Table S1 highlights |
| --- | --- | --- |
| retroviral | 11 | 12 |
| LTR retrotransposon | 2 | 2 |
| bacterial: group-II intron, retron, CRISPR-Cas | 7 | 7 |

The phrase is **closely related to the M-MLV RT**, which excludes M-MLV RT itself,
and the same Figure S1A caption separates it out explicitly: the wild-type M-MLV RT
used in the PE1 system is highlighted in black while all other enzymes are in red.
M-MLV RT is the PE1 comparator, not a survey candidate. Counting it gives 21,
excluding it gives 20, and both numbers are correct under their own definition.

### The two activity definitions, both stated

- **Table S1's definition, 21 actives.** Any enzyme the authors shaded green,
  described as showing activity in the prime editing system. M-MLV RT included.
  This is what the inherited file uses and what `curated.csv` reproduces.
- **The prose's definition, 20 actives.** Surveyed RTs showing detectable PE
  activity, excluding the M-MLV RT that defines the PE1 baseline being surveyed
  against. Neither definition states a numeric threshold; the word in the paper is
  detectable.

`curated.csv` carries the 21-active labelling, because it is the one attached to
the itemised table rather than to a sentence, and because dropping M-MLV RT would
remove the single highest-weighted row in the CLS metric. A ruling that the
benchmark should instead report the 20-active definition is a one-line change and
is a legitimate choice; it is not made here.

## 3. Sequence integrity, checksum compared against the primary source

This check had never been run on this dataset. Every inherited sequence is
compared by SHA256 against the sequence in Table S1 for the same enzyme.

| quantity | value |
| --- | --- |
| sequences compared | 57 |
| byte-identical by SHA256 | 57 |
| mismatches | 0 |

**All 57 sequences are byte-identical to the primary
source.** There is no sequence drift in the inherited dataset.

Separately, the inherited file's own `protein_length_aa` column disagrees with
`len(sequence)` on 0 of its 57 rows.

This is the one inherited claim that this reconciliation strengthens rather
than qualifies, and it is worth saying plainly: whatever else is unverifiable
about this dataset, the sequences are exactly the paper's.

## 4. The efficiency column, which has no verifiable source

**Table S1 contains no efficiency values.** There is no numeric cell anywhere in
the sheet except the row index. All six supplementary workbooks were scanned; none
carries the per-enzyme survey efficiencies. So the inherited `pe_efficiency_pct`
column cannot be checked against the published supplementary material at all.

What the column can be attributed to, and how confidently:

- **Which panel.** Figure S1A is the only panel reporting one value per enzyme for
  every surveyed enzyme, inactive ones included. Its caption gives the assay
  exactly: HEK293T cells, HEK3 +5 G to T edit, dots reflecting the mean of n = 3
  independent replicates. Figure 1C is the alternative, but it plots only the
  actives and does so across several endogenous sites, so it cannot be the source
  of a single value for all 57 rows.
- **Which quantity.** Defined verbatim in the Figure 1 caption: the frequency of
  the intended prime editing outcome with no indels or other changes at the target
  site. So these are precise-edit percentages, not total editing or indel-inclusive
  rates.
- **How the numbers were obtained.** Every one of the 21 non-zero values is an exact
  multiple of 0.5 (verified), and every inactive row is exactly 0.0. 21 independent
  amplicon-sequencing measurements landing exactly on half-percent boundaries is
  not plausible. The quantization is the signature of values read off a plot by
  eye. The values are: 41.0, 34.0, 26.5, 23.5, 23.0, 21.0, 19.0, 16.5, 12.5, 9.0, 8.0, 7.0, 5.5, 4.5, 3.5, 2.5, 1.5, 1.5, 1.5, 1.0, 0.5.

So `efficiency_source_column` is set to `FigureS1A_HEK3_plus5_G_to_T_mean_n3_UNVERIFIED_DIGITIZED`,
which names the attribution and carries the word UNVERIFIED in the value itself,
so that no downstream reader can treat it as sourced.

**What this means for the benchmark.** The regression target is a digitization of a
figure, at roughly half a percentage point of resolution, with no error bars
recoverable. The weighted Spearman component of CLS is computed on it, and the
CLS weighting concentrates most of its mass on the few highest-efficiency enzymes,
which is exactly where a digitization error is largest in absolute terms. Any
regression result in this benchmark has to be reported with that stated.

The binary `active` label does not have this problem: it is read directly from the
fill colour in Table S1 and is reproducible from the file.

## 5. Accessions

Table S1 gives no accession for any assayed enzyme; their names are bare
laboratory labels. The article's full text contains no protein accession of any
recognised form, and its data availability statement points at the key resources
table, whose accessions are sequencing-read accessions for the SRA deposit.

Accessions were therefore resolved from sequence against UniProt by
`data_acquisition/resolve_taskA_accessions.py`. Status across the 57 rows:

| status | rows | treatment in `curated.csv` |
| --- | --- | --- |
| resolved | 27 | accession and version recorded, FASTA pinned in `raw/sequences/` |
| resolved_ambiguous | 6 | left empty: several entries contain the sequence exactly |
| unresolved | 24 | left empty: no database entry contains the sequence |

An ambiguous resolution is left empty deliberately. Two UniProt entries containing
the same sequence exactly are equally good candidates, and recording one of them
would be a coin flip presented as a pinned accession.

### Why the 30 unpinned rows did not pin

A bare count of unresolved rows is not a finding. It does not distinguish a
sequence whose parent protein is absent from the searched set from one whose
parent is obvious but differs at a single residue, and only the first is a dead
end. `data_acquisition/resolve_taskA_near_matches.py` finds each unpinned row's
nearest entry in the local UniProt cache and reports every differing position.
Results are in `raw/accession_near_matches.tsv`.

| outcome | rows | what it means |
| --- | --- | --- |
| exact substring of a cached entry | 6 | the sequence is in the database; only the ambiguity blocks the pin |
| near match, 1 to 4 residues different | 13 | the parent protein is identified on the evidence, but the sequence is not that entry's sequence |
| no entry closer than 99 percent | 11 | the cache does not contain the parent entry at all |

**The near-match group is the interesting one, and it has a pattern.** The
differences are listed as the cached entry's residue, the position in the Task A
sequence, then the Task A residue:

| enzyme | nearest entry | organism | identity | differences |
| --- | --- | --- | --- | --- |
| `KORV-RT` | `A0A6P5J5X3` | Phascolarctos cinereus | 99.8525 | L1M |
| `MMLV-RT` | `P03355` | Moloney murine leukemia virus (isolate Shinnick) | 99.8523 | H8Y |
| `MPMV-RT` | `P07572` | Mason-Pfizer monkey virus | 99.844 | L1M |
| `SRV2-RT` | `P51517` | Simian retrovirus SRV-2 | 99.844 | L1M |
| `Tyrosinerecomb-RT` | `O96849` | Dictyostelium discoideum | 99.8353 | L1M |
| `MMTV-RT` | `O56220` | Mouse mammary tumor virus | 99.8344 | P1V |
| `Ec67-RT` | `A0ABU1C287` | Escherichia marmotae | 99.8294 | V25I |
| `Gypsy-RT` | `V9H1G9` | Drosophila subobscura | 99.7868 | I93S |
| `Bel-RT` | `Q8MRT3` | Drosophila melanogaster | 99.7845 | T194N |
| `ASLV-RT` | `A0A1W5WYK3` | Avian leukosis virus | 99.6503 | C176R;L476S |
| `A.platensis-Cas1-RT` | `A0A9P1KET4` | Limnospira indica PCC 8005 | 99.6403 | M217I |
| `Ty3-RT` | `Q99315` | Saccharomyces cerevisiae (strain ATCC 204508 / S288c) | 99.3724 | V1G;S2P;D428N |
| `Tel4c-RT` | `Q8DJR1` | Thermosynechococcus vestitus (strain NIES-2133 / IAM M-273 / BP-1) | 99.287 | C1E;Y2T;P3R;T4Q |

Two things stand out. First, 7 of these 13 rows differ at position 1, and in 4 of those the Task A residue there is methionine where the parent protein has
something else. That is not an isolate difference; it is a start codon. These are
excised RT domains, and an excised domain needs an initiating methionine to be
expressed, so the construct's first residue differs from the parent protein by
construction. The other position-1 differences are to residues other than
methionine, so they are not explained this way and are left as observations.

Second, the 6 rows that differ only at internal positions differ at one or two
residues in an otherwise exact match over 300 to 700, which is what a different
viral isolate or strain looks like rather than a different protein.

So the great majority of the unresolved accessions are not a mystery. They are
the expected consequence of comparing an expression construct against a
reference proteome entry by exact string matching. The identification is
well supported in these cases; what is not supported is calling the sequence
identical to the accession, and `curated.csv` therefore keeps `accession` empty
and records the difference in `notes`.

Two limits of this scan, both of which mean it can explain a failure but not
prove one. The search set is the local cache, which holds only the candidates the
earlier resolver downloaded while probing, so a distant best hit means the cache
lacks the parent rather than that UniProt does. And the alignment is ungapped, so
a row whose parent differs by an insertion or deletion scores poorly even when it
is the right protein.

### The schema conflict this creates, which is a Gate G2 decision

`schemas/task_schema.py` requires a non-empty `reference_accession` on every row,
on the principle that every row should name the accession plus version of its
parent sequence. That rule was written before it was known that the source
publishes no accessions. Running it against `curated.csv` gives:

| rule | rows |
| --- | --- |
| `reference_accession.null` | 30 |

Three ways to settle it, for a human to choose:

1. **Relax the rule for Task A**, on the ground that the source publishes no
   accessions and a sequence SHA256 is the stronger identifier anyway. Every row
   carries `sequence_sha256`, which pins the sequence exactly and does not depend
   on a database that may reassign an accession later. This is the recommendation.
2. **Drop the rows without an accession.** That removes 30 of 57 rows, including
   actives, and would leave a benchmark too small to say anything. Not recommended,
   and recorded here only so the option is on the record.
3. **Keep the rule and leave Task A failing it.** Honest, but it means the pipeline
   has a permanently failing guard, which is how guards come to be ignored.

## 6. Duplicate and near-identical sequences

| check | result |
| --- | --- |
| exact duplicate sequences under different names | 0 |
| one sequence wholly contained in another | 1 |

**`Retron86-RT` (319 residues) is wholly contained in `retronE,coli-RT` (333 residues).**

These are not two independent proteins. They are the same sequence excised
at two different boundaries, differing only by the 14 extra residues on
the longer one. They cluster together at 90 percent identity. Both are
labelled inactive, so the pair cannot inflate a classifier through
contradictory labels, but it does mean the panel holds fewer independent
observations than its row count suggests.

Identity clustering at 90, 70, 50 and 30 percent is Phase 2 and is reported in
`reports/dataset_overview.md`. The near-duplicate structure already known from the
earlier clustering run is concentrated in the retroviral family, which also holds
most of the actives, so the effective sample size is well below 57.

## 7. What `curated.csv` asserts, and on whose authority

| column | sourced from | authority |
| --- | --- | --- |
| `rt_name` | Table S1 assayed block | primary source |
| `sequence`, `sequence_len`, `sequence_sha256` | Table S1 assayed block | primary source |
| `active`, `label_binary` | the green fill in Table S1 | primary source |
| `source_doi`, `source_table`, `table_s1_index` | Table S1 | primary source |
| `accession`, `accession_version`, `reference_accession` | UniProt, resolved from sequence | derived, and empty where unresolved |
| `host_organism` | the cached UniProt FASTA header | derived, and empty where no accession |
| `family` | `data/rt_sequences.csv` | **inherited, not in the paper** |
| `pe_efficiency_pct`, `label_value` | `data/rt_sequences.csv` | **inherited, and unverifiable against any published table** |

The two bold rows are the ones a reader has to be careful with. `family` is a
7-way labelling that cannot be checked against the paper's 14 classes, because
those exist only in the Figure 1B tree image. `pe_efficiency_pct` is discussed in
section 4 above.

## Open rulings for Gate G2

1. **Does the benchmark stand at 57 rows?** Recommended yes: 57 is what Table S1
   lists and the prose's 59 names no additional enzyme.
2. **21 actives or 20?** Recommended 21, the table's own labelling, with the 20
   definition documented. The difference is M-MLV RT.
3. **The `reference_accession` schema rule.** Recommended option 1, relax it for
   Task A and rely on `sequence_sha256`.
4. **Does the efficiency column stay in the benchmark at all?** It is a figure
   digitization. Recommended: keep it, because it is the only continuous signal
   available and the inherited CLS metric needs it, but report every regression
   result with the digitization stated as a limitation, and treat classification on
   the binary label as the primary result.
