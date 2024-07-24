"""db2 target class."""

from __future__ import annotations

from textwrap import dedent

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_db2.connector import (
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
        th.Property(
            "varchar_size",
            th.IntegerType,
            description=dedent(
                """
                Field size for Varchar type. Default 10000.
                Since JSON values are serialized to varchar,
                it may be necessary to increase this value.
                Max possible value 32764
                """
            ).strip(),
        ),
    ).to_dict()

    # Make following user-configurable:
    # - batch size
    # - timeout

    default_sink_class = Db2Sink


if __name__ == "__main__":
    TargetDb2.cli()
