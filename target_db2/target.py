"""db2 target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_db2.sinks import (
    db2Sink,
)


class Targetdb2(Target):
    """Sample target for db2."""

    name = "target-db2"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "host",
            th.StringType,
            required=True,
            description="IBM DB2 Database Host",
        ),
        th.Property(
            "port",
            th.IntegerType,
            required=True,
            description="IBM DB2 Database Port",
        ),
        th.Property(
            "user",
            th.StringType,
            required=True,
            description="IBM DB2 Database User Name",
        ),
        th.Property(
            "password",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="IBM DB2 Database User Password",
        ),
        th.Property(
            "database",
            th.StringType,
            required=True,
            description="IBM DB2 Database Name",
        ),
    ).to_dict()

    # todo: decide later whether to include batch size, varchar size
    # timeout & write method (append, upsert, overwrite)

    default_sink_class = db2Sink


if __name__ == "__main__":
    Targetdb2.cli()
