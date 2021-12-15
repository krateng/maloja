FROM python:3-alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>
# https://gitlab.com/Joniator/docker-maloja
# https://github.com/Joniator

ARG MALOJA_RELEASE

WORKDIR /usr/src/app

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    libxml2-dev \
    libxslt-dev \
    py3-pip \
    libc-dev \
    linux-headers \
    && \
    pip3 install psutil && \
    pip3 install malojaserver==$MALOJA_RELEASE && \
    apk del .build-deps

RUN apk add --no-cache tzdata

EXPOSE 42010

# expected behavior for a default setup is for maloja to "just work"
ENV MALOJA_SKIP_SETUP=yes

ENTRYPOINT ["maloja", "run"]
