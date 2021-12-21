# Basic Development Instructions

After you've cloned the repository, traverse into the `maloja` folder with `cd maloja`.

Your system needs several packages installed. On Alpine, this can be done with

`apk add python3 python3-dev gcc libxml2-dev libxslt-dev py3-pip libc-dev linux-headers`

For other distros, try to find the equivalents of the packages listed or simply check your error output.

Then install all Python dependencies with `pip install -r requirements.txt`. To avoid cluttering your system, consider using a [virtual environment](https://docs.python.org/3/tutorial/venv.html).

## Running the server

For development, you might not want to install maloja files all over your filesystem. Use the environment variable `MALOJA_DATA_DIRECTORY` to force all user files into one central directory - this way, you can also quickly change between multiple configurations.

You can quickly run the server with all your local changes with `python3 -m maloja run`.

You can also build the package with `pip install .`.
