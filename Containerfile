FROM python:3-alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>
# https://gitlab.com/Joniator/docker-maloja
# https://github.com/Joniator

WORKDIR /usr/src/app


# Copy project into dir
COPY . .

RUN \
    # Build dependencies (This will pipe all packages from the file)
    sed 's/#.*//' ./install/dependencies_build.txt  | xargs apk add --no-cache --virtual .build-deps && \
    # Runtime dependencies (Same)
    sed 's/#.*//' ./install/dependencies_run.txt  | xargs apk add --no-cache && \
    # Python dependencies
    pip3 install --no-cache-dir -r requirements.txt && \
    # Local project install
    pip3 install /usr/src/app && \
    # Remove build dependencies
    apk del .build-deps

# expected behavior for a default setup is for maloja to "just work"
ENV MALOJA_SKIP_SETUP=yes

EXPOSE 42010
# use exec form for better signal handling https://docs.docker.com/engine/reference/builder/#entrypoint
ENTRYPOINT ["maloja", "run"]
