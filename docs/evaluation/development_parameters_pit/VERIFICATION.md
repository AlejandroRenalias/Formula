# Verification

197 full-suite tests passed, no skips. Four pit-specific tests cover complete
out-lap/exit availability, altered/truncated future data, shrinkage/fallback,
and the external France timing-line split. Earlier real-cache future poisoning
and network-blocking tests pass. All 1,400 snapshots / 5,446 predictions retain
the same cohorts. All onset probabilities and green subset counts/masses are
exactly unchanged. All config fields except pit_in_lap_fraction are unchanged;
only the state pit pricing is updated. Source hashes and parameter timestamps
were checked for all races. External prior re-acquisition reruns offline from
cached 2019 packets. No interval tuning, wear fitting, new evaluation races,
SC/VSC prior changes, UI edits or push.
