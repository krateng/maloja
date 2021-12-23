#!/usr/bin/env bash
sed 's/#.*//' ./install/deps_build.txt  | xargs apk add
sed 's/#.*//' ./install/deps_run.txt  | xargs apk add
pip3 install wheel
pip3 install malojaserver
