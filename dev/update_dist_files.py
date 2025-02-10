"""
Create necessary files from sources of truth. Currently just the requirements.txt files.
"""

import toml
import os
import jinja2

env = jinja2.Environment(
	loader=jinja2.FileSystemLoader('./templates'),
	autoescape=jinja2.select_autoescape(['html', 'xml']),
	keep_trailing_newline=True
)

with open("../pyproject.toml") as filed:
	data = toml.load(filed)

templatedir = "./templates"

for root,dirs,files in os.walk(templatedir):

	reldirpath = os.path.relpath(root,start=templatedir)
	for f in files:

		relfilepath = os.path.join(reldirpath,f)

		if not f.endswith('.jinja'): continue

		srcfile = os.path.join(root,f)
		trgfile = os.path.join("..", reldirpath,f.replace(".jinja",""))


		template = env.get_template(relfilepath)
		result = template.render(**data)

		with open(trgfile,"w") as filed:
			filed.write(result)
