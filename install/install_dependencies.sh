sed 's/#.*//' ./install/dependencies_run.txt  | xargs apk add
sed 's/#.*//' ./install/dependencies_build.txt  | xargs apk add
