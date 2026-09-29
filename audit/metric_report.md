# Metric properties of CLS at n = 57

Seed: 42

Library versions: python 3.14.2, numpy 2.4.2, pandas 3.0.1, scipy 1.17.1, scikit-learn 1.8.0

Everything below is a property of the metric and the label distribution. None of it depends on any model, and none of it is a result.

## 1. Effective sample size

The weighted Spearman term weights each RT by `pe_efficiency_pct + 0.01`.

| Quantity | Value |
| --- | --- |
| Rows | 57 |
| Active | 21 |
| Inactive | 36 |
| Kish effective sample size | 11.34 |

The nominal sample size is 57. The weighted Spearman term behaves like a sample of about 11.3 independent points. Any procedure that fits more free parameters than that is fitting noise, and the search-capacity null in Phase 3 measures exactly how much.

## 2. Weight concentration

| Group | Share of total weight |
| --- | --- |
| MMLV-RT (HIVpol+MMLVRNaseH_RT, MMLV-RT) | 15.56 percent |
| Top 5 RTs by weight | 56.17 percent |
| All 36 inactives combined | 0.137 percent |

Top 5 by weight: MMLV-RT, Tf1-RT, KORV-RT, WMSV-RT, AVIRE-RT.

The inactives carry a fraction of a percent of the weighted Spearman term between them. Ordering them correctly is close to free, and ordering them incorrectly is close to costless, so that half of the metric is decided by a handful of high-efficiency enzymes.

## 3. Row-order sensitivity

Prediction vector: `legacy_submission/submission.csv`, 2000 random row permutations.

| Statistic | CLS |
| --- | --- |
| Minimum | 0.9723 |
| Median | 0.9747 |
| Maximum | 0.9771 |
| Standard deviation | 0.0008 |
| Range | 0.0048 |

`weighted_spearman` ranks with `argsort(argsort(...))`, which hands distinct integer ranks to tied values. Every zero-efficiency RT is tied, so the ranks assigned to those 36 rows depend on their position in the merged array rather than on anything predicted. The effect is real, and it is small, because those rows carry almost none of the weight. It is reported because a metric whose value depends on row order at all should be stated plainly, not discovered later.

## 4. Bootstrap confidence interval

Resampling the 57 RTs with replacement, 10000 draws, on the fixed prediction vector `legacy_submission/submission.csv`.

| Statistic | CLS |
| --- | --- |
| Point estimate on the observed rows | 0.9754 |
| Bootstrap mean | 0.9649 |
| 2.5th percentile | 0.9130 |
| 97.5th percentile | 0.9924 |
| Interval width | 0.0794 |
| Draws discarded as single class | 0 |

The 95 percent interval spans 0.079 CLS. That width is the resolution limit of this benchmark: two methods whose scores differ by less than it have not been distinguished by this dataset, however many decimal places are quoted for either. Phase 5 converts this into an explicit minimum resolvable difference and refuses to call anything below it a win.

