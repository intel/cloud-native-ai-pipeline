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
