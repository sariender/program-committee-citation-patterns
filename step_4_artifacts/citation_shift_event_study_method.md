# RQ2 citation-source-shift event-study method

## Research question

During a PC-service year, do a researcher's citations shift toward papers from
that same conference?

This is a citation-share question, not a raw citation-count question. The goal is
to ask whether the composition of a researcher's citations changes around PC
service.

## Event unit

An event unit is one researcher-conference pair:

```text
i = (researcher r, conference c)
```

Let `y0` be the first observed year in which researcher `r` serves on the PC for
conference `c`. Event time is defined as:

```text
t = y - y0
```

So `t = 0` is the PC-service year.

## Sample restrictions

Keep an event unit only if all of the following are true:

1. The researcher has a first same-conference PC-service year `y0`.
2. The full five-year event window is observed:

```text
t in {-2, -1, 0, +1, +2}
```

3. The researcher does not serve again on the same conference PC at `t = +1` or
   `t = +2`.
4. The researcher has exactly one observed same-conference PC-service year in
   the PC-service data.

The third restriction keeps the post-PC years interpretable as after-service
years rather than additional PC-service years.
The fourth restriction removes repeat same-conference PC-service cases, where
the event year is harder to interpret as a clean first exposure.

## Citation-source share

For each event unit `i = (r, c)` and event time `t`, define:

```text
source_share_i,t =
    citations from papers in conference c and year y0+t to researcher r
    /
    citations from all studied conference papers in year y0+t to researcher r
```

The numerator is the researcher's citation count from the same conference-year
as the event conference.

The denominator is the researcher's total citation count from all studied
conference sources in that same calendar year.

If the denominator is zero, `source_share_i,t` is undefined for that event time.

## Baseline

Use `t = -2` as the only reference year:

```text
baseline_i = source_share_i,-2
```

Do not use the average of `t = -2` and `t = -1` as the baseline. This keeps the
method parallel to the main descriptive event-study analysis.

## Outcome

For each event unit and event time:

```text
delta_share_i,t = source_share_i,t - source_share_i,-2
```

The plotted value is expressed in percentage points:

```text
delta_share_pp_i,t = 100 * delta_share_i,t
```

Therefore, a value of `+5` means a 5 percentage-point increase in the share of
citations coming from the PC conference, relative to `t = -2`.

By construction:

```text
delta_share_i,-2 = 0
```

## Average event-study curve

For each event time `t`, average the percentage-point change across event units
with defined values:

```text
mean_delta_share_pp_t = average_i(delta_share_pp_i,t)
```

Interpretation:

- `t = -1` checks whether the share was already moving before PC service.
- `t = 0` is the PC-service-year source-share shift.
- `t = +1` and `t = +2` show whether the shift persists or fades.

## Bootstrap error bars

Use event-unit bootstrap intervals:

```text
repeat B = 2,000 times:
    resample event units with replacement
    keep each selected event unit's full five-year trajectory
    recompute mean_delta_share_pp_t for each event time t
```

The 95% interval at each event time is the 2.5th and 97.5th percentiles of the
bootstrap estimates.

The bootstrap unit is the researcher-conference event unit, not individual
event-time rows. This matters because the five event-time observations for the
same event unit are dependent.

## Regenerated figures

The figures generated with this method are stored under:

```text
v7/step_4_artifacts/figures_citation_shift_event_study/
```

They use:

- `t = -2` as the source-share baseline,
- percentage-point changes on the y-axis,
- single-service event units with a complete five-year window and no
  same-conference PC service at `t = +1` or `t = +2`,
- bootstrap error bars over event units,
- no two-year pre-PC average baseline robustness check.
