"""Db2 target sink class, which handles writing streams."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from singer_sdk.connectors import SQLConnector
from singer_sdk.helpers._typing import get_datelike_property_type
from singer_sdk.sinks import SQLSink
from singer_sdk.typing import _jsonschema_type_check

SDC_FIELDS = [
    "_sdc_extracted_at",
    "_sdc_received_at",
    "_sdc_batched_at",
    "_sdc_deleted_at",
    "_sdc_sequence",
    "_sdc_table_version",
]


class DB2Connector(SQLConnector):
    """The connector for Db2."""

    allow_temp_tables: bool = False
    allow_column_alter: bool = False
    allow_merge_upsert: bool = True
    allow_overwrite: bool = True

    def get_sqlalchemy_url(self, config: dict[str, Any]) -> str:
        """Construct & return a sqlalchemy DB URL."""
        sa_url = "ibm_db_sa://{user}:{password}@{host}:{port}/{database}"
        return sa_url.format(**config)

    def schema_exists(self, schema_name: str) -> bool:
        """Determine if the target database schema already exists.

        Args:
            schema_name: The target database schema name.

        Returns:
            True if the database schema exists, False if not.

        Overrides parent method to perform schema name comparison removing
        unnecessary spaces which seem to padded on by `sa.inspect.get_schema_names`

        Performs schema name comparison in case insensitive manner by converting
        all names to upper-case.
        """
        schemas = sa.inspect(self._engine).get_schema_names()
        exists = schema_name.upper() in {x.strip().upper() for x in schemas}
        if exists:
            self.logger.debug("Schema `%s` found", schema_name)
        else:
            self.logger.debug("Schema `%s` not found", schema_name)
        return exists

    def to_sql_type(self, jsonschema_type: dict) -> sa.types.TypeEngine:
        """Convert JsonSchema to IBM Db2 data type."""
        if _jsonschema_type_check(jsonschema_type, ("string",)):
            datelike_type = get_datelike_property_type(jsonschema_type)
            if not datelike_type and "maxLength" not in jsonschema_type:
                jsonschema_type["maxLength"] = 10000
                # Make configurable later.
        return super(DB2Connector, DB2Connector).to_sql_type(jsonschema_type)


class Db2Sink(SQLSink):
    """IBM Db2 target sink class."""

    connector_class = DB2Connector
