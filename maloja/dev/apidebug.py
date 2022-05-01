import bottle, waitress

from ..pkg_global.conf import malojaconfig

from doreah.logging import log
from nimrodel import EAPI as API


PORT = malojaconfig["PORT"]
HOST = malojaconfig["HOST"]

the_listener = API(delay=True)

@the_listener.get("{path}")
@the_listener.post("{path}")
def all_requests(path,**kwargs):
	result = {
		'path':path,
		'payload': kwargs
	}
	log(result)
	return result


def run():
	server = bottle.Bottle()
	the_listener.mount(server,path="apis")
	waitress.serve(server, listen=f"*:{PORT}")
