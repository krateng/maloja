FROM python:slim

WORKDIR /usr/src/app
COPY . . 

RUN apt-get update -y
RUN apt-get install gcc -y

RUN pip3 install -r requirements.txt

EXPOSE 42010

ENTRYPOINT ./maloja start
