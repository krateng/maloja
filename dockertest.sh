docker build -t maloja-dev . -f Dockerfile-dev
docker run -p 42010:42010 -v $PWD/testdata:/mlj -e MALOJA_DATA_DIRECTORY=/mlj maloja-dev
