import urllib


def instructions(keys):
	from utilities import getArtistImage
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_artistcharts, module_filterselection, module_artistcharts_tiles
	from malojatime import range_desc
	from doreah.settings import get_settings


	_, timekeys, _, amountkeys = uri_to_internal(keys)

	limitstring = timekeys["timerange"].desc(prefix=True)

	html_filterselector = module_filterselection(keys)




	html_charts, rep = module_artistcharts(**amountkeys,**timekeys)

	if rep is not None:
		imgurl = getArtistImage(rep)
	else:
		imgurl = ""

	topartists = ""
	imgdiv = '<div style="background-image:url('+imgurl+')"></div>'
	if get_settings("CHARTS_DISPLAY_TILES"):
		topartists = module_artistcharts_tiles(timerange=timekeys["timerange"])
		imgdiv = """<div style="background-image:url('favicon.png')"></div>"""



	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []


	replace = {
	"KEY_TOPARTIST_IMAGEDIV":imgdiv,
	"KEY_ARTISTCHART":topartists,
	"KEY_ARTISTLIST":html_charts,
	"KEY_RANGE":limitstring,
	"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
