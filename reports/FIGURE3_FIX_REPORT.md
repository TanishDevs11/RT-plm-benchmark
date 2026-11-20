# Figure 3 label-overlap fix

Date: 2026-11-20. Scope: presentation only. No benchmark score, coordinate or
conclusion was changed.

## 1. What caused the overlap

**The defect was coordinate collision, not label crowding.** Five of the ten
representations share just two marker positions:

| Coordinate | Representations sharing it |
| --- | --- |
| **(0.800000, 0.000000)** | ESM-2 650M mean-pooled; ESM-2 650M, length-residualized; ESM-2 650M, family-residualized |
| **(0.818182, 0.000000)** | ESM-2 650M, catalytic-core pooled; ESM-2, attention-weighted core pooling |

The old `plot_function_vs_lineage()` drew every label at a fixed `(+4, +4)`
point offset:

```python
for x, y, lab in pts:
    ax.annotate(lab, (x, y), fontsize=7, xytext=(4, 4), textcoords="offset points")
```

With identical anchors, three labels printed on top of one another at the first
position and two at the second, producing the unreadable smear the screenshot
shows. The longest label also ran past the right spine, and only 8 of 10
markers were distinguishable because 5 were drawn on top of 2.

**The collision is a result, not noise.** The length- and family-residualized
variants and both core-pooling variants produced *identical* family accuracy
and *identical* (zero) out-of-family CLS — the corrections changed nothing.
That coincidence is part of the report's argument, so the fix discloses it
rather than hiding it behind jitter, which would have misstated the data.

## 2. Annotation strategy implemented

`adjustText` is not installed in this environment, so a deterministic
Matplotlib strategy was written instead. It has four parts.

**Markers stay on true coordinates, with a multiplicity badge.** Collided
points are drawn once, sized larger in proportion to how many representations
coincide, and carry a white `×3` / `×2` badge. No point was moved.

**Collision groups fan to opposite sides.** The first fix stacked both groups
in one right-hand gutter, which forced the leader lines to cross: two fans
aimed at a shared column always intersect when their anchors differ in x,
whichever vertical order is used. Groups now alternate sides by anchor
position — the leftmost fans up-left into the empty upper-left band, the
rightmost fans up-right into the gutter. Two fans opening away from each other
cannot intersect, and within one fan the segments share an origin so they never
cross either.

**Leader lines connect every displaced label to its point**, drawn thin
(0.7 pt), grey and slightly curved so they read as connectors rather than data.

**Isolated points keep direct labels**, placed by a greedy pass over eight
candidate offsets that rejects any placement whose bounding box hits an
existing label, a marker, or the axes edge.

One ordering detail mattered: the constrained fan labels are now placed *first*
and their boxes registered, then the flexible singletons. Placing singletons
first left "ESM-2 150M mean-pooled" colliding with "ESM-2 650M, catalytic-core
pooled", because the singleton had no way to know a fan label would later land
on it.

The figure was widened from 9×6 to 12×6.6 inches and the label font raised from
7 pt to 9 pt. **Nothing was shrunk to fit.**

## 3. Labels repositioned

| Representation | Treatment |
| --- | --- |
| ESM-2 650M mean-pooled | fanned up-left, leader line to (0.800, 0.000) |
| ESM-2 650M, family-residualized | fanned up-left, leader line to (0.800, 0.000) |
| ESM-2 650M, length-residualized | fanned up-left, leader line to (0.800, 0.000) |
| ESM-2 650M, catalytic-core pooled | fanned up-right, leader line to (0.818, 0.000) |
| ESM-2, attention-weighted core pooling | fanned up-right, leader line to (0.818, 0.000) |
| ESM-2 150M mean-pooled | direct label, offset chosen to clear the right-hand fan |
| ESM-2 35M mean-pooled | direct label, up-left |
| ESM-2 8M mean-pooled | direct label, below-right |
| handcrafted: sequence and physicochemical | direct label, up-right |
| structure: pLDDT, cleft and topology | direct label, below-right |

## 4. Other figures

All eight remaining figures were inspected. **None required correction.**

| Figure | Assessment |
| --- | --- |
| 1 — search-capacity curve | Clean; legend readable, no overlaps |
| 2 — commit CLS ladder | Clean |
| 4 — null comparison | Clean; legend well placed, categories distinct |
| 5 — representation comparison | Clean; interval bars and labels clear |
| 6 — embedding by length | Clean; three panels, all axes labelled |
| 7 — PC-to-length correlation | Clean; small multiples legible |
| 8 — embedding by family | Clean; small multiples with per-panel counts |
| 9 — embedding by activity | Clean |

No table overflows past the right margin anywhere in the report (checked
programmatically across all 38 pages: 0 blocks beyond the text block).

## 5. Data integrity

**Unchanged.** All ten representations are present with their original
coordinates:

| x (family accuracy) | y (CLS) | representation |
| --- | --- | --- |
| 0.6590909091 | 0.000000 | structure: pLDDT, cleft and topology |
| 0.7121212121 | 0.000000 | handcrafted: sequence and physicochemical |
| 0.7454545455 | 0.007409 | ESM-2 8M mean-pooled |
| 0.7818181818 | 0.139392 | ESM-2 35M mean-pooled |
| 0.8000000000 | 0.000000 | ESM-2 650M mean-pooled |
| 0.8000000000 | 0.000000 | ESM-2 650M, family-residualized |
| 0.8000000000 | 0.000000 | ESM-2 650M, length-residualized |
| 0.8015151515 | 0.305214 | ESM-2 150M mean-pooled |
| 0.8181818182 | 0.000000 | ESM-2 650M, catalytic-core pooled |
| 0.8181818182 | 0.000000 | ESM-2, attention-weighted core pooling |

`bench/results/representations.json` and `baseline_ladder.json` were **not
written to** — their timestamps remain 2026-09-30 and git reports no
modification to any tracked result file.

To guarantee that, a `--figure-only` entry point was added:

```
python bench/representations.py --figure-only
```

It redraws from the stored result JSON and recomputes nothing. Re-running the
full benchmark to reposition a label would have put experimental results at
risk for a presentation fix.

Report-level confirmation after the rebuild: 38 pages before and after, 9
embedded images before and after, and the **827 numeric tokens in the report
text are identical in value and in sequence**. The only text difference is a
benign reflow — Table 7 now begins on page 15 rather than 16, because the
figure's aspect ratio changed. No page is blank and no content was lost.

## 6. Verification statement

> **The regenerated Figure 3 was visually inspected.** It was rendered at
> reading size and at 300 dpi from the final PDF, on printed page 12
> (PDF page 15), and examined directly. All ten representation labels are
> individually legible; each leader line is traceable to its anchor; the ×3 and
> ×2 badges are readable; no label overlaps another label, a marker, or the
> axes boundary.
>
> This was confirmed programmatically as well. Measuring the text-only bounding
> box of every label — bypassing `Annotation.get_window_extent`, which unions
> the text box with its arrow and produces false positives — at the same 150 dpi
> the figure is saved at gives **0 label-label overlaps and 0 labels outside the
> axes** across 11 text artists.
>
> Three rendering passes were required. Pass 1 fixed the stacked labels but left
> the two fans crossing; pass 2 fixed the crossings but left one singleton
> colliding with a fan label; pass 3 fixed the placement order. Each pass was
> re-rendered and re-inspected.

## 7. Files

| Artifact | Path |
| --- | --- |
| Corrected report | `reports/RT_PLM_Benchmark_Technical_Report.pdf` |
| Previous report | kept in git history (the prior commit on this branch); a local copy sits at `reports/RT_PLM_Benchmark_Technical_Report_BACKUP.pdf` and is deliberately not committed, being a 1.5 MB duplicate of what git already stores |
| Corrected figure | `bench/figures/function_vs_lineage.png` |
| Copy of corrected figure | `reports/figures/figure3_function_vs_lineage_corrected.png` |
| Original figure (backup) | `bench/figures/function_vs_lineage_ORIGINAL.png` |
| Updated plotting code | `bench/representations.py` |

Nothing was committed, pushed or uploaded.
