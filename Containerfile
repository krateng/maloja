FROM lsiobase/alpine:3.17 as base

WORKDIR /usr/src/app



COPY --chown=abc:abc ./requirements.txt ./requirements.txt

# based on https://github.com/linuxserver/docker-pyload-ng/blob/main/Dockerfile
# everything but the app installation is run in one command so we can purge
# all build dependencies and cache in the same layer
# it may be possible to decrease image size slightly by using build stage and
# copying all site-packages to runtime stage but the image is already pretty small
RUN \
  echo "" && \
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
  echo "" && \
	echo "**** install runtime packages ****" && \
	apk add --no-cache \
		python3 \
		py3-lxml \
		tzdata && \
  echo "" && \
	echo "**** install pip dependencies ****" && \
	python3 -m ensurepip && \
  pip3 install -U --no-cache-dir \
	  pip \
	  wheel && \
  echo "" && \
  echo "**** install maloja requirements ****" && \
  pip3 install --no-cache-dir -r requirements.txt && \
  echo "" && \
	echo "**** cleanup ****" && \
	apk del --purge \
		build-deps && \
	rm -rf \
		/tmp/* \
		${HOME}/.cache

# actual installation in extra layer so we can cache the stuff above

COPY --chown=abc:abc . .

RUN \
  echo "" && \
	echo "**** install maloja ****" && \
	apk add --no-cache --virtual=install-deps \
	  py3-pip && \
	pip3 install /usr/src/app && \
	apk del --purge \
		install-deps && \
	rm -rf \
		/tmp/* \
		${HOME}/.cache



COPY container/root/ /

ENV	\
	# Docker-specific configuration
	MALOJA_SKIP_SETUP=yes \
	PYTHONUNBUFFERED=1 \
	# Prevents breaking change for previous container that ran maloja as root
	# On linux hosts (non-podman rootless) these variables should be set to the
	# host user that should own the host folder bound to MALOJA_DATA_DIRECTORY
	PUID=0 \
	PGID=0

EXPOSE 42010
