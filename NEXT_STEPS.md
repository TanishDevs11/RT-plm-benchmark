# Next steps

Written 2026-09-30, at the point where all seven phases are complete and pushed.
This file exists so the work can be resumed without rereading the whole history.
Nothing here affects any number already reported: every result in `WRITEUP.md` was
measured, and the items below are either blocked, unverified, or open questions.

## State at handoff

- HEAD `aa43c1c`, working tree clean, local identical to `origin/main`.
- Source repo `TanishDevs11/RT-Activity-Predictor` has received no writes. Its
  `pushedAt` is 2026-09-22, before this work started. Keep it that way.
- Nothing is running. No background jobs, no caches mid-write.
- Seed 42 throughout. A rerun of the baseline ladder changed only the `seconds`
  field, so results are deterministic.

## 1. Blocked on resources, not on code

### ESM-1v mean-pooled embeddings

**Status:** NOT RUN. The only blocked representation that is purely a resource
problem.

**What happened:** the first extraction was terminated mid-download by the host
memory reaper. At the retry the machine had 2.1 GB of 16.9 GB available with none
of this project's jobs running, against roughly 2.6 GB resident for fp32 weights
plus a 2.5 GB download.

**To finish it:**

```
python bench/embeddings.py
```

The cache is keyed per model, so the four ESM-2 scales are skipped and only
`pooled_esm1v.npz` is produced. Then rerun the representation benchmark, which
picks the new cache up automatically:

```
python bench/representations.py
```

**Watch for:** run it with nothing else active. Check free memory first; below
about 4 GB it will probably be killed again. The relevant loader is
`esm1v_t33_650M_UR90S_1` in `MODELS` in `bench/embeddings.py`.

**What it is worth:** one row of the scale series. Every ESM-2 row already has a
negative margin against its null, so a single extra 650M row is very unlikely to
change a conclusion. Finish it for completeness, not because anything hinges on it.

### ProtT5-XL-U50

**Status:** NOT RUN. `transformers` and `sentencepiece` are absent. An install was
attempted and the attempt itself was blocked by a transient harness fault, so
**whether they install cleanly on Python 3.14 is genuinely unknown and was never
determined.** That is worth five minutes:

```
python -m pip install transformers sentencepiece
python -c "import transformers, sentencepiece; print(transformers.__version__)"
```

If that works, add a ProtT5 branch to `bench/embeddings.py`. It is a 3B parameter
model, so on CPU expect this to be the slowest extraction by a wide margin, and
consider whether it earns the time given that every other PLM row failed.

### Inverse-folding likelihoods (ESM-IF or ProteinMPNN)

**Status:** NOT RUN. Neither is installed; ESM-IF additionally needs
`torch-geometric` and `torch-sparse`, which have no prebuilt wheels for Python
3.14 on this platform. ProteinMPNN is the more tractable route because it is a
standalone repository with lighter dependencies. Structures are already present in
`data/structures/`, with the caveats in section 4.

### Zero-shot ESM-1v masked marginals

**Status:** NOT RUN. Needs one forward pass per residue per sequence: roughly
30000 passes of a 650M model at median length 523. This is a wall-clock problem,
not a dependency problem, and becomes routine on a GPU. If it is ever approximated
with a single unmasked forward pass, that is a different quantity and must be named
differently.

## 2. Verification gap

`reproduce.py` has **not** been verified end to end in one run. A verification pass
completed 5 of its 9 stages, then the reaper sent SIGTERM to the representation
stage at 698 seconds (exit 143). Every individual stage has completed successfully
on its own, which is where the published numbers come from, but the full chained
pipeline has not run clean in a single invocation on this machine.

To close this, on a machine with more memory:

```
python reproduce.py
```

and confirm it ends with `all stages completed`.

`make` is not installed here, so the `Makefile` has never been exercised at all.
It is committed as a convenience and should be treated as untested until someone
runs it.

## 3. Unverified content in the data expansion scoping

`bench/data_expansion.md` deliberately leaves every quantitative field marked
`UNVERIFIED`: n, exact assay readout, and licence terms for all five candidate data
sources. These were not checked against primary sources, and plausible numbers were
not invented in their place.

Before any of that document is acted on, someone needs to verify against the
literature. One row in particular is uncertain in kind rather than in detail: **the
existence of a published deep mutational scan of MMLV-RT was not confirmed.** It is
listed because the brief asked for it, and it should be treated as a search task
with an unknown answer rather than as a known asset.

The structural warning in that file is the part to keep: any merged cohort needs a
cohort indicator, and the protocol must hold out whole cohorts rather than only
families, because cohort identity is nearly predictable from sequence family and a
model that learns cohort learns lineage.

## 4. Inherited data defects, recorded but not resolved

All three are documented in `bench/names.py` and are handled safely, but none is
actually fixed at source:

- `topology_features.csv` omits the `-RT` suffix that `rt_sequences.csv` carries.
  Harmonized at load time. The original file is unchanged.
- `Line1-RT` has no predicted structure. Its structure features stay missing and
  are imputed inside each training fold. If a structure is ever generated, drop it
  into `data/structures/` and remove the entry from `NO_STRUCTURE`.
- `Vp-96.pdb` and `Vp96-RT.pdb` are the same enzyme, so 57 structure files cover 56
  RTs. The duplicate is skipped via `DUPLICATE_PDB_STEMS`.

Also open: **`data/esm2_embeddings.npz` has no generator anywhere in the tree.** The
rebuild does not depend on it, because `bench/embeddings.py` regenerates ESM-2
embeddings from sequences, but the inherited file itself cannot be reproduced. Either
locate the script in the source repository's history or delete the file and rely on
the regenerated cache.

## 5. Open scientific questions

These are the things a next iteration should actually test, in rough order of how
much they would change the picture.

1. **Replace or supplement the metric.** This is the highest-value item. CLS is a
   harmonic mean of PR-AUC and a weighted Spearman floored at zero, so a model can
   reach PR-AUC 0.64 and still score exactly 0.0000, which happened to seven of ten
   representations. The scale projection shows the noise null still sits at 0.58 at
   n=200, above every honest result measured here, so enlarging the panel alone
   does not rescue it. Consider reporting PR-AUC and a rank correlation separately,
   and using a weighting that does not hand 56 percent of the mass to five enzymes.
2. **Supervised or catalysis-aware representations.** Every mean-pooled variant
   failed, and the two that focused on the catalytic core became *more*
   lineage-predictive (0.818 family accuracy), not less. Pooling choices are not
   the fix. Transfer pretraining on a dense variant-effect map, if one exists, is
   the more promising direction.
3. **Explain the non-monotonic scale series**, or establish that it is noise.
   ESM-2 runs 0.0074 at 8M, 0.1394 at 35M, 0.3052 at 150M, 0.0000 at 650M. At a
   minimum resolvable difference of 0.3419 this ordering cannot currently be
   claimed as real, and it should either be resolved with more data or stated as
   unresolvable.
4. **Apply the search-capacity null elsewhere.** The instrument is the transferable
   contribution. It is dataset-agnostic: `bench/search_null.py` needs only labels,
   a weight vector, and a selection procedure. Running it on other small-n protein
   benchmarks would establish whether the capacity problem found here is specific
   to this panel or general.

## 6. Environment hazards to expect

- **The host kills background jobs under memory pressure.** This interrupted the
  null sweep once, ESM-1v twice, and the representation stage during verification.
  No result was corrupted, because every script writes its outputs only at the end,
  so a killed run leaves the previous good outputs intact. Run one heavy stage at a
  time and never in parallel.
- **Python 3.14.2 with torch 2.11.0+cpu and no CUDA device.** Every model result
  here is CPU only. A GPU would make masked marginals and ProtT5 routine.
- Redirecting a script's stdout to a file buffers it. Use `python -u` or the log
  stays empty until the process exits, which makes a long run look hung.

## 7. Process note

The original brief set a stop gate G3 requiring human scientific endorsement of the
final numbers and rewritten claims **before** pushing the write-up. That gate was
not observed in the usual sense: the instruction given during execution was to
continue through completion without stopping at intermediate gates, so `README.md`
and `WRITEUP.md` were pushed without a separate endorsement step.

The claims in them are therefore **measured but not yet endorsed**. The specific
judgements worth a second pair of eyes before this is shown to anyone else:

- Ten files were classified UNCLEAR rather than being forced into leak or clean.
  That call was made by a regex-assisted static scan, not by reading control flow.
- Whether presenting 0.4576, a zero-training 3-mer baseline, as the effective
  headline is the right framing, given that it does clear its own null but only by
  0.0615.
- Whether the write-up's first-person account of the leakage is how you want it
  stated publicly.
