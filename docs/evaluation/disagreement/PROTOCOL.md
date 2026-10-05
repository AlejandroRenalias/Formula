# Disagreement classification protocol

This extension is written before computing disagreement classifications or
selecting case cards. The accepted decision-engine-v1 calls, primary +/-1 event
matches, exclusions and score are immutable. Reuse saved artifacts only; no
project/simulator/sampler/snapshot-builder calls, parameter changes, engine runs,
new races, tuning or UI changes. Block networking and verify accepted input
hashes. This extends [AGREEMENT_PLAN.md](../AGREEMENT_PLAN.md).

## Events, reference cutoffs and outcome context

Use only the accepted tolerance=1 matching audit. A false negative (FN) is an
unmatched **observable** team stop, not an unobservable stop. A false positive
(FP) is the unmatched first BOX alert of an episode, not each repeated BOX row.
Do not re-match or move episode onsets. Report development and held-out sets
separately, per race and event-count pooled, with denominators and missing data.

For FN tags the reference is the last saved valid subject cutoff strictly before
physical pit entry, regardless of whether it lies inside +/-1; report its age
and lap distance. For FP tags the reference is the saved alert cutoff, the last
cutoff before its proposed immediate stop. Never reconstruct a missing cutoff.

FN team-stop context is the missed physical stop itself. For FP stop-specific
tags (neutralisation at actual entry and fitted compound), use the same driver's
accepted +/-10 diagnostic match if it exists. Otherwise use the nearest physical
team stop within 10 boundary laps, ties to the earlier entry. This is explicitly
**context**, not a repaired primary match or a causal explanation of the alert.
If no such stop exists, these tags are unknown, not evidence of absence. Keep
context provenance, before/after distance and entry timestamps in every event.
Other FP tags use the alert reference, not the context stop's earlier state.

## Observable tags (non-exclusive)

1. **Neutralisation.** True when SC/VSC is active at the contextual team's exact
   pit-entry session time, or when a new SC/VSC period begins during its in-lap
   before entry. In-lap begins at the latest subject crossing strictly before
   entry and ends at entry. Track codes 4=SC and 6/7=VSC; 6->7 is not a new onset.
   A new period starts on transition from outside SC/VSC to SC/VSC. Report the
   two triggers separately, event start/end, and missing crossing/status data.
   FP without physical stop context has unknown primary neutralisation tag;
   separately record SC/VSC at the actual alert cutoff without conflating it
   with a team-entry condition.
2. **Undercut/cover proxy.** At the reference cutoff a saved rival gap has
   absolute value <=3.0 s (ahead or behind, including the approved live timing
   proxy), and that rival physically stops within +/-2 boundary laps of the
   missed team stop (FN) or proposed alert stop (FP). Use all available saved
   competitors, including rivals outside the subject top ten. Record rival,
   signed gap, direction and stop offset. Do not infer motive or substitute
   future gaps. Omitted rival coverage is recorded; no proximity data means
   unknown. A positive result is an observable proximity/timing association.
3. **Compound outside candidate set.** The contextual team's final fitted
   compound is absent from the reference's saved immediate BOX candidate
   compounds. Inspect saved policies with a dry stop at the reference boundary
   and positive stop budget, not heuristic advice or a new engine call. Final
   fitted compound comes from the first pit exit after entry and the normalized
   corrected `actual_tyres` label for its out-lap. Record missing exits/labels
   or no immediate BOX option as unknown. For FP this may describe an earlier
   or later actual stop; report the context distance prominently.
4. **Strategy count.** Count all physical subject stops strictly after the
   reference cutoff time through its actual race finish, including the event
   for FN. Compare with the recommended policy's nominal future scheduled dry
   stop count (`len(dry_stops)`). Different counts tag true. Also show weighted
   mean and min/max stop counts from the saved recommended scenario traces,
   because autonomous sampled SC stops can change nominal counts. Do not replace
   the nominal primary rule with a tuned expected-count threshold. Missing
   reference/recommended policy means unknown.
5. **Late race.** The recommended policy at the reference is `stay_to_finish`.
   This is the user's policy-based tag, not an additional lap-number threshold.
   It need not occur only at laps 30+. A genuine FP references a BOX call, so
   this tag cannot be true there; do not manufacture a different reference.
6. **None of the above.** No tag 1-5 is true. Report how many such events have
   unknown tags, separating complete negative evidence from missing context.

Tags may overlap. Report marginal counts, unknown counts, all pairwise overlaps
and exact observed tag combinations for each direction/set, plus per-race
counts. Do not force an exclusive cause or sum overlapping counts as totals.

## Visibility and +/-1 window confidence

For each physical team-stop context list all accepted subject cutoffs in its
+/-1 boundary-lap window, and whether each is before or after entry. Report:
(a) whether any pre-entry valid decision opportunity existed in that window;
(b) whether its qualifying neutralisation trigger was visible at any such
cutoff (SC/VSC active there during the same relevant episode); and
(c) whether a post-entry cutoff existed. This measures boundary-time visibility
of the trigger/action opportunity, not access to the team's intentions. A
neutralisation beginning and ending between cutoffs is not labelled visible.
For FN report all window calls, signed BOX-minus-STAY expected-time margin,
confidence masses and source times. Do not silently substitute a last earlier
cutoff outside the window or treat an unavailable cutoff as STAY.

Use saved confidence tolerance (1 s) and fixed reporting labels: **confident
STAY** = STAY_OUT and `stay_clearly_better` >=0.80; **confident BOX** = BOX_NOW
and `box_clearly_better` >=0.80; otherwise **too close** if `too_close_to_call`
>=0.50; otherwise **mixed/uncertain**. Missing confidence is unavailable.
Record continuous masses so these labels cannot hide the actual confidence.
Report FN windows containing a confident STAY, too-close calls, or any BOX;
these counts overlap. A BOX inside the window can coexist with an unmatched
first episode onset, so classify that as timing/episode disagreement rather
than falsely calling it confident STAY. Flag after-entry calls separately.

## Case-card selection, before looking at results

Select five per direction per set (up to 20 cards). For FN, candidate card
cutoffs are STAY calls inside +/-1 and strictly before entry. For each event
choose highest saved `stay_clearly_better`, then largest positive BOX-minus-STAY
mean margin, then latest cutoff. Rank events by those same keys, then race name,
driver number and stop boundary. If fewer than five are eligible, show only
available cards and disclose the shortage; no distant substitute or timing-only
BOX case is relabelled a confident opposing call. FP cards use the saved first
BOX onset, ranked by `box_clearly_better`, then largest STAY-minus-BOX margin,
then race/driver/lap. No threshold filtering is used to fill the top five.

Each card contains the selected exact causal cutoff (lap/session time, position,
gaps, compound/age, previous compounds/stops, track status, observed weather,
wear/pit audits and timestamp boundary), recommended and best BOX/STAY policies,
nominal stops, mean remaining time, signed margin, confidence and sampled stop
count summary, plus the actual physical team schedule/context and fitted tyre.
No claim that either action was right or would have won a counterfactual race.

## Registered hypothesis and stopping point

Repeat explicitly: the registered **later early-call timing direction was
rejected**. The registered causal stratum had no early BOX calls and caught
none of its 11 observable team stops (nine development, two held-out). This is
consistent with the low-call/low-recall part, but too small to conclude; it does
not restore the rejected timing direction or prove a wear mechanism. Do not
reinterpret missing alerts as infinitely late alerts.

Save every event, window and context audit, tag summaries/overlaps, selected
cards and a Markdown report with provenance hashes. Stop for review; no engine
changes, threshold optimisation or choice-quality/counterfactual analysis.
