# Workbook inventory: Doman et al. 2023 supplementary tables

Written by `data_acquisition/inventory_tableS1.py`. Nothing has been parsed into
the benchmark at the time this file is produced. This is the Gate G1 artifact.

## Why this file exists before any parsing

Supplementary Table S1 of this paper is cited for two different datasets: the
reverse transcriptases assayed as prime editors, which is what Task A needs, and
the 543 reverse transcriptase sequences used for the downstream phylogenetic
analyses, which were never assayed and carry no activity labels. A parser that
read the whole sheet, or matched on a sequence column, would pull hundreds of
unlabelled sequences into a 57-row task without raising anything.

## What the layout actually turned out to be

Not two sheets. `mmc2.xlsx` holds **one** sheet, and the two datasets are two
caption-delimited blocks inside it, in a FASTA dump rather than a table, under a
single index that runs continuously from the first block into the second. There
are no column headers and no efficiency column, and activity is recorded as a
green cell fill on the name of each active enzyme.

Three consequences worth stating before the detail:

1. A sheet-level inventory would have reported one sheet and found nothing, so
   this script works at block level and reads the fill styles as data.
2. Because the index is continuous, the paper's 543 is a running total that
   **includes** the assayed enzymes as its first entries. The second block is not
   543 sequences; it is the remainder.
3. Because activity is a fill colour, it is invisible to every tool that reads
   values only, including `pandas.read_excel`.

## mmc2.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc2.xlsx` |
| bytes | 215647 |
| sha256 | `16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c` |
| sheets | 1 |
| highlighted cells | 42 |

Sheet names, in workbook order: `Table S1`

Fill styles defined in this workbook: fill id 2: theme="9" tint="0.79998168889431442".

### Sheet `Table S1`

| field | value |
| --- | --- |
| declared dimensions | 1093 rows by 3 columns |
| rows holding anything | 1091 |
| widest populated row | 2 cells |
| layout | FASTA blocks |

First 6 rows, verbatim:

```
1: Figure S1: List of reverse transcriptases used in this s[...truncated for display, 82 chars total]
2: Sequences and identities of reverse transcriptases used [...truncated for display, 143 chars total]
3: 
4: Sequences and identity of reverse transcriptases tested [...truncated for display, 179 chars total]
5: Enzymes highlighted in green show activity in the prime [...truncated for display, 93 chars total]
6: 1 | >MMLV-RT
```

This sheet is a FASTA dump, not a table: column 1 carries a running
integer index, column 2 alternates between a `>`-prefixed name and the
sequence itself. There are no column headers to read, so the structure
below is derived from the caption rows and the index column.

### Caption rows, verbatim

These are the only in-band statement of where one dataset ends and the
next begins, so they are what the block split is based on.

- row 1: Figure S1: List of reverse transcriptases used in this study, related to Figure 1.
- row 2: Sequences and identities of reverse transcriptases used for BLAST query, phylogenetic analysis, and initial screen of RTs in Figures 1B and 1C.
- row 4: Sequences and identity of reverse transcriptases tested for prime editing. These enzymes were also used as query sequences to perform BLASTP for phylogenetic analysis (Figure 1B).
- row 5: Enzymes highlighted in green show activity in the prime editing system as shown in Figure 1C.
- row 121: Sequencces of additonal reverse transcriptases used to perform phylogenetic analysis in Figure 1B.

### Index column

| field | value |
| --- | --- |
| indexed entries | 543 |
| index range | 1 to 543 |
| contiguous 1..N | yes |
| duplicate indices | 0 |

The index runs continuously across every block without restarting. That is
load bearing: it means the blocks are one numbered series, so the later block
is an extension of the earlier one rather than a separate list, and the
paper's 543 is the running total, not the size of the second block.

### Blocks

| block | opened by caption on row | entry rows | index range | entries | highlighted |
| --- | --- | --- | --- | --- | --- |
| 1 | 5 | 6 to 118 | 1 to 57 | 57 | 21 |
| 2 | 121 | 122 to 1092 | 58 to 543 | 486 | 0 |

#### Block 1, opened by the caption on row 5

| field | value |
| --- | --- |
| entries | 57 |
| index range | 1 to 57 |
| names in UniProt `tr` or `sp` pipe form | 0 |
| names that are bare labels | 57 |
| highlighted entries | 21 |
| determination | the assayed prime editor panel. Entries are bare laboratory labels, not database identifiers, and the count is near but not equal to the prose count of 59, which is a discrepancy to record |

First 6 entries:

```
row 6  index 1  >MMLV-RT [HIGHLIGHTED]
row 8  index 2  >MMTV-RT [HIGHLIGHTED]
row 10  index 3  >ASLV-RT [HIGHLIGHTED]
row 12  index 4  >PERV-RT [HIGHLIGHTED]
row 14  index 5  >HIVpol+MMLVRNaseH_RT
row 16  index 6  >AVIRE-RT [HIGHLIGHTED]
```

Every highlighted entry in this block, which per the caption on row 5
means the enzyme showed activity in the prime editing system:

- MMLV-RT
- MMTV-RT
- ASLV-RT
- PERV-RT
- AVIRE-RT
- BAEMV-RT
- GALV-RT
- KORV-RT
- MPMV-RT
- POL11ERV-RT
- SRV2-RT
- WMSV-RT
- Tf1-RT
- Rs-RT
- Vp96-RT
- Vc95-RT
- Ec48-RT
- Gs-RT
- Er-RT
- Ne144-RT
- Ty3-RT

#### Block 2, opened by the caption on row 121

| field | value |
| --- | --- |
| entries | 486 |
| index range | 58 to 543 |
| names in UniProt `tr` or `sp` pipe form | 486 |
| names that are bare labels | 0 |
| highlighted entries | 0 |
| determination | the unassayed phylogenetic sequence set. Entries are UniProt BLAST hit headers, which is what a sampled BLAST result looks like and is not what an assayed panel looks like |

First 6 entries:

```
row 122  index 58  >tr|A0A3M0K3Z6|A0A3M0K3Z6_HIRRU Ribonuclease H OS=Hirund[...truncated for display, 108 chars total]
row 124  index 59  >tr|A0A3M0K8U8|A0A3M0K8U8_HIRRU Ribonuclease H OS=Hirund[...truncated for display, 108 chars total]
row 126  index 60  >tr|A0A3M0IZX9|A0A3M0IZX9_HIRRU Ribonuclease H OS=Hirund[...truncated for display, 108 chars total]
row 128  index 61  >tr|A0A218U9M1|A0A218U9M1_9PASE Ribonuclease H OS=Lonchu[...truncated for display, 105 chars total]
row 130  index 62  >tr|A0A7N9DCA1|A0A7N9DCA1_MACFA Uncharacterized protein [...truncated for display, 96 chars total]
row 132  index 63  >tr|A0A3M0LBD1|A0A3M0LBD1_HIRRU Ribonuclease H OS=Hirund[...truncated for display, 108 chars total]
```

## mmc3.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc3.xlsx` |
| bytes | 107645 |
| sha256 | `541a6c236f4b98402b1259bc80339bc3f4e6355476e3194887a0e2fd5bff8b18` |
| sheets | 14 |
| highlighted cells | 2255 |

Sheet names, in workbook order: `Table S2A`, `Table S2B`, `Table S2C`, `Table S2D`, `Table S2E`, `Table S2F`, `Table S2G`, `Table S2H`, `Table S2I`, `Table S2J`, `Table S2K`, `Table S2L`, `Table S2M`, `Table S2N`

Fill styles defined in this workbook: fill id 2: theme="2" tint="-9.9978637043366805E-2"; fill id 3: theme="6" tint="0.79998168889431442"; fill id 4: theme="7" tint="0.59999389629810485"; fill id 5: theme="7" tint="0.59999389629810485"; fill id 6: rgb="FFFFC000"; fill id 7: rgb="FFFFC000"; fill id 8: rgb="FFD3E9FF"; fill id 9: rgb="FFD3E9FF"; fill id 10: rgb="FF65B2FF"; fill id 11: rgb="FF65B2FF"; fill id 12: rgb="FF99CCFF"; fill id 13: rgb="FF99CCFF"; fill id 14: rgb="FF99CCFF"; fill id 15: rgb="FFFDE9D9"; fill id 16: rgb="FFB7DEE8"; fill id 17: rgb="FFE4DFEC"; fill id 18: rgb="FFCCC0DA"; fill id 19: rgb="FFA4D2FF"; fill id 20: rgb="FF97CAFD"; fill id 21: theme="5" tint="0.39997558519241921"; fill id 22: theme="5" tint="0.39997558519241921"; fill id 23: rgb="FF98CDFF"; fill id 24: theme="0".

### Sheet `Table S2A`

| field | value |
| --- | --- |
| declared dimensions | 52 rows by 69 columns |
| rows holding anything | 50 |
| widest populated row | 69 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2A. Mutation table from v1 and v2 comparative PE [...truncated for display, 106 chars total]
2: Mutations in clones emerging from evolution. Mutations f[...truncated for display, 136 chars total]
3: 
4: Lagoon ID | Circuit and codon optimization used |  | 23 | 33 | 46 | 80 | 99 | 102 | 175 | 218 | 220 | 251 | 295 | 307 | 471 | 485 | 535 | 562 | 586 | 645 | 653 | 654 | 701 | 721 | 739 | 753 | 775 | 776 | 781 | 918 | 928 | 947 | 962 | 1008 | 1019 | 1020 | 1034 | 1110 | 1180 | 1229 | 1240 | 1260 | 1283 | 1322 | 1371 | 1376 | 1391 | 13 | 129 | 149 | 173 | 196 | 201 | 216 | 223 | 246 | 256 | 346 | 430 | 492 | 500 | 534 | 606 | 619 | 633 | 646 | 651 | 676
5:  |  | Clone | Cas9 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Linker |  |  | M-MLV RT polymerase domain |  |  |  |  |  |  |  |  |  |  |  |  |  | M-MLV RT RNaseH domain
6:  |  | WT | D | K | N | C | H | E | N | K | R | N | N | R | E | G | R | K | R | D | R | R | S | H | Q | R | K | N | M | K | T | D | L | F | R | K | A | I | D | P | S | E | A | A | G | S | E | T | V | L | R | P | E | D | V | T | A | E | Q | Q | A | R | S | A | I | A | M | S
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 68 |
| determination | unclassified: needs a human read |
| evidence | rows=52; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon ID`
- column 2: `Circuit and codon optimization used`
- column 4: `23`
- column 5: `33`
- column 6: `46`
- column 7: `80`
- column 8: `99`
- column 9: `102`
- column 10: `175`
- column 11: `218`
- column 12: `220`
- column 13: `251`
- column 14: `295`
- column 15: `307`
- column 16: `471`
- column 17: `485`
- column 18: `535`
- column 19: `562`
- column 20: `586`
- column 21: `645`
- column 22: `653`
- column 23: `654`
- column 24: `701`
- column 25: `721`
- column 26: `739`
- column 27: `753`
- column 28: `775`
- column 29: `776`
- column 30: `781`
- column 31: `918`
- column 32: `928`
- column 33: `947`
- column 34: `962`
- column 35: `1008`
- column 36: `1019`
- column 37: `1020`
- column 38: `1034`
- column 39: `1110`
- column 40: `1180`
- column 41: `1229`
- column 42: `1240`
- column 43: `1260`
- column 44: `1283`
- column 45: `1322`
- column 46: `1371`
- column 47: `1376`
- column 48: `1391`
- column 49: `13`
- column 50: `129`
- column 51: `149`
- column 52: `173`
- column 53: `196`
- column 54: `201`
- column 55: `216`
- column 56: `223`
- column 57: `246`
- column 58: `256`
- column 59: `346`
- column 60: `430`
- column 61: `492`
- column 62: `500`
- column 63: `534`
- column 64: `606`
- column 65: `619`
- column 66: `633`
- column 67: `646`
- column 68: `651`
- column 69: `676`

### Sheet `Table S2B`

| field | value |
| --- | --- |
| declared dimensions | 48 rows by 51 columns |
| rows holding anything | 46 |
| widest populated row | 51 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2B. Mutation table from v1 PE PA(N)CE Gs evolutio[...truncated for display, 79 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: v1 PANCE
5: Lagoon | Clone | 12 | 16 | 17 | 21 | 26 | 28 | 37 | 38 | 41 | 43 | 45 | 57 | 94 | 123 | 173 | 190 | 196 | 206 | 251 | 360 | 372 | 379 | 387 | 400
6:  |  | N | A | L | E | A | G | L | R | I | A | W | Y | E | A | Q | P | S | D | K | R | T | N | T | T
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 26 |
| determination | unclassified: needs a human read |
| evidence | rows=48; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `12`
- column 4: `16`
- column 5: `17`
- column 6: `21`
- column 7: `26`
- column 8: `28`
- column 9: `37`
- column 10: `38`
- column 11: `41`
- column 12: `43`
- column 13: `45`
- column 14: `57`
- column 15: `94`
- column 16: `123`
- column 17: `173`
- column 18: `190`
- column 19: `196`
- column 20: `206`
- column 21: `251`
- column 22: `360`
- column 23: `372`
- column 24: `379`
- column 25: `387`
- column 26: `400`

### Sheet `Table S2C`

| field | value |
| --- | --- |
| declared dimensions | 22 rows by 40 columns |
| rows holding anything | 20 |
| widest populated row | 40 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2C. Mutation table from v2 PE PANCE Gs evolution,[...truncated for display, 77 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Lagoon | Clone | 9 | 11 | 12 | 13 | 17 | 21 | 25 | 26 | 35 | 37 | 39 | 43 | 44 | 67 | 69 | 72 | 86 | 90 | 97 | 140 | 169 | 206 | 237 | 244 | 246 | 251 | 266 | 285 | 296 | 314 | 328 | 344 | 358 | 363 | 371 | 378 | 389 | 396
5:  |  | A | D | N | L | L | E | G | A | D | L | D | A | H | I | K | G | L | A | P | E | R | D | R | R | L | K | K | A | I | R | L | R | R | E | E | A | K | A
6: 1 | 1 |  |  |  |  |  |  |  |  |  |  | N |  | P |  | N |  | R | S
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 40 |
| determination | unclassified: needs a human read |
| evidence | rows=22; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `9`
- column 4: `11`
- column 5: `12`
- column 6: `13`
- column 7: `17`
- column 8: `21`
- column 9: `25`
- column 10: `26`
- column 11: `35`
- column 12: `37`
- column 13: `39`
- column 14: `43`
- column 15: `44`
- column 16: `67`
- column 17: `69`
- column 18: `72`
- column 19: `86`
- column 20: `90`
- column 21: `97`
- column 22: `140`
- column 23: `169`
- column 24: `206`
- column 25: `237`
- column 26: `244`
- column 27: `246`
- column 28: `251`
- column 29: `266`
- column 30: `285`
- column 31: `296`
- column 32: `314`
- column 33: `328`
- column 34: `344`
- column 35: `358`
- column 36: `363`
- column 37: `371`
- column 38: `378`
- column 39: `389`
- column 40: `396`

### Sheet `Table S2D`

| field | value |
| --- | --- |
| declared dimensions | 35 rows by 35 columns |
| rows holding anything | 33 |
| widest populated row | 35 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2D. Mutation table from v1 PE PANCE Ec48 evolutio[...truncated for display, 79 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Lagoon | Clone | 25 | 26 | 32 | 87 | 88 | 98 | 132 | 169 | 183 | 195 | 205 | 242 | 243 | 245 | 259 | 267 | 272 | 278 | 281 | 289 | 311 | 318 | 319 | 323 | 326 | 328 | 368 | 372 | 374 | 392 | 393 | 396 | 401
5:  |  | A | P | K | K | R | S | V | D | T | V | R | H | D | P | E | R | S | D | K | N | R | K | L | G | K | E | H | R | Y | E | K | C | L
6: 1 | 1
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 35 |
| determination | unclassified: needs a human read |
| evidence | rows=35; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `25`
- column 4: `26`
- column 5: `32`
- column 6: `87`
- column 7: `88`
- column 8: `98`
- column 9: `132`
- column 10: `169`
- column 11: `183`
- column 12: `195`
- column 13: `205`
- column 14: `242`
- column 15: `243`
- column 16: `245`
- column 17: `259`
- column 18: `267`
- column 19: `272`
- column 20: `278`
- column 21: `281`
- column 22: `289`
- column 23: `311`
- column 24: `318`
- column 25: `319`
- column 26: `323`
- column 27: `326`
- column 28: `328`
- column 29: `368`
- column 30: `372`
- column 31: `374`
- column 32: `392`
- column 33: `393`
- column 34: `396`
- column 35: `401`

### Sheet `Table S2E`

| field | value |
| --- | --- |
| declared dimensions | 11 rows by 12 columns |
| rows holding anything | 9 |
| widest populated row | 12 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2E. Mutation table from v2 PE PANCE Ec48 evolutio[...truncated for display, 79 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Lagoon | Clone | 7 | 36 | 54 | 87 | 205 | 243 | 267 | 277 | 279 | 318
5:  |  | L | A | E | K | R | D | R | S | E | K
6: 1 | 1 | P |  | K | E |  | N | I |  | K | E
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 12 |
| determination | unclassified: needs a human read |
| evidence | rows=11; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `7`
- column 4: `36`
- column 5: `54`
- column 6: `87`
- column 7: `205`
- column 8: `243`
- column 9: `267`
- column 10: `277`
- column 11: `279`
- column 12: `318`

### Sheet `Table S2F`

| field | value |
| --- | --- |
| declared dimensions | 11 rows by 12 columns |
| rows holding anything | 9 |
| widest populated row | 12 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2F. Mutation table from v2 high stringency PE PAN[...truncated for display, 95 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Lagoon | Clone | 60 | 87 | 151 | 165 | 243 | 267 | 279 | 303 | 318 | 343
5:  |  | E | K | S | E | D | R | E | V | K | K
6: 1 | 1 | K | E |  | D | N | I | K |  | E | N
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 12 |
| determination | unclassified: needs a human read |
| evidence | rows=11; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `60`
- column 4: `87`
- column 5: `151`
- column 6: `165`
- column 7: `243`
- column 8: `267`
- column 9: `279`
- column 10: `303`
- column 11: `318`
- column 12: `343`

### Sheet `Table S2G`

| field | value |
| --- | --- |
| declared dimensions | 17 rows by 22 columns |
| rows holding anything | 15 |
| widest populated row | 22 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2G. Mutation table from v1 PE PANCE Tf1 evolution[...truncated for display, 78 chars total]
2: Mutations in clones emerging from evolution.
3: 
4:  |  | 14 | 102 | 112 | 128 | 158 | 209 | 239 | 269 | 308 | 312 | 344 | 350 | 356 | 362 | 363 | 379 | 417 | 440 | 450 | 478
5: Lagoon | Clone | V | M | R | I | L | H | K | F | T | T | S | H | K | D | A | D | H | T | L | L
6: 1 | 1 |  |  |  |  |  |  |  | L |  |  | P |  |  | E
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 22 |
| determination | unclassified: needs a human read |
| evidence | rows=17; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `V`
- column 4: `M`
- column 5: `R`
- column 6: `I`
- column 7: `L`
- column 8: `H`
- column 9: `K`
- column 10: `F`
- column 11: `T`
- column 12: `T`
- column 13: `S`
- column 14: `H`
- column 15: `K`
- column 16: `D`
- column 17: `A`
- column 18: `D`
- column 19: `H`
- column 20: `T`
- column 21: `L`
- column 22: `L`

### Sheet `Table S2H`

| field | value |
| --- | --- |
| declared dimensions | 11 rows by 14 columns |
| rows holding anything | 9 |
| widest populated row | 14 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2H. Mutation table from v2 PE PANCE Tf1 evolution[...truncated for display, 78 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Lagoon | Clone | 22 | 70 | 72 | 102 | 106 | 139 | 158 | 269 | 289 | 363 | 413 | 492
5:  |  | E | P | G | M | K | A | L | F | K | A | K | S
6: 1 | 1 |  | T | V | I | R |  | Q | L |  | V | E | N
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 14 |
| determination | unclassified: needs a human read |
| evidence | rows=11; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `22`
- column 4: `70`
- column 5: `72`
- column 6: `102`
- column 7: `106`
- column 8: `139`
- column 9: `158`
- column 10: `269`
- column 11: `289`
- column 12: `363`
- column 13: `413`
- column 14: `492`

### Sheet `Table S2I`

| field | value |
| --- | --- |
| declared dimensions | 54 rows by 55 columns |
| rows holding anything | 52 |
| widest populated row | 55 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2I. Mutation table from v3 PE PANCE Tf1 evolution[...truncated for display, 78 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: K118R mutation is highlighted in green.
5: Lagoon | Clone | 1 | 5 | 8 | 21 | 27 | 70 | 72 | 75 | 76 | 87 | 102 | 106 | 109 | 118 | 119 | 128 | 136 | 140 | 155 | 158 | 167 | 173 | 197 | 220 | 236 | 238 | 258 | 269 | 283 | 284 | 313 | 322 | 330 | 353 | 363 | 365 | 371 | 394 | 299 | 402 | 405 | 413 | 438 | 452 | 462 | 466 | 468 | 471 | 477 | 486 | 487 | 492 | 503
6:  |  | I | K | L | P | Y | P | G | Q | A | S | M | K | G | K | P | I | Q | K | A | L | H | C | F | H | Q | L | K | F | K | Q | H | D | T | F | A | D | V | A | S | D | M | K | R | R | F | Y | P | A | A | E | P | S | I
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 55 |
| determination | unclassified: needs a human read |
| evidence | rows=54; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `Lagoon`
- column 2: `Clone`
- column 3: `1`
- column 4: `5`
- column 5: `8`
- column 6: `21`
- column 7: `27`
- column 8: `70`
- column 9: `72`
- column 10: `75`
- column 11: `76`
- column 12: `87`
- column 13: `102`
- column 14: `106`
- column 15: `109`
- column 16: `118`
- column 17: `119`
- column 18: `128`
- column 19: `136`
- column 20: `140`
- column 21: `155`
- column 22: `158`
- column 23: `167`
- column 24: `173`
- column 25: `197`
- column 26: `220`
- column 27: `236`
- column 28: `238`
- column 29: `258`
- column 30: `269`
- column 31: `283`
- column 32: `284`
- column 33: `313`
- column 34: `322`
- column 35: `330`
- column 36: `353`
- column 37: `363`
- column 38: `365`
- column 39: `371`
- column 40: `394`
- column 41: `299`
- column 42: `402`
- column 43: `405`
- column 44: `413`
- column 45: `438`
- column 46: `452`
- column 47: `462`
- column 48: `466`
- column 49: `468`
- column 50: `471`
- column 51: `477`
- column 52: `486`
- column 53: `487`
- column 54: `492`
- column 55: `503`

### Sheet `Table S2J`

| field | value |
| --- | --- |
| declared dimensions | 46 rows by 16 columns |
| rows holding anything | 44 |
| widest populated row | 16 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2J. Mutation table from v1 PE PACE PE2 RT evoluti[...truncated for display, 80 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Timepoint (h) | Clone | M-MLV polymerase domain
5:  |  | 11 | 18 | 19 | 32 | 71 | 128 | 200 | 223 | 259 | 346 | 388 | 439 | 468 | 477
6:  | WT | H | D | V | A | R | T | N | V | A | E | W | A | D | A
```

| field | value |
| --- | --- |
| header row, by position | row 6 |
| populated header cells | 15 |
| determination | unclassified: needs a human read |
| evidence | rows=46; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 6:

- column 2: `WT`
- column 3: `H`
- column 4: `D`
- column 5: `V`
- column 6: `A`
- column 7: `R`
- column 8: `T`
- column 9: `N`
- column 10: `V`
- column 11: `A`
- column 12: `E`
- column 13: `W`
- column 14: `A`
- column 15: `D`
- column 16: `A`

### Sheet `Table S2K`

| field | value |
| --- | --- |
| declared dimensions | 72 rows by 36 columns |
| rows holding anything | 71 |
| widest populated row | 36 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2K. Mutation table from v2 PE PANCE PE2 RT evolut[...truncated for display, 81 chars total]
2: Mutations in clones emerging from evolution.
3: Blue shading indicates an amino acid change, and orange [...truncated for display, 141 chars total]
4:  |  |  | M-MLV RT
5: PBS length | RT Temp | Lagoon ID |  | 38 | 46 | 50 | 60 | 69 | 73 | 94 | 120 | 128 | 132 | 196 | 201 | 212 | 223 | 264 | 279 | 283 | 287 | 324 | 326 | 354 | 373 | 450 | 457 | 489 | 495 | 503 | 526 | 553 | 577 | 604 | 669
6:  |  |  | Clone | G | A | I | S | E | G | W | K | T | P | P | E | I | V | K | W | A | T | L | P | A | K | R | M | E | C | H | S | P | K | L | T
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 35 |
| determination | unclassified: needs a human read |
| evidence | rows=72; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `PBS length`
- column 2: `RT Temp`
- column 3: `Lagoon ID`
- column 5: `38`
- column 6: `46`
- column 7: `50`
- column 8: `60`
- column 9: `69`
- column 10: `73`
- column 11: `94`
- column 12: `120`
- column 13: `128`
- column 14: `132`
- column 15: `196`
- column 16: `201`
- column 17: `212`
- column 18: `223`
- column 19: `264`
- column 20: `279`
- column 21: `283`
- column 22: `287`
- column 23: `324`
- column 24: `326`
- column 25: `354`
- column 26: `373`
- column 27: `450`
- column 28: `457`
- column 29: `489`
- column 30: `495`
- column 31: `503`
- column 32: `526`
- column 33: `553`
- column 34: `577`
- column 35: `604`
- column 36: `669`

### Sheet `Table S2L`

| field | value |
| --- | --- |
| declared dimensions | 63 rows by 29 columns |
| rows holding anything | 59 |
| widest populated row | 29 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S2L. Mutation table from v3 PE PANCE PE2 RT evolut[...truncated for display, 81 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: v3 PANCE (using epegRNA)
5: Lagoon | Clone | M-MLV polyermase domain
6:  |  | 66 | 93 | 128 | 212 | 223 | 233 | 409 | 424
```

| field | value |
| --- | --- |
| header row, by position | row 6 |
| populated header cells | 8 |
| determination | unclassified: needs a human read |
| evidence | rows=63; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 6:

- column 3: `66`
- column 4: `93`
- column 5: `128`
- column 6: `212`
- column 7: `223`
- column 8: `233`
- column 9: `409`
- column 10: `424`

### Sheet `Table S2M`

| field | value |
| --- | --- |
| declared dimensions | 86 rows by 104 columns |
| rows holding anything | 79 |
| widest populated row | 104 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S15. Mutation table from v1 whole editor evolution[...truncated for display, 78 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: Blue shading indicates an amino acid change, and orange [...truncated for display, 141 chars total]
5: 
6: v1 PANCE
```

| field | value |
| --- | --- |
| header row, by position | row 8 |
| populated header cells | 40 |
| determination | unclassified: needs a human read |
| evidence | rows=86; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 8:

- column 2: `219`
- column 3: `255`
- column 4: `298`
- column 5: `555`
- column 6: `673`
- column 7: `714`
- column 8: `715`
- column 9: `721`
- column 10: `740`
- column 11: `753`
- column 12: `769`
- column 13: `888`
- column 14: `928`
- column 15: `972`
- column 16: `1077`
- column 17: `1121`
- column 18: `1135`
- column 19: `1138`
- column 20: `1180`
- column 21: `1207`
- column 22: `1293`
- column 23: `1320`
- column 24: `1321`
- column 25: `46`
- column 26: `107`
- column 27: `126`
- column 28: `128`
- column 29: `196`
- column 30: `199`
- column 31: `200`
- column 32: `223`
- column 33: `346`
- column 34: `485`
- column 35: `492`
- column 36: `498`
- column 37: `500`
- column 38: `502`
- column 39: `531`
- column 40: `534`
- column 41: `540`

### Sheet `Table S2N`

| field | value |
| --- | --- |
| declared dimensions | 61 rows by 78 columns |
| rows holding anything | 57 |
| widest populated row | 78 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S16. Mutation table from v1-v3 whole editor evolut[...truncated for display, 81 chars total]
2: Mutations in clones emerging from evolution.
3: 
4: v2 PACE, low stringency
5: Clone | Cas9 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | M-MLV RT polymerase domain
6:  | 35 | 42 | 68 | 80 | 87 | 89 | 102 | 114 | 123 | 127 | 196 | 199 | 218 | 227 | 286 | 295 | 320 | 355 | 374 | 420 | 496 | 558 | 566 | 584 | 588 | 653 | 660 | 661 | 694 | 701 | 713 | 717 | 739 | 740 | 774 | 781 | 895 | 911 | 914 | 918 | 937 | 961 | 965 | 973 | 975 | 1008 | 1062 | 1124 | 1142 | 1169 | 1172 | 1173 | 1194 | 1231 | 1258 | 1291 | 1304 | 1328 | 60 | 72 | 111 | 129 | 175 | 196 | 208 | 216 | 223 | 234 | 287 | 295 | 312 | 316 | 339 | 373 | 430 | 466 | 481
```

| field | value |
| --- | --- |
| header row, by position | row 6 |
| populated header cells | 77 |
| determination | unclassified: needs a human read |
| evidence | rows=61; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 6:

- column 2: `35`
- column 3: `42`
- column 4: `68`
- column 5: `80`
- column 6: `87`
- column 7: `89`
- column 8: `102`
- column 9: `114`
- column 10: `123`
- column 11: `127`
- column 12: `196`
- column 13: `199`
- column 14: `218`
- column 15: `227`
- column 16: `286`
- column 17: `295`
- column 18: `320`
- column 19: `355`
- column 20: `374`
- column 21: `420`
- column 22: `496`
- column 23: `558`
- column 24: `566`
- column 25: `584`
- column 26: `588`
- column 27: `653`
- column 28: `660`
- column 29: `661`
- column 30: `694`
- column 31: `701`
- column 32: `713`
- column 33: `717`
- column 34: `739`
- column 35: `740`
- column 36: `774`
- column 37: `781`
- column 38: `895`
- column 39: `911`
- column 40: `914`
- column 41: `918`
- column 42: `937`
- column 43: `961`
- column 44: `965`
- column 45: `973`
- column 46: `975`
- column 47: `1008`
- column 48: `1062`
- column 49: `1124`
- column 50: `1142`
- column 51: `1169`
- column 52: `1172`
- column 53: `1173`
- column 54: `1194`
- column 55: `1231`
- column 56: `1258`
- column 57: `1291`
- column 58: `1304`
- column 59: `1328`
- column 60: `60`
- column 61: `72`
- column 62: `111`
- column 63: `129`
- column 64: `175`
- column 65: `196`
- column 66: `208`
- column 67: `216`
- column 68: `223`
- column 69: `234`
- column 70: `287`
- column 71: `295`
- column 72: `312`
- column 73: `316`
- column 74: `339`
- column 75: `373`
- column 76: `430`
- column 77: `466`
- column 78: `481`

## mmc4.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc4.xlsx` |
| bytes | 56016 |
| sha256 | `b781fc5ba50810b7b03d1e372176ed14a79ca8bbac0335d6e8ddf0ebd190dd42` |
| sheets | 1 |
| highlighted cells | 0 |

Sheet names, in workbook order: `Sheet1`

Fill styles defined in this workbook: no painted fill defined in the workbook.

### Sheet `Sheet1`

| field | value |
| --- | --- |
| declared dimensions | 80 rows by 56 columns |
| rows holding anything | 79 |
| widest populated row | 56 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S3. Reagents used to install pathogenic mutations [...truncated for display, 294 chars total]
2: 
3: peg_ID | Name | Gene | Phenotype | pegRNA PBS_seq | pegRNA Spacer | pegRNA RTT | pegRNA 3' motif | pegRNA Terminator | PBS length | RTT length | pegRNA scaffold | pegRNA full length (5' to 3') | ngRNA spacer | ngRNA scaffold | ngRNA terminator | ngRNA full length  (5' to 3' ) | HTS_Fwd_Primer | HTS_Rev_Primer | Unedited nucleotide sequence (5' to 3') | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3 | rep1 | rep2 | rep3
4: peg_1000_1 | NM_000350.3(ABCA4):c.1822T>A (p.Phe608Ile) | ABCA4 | Stargardt disease 1 | TGTACCGGAAATC | GGAAGATTTCCGGTACATCT | AGATAGGCAATCCCGCCCCAGA | CGCGGTTCTATCTAGTTACGCGTTAAACCAACTAGAA | TTTTTT | 13 | 22 | GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAA[...truncated for display, 76 chars total] | GGAAGATTTCCGGTACATCTGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCT[...truncated for display, 174 chars total] |  |  |  |  | ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNGATTCCAACTGGAGCCTCC[...truncated for display, 59 chars total] | TGGAGTTCAGACGTGTGCTCTTCCGATCTTGAGCTATCCAAGCCCGTTCCC | TGAGCTATCCAAGCCCGTTCCCATCCTTTGTCCCTCTGTGTCTTCTCAGGTATTGG[...truncated for display, 185 chars total] | 12.145796 | 12.3266564 | 13.4139389 | 14.6284006 | 14.1723704 | 13.5091748 | 9.68162447 | 10.4753713 | 11.1700727 | 0.05640719 | 0.08264463 | 0.1140145 | 0.16211561 | 0.13968431 | 0.12931707 | 0.16211248 | 0.14909112 | 0.12885348
5: peg_1000_2 | NM_000350.3(ABCA4):c.2461T>C (p.Trp821Arg) | ABCA4 | Stargardt disease 1 | GCCTTGCTCTTCA | GCTTTGAAGAGCAAGGCCTG | TTGCTCCGCTGCAGCCCCAG | CGCGGTTCTATCTAGTTACGCGTTAAACCAACTAGAA | TTTTTT | 13 | 20 | GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAA[...truncated for display, 76 chars total] | GCTTTGAAGAGCAAGGCCTGGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCT[...truncated for display, 172 chars total] |  |  |  |  | ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNACACCTGATCAAGGTACCA[...truncated for display, 60 chars total] | TGGAGTTCAGACGTGTGCTCTTCCGATCTCGAGGGCATCTGGGTGCTGTT | CGAGGGCATCTGGGTGCTGTTGCATTGGATAAAAGGCACTGCTCTTTTTCTGTGCC[...truncated for display, 273 chars total] | 20.74449 | 21.0284966 | 22.4346545 | 25.6838971 | 28.4917089 | 25.8295068 | 21.8973834 | 22.3569024 | 21.5000324 | 1.45045232 | 1.45649088 | 1.25843481 | 1.93087677 | 1.7555357 | 1.60425753 | 1.6761682 | 1.82163515 | 1.96633462
6: peg_1000_3 | NM_000397.3(CYBB):c.907C>A (p.His303Asn) | CYBB | Granulomatous disease, chronic, X-linked, variant;not pr[...truncated for display, 62 chars total] | ATAGAATAAAACA | gCATATGTTTTATTCTATAGG | TTGAAAGGGTTAGTGACCACCT | CGCGGTTCTATCTAGTTACGCGTTAAACCAACTAGAA | TTTTTT | 13 | 22 | GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAA[...truncated for display, 76 chars total] | gCATATGTTTTATTCTATAGGGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGC[...truncated for display, 175 chars total] |  |  |  |  | ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNCATCTGCTGGAGGAACTCC[...truncated for display, 61 chars total] | TGGAGTTCAGACGTGTGCTCTTCCGATCTAGCTTGGACACCTTTGGGCACTT | CATCTGCTGGAGGAACTCCTGTGTTGTCCCTAAAGCAGAGATCTAAGTGGGCCAAT[...truncated for display, 249 chars total] | 8.40002705 | 9.22000459 | 8.61131521 | 12.2762321 | 13.0774075 | 11.9191919 | 10.4873602 | 10.9434937 | 11.3842402 | 0.06537863 | 0.04817619 | 0.05038312 | 0.05861929 | 0.07421401 | 0.0453978 | 0.04898092 | 0.07930068 | 0.04813632
```

| field | value |
| --- | --- |
| header row, by position | row 3 |
| populated header cells | 56 |
| determination | candidate: an assayed panel |
| evidence | rows=80; activity-like header: yes; sequence-like header: yes; accession-like header: no |

Every column header on row 3:

- column 1: `peg_ID`
- column 2: `Name`
- column 3: `Gene`
- column 4: `Phenotype`
- column 5: `pegRNA PBS_seq`
- column 6: `pegRNA Spacer`
- column 7: `pegRNA RTT`
- column 8: `pegRNA 3' motif`
- column 9: `pegRNA Terminator`
- column 10: `PBS length`
- column 11: `RTT length`
- column 12: `pegRNA scaffold`
- column 13: `pegRNA full length (5' to 3')`
- column 14: `ngRNA spacer`
- column 15: `ngRNA scaffold`
- column 16: `ngRNA terminator`
- column 17: `ngRNA full length  (5' to 3' )`
- column 18: `HTS_Fwd_Primer`
- column 19: `HTS_Rev_Primer`
- column 20: `Unedited nucleotide sequence (5' to 3')`
- column 21: `rep1`
- column 22: `rep2`
- column 23: `rep3`
- column 24: `rep1`
- column 25: `rep2`
- column 26: `rep3`
- column 27: `rep1`
- column 28: `rep2`
- column 29: `rep3`
- column 30: `rep1`
- column 31: `rep2`
- column 32: `rep3`
- column 33: `rep1`
- column 34: `rep2`
- column 35: `rep3`
- column 36: `rep1`
- column 37: `rep2`
- column 38: `rep3`
- column 39: `rep1`
- column 40: `rep2`
- column 41: `rep3`
- column 42: `rep1`
- column 43: `rep2`
- column 44: `rep3`
- column 45: `rep1`
- column 46: `rep2`
- column 47: `rep3`
- column 48: `rep1`
- column 49: `rep2`
- column 50: `rep3`
- column 51: `rep1`
- column 52: `rep2`
- column 53: `rep3`
- column 54: `rep1`
- column 55: `rep2`
- column 56: `rep3`

## mmc5.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc5.xlsx` |
| bytes | 33730 |
| sha256 | `8883df7b18a3ac566ba26a4b30198dea1195a669726c17fbfcc9a8f4941ba159` |
| sheets | 1 |
| highlighted cells | 332 |

Sheet names, in workbook order: `Sheet1`

Fill styles defined in this workbook: fill id 2: theme="1".

### Sheet `Sheet1`

| field | value |
| --- | --- |
| declared dimensions | 169 rows by 13 columns |
| rows holding anything | 168 |
| widest populated row | 13 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S17. Editing efficiencies of single Cas9 mutants, [...truncated for display, 76 chars total]
2: Summary of mutants and corresponding editing efficiencie[...truncated for display, 84 chars total]
3: 
4:  |  |  |  | RNF2 |  |  |  |  | PCSK9
5: Editor ID | Mutation | Well ID |  | Rep1 | Rep2 | Rep3 | Mean |  | Rep1 | Rep2 | Rep3 | Mean
6: Casplate2_Editor1 | K775E | Plate2_B2 |  | 50.5216676 | 43.2868541 | 46.7572305 | 46.85525073333333 |  | 28.6857936 | 36.6529459 | 34.7383688 | 33.359036100000004
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 11 |
| determination | unclassified: needs a human read |
| evidence | rows=169; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `Editor ID`
- column 2: `Mutation`
- column 3: `Well ID`
- column 5: `Rep1`
- column 6: `Rep2`
- column 7: `Rep3`
- column 8: `Mean`
- column 10: `Rep1`
- column 11: `Rep2`
- column 12: `Rep3`
- column 13: `Mean`

## mmc6.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc6.xlsx` |
| bytes | 10127 |
| sha256 | `aaa38000856621c83f648fbfbd867728af5d8a4fa6c890d2924ef8f16db78735` |
| sheets | 1 |
| highlighted cells | 0 |

Sheet names, in workbook order: `Sheet1`

Fill styles defined in this workbook: no painted fill defined in the workbook.

### Sheet `Sheet1`

| field | value |
| --- | --- |
| declared dimensions | 31 rows by 2 columns |
| rows holding anything | 26 |
| widest populated row | 2 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S18. Genotypes of RT and Cas9 variants relating to[...truncated for display, 83 chars total]
2: Mutations in RT and Cas9 variants that were tested in Fi[...truncated for display, 79 chars total]
3: 
4: Figure 1:
5: rdPERV | PERV RT D200N+T306K+W313F+E330P+L603W
6: rdAVIRE | AVIRE RT D200N+T306K+W313F+G330P+L603W
```

| field | value |
| --- | --- |
| header row, by position | row 5 |
| populated header cells | 2 |
| determination | unclassified: needs a human read |
| evidence | rows=31; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 5:

- column 1: `rdPERV`
- column 2: `PERV RT D200N+T306K+W313F+E330P+L603W`

## mmc7.xlsx

| field | value |
| --- | --- |
| path | `tasks/taskA_crossfamily/raw/mmc7.xlsx` |
| bytes | 219558 |
| sha256 | `3cc3b4977174710b31d7e86961e018c229207323a6714d57fb2d5079c5c1b1b6` |
| sheets | 3 |
| highlighted cells | 0 |

Sheet names, in workbook order: `Table S6A`, `Table S6B`, `Table S6C`

Fill styles defined in this workbook: fill id 2: theme="5" tint="0.79998168889431442".

### Sheet `Table S6A`

| field | value |
| --- | --- |
| declared dimensions | 1118 rows by 25 columns |
| rows holding anything | 451 |
| widest populated row | 10 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S19. PegRNAs, epegRNAs and sgRNAs  sequences used [...truncated for display, 95 chars total]
2: 
3:  | spacer | scaffold | template | PBS | linker | 3' motif | terminator
4: Figure 1C
5: HEK3, +5 G to T | GGCCCAGACTGAGCACGTGA | GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAA[...truncated for display, 76 chars total] | TCTGCAATCA | CGTGCTCAGTCTG |  |  | TTTTTT
6: RNF2, +5 G to T | GTCATCTTAGTCATTACCTG | GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAA[...truncated for display, 76 chars total] | AACGAACACATCAG | GTAATGACTAAGATG |  |  | TTTTTT
```

| field | value |
| --- | --- |
| header row, by position | row 3 |
| populated header cells | 7 |
| determination | candidate: an unassayed sequence set |
| evidence | rows=1118; activity-like header: no; sequence-like header: no; accession-like header: no |

Every column header on row 3:

- column 2: `spacer`
- column 3: `scaffold`
- column 4: `template`
- column 5: `PBS`
- column 6: `linker`
- column 7: `3' motif`
- column 8: `terminator`

### Sheet `Table S6B`

| field | value |
| --- | --- |
| declared dimensions | 1024 rows by 26 columns |
| rows holding anything | 247 |
| widest populated row | 4 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S19. Primer sequences used in this study, related [...truncated for display, 71 chars total]
2: 
3: Sequences of primers used for mammalian cell genomic DNA[...truncated for display, 78 chars total]
4: Locus | Fwd-primer | Rev-primer
5: Figure 1C
6: HEK3 | ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNNCAGGGAAACGCCCATGCAA[...truncated for display, 60 chars total] | TGGAGTTCAGACGTGTGCTCTTCCGATCTCTCTGTTGAGCTCGACCCTGAA
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 3 |
| determination | unclassified: needs a human read |
| evidence | rows=1024; activity-like header: yes; sequence-like header: no; accession-like header: no |

Every column header on row 4:

- column 1: `Locus`
- column 2: `Fwd-primer`
- column 3: `Rev-primer`

### Sheet `Table S6C`

| field | value |
| --- | --- |
| declared dimensions | 1002 rows by 26 columns |
| rows holding anything | 51 |
| widest populated row | 2 cells |
| layout | tabular |

First 6 rows, verbatim:

```
1: Table S20. Amplicon sequences used in HTS analysis in th[...truncated for display, 89 chars total]
2: Genomic loci are human wild-type sequences, unless speci[...truncated for display, 121 chars total]
3: 
4: Human amplicons | Unedited nucleotide sequence (5' to 3')
5: AAVS1 | CGCCGGGAACTGCCGCTGGCCCCCCACCGCCCCAAGGATCTCCCGGTCCCCGCCCG[...truncated for display, 238 chars total]
6: HEK3 | AGGGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAG[...truncated for display, 334 chars total]
```

| field | value |
| --- | --- |
| header row, by position | row 4 |
| populated header cells | 2 |
| determination | candidate: an unassayed sequence set |
| evidence | rows=1002; activity-like header: no; sequence-like header: yes; accession-like header: no |

Every column header on row 4:

- column 1: `Human amplicons`
- column 2: `Unedited nucleotide sequence (5' to 3')`

## Determination for Gate G1

Every sheet of every supplementary workbook above has been enumerated. This is
the statement a human is asked to confirm before any row is parsed.

| question | answer |
| --- | --- |
| Which block holds the assayed enzymes | `mmc2.xlsx`, sheet `Table S1`, block 1: rows 6 to 118, index 1 to 57, 57 entries |
| Which block holds the phylogenetic sequences | `mmc2.xlsx`, sheet `Table S1`, block 2: rows 122 to 1092, index 58 to 543, 486 entries |
| How activity is recorded | a green cell fill on the name of each active enzyme, not a column |
| How many entries carry that fill | 21 |

### The evidence for each determination

The assayed block is identified by three independent signals, not by position:

1. Its own caption, on the row above it: sequences and identity of reverse
   transcriptases **tested for prime editing**.
2. Its names are bare laboratory labels such as `MMLV-RT` and `Tf1-RT`, with no
   database identifier among them. The other block's names are UniProt FASTA
   headers of the form `tr|ACCESSION|ENTRY_NAME ... OS=... OX=...`, which is what
   a BLAST result looks like.
3. Only the assayed block carries the highlight fill, which the caption on row 5
   defines as activity. The other block carries none, which is consistent with it
   never having been assayed.

### What this means for the parse

Only the assayed block may be read into `curated.csv`. The parser must key on the
caption-delimited row range and assert the entry count it finds, so that a sheet
whose layout differs from this one halts rather than silently taking the wrong
rows. The running index is **not** safe to filter on by itself: it continues from
the first block into the second without restarting, so an index filter of 1 to 57
happens to work here only because the assayed block comes first.

### Two count discrepancies against the article prose, recorded not resolved

- The prose says the authors tested 59 enzymes. This block holds 57, so
  2 are unaccounted for. The gap is between the article's own text and its own
  Table S1. It cannot be closed from either of them.
- The prose says twenty RTs showed detectable activity. 21 entries carry the
  activity fill, so that gap is one enzyme.

Neither is resolved here. Both are carried into `reports/reconciliation.md` with
the evidence for each reading, for a human to rule on at Gate G2.

### What Table S1 does not contain

Stated explicitly, because each absence changes what the benchmark can claim:

- **No efficiency values.** There is no numeric column anywhere in the sheet. The
  activity label is binary, carried by a fill colour. So the inherited
  `pe_efficiency_pct` column cannot be verified against Table S1.
- **No accessions for the assayed enzymes.** Their names are bare labels. Every
  database identifier in the workbook belongs to the phylogenetic block.
- **No class or family assignment.** The paper's 14 classes exist in Figure 1B, a
  rendered tree, and nowhere in this workbook. So the inherited 7-family labelling
  cannot be mapped onto the paper's 14 classes from this source.

All 6 supplementary workbooks were scanned for a source of the Figure 1C per-enzyme
efficiencies. None holds one: the other workbooks are the evolution mutation
tables, the Figure 5F reagent and frequency table, the Figure 6E Cas9 mutant
efficiencies, the RT and Cas9 variant genotypes, and the pegRNA and primer
sequences. The Figure 1C values appear to exist only as plotted points.

Total indexed entries across all blocks: 543.
