ARG PY_BASE_IMG=3.11-alpine

FROM python:${PY_BASE_IMG}
RUN apk update && \
    apk add nginx envsubst

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY *.py /app

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY start.sh /app/start.sh

CMD ["/bin/sh", "/app/start.sh"]
