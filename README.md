# Maloja

Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

## Never Asked Questions

### Why not Last.fm / Libre.fm?

Maloja is self-hosted. You will always be able to access your data, and not have to trust anyone to provide an API for it. Your library is not synced with any public of official music database, so you can follow your own tagging schema or even group acts together for the purpose of artist charts (e.g. HyunA, 4Minute and Trouble Maker).

### Why not GNU FM?

Maloja gets rid of all the extra stuff: social networking, radios, recommendations, etc. It only keeps track of your listening history and lets you analyze it. This focus on its core allow it to potentially implement much better database features. One example: Maloja supports multiple artists per track. This means artists like Laura Brehm who are often just "featuring" in the track title get a place in your charts, and collaborations between several of your favorite artists finally get credited to all participants.

### Why not use the established API?

Compatibility creates overhead effort. I only made this for myself, so I have no need to support lots of music players and scrobblers. Maloja has a significantly smaller API that allows it to be much simpler.

### Why Maloja?

I like to name my projects after regions in Grisons, Switzerland. Don't waste your time trying to find a connection, I just picked one at random. Do visit Maloja though. It's a great pass to drive.

## Current status

Deep in development. I just uploaded Maloja here in case I die tomorrow. It can accept scrobbles and return some basic stats in JSON format so far.

## How to install

I wouldn't recommend it yet. But if you want to test Maloja, it's fairly easy:

1) Put it anywhere and start server.py
2) (Recommended) Put your server behind a reverse proxy for SSL encryption. Configure that proxy to rewrite /db/ requests to the database port. In nginx this would look as follows:

		location /db {
			rewrite ^/db(.*)$ $1 break;
			proxy_pass http://yoururl:12349;
		}
