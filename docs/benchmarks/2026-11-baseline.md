# Token benchmark

| Agent | Tasks | Median input | Total input | Median calls | Images | Result chars |
|---|---|---|---|---|---|---|
| client-comments | 6 | 5.42M | 34.16M | 70 | 79 | 1.02M |
| figma-maintainer | 18 | 4.12M | 120.51M | 60 | 128 | 2.99M |
| qa-checker | 15 | 1.40M | 37.16M | 21 | 71 | 1.47M |

| Tool result kind | Calls | Characters | Avg |
|---|---|---|---|
| bash:other | 452 | 1.82M | 4k |
| get_figma_skill | 23 | 823k | 36k |
| bash:inline-python | 246 | 678k | 3k |
| read:md | 97 | 565k | 6k |
| use_figma | 188 | 548k | 3k |
| read:txt | 6 | 200k | 33k |
| script:figma_qa | 27 | 196k | 7k |
| get_metadata | 14 | 118k | 8k |
| get_screenshot | 174 | 89k | 510 |
| script:figma_comments | 17 | 60k | 4k |
| read:json | 4 | 57k | 14k |
| script:q | 12 | 53k | 4k |
| script:figma_snapshot | 44 | 46k | 1k |
| script:workdir | 15 | 37k | 2k |
| script:figma_common | 15 | 36k | 2k |
| mcp:other | 51 | 22k | 434 |
| read:other | 5 | 20k | 4k |
| edit | 106 | 17k | 163 |

39 task(s) · 278 image(s) in context · total input 191.84M

## Per task
| Date | Agent | Task | Input | Calls | Images |
|---|---|---|---|---|---|
| 2026-10-14 | figma-maintainer | Hook test job on test frame | 1.18M | 18 | 2 |
| 2026-10-27 | figma-maintainer | Apply LaundroLab Figma comments in copy | 11.32M | 111 | 17 |
| 2026-10-27 | client-comments | Analyse PIPP client comments | 5.29M | 63 | 11 |
| 2026-10-27 | figma-maintainer | Apply approved PIPP comment plan | 2.97M | 42 | 3 |
| 2026-10-29 | figma-maintainer | Apply Kayben client feedback | 11.75M | 104 | 16 |
| 2026-10-29 | qa-checker | QA Kayben feedback job | 3.17M | 43 | 9 |
| 2026-10-29 | client-comments | Analyse LaundroLab client comments | 12.21M | 104 | 21 |
| 2026-10-29 | figma-maintainer | Apply LaundroLab comments in Figma | 7.52M | 69 | 1 |
| 2026-10-29 | qa-checker | QA check LaundroLab comment job | 4.37M | 43 | 0 |
| 2026-11-04 | figma-maintainer | Apply Alpha Key client comments | 2.89M | 35 | 6 |
| 2026-11-04 | client-comments | Analyse WCDA client feedback | 7.83M | 80 | 25 |
| 2026-11-04 | figma-maintainer | Apply approved WCDA homepage plan | 20.50M | 127 | 12 |
| 2026-11-04 | qa-checker | QA the WCDA Homepage V2 job | 7.42M | 66 | 8 |
| 2026-11-04 | qa-checker | Re-run QA after message fixes | 1.22M | 19 | 0 |
| 2026-11-12 | client-comments | Analyse Sunward Steel client comments | 1.47M | 31 | 5 |
| 2026-11-12 | figma-maintainer | Apply approved Sunward Steel comments | 2.04M | 25 | 5 |
| 2026-11-12 | qa-checker | QA check Sunward Steel job | 1.15M | 19 | 4 |
| 2026-11-12 | figma-maintainer | QA fix round 1 Sunward Steel | 1.00M | 18 | 1 |
| 2026-11-12 | qa-checker | Re-QA Sunward Steel fix round | 1.53M | 32 | 8 |
| 2026-11-12 | figma-maintainer | Redesign Getting Started with boxes | 3.64M | 40 | 7 |
| 2026-11-12 | qa-checker | QA Sunward Steel revision round | 1.61M | 21 | 2 |
| 2026-11-12 | figma-maintainer | Switch remaining fonts to Libre Franklin | 1.83M | 33 | 4 |
| 2026-11-17 | client-comments | Analyse Homepage_V2 client comments | 5.54M | 78 | 16 |
| 2026-11-17 | figma-maintainer | Apply approved client comments | 8.59M | 78 | 10 |
| 2026-11-17 | qa-checker | QA the applied comment job | 10.96M | 82 | 9 |
| 2026-11-18 | client-comments | Analyse client comments | 1.81M | 19 | 1 |
| 2026-11-18 | figma-maintainer | Apply approved Figma comments | 549k | 8 | 0 |
| 2026-11-18 | qa-checker | Replay PIPP QA on Sonnet | 196k | 5 | 0 |
| 2026-11-18 | figma-maintainer | Apply Comfort Zone comment round | 3.56M | 51 | 5 |
| 2026-11-18 | figma-maintainer | Apply client Figma comments | 6.97M | 80 | 8 |
| 2026-11-18 | qa-checker | QA the applied comments | 1.01M | 19 | 0 |
| 2026-11-18 | qa-checker | QA Comfort Zone comment round | 388k | 12 | 4 |
| 2026-11-18 | qa-checker | QA re-check Comfort Zone round | 128k | 3 | 0 |
| 2026-11-18 | figma-maintainer | Kayben Figma client changes | 8.13M | 74 | 5 |
| 2026-11-18 | qa-checker | QA Kayben Figma round | 1.12M | 21 | 5 |
| 2026-11-18 | figma-maintainer | Kayben inner pages build | 21.48M | 140 | 18 |
| 2026-11-18 | qa-checker | QA Kayben inner pages | 1.50M | 32 | 14 |
| 2026-11-23 | figma-maintainer | Apply Alpha Key client comments | 4.60M | 72 | 8 |
| 2026-11-23 | qa-checker | QA Alpha Key comments job | 1.40M | 27 | 8 |
