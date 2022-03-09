docker build -t maloja . -f Dockerfile
docker run --rm -p 42010:42010 -v $PWD/testdata:/mlj -e MALOJA_DATA_DIRECTORY=/mlj maloja
