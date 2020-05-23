FROM python:3.8.3-slim-buster

WORKDIR /root
RUN apt update \
        && apt install -y --no-install-recommends unzip wget \
        && wget -q "http://github.com/jandelgado/rabtap/releases/download/v1.23/rabtap-v1.23-linux-amd64.zip" \
        && unzip rabtap-v1.23-linux-amd64.zip \
        && mv bin/rabtap-linux-amd64 /usr/local/bin/rabtap \
        && wget -q "https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64" \
        && mv jq-linux64 /usr/local/bin/jq \
        && chmod +x /usr/local/bin/jq

WORKDIR /app
COPY entrypoint.sh pyproject.toml ./
RUN mkdir ./rmq_py_caller
COPY rmq_py_caller/ ./rmq_py_caller/
RUN pip install .

ENV ARG_ADAPTER "[.]"
ENV OUTPUT_ADAPTER ".result"

CMD /app/entrypoint.sh
