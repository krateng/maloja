import setuptools
import toml


with open("pyproject.toml") as fd:
	pkgdata = toml.load(fd)
projectdata = pkgdata['project']


# extract info
with open(projectdata['readme'], "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=projectdata['name'],
    version=projectdata['version'],
    author=projectdata['authors'][0]['name'],
    author_email=projectdata['authors'][0]['email'],
    description=projectdata["description"],
	license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=projectdata['urls']['repository'],
    packages=[projectdata['name']],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
	python_requires=projectdata['requires-python'],
	install_requires=projectdata['dependencies'],
	include_package_data=True,
	entry_points = {
		'console_scripts':[
			k + '=' + projectdata['scripts'][k] for k in projectdata['scripts']
		]

	}
)
