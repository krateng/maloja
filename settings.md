Technically, each setting can be set via environment variable or the settings file. The columns are filled according to what is reasonable. Please do not configure each aspect of your server via environment variables!

Settings File			| Environment Variable			| Type			| Description
------					| ---------						| ---------		| ---------
&nbsp;					| MALOJA_FORCE_PASSWORD			| String		| Sets password for admin login in web interface. This should normally be done via the interactive prompt.
WEB_PORT				| &nbsp;						| Integer		| HTTP port to use for your web interface and API
HOST					| &nbsp;						| String		| Host for your server - most likely `::` for IPv6 or `0.0.0.0` for IPv4
METADATA_PROVIDERS		| &nbsp;						| List (String) | Which metadata providers should be used in what order. Musicbrainz is rate-limited and should not be used first.
SCROBBLE_LASTFM			| &nbsp;						| Boolean		| Proxy-scrobble to Last.fm
LASTFM_API_KEY			| &nbsp;						| String		| API key for Last.fm. Necessary if proxy-scrobbling to Last.fm or using it as a metadata provider
LASTFM_API_SECRET		| &nbsp;						| String		| API secret for Last.fm. Necessary if proxy-scrobbling to Last.fm or using it as a metadata provider
SPOTIFY_API_ID			| &nbsp;						| String		| API ID for Spotify. Necessary if using it as a metadata provider.
SPOTIFY_API_SECRET		| &nbsp;						| String		| API Secret for Spotify. Necessary if using it as a metadata provider.
TRACK_SEARCH_PROVIDER	| &nbsp;						| String		| Provider for track search next to scrobbles. None to disable.
THUMBOR_SERVER			| &nbsp;						| String		| URL of Thumbor server to serve custom artwork.
THUMBOR_SECRET			| &nbsp;						| String		| Secret of Thumbor server
CACHE_EXPIRE_POSITIVE	| &nbsp;						| Integer		| Days until images are refetched
CACHE_EXPIRE_NEGATIVE	| &nbsp;						| Integer		| Days until failed image fetches are reattempted
USE_DB_CACHE			| &nbsp;						| Boolean		| Whether to use the Database Cache.
CACHE_DATABASE_SHORT	| &nbsp;						| Boolean		| Whether to use the Volatile DB Cache.
CACHE_DATABASE_PERM		| &nbsp;						| Boolean		| Whether to use the Permanent DB Cache.
DB_CACHE_ENTRIES		| &nbsp;						| Integer		| Maximal entries of cache.
DB_MAX_MEMORY			| &nbsp;						| Integer		| Maximal percentage of total RAM that should be used (by whole system) before Maloja discards cache entries. Use a higher number if your Maloja runs on a dedicated instance (e.g. a container)
INVALID_ARTISTS			| &nbsp;						| List (String)	| Artists that should be discarded immediately
REMOVE_FROM_TITLE		| &nbsp;						| List (String)	| Phrases that should be removed from song titles
USE_LOCAL_IMAGES		| &nbsp;						| Boolean		| Use local images if present
LOCAL_IMAGE_ROTATE		| &nbsp;						| Integer		| How many seconds to wait between rotating local images
DEFAULT_RANGE_CHARTS_ARTISTS	| &nbsp;				| String		| What range is shown per default for the tile view on the start page
DEFAULT_RANGE_CHARTS_TRACKS		| &nbsp;				| String		| What range is shown per default for the tile view on the start page
DEFAULT_STEP_PULSE				| &nbsp;				| String		| What steps are shown per default for the pulse view on the start page
CHARTS_DISPLAY_TILES	| &nbsp;						| Boolean		| Whether to show tiles on chart pages
DISCOURAGE_CPU_HEAVY_STATS		| &nbsp;				| Boolean		| Prevent visitors from mindlessly clicking on CPU-heavy options. Does not actually disable them for malicious actors!
SCROBBLES_GOLD			| &nbsp;						| Integer		| How many scrobbles should be considered 'Gold' status for a track
SCROBBLES_PLATINUM		| &nbsp;						| Integer		| How many scrobbles should be considered 'Platinum' status for a track
SCROBBLES_DIAMOND		| &nbsp;						| Integer		| How many scrobbles should be considered 'Diamond' status for a track
NAME					| &nbsp;						| String		| Your Name for display
SKIP_SETUP				| MALOJA_SKIP_SETUP				| Boolean		| Whether to make server startup non-interactive. Vital for docker.
LOGGING					| MALOJA_LOGGING				| Boolean		| Enable logging
DEV_MODE				| MALOJA_DEV_MODE				| Boolean		| Enable developer mode
