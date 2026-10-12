# Fedora Comparison: mutable_creation_f6 vs mutable_creation_f71

Negative duration changes mean the comparison configuration is faster. Operation counts are context only; all other values are per-operation averages.

## mutable_creation_f6
Pooled runs: **4** (`stats_20261010_233118_335908.json`, `stats_20261010_234613_570248.json`, `stats_20261011_123047_197189.json`, `stats_20261011_125233_772959.json`)

### Creation Timing
| Collection type | Successful | Failed | Workflow mean (95% CI) | Workflow median / p95 / p99 | Commit mean (95% CI) | Commit median / p95 / p99 |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 1377 | 0 | 0.2023s (0.1947s to 0.2114s) | 0.1716s / 0.3245s / 0.7975s | 0.1304s (0.1243s to 0.1376s) | 0.1022s / 0.2323s / 0.6476s |
| Archival Group | 1370 | 0 | 0.1107s (0.1076s to 0.1139s) | 0.0986s / 0.1640s / 0.3983s | 0.0413s (0.0396s to 0.0430s) | 0.0332s / 0.0748s / 0.1969s |

### Collection Creation Storage
| Collection type | Collections | Avg workflow | Avg commit | Avg files | Avg directories | Avg OCFL size |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 2 | 0.1700s | 0.0841s | 58.00 | 60.00 | 21,219 bytes (20.72 KB) |
| Archival Group | 2 | 0.0897s | 0.0314s | 19.00 | 14.00 | 12,925 bytes (12.62 KB) |

### PATCH Storage
| Collection type | PATCHes | Sequences | Avg duration | Avg file / directory / size delta | Mean growth rate | Mean projected storage after 100 PATCHes |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 127 | 2 | 0.0378s | 0.00 / 0.00 / 0.06 bytes | -0.00 bytes/update | -20 bytes (-0.0 KB) |
| Archival Group | 114 | 2 | 0.0381s | 0.00 / 0.04 / 0.07 bytes | -0.00 bytes/update | -73 bytes (-0.1 KB) |

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

## Result Set Change

### Creation Timing Changes
| Collection type | Attempts | Workflow mean | Workflow change | Commit mean | Commit change |
| --- | --- | --- | --- | --- | --- |
| Atomic | 1377 successful, 0 failed -> 2111 successful, 0 failed | 0.2023s -> 0.1528s | -0.0496s (-24.5%) | 0.1304s -> 0.0899s | -0.0405s (-31.1%) |
| Archival Group | 1370 successful, 0 failed -> 2047 successful, 0 failed | 0.1107s -> 0.0946s | -0.0161s (-14.6%) | 0.0413s -> 0.0328s | -0.0085s (-20.7%) |

### Collection Creation Storage Changes
| Collection type | Metric | mutable_creation_f6 | mutable_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg workflow | 0.1700s | 0.2426s | +0.0725s (+42.6%) |
| Atomic | Avg commit | 0.0841s | 0.0959s | +0.0118s (+14.0%) |
| Atomic | Avg files | 58.0000 | 58.0000 | +0.0000 (+0.0%) |
| Atomic | Avg directories | 60.0000 | 60.0000 | +0.0000 (+0.0%) |
| Atomic | Avg OCFL size | 21,219.0000 bytes | 21,416.0000 bytes | +197.0000 bytes (+0.9%) |
| Archival Group | Avg workflow | 0.0897s | 0.1137s | +0.0240s (+26.8%) |
| Archival Group | Avg commit | 0.0314s | 0.0354s | +0.0040s (+12.9%) |
| Archival Group | Avg files | 19.0000 | 19.0000 | +0.0000 (+0.0%) |
| Archival Group | Avg directories | 14.0000 | 13.6667 | -0.3333 (-2.4%) |
| Archival Group | Avg OCFL size | 12,925.0000 bytes | 13,022.0000 bytes | +97.0000 bytes (+0.8%) |

### PATCH Storage Changes
| Collection type | Metric | mutable_creation_f6 | mutable_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg PATCH duration | 0.0378s | 0.0380s | +0.0002s (+0.5%) |
| Atomic | Avg files | 0.0000 | 0.0000 | +0.0000 (n/a) |
| Atomic | Avg directories | 0.0000 | 0.0000 | +0.0000 (n/a) |
| Atomic | Avg OCFL size | 0.0630 bytes | 0.0750 bytes | +0.0120 bytes (+19.1%) |
| Atomic | OCFL growth rate | -0.0041 bytes/update | -0.0053 bytes/update | -0.0012 bytes/update (n/a) |
| Archival Group | Avg PATCH duration | 0.0381s | 0.0401s | +0.0020s (+5.2%) |
| Archival Group | Avg files | 0.0000 | 0.0000 | +0.0000 (n/a) |
| Archival Group | Avg directories | 0.0351 | 0.0377 | +0.0026 (+7.5%) |
| Archival Group | Avg OCFL size | 0.0702 bytes | 0.0755 bytes | +0.0053 bytes (+7.5%) |
| Archival Group | OCFL growth rate | -0.0047 bytes/update | -0.0055 bytes/update | -0.0008 bytes/update (n/a) |
