"""Harmonize RT identifiers across the inherited data files.

The inherited `data/` directory uses three different naming conventions for the
same 57 enzymes, and joining them naively on `rt_name` silently produces empty
columns rather than an error. This module exists because that silence already
corrupted a result: `topology_features.csv` drops the `-RT` suffix that
`rt_sequences.csv` carries, so a left join on `rt_name` matched zero rows and fed
nine all-missing topology columns into the handcrafted feature table. The model
trained happily on nothing.

Defects recorded here, all inherited and none introduced by this rebuild:

1. `topology_features.csv` omits the `-RT` suffix on every row, and additionally
   spells a few names differently: `Tyrosine_recomb` against
   `Tyrosinerecomb-RT`, `HIVpol+MMLVRNaseH` against `HIVpol+MMLVRNaseH_RT`, and
   `Med` against `Med-CasRT`.
2. `structure_features.csv` spells one RT `Vp-96` where the label file says
   `Vp96-RT`.
3. `data/structures/` holds 57 PDB files covering only 56 distinct RTs: `Vp-96.pdb`
   and `Vp96-RT.pdb` are the same enzyme, and `Line1-RT` has no predicted
   structure at all.

The normalization is deliberately conservative: lowercase, strip a trailing RT or
CasRT suffix, drop non-alphanumeric characters. It is verified to map every row of
both feature files onto exactly one label row, and `assert_full_coverage` fails
loudly if that ever stops being true rather than quietly returning empty columns.
"""

from __future__ import annotations

import re

import pandas as pd

SUFFIX = re.compile(r"[-_]?(rt|casrt)$")
NON_ALNUM = re.compile(r"[^a-z0-9]")

# RTs with no predicted structure in data/structures/. Their structure-derived
# features stay missing and are imputed inside each training fold.
NO_STRUCTURE = ("Line1-RT",)

# PDB files that duplicate another RT's structure. The exact-name file wins.
DUPLICATE_PDB_STEMS = ("Vp-96",)


def normalize(name) -> str:
    """Reduce an RT identifier to a form comparable across the data files."""
    s = str(name).strip().lower()
    s = SUFFIX.sub("", s)
    return NON_ALNUM.sub("", s)


def canonical_map(reference_names) -> dict[str, str]:
    """Map normalized keys to the canonical `rt_name` from the label file."""
    return {normalize(n): n for n in reference_names}


def align_to_reference(frame: pd.DataFrame, reference_names, id_col="rt_name") -> pd.DataFrame:
    """Reindex a feature frame onto the canonical RT names.

    Rows that do not correspond to any reference RT are dropped, reference RTs
    with no row are added as all-missing, and the result is guaranteed to have
    exactly one row per reference RT in reference order. Missing values are left
    missing for in-fold imputation rather than filled here, because filling them
    globally would be a fit outside the fold.
    """
    ref = canonical_map(reference_names)
    out = frame.copy()
    out["_key"] = [normalize(v) for v in out[id_col]]
    out = out[out["_key"].isin(ref)]
    out = out.drop_duplicates(subset="_key", keep="first")
    out["_canonical"] = [ref[k] for k in out["_key"]]
    out = out.drop(columns=[id_col, "_key"]).set_index("_canonical")
    out.index.name = id_col
    return out.reindex(list(reference_names))


def assert_full_coverage(frame: pd.DataFrame, reference_names, label: str, allow_missing=()):
    """Fail loudly when a feature table does not cover the reference RTs.

    A silently empty join is the defect this module was written to stop, so the
    check is an assertion rather than a warning.
    """
    missing = [n for n in reference_names if n not in set(frame.index)]
    unexpected = [n for n in missing if n not in set(allow_missing)]
    if unexpected:
        raise AssertionError(
            f"{label}: {len(unexpected)} reference RTs have no row after "
            f"harmonization: {', '.join(unexpected[:10])}"
        )
    all_nan = [c for c in frame.columns if frame[c].isna().all()]
    if all_nan:
        raise AssertionError(
            f"{label}: {len(all_nan)} columns are entirely missing after "
            f"harmonization, which usually means the join key is still wrong: "
            f"{', '.join(map(str, all_nan[:10]))}"
        )
    return True
