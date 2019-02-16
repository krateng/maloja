import subprocess
import time

def startserver():
	time.sleep(5)
	print("Starting the Maloja server...")
	
	p = subprocess.Popen(["python3","server.py"])
	exit("Restarter has done his job and is exiting!")


def restart():
	#args = sys.argv[:]
	print("Starting the restarter...")
	
	#args.insert(0, sys.executable)
	#print(' '.join(args))
	
	p = subprocess.Popen(["python3","restarter.py"])
	#exit("Exiting!")



if __name__ == "__main__":
	startserver()
