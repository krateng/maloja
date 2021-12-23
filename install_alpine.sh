#!/usr/bin/env bash
sh ./install/alpine_requirements_run.sh
sh ./install/alpine_requirements_build.sh
pip3 install wheel
pip3 install malojaserver
