FROM python:3.9-slim AS downloader

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/openvinotoolkit/open_model_zoo.git

ARG pip_mirror

RUN pip install ${pip_mirror} --upgrade --no-cache-dir pip && \
    pip install ${pip_mirror} --no-cache-dir setuptools openvino-dev \
    open_model_zoo/tools/model_tools

RUN omz_downloader --name ssd_mobilenet_v1_coco

FROM intel/oneapi-aikit:2023.1.1-devel-ubuntu22.04 AS runner

RUN useradd --create-home appuser

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends libopencv-dev && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG pip_mirror

COPY ./cnap /cnap

COPY --from=downloader \
    /public/ssd_mobilenet_v1_coco/ssd_mobilenet_v1_coco_2018_01_28/frozen_inference_graph.pb \
    /demo/model/model.pb

RUN chown -R appuser:appuser /demo /cnap

ENV PYTHONPATH="/cnap:${PYTHONPATH}"

RUN /opt/intel/oneapi/tensorflow/latest/bin/pip install ${pip_mirror} \
    --upgrade --no-cache-dir pip \
    && /opt/intel/oneapi/tensorflow/latest/bin/pip install ${pip_mirror} \
    --no-cache-dir redis>=4.3.0 kafka-python websockets opencv-python

RUN date > /build-date.cnap-inference.txt

USER appuser

CMD ["/opt/intel/oneapi/tensorflow/latest/bin/python", "/cnap/userv/inference.py"]
