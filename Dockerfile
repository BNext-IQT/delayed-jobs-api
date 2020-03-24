# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.7}
FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base
ENV CONFIG_FILE_PATH=${CONFIG_FILE_PATH:-'/etc/run_config/RUN_CONFIG'}

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

FROM base AS development-server
ENTRYPOINT FLASK_APP=app flask run --host=0.0.0.0

FROM base AS production-server
# Take into account that the app will get the configuration from the variable DELAYED_JOBS_RAW_CONFIG if the config.yml
# file is not found.
ENTRYPOINT gunicorn wsgi:FLASK_APP -b 0.0.0.0:5000 -t 300

FROM base AS job-status-daemon
ENTRYPOINT /app/run_daemon.sh