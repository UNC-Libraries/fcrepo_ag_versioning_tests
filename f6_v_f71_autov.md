# Fedora Comparison: autov_creation_f6 vs autov_creation_f71

Negative duration changes mean the comparison configuration is faster. Operation counts are context only; all other values are per-operation averages.

## autov_creation_f6
Pooled runs: **3** (`stats_20261010_223946_554650.json`, `stats_20261010_232149_598367.json`, `stats_20261011_112649_486681.json`)

### Creation Timing
| Collection type | Successful | Failed | Workflow mean (95% CI) | Workflow median / p95 / p99 | Commit mean (95% CI) | Commit median / p95 / p99 |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 719 | 0 | 0.1142s (0.1123s to 0.1161s) | 0.1066s / 0.1631s / 0.2103s | 0.0473s (0.0461s to 0.0485s) | 0.0425s / 0.0762s / 0.0952s |
| Archival Group | 679 | 0 | 0.0873s (0.0860s to 0.0887s) | 0.0831s / 0.1222s / 0.1505s | 0.0229s (0.0223s to 0.0235s) | 0.0202s / 0.0386s / 0.0611s |

### Collection Creation Storage
| Collection type | Collections | Avg workflow | Avg commit | Avg files | Avg directories | Avg OCFL size |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 2 | 0.1543s | 0.0549s | 38.00 | 35.00 | 20,463 bytes (19.98 KB) |
| Archival Group | 2 | 0.0841s | 0.0249s | 15.00 | 9.00 | 15,174 bytes (14.82 KB) |

### PATCH Storage
| Collection type | PATCHes | Sequences | Avg duration | Avg file / directory / size delta | Mean growth rate | Mean projected storage after 100 PATCHes |
| --- | --- | --- | --- | --- | --- | --- |
| Atomic | 114 | 2 | 0.0333s | 4.00 / 3.00 / 26,491.61 bytes | 798.81 bytes/update | 4,311,230 bytes (4,210.2 KB) |
| Archival Group | 130 | 2 | 0.0353s | 4.00 / 3.00 / 81,019.83 bytes | 2,232.85 bytes/update | 11,983,529 bytes (11,702.7 KB) |

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
| Atomic | 719 successful, 0 failed -> 2106 successful, 0 failed | 0.1142s -> 0.1204s | +0.0062s (+5.4%) | 0.0473s -> 0.0512s | +0.0039s (+8.3%) |
| Archival Group | 679 successful, 0 failed -> 2101 successful, 0 failed | 0.0873s -> 0.0953s | +0.0080s (+9.1%) | 0.0229s -> 0.0265s | +0.0036s (+15.7%) |

### Collection Creation Storage Changes
| Collection type | Metric | autov_creation_f6 | autov_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg workflow | 0.1543s | 0.1472s | -0.0071s (-4.6%) |
| Atomic | Avg commit | 0.0549s | 0.0460s | -0.0089s (-16.1%) |
| Atomic | Avg files | 38.0000 | 38.0000 | +0.0000 (+0.0%) |
| Atomic | Avg directories | 35.0000 | 35.0000 | +0.0000 (+0.0%) |
| Atomic | Avg OCFL size | 20,463.0000 bytes | 20,695.3333 bytes | +232.3333 bytes (+1.1%) |
| Archival Group | Avg workflow | 0.0841s | 0.0831s | -0.0009s (-1.1%) |
| Archival Group | Avg commit | 0.0249s | 0.0232s | -0.0016s (-6.6%) |
| Archival Group | Avg files | 15.0000 | 15.0000 | +0.0000 (+0.0%) |
| Archival Group | Avg directories | 9.0000 | 9.0000 | +0.0000 (+0.0%) |
| Archival Group | Avg OCFL size | 15,174.0000 bytes | 15,278.0000 bytes | +104.0000 bytes (+0.7%) |

### PATCH Storage Changes
| Collection type | Metric | autov_creation_f6 | autov_creation_f71 | Change |
| --- | --- | --- | --- | --- |
| Atomic | Avg PATCH duration | 0.0333s | 0.0305s | -0.0028s (-8.4%) |
| Atomic | Avg files | 4.0000 | 4.0000 | +0.0000 (+0.0%) |
| Atomic | Avg directories | 3.0000 | 3.0000 | +0.0000 (+0.0%) |
| Atomic | Avg OCFL size | 26,491.6053 bytes | 26,682.6412 bytes | +191.0359 bytes (+0.7%) |
| Atomic | OCFL growth rate | 798.8141 bytes/update | 814.7898 bytes/update | +15.9758 bytes/update (+2.0%) |
| Archival Group | Avg PATCH duration | 0.0353s | 0.0310s | -0.0043s (-12.1%) |
| Archival Group | Avg files | 4.0000 | 4.0000 | +0.0000 (+0.0%) |
| Archival Group | Avg directories | 3.0000 | 3.0000 | +0.0000 (+0.0%) |
| Archival Group | Avg OCFL size | 81,019.8308 bytes | 71,408.9702 bytes | -9610.8605 bytes (-11.9%) |
| Archival Group | OCFL growth rate | 2,232.8543 bytes/update | 2,248.7600 bytes/update | +15.9057 bytes/update (+0.7%) |
