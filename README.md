# WRiFT
A repository to facilitate exploration, experimentation, and implementation of WRiFT: Wildfire Risks Forecasting Tool by Team Anthropocene Institute in the Spring 2022 edition of CSE 498 (Capstone) at Michigan State University.

## conda

Throughout the project, we'll rely on conda for package management. Although conda brings more overhead into the equation than pip, it is more robust, auto-solves dependency conflicts, and will allow our client to easily clone and reproduce our results at the snap of their fingers. 

The following steps explain how to configure conda for use with this repository.
1. Install conda on your machine by following the instructions at [this link](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html). Note that Miniconda will require 400 MB of space, while Anaconda will require 3 GB of space. Miniconda is a condensed version of Anaconda with fewer pre-installed packages (like numpy, scipy, etc.). If you have the space, Anaconda and its pre-installed packages may save time in the long run. 
2. If you are installing on Windows, check the "Add to Path" box during installation. It will warn you that this is not recommended, but doing this will make it much easier to run conda from powershell/cmd in Windows, and will reduce cross-platform conda behavior headaches down the line.
3. After installing conda, run `conda init` to get everything setup. Afterwards, restart your powershell/cmd/terminal. On Windows, you may get an error saying that your powershell setup script was not loaded because it tried to run a script; see [this StackOverflow thread](https://stackoverflow.com/a/67996662) to resolve that issue. 
4. When restarting your powershell/cmd/terminal, you should now see `(base)` prepended to your powershell/cmd/terminal prompt. This indicates that you are working out of the base conda environment.
5. Clone this repository to your Capstone folder with `git clone https://github.com/andrewmcdonald27/CapstoneExploration.git`
6. Create a virtual environment for this project with all necessary dependencies by running `conda env create -f environment.yml` from the terminal in the main `CapstoneExploration` folder of this repository.
7. Activate the virtual environment for use when running Python on the command line by running `conda activate CapstoneExploration`. You should see the `(base)` prefix on your powershell/cmd/terminal prompt change to `(CapstoneExploration)` after this. You can check that the correct environment is activated by running `conda env list`. 
8. Now that our virtual environment is activated, all calls to Python scripts from the command line will run using the packages installed in the virtual environment.
9. You can tell [PyCharm](https://www.jetbrains.com/help/pycharm/conda-support-creating-conda-virtual-environment.html) and [VSCode](https://code.visualstudio.com/docs/python/environments) to run Python files using the `CapstoneExploration` virtual environment by following the instructions at each link for configuration from an existing environment.   
10. You can deactivate the virtual environment and return to your base conda installation as necessary with `conda deactivate`.
11. When adding code to this repository which requires a new package, add a line to the `environment.yml` file under the `dependencies:` header with the package name and version number you are using, following the example of `flask=2.0.2` in formatting. Strive to write code that works with the latest version of the package you are working with, but be sure to list the explicit package number in the `environment.yml` file so that our code will continue to work as expected when future updates of dependencies are released. You can obtain the version number of a package with `conda list <packagename>`. For example, running `conda list flask` with environment `CapstoneExploration` active indicates that flask is indeed version 2.0.2.
12. Check out [this conda cheatsheet](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf) for more helpful tips. Google and StackOverflow will also be of great help with any conda-related questions.

To run the app locally, execute "python wsgi.py" from the source directory with your conda environment active.

The source in this repository will run without any additional downloads. For optimal performance, download all the files in [this google](https://drive.google.com/drive/folders/12l7qknzmnbe-at5y4IYGQDvXwLRwfYqK?usp=sharing) 
drive folder to app/data/.