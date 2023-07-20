FROM python:3.10-slim

RUN useradd --create-home appuser

COPY ./cnap /cnap

RUN chown -R appuser:appuser /cnap

ENV PYTHONPATH="/cnap:${PYTHONPATH}"

ARG pip_mirror

RUN pip3 install ${pip_mirror} --upgrade --no-cache-dir pip && \
    pip3 install ${pip_mirror} --no-cache-dir flask flask_cors redis

RUN date > /build-date.cnap-ppdb.txt

EXPOSE 5000

USER appuser

CMD ["python", "/cnap/userv/pipeline_server.py"]
