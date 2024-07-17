ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

WORKDIR /target_db2

RUN python -m pip install --upgrade pip
RUN pip install poetry

COPY libs ./libs
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install
COPY target_db2 ./target_db2
COPY tests ./tests
