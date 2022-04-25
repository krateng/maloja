# Scrobbling

Scrobbling can be done with the native API, see [below](#submitting-a-scrobble).
In order to scrobble from a wide selection of clients, you can also use Maloja's standard-compliant APIs with the following settings:

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

| :warning:    | Note that these are the base URLs - some scrobblers ask you for the full endpoint instead. |
|---------------|:------------------------|

## Scrobbling Guideline

Maloja makes no assumptions about scrobbling behaviour. The clients should decide when and whether a play is scrobbled - the server will accept it as long as it contains all necessary data. However, a general guideline is:

* As soon as a track has been played for 50% of its length or 4 minutes, it should be counted as a scrobble
* That scrobble should be submitted when the play has ended in order to know its duration
* If the total play duration is enough to count as a scrobble, but not longer than the total track length + enough for a second scrobble, it should be submitted as a scrobble with the according duration
* If the duration exceeds this value, the first scrobble should be submitted as a scrobble with the duration of the full track length, while the second scrobble is queued up following the above suggestions in regards to remaining time


<table>
  <tr><td>:memo: Example </td><tr>
  <tr><td>

The user starts playing '(Fine Layers of) Slaysenflite', which is exactly 3:00 minutes long.
* If the user ends the play after 1:22, no scrobble is submitted
* If the user ends the play after 2:06, a scrobble with `"duration":126` is submitted
* If the user jumps back several times and ends the play after 3:57, a scrobble with `"duration":237` is submitted
* If the user jumps back several times and ends the play after 4:49, two scrobbles with `"duration":180` and `"duration":109` are submitted
    
  </td></tr>
<table>


# API Documentation

The native Maloja API is reachable at `/apis/mlj_1`. Endpoints are listed on `/api_explorer`.

All endpoints return JSON data. POST request can be made with query string or form data arguments, but this is discouraged - JSON should be used whenever possible.

No application should ever rely on the non-existence of fields in the JSON data - i.e., additional fields can be added at any time without this being considered a breaking change. Existing fields should usually not be removed or changed, but it is always a good idea to add basic handling for missing fields.
  
## Submitting a Scrobble

The POST endpoint `/newscrobble` is used to submit new scrobbles. These use a flat JSON structure with the following fields:
  
| Key | Type | Description |
| --- | --- | --- |
| `artists` | List(String) | Track artists |
| `title` | String | Track title |
| `album` | String | Name of the album (Optional) |
| `albumartists` | List(String) | Album artists (Optional) |
| `duration` | Integer | How long the song was listened to in seconds (Optional) |
| `length` | Integer | Actual length of the full song in seconds (Optional) |
| `time` | Integer | Timestamp of the listen if it was not at the time of submitting (Optional) |
| `nofix` | Boolean | Skip server-side metadata fixing (Optional) |

## General Structure

The API is not fully consistent in order to ensure backwards-compatibility. Refer to the individual endpoints.  
Generally, most endpoints follow this structure:

| Key | Type | Description |
| --- | --- | --- |
| `status` | String | Status of the request. Can be `success`, `ok`, `error`, `failure`, `no_operation` |
| `error` | Mapping | Details about the error if one occured. |
| `warnings` | List | Any warnings that did not result in failure, but should be noted. Field is omitted if there are no warnings! |
| `desc` | String | Human-readable feedback. This can be shown directly to the user if desired. |
| `list` | List | List of returned [entities](#entity-structure) |

  
Both errors and warnings have the following structure:

| Key | Type | Description |
| --- | --- | --- |
| `type` | String | Name of the error or warning type |
| `value` | varies | Specific data for this error or warning instance |
| `desc` | String | Human-readable error or warning description. This can be shown directly to the user if desired. |


## Entity Structure

Whenever a list of entities is returned, they have the following fields:

### Scrobble

| Key | Type | Description |
| --- | --- | --- |
| `time` | Integer | Timestamp of the Scrobble in UTC |
| `track` | Mapping | The [track](#track) being scrobbled |
| `duration` | Integer | How long the track was played for in seconds |
| `origin` | String | Client that submitted the scrobble, or import source |


<table>
  <tr><td>:memo: Example </td><tr>
  <tr><td>
   
```json
{
  "time": 1650684324,
  "track": {
    "artists": ["Jennie Kim","HyunA","LE","SunMi"],
    "title": "Wow Thing",
    "length":200
  },
  "duration": 196,
  "origin": "client:navidrome_desktop"
}
```
    
  </tr></td>
</table>
  


### Track

| Key | Type | Description |
| --- | --- | --- |
| `artists` | List | The [artists](#artist) credited with the track |
| `title` | String | The title of the track |
| `length` | Integer | The full length of the track in seconds |

<table>
  <tr><td>:memo: Example </td><tr>
  <tr><td>
   
```json
{
  "artists": ["Blackpink","Chou Tzuyu"],
  "title": "MORE",
  "length": 171
}
```
    
  </tr></td>
</table>



### Artist

Artists are just represented as raw Strings.

**Example**

<table>
  <tr><td>:memo: Example </td><tr>
  <tr><td>
   
```json
"Red Velvet"
```
    
  </tr></td>
</table>
