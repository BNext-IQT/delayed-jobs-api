# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}
FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base

RUN apt-get update
RUN apt-get install -y \
    curl

WORKDIR /app
COPY requirements.txt .

RUN useradd -m glados -u 2892
RUN chown -R glados:glados /app
USER glados
ENV PATH="/home/glados/.local/bin:${PATH}"

RUN pip install --user -r requirements.txt
EXPOSE 5000
COPY . .

COPY configurations/minimal_dev_config.yml .
CMD CONFIG_FILE_PATH='/app/minimal_dev_config.yml' gunicorn wsgi:FLASK_APP -b 0.0.0.0:8080