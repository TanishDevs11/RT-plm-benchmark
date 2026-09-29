# Origin and provenance

## Source

- Source repository: https://github.com/TanishDevs11/RT-Activity-Predictor
- Source commit SHA cloned: `c1620706685d1a29e874031abd62d88a763d241e`
- Clone date: 2026-09-29
- Inherited history at clone time: 55 commits, preserved in full

## Statement

This repository is a methodological rebuild. The source repository,
`TanishDevs11/RT-Activity-Predictor`, holds the original competition submission and is
not modified by this work in any way: no push, no branch, no tag, no pull request. The
only network read of the source was the initial `git clone` recorded above. The
inherited commit history is deliberately retained rather than squashed, because the
commit ladder that climbs from a reported CLS near 0.485 to a reported CLS of 0.975372
is primary evidence for the leakage audit carried out here, and it must remain
reachable by `git log`.

The purpose of this rebuild is not a higher score. It is a defensible measurement of
what the competition metric can and cannot resolve at n = 57, and an honest answer to
whether protein language model embeddings beat handcrafted features for out-of-family
enzyme function prediction. Inherited artifacts under `legacy_leaky/` and
`legacy_submission/` are the object of study, not inputs to any result reported here.

## Provenance tag

The inherited state is tagged `provenance` at the SHA recorded above, so the boundary
between inherited work and rebuild work stays auditable.
