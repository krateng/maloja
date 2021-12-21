# Basic Development Instructions

> To avoid cluttering your system, you might want to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html).

After you've cloned the repository, traverse into the `maloja` folder with `cd maloja`.

Make sure all dependencies are installed.
Your system needs a few packages, on Alpine Linux these can all be installed with `sh install_alpine.sh`.
For other distros, try to find the equivalents of the packages listed there or simply check your error output.
Python dependencies can be installed with `pip install -r requirements.txt`

## Running the server

You can quickly run the server with all your local changes with `python3 -m maloja run`.

You can also build the package with `pip install .`.
