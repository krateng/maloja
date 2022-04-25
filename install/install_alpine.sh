#!/usr/bin/env sh
apk update
apk add \
	gcc \
	g++ \
	python3-dev \
	libxml2-dev \
	libxslt-dev \
	libffi-dev \
	libc-dev \
	py3-pip \
	linux-headers \
	python3 \
	py3-lxml \
	tzdata \
	vips

apk add py3-pip
pip install wheel
pip install malojaserver
