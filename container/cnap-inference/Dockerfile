FROM intel/oneapi-aikit:2023.1.1-devel-ubuntu22.04 AS runner

RUN useradd --create-home appuser

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends libopencv-dev && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG pip_mirror

COPY ./cnap /cnap

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
