FROM node:18-slim

RUN useradd --create-home appuser

COPY ./cnap /cnap

RUN chown -R appuser:appuser /cnap && \
    date > /build-date.cnap-spa.txt

USER appuser

WORKDIR /cnap/ui/

RUN npm install --registry=https://registry.npmmirror.com

EXPOSE 5173

CMD ["npm", "run", "dev"]
