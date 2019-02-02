# Maloja

Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

## Never Asked Questions

### Why not Last.fm / Libre.fm?

Maloja is self-hosted. You will always be able to access your data, and not have to trust anyone to provide an API for it. Your library is not synced with any public or official music database, so you can follow your own tagging schema or even group associated artists together in your charts.

### Why not GNU FM?

Maloja gets rid of all the extra stuff: social networking, radios, recommendations, etc. It only keeps track of your listening history and lets you analyze it. This focus on its core allows it to potentially implement much better database features. One example: Maloja supports multiple artists per track. This means artists who are often just "featuring" in the track title get a place in your charts, and collaborations between several artists finally get credited to all participants.

### Why not use the established API?

Compatibility creates overhead effort. I only made this for myself, so I have no need to support lots of music players and scrobblers. Maloja has a significantly smaller API that allows it to be much simpler and implement its additional features.

### Why Maloja?

I like to name my projects after regions in Grisons, Switzerland. Don't waste your time trying to find a connection, I just picked one at random. Do visit Maloja though. It's a great pass to drive.

## Current status

You can check [my own Maloja page](https://maloja.krateng.ch) to see what it currently looks like. 

The software works fairly well and has a few web views, but there is only one scrobbler (a Chrome extension for Plex).

## How to install

I wouldn't recommend it yet. But if you want to test Maloja, it's fairly easy:

1) Install the requirements:

* [bottle.py](https://github.com/bottlepy/bottle)
* [waitress](https://github.com/Pylons/waitress)


2) Put it anywhere and start server.py
3) (Recommended) Put your server behind a reverse proxy for SSL encryption. Configure that proxy to rewrite /db/ requests to the database port. In nginx this would look as follows:

		location / {
			proxy_pass http://yoururl:42010;
		}

		location /db {
			rewrite ^/db(.*)$ $1 break;
			proxy_pass http://yoururl:42011;
		}
		
If you would like to import all your previous last.fm scrobbles, use [benfoxall's website](https://benjaminbenben.com/lastfm-to-csv/) ([GitHub page](https://github.com/benfoxall/lastfm-to-csv)). Use the python script lastfmconverter.py with two arguments - the downloaded csv file and your new tsv file - to convert your data. Place the tsv file in scrobbles/ and the server will recognize it on startup.
