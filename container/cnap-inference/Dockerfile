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
    echo "$QAT_DRIVER_SHA256 $QAT_DRIVER_RELEASE.tar.gz" | sha256sum -c - && \
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

FROM intel/oneapi-aikit:2023.1.1-devel-ubuntu22.04 AS runner

RUN useradd --create-home appuser

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends libopencv-dev && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG pip_mirror

COPY ./cnap /cnap

COPY --from=builder /usr/lib/libqat* /usr/lib/libusdm_drv_s.so /usr/lib

COPY --from=builder /usr/bin/adf_ctl /usr/bin/qzip /usr/bin

RUN chown -R appuser:appuser /cnap

ENV PYTHONPATH="/cnap:${PYTHONPATH}"

RUN /opt/intel/oneapi/tensorflow/latest/bin/pip install ${pip_mirror} \
    --upgrade --no-cache-dir pip \
    && /opt/intel/oneapi/tensorflow/latest/bin/pip install ${pip_mirror} \
    --no-cache-dir redis>=4.3.0 kafka-python websockets opencv-python prometheus_client \
    ccnp requests

RUN date > /build-date.cnap-inference.txt

EXPOSE 8000

USER appuser

CMD ["/opt/intel/oneapi/tensorflow/latest/bin/python", "/cnap/userv/inference.py"]
