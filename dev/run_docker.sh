docker build -t maloja . -f Containerfile
docker run --rm -p 42010:42010 -v $PWD/testdata:/mlj -e MALOJA_DATA_DIRECTORY=/mlj maloja
