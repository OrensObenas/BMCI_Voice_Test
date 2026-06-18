# 🎙️ French TTS Benchmark Report

**Generated:** 2026-06-18 13:17:20  
**Platform:** Windows-11-10.0.26200-SP0  
**Python:** 3.13.14  
**Processor:** Intel64 Family 6 Model 170 Stepping 4, GenuineIntel  
**Lines evaluated:** 2 | **Runs per line:** 2

---

## 📊 Summary

| Rank | Model | Tier | WER (%) | CER (%) | MOS | RTF | Gen Time (s) | TTFA (s) |
|:----:|:------|:-----|--------:|--------:|----:|----:|-------------:|---------:|
| 🥇 | **hume** | local | 38.1 | 15.6 | 4.03 | 0.535 | 1.970 | 1.935 |
| 🥈 | **f5tts** | local | 90.8 | 46.8 | 3.79 | 37.435 | 127.910 | 127.910 |
| 🥉 | **mistral** | local | 16.5 | 8.0 | 3.78 | 0.363 | 1.574 | 1.440 |
| #4 | **edgetts** | local | 11.5 | 7.1 | 3.61 | 0.124 | 0.703 | 0.474 |
| #5 | **kokoro** | local | 31.5 | 13.8 | 3.56 | 0.700 | 3.027 | 3.027 |
| #6 | **gtts** | local | 11.5 | 7.1 | 3.53 | 0.090 | 0.459 | 0.459 |
| #7 | **elevenlabs** | local | 11.5 | 7.1 | 3.45 | 0.526 | 1.963 | 1.879 |
| #8 | **melo** | local | 26.5 | 11.1 | 3.17 | 2.008 | 7.976 | 7.976 |

> **RTF** (Real-Time Factor): < 1.0 = faster than real-time playback.

---

## 🥇 hume

- **Tier:** local
- **Avg WER:** 38.1%
- **Avg CER:** 15.6%
- **Avg MOS:** 4.03

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 30.0 |
| 🟡 Medium | 46.2 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.87 |
| 🟡 Medium | 4.18 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 1.9702 | 1.9702 | 2.0129 | 2.0129 | 1.9275 | 2.0129 | 0.0603 |
| TTFA (s) | 1.9354 | 1.9354 | 1.9771 | 1.9771 | 1.8936 | 1.9771 | 0.0590 |
| RTF | 0.5347 | 0.5347 | 0.6306 | 0.6306 | 0.4389 | 0.6306 | 0.1356 |

---

## 🥈 f5tts

- **Tier:** local
- **Avg WER:** 90.8%
- **Avg CER:** 46.8%
- **Avg MOS:** 3.79

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 120.0 |
| 🟡 Medium | 61.5 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.78 |
| 🟡 Medium | 3.81 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 127.9101 | 127.9101 | 136.3244 | 136.3244 | 119.4959 | 136.3244 | 11.8996 |
| TTFA (s) | 127.9101 | 127.9101 | 136.3244 | 136.3244 | 119.4959 | 136.3244 | 11.8996 |
| RTF | 37.4349 | 37.4349 | 39.1704 | 39.1704 | 35.6995 | 39.1704 | 2.4543 |

---

## 🥉 mistral

- **Tier:** local
- **Avg WER:** 16.5%
- **Avg CER:** 8.0%
- **Avg MOS:** 3.78

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 10.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.87 |
| 🟡 Medium | 3.69 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 1.5742 | 1.5742 | 1.8063 | 1.8063 | 1.3421 | 1.8063 | 0.3282 |
| TTFA (s) | 1.4405 | 1.4405 | 1.6310 | 1.6310 | 1.2501 | 1.6310 | 0.2693 |
| RTF | 0.3628 | 0.3628 | 0.4260 | 0.4260 | 0.2996 | 0.4260 | 0.0894 |

---

## #4 edgetts

- **Tier:** local
- **Avg WER:** 11.5%
- **Avg CER:** 7.1%
- **Avg MOS:** 3.61

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 0.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.71 |
| 🟡 Medium | 3.51 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 0.7025 | 0.7025 | 0.7053 | 0.7053 | 0.6998 | 0.7053 | 0.0038 |
| TTFA (s) | 0.4736 | 0.4736 | 0.5187 | 0.5187 | 0.4286 | 0.5187 | 0.0637 |
| RTF | 0.1240 | 0.1240 | 0.1318 | 0.1318 | 0.1162 | 0.1318 | 0.0110 |

---

## #5 kokoro

- **Tier:** local
- **Avg WER:** 31.5%
- **Avg CER:** 13.8%
- **Avg MOS:** 3.56

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 40.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.72 |
| 🟡 Medium | 3.40 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 3.0274 | 3.0274 | 3.1237 | 3.1237 | 2.9312 | 3.1237 | 0.1361 |
| TTFA (s) | 3.0274 | 3.0274 | 3.1236 | 3.1236 | 2.9312 | 3.1236 | 0.1361 |
| RTF | 0.6998 | 0.6998 | 0.7858 | 0.7858 | 0.6139 | 0.7858 | 0.1216 |

---

## #6 gtts

- **Tier:** local
- **Avg WER:** 11.5%
- **Avg CER:** 7.1%
- **Avg MOS:** 3.53

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 0.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.59 |
| 🟡 Medium | 3.48 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 0.4594 | 0.4594 | 0.4646 | 0.4646 | 0.4542 | 0.4646 | 0.0074 |
| TTFA (s) | 0.4594 | 0.4594 | 0.4646 | 0.4646 | 0.4542 | 0.4646 | 0.0074 |
| RTF | 0.0900 | 0.0900 | 0.1024 | 0.1024 | 0.0776 | 0.1024 | 0.0176 |

---

## #7 elevenlabs

- **Tier:** local
- **Avg WER:** 11.5%
- **Avg CER:** 7.1%
- **Avg MOS:** 3.45

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 0.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.30 |
| 🟡 Medium | 3.60 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 1.9630 | 1.9630 | 2.4826 | 2.4826 | 1.4435 | 2.4826 | 0.7347 |
| TTFA (s) | 1.8788 | 1.8788 | 2.4110 | 2.4110 | 1.3466 | 2.4110 | 0.7527 |
| RTF | 0.5262 | 0.5262 | 0.7255 | 0.7255 | 0.3270 | 0.7255 | 0.2818 |

---

## #8 melo

- **Tier:** local
- **Avg WER:** 26.5%
- **Avg CER:** 11.1%
- **Avg MOS:** 3.17

### WER by Difficulty

| Difficulty | WER (%) |
|:-----------|--------:|
| 🟢 Easy | 30.0 |
| 🟡 Medium | 23.1 |
| 🔴 Hard | — |

### MOS by Difficulty

| Difficulty | MOS |
|:-----------|----:|
| 🟢 Easy | 3.16 |
| 🟡 Medium | 3.19 |
| 🔴 Hard | — |

### ⏱️ Latency Percentiles

| Metric | Mean | Median | P95 | P99 | Min | Max | Std |
|:-------|-----:|-------:|----:|----:|----:|----:|----:|
| Gen Time (s) | 7.9765 | 7.9765 | 11.9533 | 11.9533 | 3.9996 | 11.9533 | 5.6241 |
| TTFA (s) | 7.9765 | 7.9765 | 11.9533 | 11.9533 | 3.9996 | 11.9533 | 5.6241 |
| RTF | 2.0084 | 2.0084 | 3.0890 | 3.0890 | 0.9278 | 3.0890 | 1.5282 |

---

*Report generated automatically by the French TTS Benchmark pipeline.*
