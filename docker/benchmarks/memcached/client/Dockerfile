ARG PYTHON_VERSION=3.7.12
ARG PYTHON_VERSION_SHORT=3.7

# Memcache rps calculator client
FROM cloudsuite3/data-caching:client

WORKDIR /usr/src/memcached/memcached_client

ARG PYTHON_VERSION
ARG PYTHON_VERSION_SHORT

# -- Python installation
USER root
RUN mkdir /home/memcache && chown memcache:memcache /home/memcache
RUN apt update && apt install -y \
    wget \
    gcc \
    make \
    libssl-dev build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl libbz2-dev liblzma-dev \
    && apt clean

RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
RUN tar -xf Python-${PYTHON_VERSION}.tgz
RUN cd Python-${PYTHON_VERSION} && ./configure --prefix=/usr/src/python --enable-optimizations && make install
ENV PATH=${PATH}:/usr/src/python/bin

USER memcache
RUN pip3 install pandas prometheus-client
# -- Python installation end

COPY ./entrypoint.py ./entrypoint.py
COPY ./entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
