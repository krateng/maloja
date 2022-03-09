import toml
import os
import jinja2

from pprint import pprint

with open("pyproject.toml") as filed:
	data = toml.load(filed)

templatedir = "./dev/templates"

for templatefile in os.listdir(templatedir):

	srcfile = os.path.join(templatedir,templatefile)
	trgfile = os.path.join(".",templatefile.replace(".jinja",""))

	with open(srcfile) as templatefiled:
		template = jinja2.Template(templatefiled.read())

	result = template.render(**data)

	with open(trgfile,"w") as filed:
		filed.write(result)
		filed.write('\n')
