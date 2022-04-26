import threading
import subprocess
import time
import requests
import os

ACTIVE = True

build_cmd = ["docker","build","-t","maloja",".","-f","Containerfile"]
subprocess.run(build_cmd)

common_prc = (
	["docker","run","--rm","-v",f"{os.path.abspath('./testdata')}:/mlj","-e","MALOJA_DATA_DIRECTORY=/mlj"],
	["maloja"]
)

servers = [
	{'port': 42010},
	{'port': 42011,	'extraargs':["--memory=1g"]},
	{'port': 42012,	'extraargs':["--memory=500m"]}
]
for s in servers:
	cmd = common_prc[0] + ["-p",f"{s['port']}:42010"] + s.get('extraargs',[]) + common_prc[1]
	print(cmd)
	t = threading.Thread(target=subprocess.run,args=(cmd,))
	s['thread'] = t
	t.daemon = True
	t.start()
	time.sleep(5)

time.sleep(5)
while ACTIVE:
	time.sleep(1)
	try:
		for s in servers:
			requests.get(f"http://localhost:{s['port']}")
	except KeyboardInterrupt:
		ACTIVE = False
	except Exception:
		pass

for s in servers:
	s['thread'].join()
