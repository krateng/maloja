import os

author = {
	"name":"Johannes Krattenmacher",
	"email":"maloja@krateng.dev",
	"github": "krateng"
}
version = 2,0,2
versionstr = ".".join(str(n) for n in version)


try:
	DATA_DIR = os.environ["XDG_DATA_HOME"].split(":")[0]
	assert os.path.exists(DATA_DIR)
except:
	DATA_DIR = os.path.join(os.environ["HOME"],".local/share/")

DATA_DIR = os.path.join(DATA_DIR,"maloja")
os.makedirs(DATA_DIR,exist_ok=True)
