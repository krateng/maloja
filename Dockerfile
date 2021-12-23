FROM python:3-alpine

# Based on the work of Jonathan Boeckel <jonathanboeckel1996@gmail.com>
# https://gitlab.com/Joniator/docker-maloja
# https://github.com/Joniator

WORKDIR /usr/src/app


# Copy project into dir
COPY . .

# Build dependencies
RUN sh ./install/alpine_requirements_build_volatile.sh

# Runtime dependencies
RUN sh ./install/alpine_requirements_run.sh

# Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Local project install
RUN pip3 install /usr/src/app

RUN apk del .build-deps

# expected behavior for a default setup is for maloja to "just work"
ENV MALOJA_SKIP_SETUP=yes

EXPOSE 42010
# use exec form for better signal handling https://docs.docker.com/engine/reference/builder/#entrypoint
ENTRYPOINT ["maloja", "run"]
