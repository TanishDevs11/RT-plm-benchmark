// Technical report source. Compile with: python reports/build_pdf.py
// Every number is imported from _report_data.typ, which build_pdf.py generates
// from the repository's result files. Nothing numeric is typed into this file.

#import "_report_data.typ": *

#let SHORTTITLE = "PLMs for Enzyme Function Prediction: Lessons from Reverse Transcriptases"

#set document(
  title: "Protein Language Models for Enzyme Function Prediction: Lessons from Reverse Transcriptases",
  author: "Tanish N",
)

#set page(paper: "a4", margin: (x: 2.4cm, y: 2.6cm), numbering: none, header: none)
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.68em, spacing: 1.0em)
#set heading(numbering: "1.1")
#show raw: set text(font: "DejaVu Sans Mono", size: 8.5pt)
#show link: set text(fill: rgb(20, 50, 110))
#show heading: set text(hyphenate: false)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(above: 1.4em, below: 0.9em, text(size: 15pt, weight: "bold", it))
}
#show heading.where(level: 2): it => block(above: 1.3em, below: 0.6em, text(size: 11.5pt, weight: "bold", it))
#show heading.where(level: 3): it => block(above: 1.1em, below: 0.5em, text(size: 10.5pt, weight: "bold", style: "italic", it))

#set figure(gap: 0.9em)
#show figure.caption: set text(size: 9pt)
#show figure.where(kind: table): set figure.caption(position: top)
#show figure.where(kind: table): set block(breakable: true)

// ---------------------------------------------------------------- helpers

#let btab(cols, head, rows, aligns: auto, size: 8.6pt) = {
  set text(size: size)
  set par(justify: false, leading: 0.52em)
  table(
    columns: cols,
    align: if aligns == auto { left } else { aligns },
    stroke: none,
    inset: (x: 4.5pt, y: 3.6pt),
    table.hline(stroke: 0.9pt),
    table.header(..head.map(h => strong(h))),
    table.hline(stroke: 0.45pt),
    ..rows.flatten(),
    table.hline(stroke: 0.9pt),
  )
}

// Mark "yes" so it reads in grayscale without relying on colour.
#let mk(s) = if s == "yes" { strong("yes") } else { s }
#let btab_mark(cols, head, rows, aligns: auto, size: 8.6pt) = {
  set text(size: size)
  set par(justify: false, leading: 0.52em)
  table(
    columns: cols,
    align: if aligns == auto { left } else { aligns },
    stroke: none,
    inset: (x: 4.5pt, y: 3.6pt),
    table.hline(stroke: 0.9pt),
    table.header(..head.map(h => strong(h))),
    table.hline(stroke: 0.45pt),
    ..rows.map(r => r.enumerate().map(((i, c)) => if i == r.len() - 1 { mk(c) } else { c })).flatten(),
    table.hline(stroke: 0.9pt),
  )
}

#let sha(s) = {
  // A SHA256 digest is a single unbreakable token; split it so a table cell can wrap it.
  set text(size: 7.4pt)
  raw(s.slice(0, 32))
  linebreak()
  raw(s.slice(32))
}

#let notebox(body) = block(
  width: 100%,
  inset: 9pt,
  radius: 2pt,
  stroke: 0.6pt + luma(45%),
  fill: luma(96%),
  body,
)

#let correction(date, body) = block(
  width: 100%,
  inset: 9pt,
  radius: 2pt,
  stroke: (left: 2pt + luma(25%), rest: 0.5pt + luma(65%)),
  fill: luma(97%),
  [#text(weight: "bold", size: 9.5pt)[Correction, #date.] #text(size: 9.5pt)[#body]],
)

// ================================================================ title page

#v(1.2fr)

#[
#set par(justify: false)
#align(center)[
  #text(size: 20pt, weight: "bold", hyphenate: false)[
    Protein Language Models for     Enzyme Function Prediction
  ]
  #v(0.3em)
  #text(size: 15pt, weight: "medium", style: "italic")[
    Lessons from Reverse Transcriptases
  ]

  #v(2.2em)
  #text(size: 12.5pt)[Tanish N]

  #v(0.5em)
  #text(size: 10pt)[
    B.Sc. Biotechnology (Final Year) \
    Indira Gandhi College of Arts and Science, Puducherry, India
  ]

  #v(0.9em)
  #text(size: 9.5pt)[
    #link("mailto:tanishpatrick@gmail.com")[tanishpatrick\@gmail.com] #h(0.6em) | #h(0.6em)
    #link("https://github.com/TanishDevs11")[github.com/TanishDevs11]
  ]

  #v(1.6em)
  #text(size: 11pt)[November 2026]

  #v(0.8em)
  #text(size: 9.5pt)[
    Repository: #link("https://github.com/TanishDevs11/RT-plm-benchmark")[github.com/TanishDevs11/RT-plm-benchmark] \
    Licence: MIT (`LICENSE`), Copyright (c) 2026 TanishDevs11. \
    Source data: Doman et al., _Cell_ 2023, under CC BY 4.0.
  ]
]
]

#v(2.0em)

#align(center)[
  #block(width: 86%)[
    #notebox[
      #text(size: 9.5pt)[
        *Status.* This is an independent rebuild and correction of a prior competition
        submission by the same author, not a new result on a new dataset. \
        Its headline finding is negative, and the previously reported composite score of
        #num.sub_cls is retracted as a measurement in #link(<postmortem>)[section 6]. \
        Where this document corrects an earlier version of its own claims, the correction
        is printed in place and dated rather than silently applied.
      ]
    ]
  ]
]

#v(1.4fr)

#pagebreak()

// ================================================================ abstract

#set page(numbering: "i")
#counter(page).update(1)

#align(center)[#text(size: 14pt, weight: "bold")[Abstract]]
#v(0.6em)

#block(inset: (x: 0.6cm))[
Protein language models are used as general-purpose protein representations, and they
perform well on within-protein variant effect prediction. Whether they transfer to
cross-family functional prediction, where a model must generalise to an evolutionary
lineage it has not seen labelled, is a separate question. We tested it on #num.n_enzymes
reverse transcriptases assayed as prime editors across #num.n_families families, of which
#num.n_active show detectable activity, and the answer on this panel is no.

The methodological contribution comes first, because it is what survives the sample size.
We define and use a *search-capacity null*: given a selection procedure with $K$ free
parameters and a search budget, run that procedure unchanged on $K$ vectors of pure noise
and record the score it reaches. On this panel and this composite metric, a five-parameter
search already reaches #num.k5_p95 on noise and a 29-parameter search reaches #num.k29_p95, and
the capacity curve does not saturate over the range tested. A score printed without its
null has reported nothing. Separately, a dimensionality-matched Gaussian noise control
proves insufficient on its own: it passes two ESM-2 scales that a label permutation then
rejects.

The negative result is that mean-pooled embeddings on this panel encode lineage and length
rather than catalysis. Under the composite metric no representation clears its own
search-capacity null, and no trained model beats using sequence length as the score with no
training at all. Under precision-recall area on the reproducible binary label, exactly one
of twelve representations survives a noise control, chance, and label permutation together,
and it is a 4-mer frequency block whose signal is diffuse across #num.kmer4_feats features and
associated with length at Spearman #num.kmer4_len_rho. The same ESM-2 650M representation
classifies reverse transcriptase family at #num.fam_diag against a #num.fam_major majority
baseline, with its leading principal component tracking length at Spearman #num.pc1_len.
Length residualization, family residualization and two catalytic-core pooling variants all
failed to repair this, and the two core-targeted variants produced the highest lineage
accuracy of any representation measured.

Two explanations remain live and this dataset does not separate them: that the
representations carry little transferable functional signal, and that a panel with a Kish
effective sample size of #num.kish and a minimum resolvable composite difference of #num.mrd_cls
cannot detect what they carry. Nearly every ordering reported here is therefore provisional,
and is marked as such.
]

#v(1.2em)
#block(inset: (x: 0.6cm))[
#text(size: 9.5pt)[
*Keywords:* protein language models; reverse transcriptase; prime editing; small-sample
inference; search-capacity null; data leakage; benchmark design.
]
]

#pagebreak()

#outline(title: [Contents], depth: 2, indent: 1.2em)

#pagebreak()

// ================================================================ body

#set page(
  numbering: "1",
  header: context {
    set text(size: 8pt, fill: luma(40%))
    grid(
      columns: (1fr, auto),
      align: (left, right),
      SHORTTITLE, [Tanish N],
    )
    v(-0.6em)
    line(length: 100%, stroke: 0.4pt + luma(70%))
  },
)
#counter(page).update(1)

= Introduction

Prime editing installs a programmed sequence change by fusing a Cas9 nickase to a reverse
transcriptase (RT), which copies an edit encoded in an extended guide RNA into the nicked
target. The RT is therefore not an accessory: it sets both the size of the editor, which
governs whether the construct fits a delivery vehicle, and its efficiency. Choosing an RT
well is a design decision made once per editor and inherited by everything downstream, so a
predictor that could rank candidate RTs before they are cloned and assayed would be
genuinely useful.

Doman et al. @doman2023 made that question concrete by surveying RTs of diverse phylogenetic
origin as prime editors in HEK293T cells. Their Supplementary Table S1 lists #num.n_enzymes
assayed enzymes across #num.n_families families, of which #num.n_active show detectable prime
editing activity. The panel is the natural testbed for the question this report asks:

#block(inset: (x: 0.8cm))[
  *Do protein language model representations transfer to cross-family reverse transcriptase
  function prediction?* That is, can a representation trained on unlabelled sequence predict
  whether an RT works as a prime editor in an evolutionary lineage for which it has seen no
  activity labels?
]

The answer found here is no, on this panel, and the report is organised so that the reason
is auditable rather than asserted. There are two contributions, and the first matters more
than the second.

*The search-capacity null, proposed as routine practice for small-$n$ protein benchmarks.*
A benchmark score is produced by a procedure that makes choices: which head, which
hyperparameter, which preprocessing, which blend. Each choice is a free parameter fitted
against something. If the thing it is fitted against is the same label the score is reported
on, the score is partly manufactured, and at #num.n_enzymes rows it can be manufactured almost
entirely. The search-capacity null measures that directly: run the selection procedure,
unchanged, on $K$ vectors of pure noise and record the score it reaches
(#link(<null>)[section 4]). On this panel a 29-parameter search reaches #num.k29_p95 on noise.
That number is not a curiosity; it is the bar that the author's own prior submission had to
clear and did not convincingly clear (#link(<postmortem>)[section 6]).

*A demonstration that mean-pooled embeddings encode lineage and length rather than catalysis
on this panel.* The same ESM-2 650M embedding that fails to predict activity out of family
classifies evolutionary family at #num.fam_diag against a #num.fam_major majority baseline, and
its leading principal component tracks sequence length at Spearman #num.pc1_len. Both
measurements are made without any activity label. Four attempts to remove the confound,
including two that pool only over the catalytic core, left the composite score at zero and
made the representation *more* lineage-predictive, not less
(#link(<failed>)[section 5.6]).

A third thing this report does is retract a number. The author previously reported a
composite score of #num.sub_cls on this panel. #link(<postmortem>)[Section 6] sets out, in the
first person, why that is not a measurement. The repository's entire subject is a corrected
overclaim, so this document is written to err toward understatement; where a claim would
exceed what the interval, the null and the sample size support, the claim is cut rather than
hedged.

#notebox[
*A note on the two analyses in this report.* The repository contains two evaluations of the
same representation panel, built at different times with different primary metrics and
different fold rules. They are reported separately throughout, in
#link(<clsresults>)[section 5.2] and #link(<prresults>)[section 5.3], and
#link(<two>)[section 5.7] states plainly what differs between them. No table or comparative
sentence in this report places a composite-metric value beside a precision-recall value from
the other analysis, because they are not commensurable.
]

= Dataset <dataset>

== Source and licence

#figure(
  caption: [Provenance of the Task A panel. The workbook and the full text were both
  retrieved programmatically and are committed with checksums.],
  btab(
    (auto, 1fr),
    ([field], [value]),
    (
      ([citation], [Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. _Cell_ 2023;186(18):3983--4002.e26]),
      ([DOI], raw(num.doi)),
      ([PMC accession], raw(num.pmc)),
      ([licence], [CC BY 4.0, confirmed from the article's own licence statement]),
      ([supplementary file], [Table S1, `mmc2.xlsx` #sha(num.workbook_sha)]),
      ([curated dataset], [`tasks/taskA_crossfamily/curated.csv` #sha(num.curated_sha)]),
      ([enzymes / active / families], [#num.n_enzymes / #num.n_active / #num.n_families]),
    ),
  ),
) <tab:provenance>

Table S1 is a single sheet holding two caption-delimited FASTA blocks under one running
index. The first block, rows 6 to 118, holds the #num.n_enzymes assayed enzymes. The second
block's #num.block2 entries are UniProt BLAST hits used only for the paper's phylogenetic
analysis; they were never assayed and are excluded from the benchmark entirely.

*Activity is encoded as a green cell fill, not as a column.* Any reader or script that
parses cell values alone sees no labels at all. The #num.n_active enzymes carrying the fill are
exactly the #num.n_active marked active in the inherited dataset this work rebuilds, and the
parser asserts the block captions, the entry count, the fill count and the index range before
reading a single data row, halting rather than adapting if the source changes.

All #num.n_enzymes inherited sequences are byte-identical by SHA256 to Table S1, and the
inherited length column agrees with `len(sequence)` on every row. This check had never been
run on this dataset. It is the one inherited claim this work strengthens rather than
qualifies: whatever else is unverifiable here, the sequences are exactly the paper's.

== The label provenance caveat, in full <labels>

The binary activity label is read directly from the fill and is reproducible from the source
file. The continuous efficiency label is not, and this is the most consequential finding of
the dataset work.

*Table S1 contains no numeric cell except the row index.* All six supplementary workbooks
were scanned and none carries the per-enzyme survey efficiencies, so the inherited
`pe_efficiency_pct` column cannot be checked against the published supplementary material at
all. What it can be attributed to, and how confidently:

- *Which panel.* Figure S1A is the only panel reporting one value per enzyme for every
  surveyed enzyme, inactives included. Its caption gives the assay exactly: HEK293T cells,
  the HEK3 +5 G#sym.arrow.r T edit, dots reflecting the mean of $n = 3$ independent
  replicates. Figure 1C is the alternative but plots only the actives and across several
  endogenous sites, so it cannot be the source of one value for all #num.n_enzymes rows.
- *Which quantity.* Defined verbatim in the Figure 1 caption as the frequency of the
  intended prime editing outcome with no indels or other changes at the target site. These
  are precise-edit percentages, not total editing rates.
- *How the numbers were obtained.* Every one of the #num.n_active non-zero values is an exact
  multiple of 0.5, and every inactive row is exactly 0.0. #num.n_active independent
  amplicon-sequencing measurements landing exactly on half-percent boundaries is not
  plausible. The quantization is the signature of values read off a plot by eye.

The column is therefore recorded in the curated dataset with the literal value
`FigureS1A_HEK3_plus5_G_to_T_mean_n3_UNVERIFIED_DIGITIZED`, so the word UNVERIFIED travels
with the data and no downstream reader can treat it as sourced.

#notebox[
*Consequence, and the primary-analysis decision.* The weighted Spearman half of the
composite metric is computed against a plot read at roughly half a percentage point of
resolution, and the composite's weighting concentrates on exactly the high-efficiency rows
where a digitization error is largest in absolute terms. Under the repository's Gate G2
ruling, *classification on the binary label is the primary analysis*, and every regression,
weighted Spearman and composite number in this report inherits this limitation as a stated
caveat.
]

== Two discrepancies internal to the source

Both gaps below are between the article's prose and the article's own supplementary table,
not between this repository and the paper.

*#num.n_enzymes against #num.prose_tested rows.* The prose says the authors tested
#num.prose_tested enzymes; Table S1's assayed block holds #num.n_enzymes, and its index runs 1 to
#num.n_enzymes without a gap. The #num.n_enzymes names in Table S1 are exactly the #num.n_enzymes
in the inherited file as sets, with nothing in either direction. Either the table is complete
and the prose is wrong, or two assayed enzymes were omitted from the deposited table;
nothing in the published record names them, so nothing can be done either way. Neither
reading changes the benchmark, because under both the #num.n_enzymes rows that exist are the
only ones usable. What it changes is the claim: *the panel must be described as the
#num.n_enzymes enzymes Table S1 lists, not as the #num.prose_tested the paper says were tested.*

*#num.n_active against 20 actives, with the cause identified.* The prose reports
#lower(num.prose_active) RTs with detectable activity; the fill marks #num.n_active. The
responsible enzyme is identifiable from the article's own class breakdown. The Figure S1A
caption splits the actives into 11 retroviral, 2 LTR retrotransposon and 7 bacterial, which
is 20, and the filled set matches in every class except retroviral, where it is 12. The
caption's phrase is "closely related to the M-MLV RT", which excludes M-MLV RT itself, and
the same caption separately marks wild-type M-MLV RT as the enzyme of the PE1 system it is
being surveyed against. *M-MLV RT is the PE1 comparator, not a survey candidate.* Counting
it gives #num.n_active and excluding it gives 20; both are correct under their own definition.
The benchmark uses the table's labelling, because it is attached to the itemised artifact
rather than to a sentence, and because dropping M-MLV RT would remove the single
highest-weighted row in the composite metric (#link(<resolve>)[section 8]).

== Composition, and what is not verifiable

#figure(
  caption: [Panel composition by family, with sequence length in residues. Three families
  hold no active enzyme, and one holds a single enzyme. From
  `reports/dataset_overview.md`.],
  btab(
    (auto, auto, auto, auto, auto, auto, auto),
    ([family], [enzymes], [active], [inactive], [shortest], [median], [longest]),
    (
      ([Retroviral], [18], [12], [6], [571], [654], [693]),
      ([Retron], [12], [5], [7], [292], [370], [604]),
      ([LTR_Retrotransposon], [11], [2], [9], [367], [505], [824]),
      ([Group_II_Intron], [5], [2], [3], [306], [426], [598]),
      ([CRISPR-associated], [5], [0], [5], [240], [311], [446]),
      ([Other], [5], [0], [5], [315], [336], [682]),
      ([Unclassified], [1], [0], [1], [226], [226], [226]),
    ),
    aligns: (left, right, right, right, right, right, right),
  ),
) <tab:composition>

The panel is dominated by two families: Retroviral holds 18 of the #num.n_enzymes enzymes and
12 of the #num.n_active actives, Retron holds 12 and 5. Between them they are 30 rows and 17
of the actives, so a model that learns only the retroviral clade will score well on the
pooled metric while having learned one clade. Length is not independent of family either:
the bacterial families sit near 300 to 500 residues and the retroviral family near 570 to
700, so any model with access to length has partial access to lineage. Over the whole panel
length runs from #num.len_min to #num.len_max residues, median #num.len_median, mean #num.len_mean
with a standard deviation of #num.len_sd. Among the #num.n_active actives the digitized
efficiencies run from #num.eff_min to #num.eff_max percent, median #num.eff_median, mean
#num.eff_mean.

Two further things about this dataset cannot be verified and are flagged rather than
resolved. Table S1 gives no accession for any assayed enzyme and the article's full text
contains no protein accession of any recognised form, so accessions were resolved from
sequence against UniProt; #num.accessions pinned exactly. And no class labels exist in the
table: the paper's 14 classes are in the Figure 1B tree image only, so the benchmark's
7-way family labelling is inherited and *cannot be verified against the paper*. Every
family-based result in this report is conditional on a labelling whose authority is the
inherited file.

= Methods

== The nested leave-one-family-out protocol

Every experiment in this repository calls one harness, `bench/protocol.py`, and nothing
else. The point of the harness is structural rather than statistical: the function that
selects a configuration receives only training families, so held-out labels cannot reach a
selection decision even by accident.

#figure(
  caption: [The protocol, reproduced verbatim from `WRITEUP.md`.],
  block(width: 100%, inset: 9pt, stroke: 0.5pt + luma(60%), fill: luma(97%), align(left, raw(
    "outer loop: for each of the 7 families F
    test  = F, train = the other 6
    inner loop: LOFO over the 6 training families
        select head, hyperparameters and preprocessing using inner scores only
    refit the selected configuration on all 6, predict F
pool the 57 outer predictions, compute CLS once",
    block: true,
  ))),
) <fig:protocol>

Selection is a pure function of the training families *by construction*, because
`select_configuration` never receives the test fold. `bench/test_protocol.py` demonstrates
that property rather than asserting it in prose: it corrupts every held-out label and
requires the selected configuration to be byte-identical afterwards. It also carries a
deliberate *peeking positive control*, a selector that does look at the held-out family,
which the purity check is required to reject. That control is the load-bearing test. A green
suite in which peeking also passed would mean the check is inert and proves nothing. It
currently detects peeking on #num.peek_detect families.

#notebox[
*Why that last number is not 7 of 7, stated rather than smoothed.* The control detects
peeking on #num.peek_detect families, which is the figure the repository's own verification
records. On the remaining families the peeking and pure selectors happen to choose the same
configuration, so the corrupted-label run is byte-identical and the check cannot fire. That
is a property of a small grid on a small panel, not evidence that the purity check works
there. The check is sound where it fires and uninformative where it does not.
]

*Why the composite is computed on pooled predictions and never per fold.* Three families
(CRISPR-associated, Other, Unclassified) contain zero active enzymes, so precision-recall
area is undefined within them, and Unclassified holds a single enzyme. Pooling the
#num.n_enzymes outer predictions and scoring once is the only scheme that handles those folds
without special cases or dropped rows. It is also what the source competition's evaluator
does, which keeps the honest number comparable to the dishonest one it replaces.

== Representations

Twelve representations enter the primary analysis, named here as they are named in the
result files: `length` (sequence length alone, the baseline every other row has to clear);
`aa_composition`; `dipeptide`; `kmer3`; `kmer4`; `physicochemical` (Biopython descriptors
including net charge at pH 7.4); `handcrafted` (every handcrafted block concatenated:
length, composition, dipeptide, reduced-alphabet 3-mer, physicochemical, structural);
`esm2_8M`, `esm2_35M`, `esm2_150M`, `esm2_650M` (ESM-2 @lin2023 at four parameter scales,
final layer, mean pooled over residue positions); and `handcrafted_plus_esm2_650M`.

The second analysis in this repository evaluates a different, overlapping panel of ten
representation builds under the composite metric, including a structural block and four
attempted corrections to the ESM-2 650M embedding. Those are named in
@tab:repr-cls and the difference between the two panels is set out in
#link(<two>)[section 5.7].

== Heads, and why the capacity is restricted

Two model heads and no others: regularized logistic regression for the binary label and
ridge regression for the continuous one. The only selected quantity is the regularization
strength, *one* free parameter, drawn from a grid of six values fixed in advance
(logistic $C in {#num.c_grid}$; ridge $alpha in {#num.alpha_grid}$). Scaling and imputation are
pipeline steps fitted on training rows alone.

This restriction is the design, not a shortcut, and there are two reasons for it. First, the
capacity to search over model families is itself a source of score: on this panel and this
metric a search with #num.comp_n free parameters reaches #num.k29_p95 on pure Gaussian noise
(#link(<null>)[section 4]). A flexible head would extract more signal if signal exists, and
would also manufacture more from noise, and at this sample size the second effect is not
small. Second, holding the head fixed is what makes a representation comparison
interpretable at all; otherwise the difference between two rows is a difference between two
searches.

== Metrics, and why a composite can read exactly zero <metrics>

Three quantities are reported. *PR-AUC*, the precision-recall area under the binary activity
label, is the primary metric of the manuscript analysis, because that label is the one
reproducible from the source file; its chance level is the positive prevalence,
#num.chance_pr. *Weighted Spearman* is a rank correlation against the digitized efficiency
column, weighting each enzyme by its efficiency plus 0.01. *CLS* is the composite the source
competition used: the harmonic mean of those two, and the primary metric of the rebuild
analysis.

A harmonic mean floors at zero when either term does, and the weighted Spearman term is
itself floored at zero. So a model that separates actives from inactives well, but does not
reproduce the digitized ordering of the high-efficiency enzymes, scores a composite of
exactly 0.0000 no matter how good the separation is. This is real metric behaviour, not a
bug, and it is common here: in the baseline ladder, handcrafted features with a logistic
regression head reach a precision-recall area of #num.hlr_pr, well above the #num.chance_pr
chance level, and still score a composite of 0.0000. Those two figures are the two
components of one composite on one model, not a comparison between analyses.

#notebox[
*The worked example is quoted at a different value in the repository's prose.* `WRITEUP.md`
gives this row's precision-recall area as 0.6427. The result file
`bench/results/baseline_ladder.json` gives #num.hlr_pr, and this report uses the result file.
The 0.6427 is a pre-repair value left beside a post-repair composite;
#link(<defect>)[section 7] records the defect that caused it.
]

A metric that can compress a precision-recall area of #num.hlr_pr and one of #num.chance_pr into
the same value of 0.0000 deserves to be reported alongside its components and never alone.
Every composite table in this report therefore carries the weighted Spearman term beside it.

== Identity clustering, reported as a limitation and not as control

Sequences were clustered with MMseqs2 @mmseqs2 (`easy-cluster`, commit #raw(num.mmseqs_commit)) at 90, 70,
50 and 30 percent identity, with parameters fixed a priori (`--cov-mode 1 -c 0.8 -s 7.5`).
Coverage is measured over the target rather than bidirectionally, because these are excised
domains with different boundaries and containment is what redundancy between them looks like.

*No cluster crosses a family boundary above 50 percent identity. #num.clust30_cross clusters do
at 30 percent*, which is the conventional line below which two proteins are not assumed
homologous. The crossing clusters join three bacterial families to each other and join
`CaMV-RT` to two LTR retrotransposon RTs; both patterns look like genuine phylogenetic
signal that the inherited 7-way labelling coarsens away rather than like mislabelled rows.

The consequence is stated as a limitation and not claimed as a control: leave-one-family-out
holds out a clade, and it does *not* hold out remote homology. For the families involved,
holding out the family still leaves relatives above 30 percent identity in training. An
earlier version of `reports/split_design.md` asserted that no cluster crosses a family
boundary "at any threshold"; that was written when only 90, 70 and 50 percent had been
computed, and it is false at 30. Both affected documents are corrected in place with the
original wording quoted.

Two clusters hold an active and an inactive enzyme together at 90 percent identity
(`BAEMV-RT` active with `FENV1-RT` inactive; `ASLV-RT` active with `RSVSB-RT` inactive).
These are the pairs no similarity-based method can get fully right. Either activity turns on
a few residues or one of the calls is noise, and #num.n_active positives cannot separate those
readings. Separately, `Retron86-RT` (319 residues) is wholly contained in `retronE,coli-RT`
(333 residues): the same sequence excised at two boundaries, so the panel holds fewer
independent observations than its row count suggests.

= The search-capacity null <null>

This section is given its own number because the instrument is the contribution.

== Definition

#block(inset: (x: 0.8cm))[
*Search-capacity null.* Given a selection procedure with $K$ free parameters and a search
budget $B$, run that procedure *unchanged* on $K$ vectors of pure Gaussian noise and record
the score it reaches. Nothing in those vectors carries information about activity, so
whatever the search attains is what the procedure can manufacture from nothing on this
dataset with this metric.
]

The quantity being measured is not the model and not the data; it is the *procedure's
capacity to fit*. Every score in this repository is printed next to its null, and a score
that does not clear its null has reported nothing, because the reader cannot separate the
signal from the search. The implementation is `bench/search_null.py`, whose reference
configuration mirrors the inherited `fast_opt.py` exactly: #num.comp_n vectors, weight bounds
$[-1.5, 1.5]$, a power exponent in $[0.2, 1.5]$, 260 differential-evolution iterations,
population size 10, seed 42, polish disabled.

One deviation is deliberate and recorded: `fast_opt.py` seeds its starting point from
previously fitted constants, which cannot be done for noise, so the null searches from
scratch. That can only *understate* the null, which is the safe direction for an instrument
whose purpose is to set a bar.

== Capacity grows with free parameters and does not saturate

#figure(
  caption: [Composite score reached on pure Gaussian noise, by number of free parameters in
  the search. Budget fixed at 260 differential-evolution iterations. From
  `bench/results/search_null.json`, key `k_sweep`.],
  btab(
    (auto, auto, auto, auto, auto, auto, auto),
    ([$K$], [repeats], [mean], [sd], [p95], [min], [max]),
    t_ksweep,
    aligns: (right, right, right, right, right, right, right),
  ),
) <tab:ksweep>

Five free parameters already reach a p95 of #num.k5_p95 on noise, which is above the best
trained baseline measured anywhere in this repository. At the #num.comp_n parameters that
match the prior submission's search the p95 is #num.k29_p95, and at 50 it is #num.k50_p95. *The
capacity curve does not saturate over the range tested.* There is no point in this range
where adding free parameters stops buying score from noise, which is the property that makes
the instrument necessary rather than decorative at this sample size.

The budget sweep makes a second point: most of the manufacturable score is available almost
immediately. Ten differential-evolution iterations at $K = #num.comp_n$ already reach a mean of
#num.budget10_mean, against #num.k29_p95 at the p95 of the full 260-iteration budget. A search
does not need to be patient to manufacture most of what it can manufacture.

#figure(
  caption: [Budget sweep at $K = 29$: the composite score reached on noise against the number
  of differential-evolution iterations. From `bench/results/search_null.json`, key
  `budget_sweep`.],
  btab(
    (auto, auto, auto, auto, auto),
    ([iterations], [repeats], [mean], [sd], [p95]),
    t_budget,
    aligns: (right, right, right, right, right),
  ),
) <tab:budget>

#figure(
  image("/bench/figures/search_null_capacity.png", width: 100%),
  caption: [The capacity curve. Composite score reached on pure Gaussian noise as a function
  of the number of free parameters in the search, with the budget sweep at $K = 29$
  alongside. The curve does not flatten over the range tested, which is why a reported score
  must be printed against the null at *its own* free-parameter count rather than against any
  convenient one. Generated by `bench/search_null.py`.],
) <fig:capacity>

== One number I did not force to agree

The project brief this work was built against expected the $K = #num.comp_n$ noise null to
land near #num.ref_expected. The single reference draw at seed 42 came out #num.ref_draw, a
deviation of more than the #num.ref_tolerance tolerance the self-check used, and the self-check
reported FAIL. *Nothing was adjusted*: not the budget, not the bounds, not the tolerance.

The distribution resolved it honestly. Across #num.ref_repeats repeats the reference null has
mean #num.ref_mean and median #num.ref_median. The expected #num.ref_expected was correct, and it
describes the centre of the distribution; the single draw was simply a high one compared
against the wrong statistic. The fix was to report the right quantity, not to change the
procedure until the number agreed.

Continuous integration now verifies the three properties that make the instrument
trustworthy, and deliberately does not assert a published value:

#block(inset: (x: 0.8cm))[
1. *Determinism at a fixed seed.* Two runs at the same seed must return bit-identical
   scores.
2. *A noise score well above zero.* The null must exceed 0.2, which fails loudly if the
   optimizer is not actually running.
3. *Capacity growing with $K$.* The score at $K = 20$ must be at least the score at $K = 2$.
]

#notebox[
*Why the third item is a property and not a value.* An instrument that is tuned until it
reproduces an expected number is no longer an instrument; it is a fit. Asserting
#num.ref_expected in continuous integration would have created exactly the pressure that
produced the error this repository exists to correct. The self-check asserts the properties
that would break if the instrument stopped working, and the distribution is reported in the
result file for anyone who wants the value.
]

= Results

Every number in this section is read from a result file by `reports/build_pdf.py`, which
generates the tables below rather than transcribing them, and which refuses to build this
document if a quoted figure cannot be found in its stated source.
`reports/REPORT_NUMBER_AUDIT.md` lists all of them with their key paths.

== Baseline ladder, composite metric <ladder>

All rows run through the nested protocol of @fig:protocol. The composite is the primary
column; the weighted Spearman term is shown beside it because, as
#link(<labels>)[section 2.2] and #link(<metrics>)[section 3.4] establish, the composite can
read exactly zero for reasons that are about the metric and the digitized label rather than
about the model.

#figure(
  caption: [The baseline ladder under the composite metric, ordered by score. "Selected"
  gives the number of candidate configurations the inner loop chose between; "none" marks a
  zero-training baseline that fits nothing. "Null p95" is the 95th percentile of the
  search-capacity null at that row's own free-parameter count, and "margin" is the score
  minus that null. "Beats length" compares against the #num.length_cls reference row.
  Generated from `bench/results/baseline_ladder.json`.],
  btab_mark(
    (1fr, auto, auto, auto, auto, auto, auto),
    ([method], [selected], [CLS], [wSpear.], [null p95], [margin], [beats length]),
    t_ladder,
    aligns: (left, right, right, right, right, right, center),
  ),
) <tab:ladder>

Two things in that table carry the section.

*The two best rows are zero-training baselines, and no trained model beats
`protein_length_aa` at #num.length_cls.* The four trained rows score #num.rf_cls, 0.1802, 0.0000
and 0.0000. Not one of them beats a single number that was already sitting in the input
file, computed for free, with nothing fitted.

*Four rows score exactly 0.0000*, for the harmonic-mean reason set out in
#link(<metrics>)[section 3.4] rather than because those models separate nothing.

A narrower claim needs stating precisely, because an earlier version of this repository
overstated it. The sentence "no method tested beats `protein_length_aa`" is *false* as
written: the zero-training 3-mer cosine baseline reaches #num.kmer_cos_cls against length's
#num.length_cls and clears its own null by a positive margin, as does the family prior and as
does length itself. What is true, and is what @tab:ladder shows, is that *no trained model*
beats the length column, and that the three rows which do clear their nulls are all
zero-training baselines that fit nothing at all. The result file marks the 3-mer cosine row
`beats_length_baseline: true` outright, so the broader sentence is contradicted by the
repository's own output; this report states the narrow version.

#figure(
  image("/audit/figures/cls_ladder.png", width: 92%),
  caption: [The commit ladder of the prior submission: the composite score quoted in commit
  subject lines, in commit order, rising from #num.ladder_first to #num.ladder_last across
  #num.ladder_n. This is not a learning curve. It is a record of a search being resumed
  against the labels it was scored on, and it is the evidence
  #link(<postmortem>)[section 6] turns on. Generated by `audit/leakage_audit.py`.],
) <fig:ladder>

== Representations under the composite protocol <clsresults>

One nested protocol, one pair of inner-selected heads, only the representation varies. This
is the rebuild analysis; its primary metric is the composite and its primary control is the
search-capacity null.

#figure(
  caption: [Ten representation builds under the composite metric, ordered by score. The null
  p95 is #num.repr_null_p95 for every row, because every row runs the same selection
  procedure. "Family acc." is a descriptive property of the representation, computed once on
  all rows without any activity label, against a majority baseline of #num.fam_majority.
  Generated from `bench/results/representations.json`.],
  btab(
    (1fr, auto, auto, auto, auto, auto, auto),
    ([representation], [features], [CLS], [wSpear.], [null p95], [margin vs null], [family acc.]),
    t_reps,
    aligns: (left, right, right, right, right, right, right),
  ),
) <tab:repr-cls>

*Every margin is negative.* No representation clears the score its own selection procedure
reaches on pure noise. On this task, at this sample size, under this metric, none of them has
demonstrated signal.

Three further observations, each stated at the strength the panel supports.

*The scale series is non-monotonic and the largest model is the worst.* ESM-2 goes
#num.e8_cls at 8M parameters, #num.e35_cls at 35M, #num.e150_cls at 150M, and #num.e650_cls at 650M.
No mechanism is offered for that. At a minimum resolvable composite difference of
#num.mrd_cls (#link(<resolve>)[section 8]) *the ordering cannot be claimed as real*; the gap
from best to worst in this series is smaller than the smallest difference this panel can
resolve at 80 percent power. It is reported because suppressing an inconvenient
non-monotonicity would repeat precisely the error this repository exists to correct.

*Seven of ten rows score exactly 0.0000*, which compresses a great deal of genuinely
different behaviour into one value and limits what any comparison between them can say.

*The confound is visible directly in the table.* Family accuracy is high and stable near
#num.fam_cls_protocol across the ESM-2 rows while the composite is near zero. The
representation reliably knows what an enzyme is related to and reliably does not know what
it does. #link(<lineage>)[Section 5.5] measures that separately and without activity labels.

#figure(
  image("/bench/figures/function_vs_lineage.png", width: 92%),
  caption: [Function against lineage, one point per representation build: composite activity
  score on one axis against family-classification accuracy on the other. The points occupy
  the high-lineage, low-function corner. A representation that encoded catalysis would move
  up the function axis; these move along the lineage axis instead. Generated by
  `bench/representations.py`.],
) <fig:funclin>

== Representations under the three-control protocol, precision-recall area <prresults>

This is the manuscript analysis. Its primary metric is precision-recall area on the binary
activity label, the label reproducible from Table S1, and it applies three controls rather
than one: a dimensionality-matched Gaussian noise control, a search-capacity null at the
matched free-parameter count ($K = #num.free_params$, p95 #num.k1_p95), and a label permutation
over #num.n_perm repeats in which both labels are permuted together so that only their pairing
with the sequences is broken. A representation must clear all three to count as a result.

#figure(
  caption: [Twelve representations under the three-control protocol, ordered by
  precision-recall area. Chance is the positive prevalence, #num.chance_pr. "Survives" requires
  clearing the noise control, chance, *and* the permuted-label p95 together; "n/a" marks the
  six rows for which the permutation was not run, so they are not claimed either way.
  Intervals are percentile bootstrap over #num.n_bootstrap draws. Generated from
  `bench/results/taskA_representations.json` and `bench/results/taskA_validation.json`.],
  btab_mark(
    (1fr, auto, auto, auto, auto, auto, auto),
    ([representation], [features], [PR-AUC], [95% CI], [noise control], [permuted p95], [survives]),
    t_taskA,
    aligns: (left, right, right, center, right, right, center),
  ),
) <tab:repr-pr>

#notebox[
*The central methodological point of this report.* ESM-2 650M reaches #num.e650_pr against a
noise control of #num.e650_noise, and ESM-2 8M reaches #num.e8_pr against #num.e8_noise. *Both
clear their noise controls.* Both then fail label permutation: #num.e650_pr against a permuted
p95 of #num.e650_perm, and #num.e8_pr against #num.e8_perm. In both cases shuffled labels reproduce
the observed score more than five percent of the time.

Had this study reported the noise control alone and stopped, *it would have reported two
ESM-2 scales as clearing their nulls.* On a panel this size a dimensionality-matched
random-feature control is not a sufficient null, and any small-sample representation
benchmark that reports one and stops is under-controlled.
]

The noise control is not a formality at these dimensionalities either: #num.kmer4_feats random
features reach a precision-recall area of #num.kmer4_noise, well above the #num.chance_pr chance
level, purely from having many dimensions and #num.n_enzymes rows to fit them on.

Under the composite metric with the matched $K = #num.free_params$ bar of #num.k1_p95, *no
representation under either head clears the gate*: the highest composite observed anywhere in
this analysis is #num.phys_cls, every one of the bootstrap intervals on the composite includes
zero, and the median minimum resolvable difference of #num.mrd_median exceeds every composite
value observed. The full composite tables for both heads are in #link(<app:tables>)[Appendix A].

#figure(
  image("/reports/figures/taskA_null_comparison.png", width: 100%),
  caption: [*The headline figure.* Observed precision-recall area per representation against
  its dimensionality-matched Gaussian noise control and its permuted-label 95th percentile.
  The two ESM-2 bars that clear their noise control and are then overtopped by their own
  permuted-label line are the result of this study in one picture. Generated by
  `bench/figures_taskA.py`.],
) <fig:null>

#figure(
  image("/reports/figures/taskA_representation_comparison.png", width: 100%),
  caption: [Precision-recall area per representation with its 95 percent bootstrap interval,
  against the #num.chance_pr chance level. The intervals overlap almost everywhere, which is
  the same fact @tab:mrd states numerically. Generated by `bench/figures_taskA.py`.],
) <fig:repcomp>

== The one surviving representation, and what it survived with

`kmer4`, a 4-mer frequency block over the 20-letter alphabet, clears all three controls:
precision-recall area #num.kmer4_pr against a noise control of #num.kmer4_noise, chance of
#num.chance_pr, and a permuted p95 of #num.kmer4_perm, a margin of #num.kmer4_gate_margin over the
larger of its nulls. It is the only representation in @tab:repr-pr that does, and it is not a
language model.

Because it cleared the gate it is the only representation this report interprets. The gate
exists for a reason: a feature-importance plot of a model that loses to protein length looks
exactly like the plot of a model that works, and a plot is believed. Attribution here is
*exact* rather than estimated, because the head is linear and the Shapley value of a feature
in a linear model is its coefficient times its centred value. Nothing is sampled and no SHAP
package is used. Attributions are computed out of fold: for each held-out family, the
configuration that family's own inner loop selected is refitted on its training folds and
attributions are taken for the held-out rows only, so they describe the models the benchmark
actually scored.

#figure(
  caption: [What `kmer4`'s surviving signal is made of. From `reports/interpretation.md`,
  computed by `bench/interpret_taskA.py`.],
  btab(
    (1fr, auto, 1.1fr),
    ([measurement], [value], [how to read it]),
    (
      (
        [out-of-fold score against sequence length],
        [Spearman #num.kmer4_len_rho, \ $p$ = #num.kmer4_len_p],
        [the row that matters. A score strongly ranked by length is substantially a length detector, and length is free],
      ),
      (
        [attribution mass in the top decile of family-explained features],
        [#num.kmer4_decile],
        [against a feature share of #num.kmer4_decile_share: the fit leans on dimensions that family explains, by about 64 percent more than their share],
      ),
      (
        [per-feature importance against family-explained variance],
        [Spearman #num.kmer4_perfeat, \ $p$ = #num.kmer4_perfeat_p],
        [the association is systematic across all #num.kmer4_feats features, not an artifact of a few],
      ),
      (
        [attribution mass in the top 1 percent of features],
        [#num.kmer4_top1],
        [against a feature share of #num.kmer4_top1_share: the signal is diffuse, so no small set of 4-mers carries it],
      ),
    ),
  ),
) <tab:kmer4>

*So `kmer4` survives the controls, and what it has survived them with is sequence length and
family structure rather than a specific biological motif.* The top-ranked 4-mer carries
#num.top_feat_share of the attribution mass; with #num.kmer4_feats features and #num.n_enzymes rows
no individual coefficient is estimable, and the diffuse mass confirms there is nothing
motif-like to report. *This ranking is not interpreted as motif discovery*, and a reader
looking for a catalytic signature in it would be reading noise.

This matters for how the one positive result in this benchmark should be cited. `kmer4`
clearing its noise control, chance and its own permuted labels is a real and reproducible
property of these data. It is *not* evidence that 4-mer composition captures reverse
transcriptase catalysis, and it does not rescue the headline: what separates actives here is
substantially the same lineage-and-length confound that @tab:lineage measures directly,
reached by a different route.

== Lineage against function <lineage>

The two measurements in this subsection use *no activity label anywhere*. Activity appears
only as a colour in one figure.

#figure(
  caption: [What the representation predicts, measured without activity labels for family
  and with them only for activity. Family accuracy is stratified 5-fold logistic regression
  restricted to families with at least five members, which keeps #num.diag_rows rows and drops
  the singleton Unclassified family. From `reports/representation_diagnostics.md` and
  @tab:repr-pr.],
  btab(
    (1fr, auto, auto, auto),
    ([what is predicted], [ESM-2 650M], [best simple control], [majority or chance]),
    (
      ([evolutionary family, 5-fold accuracy], [#num.fam_diag], [#num.fam_3mer, 3-mer raw counts], [#num.fam_major]),
      ([activity out of family, PR-AUC], [#num.e650_pr], [#num.kmer4_pr], [#num.chance_pr]),
    ),
    aligns: (left, right, right, right),
  ),
) <tab:lineage>

*That contrast is the finding.* The same representation that classifies evolutionary family
at #num.fam_diag predicts activity, out of family, at barely above chance. Three supporting
measurements:

- *Family accuracy rises monotonically with model scale*: #num.fam_8m at 8M parameters,
  #num.fam_35m at 35M, #num.fam_150m at 150M, #num.fam_diag at 650M, against a #num.fam_major
  majority baseline. Activity prediction does not rise with scale. Whatever scaling buys on
  this panel, it buys lineage.
- *The leading principal component is substantially a length axis*, tracking sequence length
  at Spearman #num.pc1_len on standardized embeddings. Length is a feature any model can
  compute for free, which is why the length-only baseline rather than the majority baseline
  is the bar every representation has to clear.
- *A length-only feature already classifies family at #num.fam_len*, well above the
  #num.fam_major majority baseline, which is the confound stated as a number: in this panel,
  knowing how long an enzyme is already tells you a good deal about what it is related to.

#notebox[
*Two preprocessing caveats on the correlation, stated rather than buried.* The
#num.pc1_len figure is measured on standardized embeddings. On centred but *not* standardized
embeddings the same correlation is #num.pc1_unscaled: the sign flips and the magnitude changes,
because the sign of a principal component is a PCA convention that carries no meaning. The
magnitude is what is being claimed, and it is strong under both choices. Separately, the
3-mer control is reported in two encodings (#num.fam_3mer for raw counts, and a materially
different value for frequency-normalized counts) because the repository specifies no encoding
for this control, and reporting only one would be choosing the comparison that suits the
conclusion.
]

The confound this creates is worth stating directly. Family and activity are strongly
associated in these data: 12 of 18 retroviral enzymes are active, and 0 of 15 across the
three families with no actives. *A representation can therefore score well on activity by
encoding clade.* These diagnostics establish that the representations do encode clade, and
do encode length; they establish nothing about activity prediction, which is what
@tab:repr-pr and @tab:repr-cls are for.

#figure(
  image("/reports/figures/taskA_embedding_by_length.png", width: 100%),
  caption: [*The important embedding figure.* PCA and UMAP projections of the ESM-2 650M
  embedding coloured by sequence length, with PC1 plotted against length directly in the
  third panel. The dominant axis of variation is a length axis. The UMAP panel of
  #num.n_enzymes points at `n_neighbors=10` should be read as a sketch and not as structure:
  UMAP on a sample this small will produce apparent clusters from noise. Generated by
  `embeddings/representation_diagnostics_taskA.py`.],
) <fig:emblen>

#figure(
  image("/reports/figures/taskA_pc_length_correlation.png", width: 100%),
  caption: [Spearman correlation of principal components 1 to 4 against sequence length, per
  ESM-2 model size. PC1 carries the length association at every scale above 8M. Generated by
  `embeddings/representation_diagnostics_taskA.py`.],
) <fig:pclen>

#figure(
  image("/reports/figures/taskA_embedding_by_family.png", width: 100%),
  caption: [The same embedding space, small multiples with one panel per family, each family
  highlighted against the rest. Small multiples are used rather than seven categorical hues
  because seven hues cannot be distinguished reliably in a scatter: on this project's
  reference palette the worst all-pairs separation is a colour-vision-deficiency $Delta E$ of
  3.2, below the floor, and no re-ordering fixes it because a scatter puts every pair on
  screen at once. Generated by `embeddings/representation_diagnostics_taskA.py`.],
) <fig:embfam>

#figure(
  image("/reports/figures/taskA_embedding_by_activity.png", width: 100%),
  caption: [The same projections coloured by activity instead of by length or family. Compare
  against @fig:emblen: the structure the representation organises itself around is not the
  activity label. Generated by `embeddings/representation_diagnostics_taskA.py`.],
) <fig:embact>

== Failed corrections <failed>

Four corrections were tested against the ESM-2 650M embedding, each targeting the confound
measured above. All four failed, and they failed in an informative direction.

#figure(
  caption: [The four attempted corrections, from @tab:repr-cls. Every one left the composite
  at exactly 0.0000, and the two that target the catalytic core produced the highest lineage
  accuracy of any representation build measured.],
  btab(
    (1fr, auto, auto, 1.2fr),
    ([correction], [CLS], [family acc.], [what it was meant to remove]),
    (
      ([length-residualized], [0.0000], [#num.fam_cls_protocol], [the length axis of @fig:pclen]),
      ([family-residualized], [0.0000], [#num.fam_cls_protocol], [the #num.famres_removed leading principal components that family explains, #num.famres_var of the variance]),
      ([catalytic-core pooled], [0.0000], [#num.core_fam], [everything outside the catalytic core window]),
      ([attention-weighted core pooling], [0.0000], [#num.core_fam], [the same, weighted by attention rather than masked]),
    ),
    aligns: (left, right, right, left),
  ),
) <tab:corrections>

*This is the most interesting negative result in the report.* Restricting the representation
to the catalytic machinery, which is the part of the protein that actually does the
chemistry, made the representation *better* at predicting evolutionary family (#num.core_fam,
the highest of any build measured, against #num.fam_cls_protocol for plain mean pooling) and no
better at predicting function (0.0000, unchanged). That is the opposite of the intended
effect.

Two readings are available and this panel does not separate them. Either the catalytic core
of these domains is itself the most phylogenetically informative region, so focusing on it
concentrates lineage rather than removing it; or the composite metric is floored at zero for
all four variants for the harmonic-mean reason of #link(<metrics>)[section 3.4] and is
therefore unable to register an improvement of the size any of these corrections could
produce. The second reading is live: #num.n_active positives and a minimum resolvable
difference of #num.mrd_cls leave very little room for a correction to show up. The honest
summary is that the obvious corrections did not work and that this benchmark could not have
detected it if they had worked slightly.

== Two evaluations of one panel <two>

This repository contains two evaluations of the same enzyme panel, and the two are reported
separately above rather than merged. This subsection states plainly what differs, which
numbers come from which, and why the difference is not a discrepancy to be averaged away.

#figure(
  caption: [The two analyses side by side. They share the enzyme panel, the nested
  leave-one-family-out structure and the seed. They differ in primary metric, in control
  regime, in which representation builds were run, and in the fold draw used for the
  descriptive family-accuracy measurement.],
  btab(
    (auto, 1fr, 1fr),
    ([], [the rebuild analysis], [the manuscript analysis]),
    (
      ([reported in], [#link(<clsresults>)[section 5.2], @tab:repr-cls], [#link(<prresults>)[section 5.3], @tab:repr-pr]),
      ([primary metric], [CLS, the composite], [PR-AUC on the binary label]),
      ([primary control], [search-capacity null at the row's own $K$], [three controls: Gaussian noise, matched-$K$ search null, label permutation]),
      ([representations], [10 builds, including a structural block and four attempted corrections], [12 builds, including ESM-2 at four scales and five composition blocks]),
      ([result files], [`bench/results/representations.json`, `baseline_ladder.json`], [`bench/results/taskA_representations.json`, `taskA_validation.json`]),
      ([family accuracy reported], [#num.fam_cls_protocol], [#num.fam_diag]),
      ([headline], [every margin against the null is negative], [one of twelve survives all three controls, and it is not a language model]),
    ),
  ),
) <tab:two>

The two family-accuracy figures, #num.fam_cls_protocol and #num.fam_diag, are the ones most
likely to be mistaken for a contradiction, so the cause is given exactly. *Both are
measurements of the same property of the same representation under the same rule, differing
only in how the cross-validation folds were drawn.* Both restrict to families with at least
five members, keeping #num.diag_rows rows and dropping the singleton Unclassified family; both
use stratified 5-fold logistic regression with `max_iter=5000`; both report the mean fold
accuracy against the same #num.fam_major majority baseline. They differ in two respects, both
of which change the fold assignment and neither of which changes the representation:

- *The shuffle seed.* `bench/representations.py` inherits `SEED = 42` from the protocol
  module; `embeddings/representation_diagnostics_taskA.py` sets `RANDOM_STATE = 0`.
- *The row order the shuffle is applied to.* The first reads rows in the order of
  `data/rt_sequences.csv`, the second in the order of
  `tasks/taskA_crossfamily/curated.csv`. The two files hold the same #num.n_enzymes names with
  identical family labels in a different order, and `StratifiedKFold(shuffle=True)` is
  sensitive to input order.

Those two factors give four fold draws, and the published figures are two corners of that
grid. The spread across all four is well inside the #num.fam_sd_650m fold-to-fold standard
deviation that the diagnostics report for this measurement, so the two numbers are two draws
from one sampling distribution rather than two different findings. The underlying embedding
builds are *not* the cause: the two files store the same representation, one at float32 and
one at float16, differing only by that storage precision. Neither pooling nor
layer differs; both are the final layer, mean pooled.

#notebox[
*What could not be established from the repository, stated as such.*
`reports/reconciliation.md` is the Gate G2 artifact about the *data source*, and it does not
discuss the difference between these two analyses at all; no document in the repository does.
The mechanism above was established by reading the two implementations and reproducing all
four fold draws, not by reading a document that explains it. The difference in the *PR-AUC*
columns between the two analyses, by contrast, is larger and is *not* explained here: the
rebuild analysis reports a precision-recall area for ESM-2 650M that differs materially from
the manuscript analysis's #num.e650_pr, and the two use different feature tables, different
candidate-configuration grids and different inner-selection criteria. Which of those
accounts for how much of the gap cannot be determined from what the repository records, so no
mechanism is offered.
]

The practical rule this report follows, and the reason for it: *never place a composite value
and a precision-recall value from the other analysis in the same table or the same
comparative sentence.* They are different metrics computed over different representation
builds under different fold rules, and the only thing averaging them would produce is a
number belonging to neither.

= Post-mortem: why the previously reported 0.9754 is not a measurement <postmortem>

This section is written in the first person, because the error is mine.

== What the search actually did

I wrote `legacy_leaky/fast_opt.py`. It builds an objective that returns the negation of
`compute_cls(seq["active"], y_score, seq["pe_efficiency_pct"])` evaluated over *all
#num.n_enzymes rows*, and hands that objective to
`scipy.optimize.differential_evolution` @scipy over #num.comp_n blend weights plus a power
exponent. The labels in that call are the labels the score is reported against. There is no
held-out set anywhere in the loop. The repository's static leakage scan classifies the file
as `SELECTION_LEAK`, meaning the metric value is fed back into a search construct in the same
file, so held-out labels inform a choice.

It is worse than a single pass in three ways.

*The search reseeded itself from its own previous results.* The script seeds its starting
point by parsing previously fitted constants back out of
`experiments/calibrated_lofo_predictions.py`, so every run resumes the previous run's hill
climb rather than starting fresh. The effective number of objective evaluations against
those #num.n_enzymes labels is therefore not one run's budget but the sum over every run ever
executed.

*The commit history records the climb directly.* #num.ladder_n carry a composite score in the
subject line, rising from #num.ladder_first to #num.ladder_last (@fig:ladder). That is not a
record of a model improving. It is a record of an optimizer being restarted against a fixed
set of test labels, with each improvement committed.

*The winning parameters are frozen into source at 16 significant figures*, which is the
signature of a fitted constant rather than a chosen one. For context, the #num.comp_n stored
blend components scored individually against the same labels reach a best of #num.comp_best and
a mean of #num.comp_mean; the blended #num.sub_cls is what the search added on top of its best
component, fitted against the labels it was scored on.

== The corrected comparison

#correction("2026-10-03")[
An earlier version of this comparison bolded the $K = 50$ row of @tab:ksweep and concluded
that the submitted score "sits inside its own noise floor". *That was an invalid comparison
and it is withdrawn.* It set a #(num.comp_n)-parameter search against the noise ceiling of a
50-parameter one, and the #num.de_params fitted parameters it cited to justify the larger count
belong to a *different* stored artifact, `de_best_weights.json`, which scores
#num.other_artifact rather than #num.sub_cls. Each score must be compared against the null at its
*own* $K$. The correction does not favour this repository's earlier framing.
]

At the matched count of $K = #num.comp_n$ the noise p95 is #num.k29_p95, and the submission's
#num.sub_cls sits *above* it by #num.sub_margin. So the score does not sit inside its noise
floor, and the claim that it did was wrong.

The correct statement is weaker in a different way. That margin of #num.sub_margin is roughly
half the #num.boot_width bootstrap interval width on the submitted prediction vector
(10 000 draws; point estimate #num.boot_point, bootstrap mean #num.boot_mean, interval
#num.boot_lo to #num.boot_hi), measured against a Kish effective sample size of #num.kish2. *The
score is therefore not distinguishable from what the procedure manufactures from noise at
this sample size.*

#notebox[
*Said as precisely as I can say it:* the submitted #num.sub_cls is *not shown to be inside* the
null, and it is *not shown to be outside* it either. This experiment cannot distinguish
whether the underlying model learned anything. I am not claiming it learned nothing. I am
claiming that I presented a number as though it could settle that question when it could not.

*The claim that does not depend on the null at all* is the one that settles the matter: the
search optimized `compute_cls` directly against its own test labels, resuming from its own
previous fits, with no held-out set in the loop. That half was never in doubt, it does not
rest on any comparison against a noise distribution, and it is sufficient on its own to
withdraw #num.sub_cls as a generalization estimate.
]

One further property of the metric belongs here, because it bears on how finely any of these
numbers can be read. The weighted Spearman term ranks with `argsort(argsort(...))`, which
assigns distinct integer ranks to tied values, and every zero-efficiency enzyme is tied. The
ranks given to those 36 rows therefore depend on their position in the merged array rather
than on anything predicted. Over 2000 random row permutations of the submitted vector the
composite moves with a standard deviation of #num.order_sd and a range of #num.order_range. The
effect is real and small, because those rows carry almost none of the weight, and it is
reported because a metric whose value depends on row order at all should be stated plainly
rather than discovered later.

= An inherited data defect that changed a conclusion <defect>

While building the representation tables I found that `topology_features.csv` omits the `-RT`
suffix that `rt_sequences.csv` carries. A join on `rt_name` therefore matched *zero* rows and
fed nine entirely missing columns into the handcrafted feature table. *No error was raised.*
The model trained on empty columns and reported a number, and that number looked exactly like
a number that meant something.

Repairing the join moved a result in the unflattering direction: handcrafted features with a
RandomForest head fell from #num.rf_before to #num.rf_cls, below the #num.length_cls length
baseline, with a negative margin against its own null (@tab:ladder). *The higher score had
come from training on empty columns.*

`bench/names.py` now asserts full coverage and fails loudly rather than returning empty
columns, and records two further defects in the inherited structural data:

- `Line1-RT` has no predicted structure at all.
- `Vp-96.pdb` duplicates `Vp96-RT.pdb` under a different spelling, so the #num.n_struct files
  in `data/structures/` cover only 56 distinct enzymes.

This defect also propagated into the repository's own prose, which is worth recording because
it is the same failure mode one level up. The baseline ladder tables in `WRITEUP.md` and
`PROGRESS.md` carry *pre-repair* precision-recall and weighted Spearman values beside
*post-repair* composite values: only the composite column was updated when the results were
regenerated. For the RandomForest row the write-up prints 0.7810 and 0.3755, whose harmonic
mean is #num.rf_before, beside a composite of #num.rf_cls, which is the harmonic mean of the
result file's actual 0.8288 and 0.2888. The arithmetic is the diagnosis and anyone can repeat
it: the printed pair does not produce the printed composite, and the pair that does is in the
result file. This report takes every figure in @tab:ladder from
`bench/results/baseline_ladder.json` and lists the superseded values in
`reports/REPORT_NUMBER_AUDIT.md` under numbers deliberately not carried forward.

#notebox[
*The general lesson, which is the reason this section exists.* A pipeline that cannot fail
loudly will eventually report a number that means nothing, and it will look exactly like a
number that means something. A silent join is the same class of failure as a leaky search:
in both cases the artifact is well-formed, the plot renders, the metric computes, and nothing
in the output distinguishes the broken case from the working one. The defence is not more
care. It is assertions that halt: `bench/names.py` asserting coverage, the Task A parser
asserting block captions and fill counts before reading a data row, the Task B parser halting
on a numbering mismatch rather than applying an offset it has diagnosed, and
`bench/test_protocol.py` carrying a positive control that must fail.
]

= What this benchmark can resolve <resolve>

Before comparing any two methods it is worth knowing whether this benchmark can tell them
apart. It largely cannot, and this section comes before any reading of the orderings above
for that reason.

#figure(
  caption: [The resolution limits of this panel and this metric. Nothing in this table
  depends on any model; all of it is a property of the metric and the label distribution.
  From `audit/metric_report.md`, `reports/dataset_overview.md`,
  `reports/statistical_validation.md` and `bench/results/representations.json`.],
  btab(
    (1fr, auto),
    ([quantity], [value]),
    (
      ([rows], [#num.n_enzymes, of which #num.n_active active and #num.n_inactive inactive]),
      ([Kish effective sample size of the weighted Spearman weights], [*#num.kish*]),
      ([MMLV-RT share of total weight], [#num.w_mmlv percent]),
      ([top 5 RTs' share of total weight], [#num.w_top5 percent]),
      ([all #num.n_inactive inactives combined], [#num.w_inactive percent]),
      ([bootstrap 95 percent CI width on a fixed prediction vector], [#num.boot_width]),
      ([minimum resolvable CLS difference at 80 percent power], [*#num.mrd_cls*]),
      ([median minimum resolvable CLS difference across all pairs], [*#num.mrd_median*]),
      ([smallest / largest minimum resolvable difference], [#num.mrd_min / #num.mrd_max]),
      ([families holding no active enzyme], [#num.zero_active: CRISPR-associated, Other, Unclassified]),
      ([families holding a single enzyme], [1: Unclassified]),
      ([informative leave-one-family-out folds], [#num.informative, not #num.n_families]),
      ([accessions pinned exactly], [#num.accessions]),
    ),
  ),
) <tab:mrd>

The nominal sample size is #num.n_enzymes. The weighted Spearman term behaves like about
#num.kish2 independent points, and the prior submission fitted #num.comp_n to #num.de_params free
parameters against it. The composite weights each enzyme by its efficiency plus 0.01 and the
efficiencies span 0 to #num.eff_max, so the weight is extremely concentrated: MMLV-RT alone
carries #num.w_mmlv percent of it, the top five carry #num.w_top5 percent, and all #num.n_inactive
inactive enzymes together carry #num.w_inactive percent. *Half the metric is decided by a
handful of high-efficiency enzymes.* Ordering the inactives correctly is close to free and
ordering them wrongly is close to costless.

The minimum resolvable difference is the row that governs every comparison in this report.
Estimated from the paired bootstrap rather than assumed from a formula: for each pair the
paired bootstrap gives the standard deviation of the composite difference under resampling of
the enzymes, and a two-sided test at $alpha = 0.05$ with 80 percent power needs a true
difference of about #num.mrd_z of those standard deviations. That comes to #num.mrd_cls for the
representation panel and a median of #num.mrd_median across all pairs in the manuscript
analysis.

#notebox[
*The consequence, applied to this report's own tables.* A difference smaller than #num.mrd_cls
composite is not resolvable here at 80 percent power. *Almost nothing measured in this report
differs by that much, so almost nothing measured here is a win for either side.* The correct
reading of @tab:repr-cls is not "150M is best" but "no representation is distinguishable from
any other, and none clears its null". Every one of the pairwise comparisons in the manuscript
analysis, all 132 of them, is marked not resolvable; not a single pair clears its own minimum
resolvable difference. Nearly every ordering in this document is provisional and should be
read as such.
]

Three of #num.n_families folds hold no active enzyme at all, so a ranking correlation is
undefined on them and leave-one-family-out rests on #num.informative informative folds rather
than #num.n_families. One fold holds a single enzyme, so nothing about variance within that
family is estimable.

= Would more data help? <scale>

`bench/scale_projection.py` resamples the observed #num.n_enzymes enzymes up to a target size
and recomputes the two quantities that limit this benchmark.

#figure(
  caption: [Projected resolution at larger panel sizes. #num.scale_note Generated from
  `bench/results/scale_projection.json`.],
  btab(
    (auto, auto, auto, auto, auto),
    ([$n$], [Kish ESS], [bootstrap CI width], [noise null mean], [noise null p95]),
    t_scale,
    aligns: (right, right, right, right, right),
  ),
) <tab:scale>

This is the clearest argument in the repository for collecting more data rather than building
better models. Going from #num.n_enzymes to 200 enzymes roughly quadruples the effective sample
size, more than halves the bootstrap interval width, and drops what a search of this size can
manufacture from noise from about 0.86 to about 0.58. *The null falls faster than any
modelling change in this report moved any score.*

But the same table sets a limit on that argument. At $n = 200$ the manufacturable noise score
is still about 0.58, *which is above every honest result measured anywhere in this report*.
Even a quadrupled panel would not rescue this metric on its own. Both the panel and the
metric need work, and the metric is the cheaper of the two to fix.

The projection's assumption is stated in the result file and repeated here because it is
optimistic: it resamples the observed enzymes, so it assumes new RTs resemble these ones. A
genuinely broader panel would be more heterogeneous, so these are best-case figures and the
real curve is likely shallower.

= Task B, and the limits of the cross-task story <taskb>

The repository was built as two tasks. Task A, everything above, asks whether a
representation transfers across RT families. Task B asks whether a representation predicts
the effect of a single substitution within one RT backbone: the regime where protein language
models are expected to work, and where masked marginal likelihood is a standard and often
strong zero-shot predictor.

#notebox[
*The rule this section obeys.* The two tasks' metrics are *never numerically compared*, and
no combined score appears anywhere in this repository. Task A is scored by precision-recall
area over a binary activity call and by a composite over percent precise prime edits; Task B
would be scored by Spearman correlation on a log#sub[2] enrichment ratio rescaled to
$[-1, 1]$. Those are different physical quantities on different scales with different chance
levels over different numbers of rows. `schemas/task_schema.py` refuses to concatenate two
task tables whose labels are measured in different units, so *the merge is blocked in code
and not only in prose*.
]

== Task B is blocked at acquisition

#figure(
  caption: [Where the two tasks stand. Faithful to
  `reports/CROSS_TASK_COMPARISON.md`.],
  btab(
    (auto, 1fr, 1fr),
    ([], [Task A, cross-family transfer], [Task B, within-protein variant effect]),
    (
      ([source], [Doman et al., _Cell_ 2023, Table S1 @doman2023], [Li et al., bioRxiv 2026, Supplementary Tables S6 and S7 @li2026]),
      ([rows], [#num.n_enzymes enzymes, #num.n_active active], [#num.tb_variants variants plus wild type, *expected*]),
      ([primary metric], [PR-AUC out of family], [Spearman, position-held-out and stretch-held-out]),
      ([data status], [complete and endorsed through Gate G2], [*blocked at acquisition*: the activity values were never deposited]),
      ([result status], [12 representations with three nulls each], [*no result exists*]),
    ),
  ),
) <tab:taskb>

The per-variant activity values were never deposited with the preprint. The evidence, all of
it recorded with the attempt log:

- The preprint is still at #num.tb_version after #num.tb_months, and *no journal version
  exists*; the bioRxiv API reports no articles found for a published version.
- *The publisher's own structured metadata declares zero supplementary-material blocks.*
- *#num.tb_searches across Zenodo, Dryad, OSF and GitHub returned nothing*, within
  #num.tb_attempts logged across six route families.
- The DOI in the originating brief, #raw(num.tb_doi_bad), does not resolve; the resolving form is
  #raw(num.tb_doi), and the preprint's own PDF header carries the non-resolving one, so this is a
  defect in the preprint rather than in the brief.

*This is a result about availability, not about representations.* It is reported as the
outcome rather than worked around, because every available workaround, a simulated deep
mutational scan, values digitized from a figure, or a different protein's screen, would
produce numbers indistinguishable in form from real ones and meaningless in content.

== What is ready, and what is therefore not claimed

Everything that does not require the labels was completed and frozen:

- *The reference frame is resolved and confirmed*, at #num.tb_positions, and cross-checked
  against a second independent deposit that encodes it exactly at #num.tb_ref_len of
  #num.tb_ref_len residues while sharing only #num.tb_nt_share of its nucleotides, so the two
  cannot agree by sharing a payload.
- *#num.tb_ids variant identifiers are derived and frozen*, each checked to differ from the
  reference at exactly one position and all mutually distinct.
- *#num.tb_regimes are written and verified* to cover every identifier, test each exactly once,
  and keep train and test disjoint. One is named
  `random_variant_LEAKY_DO_NOT_REPORT.csv` in its filename and in two columns on every row,
  because it controls for nothing and exists only to quantify the optimism a naive split
  buys.
- *A parser that halts rather than adapts.* On any wild-type residue mismatch it reports the
  first ten, tests whether a single constant offset would resolve them, states that offset as
  a finding, and stops without applying it. Ten positive controls require it to refuse,
  including a reference shifted by exactly one residue.

One measurement was possible without labels and was made: 4-mer frequency vectors across the
Task B variants have a median pairwise cosine similarity of #num.tb_cosine, and whole-sequence
physicochemical vectors #num.tb_phys_cosine. Those representations are *degenerate by
construction* on a single-substitution panel, which is why mean pooling would be a labelled
control there and never the primary condition.

== The cross-regime hypothesis is not tested

The pair of tasks was built to bear on one question: do these representations capture local
mutational tolerance within a protein while failing at functional transfer across families?

#notebox[
*That hypothesis is not tested, and this report does not claim it in either direction.* Task
A supplies one half of the contrast, with controls. The other half, that the same
representations do succeed within a protein, is *assumed from the wider literature and is not
measured here*. The tempting sentence, "protein language models capture local mutational
tolerance but not cross-family function, as the contrast between our two tasks shows", *is
not available*. Only one of the two tasks produced a measurement.
]

Three reasons a one-sided result cannot carry the hypothesis, as
`reports/CROSS_TASK_COMPARISON.md` states them:

1. *A null result in one regime is not evidence of success in another.* Task A's finding is
   consistent with the hypothesis, and equally consistent with the representations carrying
   little functional signal in either regime.
2. *Task A's own limits are not resolved.* With #num.n_active positives, a Kish effective
   sample size of #num.kish, #num.zero_active folds holding no active enzyme, and a median
   resolvable composite difference larger than every composite observed, the panel cannot
   distinguish "the representations carry nothing" from "the panel cannot detect what they
   carry". Those have different consequences for the hypothesis.
3. *The regimes differ in more than locality.* Task B's label would be an enrichment ratio
   from a pooled screen; Task A's is a per-enzyme editing percentage from individually
   assayed constructs. A difference in outcome between them would confound representation
   behaviour with assay type, which is the same confound that motivated splitting the tasks.

What would change this: Task B's activity values. With them the contrast becomes measurable.
Until then the repository records a one-sided study honestly, which is better than a
two-sided story with one side imagined.

= Limitations and blocked experiments

== Limitations of the panel and the metric

#figure(
  caption: [Limitations, with values where a value exists. Compiled from `WRITEUP.md`,
  `reports/FINAL_REPORT.md` and `reports/MANUSCRIPT_SUMMARY.md`.],
  btab(
    (1fr, 1.1fr),
    ([limitation], [value or consequence]),
    (
      ([the benchmark cannot resolve its own comparisons], [minimum resolvable composite difference #num.mrd_cls, median #num.mrd_median; every one of the 132 pairwise comparisons is not resolvable]),
      ([exact zeros dominate], [seven of ten representation builds score exactly 0.0000 because weighted Spearman floors at zero]),
      ([one label distribution, one assay], [#num.n_enzymes enzymes measured one way, HEK293T, one target edit]),
      ([positives], [#num.n_active, against #num.n_inactive negatives]),
      ([Kish effective sample size], [#num.kish]),
      ([families with no active enzyme], [#num.zero_active: CRISPR-associated, Other, Unclassified]),
      ([informative folds], [#num.informative of #num.n_families]),
      ([continuous label provenance], [a digitization of Figure S1A, roughly 0.5 percentage point resolution, no error bars recoverable]),
      ([family labels], [inherited 7-way; the paper's 14 classes exist only in a rendered tree image and cannot be checked]),
      ([remote homology], [#num.clust30_cross identity clusters cross a family boundary at 30 percent; no split here removes it]),
      ([accessions], [#num.accessions pinned exactly; the source publishes none]),
      ([pooling and layer], [only final-layer mean pooling was evaluated. No layer or pooling sweep was run, deliberately, because a sweep is a selection decision; a different layer may carry function better and this benchmark does not test that]),
      ([heads], [only two, deliberately. A more flexible head might extract more and would also manufacture more from noise]),
      ([permutation coverage], [6 of the 12 representations, stated rather than silent; all twelve would be 480 protocol runs]),
      ([no PR-AUC search null], [`bench/search_null.py` measures the composite, not precision-recall area. The gap is stated rather than filled with the composite bar, which would compare two different quantities]),
    ),
  ),
) <tab:limitations>

== Blocked experiments

#figure(
  caption: [Experiments that were not run, with each blocker stated as the repository records
  it. *No blocked row was given an estimated, interpolated or literature-quoted score.*],
  btab(
    (auto, auto, 1.5fr),
    ([item], [status], [blocker]),
    (
      ([ProtT5-XL-U50, mean-pooled], [NOT RUN], [`transformers` and `sentencepiece` are not installed and could not be installed in this environment]),
      ([inverse folding: ESM-IF or ProteinMPNN], [NOT RUN], [neither package is installed; ESM-IF needs a geometric deep learning stack with no Python 3.14 wheels on this platform]),
      ([zero-shot ESM-1v masked marginals], [NOT RUN], [about 30 000 forward passes of a 650M parameter model on a CPU-only build of torch]),
      ([ESM-1v mean-pooled], [NOT RUN], [host memory. The first attempt was terminated mid-download by the host memory reaper. At the retry the machine had #num.esm1v_free of #num.esm1v_total available with no jobs of this project running, against roughly 2.6 GB resident for the model weights plus a 2.5 GB download]),
    ),
  ),
) <tab:blocked>

*ESM-1v mean-pooled is the only purely resource-bound row*, and it is therefore the first
thing to rerun on a machine with more memory or a GPU; the embedding cache is keyed by model,
so the other four are not recomputed. Its absence costs one row of the scale series and does
not bear on any conclusion here, because ESM-2 at four scales already spans the model-size
question and every one of those rows has a negative margin against its null (@tab:repr-cls).
The other three rows are missing dependencies rather than missing compute, and none of them
can be estimated from what is in this tree.

= Conclusions

1. *The #num.sub_cls is not a measurement.*
   #correction("2026-10-03")[
   This conclusion previously read that a #(num.de_params)-parameter search reaches #num.k50_p95 on
   noise and that the submitted score does not clear it. *Both halves were wrong in detail.*
   The #num.de_params parameters belong to a different stored artifact scoring
   #num.other_artifact, and at the submission's matched count of #num.comp_n the noise p95 is
   #num.k29_p95, which #num.sub_cls *does* clear by #num.sub_margin.
   ]
   What survives, and is sufficient: that margin is about half the #num.boot_width bootstrap
   interval width on an effective sample of #num.kish2, so it is not distinguishable from
   manufactured score; and the search optimized `compute_cls` directly against its own test
   labels, resuming from its own previous fits. The second half was never in doubt and does
   not depend on the null.

2. *Mean-pooled protein language model embeddings encode lineage and length, not function, on
   this task.* Family accuracy of #num.fam_diag against a #num.fam_major majority baseline,
   rising monotonically with model scale; PC1 to length at Spearman #num.pc1_len; and
   out-of-family composite scores at or below a zero-training length baseline of
   #num.length_cls. The first two measurements use no activity label.

3. *The obvious corrections do not work.* Residualizing length, removing the
   #num.famres_removed family-predictive principal components, pooling over the catalytic core,
   and attention-weighting that pooling all left the composite at 0.0000, and the two
   core-focused variants became *more* lineage-predictive (#num.core_fam, the highest measured),
   not less.

4. *Nothing trained beats a single column of the input file.* The three rows that clear their
   own nulls anywhere in this benchmark are all zero-training baselines, and the two highest
   composite scores in @tab:ladder fit nothing at all.

5. *The real limit is $n$, and the real problem may be the metric.* With an effective sample
   size of #num.kish and a minimum resolvable difference of #num.mrd_cls composite, this benchmark
   cannot support the comparisons people want to make with it. @tab:scale shows the null
   falling faster with $n$ than any modelling change moved any score, and still sitting at
   about 0.58 at $n = 200$. If the search-capacity null stays high as $n$ grows, *the metric
   should be replaced rather than the panel merely enlarged.*

#block(inset: (x: 0.6cm))[
*The answer, in one sentence.* No: on this #(num.n_enzymes)-enzyme panel, protein language model
representations do not improve reverse transcriptase activity prediction over simpler
biological representations under family-held-out evaluation, and the honest reason is as much
that the panel cannot resolve a difference of the size in question as that the embeddings
encode lineage and length rather than function.
]

Those two explanations are different and this dataset does not separate them. Under the
first, scaling the model is the wrong move and pooling or fine-tuning strategy is the
question. Under the second, the dataset is the bottleneck and no representation study on this
panel will resolve anything. The honest reading is that both contribute, and that the
diagnostic evidence for the first is stronger than the benchmark evidence for it, because the
diagnostics do not depend on the small number of positives.

The contribution is the search-capacity null as routine practice for small-$n$ protein
benchmarks, plus a concrete demonstration that mean-pooled embeddings track lineage rather
than catalysis on a #(num.n_enzymes)-enzyme out-of-family task. *A lower number with an interval,
a null and a mechanism is worth more than a higher number with none of those.*

= Reproducibility

== Entry point

#block(inset: (x: 0.6cm))[`python reproduce.py`]

Retrains everything from `data/` and reads no stored result. Seed 42 throughout. The nine
stages are, in order: the protocol tests including the peeking positive control; the
search-null instrument self-check; the leakage audit of the inherited tree; the metric
properties at $n = #num.n_enzymes$; embedding extraction; the search-capacity null sweep; the
baseline ladder; the representation benchmark; and the scale projection. Each runs as a
subprocess so a failure names the stage that failed. `python reproduce.py --quick` skips the
two multi-hour stages, which are the null sweep and the embedding extraction.

The Task A manuscript pipeline is driven through the Makefile targets recorded in
`reports/FINAL_REPORT.md`:

#block(inset: (x: 0.6cm), raw(
"make pipeline-taskA-source      # fetch Table S1, inventory every sheet
make pipeline-taskA-parse       # parse the assayed block, reconcile, curate
make pipeline-clusters          # identity clustering at 90, 70, 50, 30
make pipeline-taskA-overview    # descriptive statistics and figures
make pipeline-splits            # freeze and verify the splits
make pipeline-features          # handcrafted features and the mask
make pipeline-taskA-embeddings  # ESM-2 at four sizes, then the diagnostics
python bench/representations_taskA.py
python bench/validate_taskA.py --stage all
python bench/interpret_taskA.py
python reports/build_final_report.py",
  block: true,
))

#notebox[
*The Makefile is untested, stated rather than implied.* `make` was not available on the
machine these results were produced on, so `reproduce.py` is the entry point that has
actually been exercised. It is also not equivalent to `reproduce.py`, which is worth stating
because the repository's prose says it is: the `reproduce` target runs `test`, `selfcheck`,
`audit`, `embeddings`, then the baseline ladder, the representation benchmark and the scale
projection, and it never invokes `bench/search_null.py`. *The Makefile target omits the
search-capacity null sweep*, which is the project's central instrument. Use `reproduce.py`.
]

This PDF is built by `reports/build_pdf.py`, which reads the result files, generates
`reports/_report_data.typ`, compiles this document, and writes
`reports/REPORT_NUMBER_AUDIT.md`. It *refuses to build* if any quoted figure cannot be found
in the repository file that is named as its source, so the traceability claim is enforced
mechanically rather than promised.

== Environment

Every number in this document was produced in this environment:

#figure(
  caption: [The environment of record.],
  btab(
    (auto, 1fr),
    ([component], [version]),
    (
      ([Python], [#num.py_ver on Windows 11]),
      ([numpy], [#num.numpy_ver]),
      ([scipy], [#num.scipy_ver @scipy]),
      ([pandas], [#num.pandas_ver]),
      ([scikit-learn], [#num.sklearn_ver @sklearn]),
      ([matplotlib], [#num.mpl_ver]),
      ([torch], [#num.torch_ver, *zero CUDA devices*]),
      ([fair-esm], [#num.esm_ver @lin2023]),
      ([MMseqs2], [`easy-cluster`, commit #raw(num.mmseqs_commit) @mmseqs2]),
      ([seed], [42 throughout]),
    ),
  ),
) <tab:env>

== One reproducibility caveat <caveat>

`data/esm2_embeddings.npz` is inherited and *no script in this tree generates it*. It cannot
be reproduced from this repository.

The rebuild's representation results do not depend on it, because `bench/embeddings.py`
regenerates ESM-2 embeddings from `data/rt_sequences.csv` into `bench/cache/`, and
@tab:repr-cls is computed from that cache. But the repository's prose claims more than that,
and the stronger claim is false: #raw(num.npz_loader) loads the inherited file
*unconditionally*, and two published rows of the baseline ladder are fed by it, the
amino-acid-composition PC1 baseline and the raw-ESM-2-plus-logistic-regression row. Both
score 0.0000, so no conclusion in this report moves either way, but *deleting the file would
break the baseline ladder rather than leave it unaffected*. The accurate statement is the
narrow one: the representation results do not depend on the inherited artifact, the ladder
does, and the artifact itself cannot be regenerated from this tree.

#pagebreak()

#set heading(numbering: none)

= References

#bibliography("refs.yml", title: none, style: "ieee")

= Appendix A: full result tables as generated <app:tables>

#notebox[
*Every result file is reproduced in full here, split by metric.* Each of the two result
files behind #link(<ladder>)[sections 5.1] and #link(<clsresults>)[5.2] holds a composite
column and a precision-recall column. They are printed as two tables each rather than one,
so that no table in this report places a composite value beside a precision-recall value.
Within one of those files the two are the *components of one composite under one analysis*:
the composite is their harmonic mean. A precision-recall value from @tab:ladder-pr or
@tab:repr-pr-app is *not* comparable with one from @tab:repr-pr, because the feature tables,
the candidate grids and the inner-selection criteria all differ
(#link(<two>)[section 5.7]).
]

#figure(
  caption: [`bench/results/baseline_ladder.json`, composite metric, all nine rows in file
  order. CI is the percentile bootstrap on the composite. Margin is the score minus the null
  p95 at that row's own free-parameter count.],
  btab(
    (1.6fr, auto, auto, auto, auto, auto, auto),
    ([method], [CLS], [wSpear.], [CLS 95% CI], [null mean], [null p95], [margin]),
    t_ladder_cls,
    aligns: (left, right, right, center, right, right, right),
    size: 7.8pt,
  ),
) <tab:ladder-cls>

#figure(
  caption: [`bench/results/baseline_ladder.json`, the precision-recall component of the same
  nine rows, with wall-clock seconds. This column is the separation term whose harmonic mean
  with the weighted Spearman term of @tab:ladder-cls gives that table's composite. It is not
  the same quantity as @tab:repr-pr.],
  btab(
    (1.6fr, auto, auto, auto, auto),
    ([method], [kind], [selected], [PR-AUC], [seconds]),
    t_ladder_pr,
    aligns: (left, left, right, right, right),
    size: 7.8pt,
  ),
) <tab:ladder-pr>

#figure(
  caption: [`bench/results/representations.json`, composite metric, all ten rows in file
  order.],
  btab(
    (1.6fr, auto, auto, auto, auto, auto, auto),
    ([representation], [CLS], [wSpear.], [CLS 95% CI], [null p95], [margin], [fam. acc.]),
    t_reps_cls,
    aligns: (left, right, right, center, right, right, right),
    size: 7.8pt,
  ),
) <tab:repr-cls-app>

#figure(
  caption: [`bench/results/representations.json`, the precision-recall component of the same
  ten rows. Same caveat as @tab:ladder-pr: this is a component of @tab:repr-cls-app's
  composite, not a value comparable with @tab:repr-pr.],
  btab(
    (1.6fr, auto, auto, auto),
    ([representation], [features], [PR-AUC], [seconds]),
    t_reps_pr,
    aligns: (left, right, right, right),
    size: 7.8pt,
  ),
) <tab:repr-pr-app>

#figure(
  caption: [`bench/results/taskA_representations.json` and `taskA_validation.json`, composite
  metric under the *classification* head, ordered by score. The bar is the matched
  $K = #num.free_params$ search-capacity null p95 of #num.k1_p95; margin is the score minus the
  larger of the noise control and that bar. *No row clears it.*],
  btab(
    (1fr, auto, auto, auto, auto, auto),
    ([representation], [CLS], [95% CI], [noise CLS], [search null p95], [margin]),
    t_cls_class,
    aligns: (left, right, center, right, right, right),
  ),
) <tab:cls-class>

#figure(
  caption: [The same under the *regression* head. Every value here inherits the Figure S1A
  digitization described in #link(<labels>)[section 2.2].],
  btab(
    (1fr, auto, auto, auto, auto, auto),
    ([representation], [CLS], [95% CI], [noise CLS], [search null p95], [margin]),
    t_cls_reg,
    aligns: (left, right, center, right, right, right),
  ),
) <tab:cls-reg>

#figure(
  caption: [Label permutation, #num.n_perm repeats, composite metric. Both labels are permuted
  together inside the protocol so their pairing with each other survives and only their
  pairing with the sequences is broken. From `bench/results/taskA_validation.json`, key
  `permutation`.],
  btab_mark(
    (auto, auto, auto, auto, auto, auto, auto),
    ([representation], [head], [permuted mean], [permuted p95], [permuted max], [observed], [above p95]),
    t_perm_cls,
    aligns: (left, left, right, right, right, right, center),
  ),
) <tab:perm-cls>

#figure(
  caption: [Label permutation, #num.n_perm repeats, precision-recall area. Kept in a separate
  table from @tab:perm-cls so that no row mixes the two metrics. The `kmer4` classification
  row is the only one in either table that both clears its permutation and clears its noise
  control and chance.],
  btab_mark(
    (auto, auto, auto, auto, auto, auto, auto),
    ([representation], [head], [permuted mean], [permuted p95], [permuted max], [observed], [above p95]),
    t_perm_pr,
    aligns: (left, left, right, right, right, right, center),
  ),
) <tab:perm-pr>

#figure(
  caption: [`bench/results/search_null.json`, the full $K$ sweep including the $K = 1$ and
  $K = 2$ rows omitted from @tab:ksweep, and the budget sweep at $K = 29$. Reproduced for
  completeness; the body of @tab:ksweep is identical.],
  btab(
    (auto, auto, auto, auto, auto, auto, auto),
    ([$K$], [repeats], [mean], [sd], [p95], [min], [max]),
    t_ksweep,
    aligns: (right, right, right, right, right, right, right),
  ),
) <tab:ksweep-full>

= Appendix B: figure index with provenance

#figure(
  caption: [Every figure embedded in this report, with the script that generated it. No
  figure was redrawn, cropped or rescaled for this document; each is embedded as the
  generating script wrote it.],
  btab(
    (auto, 1fr, 1fr),
    ([figure], [file], [generated by]),
    (
      ([@fig:capacity], [`bench/figures/search_null_capacity.png`], [`bench/search_null.py`]),
      ([@fig:ladder], [`audit/figures/cls_ladder.png`], [`audit/leakage_audit.py`]),
      ([@fig:funclin], [`bench/figures/function_vs_lineage.png`], [`bench/representations.py`]),
      ([@fig:null], [`reports/figures/taskA_null_comparison.png`], [`bench/figures_taskA.py`]),
      ([@fig:repcomp], [`reports/figures/taskA_representation_comparison.png`], [`bench/figures_taskA.py`]),
      ([@fig:emblen], [`reports/figures/taskA_embedding_by_length.png`], [`embeddings/representation_diagnostics_taskA.py`]),
      ([@fig:pclen], [`reports/figures/taskA_pc_length_correlation.png`], [`embeddings/representation_diagnostics_taskA.py`]),
      ([@fig:embfam], [`reports/figures/taskA_embedding_by_family.png`], [`embeddings/representation_diagnostics_taskA.py`]),
      ([@fig:embact], [`reports/figures/taskA_embedding_by_activity.png`], [`embeddings/representation_diagnostics_taskA.py`]),
    ),
  ),
) <tab:figindex>

Four further figures exist in the repository and are not embedded here, because the tables in
#link(<dataset>)[section 2] and @tab:limitations already carry their underlying numbers:
`taskA_family_composition.png`, `taskA_activity_by_family.png`, `taskA_length_by_family.png`
and `taskA_efficiency_among_actives.png` (all from `curation/dataset_overview_taskA.py`),
along with `taskA_failure_by_family.png` and `taskA_error_vs_length.png` (from
`bench/interpret_taskA.py`).

All embedded figures were written by matplotlib at 150 or 200 dots per inch, between 1350 and
2393 pixels wide, which is between 6.8 and 12 inches of print width at their native
resolution. Every one is embedded at or below its native width, so *none was upscaled*.

= Appendix C: data integrity

#figure(
  caption: [Checksums and frozen artifacts.],
  btab(
    (auto, 1fr),
    ([artifact], [digest or state]),
    (
      ([`tasks/taskA_crossfamily/curated.csv`], [SHA256 #sha(num.curated_sha)]),
      ([`tasks/taskA_crossfamily/raw/mmc2.xlsx`], [SHA256 #sha(num.workbook_sha)]),
      ([`tasks/taskB_mmlv_dms/reference.fasta`], [SHA256 #sha("070b5df7e3d6248f9dbd4213060f2d2cab9691a450a50e0de1281930f8f33cd7") #num.tb_ref_len residues]),
      ([`tasks/taskB_mmlv_dms/curated.csv`], [*absent*, blocked on the activity values]),
      ([Task A primary split], [`splits/leave_one_family_out.csv`, #num.n_families folds, asserted to reproduce the partition the harness derives at run time]),
      ([Task A secondary split], [leave-one-cluster-out at 70 percent identity, 49 folds]),
      ([Task B frozen splits], [`position_held_out.csv`, `stretch_held_out.csv`, `aa_held_out.csv`, `random_variant_LEAKY_DO_NOT_REPORT.csv`]),
      ([sequence integrity], [all #num.n_enzymes sequences byte-identical by SHA256 to Table S1; 0 mismatches; length column agrees with `len(sequence)` on every row]),
    ),
  ),
) <tab:integrity>

== Recorded defects

#figure(
  caption: [Defects found and recorded. The first changed a reported conclusion
  (#link(<defect>)[section 7]); the rest are recorded so that a later reader does not
  rediscover them as surprises.],
  btab(
    (1fr, 1.3fr),
    ([defect], [state]),
    (
      ([`topology_features.csv` omits the `-RT` suffix that `rt_sequences.csv` carries], [a join on `rt_name` matched zero rows and fed nine empty columns into the feature table with no error raised. Repaired; `bench/names.py` now asserts full coverage and fails loudly. Moved handcrafted + RandomForest from #num.rf_before to #num.rf_cls]),
      ([`Line1-RT` has no predicted structure], [recorded in `bench/names.py` as an allowed omission rather than silently imputed]),
      ([`Vp-96.pdb` duplicates `Vp96-RT.pdb`], [#num.n_struct files cover 56 distinct enzymes. Recorded in `bench/names.py`]),
      ([pre-repair precision-recall and weighted Spearman values left beside post-repair composite values in `WRITEUP.md` and `PROGRESS.md`], [superseded values listed in `reports/REPORT_NUMBER_AUDIT.md`; this report takes @tab:ladder from the result file]),
      ([`reports/split_design.md` claimed no identity cluster crosses a family boundary "at any threshold"], [false at 30 percent identity, where #num.clust30_cross do. Corrected in place in both affected documents with the original wording quoted]),
      ([`pe_efficiency_pct` has no verifiable published source], [attributed to Figure S1A and carried with the literal marker `UNVERIFIED_DIGITIZED`. See #link(<labels>)[section 2.2]]),
      ([`Retron86-RT` is wholly contained in `retronE,coli-RT`], [the same sequence excised at two boundaries; both inactive, so no contradictory labels, but the panel holds fewer independent observations than its row count suggests]),
      ([`data/esm2_embeddings.npz` is inherited and not regenerable from this tree], [loaded unconditionally by #raw(num.npz_loader); two published baseline-ladder rows are fed by it, both scoring 0.0000. See #link(<caveat>)[section 13.3]]),
      ([the brief's Task B DOI #raw(num.tb_doi_bad) does not resolve], [the resolving form is #raw(num.tb_doi); the preprint's own header carries the non-resolving one]),
    ),
  ),
) <tab:defects>

#v(1em)

#notebox[
*Every number in this report is traceable.* `reports/REPORT_NUMBER_AUDIT.md` lists each one
with the file it came from and either the JSON key path it was computed from or the exact
string the build verified in the named document. The build fails rather than producing this
PDF if any of those checks does not pass.
]
