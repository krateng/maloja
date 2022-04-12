podman build -t maloja . -f Containerfile
podman run --rm -p 42010:42010 -v $PWD/testdata:/mlj -e MALOJA_DATA_DIRECTORY=/mlj maloja
