# Saved-call disagreement analysis

Report-only analysis of decision-engine-v1: 54 missed team stops and 18 unmatched alerts in development; 25 and 17 respectively in held-out. No engine calls, new samples, rebuilt states, changed matching, tuning or UI changes. These tags describe observable context; they do not establish why a team stopped or which choice was better.

Compound outside the immediate candidate set occurs on 34/54 development misses and 17/25 held-out misses. All nine neutralisation-tagged misses are in France, and none had the relevant neutralisation visible at a saved pre-entry cutoff inside the ±1 window. There was nevertheless a valid pre-entry cutoff for every missed stop.

Definitions and deterministic case selection were committed before classification in [PROTOCOL.md](PROTOCOL.md), commits 9322fe3 and a8ea9b7. FN/FP identities reuse the accepted ±1 episode-start matching, not a new matching exercise. Lap numbers below use the accepted stop-boundary coordinate; entry times are session seconds.

The immediate BOX compound limitation remains HARD, or MEDIUM while on HARD. Strategy count compares actual remaining physical stops against nominal scheduled stops in the recommended policy; sampled stop-count distributions remain available in the audits. For FP, stop-specific tags use the predeclared ±10 contextual stop, not a primary match or proof of causation; five alerts have no such context.

## Counts, unknown evidence and overlaps

The [event register](EVENT_TAGS.md) lists all 114 events, tags, unknowns, contextual-stop provenance and reference cutoffs. Counts are nonexclusive. N/U in each tag column means observed positive / unknown. Unknown rival proximity is retained conservatively when the saved state omits a rival and no positive proximity-stop evidence exists. This is common in development; it is not a negative result. None means no positive tag; complete none additionally requires no unknown tags.

| Set/race | Direction | Events | neutralisation | undercut_cover | compound_outside_candidates | strategy_count | late_race | None | Complete none | 2+ tags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | FN | 54 | 9/0 | 19/28 | 34/0 | 24/0 | 2/0 | 6 | 1 | 31 |
| development | FP | 18 | 0/2 | 1/12 | 14/2 | 9/0 | 0/0 | 2 | 0 | 8 |
| held_out | FN | 25 | 0/0 | 7/1 | 17/0 | 4/0 | 0/0 | 1 | 1 | 4 |
| held_out | FP | 17 | 0/3 | 6/2 | 10/3 | 4/0 | 0/0 | 2 | 2 | 4 |


| Set/race | Direction | Events | neutralisation | undercut_cover | compound_outside_candidates | strategy_count | late_race | None | Complete none | 2+ tags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bahrain_2021 | FN | 18 | 0/0 | 6/12 | 8/0 | 4/0 | 0/0 | 5 | 0 | 5 |
| bahrain_2021 | FP | 2 | 0/0 | 1/1 | 0/0 | 0/0 | 0/0 | 1 | 0 | 0 |
| spain_2022 | FN | 25 | 0/0 | 6/15 | 25/0 | 18/0 | 1/0 | 0 | 0 | 18 |
| spain_2022 | FP | 15 | 0/2 | 0/10 | 13/2 | 9/0 | 0/0 | 1 | 0 | 8 |
| france_2022 | FN | 11 | 9/0 | 7/1 | 1/0 | 2/0 | 1/0 | 1 | 1 | 8 |
| france_2022 | FP | 1 | 0/0 | 0/1 | 1/0 | 0/0 | 0/0 | 0 | 0 | 0 |
| spain_2023 | FN | 13 | 0/0 | 4/1 | 9/0 | 1/0 | 0/0 | 0 | 0 | 1 |
| spain_2023 | FP | 5 | 0/2 | 2/2 | 3/2 | 3/0 | 0/0 | 0 | 0 | 2 |
| bahrain_2024 | FN | 12 | 0/0 | 3/0 | 8/0 | 3/0 | 0/0 | 1 | 1 | 3 |
| bahrain_2024 | FP | 12 | 0/1 | 4/0 | 7/1 | 1/0 | 0/0 | 2 | 2 | 2 |

### development FN: overlaps

| Pair | Events |
| --- | --- |
| neutralisation & undercut_cover | 7 |
| neutralisation & compound_outside_candidates | 0 |
| neutralisation & strategy_count | 1 |
| neutralisation & late_race | 0 |
| undercut_cover & compound_outside_candidates | 10 |
| undercut_cover & strategy_count | 7 |
| undercut_cover & late_race | 0 |
| compound_outside_candidates & strategy_count | 20 |
| compound_outside_candidates & late_race | 2 |
| strategy_count & late_race | 2 |


| Exact observed combination (unknowns may coexist) | Events |
| --- | --- |
| compound_outside_candidates | 10 |
| compound_outside_candidates+strategy_count | 12 |
| compound_outside_candidates+strategy_count+late_race | 2 |
| neutralisation | 2 |
| neutralisation+undercut_cover | 6 |
| neutralisation+undercut_cover+strategy_count | 1 |
| none | 6 |
| strategy_count | 3 |
| undercut_cover | 2 |
| undercut_cover+compound_outside_candidates | 4 |
| undercut_cover+compound_outside_candidates+strategy_count | 6 |

### development FP: overlaps

| Pair | Events |
| --- | --- |
| neutralisation & undercut_cover | 0 |
| neutralisation & compound_outside_candidates | 0 |
| neutralisation & strategy_count | 0 |
| neutralisation & late_race | 0 |
| undercut_cover & compound_outside_candidates | 0 |
| undercut_cover & strategy_count | 0 |
| undercut_cover & late_race | 0 |
| compound_outside_candidates & strategy_count | 8 |
| compound_outside_candidates & late_race | 0 |
| strategy_count & late_race | 0 |


| Exact observed combination (unknowns may coexist) | Events |
| --- | --- |
| compound_outside_candidates | 6 |
| compound_outside_candidates+strategy_count | 8 |
| none | 2 |
| strategy_count | 1 |
| undercut_cover | 1 |

### held_out FN: overlaps

| Pair | Events |
| --- | --- |
| neutralisation & undercut_cover | 0 |
| neutralisation & compound_outside_candidates | 0 |
| neutralisation & strategy_count | 0 |
| neutralisation & late_race | 0 |
| undercut_cover & compound_outside_candidates | 2 |
| undercut_cover & strategy_count | 2 |
| undercut_cover & late_race | 0 |
| compound_outside_candidates & strategy_count | 0 |
| compound_outside_candidates & late_race | 0 |
| strategy_count & late_race | 0 |


| Exact observed combination (unknowns may coexist) | Events |
| --- | --- |
| compound_outside_candidates | 15 |
| none | 1 |
| strategy_count | 2 |
| undercut_cover | 3 |
| undercut_cover+compound_outside_candidates | 2 |
| undercut_cover+strategy_count | 2 |

### held_out FP: overlaps

| Pair | Events |
| --- | --- |
| neutralisation & undercut_cover | 0 |
| neutralisation & compound_outside_candidates | 0 |
| neutralisation & strategy_count | 0 |
| neutralisation & late_race | 0 |
| undercut_cover & compound_outside_candidates | 4 |
| undercut_cover & strategy_count | 1 |
| undercut_cover & late_race | 0 |
| compound_outside_candidates & strategy_count | 1 |
| compound_outside_candidates & late_race | 0 |
| strategy_count & late_race | 0 |


| Exact observed combination (unknowns may coexist) | Events |
| --- | --- |
| compound_outside_candidates | 6 |
| none | 2 |
| strategy_count | 3 |
| undercut_cover | 2 |
| undercut_cover+compound_outside_candidates | 3 |
| undercut_cover+compound_outside_candidates+strategy_count | 1 |

## Missed-stop decision windows

The [complete window report](MISSED_STOP_WINDOWS.md) lists every saved cutoff in the ±1 window for all 79 misses, including signed BOX-minus-STAY mean margin, all three confidence masses, recommendation and visibility. Positive signed margin favours STAY in the engine. Confidence is sampled model mass beyond the saved 1-second tolerance, not a probability the engine was correct. The descriptive thresholds (0.8 confident; 0.5 close mass) were fixed before classification.

| Set | Misses | Any BOX in window | Any confident STAY | Any too close | Neutralisation visible / tagged |
| --- | --- | --- | --- | --- | --- |
| development | 54 | 16 | 16 | 12 | 0/9 |
| held_out | 25 | 11 | 10 | 1 | 0/0 |

Window categories overlap. A BOX inside a missed-stop window can belong to an episode that started outside the accepted matching window or was paired elsewhere. Thus 16 development and 11 held-out misses with window BOX calls are timing/episode disagreements, not necessarily confident refusals to stop. All saved window calls here precede pit entry; in-lap/straddling exclusions leave partial windows. Missing cutoffs are not invented.

## Most confident disagreements

Five cards in each direction for each set, ranked by the predeclared confidence mass and margin, not actual outcomes. FN cards use the strongest saved pre-entry STAY cutoff in the window; tag references remain the last pre-entry cutoff and may differ. FP cards use the first unmatched BOX alert. Full causal state, competitors, parameter counts/fallbacks/timestamps, sampled stop-count distributions and effective configuration are preserved in [case_cards.json](case_cards.json).

### development: FN

Eligible events for this ranking: 38.

#### 1. france_2022:FN:1:15 — VER

Causal cutoff lap 14 at 3950.341 s (tag reference lap 15). Position 2, MEDIUM age 14, 0 stops so far, used MEDIUM; GREEN. Saved base pace 97.669 s.

Observed weather: track_temp_c=55.0, air_temp_c=30.1, rainfall=False, humidity_pct=47.0, wind_speed_kmh=7.2; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| LEC | 1 | 1.573 | MEDIUM / 14 |

Call STAY_OUT; recommendation wait_to_22; signed BOX−STAY margin 8.234 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 14: HARD | 3936.131 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_22 | boundary 22: HARD | 3927.897 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 15: HARD. Actual stops in the primary ±1 window: boundary 15: HARD.

Physical stop context: boundary 15, entry 4138.183 s, exit 4173.449 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: none; unknown: none. Latest recorded parameter source 3949.000 s ≤ cutoff. No claim about the better choice.

#### 2. bahrain_2021:FN:44:27 — HAM

Causal cutoff lap 26 at 4889.163 s (tag reference lap 27). Position 1, HARD age 13, 1 stops so far, used HARD, MEDIUM; GREEN. Saved base pace 93.491 s.

Observed weather: track_temp_c=27.0, air_temp_c=20.5, rainfall=False, humidity_pct=55.8, wind_speed_kmh=2.16; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| VER | 2 | -2.884 | MEDIUM / 8 |

Call STAY_OUT; recommendation wait_to_34; signed BOX−STAY margin 6.775 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 26: MEDIUM | 2914.772 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_34 | boundary 34: MEDIUM | 2907.997 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 27: HARD. Actual stops in the primary ±1 window: boundary 27: HARD.

Physical stop context: boundary 27, entry 5081.240 s, exit 5105.375 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: compound_outside_candidates; unknown: undercut_cover. Latest recorded parameter source 4881.599 s ≤ cutoff. No claim about the better choice.

#### 3. bahrain_2021:FN:18:27 — STR

Causal cutoff lap 27 at 5026.379 s (tag reference lap 27). Position 8, MEDIUM age 15, 1 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 95.182 s.

Observed weather: track_temp_c=27.0, air_temp_c=20.5, rainfall=False, humidity_pct=56.0, wind_speed_kmh=3.24; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| PER | 7 | 2.077 | HARD / 25 |
| SAI | 9 | -0.860 | MEDIUM / 11 |

Call STAY_OUT; recommendation wait_to_35; signed BOX−STAY margin 5.973 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 27: HARD | 2873.944 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_35 | boundary 35: HARD | 2867.971 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 27: HARD. Actual stops in the primary ±1 window: boundary 27: HARD.

Physical stop context: boundary 27, entry 5124.368 s, exit 5150.113 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: none; unknown: undercut_cover. Latest recorded parameter source 5024.456 s ≤ cutoff. No claim about the better choice.

#### 4. france_2022:FN:4:17 — NOR

Causal cutoff lap 16 at 4172.982 s (tag reference lap 17). Position 7, MEDIUM age 16, 0 stops so far, used MEDIUM; GREEN. Saved base pace 98.633 s.

Observed weather: track_temp_c=55.3, air_temp_c=30.4, rainfall=False, humidity_pct=46.0, wind_speed_kmh=12.6; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call STAY_OUT; recommendation wait_to_28; signed BOX−STAY margin 6.951 s. STAY / BOX / close masses: 0.969 / 0.031 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_32 | boundary 16: HARD; boundary 32: MEDIUM | 3779.078 | 2.000 [2,2] | 0.000 |
| best_STAY | wait_to_28 | boundary 28: HARD | 3772.127 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 17: HARD. Actual stops in the primary ±1 window: boundary 17: HARD.

Physical stop context: boundary 17, entry 4376.152 s, exit 4413.653 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: neutralisation, undercut_cover; unknown: none. Latest recorded parameter source 4172.879 s ≤ cutoff. No claim about the better choice.

#### 5. france_2022:FN:14:17 — ALO

Causal cutoff lap 16 at 4168.972 s (tag reference lap 17). Position 6, MEDIUM age 16, 0 stops so far, used MEDIUM; GREEN. Saved base pace 98.560 s.

Observed weather: track_temp_c=55.3, air_temp_c=30.4, rainfall=False, humidity_pct=46.0, wind_speed_kmh=12.6; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| VER | 5 | 1.756 | MEDIUM / 16 |

Call STAY_OUT; recommendation wait_to_28; signed BOX−STAY margin 6.933 s. STAY / BOX / close masses: 0.969 / 0.031 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_32 | boundary 16: HARD; boundary 32: MEDIUM | 3776.316 | 2.000 [2,2] | 0.000 |
| best_STAY | wait_to_28 | boundary 28: HARD | 3769.382 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 17: HARD. Actual stops in the primary ±1 window: boundary 17: HARD.

Physical stop context: boundary 17, entry 4367.635 s, exit 4404.144 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: neutralisation; unknown: none. Latest recorded parameter source 4167.352 s ≤ cutoff. No claim about the better choice.

### development: FP

Eligible events for this ranking: 18.

#### 1. spain_2022:FP:22:47 — TSU

Causal cutoff lap 47 at 7983.940 s (tag reference lap 47). Position 10, SOFT age 18, 2 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 86.802 s.

Observed weather: track_temp_c=49.0, air_temp_c=36.8, rainfall=False, humidity_pct=7.0, wind_speed_kmh=9.72; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -1.085 s. STAY / BOX / close masses: 0.031 / 0.781 / 0.188.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 47: HARD | 1716.148 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_51 | boundary 51: HARD | 1717.232 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 51: SOFT. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 51, entry 8428.146 s, exit 8450.483 s, fitted SOFT; basis accepted_wide_match, offset 4 laps from event.

Observed tags: compound_outside_candidates; unknown: undercut_cover. Latest recorded parameter source 7980.180 s ≤ cutoff. No claim about the better choice.

#### 2. spain_2022:FP:77:49 — BOT

Causal cutoff lap 49 at 8123.457 s (tag reference lap 49). Position 4, MEDIUM age 15, 2 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 86.417 s.

Observed weather: track_temp_c=49.0, air_temp_c=36.5, rainfall=False, humidity_pct=8.0, wind_speed_kmh=4.680000000000001; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.810 s. STAY / BOX / close masses: 0.031 / 0.500 / 0.469.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 49: HARD | 1531.003 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_53 | boundary 53: HARD | 1531.813 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: no stops. Actual stops in the primary ±1 window: no stops.

No physical team-stop context within the predeclared range.

Observed tags: strategy_count; unknown: neutralisation, undercut_cover, compound_outside_candidates. Latest recorded parameter source 8117.164 s ≤ cutoff. No claim about the better choice.

#### 3. spain_2022:FP:22:28 — TSU

Causal cutoff lap 28 at 6276.228 s (tag reference lap 28). Position 8, MEDIUM age 17, 1 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 87.481 s.

Observed weather: track_temp_c=49.4, air_temp_c=37.0, rainfall=False, humidity_pct=7.0, wind_speed_kmh=12.6; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.754 s. STAY / BOX / close masses: 0.031 / 0.469 / 0.500.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 28: HARD | 3439.518 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_32 | boundary 32: HARD | 3440.272 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 31: SOFT; boundary 51: SOFT. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 31, entry 6635.980 s, exit 6658.761 s, fitted SOFT; basis accepted_wide_match, offset 3 laps from event.

Observed tags: compound_outside_candidates, strategy_count; unknown: none. Latest recorded parameter source 6274.534 s ≤ cutoff. No claim about the better choice.

#### 4. spain_2022:FP:31:49 — OCO

Causal cutoff lap 49 at 8144.395 s (tag reference lap 49). Position 6, SOFT age 17, 2 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 86.699 s.

Observed weather: track_temp_c=49.0, air_temp_c=36.5, rainfall=False, humidity_pct=8.0, wind_speed_kmh=4.680000000000001; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.750 s. STAY / BOX / close masses: 0.031 / 0.469 / 0.500.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 49: HARD | 1535.338 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_53 | boundary 53: HARD | 1536.088 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 51: SOFT. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 51, entry 8410.667 s, exit 8432.707 s, fitted SOFT; basis accepted_wide_match, offset 2 laps from event.

Observed tags: compound_outside_candidates; unknown: undercut_cover. Latest recorded parameter source 8138.150 s ≤ cutoff. No claim about the better choice.

#### 5. spain_2022:FP:4:29 — NOR

Causal cutoff lap 29 at 6361.097 s (tag reference lap 29). Position 7, MEDIUM age 17, 1 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 87.371 s.

Observed weather: track_temp_c=49.3, air_temp_c=37.2, rainfall=False, humidity_pct=7.0, wind_speed_kmh=13.32; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.546 s. STAY / BOX / close masses: 0.031 / 0.438 / 0.531.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 29: HARD | 3347.022 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_33 | boundary 33: HARD | 3347.569 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 32: SOFT; boundary 50: SOFT. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 32, entry 6719.173 s, exit 6742.458 s, fitted SOFT; basis accepted_wide_match, offset 3 laps from event.

Observed tags: compound_outside_candidates, strategy_count; unknown: undercut_cover. Latest recorded parameter source 6353.781 s ≤ cutoff. No claim about the better choice.

### held_out: FN

Eligible events for this ranking: 15.

#### 1. spain_2023:FN:24:8 — ZHO

Causal cutoff lap 7 at 4314.120 s (tag reference lap 8). Position 8, SOFT age 7, 0 stops so far, used SOFT; GREEN. Saved base pace 81.081 s.

Observed weather: track_temp_c=32.2, air_temp_c=22.3, rainfall=False, humidity_pct=64.0, wind_speed_kmh=7.2; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| PER | 9 | -0.997 | MEDIUM / 6 |
| ALO | 7 | 0.819 | SOFT / 10 |
| TSU | 10 | -2.729 | SOFT / 6 |
| RUS | 6 | 1.935 | SOFT / 7 |

Call STAY_OUT; recommendation wait_to_23; signed BOX−STAY margin 22.097 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_27 | boundary 7: HARD; boundary 27: MEDIUM | 4946.123 | 2.000 [2,2] | 0.000 |
| best_STAY | wait_to_23 | boundary 23: HARD | 4924.027 | 1.312 [1,2] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 8: HARD; boundary 35: HARD. Actual stops in the primary ±1 window: boundary 8: HARD.

Physical stop context: boundary 8, entry 4479.246 s, exit 4502.652 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: undercut_cover, strategy_count; unknown: none. Latest recorded parameter source 4313.437 s ≤ cutoff. No claim about the better choice.

#### 2. spain_2023:FN:10:38 — GAS

Causal cutoff lap 37 at 6768.566 s (tag reference lap 38). Position 8, MEDIUM age 18, 1 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 79.205 s.

Observed weather: track_temp_c=30.1, air_temp_c=22.1, rainfall=False, humidity_pct=65.0, wind_speed_kmh=4.32; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| LEC | 9 | -2.897 | SOFT / 20 |
| PIA | 7 | 1.277 | HARD / 20 |

Call STAY_OUT; recommendation wait_to_45; signed BOX−STAY margin 5.580 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 37: HARD | 2401.884 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_45 | boundary 45: HARD | 2396.304 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 38: HARD. Actual stops in the primary ±1 window: boundary 38: HARD.

Physical stop context: boundary 38, entry 6930.390 s, exit 6954.030 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: undercut_cover; unknown: none. Latest recorded parameter source 6767.440 s ≤ cutoff. No claim about the better choice.

#### 3. spain_2023:FN:31:12 — OCO

Causal cutoff lap 11 at 4637.767 s (tag reference lap 12). Position 6, SOFT age 14, 0 stops so far, used SOFT; GREEN. Saved base pace 80.232 s.

Observed weather: track_temp_c=31.8, air_temp_c=22.0, rainfall=False, humidity_pct=64.0, wind_speed_kmh=7.920000000000001; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| PER | 8 | -2.344 | MEDIUM / 10 |
| ALO | 7 | -1.575 | SOFT / 13 |
| RUS | 5 | 1.389 | SOFT / 11 |

Call STAY_OUT; recommendation two_stop_15_31; signed BOX−STAY margin 4.474 s. STAY / BOX / close masses: 1.000 / 0.000 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_31 | boundary 11: HARD; boundary 31: MEDIUM | 4575.672 | 2.000 [2,2] | 0.000 |
| best_STAY | two_stop_15_31 | boundary 15: HARD; boundary 31: MEDIUM | 4571.199 | 2.000 [2,2] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 12: MEDIUM; boundary 34: HARD. Actual stops in the primary ±1 window: boundary 12: MEDIUM.

Physical stop context: boundary 12, entry 4802.225 s, exit 4824.381 s, fitted MEDIUM; basis missed_team_stop, offset 0 laps from event.

Observed tags: compound_outside_candidates; unknown: none. Latest recorded parameter source 4636.400 s ≤ cutoff. No claim about the better choice.

#### 4. spain_2023:FN:31:34 — OCO

Causal cutoff lap 33 at 6434.433 s (tag reference lap 34). Position 6, MEDIUM age 20, 1 stops so far, used MEDIUM, SOFT; GREEN. Saved base pace 78.893 s.

Observed weather: track_temp_c=30.6, air_temp_c=22.1, rainfall=False, humidity_pct=65.0, wind_speed_kmh=7.920000000000001; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| PER | 7 | -0.663 | HARD / 5 |
| STR | 5 | 2.064 | SOFT / 22 |
| TSU | 8 | -2.833 | HARD / 22 |

Call STAY_OUT; recommendation wait_to_41; signed BOX−STAY margin 5.400 s. STAY / BOX / close masses: 0.969 / 0.031 / 0.000.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 33: HARD | 2715.940 | 1.094 [1,2] | 0.000 |
| best_STAY | wait_to_41 | boundary 41: HARD | 2710.540 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 34: HARD. Actual stops in the primary ±1 window: boundary 34: HARD.

Physical stop context: boundary 34, entry 6597.599 s, exit 6621.692 s, fitted HARD; basis missed_team_stop, offset 0 laps from event.

Observed tags: undercut_cover; unknown: none. Latest recorded parameter source 6432.477 s ≤ cutoff. No claim about the better choice.

#### 5. spain_2023:FN:18:13 — STR

Causal cutoff lap 13 at 4796.562 s (tag reference lap 13). Position 4, SOFT age 16, 0 stops so far, used SOFT; GREEN. Saved base pace 80.174 s.

Observed weather: track_temp_c=31.7, air_temp_c=22.1, rainfall=False, humidity_pct=65.0, wind_speed_kmh=9.72; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| RUS | 5 | -1.952 | SOFT / 12 |

Call STAY_OUT; recommendation two_stop_17_33; signed BOX−STAY margin 3.007 s. STAY / BOX / close masses: 0.969 / 0.000 / 0.031.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_33 | boundary 13: HARD; boundary 33: MEDIUM | 4410.447 | 2.000 [2,2] | 0.000 |
| best_STAY | two_stop_17_33 | boundary 17: HARD; boundary 33: MEDIUM | 4407.440 | 2.000 [2,2] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 13: SOFT; boundary 33: HARD. Actual stops in the primary ±1 window: boundary 13: SOFT.

Physical stop context: boundary 13, entry 4879.583 s, exit 4901.880 s, fitted SOFT; basis missed_team_stop, offset 0 laps from event.

Observed tags: compound_outside_candidates; unknown: none. Latest recorded parameter source 4791.788 s ≤ cutoff. No claim about the better choice.

### held_out: FP

Eligible events for this ranking: 17.

#### 1. bahrain_2024:FP:1:14 — VER

Causal cutoff lap 14 at 4957.889 s (tag reference lap 14). Position 1, SOFT age 17, 0 stops so far, used SOFT; GREEN. Saved base pace 95.520 s.

Observed weather: track_temp_c=23.3, air_temp_c=18.2, rainfall=False, humidity_pct=50.0, wind_speed_kmh=1.8; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |

Call BOX_NOW; recommendation box_two_stop_34; signed BOX−STAY margin -1.056 s. STAY / BOX / close masses: 0.219 / 0.562 / 0.219.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_34 | boundary 14: HARD; boundary 34: MEDIUM | 4240.518 | 2.000 [2,2] | 0.000 |
| best_STAY | wait_to_18 | boundary 18: HARD | 4241.574 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 16: HARD; boundary 36: SOFT. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 16, entry 5250.291 s, exit 5275.379 s, fitted HARD; basis accepted_wide_match, offset 2 laps from event.

Observed tags: none; unknown: none. Latest recorded parameter source 4934.142 s ≤ cutoff. No claim about the better choice.

#### 2. bahrain_2024:FP:55:10 — SAI

Causal cutoff lap 10 at 4580.259 s (tag reference lap 10). Position 5, SOFT age 13, 0 stops so far, used SOFT; GREEN. Saved base pace 96.558 s.

Observed weather: track_temp_c=23.5, air_temp_c=18.2, rainfall=False, humidity_pct=50.0, wind_speed_kmh=1.8; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| PER | 3 | 1.689 | SOFT / 13 |
| LEC | 4 | 0.373 | SOFT / 13 |
| RUS | 2 | 2.691 | SOFT / 13 |

Call BOX_NOW; recommendation box_two_stop_30; signed BOX−STAY margin -0.589 s. STAY / BOX / close masses: 0.031 / 0.500 / 0.469.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_30 | boundary 10: HARD; boundary 30: MEDIUM | 4689.699 | 2.000 [2,2] | 0.000 |
| best_STAY | two_stop_14_30 | boundary 14: HARD; boundary 30: MEDIUM | 4690.288 | 2.000 [2,2] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 13: HARD; boundary 34: HARD. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 13, entry 4970.807 s, exit 4995.387 s, fitted HARD; basis accepted_wide_match, offset 3 laps from event.

Observed tags: undercut_cover; unknown: none. Latest recorded parameter source 4580.115 s ≤ cutoff. No claim about the better choice.

#### 3. spain_2023:FP:18:45 — STR

Causal cutoff lap 45 at 7414.655 s (tag reference lap 45). Position 6, HARD age 11, 2 stops so far, used HARD, SOFT; GREEN. Saved base pace 77.965 s.

Observed weather: track_temp_c=29.8, air_temp_c=22.1, rainfall=False, humidity_pct=66.0, wind_speed_kmh=8.64; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| OCO | 7 | -2.934 | HARD / 9 |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.686 s. STAY / BOX / close masses: 0.031 / 0.375 / 0.594.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 45: MEDIUM | 1695.678 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_49 | boundary 49: MEDIUM | 1696.365 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: no stops. Actual stops in the primary ±1 window: no stops.

No physical team-stop context within the predeclared range.

Observed tags: strategy_count; unknown: neutralisation, undercut_cover, compound_outside_candidates. Latest recorded parameter source 7407.803 s ≤ cutoff. No claim about the better choice.

#### 4. bahrain_2024:FP:14:10 — ALO

Causal cutoff lap 10 at 4588.403 s (tag reference lap 10). Position 9, SOFT age 13, 0 stops so far, used SOFT; GREEN. Saved base pace 96.605 s.

Observed weather: track_temp_c=23.5, air_temp_c=18.2, rainfall=False, humidity_pct=50.0, wind_speed_kmh=1.8; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| TSU | 10 | -1.742 | SOFT / 9 |
| HAM | 8 | 0.938 | SOFT / 13 |

Call BOX_NOW; recommendation box_two_stop_30; signed BOX−STAY margin -0.527 s. STAY / BOX / close masses: 0.031 / 0.375 / 0.594.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_two_stop_30 | boundary 10: HARD; boundary 30: MEDIUM | 4691.920 | 2.000 [2,2] | 0.000 |
| best_STAY | two_stop_14_30 | boundary 14: HARD; boundary 30: MEDIUM | 4692.446 | 2.000 [2,2] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 14: HARD; boundary 40: HARD. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 14, entry 5082.030 s, exit 5106.892 s, fitted HARD; basis accepted_wide_match, offset 4 laps from event.

Observed tags: undercut_cover; unknown: none. Latest recorded parameter source 4587.518 s ≤ cutoff. No claim about the better choice.

#### 5. bahrain_2024:FP:16:30 — LEC

Causal cutoff lap 30 at 6543.236 s (tag reference lap 30). Position 5, HARD age 19, 1 stops so far, used HARD, SOFT; GREEN. Saved base pace 94.662 s.

Observed weather: track_temp_c=22.7, air_temp_c=18.0, rainfall=False, humidity_pct=49.0, wind_speed_kmh=2.52; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.

| Nearby saved car (≤3 s) | Position | Gap s | Compound / age |
| --- | --- | --- | --- |
| NOR | 6 | -2.279 | HARD / 16 |
| RUS | 4 | 1.174 | HARD / 19 |

Call BOX_NOW; recommendation box_now; signed BOX−STAY margin -0.504 s. STAY / BOX / close masses: 0.031 / 0.281 / 0.688.

| Option | Policy | Nominal stop boundaries / tyres | Mean to finish s | Sampled stops mean [min,max] | Invalid mass |
| --- | --- | --- | --- | --- | --- |
| best_BOX | box_now | boundary 30: MEDIUM | 2648.010 | 1.000 [1,1] | 0.000 |
| best_STAY | wait_to_34 | boundary 34: MEDIUM | 2648.514 | 1.000 [1,1] | 0.000 |

Team's remaining schedule after this card cutoff: boundary 33: HARD. Actual stops in the primary ±1 window: no stops.

Physical stop context: boundary 33, entry 6931.860 s, exit 6955.941 s, fitted HARD; basis accepted_wide_match, offset 3 laps from event.

Observed tags: undercut_cover, compound_outside_candidates; unknown: none. Latest recorded parameter source 6542.280 s ≤ cutoff. No claim about the better choice.

## Registered hypothesis and limits

The registered timing direction was rejected: the accepted wide-match early-race timing statistic did not show later engine BOX calls (development mean 0 laps on one match; held-out mean −1.556 laps on nine matches). In the registered stratum, the engine made no early BOX calls and caught none of the 11 observable stops (development 0/9, held-out 0/2; 331 qualifying cutoffs). That is consistent with the registered reduced-call/recall component, but the sample is too small to conclude. It does not rescue the rejected timing direction or prove a counterfactual outcome.

Undercut/cover is only an observable proximity-and-stop tag. Neutralisation visibility refers to the recorded SC/VSC trigger, not team radio or intent. FP contextual stops can be several laps away or before an alert; their tags are descriptive. The frozen prediction and accepted agreement scores remain unchanged. No disagreement outcome-quality analysis was performed.

## Audit and validation

- 114 unique events: 79 FN and 35 FP; accepted per-race event counts unchanged.
- Exact tag combinations partition each pool; pairwise overlaps respect tag totals.
- All saved window margins and pre-entry flags verified; all 20 case cards have valid source events.
- Case-card parameter timestamps are at or before cutoff; frozen uncertainty remains 3.0 / 1.0.
- All accepted source, call, matching, cache and profile hashes remain unchanged.

Classification ran once with network blocked and engine projection, sampling, simulation and snapshot construction patched to fail if invoked. [manifest.json](manifest.json) seals accepted inputs; [events.jsonl](events.jsonl) preserves all 114 classifications; [metrics.json](metrics.json) preserves per-race and pooled counts; [PROTOCOL.md](PROTOCOL.md) records definitions before computation.
