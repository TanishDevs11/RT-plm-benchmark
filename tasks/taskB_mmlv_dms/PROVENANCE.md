# Provenance: M-MLV RT (PE2dR) saturated mutagenesis, within-protein variant effect

Task identifier: `B`
Directory: `tasks/taskB_mmlv_dms/`
Status: **BLOCKED AT ACQUISITION.** Re-attempted 2026-10-03 with four fresh routes,
including the publisher's own structured metadata, which declares no supplementary
material at all. The per-variant activity values are not publicly available anywhere, the
preprint is still at version 1, and no journal version exists.

What is ready and waiting: the task structure is confirmed verbatim against the preprint,
the 1046 expected variant identifiers are derived and frozen, and the split regimes are
written. What is missing is only the labels, and there is no acceptable substitute for
them.

## Sources

### B1, the preprint, obtained

| field | value |
| --- | --- |
| citation | Li H, Wang Y, Zhang C, Thi TT, Shi Y, Cheng KY, Hu C, Yu H. Saturated mutagenesis screen of M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency. bioRxiv, posted 2026-07-07 |
| DOI | `10.64898/2026.07.06.736660` |
| file as downloaded | `raw/preprint.pdf` |
| SHA256 | `5a13f7763987116c49f76c4aad9ce1aff6d78468a6b951b41cbbcc9609730cf3` |
| bytes | 3620781, 23 pages |
| source URL | `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.full.pdf` |
| access date | 2026-09-30 |
| licence | **CC-BY-NC 4.0 International**, read from the per-page banner in the PDF itself |
| redistribution | permitted with attribution for non-commercial use, so the file is committed to `raw/` |
| bioRxiv node id | 5608071 |

**Correction to the brief.** The brief cites this preprint as bioRxiv 2026.07.06.736660,
which reads as DOI prefix `10.1101`. The bioRxiv API returns no posts found for
`10.1101/2026.07.06.736660`. The preprint resolves under prefix `10.64898`. Every Task B
row will carry `10.64898/2026.07.06.736660`.

### What the preprint PDF contains, and what it does not

Contains: main text, Methods, references, Figures 1 to 4, and Supplementary Figures 1 to 4
on pages 20 to 23.

Does not contain: Table S5, Table S6, Table S7, or Supplementary Sequences 1 to 5. Those
are referenced in the text but are not in this file.

### B2, the supplementary material, NOT obtained

| field | value |
| --- | --- |
| what is needed | Supplementary Sequence 1 (the PE2dR construct) and Tables S6 and S7 (per-variant activity) |
| attempted | the article's supplementary-material page returns HTTP 200 but its static HTML contains no file listing, no `media-N` reference, and no occurrence of the word "supplement" in the rendered text |
| attempted | legacy bioRxiv adjunct paths `content/biorxiv/early/2026/07/07/.../DC1/embed/media-1.{pdf,xlsx}` return HTTP 404 |
| attempted | `highwire/filestream/5608071/field_highwire_adjunct_files/{0..4}/media-{1..5}.{pdf,xlsx,docx,zip}`, 20 combinations, all non-200 |
| attempted | the `.full-text` view returned HTTP 429, at which point probing stopped rather than continuing to hammer the host |
| attempted | Europe PMC, which systematically harvests preprint supplementary material, indexes the preprint as `PPR1272147` and reports `hasSuppl = N` and `isOpenAccess = N`; its `supplementaryFiles` endpoint returns HTTP 404 |
| attempted | the `.full-text` view, retried after the rate limit cleared, returns HTTP 200 and offers downloads for Supplementary Figures 1 to 4 only, which are already pages 20 to 23 of the main PDF; it offers no table and no sequence file |
| outcome | **not publicly deposited.** Four independent routes agree: the supplementary-material page lists nothing, the full-text page offers only the four supplementary figures, Europe PMC reports no supplementary material, and every legacy adjunct path returns 404. Tables S1 to S7 and Supplementary Sequences 1 to 5 are referenced by the preprint but were not deposited with version 1 |
| only remaining route | the corresponding author, or a later version of the preprint, or the peer-reviewed publication when it appears |
| note | the preprint has no Data Availability and no Code Availability statement; the strings "availability", "Data availability", and "Data Availability" do not appear anywhere in the PDF |

### B2 revisited, 2026-10-03: re-attempted with four fresh routes, still not obtainable

`data_acquisition/fetch_mmlv_dms.py` re-attempted acquisition with the routes the Task B
brief specifies, three of which had not been tried before. Full log in
`data_acquisition/fetch_mmlv_dms_attempts.json`.

| route | what was tried | outcome |
| --- | --- | --- |
| bioRxiv API, details | `api.biorxiv.org/details/biorxiv/10.64898/2026.07.06.736660` | HTTP 200. **Still version 1**, posted 2026-07-07, licence `cc_by_nc`. No later version exists |
| bioRxiv API, published version | `api.biorxiv.org/pubs/biorxiv/...` | HTTP 200, "no articles found for published version". **The work has not been published in a journal**, so the brief's routes 3 and 4 against a journal or PMC mirror have no target |
| supplementary-material page, v1, v2 and current | three URLs | all HTTP 200, **no data-bearing supplementary link on any of them**. The v2 URL returns generic bioRxiv site chrome with no article content, confirming v2 does not exist |
| JATS XML, the publisher's own structured record | `biorxiv.org/content/early/2026/07/07/2026.07.06.736660.source.xml` | HTTP 200, 77870 bytes, **zero `supplementary-material` blocks**. This is the strongest single piece of evidence: the publisher's structured metadata declares no supplementary material at all |
| Zenodo | two queries, by enzyme and by assay | 0 results |
| Dryad | one query | 0 results |
| OSF | one query by title | 0 results |
| GitHub repositories | two queries | 0 results |

Conclusion unchanged and now better evidenced: **the per-variant activity values are not
publicly available anywhere.** Task B remains blocked at acquisition.

One defect in the fetcher, found and fixed during this attempt. Its first version matched
`.txt` as a data-bearing extension, which made route 1 "succeed" by downloading bioRxiv's
own full-text HTML page and storing it as a variant table. That is the same silent
substitution the Task A fetcher had. `looks_like_data` now rejects any payload served as
HTML or beginning with an HTML document, and requires either a zip or OLE container
signature or at least ten delimiters in the first 4 KiB. The guard runs at every
acceptance point and again before anything is written to `raw/`.

### What the preprint PDF does establish, read directly from it

The PDF cannot supply the labels, but it does confirm the task's structure exactly, and
these quotations are what the frozen splits are built on.

| fact | evidence, verbatim from `raw/preprint.pdf` |
| --- | --- |
| the construct | "we developed a compact prime editor, PE2dR, by deleting the RNase H domain of the MMLV reverse transcriptase (MMLV-RT)" |
| the two stretches | "specific regions within the fingers domain- S60-Q84 and N95-D124- have been shown to directly interacts with the DNA template" |
| the library sizes | "These libraries encoded all possible single-amino acid substitutions for the S60-Q84 and N95-D124 regions within the fingers domain, respectively, totalling 475 and 570 variants" |
| the library sizes again, with wild types | "producing Library Stretch 1 (475 variants + WT) and Library Stretch 2 (570 variants + WT)" |
| the label, before scaling | "log2((abundance of variant in GFP positive cells)/(abundance of variant in GFP negative cells)) was calculated for each variant and for the wild-type" |
| the label, after scaling | "of all variants were then normalized and scaled between -1 to 1, with the wild-type sequence set as the baseline (effect=0)" |
| the validated hits | the triple mutant is "PE2dR-I61R, V101R, S67W", referred to as PE2dRM3 |

The arithmetic closes exactly: S60 to Q84 is 25 positions, N95 to D124 is 30, and 19
non-wild-type substitutions per position gives 25 times 19 equals 475 and 30 times 19
equals 570. So the brief's expected counts and the frozen split files agree with the
primary source without any assumption.

### Three questions the PDF leaves open

1. **The construct's substitution content.** The strings `D200N`, `T306K`, `W313F`,
   `T330P`, `L603W` and `pentamutant` appear **nowhere** in the PDF. The name PE2dR
   implies a PE2 lineage, which conventionally carries that pentamutant, but the paper
   describes the construct as deleting the RNase H domain of MMLV-RT without naming any
   point substitution. So whether the parent RT is wild-type MMLV-RT truncated, or the
   PE2 pentamutant truncated, is undetermined from the public record. Four positions of
   difference across a 498-residue reference would silently corrupt every one of the 1045
   variant sequences, which is why this is handled as a halt condition rather than a
   guess.
2. **Whether the scaling to the interval from -1 to 1 was computed within each library or
   across both.** The Methods sentence does not say. This decides whether the headline
   stretch-held-out result also crosses two normalizations, and it has to be stated when
   that result is reported.
3. **Whether there is one wild-type row or two.** The figure legend reads "475 variants +
   WT" and "570 variants + WT", which admits two wild-type measurements, one per library.
   The frozen split files carry a single `B_wt` row, giving 1046 identifiers. If the
   tables arrive with a wild-type row per library the count is 1047 and the splits need
   one row added. Recorded so the discrepancy is noticed rather than absorbed.

### B3, UniProt, obtained

| field | value |
| --- | --- |
| accession plus version | `P03355` sequence version 5, `SV=5` |
| entry | `sp|P03355|POL_MLVMS` Gag-Pol polyprotein, Moloney murine leukemia virus, isolate Shinnick |
| file as downloaded | `raw/uniprot_P03355.fasta` |
| SHA256 | `418f1e426db315802f83b2653c6caf47cf2e78d438bee5f8be8f8cbc62ba2729` |
| source URL | `https://rest.uniprot.org/uniprotkb/P03355.fasta` |
| access date | 2026-09-30 |
| total length | 1738 residues |
| relevant annotation | CHAIN "Reverse transcriptase/ribonuclease H (p80)" at Gag-Pol 660 to 1330, so 671 residues |
| licence | CC-BY 4.0, UniProt terms of use; redistribution permitted |

## The numbering resolution

This was the pipeline's stated worst failure mode, and it is settled. Reproduce with:

    python data_acquisition/resolve_mmlv_reference.py

**The conflict.** The preprint deletes RNase H at "residues L499 to P677", implying a
677-residue RT. The annotated p80 chain is 671 residues. Six residues of offset would
silently displace every variant in both libraries.

**The test.** Nine anchors, being every residue identity the preprint states, checked
against P03355 under the hypothesis that the preprint's RT residue 1 is p80 residue 1, so
the Gag-Pol offset is 659.

| RT position | required | observed | source of the requirement |
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

All nine match. Nine of nine.

**A second, independent confirmation.** The preprint states two quantities that the
anchors say nothing about: the retained RT is "encoded by 1,494bp" and is "26.4% smaller
than the wild-type MMLV-RT". Under the resolved frame, retained residues 1 to 498 give
498 times 3, so 1494 base pairs, matching exactly; and the deleted 179 residues out of 677
give 0.2644, which rounds to the stated 26.4 percent. Two numbers derived from a different
part of the frame than the anchors, both agreeing.

**The resolution of 671 against 677.** Both are correct, about different things. The
preprint's RT extends 6 residues past the annotated p80 chain, to Gag-Pol 1336, into the
region UniProt assigns to integrase. Residues 672 to 677 in RT numbering are `IENSSP`,
ending in the P the preprint calls P677. There is no offset and no numbering error in
either source.

**Adopted frame.**

| quantity | value |
| --- | --- |
| reference accession plus version | `P03355.5` (`SV=5`) |
| RT frame | Gag-Pol 660 to 1336, so RT residues 1 to 677 |
| Gag-Pol offset | 659; RT position n is Gag-Pol position n plus 659 |
| RNase H deleted | RT 499 to 677, 179 residues |
| PE2dR RT retained | RT 1 to 498, so Gag-Pol 660 to 1157, 498 residues, 1494 base pairs |
| diversified stretch 1 | RT 60 to 84, 25 positions, `SIKQYPMSQEARLGIKPHIQRLLDQ` |
| diversified stretch 2 | RT 95 to 124, 30 positions, `NTPLLPVKKPGTNDYRPVQDLREVNKRVED` |

## The one open question on the reference

PE2dR was built from pCMV-PE2, Addgene 132775: "The pCMV-PE2ΔR plasmid was constructed via
deleting RNaseH domain from RT of pCMV-PE2 (#132775, Addgene)". PE2's RT carries the
substitutions D200N, T306K, W313F, T330P, and L603W. All five wild-type residues were
checked against the resolved frame and all five match, so the substitution set is
consistent with this frame.

L603 falls inside the deleted 499 to 677 region. So if PE2dR inherits PE2's RT, the
reference is a **tetramutant truncation** carrying D200N, T306K, W313F, and T330P, and not
L603W.

That is a derivation, not a reading. The preprint's main text never states the construct's
substitution content: the strings "pentamutant", "D200N", and "L603W" do not appear
anywhere in the PDF. So the substitution content is **UNRESOLVED**, and it must come from
Supplementary Sequence 1.

Addgene was tried as a fallback. `https://www.addgene.org/132775/sequences/` returns HTTP
200 but embeds no sequence in its static HTML, and the GenBank file derived from the map
image path returned HTTP 404. Probing stopped there. If needed, a human can download the
full sequence from that page.

## What is in `raw/`

| file | bytes | SHA256 | what it is |
| --- | --- | --- | --- |
| `preprint.pdf` | 3620781 | `5a13f776...730cf3` | the source publication, CC-BY-NC 4.0 |
| `uniprot_P03355.fasta` | 1891 | `418f1e42...ba2729` | the Gag-Pol parent, `SV=5` |
| `reference_candidate_unconfirmed.fasta` | 619 | `61fdd347...5c050c` | RT 1 to 498 with **no substitutions applied** |

`reference_candidate_unconfirmed.fasta` is deliberately not named `reference.fasta`. No
parser may consume it. It records the resolved frame so the work is not lost, and it is
unusable as a reference until the substitution content is settled, because a reference
wrong at four positions would be wrong at four positions in all 1046 rows.

## Label definition, verbatim from `raw/preprint.pdf`

"log2((abundance of variant in GFP positive cells)/(abundance of variant in GFP negative
cells)) was calculated for each variant and for the wild-type construct. The editing
efficiency of all variants were then normalized and scaled between -1 to 1, with the
wild-type sequence set as the baseline (effect=0)."

`label_units` is `normalized_-1_1`. `label_assay` is
`prime_editing_normalized_wt_centred`.

**Refinement to the assay description.** The screen is not at endogenous loci. It uses an
isogenic HEK293T eGFP reporter line carrying two premature TAG stop codons, edited
TAGTAG to GAGGAG, with variants sorted on eGFP and scored by enrichment in the eGFP
positive population against the eGFP negative population. This differs from the Task A
assay in more than normalization, which is a further reason the two tasks are never pooled.

Open: whether the scaling to the interval was computed within each library or across both.
This is why `library_stretch` is a required column and why the stretch-held-out split is
the honest Task B test: if the libraries were scaled separately, then training on one and
testing on the other also crosses two normalizations, and that must be said when the result
is reported.

## Expected row count, with an arithmetic check that passes

Verbatim: "two lentivirus-based PE2ΔR libraries L1 and L2 (Table S5). These libraries
encoded all possible single-amino acid substitutions for the S60-Q84 and N95-D124 regions
within the fingers domain, respectively, totalling 475 and 570 variants".

Verbatim: "Among all 1045 variants screened, sequencing analysis revealed that 176 variants
show increased editing efficiency compared to parental RT".

Check: stretch 1 is 25 positions, and 25 times 19 non-wild-type substitutions is 475.
Stretch 2 is 30 positions, and 30 times 19 is 570. Both libraries are exactly saturating,
and 475 plus 570 is the 1045 the paper states. So the expected table is 1045 variant rows
plus one wild-type row, with no substitution missing, and any parsed table shorter than
that has dropped variants which must be logged individually rather than accepted.

The wild type appears once. Each library carries its own wild-type construct, but both are
fixed at zero by the definition of the normalization, so they are not two independent
measurements. Two wild-type rows would also carry an identical sequence, which the schema
rejects as a duplicate. The single wild-type row records both libraries in
`library_stretch` and keeps any per-library raw values in `notes`.

## Reconciliation

Not yet run. No `curated.csv` exists. The parser cannot run until Tables S6 and S7 are
obtained and Supplementary Sequence 1 settles the substitution content.

## Open questions

1. **Blocking.** Supplementary Sequence 1, for the substitution content of PE2dR.
2. **Blocking.** Tables S6 and S7, for the per-variant activity values, and which table is
   which library.
3. Whether the normalization to the interval was per library or across both.
4. Whether any variant was dropped at a read-count filter, and what the threshold was. The
   Methods describe a 30-nt indel analysis window but state no read-depth filter, and 1045
   is the full saturating count, which suggests none were dropped.
