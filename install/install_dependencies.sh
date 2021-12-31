sed 's/#.*//' ./install/dependencies_basic.txt  | xargs apk add
sed 's/#.*//' ./install/dependencies_build.txt  | xargs apk add
sed 's/#.*//' ./install/dependencies_run.txt  | xargs apk add
sed 's/#.*//' ./install/dependencies_run_opt.txt  | xargs apk add
