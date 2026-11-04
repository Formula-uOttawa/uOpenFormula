"""Package the dynamically discovered pages and the sensor report resources."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("ui.views")
datas = collect_data_files("core.sensor_monitor", includes=["*.json", "*.html"])
