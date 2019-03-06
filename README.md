# Maloja

Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

## Never Asked Questions

### Why not Last.fm / Libre.fm?

Maloja is self-hosted. You will always be able to access your data, and not have to trust anyone to provide an API for it. Your library is not synced with any public or official music database, so you can follow your own tagging schema or even group associated artists together in your charts.

### Why not GNU FM?

Maloja gets rid of all the extra stuff: social networking, radios, recommendations, etc. It only keeps track of your listening history and lets you analyze it. This focus on its core allows it to potentially implement much better database features. One example: Maloja supports multiple artists per track. This means artists who are often just "featuring" in the track title get a place in your charts, and collaborations between several artists finally get credited to all participants.

### Why Maloja?

I like to name my projects after regions in Grisons, Switzerland. Don't waste your time trying to find a connection, I just picked one at random. Do visit Maloja though. It's a great pass to drive.

## Current status

You can check [my own Maloja page](https://maloja.krateng.ch) to see what it currently looks like. 

There is only one scrobbler (a Chrome extension for Plex), but a very simple API to create your own scrobbler.

## Requirements

* [python3](https://www.python.org/) - [GitHub](https://github.com/python/cpython)
* [bottle.py](https://bottlepy.org/) - [GitHub](https://github.com/bottlepy/bottle)
* [waitress](https://docs.pylonsproject.org/projects/waitress/) - [GitHub](https://github.com/Pylons/waitress)

## How to install

1) Either install Maloja with a package, or download the repository to some arbitrary location. If you pick the manual installation, every command needs to be executed from the Maloja directory and led with (`./`). You can also only download the file maloja instead of the whole repository and fetch the rest with

		./maloja update

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

If you didn't install Maloja from the package (and therefore don't have it in /opt/maloja), every command needs to be executed from the Maloja directory and led with (`./`). Otherwise, all commands work in any location and without the prefix.

1) In order to scrobble your music from Plex Web, install the included Chrome extension. Make sure to enter the random key Maloja generates on first startup in the extension. 

2) If you would like to import all your previous last.fm scrobbles, use [benfoxall's website](https://benjaminbenben.com/lastfm-to-csv/) ([GitHub page](https://github.com/benfoxall/lastfm-to-csv)). Use the command

		maloja import *filename*
		
	to import the downloaded file into Maloja.

3) You can interact with the server at any time with the commands
	
		maloja stop
		maloja restart
		maloja start
		maloja update
