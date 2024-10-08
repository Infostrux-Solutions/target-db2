ARG MELTANO_VERSION=v3.4.2-python3.12
FROM meltano/meltano:${MELTANO_VERSION} as base

WORKDIR /etl

# the meltano.yml project can contain all the configuration needed
# for simple projects
# Update this if the project gets bigger and configuration is split
# into multiple files.
COPY meltano.yml .
RUN meltano lock --update --all
RUN meltano install
# containerized projects are read-only.
ENV MELTANO_PROJECT_READONLY 1

ENTRYPOINT [ "meltano" ]
