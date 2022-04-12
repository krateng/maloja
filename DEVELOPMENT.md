# Development

Clone the repository and enter it.

```console
	git clone https://github.com/krateng/maloja
	cd maloja
```

## Environment

To avoid cluttering your system, consider using a [virtual environment](https://docs.python.org/3/tutorial/venv.html).

Your system needs several packages installed. For supported distributions, this can be done with e.g.

```console
	sh ./install/install_dependencies_alpine.sh
```

For other distros, try to find the equivalents of the packages listed or simply check your error output.

Then install all Python dependencies with

```console
	pip install -r requirements.txt
```


## Running the server

For development, you might not want to install maloja files all over your filesystem. Use the environment variable `MALOJA_DATA_DIRECTORY` to force all user files into one central directory - this way, you can also quickly change between multiple configurations.

You can quickly run the server with all your local changes with

```console
	python3 -m maloja run
```

You can also build the package with

```console
	pip install .
```


## Docker

You can also always build and run the server with

```console
	sh ./dev/run_docker.sh
```

This will use the directory `testdata`.

## Further help

Feel free to [ask](https://github.com/krateng/maloja/discussions) if you need some help!
