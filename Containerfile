FROM alpine:3.15
# Python image includes two Python versions, so use base Alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>

WORKDIR /usr/src/app

# Install run dependencies first
RUN apk add --no-cache python3 tzdata

# system pip could be removed after build, but apk then decides to also remove all its
# python dependencies, even if they are explicitly installed as python packages
# whut
RUN \
	apk add py3-pip && \
	pip install wheel

# these are more static than the real requirements, which means caching
COPY ./requirements_pre.txt ./requirements_pre.txt

RUN \
	apk add --no-cache --virtual .build-deps gcc g++ python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers && \
	pip install --no-cache-dir -r requirements_pre.txt && \
	apk del .build-deps


# less likely to be cached
COPY ./requirements.txt ./requirements.txt

RUN \
	apk add --no-cache --virtual .build-deps gcc g++ python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers && \
	pip install --no-cache-dir -r requirements.txt && \
	apk del .build-deps


# no chance for caching below here

COPY . .

RUN pip install /usr/src/app

# Docker-specific configuration and default to IPv4
ENV MALOJA_SKIP_SETUP=yes
ENV MALOJA_HOST=0.0.0.0

EXPOSE 42010
# use exec form for better signal handling https://docs.docker.com/engine/reference/builder/#entrypoint
ENTRYPOINT ["maloja", "run"]
