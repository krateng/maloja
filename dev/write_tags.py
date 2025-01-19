"""
Read the changelogs / version metadata and create all git tags
"""

import os
import subprocess as sp
import yaml

FOLDER = "dev/releases"

releases = {}
for f in os.listdir(FOLDER):
	if f == "branch.yml": continue
	#maj,min = (int(i) for i in f.split('.')[:2])

	with open(os.path.join(FOLDER,f)) as fd:
		data = yaml.safe_load(fd)

	name = data.pop('minor_release_name')

	for tag in data:
		tagtup = tuple(int(i) for i in tag.split('.'))
		releases[tagtup] = data[tag]

		# this is a bit dirty, works on our data
		if len(tagtup)<3 or tagtup[2] == 0: releases[tagtup]['name'] = name


for version in releases:

	info = releases[version]
	version = '.'.join(str(v) for v in version)
	msg = [
		f"Version {version}" + (f" '{info.get('name')}'" if info.get('name') else ''),
		*([""] if info.get('notes') else []),
		*[f"* {n}" for n in info.get('notes',[])]
	]


	cmd = [
		'git','tag','--force',
		'-a',f'v{version}',
		'-m',
		'\n'.join(msg),
		info['commit']
	]

	try:
		prev_tag = sp.check_output(["git","show",f'v{maj}.{min}.{hot}']).decode()
		prev_tag_commit = prev_tag.split('\n')[6].split(" ")[1]
	except Exception:
		pass
	else:
		assert prev_tag_commit == info['commit']

	print(cmd)
	sp.run(cmd)
