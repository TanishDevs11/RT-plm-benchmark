# Task B dataset survey: acquisition log

Every URL touched in deciding what Task B becomes, with status, bytes, content type and
SHA256 of the response body. Written 2026-10-03.

Three sections. The first is this survey's own attempts. The second and third restate the
M-MLV routes attempted before the survey, so that the record of that dataset is complete
in one place rather than spread across three files.

User-Agent sent on every request:

```
RT-plm-benchmark-survey/0.1 (open benchmark of protein representations for reverse
transcriptase function; contact shyamarunach@gmail.com)
```

A SHA256 of `n/a` means the request did not return a body to hash: a transport error, or
a HEAD request. Partial rows are HTTP range requests, used instead of whole-archive
downloads; the hash is of the range received, not of the archive.

## 1. This survey, 61 attempts

### Candidate 0, M-MLV RT saturated mutagenesis, 15 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| figshare: M-MLV reverse transcriptase prime editing | 404 | 222 | text/html; charset=UTF-8 | `2151e09df660fa17...` | non-200 |
| figshare: saturated mutagenesis prime editor | 404 | 222 | text/html; charset=UTF-8 | `2151e09df660fa17...` | non-200 |
| figshare: PE2 reverse transcriptase variants | 404 | 222 | text/html; charset=UTF-8 | `2151e09df660fa17...` | non-200 |
| OpenAlex citing works | 400 | 117 | application/json | `3663a8e865219862...` | non-200 |
| bioRxiv details, version recheck | 200 | 2163 | application/json | `f2f01615f2a81e01...` | ok |
| figshare POST search: M-MLV reverse transcriptase prime editing | 200 | 2 | application/json | `4f53cda18c2baa0c...` | ok |
| figshare POST search: saturated mutagenesis prime editor | 200 | 2 | application/json | `4f53cda18c2baa0c...` | ok |
| figshare POST search: PE2dR | 200 | 2 | application/json | `4f53cda18c2baa0c...` | ok |
| OpenAlex work record | 200 | 23766 | application/json | `26b312d44af900c3...` | ok |
| OpenAlex citing works | 200 | 378 | application/json | `12c6ac66d994ddd3...` | ok |
| RCSB full-text: M-MLV RT | 200 | 484 | application/json | `e0f17c227239865a...` | ok |
| RCSB entry 4MH8 | 200 | 12966 | application/json | `c6cf3d93d18c7767...` | ok |
| RCSB polymer entity 4MH8/1 | 200 | 44136 | application/json | `bb2f0c606966223b...` | ok |
| RCSB entry 1D0E | 200 | 12567 | application/json | `a5a111a05d858ce4...` | ok |
| RCSB polymer entity 1D0E/1 | 200 | 1205 | application/json | `bd74b8bc145263fa...` | ok |

URLs in full, in request order:

1. `https://api.figshare.com/v2/articles/search?search_for=%22M-MLV%20reverse%20transcriptase%20prime%20editing%22&page_size=20`
2. `https://api.figshare.com/v2/articles/search?search_for=%22saturated%20mutagenesis%20prime%20editor%22&page_size=20`
3. `https://api.figshare.com/v2/articles/search?search_for=%22PE2%20reverse%20transcriptase%20variants%22&page_size=20`
4. `https://api.openalex.org/works?filter=cites:doi:10.64898/2026.07.06.736660&per-page=25&mailto=shyamarunach@gmail.com`
5. `https://api.biorxiv.org/details/biorxiv/10.64898/2026.07.06.736660`
6. `https://api.figshare.com/v2/articles/search (POST body search_for=M-MLV reverse transcriptase prime editing)`
7. `https://api.figshare.com/v2/articles/search (POST body search_for=saturated mutagenesis prime editor)`
8. `https://api.figshare.com/v2/articles/search (POST body search_for=PE2dR)`
9. `https://api.openalex.org/works/doi:10.64898/2026.07.06.736660?mailto=shyamarunach@gmail.com`
10. `https://api.openalex.org/works?filter=cites:W7167616871&per-page=25&mailto=shyamarunach@gmail.com`
11. `https://search.rcsb.org/rcsbsearch/v2/query (POST value=Moloney murine leukemia virus reverse transcriptase)`
12. `https://data.rcsb.org/rest/v1/core/entry/4MH8`
13. `https://data.rcsb.org/rest/v1/core/polymer_entity/4MH8/1`
14. `https://data.rcsb.org/rest/v1/core/entry/1D0E`
15. `https://data.rcsb.org/rest/v1/core/polymer_entity/1D0E/1`

### Candidate 1, ProteinGym, 28 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| ProteinGym README (raw) | 200 | 26106 | text/plain; charset=utf-8 | `321487a8de52c6cf...` | ok |
| ProteinGym DMS_substitutions.csv reference file | 200 | 208734 | text/plain; charset=utf-8 | `a8f498011532a74a...` | ok |
| ProteinGym substitutions archive (HEAD) | 200 | 0 | application/zip | `n/a` | ok, size 43021128 |
| ZIP end-of-central-directory tail [bytes=41021128-43021127] | 206 | 2000000 | application/zip | `417071102dd67d54...` | ok |
| ZIP central directory [bytes=42992822-43021105] | 206 | 28284 | application/zip | `d43ea74f3d1057a9...` | ok |
| ZIP local header: DMS_ProteinGym_substitutions/BLAT_ECOLX_Firnberg_2014.csv [bytes=10044879-1... | 206 | 30 | application/zip | `11aa797312fea60a...` | ok |
| ZIP member data: DMS_ProteinGym_substitutions/BLAT_ECOLX_Firnberg_2014.csv [bytes=10044994-10... | 206 | 53296 | application/zip | `7eea3735b3115fff...` | ok |
| ZIP local header: DMS_ProteinGym_substitutions/BLAT_ECOLX_Stiffler_2015.csv [bytes=33504655-3... | 206 | 30 | application/zip | `8578846d73f8f983...` | ok |
| ZIP member data: DMS_ProteinGym_substitutions/BLAT_ECOLX_Stiffler_2015.csv [bytes=33504770-33... | 206 | 74992 | application/zip | `5c15a6664bbe582e...` | ok |
| ZIP local header: DMS_ProteinGym_substitutions/GFP_AEQVI_Sarkisyan_2016.csv [bytes=29590791-2... | 206 | 30 | application/zip | `88f37bbd0af974a4...` | ok |
| ZIP member data: DMS_ProteinGym_substitutions/GFP_AEQVI_Sarkisyan_2016.csv [bytes=29590906-31... | 206 | 1432309 | application/zip | `cbe04d1e6448b408...` | ok |
| ZIP local header: DMS_ProteinGym_substitutions/CAPSD_AAV2S_Sinai_2021.csv [bytes=35898344-358... | 206 | 30 | application/zip | `26cc1eec4f1b4904...` | ok |
| ZIP member data: DMS_ProteinGym_substitutions/CAPSD_AAV2S_Sinai_2021.csv [bytes=35898457-3703... | 206 | 1136579 | application/zip | `a5b65d3f482fc091...` | ok |
| ProteinGym repo tree | 200 | 191646 | application/json; charset=utf-8 | `72903f76e04ffb0c...` | ok |
| ProteinGym published baselines: zero_shot_spearman | 200 | 141235 | text/plain; charset=utf-8 | `f432423b87f79ac9...` | ok |
| ProteinGym published baselines: supervised_spearman_random | 200 | 20404 | text/plain; charset=utf-8 | `9ec9288d0f5e1530...` | ok |
| ProteinGym published baselines: supervised_spearman_contiguous | 200 | 20506 | text/plain; charset=utf-8 | `94f0c739b3dd55a8...` | ok |
| ProteinGym published baselines: supervised_spearman_modulo | 200 | 20486 | text/plain; charset=utf-8 | `4a4e97c3359172f2...` | ok |
| ProteinGym LICENSE | 200 | 1134 | text/plain; charset=utf-8 | `9b0d23df61da60c3...` | ok |
| ProteinGym CV folds archive (HEAD) | 200 | 0 | application/zip | `n/a` | ok, size 13412036 |
| ZIP end-of-central-directory tail [bytes=11412036-13412035] | 206 | 2000000 | application/zip | `9928b6d4f1616ddd...` | ok |
| ZIP central directory [bytes=13383294-13412013] | 206 | 28720 | application/zip | `c9873f7480b85b96...` | ok |
| ZIP local header: cv_folds_singles_substitutions/BLAT_ECOLX_Firnberg_2014.csv [bytes=2144740-... | 206 | 30 | application/zip | `f4e13ae737b5f488...` | ok |
| ZIP member data: cv_folds_singles_substitutions/BLAT_ECOLX_Firnberg_2014.csv [bytes=2144857-2... | 206 | 58766 | application/zip | `9fc79a4daef79831...` | ok |
| ProteinGym zero-shot summary performance | 200 | 44132 | text/plain; charset=utf-8 | `ee61a7c09efbfbd8...` | ok |
| Harvard host LICENSE probe | 404 | 236 | text/html; charset=iso-8859-1 | `9448f8a1159c9b14...` | non-200 |
| Harvard host v1.3 LICENSE probe | 404 | 236 | text/html; charset=iso-8859-1 | `9448f8a1159c9b14...` | non-200 |
| GitHub code search: permutation in ProteinGym | 401 | 120 | application/json; charset=utf-8 | `b7dbd173f33b1965...` | non-200 |

URLs in full, in request order:

1. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/README.md`
2. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/reference_files/DMS_substitutions.csv`
3. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
4. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
5. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
6. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
7. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
8. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
9. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
10. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
11. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
12. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
13. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
14. `https://api.github.com/repos/OATML-Markslab/ProteinGym/git/trees/main?recursive=1`
15. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_zero_shot/substitutions/Spearman/DMS_substitutions_Spearman_DMS_level.csv`
16. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_supervised/substitutions/Spearman/DMS_substitutions_Spearman_DMS_level_fold_random_5.csv`
17. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_supervised/substitutions/Spearman/DMS_substitutions_Spearman_DMS_level_fold_contiguous_5.csv`
18. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_supervised/substitutions/Spearman/DMS_substitutions_Spearman_DMS_level_fold_modulo_5.csv`
19. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/LICENSE`
20. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/cv_folds_singles_substitutions.zip`
21. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/cv_folds_singles_substitutions.zip`
22. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/cv_folds_singles_substitutions.zip`
23. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/cv_folds_singles_substitutions.zip`
24. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/cv_folds_singles_substitutions.zip`
25. `https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/benchmarks/DMS_zero_shot/substitutions/Spearman/Summary_performance_DMS_substitutions_Spearman.csv`
26. `https://marks.hms.harvard.edu/proteingym/LICENSE`
27. `https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/LICENSE`
28. `https://api.github.com/search/code?q=repo:OATML-Markslab/ProteinGym+permutation`

### Candidate 2, TEM-1 beta-lactamase, 1 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| RCSB full-text: TEM-1 | 200 | 515 | application/json | `6e52e620e53e93b2...` | ok |

URLs in full, in request order:

1. `https://search.rcsb.org/rcsbsearch/v2/query (POST value=TEM-1 beta-lactamase)`

### Candidate 3, GFP, 1 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| RCSB full-text: avGFP | 200 | 515 | application/json | `0697e3502bac23b3...` | ok |

URLs in full, in request order:

1. `https://search.rcsb.org/rcsbsearch/v2/query (POST value=green fluorescent protein Aequorea)`

### Candidate 4, AAV capsid, 1 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| RCSB full-text: AAV2 capsid | 200 | 513 | application/json | `bf56a83f9b7f4055...` | ok |

URLs in full, in request order:

1. `https://search.rcsb.org/rcsbsearch/v2/query (POST value=adeno-associated virus 2 capsid)`

### Candidate 5, other reverse transcriptase variant data, 15 attempts

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| MaveDB GET: score-sets/search?search=reverse%20transcriptase | 404 | 50 | application/json | `9819cf2342c19679...` | non-200 |
| MaveDB GET: experiments/search?search=reverse%20transcriptase | 404 | 49 | application/json | `1fd8c798a0da1fc2...` | non-200 |
| MaveDB GET: target-genes | 200 | 3158483 | application/json | `0b5f9381dd4241db...` | ok |
| MaveDB full target-gene list | 200 | 3158483 | application/json | `0b5f9381dd4241db...` | ok |
| Europe PMC: ("reverse transcriptase" AND "deep mutational scan") | 200 | 88447 | application/json;charset=UTF-8 | `b02b184e9d794c38...` | ok |
| Europe PMC: ("reverse transcriptase" AND ("saturation mutagenesis" OR  | 200 | 92960 | application/json;charset=UTF-8 | `610701206c5a01f6...` | ok |
| Europe PMC: ("telomerase reverse transcriptase" AND "deep mutational") | 200 | 43578 | application/json;charset=UTF-8 | `bcac93132bf79423...` | ok |
| Europe PMC: ("retron" AND "reverse transcriptase" AND variant) | 200 | 84921 | application/json;charset=UTF-8 | `134ae425cfc493fb...` | ok |
| Europe PMC: ("group II intron" AND "reverse transcriptase" AND (librar | 200 | 74783 | application/json;charset=UTF-8 | `a5cfb7968cfec62a...` | ok |
| Europe PMC: ("prime editing" AND "reverse transcriptase" AND ("variant | 200 | 76416 | application/json;charset=UTF-8 | `7a1bb6e0c06bc8b7...` | ok |
| Europe PMC: retron variant library paper | 200 | 269 | application/json;charset=UTF-8 | `7522b873e9a79d34...` | ok |
| Europe PMC: retron design rules | 200 | 203 | application/json;charset=UTF-8 | `d29e4e8f0fadedf6...` | ok |
| Europe PMC: prime editing RT variant libraries, full records | 200 | 181125 | application/json;charset=UTF-8 | `5efca0c3612bb50f...` | ok |
| Europe PMC supplementaryFiles: PMC11754653 | 200 | 4279619 | application/zip | `3890c2a380bea4fc...` | ok |
| RCSB full-text: HIV-1 RT | 200 | 514 | application/json | `f3ba8dc1beec8cfb...` | ok |

URLs in full, in request order:

1. `https://api.mavedb.org/api/v1/score-sets/search?search=reverse%20transcriptase`
2. `https://api.mavedb.org/api/v1/experiments/search?search=reverse%20transcriptase`
3. `https://api.mavedb.org/api/v1/target-genes`
4. `https://api.mavedb.org/api/v1/target-genes`
5. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22reverse%20transcriptase%22%20AND%20%22deep%20mutational%20scan%22%29`
6. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22reverse%20transcriptase%22%20AND%20%28%22saturation%20mutagenesis%22%20OR%20%22saturated%20mutagenesis%22%29%29`
7. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22telomerase%20reverse%20transcriptase%22%20AND%20%22deep%20mutational%22%29`
8. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22retron%22%20AND%20%22reverse%20transcriptase%22%20AND%20variant%29`
9. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22group%20II%20intron%22%20AND%20%22reverse%20transcriptase%22%20AND%20%28library%20OR%20variants%29%29`
10. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%28%22prime%20editing%22%20AND%20%22reverse%20transcriptase%22%20AND%20%28%22variant%20library%22%20OR%20%22mutational%20scan%22%29%29`
11. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=5&resultType=core&query=TITLE%3A%22High%20throughput%20variant%20libraries%20and%20machine%20learning%20yield%20design%20rules%20for%20retron%20gene%20editing%22`
12. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&resultType=core&query=%22design%20rules%20for%20retron%20gene%20editing%22`
13. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=25&resultType=core&query=%28%22prime%20editing%22%20AND%20%22reverse%20transcriptase%22%20AND%20%28%22variant%20libraries%22%20OR%20%22variant%20library%22%20OR%20%22mutational%20scan%22%29%29`
14. `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11754653/supplementaryFiles`
15. `https://search.rcsb.org/rcsbsearch/v2/query (POST value=HIV-1 reverse transcriptase)`

## 2. M-MLV label routes attempted before this survey, 30 attempts

From `data_acquisition/fetch_mmlv_dms_attempts.json`, access date 2026-10-03.
Routes 1 to 4 are the Task B brief's; routes 5 and 6 were added when the brief's route 3
turned out to be conditional on a single API's answer.

| route | what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | bioRxiv API details | 200 | 2163 | application/json | `f2f01615f2a81e01...` | resolved: version 1, posted 2026-07-07, licence cc_by_nc |
| 2 | bioRxiv API published version | 200 | 96 | application/json | `f1ec7ef445373988...` | no published version of this preprint exists yet |
| 1 | bioRxiv supplementary-material page v1 | 200 | 107089 | text/html; charset=utf-8 | `4d2a0b3e2c3cbab2...` | page served, no data-bearing supplementary link |
| 1 | bioRxiv supplementary-material page v2 | 200 | 29954 | text/html; charset=utf-8 | `6a77e67cbfc9f103...` | page served, no data-bearing supplementary link |
| 1 | bioRxiv supplementary-material page current | 200 | 106819 | text/html; charset=utf-8 | `3bde63b5d299f20b...` | page served, no data-bearing supplementary link |
| 2 | bioRxiv JATS XML | 200 | 77870 | application/xml | `57c829ef73304dce...` | 0 supplementary-material block(s), 20 href(s) |
| 3 | published journal version | n/a | 0 | n/a | `n/a` | skipped: the bioRxiv API reports no published version, so there is no journal or PMC mirror t... |
| 4 | Zenodo | 200 | 483 | application/json | `bcab6b096c98ef33...` | 0 result(s), 0 plausibly relevant |
| 4 | Zenodo, by title | 200 | 485 | application/json | `5779c24426ae65b2...` | 0 result(s), 0 plausibly relevant |
| 4 | Dryad | 200 | 318 | application/json; charset=utf-8 | `dd008f3ff0cb3198...` | 0 result(s), 0 plausibly relevant |
| 4 | OSF | 200 | 128 | application/vnd.api+json; charset=utf-8 | `337a5845bf62ccbe...` | 0 result(s), 0 plausibly relevant |
| 4 | GitHub repositories | 200 | 55 | application/json; charset=utf-8 | `4af480b8ee5b87b3...` | 0 result(s), 0 plausibly relevant |
| 4 | GitHub code, by variant table | 200 | 55 | application/json; charset=utf-8 | `4af480b8ee5b87b3...` | 0 result(s), 0 plausibly relevant |
| 5 | Crossref, by title | 200 | 26634 | application/json | `f9b6a92d82ec904c...` | 5 record(s), 1 of them this work, 0 pointing at a journal version |
| 5 | Crossref, the record itself, for a link to a journal article | 200 | 10737 | application/json | `4ccf39d7dbbb8bdd...` | 1 record(s), 1 of them this work, 0 pointing at a journal version |
| 5 | OpenAlex | 200 | 156466 | application/json | `17942ea7e8291c93...` | 5 record(s), 1 of them this work, 0 pointing at a journal version |
| 5 | Semantic Scholar | 429 | 174 | application/json | `65ab993d12c5c2cc...` | non-200 |
| 5 | Europe PMC, by title | 200 | 3940 | application/json;charset=UTF-8 | `812c62cd1ac99609...` | 1 record(s), 1 of them this work, 0 pointing at a journal version |
| 6 | bioproject: PE2dR | 200 | 339 | application/json; charset=UTF-8 | `df9e5a305ad74ed5...` | 0 record(s) |
| 6 | bioproject: "prime editing" AND "saturated mutagenesis" | 200 | 442 | application/json; charset=UTF-8 | `927c3a1d5ef4e356...` | 0 record(s) |
| 6 | bioproject: "reverse transcriptase" AND "prime editor" AND screen | 200 | 550 | application/json; charset=UTF-8 | `3be02a02ffaabf75...` | 0 record(s) |
| 6 | bioproject: "PEmax" AND "RNase H" | 200 | 399 | application/json; charset=UTF-8 | `a5805a0b92497fdb...` | 0 record(s) |
| 6 | gds: PE2dR | 200 | 339 | application/json; charset=UTF-8 | `df9e5a305ad74ed5...` | 0 record(s) |
| 6 | gds: "prime editing" AND "saturated mutagenesis" | 200 | 444 | application/json; charset=UTF-8 | `34ddc3c5b31b38d1...` | 0 record(s) |
| 6 | gds: "reverse transcriptase" AND "prime editor" AND screen | 200 | 807 | application/json; charset=UTF-8 | `0370527329dd3e9a...` | 3 record(s) |
| 6 | gds: "PEmax" AND "RNase H" | 200 | 401 | application/json; charset=UTF-8 | `8255c65f8575877d...` | 0 record(s) |
| 6 | sra: PE2dR | 200 | 339 | application/json; charset=UTF-8 | `df9e5a305ad74ed5...` | 0 record(s) |
| 6 | sra: "prime editing" AND "saturated mutagenesis" | 200 | 444 | application/json; charset=UTF-8 | `e8e40e59e6ac1659...` | 0 record(s) |
| 6 | sra: "reverse transcriptase" AND "prime editor" AND screen | 200 | 557 | application/json; charset=UTF-8 | `7ef8b08e67fb1ed5...` | 0 record(s) |
| 6 | sra: "PEmax" AND "RNase H" | 200 | 403 | application/json; charset=UTF-8 | `8ffaacc6b30e2b23...` | 0 record(s) |

URLs in full:

1. route 2: `https://api.biorxiv.org/details/biorxiv/10.64898/2026.07.06.736660`
2. route 2: `https://api.biorxiv.org/pubs/biorxiv/10.64898/2026.07.06.736660`
3. route 1: `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material`
4. route 1: `https://www.biorxiv.org/content/10.64898/2026.07.06.736660v2.supplementary-material`
5. route 1: `https://www.biorxiv.org/content/10.64898/2026.07.06.736660.supplementary-material`
6. route 2: `https://www.biorxiv.org/content/early/2026/07/07/2026.07.06.736660.source.xml`
7. route 3: `n/a`
8. route 4: `https://zenodo.org/api/records?q=%22M-MLV%20reverse%20transcriptase%22%20AND%20%22prime%20editing%22&size=20`
9. route 4: `https://zenodo.org/api/records?q=%22saturated%20mutagenesis%22%20AND%20%22reverse%20transcriptase%22&size=20`
10. route 4: `https://datadryad.org/api/v2/search?q=M-MLV%20reverse%20transcriptase%20prime%20editing`
11. route 4: `https://api.osf.io/v2/nodes/?filter[title]=saturated%20mutagenesis%20reverse%20transcriptase`
12. route 4: `https://api.github.com/search/repositories?q=M-MLV%20reverse%20transcriptase%20prime%20editing%20mutagenesis`
13. route 4: `https://api.github.com/search/repositories?q=PE2%20reverse%20transcriptase%20saturation%20mutagenesis%20screen`
14. route 5: `https://api.crossref.org/works?rows=5&query.bibliographic=Saturated%20mutagenesis%20screen%20of%20M-MLV%20reverse%20transcriptase`
15. route 5: `https://api.crossref.org/works/10.64898/2026.07.06.736660`
16. route 5: `https://api.openalex.org/works?per-page=5&search=Saturated%20mutagenesis%20screen%20of%20M-MLV%20reverse%20transcriptase`
17. route 5: `https://api.semanticscholar.org/graph/v1/paper/search?limit=5&fields=title,externalIds,venue,year&query=Saturated%20mutagenesis%20screen%20of%20M-MLV%20reverse%20transcriptase`
18. route 5: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=core&pageSize=5&query=TITLE%3A%22Saturated%20mutagenesis%20screen%20of%20M-MLV%20reverse%20transcriptase%22`
19. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&retmode=json&retmax=10&term=PE2dR`
20. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&retmode=json&retmax=10&term=%22prime%20editing%22%20AND%20%22saturated%20mutagenesis%22`
21. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&retmode=json&retmax=10&term=%22reverse%20transcriptase%22%20AND%20%22prime%20editor%22%20AND%20screen`
22. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&retmode=json&retmax=10&term=%22PEmax%22%20AND%20%22RNase%20H%22`
23. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json&retmax=10&term=PE2dR`
24. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json&retmax=10&term=%22prime%20editing%22%20AND%20%22saturated%20mutagenesis%22`
25. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json&retmax=10&term=%22reverse%20transcriptase%22%20AND%20%22prime%20editor%22%20AND%20screen`
26. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json&retmax=10&term=%22PEmax%22%20AND%20%22RNase%20H%22`
27. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&retmode=json&retmax=10&term=PE2dR`
28. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&retmode=json&retmax=10&term=%22prime%20editing%22%20AND%20%22saturated%20mutagenesis%22`
29. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&retmode=json&retmax=10&term=%22reverse%20transcriptase%22%20AND%20%22prime%20editor%22%20AND%20screen`
30. route 6: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&retmode=json&retmax=10&term=%22PEmax%22%20AND%20%22RNase%20H%22`

## 3. The reference resolution, 5 attempts

From `data_acquisition/fetch_pe2_plasmid_attempts.json`, access date 2026-10-03.
These succeeded: they are what resolved the PE2dR reference from Addgene 132775.

| what was asked | status | bytes | content type | SHA256 | outcome |
| --- | --- | --- | --- | --- | --- |
| plasmid page | 200 | 242991 | text/html; charset=utf-8 | `011f06ef78601f56...` | ok |
| sequences page | 200 | 206328 | text/html; charset=utf-8 | `8f25314e6149387c...` | ok |
| sequence analysis page | 200 | 222109 | text/html; charset=utf-8 | `80050cf9e6be06fc...` | ok |
| genbank | 404 | 9 | text/plain;charset=UTF-8 | `0019dfc4b32d63c1...` | non-200 |
| sequence lines | 200 | 7537177 | application/json | `8fdd715107ae5c27...` | ok |

URLs in full:

1. `https://www.addgene.org/132775/`
2. `https://www.addgene.org/132775/sequences/`
3. `https://www.addgene.org/browse/sequence/259720/`
4. `https://sequences.addgene.org/snapgene-media/v3.101.0/sequences/259720/77be6b1b-d243-4c8c-bd5f-84f709c92280/addgene-plasmid-132775-sequence-259720.gbk`
5. `https://sequences.addgene.org/snapgene-media/v3.101.0/sequences/259720/77be6b1b-d243-4c8c-bd5f-84f709c92280/addgene-plasmid-132775-sequence-259720-sequence-lines.json`

## Totals

| section | attempts | distinct hosts |
| --- | --- | --- |
| this survey | 61 | 10 |
| M-MLV label routes | 30 | 11 |
| reference resolution | 5 | 2 |
| **all** | **96** | |

