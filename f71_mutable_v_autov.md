# Fedora Comparison: mutable_creation_f71 vs autov_creation_f71

Negative duration changes mean the comparison configuration is faster. Operation counts are context only; all other values are per-operation averages.

## mutable_creation_f71
Pooled runs: **6** (`stats_20261010_121644_104522.json`, `stats_20261010_212828_476316.json`, `stats_20261011_125953_580229.json`, `stats_20261011_132134_194799.json`, `stats_20261011_135311_138624.json`, `stats_20261011_141441_561843.json`)

### Creation Timing
| Collection type | Successful | Failed | Workflow mean (95% CI) | Workflow median / p95 / p99 | Commit mean (95% CI) | Commit median / p95 / p99 |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 2111 | 0 | 0.1528s (0.1511s to 0.1545s) | 0.1424s / 0.2197s / 0.2898s | 0.0899s (0.0885s to 0.0913s) | 0.0793s / 0.1485s / 0.2014s |
| Archival Group | 2047 | 0 | 0.0946s (0.0937s to 0.0956s) | 0.0897s / 0.1313s / 0.1850s | 0.0328s (0.0322s to 0.0334s) | 0.0283s / 0.0556s / 0.0814s |

### Collection Creation Storage
| Collection type | Collections | Avg workflow | Avg commit | Avg files | Avg directories | Avg OCFL size |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 3 | 0.2426s | 0.0959s | 58.00 | 60.00 | 21,416 bytes (20.91 KB) |
| Archival Group | 3 | 0.1137s | 0.0354s | 19.00 | 13.67 | 13,022 bytes (12.72 KB) |

### PATCH Storage
| Collection type | PATCHes | Sequences | Avg duration | Avg file / directory / size delta | Mean growth rate | Mean projected storage after 100 PATCHes |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 160 | 3 | 0.0380s | 0.00 / 0.00 / 0.07 bytes | -0.01 bytes/update | -26 bytes (-0.0 KB) |
| Archival Group | 159 | 3 | 0.0401s | 0.00 / 0.04 / 0.08 bytes | -0.01 bytes/update | -27 bytes (-0.0 KB) |

## autov_creation_f71
Pooled runs: **6** (`stats_20261010_211820_333756.json`, `stats_20261010_213905_973839.json`, `stats_20261011_132846_662789.json`, `stats_20261011_134507_369977.json`, `stats_20261011_142150_052184.json`, `stats_20261011_143719_722811.json`)

### Creation Timing
| Collection type | Successful | Failed | Workflow mean (95% CI) | Workflow median / p95 / p99 | Commit mean (95% CI) | Commit median / p95 / p99 |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 2106 | 0 | 0.1204s (0.1181s to 0.1231s) | 0.1109s / 0.1689s / 0.3221s | 0.0512s (0.0493s to 0.0535s) | 0.0434s / 0.0795s / 0.1524s |
| Archival Group | 2101 | 0 | 0.0953s (0.0935s to 0.0971s) | 0.0878s / 0.1382s / 0.2041s | 0.0265s (0.0251s to 0.0280s) | 0.0217s / 0.0415s / 0.0843s |

### Collection Creation Storage
| Collection type | Collections | Avg workflow | Avg commit | Avg files | Avg directories | Avg OCFL size |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 3 | 0.1472s | 0.0460s | 38.00 | 35.00 | 20,695 bytes (20.21 KB) |
| Archival Group | 3 | 0.0831s | 0.0232s | 15.00 | 9.00 | 15,278 bytes (14.92 KB) |

### PATCH Storage
| Collection type | PATCHes | Sequences | Avg duration | Avg file / directory / size delta | Mean growth rate | Mean projected storage after 100 PATCHes |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 170 | 3 | 0.0305s | 4.00 / 3.00 / 26,682.64 bytes | 814.79 bytes/update | 4,396,010 bytes (4,293.0 KB) |
| Archival Group | 168 | 3 | 0.0310s | 4.00 / 3.00 / 71,408.97 bytes | 2,248.76 bytes/update | 12,067,962 bytes (11,785.1 KB) |

## Result Set Change

### Creation Timing Changes
| Collection type | Attempts | Workflow mean | Workflow change | Commit mean | Commit change |
| --- | --- | --- | --- | --- | --- |
| Atomic | 2111 successful, 0 failed -> 2106 successful, 0 failed | 0.1528s -> 0.1204s | -0.0323s (-21.2%) | 0.0899s -> 0.0512s | -0.0387s (-43.0%) |
| Archival Group | 2047 successful, 0 failed -> 2101 successful, 0 failed | 0.0946s -> 0.0953s | +0.0007s (+0.7%) | 0.0328s -> 0.0265s | -0.0063s (-19.2%) |

### Collection Creation Storage Changes
| Collection type | Metric | mutable_creation_f71 | autov_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg workflow | 0.2426s | 0.1472s | -0.0954s (-39.3%) |
| Atomic | Avg commit | 0.0959s | 0.0460s | -0.0498s (-52.0%) |
| Atomic | Avg files | 58.0000 | 38.0000 | -20.0000 (-34.5%) |
| Atomic | Avg directories | 60.0000 | 35.0000 | -25.0000 (-41.7%) |
| Atomic | Avg OCFL size | 21,416.0000 bytes | 20,695.3333 bytes | -720.6667 bytes (-3.4%) |
| Archival Group | Avg workflow | 0.1137s | 0.0831s | -0.0305s (-26.9%) |
| Archival Group | Avg commit | 0.0354s | 0.0232s | -0.0122s (-34.4%) |
| Archival Group | Avg files | 19.0000 | 15.0000 | -4.0000 (-21.1%) |
| Archival Group | Avg directories | 13.6667 | 9.0000 | -4.6667 (-34.1%) |
| Archival Group | Avg OCFL size | 13,022.0000 bytes | 15,278.0000 bytes | +2256.0000 bytes (+17.3%) |

### PATCH Storage Changes
| Collection type | Metric | mutable_creation_f71 | autov_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg PATCH duration | 0.0380s | 0.0305s | -0.0075s (-19.7%) |
| Atomic | Avg files | 0.0000 | 4.0000 | +4.0000 (n/a) |
| Atomic | Avg directories | 0.0000 | 3.0000 | +3.0000 (n/a) |
| Atomic | Avg OCFL size | 0.0750 bytes | 26,682.6412 bytes | +26682.5662 bytes (+35576754.9%) |
| Atomic | OCFL growth rate | -0.0053 bytes/update | 814.7898 bytes/update | +814.7951 bytes/update (n/a) |
| Archival Group | Avg PATCH duration | 0.0401s | 0.0310s | -0.0091s (-22.7%) |
| Archival Group | Avg files | 0.0000 | 4.0000 | +4.0000 (n/a) |
| Archival Group | Avg directories | 0.0377 | 3.0000 | +2.9623 (+7850.0%) |
| Archival Group | Avg OCFL size | 0.0755 bytes | 71,408.9702 bytes | +71408.8948 bytes (+94616785.6%) |
| Archival Group | OCFL growth rate | -0.0055 bytes/update | 2,248.7600 bytes/update | +2248.7655 bytes/update (n/a) |

# Summary

Atomic vs Archival Group: Across both versioning modes, Archival Groups remained faster and smaller to create. Under mutable head, AG creation timing averaged 0.0946s versus 0.1528s for atomic, a 38% workflow reduction, with commit time 64% lower; with autoversioning, AG was 21% faster (0.0953s vs 0.1204s) with a 48% lower commit mean. AG initial creation also wrote fewer OCFL objects: 67% fewer files and 77% fewer directories under mutable head, and 61%/74% fewer under autoversioning; byte growth was 39% lower under mutable head and 26% lower with autoversioning.

Autoversioning vs Mutable Head: Autoversioning substantially improved atomic creation performance, reducing mean workflow time by 21% (0.1528s to 0.1204s) and commit time by 43%, while AG workflow time was effectively unchanged (0.0946s to 0.0953s) although AG commits were 19% faster. The resource tradeoff remains almost entirely in updates: mutable-head PATCHes added effectively no OCFL content, while autoversioned PATCHes added about 26.7 KB per atomic PATCH and 71.4 KB per AG PATCH, with corresponding version-storage growth of about 815 and 2,249 bytes per update.

Interaction: AG + Autoversioning: AG plus autoversioning delivers the fastest commit timings (0.0265s) and near-identical overall creation workflow timing to mutable-head AG (0.0953s versus 0.0946s), but it has the highest update-storage cost. With autoversioning, AG PATCHes added 2.7 times as many bytes as atomic PATCHes and projected about 12.1 MB of cumulative OCFL growth over 100 updates, compared with 4.4 MB for atomic; the AG growth slope was also 176% higher. The main interaction is therefore that AG’s initial creation efficiency is preserved, but autoversioning makes AG’s ongoing update history materially more expensive.