import urllib


def instructions(keys):
	from utilities import getArtistImage
	from htmlgenerators import KeySplit
	from htmlmodules import module_artistcharts, module_filterselection
	from malojatime import range_desc


	_, timekeys, _, amountkeys = KeySplit(keys)

	limitstring = range_desc(**timekeys)

	html_filterselector = module_filterselection(keys)



	html_charts, rep = module_artistcharts(**amountkeys,**timekeys)

	if rep is not None:
		imgurl = getArtistImage(rep)
	else:
		imgurl = ""

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []


	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_ARTISTLIST":html_charts,"KEY_RANGE":limitstring,"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
