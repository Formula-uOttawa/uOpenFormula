# Formula uOttawa's Data Analysis Tool


**What this project is**

This repository contains a custom analysis toolkit that connects to the team’s data sources to generate reusable plots, metrics, and reports tailored to FSAE needs. It is designed to be lightweight and easy for team members to run, modify, and extend as the car and sensors evolve over the season.

​
**Why build our own tools**

Off‑the‑shelf software that integrates with the ECU and dash (such as RaceStudio3) is powerful, but it hides much of the implementation and limits how deeply the team can experiment with custom analysis workflows. Building an in‑house toolkit aligns with the core FSAE goal of learning how systems work by designing and implementing them, rather than only configuring commercial solutions.

​
**Learning focus for new members**

This project is also a training ground for new software sub‑team members to learn modern software development practices in the context of real telemetry and performance questions. Contributors gain experience in data engineering, numerical analysis, and visualization while shipping tools that the rest of the team uses on a regular basis.
​

**Videos to get started**

[Race Telemetry for driver performance](https://youtu.be/lfqkhCCq5sg?si=wPToaZO_qaVD7nn6)

[Data Analysis in Racestudio3](https://youtu.be/IQTP2LN9oNg?si=Uc9kALhEnzJ77W5h)

[Formula SAE design competition format](https://www.youtube.com/watch?v=DqKXPHdX1aY)

**License**

Copyright (c) 2025 Formula uOttawa Contributors.

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contents
1. [Setup](#setup)
2. [Updating Libraries](#updating-libraries)
3. [Publishing a New Release](#publishing-a-new-release)
5. [Analyses](#analyses)
   - [Oil Starvation](#oil-starvation)

## Setup
First, download and install the [Anaconda installer](https://www.anaconda.com/download), this will allow you to organize the libraries we use. Then, open Anaconda prompt (as administrator) and create the project environment from the provided spec file using:

`conda env create -f environment.yml`

This will automatically create the environment, set the correct Python version, and install all required libraries in one step. Once it finishes, activate the environment using:

`conda activate FSAEDataGUI`

Then, verify your dearpygui installation by running the following command:

`python -m dearpygui.demo`

You should see a demo program showing off some features. You can now install Git and your preferred integrated development environment (IDE) to contribute to the software! Make sure to set your environment to FSAEDataGUI in the IDE. You should also be familiar with using branches and making pull requests on Git, you can find many good tutorials on YouTube. We recommend using [GitHub Desktop](https://desktop.github.com/download/) and [VSCode](https://code.visualstudio.com/).

## Updating Libraries
The exe is built automatically by GitHub Actions, and it installs libraries **only from `environment.yml`**. Installing a library with `pip` or `conda` does not automatically update that file, so if you add a library and forget to export your environment, your code will work on your machine but the exe build will fail or crash on launch with `ModuleNotFoundError`.

Whenever you add, remove, or change a library:

1. **Install, update, or remove the library** in your active conda environment using `conda` or `pip` as usual.
2. **Run the program** from source to confirm your changes work as expected.
3. **Export your updated environment to `environment.yml`** (this strips your local machine's `prefix:` path and overwrites the file with exact pinned versions):

```powershell
   conda env export --no-builds | Select-String -NotMatch "^prefix:" | Out-File -Encoding utf8 environment.yml
   ```

4. **Check `git diff environment.yml`** to make sure only the expected packages changed and no unrelated local tools were accidentally included.
5. **Test** the environment file to ensure the solver can resolve it cleanly:

```powershell
   conda --no-plugins install --solver classic --dry-run --file environment.yml
   ```

6. **Commit `environment.yml` together with your code changes** and open your pull request.



## Publishing a New Release

1. Merge your changes into `main` and wait for the **Build exe** run in the Actions tab to go green.
2. Open a terminal in the project folder and make sure you're on the latest `main`:
```
   git checkout main
   git pull
```
3. Create a tag on that commit. Use a new version number each time (`v1.0.0`, `v1.0.1`, `v1.1.0`, ...):
```
   git tag v1.0.1
```
4. Push the tag (a normal `git push` does not send tags):
```
   git push origin v1.0.1
```
5. Watch the **Actions** tab. When the run for your tag goes green, the release appears on the Releases page with `uOpenFormula.exe` attached and auto-generated release notes.

### Fixing a mistake
If you tagged the wrong commit or used the wrong version number:
```
git tag -d v1.0.1
git push origin --delete v1.0.1
```
Then delete the release on the Releases page (if one was created) and redo the steps above.

<br />


## Analyses
### Oil Starvation

The Oil Starvation tool helps our team analyze the oil-system behaviour during vehicle operation and identify any potential losses in oil pressure which causes a lack of lubrication inside the engine. A phenomenon known as oil starvation. It's important for motorsport because oil starvation results in worn cylinder walls, gasket damage, and eventually a blown engine. By Analiyzing oil pressure, oil temperature, engine RPM, and G-Forces, we can better understand how the engine's lubrication system performs under diffrent driving conditions and stress.

During aggressive cornering, braking, and acceleration, engine oil can shift inside the oil pan, reducing the oil supply to critical engine components. Using RPM-dependent pressure thresholds, the system automatically identifies abnormal pressure readings and allows the team to investigate their frequency, duration, and severity. These findings can be compared with physical engine inspections, including checks for cylinder wall damage, bearing wear, and other signs of engine damage. By identifying when and under what conditions oil pressure drops occur, our team can investigate potential lubrication issues, evaluate design improvements, make data-driven decisions to improve engine reliability, and ultimately maximize vehicle performance on track.
<br />

#### **Key Features**

- **Oil Pressure Monitoring:** Visulizes oil pressure alongside engine RPM, oil temperature, and excess oil pressure.
- **G-Force Analysis:** Helps identify whether acceleration, braking, or cornering contributes to oil pressure starvation.
- **Severity Analysis:** Measures how far oil pressure falls outside its ideal range, helping the team evaluate the effectiveness of design improvements.
- **Customizable Thresholds:** Enables the team to adjust acceptable oil pressure ranges for different engine speeds.

<br />




<p align="center">
  <img src="Assets/ReadMeAssets/Distrobution_graph.png" width="400" alt="Oil pressure overview">
  <img src="Assets/ReadMeAssets/GforcePlot.png" width="400" alt="G-Force Plot">
  <img src="Assets/ReadMeAssets/RpmVSPressure.png" width="400" alt="RPM vs Pressure">
  <img src="Assets/ReadMeAssets/gforceGGplot.png" width="400" alt="Starvation event">
  <img src="Assets/ReadMeAssets/RpmAndPressure.png" width="600" alt="RPM and Pressure">
</p>






<br />





![Alt Text](https://i.redd.it/q0dd3k02unqb1.gif)
