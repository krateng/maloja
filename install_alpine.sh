#!/usr/bin/env bash
apk add \
	python3 \
	gcc \
	libxml2-dev \
	libxslt-dev \
	libffi-dev \
	libc-dev \
	py3-pip \
	linux-headers \
	tzdata \
	vips
pip3 install wheel
pip3 install malojaserver
