# All disagreement event tags

FN = missed observable team stop; FP = unmatched first BOX alert. Tag definitions were fixed in [PROTOCOL.md](PROTOCOL.md). FP physical-stop context is descriptive, not a repaired primary match. None means no observed positive tag; unknown evidence remains explicit. Full timestamped evidence is in events.jsonl.
## development

| Event / driver | Observed tags | Unknown tags | Complete none | Reference cutoff | Context boundary / offset | Context basis |
| --- | --- | --- | --- | --- | --- | --- |
| bahrain_2021:FN:11:18 / PER | none | undercut_cover | False | 18 | 18 / 0 | missed_team_stop |
| bahrain_2021:FN:11:37 / PER | none | undercut_cover | False | 37 | 37 / 0 | missed_team_stop |
| bahrain_2021:FP:11:29 / PER | undercut_cover | none | False | 29 | 37 / 8 | accepted_wide_match |
| bahrain_2021:FN:16:11 / LEC | undercut_cover, compound_outside_candidates | none | False | 11 | 11 / 0 | missed_team_stop |
| bahrain_2021:FN:16:31 / LEC | undercut_cover | none | False | 31 | 31 / 0 | missed_team_stop |
| bahrain_2021:FN:18:11 / STR | undercut_cover, compound_outside_candidates | none | False | 11 | 11 / 0 | missed_team_stop |
| bahrain_2021:FN:18:27 / STR | none | undercut_cover | False | 27 | 27 / 0 | missed_team_stop |
| bahrain_2021:FN:22:14 / TSU | strategy_count | undercut_cover | False | 14 | 14 / 0 | missed_team_stop |
| bahrain_2021:FN:22:32 / TSU | compound_outside_candidates | undercut_cover | False | 32 | 32 / 0 | missed_team_stop |
| bahrain_2021:FN:3:12 / RIC | undercut_cover, compound_outside_candidates | none | False | 12 | 12 / 0 | missed_team_stop |
| bahrain_2021:FN:3:31 / RIC | undercut_cover | none | False | 31 | 31 / 0 | missed_team_stop |
| bahrain_2021:FN:33:16 / VER | compound_outside_candidates | undercut_cover | False | 16 | 16 / 0 | missed_team_stop |
| bahrain_2021:FN:33:38 / VER | none | undercut_cover | False | 38 | 38 / 0 | missed_team_stop |
| bahrain_2021:FP:33:36 / VER | none | undercut_cover | False | 36 | 38 / 2 | accepted_wide_match |
| bahrain_2021:FN:4:11 / NOR | undercut_cover, compound_outside_candidates | none | False | 11 | 11 / 0 | missed_team_stop |
| bahrain_2021:FN:4:32 / NOR | none | undercut_cover | False | 32 | 32 / 0 | missed_team_stop |
| bahrain_2021:FN:44:12 / HAM | strategy_count | undercut_cover | False | 12 | 12 / 0 | missed_team_stop |
| bahrain_2021:FN:44:27 / HAM | compound_outside_candidates | undercut_cover | False | 27 | 27 / 0 | missed_team_stop |
| bahrain_2021:FN:77:15 / BOT | strategy_count | undercut_cover | False | 15 | 15 / 0 | missed_team_stop |
| bahrain_2021:FN:77:29 / BOT | compound_outside_candidates, strategy_count | undercut_cover | False | 29 | 29 / 0 | missed_team_stop |
| spain_2022:FN:1:12 / VER | undercut_cover, compound_outside_candidates, strategy_count | none | False | 12 | 12 / 0 | missed_team_stop |
| spain_2022:FN:1:27 / VER | compound_outside_candidates, strategy_count | none | False | 27 | 27 / 0 | missed_team_stop |
| spain_2022:FN:11:36 / PER | compound_outside_candidates, strategy_count | undercut_cover | False | 36 | 36 / 0 | missed_team_stop |
| spain_2022:FN:11:52 / PER | compound_outside_candidates, strategy_count, late_race | undercut_cover | False | 52 | 52 / 0 | missed_team_stop |
| spain_2022:FP:11:32 / PER | compound_outside_candidates, strategy_count | undercut_cover | False | 32 | 36 / 4 | accepted_wide_match |
| spain_2022:FN:14:9 / ALO | undercut_cover, compound_outside_candidates, strategy_count | none | False | 9 | 9 / 0 | missed_team_stop |
| spain_2022:FN:14:30 / ALO | compound_outside_candidates, strategy_count | undercut_cover | False | 30 | 30 / 0 | missed_team_stop |
| spain_2022:FN:14:52 / ALO | compound_outside_candidates | undercut_cover | False | 52 | 52 / 0 | missed_team_stop |
| spain_2022:FP:14:27 / ALO | compound_outside_candidates, strategy_count | none | False | 27 | 30 / 3 | accepted_wide_match |
| spain_2022:FP:14:48 / ALO | compound_outside_candidates | undercut_cover | False | 48 | 52 / 4 | accepted_wide_match |
| spain_2022:FN:22:10 / TSU | undercut_cover, compound_outside_candidates, strategy_count | none | False | 10 | 10 / 0 | missed_team_stop |
| spain_2022:FN:22:31 / TSU | compound_outside_candidates, strategy_count | undercut_cover | False | 31 | 31 / 0 | missed_team_stop |
| spain_2022:FN:22:51 / TSU | compound_outside_candidates | undercut_cover | False | 51 | 51 / 0 | missed_team_stop |
| spain_2022:FP:22:28 / TSU | compound_outside_candidates, strategy_count | none | False | 28 | 31 / 3 | accepted_wide_match |
| spain_2022:FP:22:47 / TSU | compound_outside_candidates | undercut_cover | False | 47 | 51 / 4 | accepted_wide_match |
| spain_2022:FN:31:12 / OCO | compound_outside_candidates, strategy_count | none | False | 12 | 12 / 0 | missed_team_stop |
| spain_2022:FN:31:34 / OCO | compound_outside_candidates, strategy_count | undercut_cover | False | 34 | 34 / 0 | missed_team_stop |
| spain_2022:FN:31:51 / OCO | compound_outside_candidates | undercut_cover | False | 51 | 51 / 0 | missed_team_stop |
| spain_2022:FP:31:29 / OCO | compound_outside_candidates, strategy_count | undercut_cover | False | 29 | 34 / 5 | accepted_wide_match |
| spain_2022:FP:31:49 / OCO | compound_outside_candidates | undercut_cover | False | 49 | 51 / 2 | accepted_wide_match |
| spain_2022:FN:4:11 / NOR | undercut_cover, compound_outside_candidates, strategy_count | none | False | 11 | 11 / 0 | missed_team_stop |
| spain_2022:FN:4:32 / NOR | compound_outside_candidates, strategy_count | undercut_cover | False | 32 | 32 / 0 | missed_team_stop |
| spain_2022:FN:4:50 / NOR | compound_outside_candidates | undercut_cover | False | 50 | 50 / 0 | missed_team_stop |
| spain_2022:FP:4:29 / NOR | compound_outside_candidates, strategy_count | undercut_cover | False | 29 | 32 / 3 | accepted_wide_match |
| spain_2022:FP:4:47 / NOR | compound_outside_candidates | undercut_cover | False | 47 | 50 / 3 | accepted_wide_match |
| spain_2022:FN:44:21 / HAM | compound_outside_candidates, strategy_count | none | False | 21 | 21 / 0 | missed_team_stop |
| spain_2022:FN:44:47 / HAM | compound_outside_candidates | undercut_cover | False | 47 | 47 / 0 | missed_team_stop |
| spain_2022:FP:44:17 / HAM | compound_outside_candidates, strategy_count | none | False | 17 | 21 / 4 | accepted_wide_match |
| spain_2022:FP:44:36 / HAM | none | neutralisation, undercut_cover, compound_outside_candidates | False | 36 | unknown | unavailable |
| spain_2022:FN:55:9 / SAI | undercut_cover, compound_outside_candidates, strategy_count | none | False | 9 | 9 / 0 | missed_team_stop |
| spain_2022:FN:55:30 / SAI | compound_outside_candidates, strategy_count | undercut_cover | False | 30 | 30 / 0 | missed_team_stop |
| spain_2022:FN:55:44 / SAI | compound_outside_candidates | undercut_cover | False | 44 | 44 / 0 | missed_team_stop |
| spain_2022:FP:55:27 / SAI | compound_outside_candidates, strategy_count | none | False | 27 | 30 / 3 | accepted_wide_match |
| spain_2022:FN:63:12 / RUS | undercut_cover, compound_outside_candidates, strategy_count | none | False | 12 | 12 / 0 | missed_team_stop |
| spain_2022:FN:63:35 / RUS | compound_outside_candidates, strategy_count | undercut_cover | False | 35 | 35 / 0 | missed_team_stop |
| spain_2022:FP:63:28 / RUS | compound_outside_candidates, strategy_count | none | False | 28 | 35 / 7 | accepted_wide_match |
| spain_2022:FN:77:13 / BOT | compound_outside_candidates, strategy_count | none | False | 13 | 13 / 0 | missed_team_stop |
| spain_2022:FN:77:33 / BOT | compound_outside_candidates | undercut_cover | False | 33 | 33 / 0 | missed_team_stop |
| spain_2022:FP:77:29 / BOT | compound_outside_candidates | undercut_cover | False | 29 | 33 / 4 | accepted_wide_match |
| spain_2022:FP:77:49 / BOT | strategy_count | neutralisation, undercut_cover, compound_outside_candidates | False | 49 | unknown | unavailable |
| france_2022:FN:1:15 / VER | none | none | True | 15 | 15 / 0 | missed_team_stop |
| france_2022:FN:11:17 / PER | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:14:17 / ALO | neutralisation | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:18:17 / STR | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:3:17 / RIC | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:31:17 / OCO | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:4:17 / NOR | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:44:17 / HAM | neutralisation | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:55:17 / SAI | neutralisation, undercut_cover, strategy_count | none | False | 17 | 17 / 0 | missed_team_stop |
| france_2022:FN:55:41 / SAI | compound_outside_candidates, strategy_count, late_race | undercut_cover | False | 41 | 41 / 0 | missed_team_stop |
| france_2022:FP:55:33 / SAI | compound_outside_candidates | undercut_cover | False | 33 | 41 / 8 | accepted_wide_match |
| france_2022:FN:63:17 / RUS | neutralisation, undercut_cover | none | False | 17 | 17 / 0 | missed_team_stop |

## held_out

| Event / driver | Observed tags | Unknown tags | Complete none | Reference cutoff | Context boundary / offset | Context basis |
| --- | --- | --- | --- | --- | --- | --- |
| spain_2023:FN:1:51 / VER | compound_outside_candidates | none | False | 51 | 51 / 0 | missed_team_stop |
| spain_2023:FP:1:41 / VER | compound_outside_candidates | none | False | 41 | 51 / 10 | accepted_wide_match |
| spain_2023:FN:10:18 / GAS | compound_outside_candidates | none | False | 18 | 18 / 0 | missed_team_stop |
| spain_2023:FN:10:38 / GAS | undercut_cover | none | False | 38 | 38 / 0 | missed_team_stop |
| spain_2023:FN:11:49 / PER | compound_outside_candidates | none | False | 49 | 49 / 0 | missed_team_stop |
| spain_2023:FP:11:41 / PER | undercut_cover, compound_outside_candidates | none | False | 41 | 49 / 8 | accepted_wide_match |
| spain_2023:FN:14:18 / ALO | compound_outside_candidates | none | False | 18 | 18 / 0 | missed_team_stop |
| spain_2023:FN:18:13 / STR | compound_outside_candidates | none | False | 13 | 13 / 0 | missed_team_stop |
| spain_2023:FN:18:33 / STR | undercut_cover | none | False | 33 | 33 / 0 | missed_team_stop |
| spain_2023:FP:18:45 / STR | strategy_count | neutralisation, undercut_cover, compound_outside_candidates | False | 45 | unknown | unavailable |
| spain_2023:FN:24:8 / ZHO | undercut_cover, strategy_count | none | False | 8 | 8 / 0 | missed_team_stop |
| spain_2023:FN:24:35 / ZHO | compound_outside_candidates | none | False | 35 | 35 / 0 | missed_team_stop |
| spain_2023:FP:24:45 / ZHO | undercut_cover, compound_outside_candidates, strategy_count | none | False | 45 | 35 / -10 | accepted_wide_match |
| spain_2023:FN:31:12 / OCO | compound_outside_candidates | none | False | 12 | 12 / 0 | missed_team_stop |
| spain_2023:FN:31:34 / OCO | undercut_cover | none | False | 34 | 34 / 0 | missed_team_stop |
| spain_2023:FP:31:45 / OCO | strategy_count | neutralisation, undercut_cover, compound_outside_candidates | False | 45 | unknown | unavailable |
| spain_2023:FN:55:14 / SAI | compound_outside_candidates | none | False | 14 | 14 / 0 | missed_team_stop |
| spain_2023:FN:63:44 / RUS | compound_outside_candidates | undercut_cover | False | 44 | 44 / 0 | missed_team_stop |
| bahrain_2024:FN:1:16 / VER | none | none | True | 16 | 16 / 0 | missed_team_stop |
| bahrain_2024:FN:1:36 / VER | compound_outside_candidates | none | False | 36 | 36 / 0 | missed_team_stop |
| bahrain_2024:FP:1:9 / VER | none | none | True | 9 | 16 / 7 | nearest_physical_stop_within_10 |
| bahrain_2024:FP:1:14 / VER | none | none | True | 14 | 16 / 2 | accepted_wide_match |
| bahrain_2024:FP:1:32 / VER | compound_outside_candidates | none | False | 32 | 36 / 4 | accepted_wide_match |
| bahrain_2024:FN:11:35 / PER | compound_outside_candidates | none | False | 35 | 35 / 0 | missed_team_stop |
| bahrain_2024:FP:11:30 / PER | compound_outside_candidates | none | False | 30 | 35 / 5 | accepted_wide_match |
| bahrain_2024:FN:14:14 / ALO | strategy_count | none | False | 14 | 14 / 0 | missed_team_stop |
| bahrain_2024:FN:14:40 / ALO | compound_outside_candidates | none | False | 40 | 40 / 0 | missed_team_stop |
| bahrain_2024:FP:14:10 / ALO | undercut_cover | none | False | 10 | 14 / 4 | accepted_wide_match |
| bahrain_2024:FP:14:31 / ALO | compound_outside_candidates | none | False | 31 | 40 / 9 | accepted_wide_match |
| bahrain_2024:FN:16:33 / LEC | compound_outside_candidates | none | False | 33 | 33 / 0 | missed_team_stop |
| bahrain_2024:FP:16:30 / LEC | undercut_cover, compound_outside_candidates | none | False | 30 | 33 / 3 | accepted_wide_match |
| bahrain_2024:FN:18:8 / STR | undercut_cover, strategy_count | none | False | 8 | 8 / 0 | missed_team_stop |
| bahrain_2024:FN:18:26 / STR | compound_outside_candidates | none | False | 26 | 26 / 0 | missed_team_stop |
| bahrain_2024:FP:18:37 / STR | strategy_count | neutralisation, compound_outside_candidates | False | 37 | unknown | unavailable |
| bahrain_2024:FN:44:32 / HAM | undercut_cover, compound_outside_candidates | none | False | 32 | 32 / 0 | missed_team_stop |
| bahrain_2024:FP:44:30 / HAM | compound_outside_candidates | none | False | 30 | 32 / 2 | accepted_wide_match |
| bahrain_2024:FN:55:13 / SAI | strategy_count | none | False | 13 | 13 / 0 | missed_team_stop |
| bahrain_2024:FN:55:34 / SAI | compound_outside_candidates | none | False | 34 | 34 / 0 | missed_team_stop |
| bahrain_2024:FP:55:10 / SAI | undercut_cover | none | False | 10 | 13 / 3 | accepted_wide_match |
| bahrain_2024:FP:55:31 / SAI | compound_outside_candidates | none | False | 31 | 34 / 3 | accepted_wide_match |
| bahrain_2024:FN:81:33 / PIA | undercut_cover, compound_outside_candidates | none | False | 33 | 33 / 0 | missed_team_stop |
| bahrain_2024:FP:81:30 / PIA | undercut_cover, compound_outside_candidates | none | False | 30 | 33 / 3 | accepted_wide_match |

