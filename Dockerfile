FROM python:3.6-alpine

WORKDIR /usr/src/app

RUN apk update
RUN apk add gcc libxml2-dev libxslt-dev py3-pip libc-dev

RUN pip3 install malojaserver

EXPOSE 42010

ENTRYPOINT maloja start
