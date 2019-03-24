import os

def instructions(keys):

    html = "<table>"

    html += "<tr><th></th><th>Module</th><th>Author</th><th>Description</th></tr>"

    for f in os.listdir("rules/predefined"):
        if f.endswith(".tsv"):

            try:
                with open("rules/predefined/" + f) as tsvfile:
                    line1 = tsvfile.readline()
                    line2 = tsvfile.readline()

                    if "# NAME: " in line1:
                        name = line1.replace("# NAME: ","")
                    else: name = f
                    if "# DESC: " in line2:
                        desc = line2.replace("# DESC: ","")
                    else: desc = ""

                    author = f.split("_")[0]
            except:
                continue

            html += "<tr>"

            if os.path.exists("rules/" + f):
                html += "<td class='interaction' onclick=deactivateRuleModule(this,'" + f.replace(".tsv","") + "')><a class='textlink'>Remove:</a></td>"
            else:
                html += "<td class='interaction' onclick=activateRuleModule(this,'" + f.replace(".tsv","") + "')><a class='textlink'>Add:</a></td>"
            html += "<td>" + name + "</td>"
            html += "<td>" + author + "</td>"
            html += "<td>" + desc + "</td>"

            html += "</tr>"
    html += "</table>"


    pushresources = []
    replace = {"KEY_PREDEFINED_RULESETS":html}
    return (replace,pushresources)
