import urllib
import json
from utilities import artistLink

def replacedict(keys,dbport):
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/issues")
	db_data = json.loads(response.read())
	i = 0
	
	html = "<table>"
	if db_data["inconsistent"]:
		html += "<tr>"
		html += "<td>The current database wasn't built with all current rules in effect. Any problem below might be a false alarm and fixing it could create redundant rules.</td>"
		html += """<td class='button important' onclick="fullrebuild()">Rebuild the database</td>"""
		html += "</tr>"
		i += 1
	for d in db_data["duplicates"]:
		html += "<tr>"
		html += "<td>'" + artistLink(d[0]) + "'"
		html += " is a possible duplicate of "
		html += "'" + artistLink(d[1]) + "'</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + d[0] + """','""" + d[1] + """')">""" + d[1] + """ is correct</td>"""
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + d[1] + """','""" + d[0] + """')">""" + d[0] + """ is correct</td>"""
		html += "</tr>"
		i += 1
	for c in db_data["combined"]:
		html += "<tr>"
		html += "<td>'" + artistLink(c[0]) + "' sounds like the combination of " + str(len(c[1])) + " artists: "
		for a in c[1]:
			html += "'" + artistLink(a) + "' "
		html += "</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + c[0] + """','""" + "␟".join(c[1]) + """')">Fix it</td>"""
		html += "</tr>"
		i += 1
	for n in db_data["newartists"]:
		html += "<tr>"
		html += "<td>Is '" + n[0] + "' in '" + artistLink(n[1]) + "' an artist?</td>"
		html += """<td class='button' onclick="newrule(this,'replaceartist','""" + n[1] + """','""" + "␟".join(n[2] + [n[0]]) + """')">Yes</td>"""
		html += "</tr>"
		i += 1
	
	html += "</table>"

	return {"KEY_ISSUESLIST":html,"KEY_ISSUES":str(i)}
