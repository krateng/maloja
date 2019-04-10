import urllib


def instructions(keys):
	from utilities import getArtistImage
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_artistcharts, module_filterselection
	from malojatime import range_desc


	_, timekeys, _, amountkeys = uri_to_internal(keys)

	limitstring = timekeys["timerange"].desc(prefix=True)

	html_filterselector = module_filterselection(keys)



	html_charts, rep = module_artistcharts(**amountkeys,**timekeys)

	if rep is not None:
		imgurl = getArtistImage(rep)
	else:
		imgurl = ""

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []


	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,
	"KEY_ARTISTLIST":html_charts,
	"KEY_RANGE":limitstring,
	"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
