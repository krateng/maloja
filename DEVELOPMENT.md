# Basic Development Instructions

After you've cloned the repository, traverse into the `maloja` folder with `cd maloja`.

Make sure all dependencies are installed.
Your system needs a few packages, on Alpine Linux these should all be installed with `sh install_alpine.sh`.
Python dependencies can be installed with `pip install -r requirements.txt`

## Running the server

You can quickly run the server with all your local changes with `python3 -m maloja.proccontrol.control run`.

You can also build the package with `pip install .`.
