# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}
FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base

RUN apt-get update
RUN apt-get install -y \
    curl

WORKDIR /app_workdir
COPY requirements.txt requirements.txt

RUN useradd -m glados -u 2892
RUN chown -R glados:glados /app_workdir
USER glados
ENV PATH="/home/glados/.local/bin:${PATH}"
