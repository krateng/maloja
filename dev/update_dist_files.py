import toml
import os
import jinja2

with open("pyproject.toml") as filed:
	data = toml.load(filed)

templatedir = "./dev/templates"

for root,dirs,files in os.walk(templatedir):

	relpath = os.path.relpath(root,start=templatedir)
	for f in files:

		srcfile = os.path.join(root,f)
		trgfile = os.path.join(relpath,f.replace(".jinja",""))


		with open(srcfile) as templatefiled:
			template = jinja2.Template(templatefiled.read())

		result = template.render(**data)

		with open(trgfile,"w") as filed:
			filed.write(result)
			filed.write('\n')
