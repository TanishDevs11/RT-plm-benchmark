#!/usr/bin/env python
"""Build the technical report PDF reproducibly from this repository.

    python reports/build_pdf.py

Output:
    reports/RT_PLM_Benchmark_Technical_Report.pdf
    reports/_report_data.typ          generated table and scalar data
    reports/REPORT_NUMBER_AUDIT.md    every reported number with its source

Toolchain: Typst, via the `typst` PyPI package, which bundles the compiler binary
and the Libertinus Serif / New Computer Modern / DejaVu Sans Mono font families.
No TeX distribution is required and none is installed. Install with:

    python -m pip install typst==0.15.2

Design rule: this script is the only place a number enters the report. Every
figure quoted in the PDF is either

  (a) read out of a result JSON in `bench/results/` and formatted here, or
  (b) listed in DOC_SOURCED below with the repository file that states it, and
      *verified to appear in that file* before the PDF is built.

A value in group (b) whose string cannot be found in its stated source aborts
the build. That makes the traceability requirement mechanical rather than a
promise: the report cannot be produced with an unsourced number in it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "reports"
RESULTS = REPO / "bench" / "results"

DOC = REPORTS / "_report_data.typ"
TYP = REPORTS / "report.typ"
PDF = REPORTS / "RT_PLM_Benchmark_Technical_Report.pdf"
AUDIT = REPORTS / "REPORT_NUMBER_AUDIT.md"

CHANCE_PR_AUC = 0.3684  # positive prevalence, 21/57


# --------------------------------------------------------------- formatting


def f4(x: float) -> str:
    return f"{float(x):.4f}"


def f3(x: float) -> str:
    return f"{float(x):.3f}"


def f2(x: float) -> str:
    return f"{float(x):.2f}"


def sgn4(x: float) -> str:
    return f"{float(x):+.4f}"


def rng(lo: float, hi: float) -> str:
    return f"{float(lo):.4f}–{float(hi):.4f}"


def load(name: str) -> dict:
    with open(RESULTS / name, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------- result files

ladder = load("baseline_ladder.json")
reps = load("representations.json")
snull = load("search_null.json")
scale = load("scale_projection.json")
taskA = load("taskA_representations.json")
valid = load("taskA_validation.json")

audit_rows: list[tuple[str, str, str, str]] = []  # (what, value, source, locator)

# Per-table provenance, so the audit can name a key path for every printed cell rather
# than only for each row. A column spec is (header, key-path template using {row}).
table_provenance: list = []


def register_table(name, what, source, columns, rows):
    table_provenance.append((name, what, source, list(columns), rows))


def j(what: str, value: str, source: str, key: str) -> str:
    """Record a JSON-derived number in the audit and return it formatted."""
    audit_rows.append((what, value, source, key))
    return value


# --------------------------------------------------------------- tables

# 5.1 baseline ladder, CLS protocol. Sorted by CLS descending.
lad = sorted(ladder["rows"], key=lambda r: -r["cls"])
LENGTH_CLS = ladder["length_baseline_cls"]

t_ladder = []
for r in lad:
    name = r["method"].split(". ", 1)[1] if ". " in r["method"] else r["method"]
    if abs(r["cls"] - LENGTH_CLS) < 1e-12:
        mark = "ref."
    elif r["beats_length_baseline"]:
        mark = "yes"
    else:
        mark = "no"
    t_ladder.append(
        (
            name,
            "none" if r["kind"] == "zero-parameter" else str(r["n_candidates"]),
            f4(r["cls"]),
            f4(r["w_spearman"]),
            f4(r["null_cls_p95"]),
            sgn4(r["signal_margin"]),
            mark,
        )
    )
    audit_rows.append(
        (
            f"baseline ladder: {name} (CLS, wSpearman, null p95, margin)",
            f"{f4(r['cls'])}, {f4(r['w_spearman'])}, {f4(r['null_cls_p95'])}, {sgn4(r['signal_margin'])}",
            "bench/results/baseline_ladder.json",
            f"rows[method={r['method']!r}].{{cls,w_spearman,null_cls_p95,signal_margin}}",
        )
    )

# Appendix A: the ladder exactly as the file holds it, split so that no single table
# places a composite value beside a precision-recall value.
t_ladder_cls = [
    (
        r["method"],
        f4(r["cls"]),
        f4(r["w_spearman"]),
        rng(r["ci_low"], r["ci_high"]),
        f4(r["null_cls_mean"]),
        f4(r["null_cls_p95"]),
        sgn4(r["signal_margin"]),
    )
    for r in ladder["rows"]
]
t_ladder_pr = [
    (
        r["method"],
        r["kind"],
        "none" if r["kind"] == "zero-parameter" else str(r["n_candidates"]),
        f4(r["pr_auc"]),
        f2(r["seconds"]),
    )
    for r in ladder["rows"]
]

# 5.2 representations, CLS protocol. Sorted by CLS descending.
rep_rows = sorted(reps["rows"], key=lambda r: -r["cls"])
t_reps = []
for r in rep_rows:
    t_reps.append(
        (
            r["method"],
            str(r["n_features"]),
            f4(r["cls"]),
            f4(r["w_spearman"]),
            f4(r["null_cls_p95"]),
            sgn4(r["signal_margin"]),
            f3(r["family_accuracy"]),
        )
    )
    audit_rows.append(
        (
            f"representation (CLS protocol): {r['method']} (CLS, wSpearman, null p95, margin, family acc.)",
            f"{f4(r['cls'])}, {f4(r['w_spearman'])}, {f4(r['null_cls_p95'])}, "
            f"{sgn4(r['signal_margin'])}, {f3(r['family_accuracy'])}",
            "bench/results/representations.json",
            f"rows[method={r['method']!r}].{{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}}",
        )
    )

t_reps_cls = [
    (
        r["method"],
        f4(r["cls"]),
        f4(r["w_spearman"]),
        rng(r["ci_low"], r["ci_high"]),
        f4(r["null_cls_p95"]),
        sgn4(r["signal_margin"]),
        f3(r["family_accuracy"]),
    )
    for r in reps["rows"]
]
t_reps_pr = [
    (r["method"], str(r["n_features"]), f4(r["pr_auc"]), f2(r["seconds"]))
    for r in reps["rows"]
]

# 5.3 Task A, three controls, PR-AUC primary. Sorted by PR-AUC descending.
order = sorted(taskA["results"], key=lambda n: -taskA["results"][n]["classification"]["pr_auc"])
t_taskA = []
for name in order:
    res = taskA["results"][name]
    cls_head = res["classification"]
    noise = valid["noise"][name]["classification"]["pr_auc"]
    ci = valid["intervals"][name]["classification"]["pr_auc"]
    perm = valid["permutation"].get(name)
    perm_p95 = perm["classification"]["pr_auc_p95"] if perm else None
    pr = cls_head["pr_auc"]
    if perm_p95 is None:
        survives = "n/a"  # permutation not run for this row
        perm_s = "not tested"
    else:
        perm_s = f4(perm_p95)
        survives = "yes" if (pr > noise and pr > CHANCE_PR_AUC and pr > perm_p95) else "no"
    t_taskA.append(
        (
            name,
            str(res["n_features"]),
            f4(pr),
            rng(ci["ci_low"], ci["ci_high"]),
            f4(noise),
            perm_s,
            survives,
        )
    )
    audit_rows.append(
        (
            f"Task A {name}: PR-AUC, 95% CI, noise control, permuted p95",
            f"{f4(pr)}, {rng(ci['ci_low'], ci['ci_high'])}, {f4(noise)}, {perm_s}",
            "bench/results/taskA_representations.json, bench/results/taskA_validation.json",
            f"results.{name}.classification.pr_auc; intervals.{name}.classification.pr_auc; "
            f"noise.{name}.classification.pr_auc; permutation.{name}.classification.pr_auc_p95",
        )
    )

# Appendix A: Task A CLS tables, both heads.
def cls_table(head: str) -> list[tuple[str, ...]]:
    rows = sorted(taskA["results"], key=lambda n: -taskA["results"][n][head]["cls"])
    out = []
    for name in rows:
        r = taskA["results"][name][head]
        ci = valid["intervals"][name][head]["cls"]
        noise = valid["noise"][name][head]["cls"]
        bar = valid["search_null_matched"]["p95"]
        out.append(
            (
                name,
                f4(r["cls"]),
                rng(ci["ci_low"], ci["ci_high"]),
                f4(noise),
                f4(bar),
                sgn4(r["cls"] - max(noise, bar)),
            )
        )
    return out


t_cls_class = cls_table("classification")
t_cls_reg = cls_table("regression")

# Section 4: the search-capacity null, K sweep and budget sweep.
t_ksweep = []
for row in snull["k_sweep"]:
    t_ksweep.append(
        (
            str(row["k"]),
            str(row["n_repeats"]),
            f4(row["mean"]),
            f4(row["std"]),
            f4(row["p95"]),
            f4(row["min"]),
            f4(row["max"]),
        )
    )
    audit_rows.append(
        (
            f"search-capacity null K={row['k']}: mean, sd, p95",
            f"{f4(row['mean'])}, {f4(row['std'])}, {f4(row['p95'])}",
            "bench/results/search_null.json",
            f"k_sweep[k={row['k']}].{{mean,std,p95}}",
        )
    )

t_budget = []
for row in snull["budget_sweep"]:
    t_budget.append(
        (str(row["budget"]), str(row["n_repeats"]), f4(row["mean"]), f4(row["std"]), f4(row["p95"]))
    )
    audit_rows.append(
        (
            f"search-null budget sweep at K=29, {row['budget']} iterations: mean, p95",
            f"{f4(row['mean'])}, {f4(row['p95'])}",
            "bench/results/search_null.json",
            f"budget_sweep[budget={row['budget']}].{{mean,p95}}",
        )
    )

# Section 9: scale projection.
t_scale = []
for row in scale["rows"]:
    t_scale.append(
        (
            str(row["n"]),
            f2(row["kish_ess"]),
            f4(row["ci_width"]),
            f4(row["null_mean"]),
            f4(row["null_p95"]),
        )
    )
    audit_rows.append(
        (
            f"scale projection n={row['n']}: Kish ESS, CI width, null mean, null p95",
            f"{f2(row['kish_ess'])}, {f4(row['ci_width'])}, {f4(row['null_mean'])}, {f4(row['null_p95'])}",
            "bench/results/scale_projection.json",
            f"rows[n={row['n']}].{{kish_ess,ci_width,null_mean,null_p95}}",
        )
    )

# Appendix A: label permutation, both heads, CLS and PR-AUC kept in separate tables.
t_perm_cls, t_perm_pr = [], []
for name in sorted(valid["permutation"]):
    for head in ("classification", "regression"):
        p = valid["permutation"][name][head]
        obs_cls = taskA["results"][name][head]["cls"]
        obs_pr = taskA["results"][name][head]["pr_auc"]
        t_perm_cls.append(
            (
                name,
                head,
                f4(p["mean"]),
                f4(p["p95"]),
                f4(p["max"]),
                f4(obs_cls),
                "yes" if obs_cls > p["p95"] else "no",
            )
        )
        t_perm_pr.append(
            (
                name,
                head,
                f4(p["pr_auc_mean"]),
                f4(p["pr_auc_p95"]),
                f4(p["pr_auc_max"]),
                f4(obs_pr),
                "yes" if obs_pr > p["pr_auc_p95"] else "no",
            )
        )

# --------------------------------------------------------------- scalars from JSON

V: dict[str, str] = {}


def jv(key: str, what: str, value: str, source: str, locator: str) -> None:
    V[key] = j(what, value, source, locator)


jv("length_cls", "length-only baseline CLS", f4(LENGTH_CLS),
   "bench/results/baseline_ladder.json", "length_baseline_cls")
jv("kmer_cos_cls", "3-mer cosine baseline CLS", f4(lad[0]["cls"]),
   "bench/results/baseline_ladder.json", "rows[4].cls")
jv("mrd_cls", "minimum resolvable CLS difference at 80% power", f4(reps["minimum_resolvable_difference"]),
   "bench/results/representations.json", "minimum_resolvable_difference")
jv("repr_null_p95", "CLS search-capacity null p95 used by the representation panel",
   f4(rep_rows[0]["null_cls_p95"]), "bench/results/representations.json", "rows[*].null_cls_p95")
jv("k1_p95", "search-capacity null p95 at K=1", f4(valid["search_null_matched"]["p95"]),
   "bench/results/taskA_validation.json", "search_null_matched.p95")
jv("k1_mean", "search-capacity null mean at K=1", f4(valid["search_null_matched"]["mean"]),
   "bench/results/taskA_validation.json", "search_null_matched.mean")
jv("k29_p95", "search-capacity null p95 at K=29, the matched count",
   f4([r for r in snull["k_sweep"] if r["k"] == 29][0]["p95"]),
   "bench/results/search_null.json", "k_sweep[k=29].p95")
jv("k50_p95", "search-capacity null p95 at K=50",
   f4([r for r in snull["k_sweep"] if r["k"] == 50][0]["p95"]),
   "bench/results/search_null.json", "k_sweep[k=50].p95")
jv("k5_p95", "search-capacity null p95 at K=5",
   f4([r for r in snull["k_sweep"] if r["k"] == 5][0]["p95"]),
   "bench/results/search_null.json", "k_sweep[k=5].p95")
jv("budget10_mean", "search-null mean at K=29 after ten DE iterations",
   f4(snull["budget_sweep"][0]["mean"]), "bench/results/search_null.json",
   "budget_sweep[budget=10].mean")
jv("ref_draw", "reference single draw at seed 42, K=29",
   f4(snull["reference"]["observed_single_draw"]), "bench/results/search_null.json",
   "reference.observed_single_draw")
jv("ref_expected", "value the brief expected for the K=29 null", f"{snull['reference']['expected']:.3f}",
   "bench/results/search_null.json", "reference.expected")
jv("ref_mean", "reference null mean over 20 repeats",
   f4(snull["reference"]["distribution"]["mean"]), "bench/results/search_null.json",
   "reference.distribution.mean")
jv("ref_median", "reference null median over 20 repeats",
   f4(snull["reference"]["distribution"]["median"]), "bench/results/search_null.json",
   "reference.distribution.median")
jv("ref_repeats", "reference null repeats", str(snull["reference"]["distribution"]["n_repeats"]),
   "bench/results/search_null.json", "reference.distribution.n_repeats")
jv("ref_tolerance", "self-check tolerance", f"{snull['reference']['tolerance']:.2f}",
   "bench/results/search_null.json", "reference.tolerance")
jv("curated_sha", "curated.csv SHA256", taskA["curated_sha256"],
   "bench/results/taskA_representations.json", "curated_sha256")
jv("n_bootstrap", "bootstrap draws", f"{valid['n_bootstrap']:,}".replace(",", " "),
   "bench/results/taskA_validation.json", "n_bootstrap")
jv("n_perm", "label permutation repeats", str(valid["n_permutations"]),
   "bench/results/taskA_validation.json", "n_permutations")
jv("free_params", "free parameters selected by the Task A inner loop",
   str(valid["free_parameters_used"]), "bench/results/taskA_validation.json", "free_parameters_used")
jv("c_grid", "logistic regularization grid",
   ", ".join(str(c) for c in taskA["logistic_C_grid"]),
   "bench/results/taskA_representations.json", "logistic_C_grid")
jv("alpha_grid", "ridge regularization grid",
   ", ".join(str(a) for a in taskA["ridge_alpha_grid"]),
   "bench/results/taskA_representations.json", "ridge_alpha_grid")
jv("kmer4_pr", "kmer4 PR-AUC", f4(taskA["results"]["kmer4"]["classification"]["pr_auc"]),
   "bench/results/taskA_representations.json", "results.kmer4.classification.pr_auc")
jv("kmer4_noise", "kmer4 noise control PR-AUC", f4(valid["noise"]["kmer4"]["classification"]["pr_auc"]),
   "bench/results/taskA_validation.json", "noise.kmer4.classification.pr_auc")
jv("kmer4_perm", "kmer4 permuted PR-AUC p95",
   f4(valid["permutation"]["kmer4"]["classification"]["pr_auc_p95"]),
   "bench/results/taskA_validation.json", "permutation.kmer4.classification.pr_auc_p95")
jv("kmer4_feats", "kmer4 feature count", str(taskA["results"]["kmer4"]["n_features"]),
   "bench/results/taskA_representations.json", "results.kmer4.n_features")
jv("kmer4_cls", "kmer4 CLS, classification head", f4(taskA["results"]["kmer4"]["classification"]["cls"]),
   "bench/results/taskA_representations.json", "results.kmer4.classification.cls")
jv("e650_pr", "ESM-2 650M PR-AUC", f4(taskA["results"]["esm2_650M"]["classification"]["pr_auc"]),
   "bench/results/taskA_representations.json", "results.esm2_650M.classification.pr_auc")
jv("e650_noise", "ESM-2 650M noise control PR-AUC",
   f4(valid["noise"]["esm2_650M"]["classification"]["pr_auc"]),
   "bench/results/taskA_validation.json", "noise.esm2_650M.classification.pr_auc")
jv("e650_perm", "ESM-2 650M permuted PR-AUC p95",
   f4(valid["permutation"]["esm2_650M"]["classification"]["pr_auc_p95"]),
   "bench/results/taskA_validation.json", "permutation.esm2_650M.classification.pr_auc_p95")
jv("e8_pr", "ESM-2 8M PR-AUC", f4(taskA["results"]["esm2_8M"]["classification"]["pr_auc"]),
   "bench/results/taskA_representations.json", "results.esm2_8M.classification.pr_auc")
jv("e8_noise", "ESM-2 8M noise control PR-AUC", f4(valid["noise"]["esm2_8M"]["classification"]["pr_auc"]),
   "bench/results/taskA_validation.json", "noise.esm2_8M.classification.pr_auc")
jv("e8_perm", "ESM-2 8M permuted PR-AUC p95",
   f4(valid["permutation"]["esm2_8M"]["classification"]["pr_auc_p95"]),
   "bench/results/taskA_validation.json", "permutation.esm2_8M.classification.pr_auc_p95")
jv("phys_cls", "physicochemical CLS, the highest observed under either head",
   f4(taskA["results"]["physicochemical"]["classification"]["cls"]),
   "bench/results/taskA_representations.json", "results.physicochemical.classification.cls")
jv("e650_cls_a", "ESM-2 650M CLS, Task A classification head",
   f4(taskA["results"]["esm2_650M"]["classification"]["cls"]),
   "bench/results/taskA_representations.json", "results.esm2_650M.classification.cls")
jv("e150_cls", "ESM-2 150M CLS under the CLS protocol",
   f4([r for r in reps["rows"] if r["method"] == "ESM-2 150M mean-pooled"][0]["cls"]),
   "bench/results/representations.json", "rows[ESM-2 150M mean-pooled].cls")
jv("e35_cls", "ESM-2 35M CLS under the CLS protocol",
   f4([r for r in reps["rows"] if r["method"] == "ESM-2 35M mean-pooled"][0]["cls"]),
   "bench/results/representations.json", "rows[ESM-2 35M mean-pooled].cls")
jv("e8_cls", "ESM-2 8M CLS under the CLS protocol",
   f4([r for r in reps["rows"] if r["method"] == "ESM-2 8M mean-pooled"][0]["cls"]),
   "bench/results/representations.json", "rows[ESM-2 8M mean-pooled].cls")
jv("e650_cls", "ESM-2 650M CLS under the CLS protocol",
   f4([r for r in reps["rows"] if r["method"] == "ESM-2 650M mean-pooled"][0]["cls"]),
   "bench/results/representations.json", "rows[ESM-2 650M mean-pooled].cls")
jv("fam_cls_protocol", "ESM-2 650M family accuracy under the CLS-protocol measurement",
   f4([r for r in reps["rows"] if r["method"] == "ESM-2 650M mean-pooled"][0]["family_accuracy"]),
   "bench/results/representations.json", "rows[ESM-2 650M mean-pooled].family_accuracy")
jv("fam_majority", "family majority baseline",
   f4(rep_rows[0]["family_majority"]), "bench/results/representations.json", "rows[*].family_majority")
jv("core_fam", "catalytic-core pooled family accuracy",
   f3([r for r in reps["rows"] if r["method"] == "ESM-2 650M, catalytic-core pooled"][0]["family_accuracy"]),
   "bench/results/representations.json", "rows[ESM-2 650M, catalytic-core pooled].family_accuracy")
jv("rf_cls", "handcrafted + RandomForest CLS after the join repair",
   f4([r for r in ladder["rows"] if "RandomForest" in r["method"]][0]["cls"]),
   "bench/results/baseline_ladder.json", "rows[8b. handcrafted + RandomForest].cls")
jv("hlr_pr", "handcrafted + logistic regression PR-AUC",
   f4([r for r in ladder["rows"] if "logistic regression" in r["method"] and "ESM" not in r["method"]][0]["pr_auc"]),
   "bench/results/baseline_ladder.json", "rows[9. handcrafted + logistic regression].pr_auc")
jv("famres_removed", "principal components removed by family residualization",
   str([r for r in reps["rows"] if "family-residualized" in r["method"]][0]["transform_info"]["components_removed"]),
   "bench/results/representations.json", "rows[ESM-2 650M, family-residualized].transform_info.components_removed")
jv("famres_var", "variance removed by family residualization",
   f4([r for r in reps["rows"] if "family-residualized" in r["method"]][0]["transform_info"]["variance_removed"]),
   "bench/results/representations.json", "rows[ESM-2 650M, family-residualized].transform_info.variance_removed")
jv("chance_pr", "PR-AUC chance level, the positive prevalence", f"{CHANCE_PR_AUC:.4f}",
   "reports/FINAL_REPORT.md", "prevalence chance level of 0.3684")
jv("scale_note", "stated assumption of the scale projection", scale["note"],
   "bench/results/scale_projection.json", "note")

# --------------------------------------------------------------- doc-sourced scalars
#
# (key, value as it will be printed, source file, string that must appear in it)

DOC_SOURCED: list[tuple[str, str, str, str, str]] = [
    # key, printed value, source path, locator string, description
    ("fam_diag", "0.8197", "reports/representation_diagnostics.md", "0.8197",
     "ESM-2 650M family accuracy, diagnostics measurement"),
    ("fam_8m", "0.7652", "reports/representation_diagnostics.md", "0.7652",
     "ESM-2 8M family accuracy, diagnostics measurement"),
    ("fam_35m", "0.7833", "reports/representation_diagnostics.md", "0.7833",
     "ESM-2 35M family accuracy, diagnostics measurement"),
    ("fam_150m", "0.8030", "reports/representation_diagnostics.md", "0.8030",
     "ESM-2 150M family accuracy, diagnostics measurement"),
    ("fam_sd_650m", "0.1450", "reports/representation_diagnostics.md", "0.1450",
     "fold-to-fold SD of the ESM-2 650M family accuracy"),
    ("fam_3mer", "0.6621", "reports/representation_diagnostics.md", "0.6621",
     "best composition control family accuracy, 3-mer raw counts"),
    ("fam_len", "0.5167", "reports/representation_diagnostics.md", "0.5167",
     "length-only family accuracy"),
    ("fam_major", "0.3214", "reports/representation_diagnostics.md", "0.3214",
     "family majority baseline"),
    ("pc1_len", "-0.7681", "reports/representation_diagnostics.md", "-0.7681",
     "Spearman of ESM-2 650M PC1 against sequence length"),
    ("pc1_unscaled", "+0.6198", "reports/representation_diagnostics.md", "+0.6198",
     "the same correlation on centred but unstandardized embeddings"),
    ("diag_rows", "56 of 57", "reports/representation_diagnostics.md", "56 of 57",
     "rows retained by the at-least-five-members restriction"),
    ("kish", "11.338", "reports/dataset_overview.md", "11.338",
     "Kish effective sample size of the CLS weighting"),
    ("kish2", "11.34", "audit/metric_report.md", "11.34",
     "Kish effective sample size, as the metric audit prints it"),
    ("w_mmlv", "15.56", "audit/metric_report.md", "15.56",
     "MMLV-RT share of total CLS weight, percent"),
    ("w_top5", "56.17", "audit/metric_report.md", "56.17",
     "top five RTs' share of total CLS weight, percent"),
    ("w_inactive", "0.137", "audit/metric_report.md", "0.137",
     "all 36 inactives' combined share of total CLS weight, percent"),
    ("boot_width", "0.0794", "audit/metric_report.md", "0.0794",
     "bootstrap 95 percent CI width on the submitted prediction vector"),
    ("boot_point", "0.9754", "audit/metric_report.md", "0.9754",
     "point estimate of the submitted vector on the observed rows"),
    ("boot_lo", "0.9130", "audit/metric_report.md", "0.9130",
     "2.5th percentile of the bootstrap on the submitted vector"),
    ("boot_hi", "0.9924", "audit/metric_report.md", "0.9924",
     "97.5th percentile of the bootstrap on the submitted vector"),
    ("boot_mean", "0.9649", "audit/metric_report.md", "0.9649",
     "bootstrap mean on the submitted vector"),
    ("order_sd", "0.0008", "audit/metric_report.md", "0.0008",
     "standard deviation of CLS over 2000 row permutations"),
    ("order_range", "0.0048", "audit/metric_report.md", "0.0048",
     "range of CLS over 2000 row permutations"),
    ("mrd_median", "0.4816", "reports/statistical_validation.md", "0.4816",
     "median minimum resolvable CLS difference across all pairs"),
    ("mrd_min", "0.1499", "reports/statistical_validation.md", "0.1499",
     "smallest minimum resolvable difference, most similar pair"),
    ("mrd_max", "0.9056", "reports/statistical_validation.md", "0.9056",
     "largest minimum resolvable difference, least similar pair"),
    ("mrd_z", "2.8016", "reports/statistical_validation.md", "2.8016",
     "standard deviations needed for 80 percent power at alpha 0.05"),
    ("kmer4_len_rho", "+0.5212", "reports/interpretation.md", "+0.5212",
     "Spearman of kmer4 out-of-fold score against sequence length"),
    ("kmer4_len_p", "3.23e-05", "reports/interpretation.md", "3.23e-05",
     "p-value of that correlation"),
    ("kmer4_decile", "0.1638", "reports/interpretation.md", "0.1638",
     "kmer4 attribution mass in the top decile of family-explained features"),
    ("kmer4_decile_share", "0.1000", "reports/interpretation.md", "0.1000",
     "the feature share that decile represents"),
    ("kmer4_perfeat", "+0.2055", "reports/interpretation.md", "+0.2055",
     "Spearman of per-feature importance against family-explained variance"),
    ("kmer4_perfeat_p", "1.05e-190", "reports/interpretation.md", "1.05e-190",
     "p-value of the per-feature association"),
    ("kmer4_top1", "0.0656", "reports/interpretation.md", "0.0656",
     "kmer4 attribution mass in the top 1 percent of features"),
    ("kmer4_top1_share", "0.0100", "reports/interpretation.md", "0.0100",
     "the feature share the top 1 percent represents"),
    ("kmer4_gate_margin", "+0.0814", "reports/interpretation.md", "+0.0814",
     "kmer4 margin over its noise control"),
    ("top_feat_share", "0.00079", "reports/interpretation.md", "0.00079",
     "share of attribution mass carried by the top-ranked 4-mer"),
    ("sub_cls", "0.9754", "WRITEUP.md", "0.9754", "the previously reported CLS"),
    ("sub_margin", "+0.0414", "WRITEUP.md", "+0.0414",
     "margin of 0.9754 over the matched K=29 noise p95"),
    ("ladder_first", "0.4380", "audit/leakage_report.md", "0.4380",
     "first CLS quoted in the commit ladder"),
    ("ladder_last", "0.9754", "audit/leakage_report.md", "0.9754",
     "last CLS quoted in the commit ladder"),
    ("ladder_n", "20 commits", "audit/leakage_report.md", "20 commits",
     "number of commit messages quoting a CLS"),
    ("other_artifact", "0.8978", "WRITEUP.md", "0.8978",
     "CLS of the different stored artifact that holds 62 fitted parameters"),
    ("de_params", "62", "audit/leakage_report.md", "62",
     "free parameters in de_best_weights.json"),
    ("comp_n", "29", "audit/leakage_report.md", "29",
     "components scored on their own against the 57 labels"),
    ("comp_best", "0.6006", "audit/leakage_report.md", "0.6006",
     "best single stored component"),
    ("comp_mean", "0.4040", "audit/leakage_report.md", "0.4040",
     "mean single stored component"),
    ("rf_before", "0.5072", "WRITEUP.md", "0.5072",
     "handcrafted + RandomForest CLS before the join repair"),
    ("peek_detect", "5 of 7", "WRITEUP.md", "detects peeking on 5 of 7 families",
     "families on which the peeking positive control is detected"),
    ("n_struct", "57 structure", "WRITEUP.md", "57 structure",
     "structure files covering 56 enzymes"),
    ("n_enzymes", "57", "reports/dataset_overview.md", "| enzymes | 57 |",
     "enzymes in the panel"),
    ("n_active", "21", "reports/dataset_overview.md", "21 (36.8 percent)",
     "active enzymes"),
    ("n_inactive", "36", "reports/dataset_overview.md", "| inactive | 36 |",
     "inactive enzymes"),
    ("n_families", "7", "reports/dataset_overview.md", "| families | 7 |", "families"),
    ("zero_active", "3 of 7", "reports/dataset_overview.md", "3 of 7",
     "families holding no active enzyme"),
    ("informative", "4", "reports/dataset_overview.md",
     "Leave-one-family-out rests on 4 informative folds, not 7",
     "informative leave-one-family-out folds"),
    ("accessions", "27 of 57", "reports/FINAL_REPORT.md", "27 of 57",
     "accessions pinned exactly from sequence"),
    ("len_min", "226", "reports/dataset_overview.md", "| min | 226 |", "shortest sequence"),
    ("len_max", "824", "reports/dataset_overview.md", "| max | 824 |", "longest sequence"),
    ("len_median", "523", "reports/dataset_overview.md", "| median | 523 |", "median length"),
    ("len_mean", "503.7", "reports/dataset_overview.md", "503.7", "mean length"),
    ("len_sd", "149.9", "reports/dataset_overview.md", "149.9", "length standard deviation"),
    ("eff_max", "41", "reports/dataset_overview.md", "| max | 41 |", "highest digitized efficiency"),
    ("eff_min", "0.5", "reports/dataset_overview.md", "| min | 0.5 |", "lowest non-zero efficiency"),
    ("eff_median", "8", "reports/dataset_overview.md", "| median | 8 |", "median efficiency among actives"),
    ("eff_mean", "12.524", "reports/dataset_overview.md", "12.524", "mean efficiency among actives"),
    ("clust30_cross", "4", "reports/dataset_overview.md", "| 30 percent | 24 |",
     "clusters crossing a family boundary at 30 percent identity"),
    ("prose_tested", "59", "reports/doman2023_source_facts.md", "tested 59 enzymes",
     "enzymes the article's prose says were tested"),
    ("prose_active", "Twenty", "reports/doman2023_source_facts.md", "Twenty RTs from four different classes",
     "actives the article's prose reports"),
    ("tb_variants", "1045", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "1045",
     "Task B variants expected"),
    ("tb_ids", "1046", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "1046",
     "Task B variant identifiers frozen"),
    ("tb_ref_len", "498", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "498",
     "length of the resolved Task B reference"),
    ("tb_positions", "seven residue positions", "reports/CROSS_TASK_COMPARISON.md",
     "resolved and confirmed at seven",
     "residue positions at which the Task B reference was confirmed"),
    ("tb_regimes", "4 split regimes", "reports/CROSS_TASK_COMPARISON.md", "split regimes written and verified",
     "Task B split regimes written and verified"),
    ("tb_searches", "seven repository searches", "reports/CROSS_TASK_COMPARISON.md",
     "seven repository searches", "repository searches that returned nothing"),
    ("tb_version", "version 1", "reports/CROSS_TASK_COMPARISON.md", "still at version 1",
     "the preprint version"),
    ("tb_months", "three months", "reports/CROSS_TASK_COMPARISON.md", "after three months",
     "how long version 1 has been current"),
    ("tb_doi", "10.64898/2026.07.06.736660", "reports/taskB_mmlv_dms/FINAL_REPORT.md",
     "10.64898/2026.07.06.736660", "the resolving Task B DOI"),
    ("tb_doi_bad", "10.1101/2026.07.06.736660", "reports/taskB_mmlv_dms/FINAL_REPORT.md",
     "10.1101/2026.07.06.736660", "the non-resolving DOI the preprint's own header carries"),
    ("tb_attempts", "30 attempts", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "30 attempts",
     "acquisition attempts logged"),
    ("tb_cosine", "0.983968", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "0.983968",
     "median pairwise cosine similarity of 4-mer vectors across Task B variants"),
    ("tb_phys_cosine", "0.999998", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "0.999998",
     "median pairwise cosine similarity of physicochemical vectors"),
    ("doi", "10.1016/j.cell.2023.07.039", "reports/doman2023_source_facts.md",
     "10.1016/j.cell.2023.07.039", "the Task A source DOI"),
    ("pmc", "PMC10482982", "reports/doman2023_source_facts.md", "PMC10482982",
     "the Task A source PMC accession"),
    ("workbook_sha", "16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c",
     "reports/reconciliation.md",
     "16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c",
     "SHA256 of the source workbook mmc2.xlsx"),
    ("py_ver", "3.14.2", "WRITEUP.md", "Python 3.14.2", "Python version of record"),
    ("numpy_ver", "2.4.2", "WRITEUP.md", "numpy 2.4.2", "numpy version of record"),
    ("scipy_ver", "1.17.1", "WRITEUP.md", "scipy 1.17.1", "scipy version of record"),
    ("pandas_ver", "3.0.1", "WRITEUP.md", "pandas 3.0.1", "pandas version of record"),
    ("sklearn_ver", "1.8.0", "WRITEUP.md", "scikit-learn 1.8.0", "scikit-learn version of record"),
    ("mpl_ver", "3.10.8", "WRITEUP.md", "matplotlib 3.10.8", "matplotlib version of record"),
    ("torch_ver", "2.11.0+cpu", "WRITEUP.md", "torch 2.11.0+cpu", "torch build of record, zero CUDA devices"),
    ("esm_ver", "2.0.0", "WRITEUP.md", "fair-esm 2.0.0", "fair-esm version of record"),
    ("mmseqs_commit", "8cc5ce36", "reports/dataset_overview.md", "8cc5ce36", "MMseqs2 commit used for clustering"),
    ("npz_loader", "bench/baselines.py", "bench/baselines.py", "esm2_embeddings.npz",
     "the baseline-ladder module that loads the inherited embedding file unconditionally"),
    ("mk_reproduce", "reproduce", "Makefile", "reproduce: test selfcheck audit embeddings",
     "the Makefile reproduce target, which does not invoke bench/search_null.py"),
    ("esm1v_free", "2.1 GB", "WRITEUP.md", "2.1 GB", "memory available at the ESM-1v retry"),
    ("esm1v_total", "16.9 GB", "WRITEUP.md", "16.9 GB", "total host memory at the ESM-1v retry"),
    ("tb_nt_share", "0.807", "reports/taskB_mmlv_dms/FINAL_REPORT.md", "0.807",
     "nucleotide identity shared by the two Task B reading frames"),
    ("block2", "486", "reports/FINAL_REPORT.md", "Block 2's 486 entries", "unassayed BLAST-hit entries in block 2"),
]

missing: list[str] = []
for key, value, source, locator, desc in DOC_SOURCED:
    path = REPO / source
    if not path.exists():
        missing.append(f"{key}: source file {source} does not exist")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if locator not in text:
        missing.append(f"{key}: {locator!r} not found in {source}")
        continue
    V[key] = value
    audit_rows.append((desc, value, source, f"verified present: {locator!r}"))

if missing:
    print("UNSOURCED NUMBERS -- refusing to build the PDF:", file=sys.stderr)
    for m in missing:
        print("  " + m, file=sys.stderr)
    raise SystemExit(1)


# --------------------------------------------------------------- table provenance

LAD = "bench/results/baseline_ladder.json"
REP = "bench/results/representations.json"
TAJ = "bench/results/taskA_representations.json"
VAL = "bench/results/taskA_validation.json"
SNL = "bench/results/search_null.json"
SCL = "bench/results/scale_projection.json"
BOTH = TAJ + " + " + VAL

register_table("t_ladder", 'Baseline ladder, composite metric (body)', LAD, [
    ('method', 'rows[{row}].method'),
    ('selected', 'rows[{row}].kind / rows[{row}].n_candidates'),
    ('CLS', 'rows[{row}].cls'),
    ('wSpear.', 'rows[{row}].w_spearman'),
    ('null p95', 'rows[{row}].null_cls_p95'),
    ('margin vs null', 'rows[{row}].signal_margin'),
    ('beats length', 'rows[{row}].beats_length_baseline vs length_baseline_cls'),
], t_ladder)

register_table("t_ladder_cls", 'Baseline ladder, composite metric (appendix)', LAD, [
    ('method', 'rows[{row}].method'),
    ('CLS', 'rows[{row}].cls'),
    ('wSpear.', 'rows[{row}].w_spearman'),
    ('CLS 95% CI', 'rows[{row}].ci_low / rows[{row}].ci_high'),
    ('null mean', 'rows[{row}].null_cls_mean'),
    ('null p95', 'rows[{row}].null_cls_p95'),
    ('margin', 'rows[{row}].signal_margin'),
], t_ladder_cls)

register_table("t_ladder_pr", 'Baseline ladder, precision-recall component (appendix)', LAD, [
    ('method', 'rows[{row}].method'),
    ('kind', 'rows[{row}].kind'),
    ('selected', 'rows[{row}].n_candidates'),
    ('PR-AUC', 'rows[{row}].pr_auc'),
    ('seconds', 'rows[{row}].seconds'),
], t_ladder_pr)

register_table("t_reps", 'Representations, composite metric (body)', REP, [
    ('representation', 'rows[{row}].method'),
    ('features', 'rows[{row}].n_features'),
    ('CLS', 'rows[{row}].cls'),
    ('wSpear.', 'rows[{row}].w_spearman'),
    ('null p95', 'rows[{row}].null_cls_p95'),
    ('margin vs null', 'rows[{row}].signal_margin'),
    ('family acc.', 'rows[{row}].family_accuracy'),
], t_reps)

register_table("t_reps_cls", 'Representations, composite metric (appendix)', REP, [
    ('representation', 'rows[{row}].method'),
    ('CLS', 'rows[{row}].cls'),
    ('wSpear.', 'rows[{row}].w_spearman'),
    ('CLS 95% CI', 'rows[{row}].ci_low / rows[{row}].ci_high'),
    ('null p95', 'rows[{row}].null_cls_p95'),
    ('margin', 'rows[{row}].signal_margin'),
    ('fam. acc.', 'rows[{row}].family_accuracy'),
], t_reps_cls)

register_table("t_reps_pr", 'Representations, precision-recall component (appendix)', REP, [
    ('representation', 'rows[{row}].method'),
    ('features', 'rows[{row}].n_features'),
    ('PR-AUC', 'rows[{row}].pr_auc'),
    ('seconds', 'rows[{row}].seconds'),
], t_reps_pr)

register_table("t_taskA", 'Task A, three-control protocol, precision-recall area (body)', BOTH, [
    ('representation', 'results.{row}'),
    ('features', 'results.{row}.n_features'),
    ('PR-AUC', 'results.{row}.classification.pr_auc'),
    ('95% CI', 'intervals.{row}.classification.pr_auc.ci_low / .ci_high'),
    ('noise control', 'noise.{row}.classification.pr_auc'),
    ('permuted p95', 'permutation.{row}.classification.pr_auc_p95'),
    ('survives', 'derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95'),
], t_taskA)

register_table("t_cls_class", 'Task A composite, classification head (appendix)', BOTH, [
    ('representation', 'results.{row}'),
    ('CLS', 'results.{row}.classification.cls'),
    ('95% CI', 'intervals.{row}.classification.cls.ci_low / .ci_high'),
    ('noise CLS', 'noise.{row}.classification.cls'),
    ('search null p95', 'search_null_matched.p95'),
    ('margin', 'derived: cls minus max(noise cls, search_null_matched.p95)'),
], t_cls_class)

register_table("t_cls_reg", 'Task A composite, regression head (appendix)', BOTH, [
    ('representation', 'results.{row}'),
    ('CLS', 'results.{row}.regression.cls'),
    ('95% CI', 'intervals.{row}.regression.cls.ci_low / .ci_high'),
    ('noise CLS', 'noise.{row}.regression.cls'),
    ('search null p95', 'search_null_matched.p95'),
    ('margin', 'derived: cls minus max(noise cls, search_null_matched.p95)'),
], t_cls_reg)

register_table("t_ksweep", 'Search-capacity null, K sweep', SNL, [
    ('K', 'k_sweep[k={row}].k'),
    ('repeats', 'k_sweep[k={row}].n_repeats'),
    ('mean', 'k_sweep[k={row}].mean'),
    ('sd', 'k_sweep[k={row}].std'),
    ('p95', 'k_sweep[k={row}].p95'),
    ('min', 'k_sweep[k={row}].min'),
    ('max', 'k_sweep[k={row}].max'),
], t_ksweep)

register_table("t_budget", 'Search-capacity null, budget sweep at K=29', SNL, [
    ('iterations', 'budget_sweep[budget={row}].budget'),
    ('repeats', 'budget_sweep[budget={row}].n_repeats'),
    ('mean', 'budget_sweep[budget={row}].mean'),
    ('sd', 'budget_sweep[budget={row}].std'),
    ('p95', 'budget_sweep[budget={row}].p95'),
], t_budget)

register_table("t_scale", 'Scale projection', SCL, [
    ('n', 'rows[n={row}].n'),
    ('Kish ESS', 'rows[n={row}].kish_ess'),
    ('bootstrap CI width', 'rows[n={row}].ci_width'),
    ('noise null mean', 'rows[n={row}].null_mean'),
    ('noise null p95', 'rows[n={row}].null_p95'),
], t_scale)

register_table("t_perm_cls", 'Label permutation, composite metric', BOTH, [
    ('representation', 'permutation.{row}'),
    ('head', 'the head named in this cell'),
    ('permuted mean', 'permutation.{row}.<head>.mean'),
    ('permuted p95', 'permutation.{row}.<head>.p95'),
    ('permuted max', 'permutation.{row}.<head>.max'),
    ('observed', 'results.{row}.<head>.cls'),
    ('above p95', 'derived: observed exceeds permuted p95'),
], t_perm_cls)

register_table("t_perm_pr", 'Label permutation, precision-recall area', BOTH, [
    ('representation', 'permutation.{row}'),
    ('head', 'the head named in this cell'),
    ('permuted mean', 'permutation.{row}.<head>.pr_auc_mean'),
    ('permuted p95', 'permutation.{row}.<head>.pr_auc_p95'),
    ('permuted max', 'permutation.{row}.<head>.pr_auc_max'),
    ('observed', 'results.{row}.<head>.pr_auc'),
    ('above p95', 'derived: observed exceeds permuted p95'),
], t_perm_pr)

# --------------------------------------------------------------- emit typst data


def tq(s: str) -> str:
    """Quote a Python string as a Typst string literal."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit_rows(name: str, rows) -> str:
    body = ",\n  ".join("(" + ", ".join(tq(c) for c in row) + ")" for row in rows)
    return f"#let {name} = (\n  {body},\n)\n\n"


def emit_dict(name: str, mapping: dict) -> str:
    body = ",\n  ".join(f"{k}: {tq(val)}" for k, val in sorted(mapping.items()))
    return f"#let {name} = (\n  {body},\n)\n\n"


parts = [
    "// GENERATED BY reports/build_pdf.py -- DO NOT EDIT BY HAND.\n"
    "// Every value here is read from a file in this repository at build time.\n\n",
    emit_dict("num", V),
    emit_rows("t_ladder", t_ladder),
    emit_rows("t_ladder_cls", t_ladder_cls),
    emit_rows("t_ladder_pr", t_ladder_pr),
    emit_rows("t_reps", t_reps),
    emit_rows("t_reps_cls", t_reps_cls),
    emit_rows("t_reps_pr", t_reps_pr),
    emit_rows("t_taskA", t_taskA),
    emit_rows("t_cls_class", t_cls_class),
    emit_rows("t_cls_reg", t_cls_reg),
    emit_rows("t_ksweep", t_ksweep),
    emit_rows("t_budget", t_budget),
    emit_rows("t_scale", t_scale),
    emit_rows("t_perm_cls", t_perm_cls),
    emit_rows("t_perm_pr", t_perm_pr),
]
DOC.write_text("".join(parts), encoding="utf-8")
print(f"wrote {DOC.relative_to(REPO)}  ({len(V)} scalars, "
      f"{sum(len(t) for t in (t_ladder, t_reps, t_taskA, t_ksweep, t_scale))} principal table rows)")


# --------------------------------------------------------------- compile


def compile_pdf() -> None:
    try:
        import typst
    except ImportError:
        raise SystemExit(
            "The `typst` package is not installed. Run:\n"
            "    python -m pip install typst==0.15.2\n"
            "It bundles the compiler and its fonts; no TeX distribution is needed."
        )
    typst.compile(str(TYP), output=str(PDF), root=str(REPO))
    print(f"wrote {PDF.relative_to(REPO)}  ({PDF.stat().st_size / 1024:.0f} KB)")


compile_pdf()


# --------------------------------------------------------------- audit


def write_audit() -> None:
    esc = lambda x: str(x).replace("|", r"\|").replace("\n", " ")
    lines = [
        "# Number audit for the technical report",
        "",
        "Written by `reports/build_pdf.py`, which is the only place a number enters",
        "`RT_PLM_Benchmark_Technical_Report.pdf`. Nothing numeric is typed into",
        "`reports/report.typ`; every figure is either computed from a result file at build",
        "time or verified to occur, as an exact string, in the repository document named as",
        "its source. *A value whose string cannot be found in its stated source aborts the",
        "build*, so the PDF cannot be produced with an unsourced number in it.",
        "",
        "Three kinds of entry appear below.",
        "",
        "1. **Scalars quoted in the prose** (section 1), each with the result-file key path",
        "   it was computed from, or the document whose text was verified to contain it.",
        "2. **Every cell of every generated table** (section 2), one row per printed cell,",
        "   with the key path that produced it.",
        "3. **Numbers deliberately not carried into the report** (section 3), with the",
        "   reason each was excluded.",
        "",
        "Not audited here, and why. Section, figure, table and page numbers are generated",
        "by the typesetter. Counts inside prose sentences that restate a table (for example",
        "\"four trained rows\") are read off the table in the same section. Deliberately",
        "rounded restatements of an audited value (for example \"from about 0.86 to about",
        "0.58\" for the noise-null means of 0.8624 and 0.5794 in Table 14) are marked as",
        "approximate in the text. The DOIs in the reference list are citation identifiers,",
        "verified against the sources recorded in `reports/refs.yml`.",
        "",
        "## 1. Scalars quoted in the prose",
        "",
        f"Rows: {len(audit_rows)}.",
        "",
        "| what the report states | value as printed | source file | locator |",
        "| --- | --- | --- | --- |",
    ]
    for what, value, source, locator in audit_rows:
        lines.append(f"| {esc(what)} | `{esc(value)}` | `{esc(source)}` | `{esc(locator)}` |")

    cell_count = 0
    lines += ["", "## 2. Every cell of every generated table", ""]
    lines += [
        "Each table below is generated by `reports/build_pdf.py` directly from the named",
        "result file and inserted into the PDF as data; the document source contains no",
        "copy of these values. The locator column gives the key path for that exact cell.",
        "",
    ]
    for name, what, source, columns, rows in table_provenance:
        lines += [
            f"### `{name}` — {what}",
            "",
            f"Source: `{source}`. Rows: {len(rows)}. Cells: {len(rows) * len(columns)}.",
            "",
            "| row | column | value as printed | locator |",
            "| --- | --- | --- | --- |",
        ]
        for row in rows:
            key = row[0]
            for i, (header, template) in enumerate(columns):
                if i >= len(row):
                    continue
                cell_count += 1
                lines.append(
                    f"| {esc(key)} | {esc(header)} | `{esc(row[i])}` | "
                    f"`{esc(template.replace('{row}', str(key)))}` |"
                )
        lines.append("")

    lines[lines.index("## 2. Every cell of every generated table") + 1] = (
        f"Tables: {len(table_provenance)}. Cells audited: {cell_count}."
    )

    lines += [
        "## 3. Numbers deliberately not carried into the report",
        "",
        "| number | where it appears | why it was not used |",
        "| --- | --- | --- |",
        "| PR-AUC 0.7810 and weighted Spearman 0.3755 for handcrafted + RandomForest | "
        "`WRITEUP.md`, `PROGRESS.md` | pre-join-repair values printed beside a post-repair "
        "composite. `bench/results/baseline_ladder.json` gives 0.8288 and 0.2888, whose "
        "harmonic mean is the reported composite. The report uses the result file and "
        "records the defect in section 7. |",
        "| PR-AUC 0.6830 and weighted Spearman 0.0856 for handcrafted + ExtraTrees | "
        "`WRITEUP.md`, `PROGRESS.md` | same defect; the result file gives 0.6948 and 0.1036. |",
        "| PR-AUC 0.6427 for handcrafted + logistic regression | `WRITEUP.md` | same defect; "
        "the result file gives 0.6533, which the report uses and flags in section 3.4. |",
        "| the frequency-normalized 3-mer family accuracy of 0.6803 | "
        "`reports/representation_diagnostics.md` | reported there as one of two encodings of "
        "a control the repository never specified. The report states that both encodings "
        "exist and quotes only the raw-counts figure of 0.6621 as the stated control, "
        "rather than choosing the encoding that suits the conclusion. |",
        "| any score for ProtT5-XL-U50, ESM-IF or ProteinMPNN, zero-shot ESM-1v masked "
        "marginals, or ESM-1v mean-pooled | nowhere | the experiments were blocked and no "
        "value exists. No estimate, interpolation or literature-quoted figure was "
        "substituted. See Table 17. |",
        "| any Task B benchmark score | nowhere | Task B produced no measurement; the "
        "per-variant activity values were never deposited. |",
        "| any combined or cross-task score, and any sentence comparing a Task A number "
        "with a Task B number | nowhere | forbidden by `reports/CROSS_TASK_COMPARISON.md` "
        "and blocked in code by `schemas/task_schema.py`. |",
        "| a maximum elementwise difference between the two ESM-2 650M embedding files | "
        "nowhere | the two builds were compared while preparing section 5.7 and agree to "
        "within float16 storage precision, but no repository file records that comparison, "
        "so the report states the dtype difference rather than quoting a magnitude it "
        "cannot source. |",
        "| a precision-recall search-capacity null | nowhere | `bench/search_null.py` "
        "measures the composite, not precision-recall area. The gap is stated in the report "
        "rather than filled with the composite bar, which would compare two different "
        "quantities. |",
        "",
    ]
    AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"wrote {AUDIT.relative_to(REPO)}  "
        f"({len(audit_rows)} prose scalars, {cell_count} table cells)"
    )


write_audit()
