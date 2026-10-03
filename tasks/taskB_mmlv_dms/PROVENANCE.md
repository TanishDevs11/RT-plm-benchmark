# Provenance: M-MLV RT (PE2dR) saturated mutagenesis, within-protein variant effect

Task identifier: `B`
Directory: `tasks/taskB_mmlv_dms/`
Status: **BLOCKED ON LABELS ONLY.** Two things were missing. One of them no longer is.

The reference is resolved. It was the item the brief calls the single highest-risk item in
the whole pipeline, and it was resolved on 2026-10-03 from the parent plasmid rather than
from the supplementary sequence the preprint never deposited. It is confirmed against a
second, independently deposited plasmid. See "The reference, resolved from the parent
plasmid" below. The finding there is not a formality: the obvious way of building this
reference gives a sequence that is wrong at one position, satisfies every residue identity
the preprint states, and would have corrupted all 1046 variant sequences silently.

The labels are still missing. Re-attempted 2026-10-03 across six routes, now including
four literature indexes and the three NCBI sequence archives. The per-variant activity
values are not publicly available anywhere, the preprint is still at version 1, and no
journal version exists.

What is ready and waiting: the reference, the 1046 expected variant identifiers, the
frozen split regimes, and a parser that provably halts on a wrong reference. What is
missing is only the labels, and there is no acceptable substitute for them.

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

### B2 revisited a second time, 2026-10-03: two route families the brief does not list

The brief's route 3, a journal or PMC mirror, is conditional on the work having been
published, and the first attempt took the bioRxiv API's single "NA" as that answer. One
API is a single point of failure for a route that would otherwise open the supplement, so
`fetch_mmlv_dms.py` gained two further route families. Full log in
`data_acquisition/fetch_mmlv_dms_attempts.json`, 30 attempts across six routes.

| route | what was asked | outcome |
| --- | --- | --- |
| 5, Crossref by title | does any indexed record other than the preprint match this title | 5 records returned, 1 of them this work, typed `posted-content` |
| 5, Crossref by DOI | does the preprint's own record carry a relation to a journal article | HTTP 200, `relation` is **empty**. Crossref knows of no journal version |
| 5, OpenAlex | how many locations does this work have | 1 location, typed `preprint`. A published version would appear as a second location |
| 5, Semantic Scholar | the same question again | HTTP 429 in the scripted run, and again on its one retry. A single manual query in the same session returned exactly one record, the bioRxiv preprint, with no journal venue. Recorded as rate limited rather than as an answer |
| 5, Europe PMC by title | supplementary and open-access flags | 1 record, `PPR1272147`, `hasSuppl=N`, `isOpenAccess=N` |
| 6, NCBI BioProject | is the screen deposited as a project, under four query forms | 0 records for all four |
| 6, NCBI GEO DataSets | the same four queries | 0 for three; 3 unrelated records for the broadest query, none of which is this work |
| 6, NCBI SRA | the same four queries | 0 records for all four |

Four independent indexes now agree that no journal version exists, so the brief's route 3
has no target and this is not one API's opinion. The sequence archives hold nothing
either, which is worth recording: a read-level deposit would not have supplied the
published labels, since those are normalized and scaled, but it would have been a real
route to the underlying counts. It does not exist.

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

1. **The construct's substitution content. ANSWERED, from outside the PDF.** The strings
   `D200N`, `T306K`, `W313F`, `T330P`, `L603W` and `pentamutant` appear **nowhere** in the
   PDF, so this could not be settled from the preprint and was a halt condition rather
   than a guess. It was settled instead from the parent plasmid, and the answer is not
   the one the obvious reasoning gives. See "The reference, resolved from the parent
   plasmid" below.
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

## The reference, resolved from the parent plasmid

Reproduce with:

    python data_acquisition/fetch_pe2_plasmid.py
    python data_acquisition/resolve_pe2dr_reference.py

**What made this resolvable.** The preprint states how the construct was made: "The
pCMV-PE2ΔR plasmid was constructed via deleting RNaseH domain from RT of pCMV-PE2
(#132775, Addgene)". That names a public record, so the construct's RT is a sequence to be
read rather than a substitution set to be reasoned about.

**The route.** Addgene publishes one Addgene-verified full sequence for 132775, sequence
259720. Its GenBank file is referenced by the page's own sequence viewer and returns HTTP
404, which is where the earlier attempt stopped. The viewer's `sequence-lines.json` is
served, and it carries both strands as text glyphs with explicit base-pair coordinates.
The 9753 bp were reconstructed from it under four assertions, any one of which halts the
fetch: each line's recovered base count must equal its declared `data-begin-bp` to
`data-end-bp` span, the two strands of each line must be exact complements, the lines must
tile the plasmid with no gap and no overlap from bp 0, and exactly one candidate strand
pair per line may satisfy the first two. This is machine-readable text from the
depositor's own record, not a figure: no base is inferred anywhere.

**The RT was located, not assumed.** All six reading frames were translated and every
window of 677 residues scored against P03355 RT. The best is the forward strand, frame 0,
nucleotide 4915, at 6 differences out of 677; the next best frame is far away. The RT is
also bounded on both sides: it is preceded by `PESSGGSSGGSS`, the prime editor's linker,
and residues 672 to 677 read `IENSSP`, ending in the P the preprint calls P677.

**The six differences from UniProt P03355, each accounted for.**

| RT position | P03355 | plasmid | accounted for by |
| --- | --- | --- | --- |
| 8 | H | Y | **nothing in the published record.** Named by neither the preprint nor Addgene |
| 200 | D | N | Addgene 132775, insert `Cas9(H840A)-M-MLVrt(D200N, T306K, W313F, T330P, L603W)` |
| 306 | T | K | the same record |
| 313 | W | F | the same record |
| 330 | T | P | the same record |
| 603 | L | W | the same record, and inside the deleted region |

**Why position 8 is the finding and not a footnote.** The obvious way to build this
reference is to take UniProt P03355, apply the PE2 substitutions that the literature
documents, and truncate at 498. That sequence passes every check the preprint makes
available: all seven residue identities the paper states, both deletion boundaries, both
stretch sequences, and the 1494 base pair and 26.4 percent arithmetic. It is also wrong at
position 8, and it would have been wrong at position 8 in all 1046 variant sequences and
in every embedding computed from them, with nothing raising anywhere. The file that
sequence lives in, `raw/reference_candidate_unconfirmed.fasta`, is kept for exactly this
reason: `test_parse_mmlv_dms.py` feeds it to the parser and requires rejection.

The parser now asserts construct identity as well as position numbering, at positions 8,
200, 306, 313 and 330, plus the reference length. Twelve assertions, all passing.

**The independent confirmation.** Everything above comes from one deposited payload, so a
flaw in that payload, or in how it is read, would survive all of it. pCMV-PEmax, Addgene
174820, is a separate deposit, and it is also the parent of the paper's best construct,
PEmaxΔRM3. It encodes this reference **exactly, 498 of 498 residues**, while the two RT
open reading frames share only 1206 of 1494 nucleotides, 0.807. The two records are
differently codon-optimized, so protein-level agreement cannot come from one payload or
one rendering of it. Position 8 is Y in both.

**Stop gate G1: confirmed.** Presented 2026-10-03 and endorsed by the repository owner
on the same day: the reference resolution, the numbering outcome, 12 of 12 residue
assertions passing, and the variant count reconciling at 475 and 570 against the
preprint's stated counts.

The ruling was to confirm the reference and **stop there**, rather than to go on and build
the Phase 4 representations that need no labels. That is a deliberate decision and the
reasoning is worth keeping: a zero-shot score or an embedding with no labels to correlate
against is a column of numbers rather than a result, and computing one would look like
progress without being any. Nothing in Phase 4 has been run. The task is prepared and
blocked on Tables S6 and S7, and on nothing else.

**Adopted reference.**

| quantity | value |
| --- | --- |
| file | `tasks/taskB_mmlv_dms/reference.fasta` |
| SHA256 | `070b5df7e3d6248f9dbd4213060f2d2cab9691a450a50e0de1281930f8f33cd7` |
| length | 498 residues, 1494 base pairs |
| read from | Addgene 132775 verified full sequence 259720, translated RT 1 to 498 |
| cross-checked against | Addgene 174820, 498 of 498 residues |
| frame cross-checked against | `P03355.5`, Gag-Pol 660 to 1157 |
| substitutions relative to P03355 RT | H8Y, D200N, T306K, W313F, T330P |
| not carried, being inside the deletion | L603W |
| machine-readable record | `tasks/taskB_mmlv_dms/reference_resolution.json` |

Supplementary Sequence 1 would still be worth having as a direct statement of the
construct. It is now a check on a settled answer rather than a blocker.

## What is in `raw/`

Checksums for every file, with sources, are in `raw/CHECKSUMS.txt`, rewritten over the
whole directory by `fetch_pe2_plasmid.py` rather than appended to.

| file | bytes | SHA256 | what it is |
| --- | --- | --- | --- |
| `preprint.pdf` | 3620781 | `5a13f776...730cf3` | the source publication, CC-BY-NC 4.0 |
| `uniprot_P03355.fasta` | 1891 | `418f1e42...ba2729` | the Gag-Pol parent, `SV=5` |
| `addgene_132775_pCMV-PE2.fasta` | 10213 | `ce5398da...13cc32` | the parent plasmid, 9753 bp, the record the reference is read from |
| `reference_candidate_unconfirmed.fasta` | 619 | `61fdd347...5c050c` | RT 1 to 498 with **no substitutions applied**, superseded |

`reference_candidate_unconfirmed.fasta` is still deliberately not named `reference.fasta`,
and no parser may consume it. It now has a second job: it is the near miss the test suite
uses. It satisfies every residue identity the preprint states and is wrong at five
positions, so `test_the_unmutated_uniprot_frame_is_rejected` feeds it to the parser and
requires a halt. Deleting it would delete that test.

The adopted reference lives at `tasks/taskB_mmlv_dms/reference.fasta`, one level up,
because it is a derived artifact of the pipeline rather than a file as served.

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

Not yet run. No `curated.csv` exists, because it cannot: there are no labels to put in it.
The reference half of the parser does run, and does pass:

    python data_acquisition/parse_mmlv_dms.py --check-reference

12 residue assertions pass against the adopted reference, and the saturating library sizes
derive exactly, 475 for stretch 1 and 570 for stretch 2, against the preprint's stated
counts. What is left is the labels.

## Open questions

1. **Blocking, and the only blocker.** Tables S6 and S7, for the per-variant activity
   values, and which table is which library.
2. Whether the normalization to the interval was per library or across both.
3. Whether any variant was dropped at a read-count filter, and what the threshold was. The
   Methods describe a 30-nt indel analysis window but state no read-depth filter, and 1045
   is the full saturating count, which suggests none were dropped.
4. Whether `H8Y` is deliberate in the prime editor lineage or an incidental property of
   the M-MLV RT clone it was built from. It does not matter for this task: the reference is
   whatever the construct carries, and two independent deposits agree on what that is.
   Position 8 is also outside both diversified stretches, so it changes no variant's
   identity, only the background all of them sit on. Recorded because it is a real
   difference from the canonical viral sequence and someone will ask.

Resolved since the last revision of this file: the substitution content of PE2dR, which
was open question 1 and is now settled from Addgene 132775 and confirmed against 174820.
