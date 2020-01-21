FROM python:slim

WORKDIR /usr/src/app

RUN apt-get update -y
RUN apt-get install gcc -y

COPY requirements.txt . 
RUN pip3 install -r requirements.txt

EXPOSE 42010

COPY . .
ENTRYPOINT ./maloja start
