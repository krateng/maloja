# Maloja

Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

You can check [my own Maloja page](https://maloja.krateng.ch) to see what it looks like.

## Why not Last.fm / Libre.fm / GNU FM?

Maloja is **self-hosted**. You will always be able to access your data in an easily-parseable format. Your library is not synced with any public or official music database, so you can **follow your own tagging schema** or even **group associated artists together** in your charts.

Maloja also gets **rid of all the extra stuff**: social networking, radios, recommendations, etc. It only keeps track of your listening history and lets you analyze it.

Maloja's database has one big advantage: It supports **multiple artists per track**. This means artists who are often just "featuring" in the track title get a place in your charts, and **collaborations between several artists finally get credited to all participants**. This allows you to get an actual idea of your artist preferences over time.

Also neat: You can use your **custom artist or track images**.

## Requirements

* Python 3
* Pip packages specified in `requirements.txt`
* If you'd like to display images, you will need API keys for [Last.fm](https://www.last.fm/api/account/create) and [Fanart.tv](https://fanart.tv/get-an-api-key/). These are free of charge!

## How to install

1) Either install Maloja with the [debian package](https://github.com/krateng/maloja/raw/master/packages/maloja.deb), or download the repository to some arbitrary location. If you pick the manual installation, every command needs to be executed from the Maloja directory and led with `./`. You can also only download the file `maloja` instead of the whole repository and fetch the rest with

		./maloja install

2) Install required packages with

		pip3 install -r requirements.txt

3) Start the server with

		maloja start

4) (Recommended) Put your server behind a reverse proxy for SSL encryption.

## How to use

If you didn't install Maloja from the package (and therefore don't have it in `/opt/maloja`), every command needs to be executed from the Maloja directory and led with `./`. Otherwise, all commands work in any location and without the prefix.


1) If you would like to import all your previous last.fm scrobbles, use [benfoxall's website](https://benjaminbenben.com/lastfm-to-csv/) ([GitHub page](https://github.com/benfoxall/lastfm-to-csv)). Use the command

		maloja import *filename*

	to import the downloaded file into Maloja.

2) You can interact with the server at any time with the commands

		maloja stop
		maloja restart
		maloja start
		maloja update

	The `update` command will always fetch the latest version, while packages are only offered for release versions.

3) Various folders have `.info` files with more information on how to use their associated features.

4) If you'd like to implement anything on top of Maloja, visit `/api_explorer`.

## How to scrobble

### Native API

If you use Plex Web, Spotify, Bandcamp, Soundcloud or Youtube Music on Chromium, you can use the included extension (also available on the [Chrome Web Store](https://chrome.google.com/webstore/detail/maloja-scrobbler/cfnbifdmgbnaalphodcbandoopgbfeeh)). Make sure to enter the random key Maloja generates on first startup in the extension settings.

If you want to implement your own method of scrobbling, it's very simple: You only need one POST request to `/api/newscrobble` with the keys `artist`, `title` and `key` - either as form-data or json.

### Standard-compliant API

You can use any third-party scrobbler that supports the audioscrobbler (GNUFM) or the ListenBrainz protocol. This is still very experimental, but give it a try with these settings:

GNU FM | &nbsp;
------ | ---------
Gnukebox URL | Your Maloja URL followed by `/api/s/audioscrobbler`
Username | Any name, doesn't matter
Password | Any of your API keys

ListenBrainz | &nbsp;
------ | ---------
API URL | Your Maloja URL followed by `/api/s/listenbrainz`
Username | Any name, doesn't matter
Auth Token | Any of your API keys

These are tested with the Pano Scrobbler and the Simple Last.fm Scrobbler for Android. I'm thankful for any feedback whether other scrobblers work!

It is recommended to define a different API key for every scrobbler you use in `clients/authenticated_machines.tsv` in your Maloja folder.

### Manual

If you can't automatically scrobble your music, you can always do it manually on the `/manual` page of your Maloja server.
