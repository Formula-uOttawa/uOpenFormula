# Gear analysis rules, version 0.5

These rules identify recorded patterns to review. The recordings do not contain
independently verified fault labels. The timing thresholds remain configurable
starting points, rather than validated sensor-failure limits.

## Codes and settings

The valid codes are reverse (-1), neutral (0), and whole-number forward gears
1–6. The maximum forward gear is a user-provided assumption. Change it in
`gear_rules.json` when better information becomes available. Fractional readings
are retained exactly as recorded; they are never rounded to a valid gear.

| Setting | Default | Meaning |
|---|---:|---|
| `maximum_forward_gear` | 6 | Largest currently allowed forward code |
| `confirmation_samples` | 3 | Consecutive matching valid readings required to confirm a basic state |
| `large_jump_code_difference` | 3 | Minimum absolute code difference for a large-change review |
| `large_jump_endpoint_seconds` | 0.5 | Minimum continuous plateau span at each large-change endpoint |
| `persistent_bad_seconds` | 1.0 | Minimum continuous unusable-reading episode span for review |
| `no_shift_minimum_confirmed_coverage` | 0.9 | Required fraction of rows in confirmed states for a whole-run variation assessment |
| `maximum_gap_factor` | 3 | Recorded time gap limit, relative to the median timestamp interval |

All seconds-based conditions use last timestamp minus first timestamp. At 20 Hz,
three readings span 0.10 seconds; 11 readings span 0.50 seconds; 21 readings span
1.00 second. Threshold comparisons include a small floating-point tolerance.

## Persistent unusable readings

The program groups consecutive unusable readings into episodes. Types are:

- Missing: blank readings.
- Invalid: nonnumeric values, NaN, or infinity.
- Outside range: finite values below -1 or above the configured maximum.
- Fractional: other finite values that are not whole-number gear codes.

Values may change within an episode. A mixture of unusable types remains one
episode and produces one finding after its span reaches 1.0 second. A valid
reading or timestamp gap ends the episode. Shorter episodes remain observations.
The finding records its types, example values, first/last samples, threshold
activation sample, and whether the episode continues to the file's end.

Missing timing leaves counts and row-based observations available but prevents
seconds-based findings. Partially invalid timestamps are not silently replaced
with estimates. Explicitly authorized header-based estimates are labelled and
cannot verify real logger dropouts.

## Large changes and smaller notes

The analyzer first builds a sequence using three matching valid readings per
state. It compares consecutive confirmed states. Increasing the longer review
window never removes an intermediate confirmed state to create a new pair.

- `0 → 3`, `0 → 5`, and `5 → 2` can become Review findings when both endpoint
  plateaus continuously span at least 0.5 seconds.
- `0 → 2` and `4 → 2` are informational transition notes.
- Adjacent changes require no finding.
- One- and two-sample whole-number readings remain in the evidence. A complete
  ordered intermediate path can explain an apparent large endpoint difference.
- Basically confirmed endpoints that fail the longer duration requirement
  become brief observations, rather than large-change reviews.
- Reverse is a valid code. Its numeric value -1 is not used as a forward-gear
  distance. Reverse transitions remain observations.
- Missing, invalid, or out-of-range readings prevent comparisons across the
  interruption. Persistent fractional episodes also prevent a jump comparison
  across that episode; their data-quality finding remains available.
- Brief fractional readings can accompany an otherwise sustained large recorded
  change. They are preserved in the evidence and do not automatically hide it.

Endpoint duration confirmation uses uninterrupted timestamp segments. Gaps in
the transition or confirmation windows prevent a Review finding. The finding is
raised at the first destination sample that establishes the required duration.
Its evidence-window span is not a proven physical fault duration.

## No gear variation across a recording

At least 90% of recorded rows must belong to confirmed valid states. If only one
distinct code was confirmed, the program reports no confirmed gear variation at
the end of the file. Small unconfirmed spikes do not count as real variation.
Short legitimate confirmed states still count, even if too short for a large-jump
review. Timestamp gaps prevent a whole-recording continuity assessment.

The default run purpose is unknown. No variation is a Review observation asking
the user to interpret the recording's purpose, not a declaration of sensor
failure. `--shifts-expected no` makes the same pattern informational. A valid
gear held for a long section of an otherwise varying file is not automatically
classified as a frozen sensor.

If GPS Speed is logged, its recorded minimum, median, maximum, unit and numeric
sample count are included as context. GPS speed does not prove shifting was
required and does not change the finding automatically. No guessed vehicle-speed
cutoff is used.

## Reports and validation

Findings, informational transition notes, checks, raw-data observations and
limitations are separate report fields. The terminal, optional Matplotlib plot,
saved JSON and browser report use the same analysis result. Transition notes are
available under Statistics and check details. Multiple findings use a selector
to keep the detailed view compact.

The 34 additional CSVs contain 82,860 rows. This revision reproduces the separate
calibration audit's 82 large-change candidates, six no-variation observations,
and one persistent fractional episode. The latter is 1.9400 from 41.95 to 42.95
seconds in 15.csv. No missing or out-of-range readings occur in this batch; tests
cover those cases with synthetic examples. Counts of candidates do not establish
false-positive or false-negative rates.

The batch distinguishes very short fractional episodes from one longer episode,
but 0.2-, 0.5-, and 1.0-second thresholds select that same longer example.
Therefore it does not establish that the chosen 1.0-second starting point is
optimal. Common 0-to-5 changes are not automatically learned as healthy behaviour.
