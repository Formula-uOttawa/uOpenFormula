"""Application entry points for the existing offline sensor analysis."""

from .csv_loader import load_csv
from .gear_report import analyze_gear
from .gear_rules import load_gear_rules
from .run_report import build_run_report
from .timing import build_timing


def analyze_run(run, *, allow_estimated=False, shifts_expected=None):
    """Return the same report used by the offline HTML/JSON interface.

    No prompts, browser launch, or file exports occur here. Unusable timing
    retains sample-index views and disables the same checks as the original.
    """
    try:
        timing = build_timing(run, allow_estimated=allow_estimated)
    except ValueError as error:
        timing = {"available": False, "reason": str(error)}
    gear = analyze_gear(run, timing, load_gear_rules(), shifts_expected=shifts_expected)
    return build_run_report(run, timing, gear)


def analyze_recording(path, *, allow_estimated=False, shifts_expected=None):
    return analyze_run(load_csv(path), allow_estimated=allow_estimated,
                       shifts_expected=shifts_expected)


def analyze_loaded_recording(data_manager, **options):
    """Use the project's selected CSV without modifying its numeric dataframe.

    Read the source CSV to preserve blank versus nonnumeric readings, exact
    fractional codes, metadata, and units. DataManager's numeric conversion
    cannot supply all that original evidence. Only source reads occur here.
    """
    if not data_manager.path or data_manager.df is None:
        raise ValueError("Load a project recording first, or open a CSV in Sensor Monitor.")
    return analyze_recording(data_manager.path, **options)
