/**
 * Builds presentation/RT_PLM_Benchmark_Presentation.pptx
 *
 * Run:  node presentation/build_deck.js      (from the repository root)
 *
 * Every figure referenced here is produced by presentation/make_figures.py from
 * committed result artifacts. Every number on a slide is traced in that slide's
 * speaker notes to the file it came from.
 */

const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "reports", "figures", "presentation");
const OUT = path.join(__dirname, "RT_PLM_Benchmark_Presentation.pptx");

/* ---------------------------------------------------------------- tokens */

const INK = "1F1F1F";
const MUTED = "6B6B6B";
const ACCENT = "2C6E7F";
const ALERT = "B85450";
const PANEL = "FAF9F6";
const TINT = "EEF2F3";
const RULE = "C4C4C4";
const BG = "FFFFFF";

const SERIF = "Georgia";
const SANS = "Calibri";
const BODY = "Times New Roman";

const W = 16;
const H = 9;
const M = 0.9;
const CW = W - 2 * M;

const pres = new pptxgen();
pres.defineLayout({ name: "T16x9", width: W, height: H });
pres.layout = "T16x9";
pres.author = "Tanish N.";
pres.title = "Benchmarking protein language models for reverse transcriptase activity prediction";

/* --------------------------------------------------------------- helpers */

function newSlide() {
  const s = pres.addSlide();
  s.background = { color: BG };
  return s;
}

function text(slide, body, opts) {
  slide.addText(body, Object.assign({ isTextBox: true, margin: 0, valign: "top" }, opts));
}

function eyebrow(slide, label) {
  text(slide, label.toUpperCase(), {
    x: M, y: 0.52, w: CW, h: 0.3,
    fontFace: SANS, fontSize: 14, color: MUTED, charSpacing: 1.4,
  });
}

function heading(slide, title) {
  text(slide, title, {
    x: M, y: 0.88, w: CW, h: 0.82,
    fontFace: SERIF, fontSize: 36, color: INK,
  });
}

function head(slide, label, title) {
  eyebrow(slide, label);
  heading(slide, title);
}

function caption(slide, body, x, y, w) {
  text(slide, body, {
    x: x, y: y, w: w, h: 0.42,
    fontFace: SANS, fontSize: 14, color: MUTED,
  });
}

function prose(slide, body, x, y, w, h, size) {
  text(slide, body, {
    x: x, y: y, w: w, h: h,
    fontFace: BODY, fontSize: size || 24, color: INK, lineSpacingMultiple: 1.12,
  });
}

function bullets(slide, items, x, y, w, h, size) {
  const runs = items.map((t, i) => ({
    text: t,
    options: {
      bullet: true,
      breakLine: i < items.length - 1,
      paraSpaceAfter: 10,
      fontFace: BODY,
      fontSize: size || 22,
      color: INK,
    },
  }));
  text(slide, runs, { x: x, y: y, w: w, h: h });
}

function hairline(slide, x, y, w) {
  slide.addShape(pres.ShapeType.line, {
    x: x, y: y, w: w, h: 0,
    line: { color: RULE, width: 0.75 },
  });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    rectRadius: 0.1,
    fill: { color: fill || PANEL },
    line: { color: RULE, width: 1 },
  });
}

function divider(slide, kicker, word, summary) {
  text(slide, kicker.toUpperCase(), {
    x: M, y: 3.0, w: CW, h: 0.34,
    fontFace: SANS, fontSize: 14, color: ACCENT, charSpacing: 1.6,
  });
  text(slide, word, {
    x: M, y: 3.42, w: CW, h: 1.5,
    fontFace: SERIF, fontSize: 72, color: INK,
  });
  text(slide, summary, {
    x: M, y: 5.05, w: 10.5, h: 0.5,
    fontFace: SANS, fontSize: 20, color: MUTED,
  });
}

/* ------------------------------------------------------------- 1. title */

{
  const s = newSlide();
  text(s, "Benchmarking protein language models for\nreverse transcriptase activity prediction", {
    x: M, y: 2.5, w: 13.0, h: 1.9,
    fontFace: SERIF, fontSize: 40, color: INK, lineSpacingMultiple: 1.2,
  });
  hairline(s, M, 4.75, 6.4);
  text(s, "Tanish N.", {
    x: M, y: 5.05, w: 10, h: 0.7,
    fontFace: SANS, fontSize: 32, color: INK,
  });
  text(s, "Documentation and presentation: Hemalakshmi P.", {
    x: M, y: 5.85, w: 10, h: 0.4,
    fontFace: SANS, fontSize: 17, color: MUTED,
  });
  text(s, "Intern research presentation   |   7 October 2026   |   github.com/TanishDevs11/RT-plm-benchmark", {
    x: M, y: 7.5, w: 13.5, h: 0.4,
    fontFace: SANS, fontSize: 14, color: MUTED,
  });
  s.addNotes(
    "Budget: 10 seconds.\n\n" +
    "Open with the title and move. Say only: this is a benchmark, and it began as a correction of my own result.\n\n" +
    "Sources: repository name and authorship from README.md Contributors section and CITATION.cff."
  );
}

/* ------------------------------------------------- 2. what an RT is */

{
  const s = newSlide();
  head(s, "Introduction", "What a reverse transcriptase does, and why it matters here");

  const cards = [
    ["THE ENZYME",
     "A reverse transcriptase writes DNA from an RNA template. RTs sit at the centre of retroviruses, retrotransposons, retrons and group II introns."],
    ["THE APPLICATION",
     "A prime editor is a Cas9 nickase fused to an RT. The RT copies the edit encoded in the guide RNA into the genome, so the editor is only as good as its RT."],
    ["THE QUESTION",
     "Assaying a new RT in cells is slow. If activity could be predicted from sequence alone, the search for better prime editors would widen enormously."],
  ];
  const cw = (CW - 2 * 0.5) / 3;
  cards.forEach((c, i) => {
    const x = M + i * (cw + 0.5);
    card(s, x, 2.2, cw, 4.2);
    text(s, c[0], {
      x: x + 0.45, y: 2.6, w: cw - 0.9, h: 0.34,
      fontFace: SANS, fontSize: 17, color: ACCENT, charSpacing: 1.2,
    });
    prose(s, c[1], x + 0.45, 3.1, cw - 0.9, 3.0, 20);
  });
  caption(s, "Panel source: Doman et al. 2023, Cell 186(18):3983-4002.e26, the prime editor survey this benchmark's dataset comes from.", M, 6.75, CW);

  s.addNotes(
    "Budget: 35 seconds.\n\n" +
    "Three sentences, one per card, then move. An RT writes DNA from RNA. A prime editor is Cas9 nickase plus an RT, so RT activity sets the ceiling on editing. Measuring every candidate RT in cells is slow, which is why a sequence-only predictor would be valuable.\n\n" +
    "No figures on this slide. Dataset attribution: reports/doman2023_source_facts.md and tasks/taskA_crossfamily/PROVENANCE.md.\n" +
    "If running late, this is one of the three slides to compress (2, 3, 5). Never cut from 10 to 12."
  );
}

/* ----------------------------------------------- 3. the dataset and task */

{
  const s = newSlide();
  head(s, "Motivation", "The challenge, and the panel it is scored on");

  const stats = [
    ["57", "reverse transcriptases\nassayed in HEK293T"],
    ["21", "active under the\nprime editing assay"],
    ["7", "evolutionary families,\nfrom 1 to 18 members"],
  ];
  const sw = 3.05;
  stats.forEach((st, i) => {
    const x = M + i * (sw + 0.45);
    text(s, st[0], {
      x: x, y: 2.15, w: sw, h: 1.35,
      fontFace: SERIF, fontSize: 72, color: ACCENT,
    });
    text(s, st[1], {
      x: x, y: 3.55, w: sw, h: 0.9,
      fontFace: SANS, fontSize: 17, color: INK,
    });
  });

  card(s, M + 3 * (sw + 0.45), 2.15, CW - 3 * (sw + 0.45), 2.6, TINT);
  text(s, "THE TASK AS POSED", {
    x: M + 3 * (sw + 0.45) + 0.4, y: 2.5, w: 2.6, h: 0.32,
    fontFace: SANS, fontSize: 14, color: ACCENT, charSpacing: 1.2,
  });
  prose(s, "Rank and classify which RTs are active, from amino acid sequence alone.",
    M + 3 * (sw + 0.45) + 0.4, 2.95, CW - 3 * (sw + 0.45) - 0.8, 1.6, 20);

  hairline(s, M, 5.25, CW);
  prose(s,
    "The panel is small and strongly structured by lineage: positive prevalence is 0.3684, the weighted Spearman term has a Kish effective sample size of 11.34, and three of the seven held-out families contain no active enzyme at all.",
    M, 5.6, CW, 1.3, 24);
  caption(s, "Counts and sequences: Doman et al. 2023 Table S1, redistributed under CC BY 4.0 in tasks/taskA_crossfamily/.", M, 7.1, CW);

  s.addNotes(
    "Budget: 35 seconds.\n\n" +
    "57 enzymes, 21 active, 7 families. The task is to say which are active from sequence. The sentence that matters is the last one: with 21 positives, an effective sample size of 11.34, and three folds holding no positives, this dataset can be overfitted without anyone noticing.\n\n" +
    "Sources for every number here:\n" +
    "  57, 21, 7 families and prevalence 0.3684: README.md Dataset section, tasks/taskA_crossfamily/curated.csv, reports/dataset_overview.md\n" +
    "  Kish effective sample size 11.34: reports/statistical_validation.md\n" +
    "  three folds with no active: bench/results/taskA_representations.md, per-family breakdown (CRISPR-associated, Other, Unclassified)\n" +
    "  Table S1 counts versus the article prose, 59 and 20: reports/reconciliation.md\n" +
    "Compressible slide if time is short."
  );
}

/* ------------------------------------------------------------- 4. hook */

{
  const s = newSlide();
  head(s, "Motivation", "A 0.975 that did not survive its own audit");

  text(s, "0.9754", {
    x: M, y: 2.05, w: 6.0, h: 1.5,
    fontFace: SERIF, fontSize: 72, color: ALERT,
  });
  text(s, "COMPETITION SCORE, SINCE WITHDRAWN AS A RESULT", {
    x: M, y: 3.5, w: 6.0, h: 0.34,
    fontFace: SANS, fontSize: 14, color: MUTED, charSpacing: 1.2,
  });
  bullets(s, [
    "The search optimized the competition metric directly over all 57 labels, with 29 blend weights plus an exponent, reseeding from its own fitted constants.",
    "Twenty commits quote a CLS: 0.4380 climbing to 0.9754.",
    "Run that same search on pure noise at the matched 29 parameters and it reaches a 95th percentile of 0.9340.",
  ], M, 4.1, 6.0, 3.1, 19);

  s.addImage({ path: path.join(FIG, "hill_climb.png"), x: 7.4, y: 2.1, w: 7.7, h: 4.3 });
  caption(s, "Reported CLS per commit, parsed from the audit's commit ladder. This is a record of optimization, not of generalization.", 7.4, 6.55, 7.7);

  s.addNotes(
    "Budget: 45 seconds. This is the hook: lead with it, state it plainly, do not apologise.\n\n" +
    "Script: I submitted a 0.975. Then I audited my own pipeline and found the score was produced by optimizing the metric against the very labels it was scored on. The curve on the right is twenty commits of hill climbing. The honest statement is that at the matched 29 free parameters the same procedure reaches 0.9340 on pure noise, and the gap, plus 0.0414, is about half the bootstrap interval width of 0.0794. So the submitted score is not distinguishable from what the search manufactures from nothing. Everything after this slide is the rebuild.\n\n" +
    "Sources:\n" +
    "  0.9754, the 29 free parameters, the reseeding and the 20-commit ladder from 0.4380: audit/leakage_report.md sections 1 to 3, legacy_leaky/fast_opt.py\n" +
    "  null p95 0.9340 at K=29, and 0.9727 at K=50: bench/results/search_null.json, k_sweep\n" +
    "  margin +0.0414 against bootstrap width 0.0794: README.md, section Why the previously reported 0.975 is not a result\n" +
    "  figure: reports/figures/presentation/hill_climb.png, built by presentation/make_figures.py from audit/leakage_report.md"
  );
}

/* --------------------------------------------------------- 5. PLM primer */

{
  const s = newSlide();
  head(s, "Background", "What a protein language model gives you");

  const boxes = [
    ["AMINO ACID SEQUENCE", "TLNIEDEYRLHETSKEPDVSLGSTWLSDFPQAWAETGGMGLAVRQAPLIIPLKA...\n\nM-MLV RT reference, first 54 of 498 residues"],
    ["ESM-2, FROZEN", "A transformer trained on millions of unlabelled protein sequences, 8M to 650M parameters"],
    ["EMBEDDING VECTOR", "320 to 1280 numbers per protein, mean-pooled over residues"],
    ["SIMPLE HEAD", "Regularized logistic regression, one free parameter"],
  ];
  const bw = 3.25;
  const gap = 0.42;
  boxes.forEach((b, i) => {
    const x = M + i * (bw + gap);
    card(s, x, 2.35, bw, 2.35);
    text(s, b[0], {
      x: x + 0.3, y: 2.65, w: bw - 0.6, h: 0.6,
      fontFace: SANS, fontSize: 17, color: ACCENT,
    });
    text(s, b[1], {
      x: x + 0.3, y: 3.3, w: bw - 0.6, h: 1.1,
      fontFace: SANS, fontSize: 14, color: INK,
    });
    if (i < boxes.length - 1) {
      s.addShape(pres.ShapeType.rightArrow, {
        x: x + bw + 0.06, y: 3.33, w: gap - 0.12, h: 0.4,
        fill: { color: RULE }, line: { color: RULE, width: 0 },
      });
    }
  });

  hairline(s, M, 5.3, CW);
  prose(s,
    "The expectation is that pretraining on evolutionary sequence data encodes the structural and functional constraints a handcrafted feature set would miss. This benchmark tests that expectation rather than assuming it.",
    M, 5.65, CW, 1.4, 24);

  s.addNotes(
    "Budget: 30 seconds.\n\n" +
    "An embedding is just a fixed-length vector summarising a sequence, produced by a model that never saw an activity label. The hope is that it carries functional constraint. We keep the head deliberately trivial, so that what we are measuring is the representation, not a modelling search.\n\n" +
    "Sources: model scales 8M, 35M, 150M, 650M and the 320 to 1280 dimensions: embeddings/MANIFEST_TASKA.json and bench/results/taskA_representations.md feature counts. Head and single free parameter: bench/protocol.py and README.md Evaluation Protocol.\n" +
    "Compressible slide if time is short."
  );
}

/* ------------------------------------------------------- 6. part 01 */

{
  const s = newSlide();
  divider(s, "Part 01", "Design", "How the rebuild is constructed, and what it refuses to let itself do");
  s.addNotes("Budget: 5 seconds. Say the word and move on.");
}

/* ---------------------------------------------------- 7. system design */

{
  const s = newSlide();
  head(s, "System design", "The pipeline, end to end");

  const stages = [
    ["SOURCE AND CURATION", "Doman 2023 Table S1, 57 RTs verified by SHA256, splits frozen on disk"],
    ["REPRESENTATIONS", "12 in all: length, composition, k-mers, handcrafted, structure, ESM-2"],
    ["NESTED LOFO", "7 outer folds, inner grid of 6, training families only"],
    ["CONTROLS", "Noise, label permutation, search-capacity null, bootstrap"],
    ["REPORTED RESULT", "Pooled once over all 57 rows, with its null and its interval"],
  ];
  const gap = 0.5;
  const bw = (CW - (stages.length - 1) * gap) / stages.length;
  stages.forEach((st, i) => {
    const x = M + i * (bw + gap);
    card(s, x, 2.3, bw, 1.6);
    text(s, st[0], {
      x: x + 0.15, y: 2.3, w: bw - 0.3, h: 1.6,
      fontFace: SANS, fontSize: 17, color: ACCENT, align: "center", valign: "middle",
    });
    text(s, st[1], {
      x: x, y: 4.05, w: bw, h: 1.35,
      fontFace: SANS, fontSize: 14, color: MUTED, align: "center",
    });
    if (i < stages.length - 1) {
      s.addShape(pres.ShapeType.rightArrow, {
        x: x + bw + 0.06, y: 2.95, w: gap - 0.12, h: 0.3,
        fill: { color: RULE }, line: { color: RULE, width: 0 },
      });
    }
  });

  card(s, M, 5.75, CW, 1.5, TINT);
  prose(s,
    "Nothing downstream of the split definition can see a held-out label. The split files are frozen on disk, and a test asserts that the frozen file still equals the partition the harness derives at run time.",
    M + 0.5, 6.15, CW - 1.0, 1.0, 24);

  s.addNotes(
    "Budget: 55 seconds.\n\n" +
    "Walk the six boxes left to right in one pass. Spend the time on the last two: controls and the reporting rule. Then read the panel at the bottom.\n\n" +
    "Sources:\n" +
    "  57 sequences byte-identical by SHA256: tasks/taskA_crossfamily/raw/CHECKSUMS.txt, reports/reconciliation.md\n" +
    "  12 representations, 7 outer folds, inner grid of 6 regularization strengths: bench/results/taskA_representations.md, bench/protocol.py\n" +
    "  frozen splits equal the derived partition: reports/split_verification.md, curation/verify_splits_taskA.py\n" +
    "  the controls: bench/search_null.py, bench/results/representations.json"
  );
}

/* ------------------------------------------ 8. stack and evaluation design */

{
  const s = newSlide();
  head(s, "System design", "Stack, and the evaluation design that does the work");

  const colW = (CW - 0.6) / 2;
  card(s, M, 2.2, colW, 4.6);
  text(s, "TECH STACK", {
    x: M + 0.5, y: 2.6, w: colW - 1.0, h: 0.34,
    fontFace: SANS, fontSize: 17, color: ACCENT, charSpacing: 1.2,
  });
  bullets(s, [
    "Python 3.14.2, numpy 2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0",
    "torch 2.11.0+cpu with zero CUDA devices, fair-esm 2.0.0 for ESM-2",
    "Seed 42 throughout; every script prints its seed and library versions",
    "Continuous integration runs the protocol tests on every push",
  ], M + 0.5, 3.15, colW - 1.0, 3.3, 19);

  card(s, M + colW + 0.6, 2.2, colW, 4.6);
  text(s, "EVALUATION DESIGN", {
    x: M + colW + 1.1, y: 2.6, w: colW - 1.0, h: 0.34,
    fontFace: SANS, fontSize: 17, color: ACCENT, charSpacing: 1.2,
  });
  bullets(s, [
    "Nested leave-one-family-out: the inner loop sees training families only",
    "Frozen splits, out-of-fold predictions pooled once over all 57 rows",
    "10000 bootstrap resamples for every interval",
    "A deliberate peeking positive control the leakage check must reject, so a green suite cannot mean the check is inert",
  ], M + colW + 1.1, 3.15, colW - 1.0, 3.3, 19);

  caption(s, "Live walkthrough of the repository follows this slide.", M, 7.05, CW);

  s.addNotes(
    "Budget: 45 seconds, then the 90 second live walkthrough.\n\n" +
    "Read the right column, not the left. The load-bearing item is the last one: the peeking positive control. A leakage check that always passes is worthless, so we wrote a test that deliberately peeks and requires the check to catch it.\n\n" +
    "LIVE WALKTHROUGH SCRIPT, 90 seconds, runs here, before the Results divider. Keep to four stops and do not browse:\n" +
    "  1. 15s. Repository root. Point at tasks/, bench/, audit/, legacy_leaky/. Say: the quarantined inherited code lives in legacy_leaky and cannot enter any results table.\n" +
    "  2. 30s. Open bench/test_protocol.py. Show the label-corruption test and the deliberate peeking positive control that must fail. Say: this is the test that makes the suite mean something.\n" +
    "  3. 25s. Open bench/results/baseline_ladder.md. Point at the null p95 and margin columns. Say: every row carries its own null.\n" +
    "  4. 20s. Open reports/figures/presentation/search_capacity_null.png, which is the next slide. Hand straight over to it.\n" +
    "If anything is slow to load, abandon the stop and move on. The slides carry the argument on their own.\n\n" +
    "Sources: library versions and seed: README.md Reproducibility section, bench/results/search_null.json versions block. 10000 resamples and the nested design: bench/protocol.py, README.md Evaluation Protocol. Peeking positive control: bench/test_protocol.py."
  );
}

/* ------------------------------------------------------- 9. part 02 */

{
  const s = newSlide();
  divider(s, "Part 02", "Results", "What the instrument measured once the leakage was removed");
  s.addNotes("Budget: 5 seconds. Say the word and move on.");
}

/* ------------------------------------------- 10. leakage and the null */

{
  const s = newSlide();
  head(s, "Results", "How much score a search can manufacture from nothing");

  bullets(s, [
    "Run the selection procedure, unchanged, on K vectors of pure Gaussian noise. Record the score it reaches.",
    "At the matched 29 free parameters the null reaches 0.9340 at the 95th percentile.",
    "The submitted 0.9754 sits 0.0414 above that, against a bootstrap interval 0.0794 wide: not distinguishable from noise, in either direction.",
    "At the one free parameter the rebuilt benchmark uses, the bar is 0.4433.",
  ], M, 2.2, 5.1, 4.6, 19);

  s.addImage({ path: path.join(FIG, "search_capacity_null.png"), x: 6.3, y: 2.1, w: 8.8, h: 4.78 });
  caption(s, "Search-capacity null, 10 repeats per K, differential evolution budget 260. Source: bench/results/search_null.json.", 6.3, 7.0, 8.8);

  s.addNotes(
    "Budget: 70 seconds. This slide carries the central argument. Do not rush it.\n\n" +
    "Script: the instrument is simple. Take the selection procedure, change nothing, and give it pure noise instead of features. Whatever score it reaches is what the procedure can manufacture at this sample size. The teal curve is that score against the number of free parameters. The red line is the submitted 0.975. At 29 parameters, the count the submission actually used, the null reaches 0.934. The submission sits a little above it, by 0.0414, which is about half the width of its own bootstrap interval, so it is not distinguishable from the null. The important consequence is at the left edge: the rebuilt benchmark fits one free parameter, so its bar is 0.4433, and every score in the next slide has to clear that.\n\n" +
    "Sources:\n" +
    "  null p95 values 0.4433 at K=1 and 0.9340 at K=29, 10 repeats, budget 260: bench/results/search_null.json, k_sweep\n" +
    "  submitted 0.9754, margin +0.0414, bootstrap width 0.0794: audit/leakage_report.md and README.md\n" +
    "  0.4433 as the gate for the rebuilt benchmark: reports/statistical_validation.md, line 21\n" +
    "  figure: reports/figures/presentation/search_capacity_null.png"
  );
}

/* ------------------------------------------------- 11. baseline ladder */

{
  const s = newSlide();
  head(s, "Results", "Nothing learned beats a number already in the file");

  bullets(s, [
    "Protein length, used directly as the score with no training at all, reaches CLS 0.4416.",
    "The best protein language model row, ESM-2 150M mean-pooled, reaches 0.3052.",
    "Every bar sits below the red tick, its own search-capacity null, so none has demonstrated signal.",
    "The median minimum resolvable CLS difference is 0.4816, larger than every score here: the ordering itself is not resolvable at this sample size.",
  ], M, 2.1, 4.3, 4.9, 18);

  s.addImage({ path: path.join(FIG, "baseline_ladder.png"), x: 5.5, y: 1.95, w: 9.6, h: 5.17 });
  caption(s, "All rows out of fold under the frozen nested leave-one-family-out split. Sources: bench/results/baseline_ladder.json and bench/results/representations.json.", 5.5, 7.25, 9.6);

  s.addNotes(
    "Budget: 55 seconds.\n\n" +
    "Script: this is the ladder under the honest split. Every row is nested leave-one-family-out, pooled out of fold over all 57 rows. The highlighted bar is protein length with no training whatsoever, at 0.4416. Nothing trained beats it. The best language model representation reaches 0.3052. And the red ticks are each row's own search-capacity null, so strictly speaking no row here has demonstrated signal at all. One more honesty point: the minimum difference this panel can resolve is 0.4816, which is larger than every bar, so please do not read the ordering as a ranking.\n\n" +
    "Sources, every number on this slide:\n" +
    "  0.4416 protein length, 0.4576 3-mer cosine, 0.4284 handcrafted + random forest, 0.4160 family prior, 0.1802 handcrafted + extra trees, 0.0000 raw ESM-2 + logistic regression, with their intervals and null p95 values: bench/results/baseline_ladder.json and bench/results/baseline_ladder.md\n" +
    "  0.3052 ESM-2 150M mean-pooled, null p95 0.4914: bench/results/representations.json and bench/results/representations.md\n" +
    "  median minimum resolvable CLS difference 0.4816: reports/statistical_validation.md\n" +
    "  figure: reports/figures/presentation/baseline_ladder.png"
  );
}

/* ------------------------------------------ 12. lineage, not function */

{
  const s = newSlide();
  head(s, "Results", "The embeddings encode lineage and length, not activity");

  bullets(s, [
    "ESM-2 650M classifies RT family at 0.8197 accuracy against a 0.3214 majority baseline, and accuracy rises with scale: 0.7652, 0.7833, 0.8030, 0.8197.",
    "Embedding PC1 tracks sequence length at Spearman -0.7681.",
    "The same representation predicts out-of-family activity at PR-AUC 0.4220, which loses to its own permuted labels at p95 0.5217.",
    "Length residualization, family residualization and catalytic-core pooling all failed to fix it. The two core-focused variants became the most lineage-predictive of all, at 0.818.",
  ], M, 2.1, 4.5, 5.0, 17);

  s.addImage({ path: path.join(FIG, "lineage_vs_function.png"), x: 5.7, y: 2.0, w: 9.4, h: 5.09 });
  caption(s, "Each point is one representation under the same nested leave-one-family-out protocol. Source: bench/results/representations.json.", 5.7, 7.2, 9.4);

  s.addNotes(
    "Budget: 50 seconds.\n\n" +
    "Script: this explains why the previous slide looks the way it does. Horizontally, how well a representation identifies which family an RT belongs to. Vertically, how well it predicts activity in a family it has never seen. The language models are far to the right and flat on the floor. They know what an enzyme is related to, and how long it is, and not what it does. And note the 650M variants: the catalytic-core poolings, which were the obvious fix, came out the most lineage-predictive of all.\n\n" +
    "Sources:\n" +
    "  family accuracy 0.8197 and majority 0.3214, scale ladder 0.7652, 0.7833, 0.8030, 0.8197: reports/representation_diagnostics.md, embeddings/representation_diagnostics_taskA.py\n" +
    "  PC1 against length, Spearman -0.7681: reports/representation_diagnostics.md\n" +
    "  PR-AUC 0.4220 and permuted p95 0.5217: bench/results/taskA_representations.md and reports/statistical_validation.md\n" +
    "  core-focused variants at 0.818 family accuracy: bench/results/representations.json, family_accuracy field\n" +
    "  figure: reports/figures/presentation/lineage_vs_function.png"
  );
}

/* --------------------------------------------- 13. limits and future */

{
  const s = newSlide();
  head(s, "Limitations", "What this cannot say, and what is already built");

  const colW = (CW - 0.6) / 2;
  card(s, M, 2.15, colW, 4.7);
  text(s, "WHAT THIS BENCHMARK CANNOT SAY", {
    x: M + 0.5, y: 2.55, w: colW - 1.0, h: 0.34,
    fontFace: SANS, fontSize: 17, color: ACCENT, charSpacing: 1.2,
  });
  bullets(s, [
    "57 enzymes, 21 positives, Kish effective sample size 11.34",
    "Three of seven held-out families contain no active enzyme",
    "On CLS nothing clears its null, and the ordering is not resolvable",
    "The continuous efficiency target is a digitization of a figure, and is marked unverified in its own provenance column",
  ], M + 0.5, 3.1, colW - 1.0, 3.5, 18);

  card(s, M + colW + 0.6, 2.15, colW, 4.7);
  text(s, "FUTURE SCOPE: THE M-MLV VARIANT TASK", {
    x: M + colW + 1.1, y: 2.55, w: colW - 1.0, h: 0.34,
    fontFace: SANS, fontSize: 17, color: ACCENT, charSpacing: 1.2,
  });
  bullets(s, [
    "Reference resolved from the parent plasmid: 498 residues, cross-checked at 498 of 498",
    "1,046 single-substitution variant sequences constructed, four split regimes frozen",
    "The per-variant labels were never deposited, across 30 acquisition attempts in six route families",
    "No result exists for this task, and none has been invented for it",
  ], M + colW + 1.1, 3.1, colW - 1.0, 3.5, 18);

  caption(s, "A feasibility survey found no RT deep mutational scan in either standardized collection: 0 of ProteinGym v1.3's 217 substitution assays, 0 of MaveDB's 2,894 target genes.", M, 7.1, CW);

  s.addNotes(
    "Budget: 45 seconds.\n\n" +
    "Script: the honest limits first. Then the right column, which is the prepared future work. Everything is ready except the labels: the reference is resolved, the variants are built, the splits are frozen. The labels were never deposited. I did not estimate them, and there is no number for this task anywhere in the repository.\n\n" +
    "Sources:\n" +
    "  57, 21, Kish 11.34, three empty folds, unresolvable CLS ordering: README.md Limitations, reports/statistical_validation.md\n" +
    "  efficiency column marked UNVERIFIED_DIGITIZED: tasks/taskA_crossfamily/curated.csv, reports/reconciliation.md\n" +
    "  498 residues, 498 of 498 cross-check, 1046 variants, four frozen regimes, 30 attempts in six route families: reports/taskB_mmlv_dms/FINAL_REPORT.md, tasks/taskB_mmlv_dms/reference_resolution.json, tasks/taskB_mmlv_dms/variants_unlabelled.csv\n" +
    "  0 of 217 ProteinGym assays and 0 of 2894 MaveDB targets: survey/DATASET_SURVEY.md"
  );
}

/* ------------------------------------------------------ 14. references */

{
  const s = newSlide();
  head(s, "References", "Sources and artifacts");

  bullets(s, [
    "Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. Phage-assisted evolution and protein engineering yield compact, efficient prime editors. Cell 2023, 186(18):3983-4002.e26. DOI 10.1016/j.cell.2023.07.039",
    "ESM-2 representations computed with fair-esm 2.0.0, at 8M, 35M, 150M and 650M parameters",
    "ProteinGym v1.3 and MaveDB, searched for a reverse transcriptase deep mutational scan: survey/DATASET_SURVEY.md",
    "This benchmark: github.com/TanishDevs11/RT-plm-benchmark, MIT licence, citation in CITATION.cff",
    "Provenance of the inherited submission: ORIGIN.md, audit/leakage_report.md",
  ], M, 2.3, CW, 4.5, 20);

  caption(s, "Supplementary files are redistributed under the article's own CC BY 4.0 licence, with per-file provenance in tasks/taskA_crossfamily/PROVENANCE.md.", M, 7.1, CW);

  s.addNotes(
    "Budget: 10 seconds. Do not read the slide aloud. Say: the dataset is Doman et al. 2023 in Cell, and everything else is in the repository.\n\n" +
    "Sources: README.md Data source and citation section, CITATION.cff, survey/DATASET_SURVEY.md, ORIGIN.md."
  );
}

/* -------------------------------------------------------- 15. thank you */

{
  const s = newSlide();
  text(s, "Thank you", {
    x: 0.7, y: 2.55, w: 14.6, h: 3.4,
    fontFace: SERIF, fontSize: 138, color: INK, align: "center",
  });
  text(s, "Questions", {
    x: 0.7, y: 6.1, w: 14.6, h: 0.6,
    fontFace: SANS, fontSize: 20, color: MUTED, align: "center",
  });
  s.addNotes(
    "Budget: 5 seconds.\n\n" +
    "Likely questions and the sourced answer:\n" +
    "  Is the 0.975 fraudulent? No: it is a real metric value, computed correctly, on a predictor fitted against the labels it was scored on. The defect is the protocol, not the arithmetic. See audit/leakage_report.md.\n" +
    "  Why not just use a bigger model? 650M is the largest run, and it is the most lineage-predictive and among the weakest on activity. See bench/results/representations.json.\n" +
    "  What would change the answer? More assayed RTs. At a Kish effective sample size of 11.34, the minimum resolvable CLS difference is 0.4816. See reports/statistical_validation.md.\n\n" +
    "Total slide budget: 8 minutes 20 seconds, plus the 90 second walkthrough after slide 8, for 9 minutes 50 seconds against the 10 minute cap."
  );
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
