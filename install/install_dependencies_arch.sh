#!/usr/bin/env sh
pacman -Syu
pacman -S --needed \
	gcc \
	python3 \
	libxml2 \
	libxslt \
	libffi \
	glibc \
	python-pip \
	linux-headers \
	python \
	python-lxml \
	tzdata \
	libvips
