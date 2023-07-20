FROM python:3.10-slim

RUN useradd --create-home appuser

COPY ./cnap /cnap

RUN chown -R appuser:appuser /cnap

ENV PYTHONPATH="/cnap:${PYTHONPATH}"

ARG pip_mirror

RUN pip3 install ${pip_mirror} --upgrade --no-cache-dir pip && \
    pip3 install ${pip_mirror} --no-cache-dir websockets redis>=4.3.0

RUN date > /build-date.cnap-wss.txt

EXPOSE 31611

USER appuser

CMD ["python", "/cnap/userv/websocket_server.py"]
