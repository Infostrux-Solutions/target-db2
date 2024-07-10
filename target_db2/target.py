"""db2 target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_db2.Db2Sink import (
    Db2Sink,
)


class TargetDb2(Target):
    """Sample target for Bb2."""

    name = "target-db2"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "host",
            th.StringType,
            required=True,
            description="IBM Db2 Database Host",
        ),
        th.Property(
            "port",
            th.IntegerType,
            required=True,
            description="IBM Db2 Database Port",
        ),
        th.Property(
            "user",
            th.StringType,
            required=True,
            description="IBM Db2 Database User Name",
        ),
        th.Property(
            "password",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="IBM Db2 Database User Password",
        ),
        th.Property(
            "database",
            th.StringType,
            required=True,
            description="IBM Db2 Database Name",
        ),
    ).to_dict()

    # Make following user-configurable:
    # - batch size
    # - varchar size
    # - timeout

    default_sink_class = Db2Sink


if __name__ == "__main__":
    TargetDb2.cli()
