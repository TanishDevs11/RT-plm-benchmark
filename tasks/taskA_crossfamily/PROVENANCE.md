# Provenance: Cross-family ortholog prime editing activity

Task identifier: `A`
Directory: `tasks/taskA_crossfamily/`
Status: **SOURCE ACQUIRED, NOT YET PARSED.** Awaiting the Gate G1 ruling on the sheet
identification in `reports/tableS1_inventory.md`.

This file is the per-task provenance record. It is written before any data is parsed and
is filled in as acquisition proceeds, so that the gap between what was planned and what
was obtained stays visible rather than being quietly closed.

The brief for this task names the directory `tasks/taskA/`. The longer name here is the
one already carried by the frozen splits, the audit and the earlier reports, so it is
kept and this line records the alias rather than creating a second directory holding the
same task.

## Sources

One block per source. A source that was attempted and failed keeps its block, with the
reason recorded, rather than being deleted.

### Source 1: Supplementary Table S1, the RT panel

| field | value |
| --- | --- |
| citation | Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. Phage-assisted evolution and protein engineering yield compact, efficient prime editors. Cell 2023, 186(18):3983-4002.e26 |
| DOI | `10.1016/j.cell.2023.07.039` |
| PMC accession | `PMC10482982` |
| file as downloaded | `raw/mmc2.xlsx`, the publisher's own filename, kept unchanged |
| SHA256 of that file | `16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c` |
| bytes | 215647 |
| access date | 2026-10-02 |
| route that succeeded | Europe PMC `supplementaryFiles` endpoint with `includeInlineImage=false`, which returns a zip of the article's supplementary files |
| sequences taken from | sheet `Table S1`, rows 6 to 118, the caption-delimited assayed block, 57 entries |
| activity values taken from | the green cell fill on each active enzyme's name cell in that block. There is no activity column. 21 entries carry the fill |
| efficiency values taken from | **nowhere. Table S1 carries no numeric cell except the row index.** See the open question below |
| label definition, verbatim | "prime editing efficiencies shown reflect the frequency of the intended prime editing outcome with no indels or other changes at the target site" (Figure 1 caption) |
| activity criterion, verbatim | "Twenty RTs from four different classes showed detectable PE activity"; the criterion is the word detectable, with no stated numeric threshold |
| label units | binary for activity. Percent of sequenced alleles for efficiency, where an efficiency value can be sourced at all |
| reference accession plus version | absent from this source. The assayed block's names are bare laboratory labels, with no database identifier among them |
| full length or truncation | not stated in the table. Each entry is a single excised RT domain sequence of the length given in the cell |
| licence and redistribution status | CC BY 4.0, per the article's own permissions block: "This is an open access article under the CC BY license" |
| committed to `raw/` or fetch script only | **committed**, which CC BY permits. The earlier plan had assumed Elsevier terms would forbid it; the licence was checked rather than assumed |

### Source 2: Article full text, for everything the table cannot settle

| field | value |
| --- | --- |
| file as downloaded | `raw/PMC10482982_fulltext.xml`, JATS XML |
| SHA256 of that file | `5ce4b3b22e7dc14e76fcf0542014eb8ac3494e90371e7ad263e3f1c43cf5c397` |
| bytes | 301315 |
| access date | 2026-10-02 |
| retrieved from | `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10482982/fullTextXML` |
| why it is here | the table has no efficiency values, no accessions and no class labels, and does not state the activity criterion. The article body states the counts, the criterion, the efficiency definition and the licence. Those quotations are extracted to `reports/doman2023_source_facts.md` |

### Also acquired, not used by Task A

`raw/mmc3.xlsx` through `raw/mmc7.xlsx`, Tables S2 to S6, arrived in the same archive and
are kept because the licence permits it and because the Figure 1C efficiency search had
to examine all of them to be able to report that none holds those values. Checksums are
in `raw/CHECKSUMS.txt`. None is a Task A input.

### Routes attempted and failed

Recorded in full in `data_acquisition/fetch_doman_s1_attempts.json`. In summary:

| route | outcome |
| --- | --- |
| Europe PMC `supplementaryFiles`, default parameters | HTTP 200 but the archive includes the inline figure images and stalled mid-stream; later attempts returned 500 then 503 under rate limiting |
| NCBI PMC Open Access service, `oa.fcgi` | HTTP 404. This article is not in the OA package subset |
| PMC article page, `/articles/instance/10482982/bin/mmc2.xlsx` | HTTP 200 serving an HTML bot-check page, not a workbook. Refused by the fetcher's magic-byte guard |
| Publisher, `cell.com` | HTTP 403 on both the full text page and the attachment path |

## Reconciliation

To be written by the parser run, not by hand: rows expected, rows parsed, rows dropped,
and the reason for every drop. Not yet run; gated on G1.

What the acquisition already establishes, before any parse:

- Table S1's assayed block holds **57** entries, and their names are exactly the 57
  `rt_name` values in the inherited `data/rt_sequences.csv`, as sets.
- **21** of those entries carry the activity fill, and they are exactly the 21 rows the
  inherited file marks `active = 1`.
- So the inherited row set and the inherited binary labels both reproduce Table S1
  exactly. The 57-against-59 and 21-against-20 discrepancies are between the article's
  prose and the article's own Table S1, not between this repository and the paper.

## Open questions

Carried into `reports/reconciliation.md` and `reports/data_pipeline_report.md`.

1. **The prose says 59 enzymes were tested; Table S1 lists 57.** Neither the table nor
   the text names the missing two. Unresolvable from the published record as fetched.
2. **The prose says twenty RTs showed detectable activity; Table S1 highlights 21.** The
   class breakdown in the text, 11 retroviral plus 2 LTR retrotransposon plus 7
   bacterial, matches the highlighted set in every class except retroviral, where the
   text says 11 and the table highlights 12. M-MLV RT is the wild-type RT of the PE1
   comparator rather than a survey candidate, which would explain the text excluding it.
   That is an inference and is labelled as one.
3. **No efficiency values exist in any supplementary file.** The Figure 1C per-enzyme
   efficiencies appear only as plotted points. The inherited `pe_efficiency_pct` column
   therefore has no verifiable source in the published supplementary material, and its
   provenance is unknown. This is the most consequential open question for Task A,
   because that column is the regression target and it carries most of the CLS weight.
4. **No accessions.** They are absent from Table S1, and the article's full text contains
   no protein accession of any recognised form. The data availability statement points at
   the key resources table, whose accessions are sequencing-read accessions for the SRA
   deposit. Accessions must therefore come from sequence-level resolution against UniProt,
   which `data_acquisition/resolve_taskA_accessions.py` has already done for 27 of 57 rows
   exactly, 6 ambiguously, with 24 unresolved.
5. **No class labels.** The paper's 14 classes exist only in the Figure 1B tree image. The
   inherited 7-family labelling cannot be mapped onto them from this source, so the
   coarsening cannot be verified and the controlled vocabulary has to be derived from the
   inherited labels with that limitation stated.
