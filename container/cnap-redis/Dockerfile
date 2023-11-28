# base-OS-image for build
ARG OS_VER=20.04
ARG OS_IMAGE=ubuntu
FROM ${OS_IMAGE}:${OS_VER} AS baseimage

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="America/Los_Angeles" apt-get install -y build-essential git cmake autoconf libtool pkg-config uuid-dev numactl libevent-dev asciidoc libjson-c-dev gdb curl libz-dev libssl-dev

# accel for DSA
ARG ACCEL_CONFIG_VERSION="4.0"
ARG ACCEL_CONFIG_DOWNLOAD_URL="https://github.com/intel/idxd-config/archive/accel-config-v$ACCEL_CONFIG_VERSION.tar.gz"
ARG ACCEL_CONFIG_SHA256="6d9bce40d797a87508ce5c5a5b71bb2bdc1cb544848925ed2c4c37b46a1252ce"

RUN /bin/bash -c set -o pipefail && curl -fsSL "$ACCEL_CONFIG_DOWNLOAD_URL" -o accel-config.tar.gz && echo "$ACCEL_CONFIG_SHA256 accel-config.tar.gz" | sha256sum -c - && tar -xzf accel-config.tar.gz
COPY container/cnap-redis/patches/*.patch /
RUN cd idxd-config-accel-config-v$ACCEL_CONFIG_VERSION && \
    patch -p1 < ../idxd-reset.patch && \
    patch -p1 < ../test_runner_disable_shared_queues.patch && \
    ./git-version-gen && \
    autoreconf -i && \
    ./configure -q --libdir=/usr/lib64 --enable-test=yes --disable-docs && \
    make install

# DTO
ARG DTO_VERSION="1.0"
ARG DTO_URL="https://github.com/intel/DTO/archive/refs/tags/v$DTO_VERSION.tar.gz"

RUN curl -fsSL "$DTO_URL" -o dto.tar.gz && tar -xzf dto.tar.gz
COPY container/cnap-redis/patches/idxd.h /usr/local/include/linux/
RUN cd DTO-$DTO_VERSION && \
    make libdto && make install && \
    cp lib* /

# Redis
ARG REDIS_VERSION="7.2.0"
ARG REDIS_URL="https://github.com/redis/redis/archive/refs/tags/$REDIS_VERSION.tar.gz"
RUN curl -fsSL "$REDIS_URL" -o redis.tar.gz && tar -xzf redis.tar.gz
RUN cd redis-$REDIS_VERSION && \
    make && \
    cp src/redis-server /redis-server-orig && \
    cp src/redis-cli /redis-cli && \
    patch -p1 < ../redis_dto.patch && \
    make clean && make && \
    cp src/redis-server /redis-server-dto

# target image with binaries and libraries
FROM ${OS_IMAGE}:${OS_VER} AS redis

RUN groupadd -r nonroot && useradd -r -g nonroot nonroot

COPY --from=baseimage /usr/lib64/libaccel* /lib/x86_64-linux-gnu/ 
COPY --from=baseimage /libdto.so.1.0 /lib/x86_64-linux-gnu/

WORKDIR /opt
RUN mkdir bin
WORKDIR /opt/bin 

COPY --from=baseimage /usr/local/bin /opt/bin
COPY container/cnap-redis/redis.conf /etc/redis.conf

WORKDIR /opt
RUN mkdir redis
WORKDIR /opt/redis

COPY --from=baseimage /redis-server* /opt/redis/
COPY --from=baseimage /redis-cli /usr/local/bin/

RUN ldconfig

USER nonroot

