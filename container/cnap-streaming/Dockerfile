FROM ubuntu:20.04 as builder

ARG DEBIAN_FRONTEND=noninteractive
ARG QAT_DRIVER_RELEASE="QAT20.L.1.0.50-00003"
ARG QAT_DRIVER_SHA256="41b45f936dc870299a00dffeeb1818774de1a3791d8fbb4365a5074a22f20017"
ARG QATZIP_URL=https://github.com/intel/QATzip
ARG QATZIP_VERSION="v1.1.2"

RUN apt-get update && \
    apt-get install -y --no-install-recommends libudev-dev build-essential make gcc g++ nasm \
    pkg-config libssl-dev zlib1g-dev wget ca-certificates git yasm autoconf cmake libtool \
    libboost-all-dev openssl haproxy liblz4-tool liblz4-dev && \
    rm -rf /var/lib/apt/lists/*

# QAT driver
WORKDIR /home/project/QAT

RUN wget https://downloadmirror.intel.com/783270/$QAT_DRIVER_RELEASE.tar.gz && \
    echo "$QAT_DRIVER_SHA256 $QAT_DRIVER_RELEASE.tar.gz" | sha256sum -c -&& \
    tar -zxvf $QAT_DRIVER_RELEASE.tar.gz -C . && \
    sed -i -e 's/cmn_ko$//' -e 's/lac_kernel$//' quickassist/Makefile && \
    KERNEL_SOURCE_ROOT=/tmp ./configure --disable-param-check --prefix=/usr && \
    make quickassist-all adf-ctl-all && \
    install -m 755 build/libqat_s.so /usr/lib/ && \
    install -m 755 build/libusdm_drv_s.so /usr/lib/ && \
    install -m 755 build/adf_ctl /usr/bin/

# QATzip
WORKDIR /home/project

RUN git clone -b $QATZIP_VERSION $QATZIP_URL && \
    cd QATzip && \
    export ICP_ROOT=/home/project/QAT && \
    export QZ_ROOT=/home/project/QATzip && \
    ./autogen.sh && \
    ./configure --with-ICP_ROOT=$ICP_ROOT --prefix=/usr && \
    make install

FROM ubuntu:22.04 AS downloader

COPY ./tools /tools

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN ./tools/video_downloader.sh

FROM python:3.10-slim AS runner

RUN useradd --create-home appuser

COPY ./cnap /cnap

COPY --from=downloader /sample-videos /demo/sample-videos

COPY --from=builder /usr/lib/libqat* /usr/lib/libusdm_drv_s.so /usr/lib

COPY --from=builder /usr/bin/adf_ctl /usr/bin/qzip /usr/bin

RUN chown -R appuser:appuser /cnap /demo

ENV PYTHONPATH="/cnap:${PYTHONPATH}"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ARG pip_mirror

RUN pip3 install ${pip_mirror} --upgrade --no-cache-dir pip && \
    pip3 install ${pip_mirror} --no-cache-dir redis numpy opencv-python kafka-python protobuf

RUN date > /build-date.cnap-streaming.txt

USER appuser

CMD ["python", "/cnap/userv/streaming.py"]
