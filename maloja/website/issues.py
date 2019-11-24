import urllib
from .. import database
from ..htmlgenerators import artistLink

def instructions(keys):

	db_data = database.issues()
	i = 0

	html = "<table class='list'>"
	if db_data["inconsistent"]:
		html += "<tr>"
		html += "<td>The current database wasn't built with all current rules in effect. Any problem below might be a false alarm and fixing it could create redundant rules.</td>"
		html += """<td class='button important' onclick="fullrebuild()"><div>Rebuild the database</div></td>"""
		html += "</tr>"
		i += 1
	for d in db_data["duplicates"]:
		html += "<tr>"
		html += "<td>'" + artistLink(d[0]) + "'"
		html += " is a possible duplicate of "
		html += "'" + artistLink(d[1]) + "'</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + d[0] + """','""" + d[1] + """')"><div>""" + d[1] + """ is correct</div></td>"""
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + d[1] + """','""" + d[0] + """')"><div>""" + d[0] + """ is correct</div></td>"""
		html += "</tr>"
		i += 1
	for c in db_data["combined"]:
		html += "<tr>"
		html += "<td>'" + artistLink(c[0]) + "' sounds like the combination of " + str(len(c[1])) + " artists: "
		for a in c[1]:
			html += "'" + artistLink(a) + "' "
		html += "</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + c[0] + """','""" + "␟".join(c[1]) + """')"><div>Fix it</div></td>"""
		html += "</tr>"
		i += 1
	for n in db_data["newartists"]:
		html += "<tr>"
		html += "<td>Is '" + n[0] + "' in '" + artistLink(n[1]) + "' an artist?</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + n[1] + """','""" + "␟".join(n[2] + [n[0]]) + """')"><div>Yes</div></td>"""
		html += "</tr>"
		i += 1

	html += "</table>"

	return ({"KEY_ISSUESLIST":html,"KEY_ISSUES":str(i)},[])
