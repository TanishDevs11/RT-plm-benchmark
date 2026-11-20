# Presentation

A 10 minute intern talk on this benchmark: 15 slides plus a 90 second live
walkthrough of the repository.

| file | what it is |
| --- | --- |
| `build_deck.js` | the generator; writes `RT_PLM_Benchmark_Presentation.pptx` |
| `make_figures.py` | regenerates the four presentation figures from committed result artifacts |
| `RT_PLM_Benchmark_Presentation.pptx` | the deck, 16 x 9 inches |

## Rebuild

```bash
python presentation/make_figures.py          # writes reports/figures/presentation/
cd presentation && npm install pptxgenjs     # first time only
node presentation/build_deck.js              # run from the repository root
```

The deck is reproducible: nothing is hand edited in the packed XML, and the
figures are rebuilt from `bench/results/*.json` and `audit/leakage_report.md`
rather than being redrawn by hand.

## Rules the deck is built to

1. Every number on a slide is traced in that slide's speaker notes to the
   repository artifact it came from. A number without a source does not appear.
2. `0.9754` appears only as the claim the audit corrected, never as a result.
3. Every reported score carries its split regime: all result slides are out of
   fold under the frozen nested leave-one-family-out protocol.
4. Where a comparison falls below the minimum resolvable difference, the slide
   says so.
5. The M-MLV slide states that the labels were never obtained and that no result
   exists.

## Timing

Speaker notes carry a per-slide budget. The slides total 8 minutes 20 seconds;
the live walkthrough, scripted in the notes of slide 8, adds 90 seconds, for
9 minutes 50 seconds against the 10 minute cap.

## Figures

Written to `reports/figures/presentation/`:

| figure | source artifact |
| --- | --- |
| `search_capacity_null.png` | `bench/results/search_null.json` |
| `baseline_ladder.png` | `bench/results/baseline_ladder.json`, `bench/results/representations.json` |
| `lineage_vs_function.png` | `bench/results/representations.json` |
| `hill_climb.png` | `audit/leakage_report.md`, commit ladder table |

## Checks that were run

- `python scripts/office/validate.py` on the deck: all validations passed
- every slide rendered through PowerPoint and inspected for overflow, overlap,
  margins and legibility
- a text dump checked for placeholder strings and for a time budget plus source
  paths in every slide's notes
