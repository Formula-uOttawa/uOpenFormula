import json
import sys

if __name__ == "__main__":
    if sys.argv[1:] == ["--choose-project-file"]:
        from ui.project_file_picker import ask_project_filename

        print(json.dumps(ask_project_filename()))
    else:
        from ui.home_page import HomePage

        HomePage()
