# Source facts: Doman et al. 2023, from the article text

Written by `data_acquisition/extract_doman_fulltext_facts.py`. Every quotation
below is reproduced from the article XML with only tag stripping and whitespace
collapsing applied. Nothing here is a paraphrase, and nothing here was recalled
rather than read.

| field | value |
| --- | --- |
| citation | Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. Cell 2023, 186(18):3983-4002.e26 |
| DOI | `10.1016/j.cell.2023.07.039` |
| PMC accession | `PMC10482982` |
| source file | `tasks/taskA_crossfamily/raw/PMC10482982_fulltext.xml` |
| source SHA256 | `5ce4b3b22e7dc14e76fcf0542014eb8ac3494e90371e7ad263e3f1c43cf5c397` |
| retrieved from | `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10482982/fullTextXML` |
| access date | 2026-10-02 |

## Licence

> © 2023 The Authors This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/).

CC BY 4.0 permits redistribution with attribution, so the supplementary files
and this XML may be committed to `raw/` rather than only a fetch script. That
settles the licence question Task A's provenance record had left open, which had
assumed Elsevier terms would forbid it.

## Which supplementary file is which

Taken from the article's own supplementary-material declarations, so the mapping
from `mmcN` to table number is the publisher's, not an inference from file order.

| file | declared contents |
| --- | --- |
| `mmc1.pdf` | Document S1. Notes S1 and S2 |
| `mmc2.xlsx` | Table S1. List of reverse transcriptases used in this study, related to Figure 1 Sequences and identities of reverse transcriptases used for BLAST query, phylogenetic analysis, and initial screen of RTs in Figures 1 B and 1C |
| `mmc3.xlsx` | Table S2. (A–N) Mutation tables from PE PA(N)CE, related to Figures 2, 3, 4, and 6 Mutations in clones emerging from evolution |
| `mmc4.xlsx` | Table S3. Reagents used to install pathogenic mutations into endogenous sites in HEK293T cells using PEmax and Tf1-derived editors along with their corresponding editing and indel frequencies, related to Figure 5 EpegRNAs, nicking sgRNAs, high-throughput sequencing primers, and amplicons, along with editing and indel frequencies used to make Figure 5 F |
| `mmc5.xlsx` | Table S4. Editing efficiencies of single Cas9 mutants, related to Figure 6 Summary of mutants and corresponding editing efficiencies used to generate Figure 6 E |
| `mmc6.xlsx` | Table S5. Genotypes of RT and Cas9 variants related to Figures 1, 3, 4, 5, and 6 Mutations in RT and Cas9 variants that were tested in Figures 1 , 3 , 4 , 5 , and 6 |
| `mmc7.xlsx` | Table S6. (A–C) pegRNA sequences, primer sequences, and amplicon sequences for HTS analysis used in this study, related to Figures 1–7 |

Table S1 is `mmc2.xlsx`. Note what its own caption says it contains: sequences
and identities for the BLAST query, for the phylogenetic analysis, **and** for
the initial screen in Figures 1B and 1C. One file, both datasets, which is the
reason the workbook is inventoried sheet by sheet before anything is parsed.

## The questions the reconciliation has to answer

### How many enzymes were tested, and how many classes

> ... cells in the mouse cortex. Results Surveying reverse transcriptase enzymes for prime editing Because only a handful of RTs beyond M-MLV RT have been used for PE, 3 , 16 , 21 , 22 we first surveyed RTs from diverse phylogenetic origins and tested 59 enzymes ( Table S1 ) spanning 14 classes ( Figure 1 B) as prime editors. We compared these editors to PE1, PE2, and PE2ΔRNaseH (the RNaseH-truncated form of PE2 used for dual-AAV delivery 3 , 21 , 25 , 26 , 27 ) for three edits in HEK293T cells. Twenty RTs from four different classes showed detectable PE activity, and nine of these RTs are ≥500 bp smaller in gene size than M-MLV RT ( Figure 1 C). However, all PE-compatible ...

### How many were called active, and by what criterion

> ...phylogenetic origins and tested 59 enzymes ( Table S1 ) spanning 14 classes ( Figure 1 B) as prime editors. We compared these editors to PE1, PE2, and PE2ΔRNaseH (the RNaseH-truncated form of PE2 used for dual-AAV delivery 3 , 21 , 25 , 26 , 27 ) for three edits in HEK293T cells. Twenty RTs from four different classes showed detectable PE activity, and nine of these RTs are ≥500 bp smaller in gene size than M-MLV RT ( Figure 1 C). However, all PE-compatible RTs exhibited lower editing efficiencies than PE2, with the smaller RTs showing especially poor activity ( Figures 1 C and S1 A). These results agree with recent reports 3 , 16 , 21 , 22 that while diverse RTs can support PE, their wild-type forms...

### How the 20 actives break down by class

> ...T edit). RT enzymes engineered in Figure 1 are highlighted in green, and the wild-type M-MLV RT used in the PE1 system is highlighted in black. All other enzymes are in red. Dots reflect the mean of n = 3 independent replicates. Of these enzymes that can support detectable mammalian PE activity, 11 are closely related to the M-MLV RT and are encoded by retroviruses, two are encoded by LTR retrotransposons, and seven are bacterial RTs from group-II introns, retrons, or CRISPR-Cas associated systems. (B) Overview of twinPE. The prime editor protein (gray and blue) uses two pegRNAs (dark blue and teal) to target opposite strands of DNA. The prime edi...

### What quantity the reported efficiencies are

> ...f n = 3 independent replicates (C, D, G, H, and J). See also Figure S1 . Throughout all figures ( Figures 1 , 2 , 3 , 4 , 5 , 6 , 7 , and S1–S7 ), prime editing efficiencies shown reflect the frequency of the intended prime editing outcome with no indels or other changes at the target site. Since the development of PE systems, we and others have improved them by engineering the pegRNA, 3 , 4 , 5 prime editor archite...

### What Figure 1C plots, which is the panel the survey values come from

> ...ve enzymes. Green circles indicate PE-inactive enzymes. (C) Mammalian activity of 20 different RT enzymes in the prime editing system at endogenous sites in HEK293T cells. (D) Comparison of wild-type Tf1 RT, PE2ΔRNaseH, and PE2 at three longer, complex PE ( HEK3 ) or twinPE ( CCR5 and IDS ) edits in HEK293T cells. (E) Compa...

### Where the 543 phylogenetic sequences come from, and that they share Table S1

> ...ng QIAprep Spin Miniprep Kit. All isolated plasmid DNA were eluted in nuclease-free water and quantified using NanoDrop One UV-Vis spectrophotometer (Thermo Fisher Scientific). Phylogenetic tree analysis RT protein sequences were collected by searching the UniProt database with the BLASTP algorithm using query sequences listed in Table S1 . Each individual BLASTP result was filtered to remove duplicate sequences, sequences shorter than 100 residues, and sequences longer than 1000 residues. To reduce phylogenetic complexity, 9–10 representative sequences were randomly sampled from each filtered BLASTP result. The 543 RT sequences used for downstream phylogenetic analyses are listed in Table S1 . Phylogenetic analyses were performed using Geneious Prime. The MUSCLE algorithm was used to generate a multiple sequence alignment of all 543 RT sequences. From this sequence...

### That the phylogenetic set was never assayed, only BLAST sampled

> ... Miniprep Kit. All isolated plasmid DNA were eluted in nuclease-free water and quantified using NanoDrop One UV-Vis spectrophotometer (Thermo Fisher Scientific). Phylogenetic tree analysis RT protein sequences were collected by searching the UniProt database with the BLASTP algorithm using query sequences listed in Table S1 . Each individual BLASTP result was filtered to remove duplicate sequences, sequences shorter than 100 residues, and sequences longer than 1000 residues. To reduce phylogenetic complexity, 9–10 representative sequences were randomly sampled from each filtered BLASTP result. The 543 RT sequences used for downstream phylogenetic analyses are listed in Table S1 . Phylogenetic analyses were performed using Geneious Prime. The MUSCLE algorithm was used to generate a multiple sequence alignment of all...

### Where accession numbers are said to live

> ...ences, and amplicon sequences for HTS analysis used in this study, related to Figures 1–7 Data and code availability • All sequencing data have been deposited at the NCBI Sequence Read Archive database and are publicly available as of the date of publication. Accession numbers are listed in the key resources table . • All original code is available in Notes S1 and S2 . • Any additional information required to reanalyze the data reported in this paper is available from th...

### Figure 1 caption, in full

> Figure 1 Identification and engineering of reverse transcriptase enzymes into prime editor candidates (A) Overview of PE systems. All use a prime editor protein consisting of SpCas9(H840A) nickase fused to a reverse transcriptase (RT) enzyme. PE1 uses the wild-type RT from the Moloney murine leukemia virus (M-MLV), while the PE2 system uses an engineered pentamutant variant of the M-MLV RT. PE3 uses an additional single guide RNA (sgRNA) to nick the non-edited strand. PBS = primer binding site. RT template = reverse transcriptase template. (B) Phylogenetic classification of RTs tested in this study. Red circles indicate PE-active enzymes. Green circles indicate PE-inactive enzymes. (C) Mammalian activity of 20 different RT enzymes in the prime editing system at endogenous sites in HEK293T cells. (D) Comparison of wild-type Tf1 RT, PE2ΔRNaseH, and PE2 at three longer, complex PE ( HEK3 ) or twinPE ( CCR5 and IDS ) edits in HEK293T cells. (E) Comparison of prime editors containing engineered retroviral RT variants with their wild-type counterparts in HEK293T cells. Horizontal bars show the mean value. (F) Residues mutated to improve editing of the Tf1 RT prime editor correspond to V188, R118, L258, M281 and V286 (red) in Ty3 RT (blue, PDB: 4OL8). V188 and R118 are in close proximity to the RNA (green) substrate and correspond to K118 and S188 in Tf1, respectively. L258, M281 and V286 are near the DNA (yellow) substrate and correspond to I260, S297 and R288 in Tf1, respectively. (G) Rationally designed Tf1 pentamutant variant (rdTf1) shows improvements in editing over its wild-type counterpart in HEK293T cells. All edits are PE edits, except the AAVS1 site, which is twinPE. (H) Rationally designed Ec48 triple mutant variant (rdEc48) shows improvements in editing over its wild-type counterpart for five edits in HEK293T cells. (I) Comparison of prime editors containing engineered RT variants with PE2 in HEK293T cells. All edits use single-flap prime editing, except the AAVS1 site, which uses twinPE. (J) Comparison of rdTf1 with PE2 and its wild-type counterpart at three longer, complex PE ( HEK3 ) or twinPE ( CCR5 and IDS ) edits in HEK293T cells. Dots indicate individual replicates for n = 3 biological replicates (C–E and G–J). Bars reflect the mean of n = 3 independent replicates (C, D, G, H, and J). See also Figure S1 . Throughout all figures ( Figures 1 , 2 , 3 , 4 , 5 , 6 , 7 , and S1–S7 ), prime editing efficiencies shown reflect the frequency of the intended prime editing outcome with no indels or other changes at the target site.

## What these quotations establish, and what they do not

Established by the article text alone, before Table S1 is opened:

1. **59 enzymes were tested, spanning 14 classes.** The inherited
   `data/rt_sequences.csv` has 57 rows, so 2 rows are unaccounted for and the
   gap is real rather than a miscount.
2. **Twenty RTs showed detectable PE activity**, and the criterion is the word
   detectable, not a stated numeric threshold. The inherited file has 21 actives.
3. **The 20 break down as 11 retroviral, 2 LTR retrotransposon, and 7 bacterial**
   from group-II introns, retrons, or CRISPR-Cas systems. The inherited file has
   12 retroviral, 2 LTR retrotransposon, 2 group-II intron, 5 retron and 0
   CRISPR-associated actives. The bacterial total agrees at 7 and the
   retrotransposon total agrees at 2; the entire discrepancy is one extra
   retroviral active. Which enzyme that is, is settled in the reconciliation
   report against Table S1, not here.
4. **The efficiency quantity is defined verbatim**: the frequency of the intended
   prime editing outcome with no indels or other changes at the target site. So a
   percentage in this benchmark is a correct-edit frequency, not a total editing
   rate, and not an indel-inclusive one.
5. **The 543 sequences are BLAST hits, randomly subsampled, never assayed.** They
   share Table S1 with the assayed panel. Any of them appearing in `curated.csv`
   would be an unlabelled sequence carrying an invented label.

Not established by the article text, and left open here:

- **Which two enzymes the inherited 57 omits.** Needs the Table S1 roster.
- **Whether Table S1 carries per-enzyme efficiency values at all.** Its caption
  promises sequences and identities. The numbers in Figure 1C may exist only as
  plotted points, in which case the inherited `pe_efficiency_pct` column cannot
  be verified against any table and that has to be said plainly.
- **Accession numbers.** The data availability statement points at the key
  resources table, and a scan of the full text finds no protein accession of any
  recognised form in it: the accessions mentioned there are sequencing-read
  accessions for the SRA deposit, not RT protein accessions. So accessions have
  to come from Table S1 or from sequence-level resolution against UniProt.

