The native Maloja API is reachable at `/apis/mlj_1`. Endpoints are listed on `/api_explorer`.

All endpoints return JSON data. POST request can be made with query string or form data arguments, but this is discouraged - JSON should be used whenever possible.

No application should ever rely on the non-existence of fields in the JSON data - i.e., additional fields can be added at any time without this being considered a breaking change. Existing fields should usually not be removed or changed, but it is always a good idea to add basic handling for missing fields.

## Entity Structure

Whenever a list of entities is returned, they have the following fields:

### Scrobble

| Key | Type | Description |
| --- | --- | --- |
| `time` | Integer | Timestamp of the Scrobble in UTC |
| `track` | Mapping | The [track](#Track) being scrobbled |
| `duration` | Integer | How long the track was played for in seconds |
| `origin` | String | Client that submitted the scrobble, or import source |

**Example**

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

### Track

| Key | Type | Description |
| --- | --- | --- |
| `artists` | List | The [artists](#Artist) credited with the track |
| `title` | String | The title of the track |
| `length` | Integer | The full length of the track in seconds |

**Example**

```json
{
  "artists": ["Blackpink","Chou Tzuyu"],
  "title": "MORE",
  "length": 171
}
```

### Artist

Artists are just represented as raw Strings.

**Example**

```json
"Red Velvet"
```

## General Structure

Most endpoints follow this structure:

| Key | Type | Description |
| --- | --- | --- |
| `status` | String | Status of the request. Can be `success`, `ok`, `error`, `failure`, `no_operation` |
| `error` | Mapping | Details about the error if one occured. |
| `warnings` | List | Any warnings that did not result in failure, but should be noted. Field is omitted if there are no warnings! |
| `desc` | String | Human-readable feedback. This can be shown directly to the user if desired. |

Both errors and warnings have the following structure:


| Key | Type | Description |
| --- | --- | --- |
| `type` | String | Name of the error or warning type |
| `value` | varies | Specific data for this error or warning instance |
| `desc` | String | Human-readable error or warning description. This can be shown directly to the user if desired. |



