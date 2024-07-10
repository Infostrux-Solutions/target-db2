# target-db2

`target-db2` is a Singer target for db2.

Build with the [Meltano Target SDK](https://sdk.meltano.com).

<!--

Developer TODO: Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

## Installation

Install from PyPi:

```bash
pipx install target-db2
```

Install from GitHub:

```bash
pipx install git+https://github.com/haleemur-infostrux/target-db2.git@main
```

-->

Currently, the only supported method to install this target is. In future, the package will be published to PyPi

### Install from GitHub:

```bash
pipx install git+https://github.com/haleemur-infostrux/target-db2.git@main
```

### Install from GitHub in the Meltano Configuration (meltano.yml)

```yaml
  loaders:
  - name: target-db2
    namespace: target_db2
    pip_url: git+https://github.com/haleemur-infostrux/target-db2.git@main
```

_complete the meltano installation with appropriate configuration settings described in [Settings](#settings) section below.

## Configuration

<!--
Developer TODO: Each time the project's version is bumped, recreate these sections

1. Capabilities
2. Settings
3. Supported Python Versions

This section can be created by copy-pasting the CLI output from:

```
target-db2 --about --format=markdown
```
-->


## Capabilities

* `about`
* `stream-maps`
* `schema-flattening`
* `validate-records`

## Settings

| Setting | Required | Default | Description |
|:--------|:--------:|:-------:|:------------|
| host | True     | None    | IBM DB2 Database Host |
| port | True     | None    | IBM DB2 Database Port |
| user | True     | None    | IBM DB2 Database User Name |
| password | True     | None    | IBM DB2 Database User Password |
| database | True     | None    | IBM DB2 Database Name |
| add_record_metadata | False    | None    | Add metadata to records. |
| load_method | False    | TargetLoadMethods.APPEND_ONLY | The method to use when loading data into the destination. `append-only` will always write all input records whether that records already exists or not. `upsert` will update existing records and insert new records. `overwrite` will delete all existing records and insert all input records. |
| batch_size_rows | False    | None    | Maximum number of rows in each batch. |
| validate_records | False    |       1 | Whether to validate the schema of the incoming streams. |
| stream_maps | False    | None    | Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html). |
| stream_map_config | False    | None    | User-defined config values to be used within map expressions. |
| faker_config | False    | None    | Config for the [`Faker`](https://faker.readthedocs.io/en/master/) instance variable `fake` used within map expressions. Only applicable if the plugin specifies `faker` as an addtional dependency (through the `singer-sdk` `faker` extra or directly). |
| faker_config.seed | False    | None    | Value to seed the Faker generator for deterministic output: https://faker.readthedocs.io/en/master/#seeding-the-generator |
| faker_config.locale | False    | None    | One or more LCID locale strings to produce localized output for: https://faker.readthedocs.io/en/master/#localization |
| flattening_enabled | False    | None    | 'True' to enable schema flattening and automatically expand nested properties. |
| flattening_max_depth | False    | None    | The max depth to flatten schemas. |

A full list of supported settings and capabilities is available by running: `target-db2 --about`

## Supported Python Versions

* 3.8
* 3.9
* 3.10
* 3.11
* 3.12

### Configure using environment variables

This Singer target will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

<!--
Developer TODO: If your target requires special access on the destination system, or any special authentication requirements, provide those here.
-->

## Usage

You can easily run `target-db2` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-db2 --version
target-db2 --help
# Test using the "Carbon Intensity" sample:
tap-carbon-intensity | target-db2 --config /path/to/target-db2-config.json
```

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `target-db2` CLI interface directly using `poetry run`:

```bash
poetry run target-db2 --help
```

### Testing with [Meltano](https://meltano.com/)

_**Note:** This target will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

This project is supplied with a custom `meltano.yml` project file already created, as well as a docker-compose.yml file to set up source & target systems for end-to-end testing.


Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd target-db2
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke target-db2 --version

# OR run a test `elt` pipeline with the Carbon Intensity sample tap:
docker compose up -d
meltano run tap-carbon-intensity target-db2
# after testing is complete, remember to shut down the container resources
docker compose down

# OR run a test `elt` pipeline with the supplied postgresql
# source & sample data generator
docker compose up -d
python generate_postgresql_data.py
meltano run tap-postgres target-db2
# after testing is complete, remember to shut down the container resources
docker compose down
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the Meltano Singer SDK to
develop your own Singer taps and targets.
