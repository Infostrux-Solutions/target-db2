"""db2 target sink class, which handles writing streams."""

from __future__ import annotations
from typing import Any
from singer_sdk.typing import _jsonschema_type_check
from singer_sdk.helpers._typing import get_datelike_property_type
from singer_sdk.sinks import SQLSink
from singer_sdk.connectors import SQLConnector
import sqlalchemy as sa

SDC_FIELDS = [
    "_sdc_extracted_at",
    "_sdc_received_at",
    "_sdc_batched_at",
    "_sdc_deleted_at",
    "_sdc_sequence",
    "_sdc_table_version",
]

def to_sql_type(  # noqa: PLR0911, C901
    jsonschema_type: dict,
) -> sa.types.TypeEngine:
    """Convert JSON Schema type to a SQL type.

    Args:
        jsonschema_type: The JSON Schema object.

    Returns:
        The SQL type.
    """
    if _jsonschema_type_check(jsonschema_type, ("string",)):
        datelike_type = get_datelike_property_type(jsonschema_type)
        if datelike_type:
            if datelike_type == "date-time":
                return sa.types.DATETIME()
            if datelike_type in "time":
                return sa.types.TIME()
            if datelike_type == "date":
                return sa.types.DATE()

        maxlength = jsonschema_type.get("maxLength")
        return sa.types.VARCHAR(maxlength)

    if _jsonschema_type_check(jsonschema_type, ("integer",)):
        return sa.types.INTEGER()
    if _jsonschema_type_check(jsonschema_type, ("number",)):
        return sa.types.DECIMAL()
    if _jsonschema_type_check(jsonschema_type, ("boolean",)):
        return sa.types.BOOLEAN()

    if _jsonschema_type_check(jsonschema_type, ("object",)):
        return sa.types.VARCHAR()

    if _jsonschema_type_check(jsonschema_type, ("array",)):
        return sa.types.VARCHAR()

    return sa.types.VARCHAR()

class DB2Connector(SQLConnector):
    """The connector for DB2"""

    allow_temp_tables: bool = False
    allow_column_alter: bool = False
    allow_merge_upsert: bool = True
    allow_overwrite: bool = True

    def get_sqlalchemy_url(self, config: dict[str, Any]) -> str:
        sa_url = 'ibm_db_sa://{user}:{password}@{host}:{port}/{database}'
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
            self.logger.debug(f"Schema `{schema_name.upper()}` found")
        else:
            self.logger.debug(f"Schema `{schema_name.upper()}` found")
        return exists


    def to_sql_type(self, jsonschema_type: dict) -> sa.types.TypeEngine:
        if _jsonschema_type_check(jsonschema_type, ("string",)):
            datelike_type = get_datelike_property_type(jsonschema_type)
            if not datelike_type and "maxLength" not in jsonschema_type:
                jsonschema_type["maxLength"] = 10000 # setting this for testing. Need to find a better way to pass this.
        return super(DB2Connector, DB2Connector).to_sql_type(jsonschema_type)

class db2Sink(SQLSink):
    """IBM DB2 target sink class."""
    connector_class = DB2Connector