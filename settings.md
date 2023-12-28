If you wish to adjust settings in the settings.ini file, do so while the server
	is not running in order to avoid data being overwritten.

	Technically, each setting can be set via environment variable or the settings
	file - simply add the prefix `MALOJA_` for environment variables. It is recommended
	to use the settings file where possible and not configure each aspect of your
	server via environment variables!

	You also can specify additional settings in the files`/run/secrets/maloja.yml` or
	`/run/secrets/maloja.ini`, as well as their values directly in files of the respective
	name in `/run/secrets/` (e.g. `/run/secrets/lastfm_api_key`).

Settings File			| Environment Variable			| Type			| Description
------					| ---------						| ---------		| ---------
**Setup**
`data_directory`	| `MALOJA_DATA_DIRECTORY`  | String | Folder for all user data. Overwrites all choices for specific directories.
`directory_config`	| `MALOJA_DIRECTORY_CONFIG`  | String | Folder for config data. Only applied when global data directory is not set.
`directory_state`	| `MALOJA_DIRECTORY_STATE`  | String | Folder for state data. Only applied when global data directory is not set.
`directory_logs`	| `MALOJA_DIRECTORY_LOGS`  | String | Folder for log data. Only applied when global data directory is not set.
`directory_cache`	| `MALOJA_DIRECTORY_CACHE`  | String | Folder for cache data. Only applied when global data directory is not set.
`skip_setup`	| `MALOJA_SKIP_SETUP`  | Boolean | Make server setup process non-interactive. Vital for Docker.
`force_password`	| `MALOJA_FORCE_PASSWORD`  | String | On startup, overwrite admin password with this one. This should usually only be done via environment variable in Docker.
`clean_output`	| `MALOJA_CLEAN_OUTPUT`  | Boolean | Use if console output will be redirected e.g. to a web interface.
**Debug**
`logging`	| `MALOJA_LOGGING`  | Boolean | Enable Logging
`dev_mode`	| `MALOJA_DEV_MODE`  | Boolean | Enable developer mode
**Network**
`host`	| `MALOJA_HOST`  | String | Host for your server, e.g. '*' for dual stack, '::' for IPv6 or '0.0.0.0' for IPv4
`port`	| `MALOJA_PORT`  | Integer | Port
**Technical**
`cache_expire_positive`	| `MALOJA_CACHE_EXPIRE_POSITIVE`  | Integer | Days until images are refetched
`cache_expire_negative`	| `MALOJA_CACHE_EXPIRE_NEGATIVE`  | Integer | Days until failed image fetches are reattempted
`db_max_memory`	| `MALOJA_DB_MAX_MEMORY`  | Integer | RAM Usage in percent at which Maloja should no longer increase its database cache.
`use_request_cache`	| `MALOJA_USE_REQUEST_CACHE`  | Boolean | Use request-local DB Cache
`use_global_cache`	| `MALOJA_USE_GLOBAL_CACHE`  | Boolean | This is vital for Maloja's performance. Do not disable this unless you have a strong reason to.
**Fluff**
`scrobbles_gold`	| `MALOJA_SCROBBLES_GOLD`  | Integer | How many scrobbles a track needs to be considered 'Gold' status
`scrobbles_platinum`	| `MALOJA_SCROBBLES_PLATINUM`  | Integer | How many scrobbles a track needs to be considered 'Platinum' status
`scrobbles_diamond`	| `MALOJA_SCROBBLES_DIAMOND`  | Integer | How many scrobbles a track needs to be considered 'Diamond' status
`scrobbles_gold_album`	| `MALOJA_SCROBBLES_GOLD_ALBUM`  | Integer | How many scrobbles an album needs to be considered 'Gold' status
`scrobbles_platinum_album`	| `MALOJA_SCROBBLES_PLATINUM_ALBUM`  | Integer | How many scrobbles an album needs to be considered 'Platinum' status
`scrobbles_diamond_album`	| `MALOJA_SCROBBLES_DIAMOND_ALBUM`  | Integer | How many scrobbles an album needs to be considered 'Diamond' status
`name`	| `MALOJA_NAME`  | String | Name
**Third Party Services**
`metadata_providers`	| `MALOJA_METADATA_PROVIDERS`  | List | List of which metadata providers should be used in what order. Musicbrainz is rate-limited and should not be used first.
`scrobble_lastfm`	| `MALOJA_SCROBBLE_LASTFM`  | Boolean | Proxy-Scrobble to Last.fm
`lastfm_api_key`	| `MALOJA_LASTFM_API_KEY`  | String | Last.fm API Key
`lastfm_api_secret`	| `MALOJA_LASTFM_API_SECRET`  | String | Last.fm API Secret
`lastfm_api_sk`	| `MALOJA_LASTFM_API_SK`  | String | Last.fm API Session Key
`lastfm_username`	| `MALOJA_LASTFM_USERNAME`  | String | Last.fm Username
`lastfm_password`	| `MALOJA_LASTFM_PASSWORD`  | String | Last.fm Password
`spotify_api_id`	| `MALOJA_SPOTIFY_API_ID`  | String | Spotify API ID
`spotify_api_secret`	| `MALOJA_SPOTIFY_API_SECRET`  | String | Spotify API Secret
`audiodb_api_key`	| `MALOJA_AUDIODB_API_KEY`  | String | TheAudioDB API Key
`other_maloja_url`	| `MALOJA_OTHER_MALOJA_URL`  | String | Other Maloja Instance URL
`other_maloja_api_key`	| `MALOJA_OTHER_MALOJA_API_KEY`  | String | Other Maloja Instance API Key
`track_search_provider`	| `MALOJA_TRACK_SEARCH_PROVIDER`  | String | Track Search Provider
`send_stats`	| `MALOJA_SEND_STATS`  | Boolean | Send Statistics
`proxy_images`	| `MALOJA_PROXY_IMAGES`  | Boolean | Whether third party images should be downloaded and served directly by Maloja (instead of just linking their URL)
**Database**
`album_information_trust`	| `MALOJA_ALBUM_INFORMATION_TRUST`  | Choice | Whether to trust the first album information that is sent with a track or update every time a different album is sent
`invalid_artists`	| `MALOJA_INVALID_ARTISTS`  | Set | Artists that should be discarded immediately
`remove_from_title`	| `MALOJA_REMOVE_FROM_TITLE`  | Set | Phrases that should be removed from song titles
`delimiters_feat`	| `MALOJA_DELIMITERS_FEAT`  | Set | Delimiters used for extra artists, even when in the title field
`delimiters_informal`	| `MALOJA_DELIMITERS_INFORMAL`  | Set | Delimiters in informal artist strings with spaces expected around them
`delimiters_formal`	| `MALOJA_DELIMITERS_FORMAL`  | Set | Delimiters used to tag multiple artists when only one tag field is available
`filters_remix`	| `MALOJA_FILTERS_REMIX`  | Set | Filters used to recognize the remix artists in the title
`parse_remix_artists`	| `MALOJA_PARSE_REMIX_ARTISTS`  | Boolean | Parse Remix Artists
`week_offset`	| `MALOJA_WEEK_OFFSET`  | Integer | Start of the week for the purpose of weekly statistics. 0 = Sunday, 6 = Saturday
`timezone`	| `MALOJA_TIMEZONE`  | Integer | UTC Offset
**Web Interface**
`default_range_startpage`	| `MALOJA_DEFAULT_RANGE_STARTPAGE`  | Choice | Default Range for Startpage Stats
`default_step_pulse`	| `MALOJA_DEFAULT_STEP_PULSE`  | Choice | Default Pulse Step
`charts_display_tiles`	| `MALOJA_CHARTS_DISPLAY_TILES`  | Boolean | Display Chart Tiles
`album_showcase`	| `MALOJA_ALBUM_SHOWCASE`  | Boolean | Display a graphical album showcase for artist overview pages instead of a chart list
`display_art_icons`	| `MALOJA_DISPLAY_ART_ICONS`  | Boolean | Display Album/Artist Icons
`default_album_artist`	| `MALOJA_DEFAULT_ALBUM_ARTIST`  | String | Default Albumartist
`use_album_artwork_for_tracks`	| `MALOJA_USE_ALBUM_ARTWORK_FOR_TRACKS`  | Boolean | Use Album Artwork for tracks
`fancy_placeholder_art`	| `MALOJA_FANCY_PLACEHOLDER_ART`  | Boolean | Use fancy placeholder artwork
`show_play_number_on_tiles`	| `MALOJA_SHOW_PLAY_NUMBER_ON_TILES`  | Boolean | Show amount of plays on tiles
`discourage_cpu_heavy_stats`	| `MALOJA_DISCOURAGE_CPU_HEAVY_STATS`  | Boolean | Prevent visitors from mindlessly clicking on CPU-heavy options. Does not actually disable them for malicious actors!
`use_local_images`	| `MALOJA_USE_LOCAL_IMAGES`  | Boolean | Use Local Images
`time_format`	| `MALOJA_TIME_FORMAT`  | String | Time Format
`theme`	| `MALOJA_THEME`  | String | Theme
