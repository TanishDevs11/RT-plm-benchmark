# Draft request to the Task B corresponding author

**This is a draft for a human to send. Nothing here has been sent.** It was written at Gate G3,
after four independent routes established that the supplementary material is not publicly
deposited (see `tasks/taskB_mmlv_dms/PROVENANCE.md`, section B2).

## Why this exists

Task B is the within-protein variant effect half of this benchmark, and the contrast between it
and the cross-family Task A is the deliverable. Its labels are the per-variant editing
efficiencies in Supplementary Tables S6 and S7 of the preprint, and those tables were not
deposited with version 1. The preprint carries no Data Availability statement, so there is no
repository to check.

Everything else on the Task B side is already done and waiting: the reference frame is resolved
and confirmed four ways, the 1045 expected variant identifiers are derived and frozen, all three
split regimes are written, and the parser only needs the two tables plus one sequence.

## Recipient

| field | value |
| --- | --- |
| corresponding author | Haojie Yu, listed as Lead Contact |
| email, as printed in the preprint | `bchhaoy@nus.edu.sg` |
| affiliation | Precision Medicine Research Programme and Cardiovascular Disease Research Programme, Yong Loo Lin School of Medicine, National University of Singapore |
| co-first authors | Hui Li and Yifan Wang |
| preprint | bioRxiv, DOI `10.64898/2026.07.06.736660`, posted 2026-07-07 |

Taken from page 1 of `tasks/taskB_mmlv_dms/raw/preprint.pdf`. Verify it against the current
version of the preprint before sending, in case a later version changes the contact.

## What to ask for, and why each item matters

Three things, in order of how much they unblock:

1. **Supplementary Tables S6 and S7**, the per-variant normalized editing efficiencies for
   libraries L1 and L2. Without these Task B has no labels at all.
2. **Supplementary Sequence 1**, the PE2ΔR construct protein sequence. The numbering is already
   resolved, but the construct's substitution content is not: whether it retains PE2's D200N,
   T306K, W313F and T330P is undetermined, and building 1046 variant sequences on a reference
   wrong at four positions would invalidate the whole task.
3. **Whether the scaling to the interval from -1 to 1 was computed within each library or across
   both.** This one is a single sentence of clarification rather than a file, and it decides how
   the headline stretch-held-out result has to be reported: if the libraries were scaled
   separately, then training on one and testing on the other also crosses two normalizations.

## Draft message

Adjust the tone and the signature to suit. Keep the specifics: a request that names the exact
tables and states what they are for is much easier to act on than a general one.

> Subject: Request for Supplementary Tables S6 and S7, and Supplementary Sequence 1, from your
> M-MLV RT saturated mutagenesis preprint
>
> Dear Dr Yu,
>
> I am working on an open benchmark of protein representation methods for reverse transcriptase
> function, and your preprint "Saturated mutagenesis screen of M-MLV reverse transcriptase
> identifies variants enhancing prime editing efficiency" (bioRxiv, DOI
> 10.64898/2026.07.06.736660) is the best available dataset for the within-protein variant
> effect half of it. Your saturating libraries over the S60-Q84 and N95-D124 stretches are
> exactly the kind of dense, single-assay, single-protein measurement that the field's
> cross-family datasets cannot provide.
>
> The supplementary files do not appear to be attached to the bioRxiv record: the
> supplementary-material page lists none, and Europe PMC indexes the preprint without
> supplementary content. I wanted to check whether they could be shared directly rather than
> assume they were withheld deliberately.
>
> Specifically, I would be grateful for:
>
> 1. Supplementary Tables S6 and S7, the per-variant editing efficiency values for libraries L1
>    and L2.
> 2. Supplementary Sequence 1, the PE2ΔR protein sequence. I have resolved the numbering against
>    UniProt P03355 and confirmed it at nine residue positions, but I cannot tell from the main
>    text whether the construct retains the PE2 RT substitutions D200N, T306K, W313F and T330P.
>    Since L603 falls inside the deleted RNase H region, I believe L603W is not present, but I
>    would rather confirm than infer.
> 3. One clarification if you have a moment: was the scaling of editing efficiency to the
>    interval from -1 to 1 computed within each library separately, or across both libraries
>    together? This affects whether a model trained on one stretch and tested on the other is
>    also crossing two normalizations, which I would need to state when reporting that result.
>
> On attribution and use: the work is a public, non-commercial methodological benchmark, and any
> use of your data would cite the preprint and state clearly that the labels are yours. I am
> happy to share what I find, including the split definitions and the reference-frame resolution,
> and to hold the data privately if you would prefer it not be redistributed before publication.
>
> Thank you for considering this, and for a genuinely useful dataset.
>
> With best regards,
> [name]
> [affiliation, if any]

## Two things to be careful about

- **Do not redistribute the tables without permission.** The preprint itself is CC-BY-NC 4.0 and
  is committed to `raw/` on that basis, but supplementary files shared privately by an author
  carry whatever terms the author sets. If they are shared privately, they go in `raw/` locally
  and `PROVENANCE.md` records that they must not be committed, and the repository keeps only a
  parser plus the recorded checksums.
- **If there is no reply, that is a result too.** It goes in
  `reports/data_pipeline_report.md` as the outcome of a recorded attempt, not as a reason to
  estimate, model, or reconstruct the values. There is no acceptable substitute for the labels:
  a simulated deep mutational scan would make every downstream number meaningless.

## What to do once the files arrive

1. Place them per `MANUAL_FETCH.md` and run `python data_acquisition/check_inputs.py`.
2. Resolve the substitution content and write `tasks/taskB_mmlv_dms/raw/reference.fasta`, which
   supersedes `reference_candidate_unconfirmed.fasta`.
3. Write the Task B parser, asserting the wild-type residue at every one of the 55 diversified
   positions and halting on any mismatch.
4. Reconcile the parsed variants against the frozen split files, which already contain the
   complete expected identifier set. Any variant in one and not the other is a discrepancy to log.
