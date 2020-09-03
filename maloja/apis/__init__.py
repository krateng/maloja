from . import native_v1
from .audioscrobbler import Audioscrobbler
from .listenbrainz import Listenbrainz

import copy


apis = {
	"mlj_1":native_v1.api,
	"listenbrainz/1":Listenbrainz().nimrodelapi,
	"audioscrobbler/2.0":Audioscrobbler().nimrodelapi
}

aliases = {
	"native_1":"mlj_1"
}

def init_apis(server):

	for api in apis:
		apis[api].mount(server=server,path="apis/"+api)
