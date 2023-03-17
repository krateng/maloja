FROM lsiobase/alpine:3.17 as base

WORKDIR /usr/src/app

COPY --chown=abc:abc . .

# based on https://github.com/linuxserver/docker-pyload-ng/blob/main/Dockerfile
# Everything is run in one command so we can purge all build dependencies and cache in the same layer after maloja is installed
#
# -- it may be possible to decrease image size slightly by using build stage and copying all site-packages to runtime stage
# but the image is already pretty small (117mb uncompressed, ~40mb compressed)
RUN \
    echo "**** install build packages ****" && \
	apk add --no-cache --virtual=build-deps \
	gcc \
	g++ \
	python3-dev \
	libxml2-dev \
	libxslt-dev \
	libffi-dev \
	libc-dev \
	py3-pip \
	linux-headers && \
	echo "**** install runtime packages ****" && \
	apk add --no-cache \
	python3 \
	py3-lxml \
	tzdata && \
	echo "**** install pip dependencies ****" && \
	python3 -m ensurepip && \
    pip3 install -U --no-cache-dir \
        pip \
        wheel && \
    echo "**** install maloja requirements ****" && \
    pip3 install --no-cache-dir -r requirements.txt && \
    echo "**** install maloja ****" && \
    pip3 install /usr/src/app && \
    echo "**** cleanup ****" && \
    apk del --purge \
        build-deps && \
    rm -rf \
        /tmp/* \
        ${HOME}/.cache

COPY container/root/ /

# Docker-specific configuration
# defaulting to IPv4 is no longer necessary (default host is dual stack)
ENV MALOJA_SKIP_SETUP=yes
ENV PYTHONUNBUFFERED=1

# Prevents breaking change for previous container that ran maloja as root
# which meant MALOJA_DATA_DIRECTORY was created by and owned by root (UID 0)
#
# On linux hosts (non-podman rootless) these variables should be set to the host user that should own the host folder bound to MALOJA_DATA_DIRECTORY
ENV PUID=0
ENV PGID=0

EXPOSE 42010
