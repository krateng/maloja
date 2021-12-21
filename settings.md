Technically, each setting can be set via environment variable or the settings file - simply add the prefix `MALOJA_` for environment variables. The columns are filled according to what is reasonable, it is recommended to use the settings file where possible and not configure each aspect of your server via environment variables!

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
`host`	| `MALOJA_HOST`  | String | Host for your server - most likely :: for IPv6 or 0.0.0.0 for IPv4
`port`	| `MALOJA_PORT`  | Integer | Port
**Technical**
`cache_expire_positive`	| `MALOJA_CACHE_EXPIRE_POSITIVE`  | Integer | Days until images are refetched
`cache_expire_negative`	| `MALOJA_CACHE_EXPIRE_NEGATIVE`  | Integer | Days until failed image fetches are reattempted
`use_db_cache`	| `MALOJA_USE_DB_CACHE`  | Boolean | Use DB Cache
`cache_database_short`	| `MALOJA_CACHE_DATABASE_SHORT`  | Boolean | Use volatile Database Cache
`cache_database_perm`	| `MALOJA_CACHE_DATABASE_PERM`  | Boolean | Use permanent Database Cache
`db_cache_entries`	| `MALOJA_DB_CACHE_ENTRIES`  | Integer | Maximal Cache entries
`db_max_memory`	| `MALOJA_DB_MAX_MEMORY`  | Integer | Maximal percentage of RAM that should be used by whole system before Maloja discards cache entries. Use a higher number if your Maloja runs on a dedicated instance (e.g. a container)
**Fluff**
`scrobbles_gold`	| `MALOJA_SCROBBLES_GOLD`  | Integer | How many scrobbles a track needs to be considered 'Gold' status
`scrobbles_platinum`	| `MALOJA_SCROBBLES_PLATINUM`  | Integer | How many scrobbles a track needs to be considered 'Platinum' status
`scrobbles_diamond`	| `MALOJA_SCROBBLES_DIAMOND`  | Integer | How many scrobbles a track needs to be considered 'Diamond' status
`name`	| `MALOJA_NAME`  | String | Name
**Third Party Services**
`metadata_providers`	| `MALOJA_METADATA_PROVIDERS`  | List | Which metadata providers should be used in what order. Musicbrainz is rate-limited and should not be used first.
`scrobble_lastfm`	| `MALOJA_SCROBBLE_LASTFM`  | Boolean | Proxy-Scrobble to Last.fm
`lastfm_api_key`	| `MALOJA_LASTFM_API_KEY`  | String | Last.fm API Key
`lastfm_api_secret`	| `MALOJA_LASTFM_API_SECRET`  | String | Last.fm API Secret
`spotify_api_id`	| `MALOJA_SPOTIFY_API_ID`  | String | Spotify API ID
`spotify_api_secret`	| `MALOJA_SPOTIFY_API_SECRET`  | String | Spotify API Secret
`audiodb_api_key`	| `MALOJA_AUDIODB_API_KEY`  | String | TheAudioDB API Key
`track_search_provider`	| `MALOJA_TRACK_SEARCH_PROVIDER`  | String | Track Search Provider
`send_stats`	| `MALOJA_SEND_STATS`  | Boolean | Send Statistics
**Database**
`invalid_artists`	| `MALOJA_INVALID_ARTISTS`  | Set | Artists that should be discarded immediately
`remove_from_title`	| `MALOJA_REMOVE_FROM_TITLE`  | Set | Phrases that should be removed from song titles
`delimiters_feat`	| `MALOJA_DELIMITERS_FEAT`  | Set | Delimiters used for extra artists, even when in the title field
`delimiters_informal`	| `MALOJA_DELIMITERS_INFORMAL`  | Set | Delimiters in informal artist strings with spaces expected around them
`delimiters_formal`	| `MALOJA_DELIMITERS_FORMAL`  | Set | Delimiters used to tag multiple artists when only one tag field is available
**Web Interface**
`default_range_charts_artists`	| `MALOJA_DEFAULT_RANGE_CHARTS_ARTISTS`  | Choice | Default Range Artist Charts
`default_range_charts_tracks`	| `MALOJA_DEFAULT_RANGE_CHARTS_TRACKS`  | Choice | Default Range Track Charts
`default_step_pulse`	| `MALOJA_DEFAULT_STEP_PULSE`  | Choice | Default Pulse Step
`charts_display_tiles`	| `MALOJA_CHARTS_DISPLAY_TILES`  | Boolean | Display Chart Tiles
`discourage_cpu_heavy_stats`	| `MALOJA_DISCOURAGE_CPU_HEAVY_STATS`  | Boolean | Prevent visitors from mindlessly clicking on CPU-heavy options. Does not actually disable them for malicious actors!
`use_local_images`	| `MALOJA_USE_LOCAL_IMAGES`  | Boolean | Use Local Images
`local_image_rotate`	| `MALOJA_LOCAL_IMAGE_ROTATE`  | Integer | Local Image Rotate
`timezone`	| `MALOJA_TIMEZONE`  | Integer | UTC Offset
`time_format`	| `MALOJA_TIME_FORMAT`  | String | Time Format
