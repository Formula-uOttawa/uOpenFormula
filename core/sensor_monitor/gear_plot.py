"""Display the findings and assessment supplied by the combined report."""

import math
from pathlib import Path
import matplotlib.pyplot as plt


def plot_gear(run, report):
    values = []
    for row in run["data"]:
        try:
            value = float(row["Gear Position"])
        except ValueError:
            value = math.nan
        values.append(value if math.isfinite(value) else math.nan)

    intervals = report["observations"]["intervals"]
    findings = report["findings"]
    focus = findings[0]["location"] if findings else max(
        intervals, key=lambda item: item["sample_count"], default=None,
    )
    if focus is None:
        figure, axis = plt.subplots(figsize=(12, 5))
        axes = [axis]
    else:
        figure, axes = plt.subplots(2, 1, figsize=(12, 8))

    local_findings = [item for item in findings if item["scope"] == "local_event"]
    marker_artists = []
    for axis in axes:
        axis.step(range(len(values)), values, where="post", linewidth=1.2,
                  color="tab:blue", label="Recorded gear value")
        fractions = [(index, value) for index, value in enumerate(values)
                     if math.isfinite(value) and not value.is_integer()]
        if fractions:
            axis.scatter([item[0] for item in fractions], [item[1] for item in fractions],
                         marker="x", color="tab:orange", s=30, label="Fractional observation")
        labelled = set()
        for interval in intervals:
            reverse = interval["kind"] == "Reverse gear (-1)"
            axis.axvspan(interval["start_sample"] - 0.5, interval["end_sample"] + 0.5,
                         color="tab:green" if reverse else "tab:orange", alpha=0.12,
                         label=interval["kind"] if interval["kind"] not in labelled else None)
            labelled.add(interval["kind"])
        if local_findings:
            markers = axis.scatter(
                [item["location"]["activation_sample"] for item in local_findings],
                [0.95 for item in local_findings],
                transform=axis.get_xaxis_transform(),
                color="crimson", marker="^", s=75, zorder=6, picker=6,
                label="Review finding (click to inspect)",
            )
            marker_artists.append(markers)
        finite = [value for value in values if math.isfinite(value)]
        if finite and min(finite) == max(finite):
            axis.set_ylim(finite[0] - 1, finite[0] + 1)
        axis.set_xlabel("Sample index (starting at 0)")
        axis.set_ylabel("Recorded gear value")
        axis.grid(True, alpha=0.3)
        axis.legend(loc="upper left", ncol=2)

    axes[0].set_title(f"Full recording: {Path(run['source']).name}")

    def show_focus(location, title):
        if len(axes) < 2:
            return
        axes[1].set_xlim(max(0, location["start_sample"] - 20),
                         min(len(values) - 1, location["end_sample"] + 20))
        axes[1].set_title(title)

    if focus is not None:
        title = (f"{findings[0]['id']}: {findings[0]['title']}" if findings else
                 f"Observation: {focus['kind']} — not a finding by itself")
        show_focus(focus, title)

    def select_finding(event):
        if not any(event.artist is artist for artist in marker_artists) or not len(event.ind):
            return
        finding = local_findings[int(event.ind[0])]
        show_focus(finding["location"], f"{finding['id']}: {finding['title']}")
        figure.canvas.draw_idle()

    figure.canvas.mpl_connect("pick_event", select_finding)
    overall = report["overall"]
    figure.suptitle(
        f"{overall['summary']} — {overall['finding_count']} review finding(s)\n"
        f"Assessment: {overall['assessment_scope']}. Timing: {report['timing']['basis']}. "
        f"See the report for {len(report['limitations'])} assessment limitation(s)."
    )
    figure.tight_layout()
    plt.show()
    return figure
