FROM python:3-alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>
# https://gitlab.com/Joniator/docker-maloja
# https://github.com/Joniator

WORKDIR /usr/src/app

# this should change rarely, can be cached
COPY ./requirements.txt ./requirements.txt

# Install everything before copying rest of the project, can be cached
RUN \
	apk add --no-cache --virtual .build-deps gcc python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers && \
	apk add --no-cache python3 tzdata && \
	pip3 install --no-cache-dir -r requirements.txt && \
	apk del .build-deps


COPY . .
RUN pip3 install /usr/src/app

# Docker-specific configuration and default to IPv4
ENV MALOJA_SKIP_SETUP=yes
ENV MALOJA_HOST=0.0.0.0

EXPOSE 42010
# use exec form for better signal handling https://docs.docker.com/engine/reference/builder/#entrypoint
ENTRYPOINT ["maloja", "run"]
