# Sensor Monitor

The **Electrical → Monitor** node now opens a Dear PyGui view of the existing
sensor-monitor report. Analysis rules remain in `core/sensor_monitor`; the view
in `ui/views/elec_monitor.py` handles controls and presentation.

## Monitor layout

The Monitor fits the existing application's 800 × 600 starting window. It does
not change the viewport settings, navigation layout, Raw Data, or oil plots.
Its content is organized into three tabs:

- **Overview:** a scrollable two-column list with whole-run mini plots and
  assessments. Select a sensor's name to open its details.
- **Sensor detail:** a sensor selector, full-width chart, findings, and
  expandable evidence/statistics. Scroll inside this tab to read longer results.
- **Options:** recording information, reanalysis, timing/gear context settings,
  optional report export, and report limitations.

Only Monitor widgets adapt to the size of their own panel. Text wraps and
mini plots fill their cells; resizing preserves the current report and plot
objects. The chart's time-axis label distinguishes recorded, estimated, and
sample-index timing. Other sensors remain accessible without returning to the
overview through the selector at the top of Sensor detail.

## Review a recording

1. Run `python main.py` from the repository directory in the project environment.
2. Choose **Load Project** on the landing page and select a CSV recording.
3. Open **Electrical → Monitor**. It automatically follows the selected project
   recording; no second file selection is required. To change recordings, use
   **File → Load Project**. All views are rebuilt with the newly loaded data.
4. Select a sensor in **Overview** to open **Sensor detail**, or use the sensor
   selector at the top of that tab to change sensors.
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
data used by other analysis pages. Loading a new project resets all views,
including Monitor, to follow the new recording.

For a standalone review, choose **New Project → Electrical → Monitor → Open CSV**.
The global loader retains its existing CSV validation; this monitor-only route
can also review recordings that the global numeric conversion rejects. When
Monitor is using a loaded project recording, it hides the redundant Open CSV
and Use project recording controls.

## Timing and gear settings

- Recorded, complete, strictly increasing timestamps use the recorded time axis.
- In **Options**, **Estimate time for all-blank timestamps** is off by default. Estimation
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

The branch includes the Mac file-picker fix. Both main loading buttons use
Dear PyGui on macOS, avoiding the native Tk crash from a background callback.
Other platforms retain their existing native picker. Cancelling leaves the
current project intact; a failed import displays an error and preserves the
previous recording. A view that cannot compute its analysis shows an unavailable
message without preventing other views from opening.

Eight additional loading regression tests cover both main Mac entry points
avoiding Tk, cancellation, automatic Monitor population, missing oil channels,
repeat loads, and failure recovery. Real-log smoke checks also load 15.csv and
the team's faran_a_3731.csv through the shared project-loading path.

Four monitor layout checks bring the suite to 153 tests. They cover the original
viewport dimensions, compact overview, navigation to sensor details, preservation
of the selected tab during reanalysis, and panel-local sizing without changing
the surrounding application or replacing plot objects.
