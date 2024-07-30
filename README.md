# target-db2

`target-db2` is a Singer target for db2.

Build with the [Meltano Target SDK](https://sdk.meltano.com), by the [Infostrux Team](https://www.infostrux.com/)

## Installation

Install from PyPi:

```bash
pipx install target-db2
```

Install from GitHub:

```bash
pipx install git+https://github.com/Infostrux-Solutions/target-db2.git@main
```


### Install via Meltano Configuration (meltano.yml)

```yaml
  loaders:
  - name: target-db2
    namespace: target_db2
    # uncomment one of the following
    # pip_url: git+https://github.com/Infostrux-Solutions/target-db2.git@main
    # pip_url: target-db2
```

_complete the meltano installation with appropriate configuration settings described in [Settings](#settings) section below._

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
| host | True     | None    | IBM Db2 Database Host |
| port | True     | None    | IBM Db2 Database Port |
| user | True     | None    | IBM Db2 Database User Name |
| password | True     | None    | IBM Db2 Database User Password |
| database | True     | None    | IBM Db2 Database Name |
| varchar_size | False    | None    | Field size for Varchar type. Default 10000. <BR/>Since JSON values are serialized to varchar, <BR/>it may be necessary to increase this value. <BR/>Max possible value 32764 |
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

### Db2 Authentication and Authorization


Currently, only username / password (UID / PWD) based authentication is supported. If you need support for additional authentication mechanisms, please open an issue.

The username & password can be provided through `meltano.yml` or the `target-db2`'s config.json. The user must have the following permissions in order to be able to load data into Db2.

* TODO: figure out the minimal permissions requied by meltano to load data to Db2.

## Usage

You can easily run `target-db2` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

_note: requires installing `tap-carbon-intensity`_

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


## Minimal Permissions Required on DB2

This library will perform the following actions on DB2.

* CREATE TABLE
* DROP TABLE
* ALTER TABLE ADD COLUMN
* ALTER TABLE ALTER COLUMN
* INSERT INTO TABLE
* MERGE INTO TABLE USING
* [OPTIONALLY] CREATE SCHEMA

_NOTE: `CREATE SCHEMA` is used to create a new schema where data will be loaded. If the stated target_schema, specified via `default_target_schema` exists, this library will not issue a `CREATE SCHEMA` command_

## Known Limitations & Issues

# Complex Data Structures (arrays & maps)

Complex values such as `dict` or `list` will be json encoded and stored as `VARCHAR`. The `VARCHAR` column has a default size of 10000, and it is user configurable via the setting `varchar_size`.

IBM Db2 allows VARCHAR columns up to 32704 bytes.

This target currently does not write to CLOB fields, PRs welcome!
