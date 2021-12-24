# maloja-lib

Library for Python music players to allow users to scrobble to [Maloja](https://github.com/krateng/maloja) servers.

```
	from malojalib import MalojaInstance

	instance = MalojaInstance(user_supplied_url,user_supplied_key)

	instance.scrobble(artists=['K/DA','Howard Shore','Blackbeard's Tea Party],title='Grüezi Wohl Frau Stirnimaa')

```
