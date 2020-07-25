FROM python:3-alpine

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
    pip3 install malojaserver && \
    apk del .build-deps

EXPOSE 42010

ENTRYPOINT maloja run
