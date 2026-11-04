# Sensor Monitor

The **Electrical → Monitor** node now opens a Dear PyGui view of the existing
sensor-monitor report. Analysis rules remain in `core/sensor_monitor`; the view
in `ui/views/elec_monitor.py` handles controls and presentation.

## Review a recording

1. Run `python main.py` from the repository directory in the project environment.
2. Either load a compatible project recording from the landing page, or choose
   **New Project** to open the navigation without importing data.
3. Open **Electrical → Monitor**. **Use project recording** reads the CSV selected
   by the application; **Open CSV** reviews a recording in this page only.
4. Select a sensor in the table and scroll to its detailed trace and findings.
   Missing channels are **Not logged**; logged channels without detection rules
   are **Not assessed**. **No findings** applies only to completed checks.
5. Use the finding selector and **Finding context** to inspect localized results.
   **Whole run** restores the full time range. Raw evidence and check details are
   available in the expandable sections.

The monitor accepts both supported brake-pressure header variants. Each table
row contains a whole-run trace; front and rear brakes share a vertical scale
when their units match. All original numeric points are retained. Invalid or
missing readings and recorded timestamp gaps split traces. Gear uses a step
trace without rounding fractional readings. Finding markers indicate activation.

**Reanalyze** rereads the selected source CSV. Project-file changes are picked up
when the Monitor page is opened again. A CSV opened within the monitor stays
selected until **Use project recording** is chosen; it does not replace the
data used by other analysis pages.

## Timing and gear settings

- Recorded, complete, strictly increasing timestamps use the recorded time axis.
- **Estimate time when all timestamps are blank** is off by default. Estimation
  requires consistent sample-rate and duration metadata. The report and plots
  explicitly label estimated timing and its uniform-sampling assumption.
- Partial, nonnumeric, duplicate, or reversed timestamps use sample indices;
  opting in does not silently replace those timestamps. Seconds-based checks
  remain unavailable as in the original analyzer.
- **Shifts expected** defaults to Unknown. Choose No for a run deliberately
  recorded in one gear; constant gear alone does not establish a sensor fault.

The original version 0.5 settings remain in
`core/sensor_monitor/gear_rules.json`. Reverse, neutral, and assumed forward
codes 1–6 are preserved. Persistent unusable data, sustained large recorded
changes, and whole-run variation checks retain the original conditions. See
[the imported gear rule specification](../core/sensor_monitor/GEAR_RULES.md).
The other eight channels have descriptive statistics and plots, without new
sensor-specific detection rules.

## Architecture

```text
DataManager.path (project CSV) OR Monitor's CSV picker
    -> core.sensor_monitor.csv_loader (original raw readings)
    -> service.analyze_run
        -> timing + gear analysis + shared run report
    -> ui.views.elec_monitor.MonitorView
        -> sensor table, traces, findings, check details
```

The adapter reads the source CSV rather than converting the shared numeric
dataframe back to strings. This preserves blank versus invalid readings, exact
raw gear evidence, original units, and metadata. It leaves DataManager and the
data used by the existing analysis views unchanged. Failed monitor imports
display an error and clear the previous report.

The application discovers `elec_monitor.py` through its existing view loader;
the filename matches the `elec_monitor` node and `MonitorView` provides the
existing constructor, `build`, and `refresh` interface. The only navigation
change refreshes this view when it is selected, so new project files are used.

The original analysis, optional Matplotlib gear plot, HTML renderer, JSON
exports, and CLI are imported as a package, with package-relative imports.
**Export HTML + JSON** saves the same report displayed by Dear PyGui in a chosen
directory; existing exports are not overwritten and no browser is opened.
The optional CLI remains available:

```sh
python -m core.sensor_monitor recording.csv --no-open
```

## Validation and packaging

Run the original analysis/report tests plus the new adapter and GUI checks:

```sh
MPLBACKEND=Agg python -m unittest discover -s tests -t . -q
```

The original 126 tests are under `tests/sensor_monitor`, with import paths
updated for the package. Integration checks cover raw input preservation,
timing opt-in, plot discontinuities, brake scales, finding navigation, optional
exports, project refresh, and construction of the existing Raw Data and Oil
Starvation pages alongside the new view. The GUI checks build widget trees
without opening a desktop window.

`hooks/hook-ui.views.py` includes the dynamically discovered views and the JSON
rules/HTML template in PyInstaller builds. The existing executable build uses
this hook and runs the tests before packaging. Windows builds must still be
verified on Windows; a local Mac build does not establish Windows compatibility.

The separate Mac file-picker fix is outside this feature branch. On a Mac using
this branch alone, the **New Project → Electrical → Monitor → Open CSV** path
uses Dear PyGui's picker and avoids the original global Tk file picker.
