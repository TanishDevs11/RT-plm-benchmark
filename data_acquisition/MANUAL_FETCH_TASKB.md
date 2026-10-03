# Manual fetch required: Task B, the M-MLV RT saturated mutagenesis screen

Every scripted route failed. **Task B has no labels and cannot proceed past
acquisition.** This is a recorded outcome, not a reason to estimate, model, or
reconstruct the values.

## What is needed

| file | why | destination |
| --- | --- | --- |
| Supplementary Tables S6 and S7 | the per-variant normalized editing efficiencies for libraries L1 and L2. Without these Task B has no labels at all | `tasks/taskB_mmlv_dms/raw/table_s6.xlsx`, `table_s7.xlsx` |
| Supplementary Sequence 1 | the PE2dR construct protein sequence. Every one of the 1045 variants is built on it, and building them on a reference wrong at even one position would invalidate the whole task | `tasks/taskB_mmlv_dms/raw/supplementary_sequences.pdf` |

## The work

| field | value |
| --- | --- |
| title | Saturated mutagenesis screen of M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency |
| DOI, resolved | `10.64898/2026.07.06.736660` |
| DOI in the brief, which does not resolve | `10.1101/2026.07.06.736660` |
| version | 1 |
| posted | 2026-07-07 |
| licence | cc_by_nc |
| corresponding author | Haojie Yu |

## Routes tried

| route | URL | status | outcome |
| --- | --- | --- | --- |
| 2 | `https://api.biorxiv.org/details/biorxiv/10.64898/2026.07.06.736660` | 200 | resolved: version 1, posted 2026-07-07, licence cc_by_nc |
| 2 | `https://api.biorxiv.org/pubs/biorxiv/10.64898/2026.07.06.736660` | 200 | no published version of this preprint exists yet |
| 1 | `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material` | 200 | page served, no data-bearing supplementary link |
| 1 | `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v2.supplementary-material` | 200 | page served, no data-bearing supplementary link |
| 1 | `https://www.biorxiv.org/content/10.64898/2026.07.06.736660.supplementary-material` | 200 | page served, no data-bearing supplementary link |
| 2 | `https://www.biorxiv.org/content/early/2026/07/07/2026.07.06.736660.source.xml` | 200 | 0 supplementary-material block(s), 20 href(s) |
| 3 | `n/a` | None | skipped: the bioRxiv API reports no published version, so there is no journal or PMC mirror to try |
| 4 | `https://zenodo.org/api/records?q=%22M-MLV%20reverse%20transcriptase%22%20AND%20%22prime%20editing%22&size=20` | 200 | 0 result(s), 0 plausibly relevant |
| 4 | `https://zenodo.org/api/records?q=%22saturated%20mutagenesis%22%20AND%20%22reverse%20transcriptase%22&size=20` | 200 | 0 result(s), 0 plausibly relevant |
| 4 | `https://datadryad.org/api/v2/search?q=M-MLV%20reverse%20transcriptase%20prime%20editing` | 200 | 0 result(s), 0 plausibly relevant |
| 4 | `https://api.osf.io/v2/nodes/?filter[title]=saturated%20mutagenesis%20reverse%20transcriptase` | 200 | 0 result(s), 0 plausibly relevant |
| 4 | `https://api.github.com/search/repositories?q=M-MLV%20reverse%20transcriptase%20prime%20editing%20mutagenesis` | 200 | 0 result(s), 0 plausibly relevant |
| 4 | `https://api.github.com/search/repositories?q=PE2%20reverse%20transcriptase%20saturation%20mutagenesis%20screen` | 200 | 0 result(s), 0 plausibly relevant |

## The remaining route is the corresponding author

`data_acquisition/AUTHOR_REQUEST.md` holds a drafted request, written at an
earlier gate and still accurate. Nothing has been sent; sending it is a human
action.

If the tables arrive privately, they go in `raw/` locally and `PROVENANCE.md`
records that they must not be committed, because a file shared privately by an
author carries whatever terms the author sets regardless of the preprint's CC
BY-NC licence. The repository would then keep the parser and the checksums only.

## What must not happen

There is no acceptable substitute for these labels. A simulated deep mutational
scan, values digitized from a figure, or a different protein's screen would each
make every downstream number meaningless while looking exactly like a result.
