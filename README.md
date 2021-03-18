# Maloja

[![](https://img.shields.io/pypi/v/malojaserver?style=for-the-badge)](https://pypi.org/project/malojaserver/)
[![](https://img.shields.io/pypi/l/malojaserver?style=for-the-badge)](https://github.com/krateng/maloja/blob/master/LICENSE)
[![](https://img.shields.io/codeclimate/maintainability/krateng/maloja?style=for-the-badge)](https://codeclimate.com/github/krateng/maloja)


Simple self-hosted music scrobble database to create personal listening statistics. No recommendations, no social network, no nonsense.

You can check [my own Maloja page](https://maloja.krateng.ch) to see what it looks like (it's down fairly often because I use it as staging environment, that doesn't reflect the stability of the Maloja software!).


> **IMPORTANT**: With the update 2.7, the backend has been reworked to use a password. With a normal installation, you are asked to provide a password on setup. If you use docker or skip the setup for other reasons, you need to provide the environment variable `MALOJA_FORCE_PASSWORD` on first startup.

> **IMPORTANT**: With the update 2.9, the API endpoints have changed. All old endpoints should be redirected properly, but I recommend updating your clients to use the new ones.

## Table of Contents
* [Features](#features)
* [How to install](#how-to-install)
	* [Environment](#environment)
	* [New Installation](#new-installation)
	* [Update](#update)
	* [Docker](#docker)
* [How to use](#how-to-use)
	* [Basic control](#basic-control)
	* [Data](#data)
	* [Customization](#customization)
* [How to scrobble](#how-to-scrobble)
	* [Native support](#native-support)
	* [Native API](#native-api)
	* [Standard-compliant API](#standard-compliant-api)
	* [Manual](#manual)
* [How to extend](#how-to-extend)

## Features

* **Self-hosted**: You will always be able to access your data in an easily-parseable format. Your library is not synced with any public or official music database, so you can follow your own tagging schema.
* **Associated Artists**: Compare different artist's popularity in your listening habits including subunits, collaboration projects or solo performances by their members. Change these associations at any time without losing any information.
* **Multi-Artist Tracks**: Some artists often collaborate with others or are listed under "featuring" in the track title. Instead of tracking each combination of artists, each individual artist competes in your charts.
* **Custom Images**: Don't rely on the community to select the best pictures for your favorite artists. Upload your own so that your start page looks like you want it to look.
* **Proxy Scrobble**: No need to fully commit or set up every client twice - you can configure your Maloja server to forward your scrobbles to other services.
* **Standard-compliant API**: Use existing, mature apps or extensions to scrobble to your Maloja server.
* **Manual Scrobbling**: Listening to vinyl or elevator background music? Simply submit a scrobble with the web interface.
* **Keep it Simple**: Unlike Last.fm and similar alternatives, Maloja doesn't have social networking, radios, recommendations or any other gimmicks. It's a tool to keep track of your listening habits over time.


## How to install

### Environment

I can support you with issues best if you use **Alpine Linux**. In my experience, **2 GB RAM** should do nicely, but higher amounts allow more caching and reduce page load times for complicated statistics. My personal recommendation is using a dedicated LXC container (e.g. on Proxmox), but of course Maloja will also run on a VM, in Docker or on bare metal.

### New Installation

1) Make sure you have Python 3.5 or higher installed. You also need some basic packages that should be present on most systems, but I've provided simple shell scripts for Alpine and Ubuntu to get everything you need.

2) If you'd like to display images, you will need API keys for [Last.fm](https://www.last.fm/api/account/create) and [Spotify](https://developer.spotify.com/dashboard/applications). These are free of charge!

3) Download Maloja with the command `pip install malojaserver`. Make sure to use the correct python version (Use `pip3` if necessary).

4) (Recommended) Put your server behind a reverse proxy for SSL encryption. Make sure that you're proxying to the IPv6 address unless you changed your settings to use IPv4. If you're running Maloja in a container, make sure to expose port 32400 (or whichever port you have chosen in your settings).

5) (Optional) You can set up a cronjob to start your server on system boot, and potentially restart it on a regular basis:

```
@reboot sleep 15 && maloja start
42 0 7 * * maloja restart
```


### Update

* If you use a version before 2.0 (1.x), install the package as described above, then manually copy all your user data to your `/etc/maloja` folder.
* Otherwise, simply run the command `maloja update` or use `pip`s update mechanic.


### Docker

There is a Dockerfile in the repo that should work by itself. You can also use the unofficial [Dockerhub repository](https://hub.docker.com/r/joniator/maloja) kindly provided by joniator.

You might want to set the environment variables `MALOJA_FORCE_PASSWORD`, `MALOJA_SKIP_SETUP` and `MALOJA_DATA_DIRECTORY`.


## How to use

### Basic control

Start and stop the server with

	maloja start
	maloja stop
	maloja restart

If something is not working, you can try

	maloja debug

to run the server in the foreground.


### Data

* If you would like to import all your previous last.fm scrobbles, use [benfoxall's website](https://benjaminbenben.com/lastfm-to-csv/) ([GitHub page](https://github.com/benfoxall/lastfm-to-csv)). Use the command `maloja import *filename*`	to import the downloaded file into Maloja.

* To backup your data, run `maloja backup` or, to only backup essential data (no artwork etc), `maloja backup -l minimal`.

* To fix your database (e.g. after you've added new rules), use `maloja fix`.

### Customization

* Have a look at the [available settings](settings.md) and specifiy your choices in `/etc/maloja/settings/settings.ini`. You can also set each of these settings as an environment variable with the prefix `MALOJA_` (e.g. `MALOJA_SKIP_SETUP`).

* If you have activated admin mode in your web interface, you can upload custom images for artists or tracks by simply dragging them onto the existing image on the artist or track page. You can also manage custom images directly in the file system - consult `images.info` in the `/var/lib/maloja/images` folder.

* To specify custom rules, consult the `rules.info` file in `/etc/maloja/rules`. You can also apply some predefined rules on the `/setup` page of your server.


## How to scrobble

You can set up any amount of API keys in the file `authenticated_machines.tsv` in the `/etc/maloja/clients` folder. It is recommended to define a different API key for every scrobbler you use.

### Native support

These solutions allow you to directly setup scrobbling to your Maloja server:
* [Tauon](https://tauonmusicbox.rocks) Desktop Player
* [Web Scrobbler](https://github.com/web-scrobbler/web-scrobbler) Browser Extension
* [Multi Scrobbler](https://github.com/FoxxMD/multi-scrobbler) Desktop Application
* [Cmus-maloja-scrobbler](https://git.sr.ht/~xyank/cmus-maloja-scrobbler) Script
* [OngakuKiroku](https://github.com/Atelier-Shiori/OngakuKiroku) Desktop Application (Mac)
* [Albula](https://github.com/krateng/albula) Music Server
* [Maloja Scrobbler](https://chrome.google.com/webstore/detail/maloja-scrobbler/cfnbifdmgbnaalphodcbandoopgbfeeh) Chromium Extension (also included in the repository) for Plex Web, Spotify, Bandcamp, Soundcloud or Youtube Music

### Native API

If you want to implement your own method of scrobbling, it's very simple: You only need one POST request to `/apis/mlj_1/newscrobble` with the keys `artist`, `title` and `key` (and optionally `album`,`duration` (in seconds) and `time`(for cached scrobbles)) - either as form-data or json.

If you're the maintainer of a music player or server and would like to implement native Maloja scrobbling, feel free to reach out - I'll try my best to help. For Python applications, you can simply use the [`malojalib` package](https://pypi.org/project/maloja-lib/) for a consistent interface even with future updates.

### Standard-compliant API

You can use any third-party scrobbler that supports the audioscrobbler (GNUFM) or the ListenBrainz protocol. This is still very experimental, but give it a try with these settings:

GNU FM | &nbsp;
------ | ---------
Gnukebox URL | Your Maloja URL followed by `/apis/audioscrobbler`
Username | Doesn't matter
Password | Any of your API keys

ListenBrainz | &nbsp;
------ | ---------
API URL | Your Maloja URL followed by `/apis/listenbrainz`
Username | Doesn't matter
Auth Token | Any of your API keys

Audioscrobbler v1.2 | &nbsp;
------ | ---------
Server URL | Your Maloja URL followed by `/apis/audioscrobbler_legacy`
Username | Doesn't matter
Password | Any of your API keys

Known working scrobblers:
* [Pano Scrobbler](https://github.com/kawaiiDango/pScrobbler) for Android
* [Simple Scrobbler](https://simple-last-fm-scrobbler.github.io) for Android
* [Airsonic Advanced](https://github.com/airsonic-advanced/airsonic-advanced) (requires you to supply the full endpoint (`yoururl.tld/apis/listenbrainz/1/submit-listens`))
* [Funkwhale](https://dev.funkwhale.audio/funkwhale/funkwhale) (use the legacy API `yoururl.tld/apis/audioscrobbler_legacy`)
* [mpdscribble](https://github.com/MusicPlayerDaemon/mpdscribble) (use the legacy API `yoururl.tld/apis/audioscrobbler_legacy`)

I'm thankful for any feedback whether other scrobblers work!



### Manual

If you can't automatically scrobble your music, you can always do it manually on the `/admin_manual` page of your Maloja server.


## How to extend

If you'd like to implement anything on top of Maloja, visit `/api_explorer`.
