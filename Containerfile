FROM lsiobase/alpine:3.17 as base
# Python image includes two Python versions, so use base Alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>

WORKDIR /usr/src/app

# Install run dependencies first
RUN apk add --no-cache python3 py3-lxml tzdata

# system pip could be removed after build, but apk then decides to also remove all its
# python dependencies, even if they are explicitly installed as python packages
# whut
RUN \
	apk add py3-pip && \
	pip install wheel


COPY ./requirements.txt ./requirements.txt

RUN \
	apk add --no-cache --virtual .build-deps gcc g++ python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers && \
	pip install --no-cache-dir -r requirements.txt && \
	apk del .build-deps

COPY container/root/ /


# no chance for caching below here

COPY --chown=abc:abc . .

RUN pip install /usr/src/app

# Docker-specific configuration
# defaulting to IPv4 is no longer necessary (default host is dual stack)
ENV MALOJA_SKIP_SETUP=yes
ENV PYTHONUNBUFFERED=1

EXPOSE 42010
