import os
from ..globalconf import datadir

def instructions(keys):

    html = "<table class='misc'>"

    html += "<tr><th></th><th>Module</th><th>Author</th><th>Description</th></tr>"


    validchars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for f in os.listdir(datadir("rules/predefined")):
        if f.endswith(".tsv"):

            rawf = f.replace(".tsv","")
            valid = True
            for char in rawf:
                if char not in validchars:
                    valid = False
                    break # don't even show up invalid filenames

            if not valid: continue
            if not "_" in rawf: continue

            try:
                with open(datadir("rules/predefined",f)) as tsvfile:
                    line1 = tsvfile.readline()
                    line2 = tsvfile.readline()

                    if "# NAME: " in line1:
                        name = line1.replace("# NAME: ","")
                    else: name = rawf.split("_")[1]
                    if "# DESC: " in line2:
                        desc = line2.replace("# DESC: ","")
                    else: desc = ""

                    author = rawf.split("_")[0]
            except:
                continue

            html += "<tr>"

            if os.path.exists(datadir("rules",f)):
                html += "<td class='interaction' onclick=deactivateRuleModule(this,'" + rawf + "')><a class='textlink'>Remove:</a></td>"
            else:
                html += "<td class='interaction' onclick=activateRuleModule(this,'" + rawf + "')><a class='textlink'>Add:</a></td>"
            html += "<td>" + name + "</td>"
            html += "<td>" + author + "</td>"
            html += "<td>" + desc + "</td>"

            html += "</tr>"
    html += "</table>"


    pushresources = []
    replace = {"KEY_PREDEFINED_RULESETS":html}
    return (replace,pushresources)
