# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}
FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base

RUN apt-get update
RUN apt-get install -y \
    curl \
    netcat \
    iputils-ping \
    ssh \
    build-essential \
    default-libmysqlclient-dev

WORKDIR /app
COPY requirements.txt .

RUN useradd -m glados -u 2892
RUN chown -R glados:glados /app
USER glados
ENV PATH="/home/glados/.local/bin:${PATH}"

RUN pip install --user -r requirements.txt
COPY . .

FROM base AS development
ENTRYPOINT CONFIG_FILE_PATH='/app/config.yml' FLASK_APP=app flask run --host=0.0.0.0

FROM base AS production
# Take into account that the app will get the configuration from the variable DELAYED_JOBS_RAW_CONFIG if the config.yml
# file is not found.
ENTRYPOINT CONFIG_FILE_PATH='/app/config.yml' gunicorn wsgi:FLASK_APP -b 0.0.0.0:8080 -t 300