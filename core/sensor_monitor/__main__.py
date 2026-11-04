"""Load one recording, run available checks, and open its local sensor report."""

import argparse
import csv
import webbrowser

from .csv_loader import load_csv
from .gear_report import analyze_gear, format_gear_report
from .gear_rules import load_gear_rules
from .run_report import build_run_report, format_run_report, save_run_report
from .timing import build_timing


def main(file_path=None, shifts_expected=None, report_dir=None, detailed=False,
         open_report=True, estimate_time=False, show_gear_plot=False):
    if file_path is None:
        file_path = input("Enter the CSV file path: ").strip().strip('"')
    try:
        run = load_csv(file_path)
        rules = load_gear_rules()
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError) as error:
        print(f"Could not load the recording or gear rules: {error}")
        return None

    try:
        timing = build_timing(run, allow_estimated=estimate_time)
        if not timing["available"]:
            print(timing["reason"])
            answer = input("Estimate time from the CSV sample rate? [y/N]: ").strip().lower()
            if answer in ("y", "yes"):
                timing = build_timing(run, allow_estimated=True)
    except ValueError as error:
        timing = {"available": False, "reason": str(error)}

    gear_report = analyze_gear(run, timing, rules, shifts_expected=shifts_expected)
    try:
        report = build_run_report(run, timing, gear_report)
    except ValueError as error:
        print(f"Could not build the sensor report: {error}")
        return None
    print(format_run_report(report))
    if detailed:
        print(format_gear_report(gear_report, detailed=True))
    try:
        paths = save_run_report(report, directory=report_dir)
        print(f"\nSaved HTML report: {paths['html']}")
        print(f"Saved JSON report: {paths['json']}")
    except OSError as error:
        print(f"\nCould not save the report: {error}")
    else:
        if open_report:
            try:
                opened = webbrowser.open(paths["html"].as_uri())
            except (OSError, webbrowser.Error):
                opened = False
            if not opened:
                print("Open the saved HTML file in your browser to view the table and graphs.")

    if show_gear_plot and gear_report["data_summary"]["channel_available"]:
        # Matplotlib is optional; the standard report only needs Python itself.
        from .gear_plot import plot_gear
        plot_gear(run, gear_report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review the recorded sensor suite in a local HTML report.")
    parser.add_argument("csv_file", nargs="?", help="CSV path; prompt for it when omitted.")
    parser.add_argument("--shifts-expected", choices=("yes", "no", "unknown"), default="unknown")
    parser.add_argument("--report-dir", help="Save HTML and JSON here; defaults to a reports folder beside the CSV.")
    parser.add_argument("--details", action="store_true", help="Also print the full gear analysis and settings.")
    parser.add_argument("--no-open", "--no-plot", dest="no_open", action="store_true",
                        help="Save reports without opening a browser. --no-plot is a legacy alias.")
    parser.add_argument("--gear-plot", action="store_true", help="Also open the original Matplotlib gear graph.")
    parser.add_argument("--estimate-time", action="store_true", help="Allow header-based time estimation when all timestamps are blank.")
    options = parser.parse_args()
    expectation = {"yes": True, "no": False, "unknown": None}[options.shifts_expected]
    main(file_path=options.csv_file, shifts_expected=expectation, report_dir=options.report_dir,
         detailed=options.details, open_report=not options.no_open,
         estimate_time=options.estimate_time, show_gear_plot=options.gear_plot)
