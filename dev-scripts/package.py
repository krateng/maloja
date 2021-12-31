import toml
import os

with open("pyproject.toml") as filed:
	data = toml.load(filed)

info = {
	'name':data['project']['name'],
	'license':"GPLv3",
	'version':data['project']['version'],
	'architecture':'all',
	'description':'"' + data['project']['description'] + '"',
	'url':'"' + data['project']['urls']['homepage'] + '"',
	'maintainer':f"\"{data['project']['authors'][0]['name']} <{data['project']['authors'][0]['email']}>\"",
}


for target in ["apk","deb"]:
	lcmd = f"fpm {' '.join(f'--{key} {info[key]}' for key in info)} -s python -t {target} . "
	print(lcmd)
	os.system(lcmd)
