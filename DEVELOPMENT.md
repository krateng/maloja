# Development

Clone the repository and enter it.

```console
	git clone https://github.com/krateng/maloja
	cd maloja
```

## Environment

To avoid cluttering your system, consider using a [virtual environment](https://docs.python.org/3/tutorial/venv.html), or better yet run the included `docker-compose.yml` file.
Your IDE should let you run the file directly, otherwise you can execute `docker compose -f dev/docker-compose.yml -p maloja up --force-recreate --build`.


## Running the server

Use the environment variable `MALOJA_DATA_DIRECTORY` to force all user files into one central directory - this way, you can also quickly change between multiple configurations.


## Further help

Feel free to [ask](https://github.com/krateng/maloja/discussions) if you need some help!
