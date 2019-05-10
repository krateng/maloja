# Maloja

Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

You can check [my own Maloja page](https://maloja.krateng.ch) to see what it looks like.

## Never Asked Questions

### Why not Last.fm / Libre.fm / GNU FM?

Maloja is **self-hosted**. You will always be able to access your data in an easily-parseable format. Your library is not synced with any public or official music database, so you can **follow your own tagging schema** or even **group associated artists together** in your charts.

Maloja also gets **rid of all the extra stuff**: social networking, radios, recommendations, etc. It only keeps track of your listening history and lets you analyze it.

Maloja's database has one big advantage: It supports **multiple artists per track**. This means artists who are often just "featuring" in the track title get a place in your charts, and **collaborations between several artists finally get credited to all participants**. This allows you to get an actual idea of your artist preferences over time.

Also neat: You can use your **custom artist or track images**.

## Requirements

* [python3](https://www.python.org/) - [GitHub](https://github.com/python/cpython)
* [bottle.py](https://bottlepy.org/) - [GitHub](https://github.com/bottlepy/bottle)
* [waitress](https://docs.pylonsproject.org/projects/waitress/) - [GitHub](https://github.com/Pylons/waitress)
* [doreah](https://pypi.org/project/doreah/) - [GitHub](https://github.com/krateng/doreah) (at least Version 0.6.1)
* Wand
* setproctitle
  * For Windows: [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/downloads/)
* If you'd like to display images, you will need API keys for [Last.fm](https://www.last.fm/api/account/create) and [Fanart.tv](https://fanart.tv/get-an-api-key/). These are free of charge!

## How to install

1) Either install Maloja with the [debian package](https://github.com/krateng/maloja/raw/master/packages/maloja.deb), or download the repository to some arbitrary location. If you pick the manual installation, every command needs to be executed from the Maloja directory and led with `./`. You can also only download the file `maloja` instead of the whole repository and fetch the rest with

		./maloja install
			-or-
		pip install -r requirements.txt

2) Start the server with

		maloja start

	If you're missing packages, the console output will tell you so. Install them.

2) (Recommended) Put your server behind a reverse proxy for SSL encryption. Configure that proxy to rewrite /db/ requests to the database port. In nginx this would look as follows:

		location / {
			proxy_pass http://yoururl:42010;
		}

		location /db {
			rewrite ^/db(.*)$ $1 break;
			proxy_pass http://yoururl:42011;
		}

## How to use

If you didn't install Maloja from the package (and therefore don't have it in `/opt/maloja`), every command needs to be executed from the Maloja directory and led with `./`. Otherwise, all commands work in any location and without the prefix.

1) In order to scrobble your music from Plex Web or YouTube Music, install the included Chrome extension. Make sure to enter the random key Maloja generates on first startup in the extension. If you use another music player, Maloja has a very simple API to create your own scrobbler.

2) If you would like to import all your previous last.fm scrobbles, use [benfoxall's website](https://benjaminbenben.com/lastfm-to-csv/) ([GitHub page](https://github.com/benfoxall/lastfm-to-csv)). Use the command

		maloja import *filename*

	to import the downloaded file into Maloja.

3) You can interact with the server at any time with the commands

		maloja stop
		maloja restart
		maloja start
		maloja update

	The `update` command will always fetch the latest version, while packages are only offered for release versions.
