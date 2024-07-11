"""Db2 target sink class, which handles writing streams."""

from __future__ import annotations

import json
import typing as t
from textwrap import dedent
from random import choice
from string import ascii_lowercase
import sqlalchemy as sa
from singer_sdk.connectors import SQLConnector
from singer_sdk.helpers._typing import get_datelike_property_type
from singer_sdk.helpers.capabilities import TargetLoadMethods
from singer_sdk.typing import _jsonschema_type_check
from singer_sdk.sinks import SQLSink

if t.TYPE_CHECKING:
    from sqlalchemy.engine import Engine

from ibm_db_sa import VARCHAR

MAX_VARCHAR_SIZE = 10000
MAX_PK_STRING_SIZE = 1022
SDC_FIELDS = [
    "_sdc_extracted_at",
    "_sdc_received_at",
    "_sdc_batched_at",
    "_sdc_deleted_at",
    "_sdc_sequence",
    "_sdc_table_version",
]


class JSONVARCHAR(sa.types.TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)


class DB2Connector(SQLConnector):
    """The connector for Db2."""

    allow_temp_tables: bool = False
    allow_column_alter: bool = True
    allow_merge_upsert: bool = True
    allow_overwrite: bool = True

    @staticmethod
    def get_column_alter_ddl(
        table_name: str,
        column_name: str,
        column_type: sa.types.TypeEngine,
    ) -> sa.DDL:
        """Get the alter column DDL statement.

        Override this if your database uses a different syntax for altering columns.

        Args:
            table_name: Fully qualified table name of column to alter.
            column_name: Column name to alter.
            column_type: New column type string.

        Returns:
            A sqlalchemy DDL instance.
        """
        return sa.DDL(
            "ALTER TABLE %(table_name)s ALTER COLUMN %(column_name)s SET DATA TYPE %(column_type)s",
            {  # type: ignore
                "table_name": table_name,
                "column_name": column_name,
                "column_type": column_type,
            },
        )

    def get_sqlalchemy_url(self, config: dict[str, t.Any]) -> str:
        """Construct & return a sqlalchemy DB URL."""
        sa_url = "ibm_db_sa://{user}:{password}@{host}:{port}/{database}"
        return sa_url.format(**config)

    def create_engine(self) -> Engine:
        """Creates and returns a new engine. Do not call outside of _engine.

        Parent method overridden to prevent raising & catching an exception.

        NOTE: if needed, update the method logic to add a json_serializer
              e.g.
              return sa.create_engine(
                self.sqlalchemy_url,
                echo=False,
                pool_pre_ping=True,
                json_serializer=<function serialize_json>
              )

        Returns:
            A new SQLAlchemy Engine.
        """
        return sa.create_engine(
            self.sqlalchemy_url,
            echo=False,
            pool_pre_ping=True,
        )

    def create_schema(self, schema_name: str) -> None:
        """Create target schema.

        Args:
            schema_name: The target schema to create.
        """
        with self._engine.connect() as conn, conn.begin():
            conn.execute(sa.schema.CreateSchema(schema_name))

    def _adapt_column_type(
        self,
        full_table_name: str,
        column_name: str,
        sql_type: sa.types.TypeEngine,
    ) -> None:
        """Adapt table column type to support the new JSON schema type.

        Args:
            full_table_name: The target table name.
            column_name: The target column name.
            sql_type: The new SQLAlchemy type.

        Raises:
            NotImplementedError: if altering columns is not supported.
        """
        current_type: sa.types.TypeEngine = self._get_column_type(
            full_table_name,
            column_name,
        )

        # remove collation if present and save it
        current_type_collation = self.remove_collation(current_type)

        # Check if the existing column type and the sql type are the same
        if str(sql_type) == str(current_type):
            # The current column and sql type are the same
            # Nothing to do
            return

        # Not the same type, generic type or compatible types
        # calling merge_sql_types for assistnace
        compatible_sql_type = self.merge_sql_types([current_type, sql_type])

        if str(compatible_sql_type) == str(current_type):
            # Nothing to do
            return

        # Put the collation level back before altering the column
        if current_type_collation:
            self.update_collation(compatible_sql_type, current_type_collation)

        if not self.allow_column_alter:
            msg = (
                "Altering columns is not supported. Could not convert column "
                f"'{full_table_name}.{column_name}' from '{current_type}' to "
                f"'{compatible_sql_type}'."
            )
            raise NotImplementedError(msg)

        alter_column_ddl = self.get_column_alter_ddl(
            table_name=full_table_name,
            column_name=column_name,
            column_type=compatible_sql_type,
        )
        with self._connect() as conn:
            conn.execute(alter_column_ddl)

    def _create_empty_column(
        self,
        full_table_name: str,
        column_name: str,
        sql_type: sa.types.TypeEngine,
    ) -> None:
        """Create a new column.

        Args:
            full_table_name: The target table name.
            column_name: The name of the new column.
            sql_type: SQLAlchemy type engine to be used in creating the new column.

        Raises:
            NotImplementedError: if adding columns is not supported.
        """
        if not self.allow_column_add:
            msg = "Adding columns is not supported."
            raise NotImplementedError(msg)

        column_add_ddl = self.get_column_add_ddl(
            table_name=full_table_name,
            column_name=column_name,
            column_type=sql_type,
        )
        with self._engine.connect() as conn, conn.begin():
            conn.execute(column_add_ddl)

    def prepare_table(
        self,
        full_table_name: str,
        schema: dict,
        primary_keys: t.Sequence[str],
        partition_keys: list[str] | None = None,
        as_temp_table: bool = False,  # noqa: FBT002, FBT001
    ) -> None:
        """Adapt target table to provided schema if possible.

        Args:
            full_table_name: the target table name.
            schema: the JSON Schema for the table.
            primary_keys: list of key properties.
            partition_keys: list of partition keys.
            as_temp_table: True to create a temp table.
        """
        if not self.table_exists(full_table_name=full_table_name):
            self.create_empty_table(
                full_table_name=full_table_name,
                schema=schema,
                primary_keys=primary_keys,
                partition_keys=partition_keys,
                as_temp_table=as_temp_table,
            )
            return
        if self.config["load_method"] == TargetLoadMethods.OVERWRITE:
            self.get_table(full_table_name=full_table_name).drop(self._engine)
            self.create_empty_table(
                full_table_name=full_table_name,
                schema=schema,
                primary_keys=primary_keys,
                partition_keys=partition_keys,
                as_temp_table=as_temp_table,
            )
            return

        for property_name, property_def in schema["properties"].items():
            self.prepare_column(
                full_table_name,
                property_name,
                self.to_sql_type(property_def, property_name in primary_keys),
            )

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
        msg = "Schema `%s`" + (" found" if exists else " not found")
        self.logger.debug(msg, schema_name)
        return exists

    def to_sql_type(
        self,
        jsonschema_type: dict,
        is_primary_key: bool = False,  # noqa: FBT001, FBT002
    ) -> sa.types.TypeEngine:
        """Convert JsonSchema to IBM Db2 data type."""

        string_length = MAX_PK_STRING_SIZE if is_primary_key else MAX_VARCHAR_SIZE
        if _jsonschema_type_check(jsonschema_type, ("string",)):
            datelike_type = get_datelike_property_type(jsonschema_type)
            if not datelike_type and "maxLength" not in jsonschema_type:
                jsonschema_type["maxLength"] = string_length
        is_obj = _jsonschema_type_check(jsonschema_type, ("object",))
        is_arr = _jsonschema_type_check(jsonschema_type, ("array",))
        if is_obj or is_arr:
            return JSONVARCHAR(MAX_VARCHAR_SIZE)
        return super(DB2Connector, DB2Connector).to_sql_type(jsonschema_type)

    def create_empty_table(  # noqa: PLR0913
        self,
        full_table_name: str,
        schema: dict,
        primary_keys: t.Sequence[str] | None = None,
        partition_keys: list[str] | None = None,
        as_temp_table: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Create an empty target table.

        Args:
            full_table_name: the target table name.
            schema: the JSON schema for the new table.
            primary_keys: list of key properties.
            partition_keys: list of partition keys.
            as_temp_table: True to create a temp table.

        Raises:
            NotImplementedError: if temp tables are unsupported and as_temp_table=True.
            RuntimeError: if a variant schema is passed with no properties defined.
        """
        if as_temp_table:
            msg = "Temporary tables are not supported."
            raise NotImplementedError(msg)

        _ = partition_keys  # Not supported in generic implementation.

        _, schema_name, table_name = self.parse_full_table_name(full_table_name)
        meta = sa.MetaData(schema=schema_name)
        columns: list[sa.Column] = []
        primary_keys = primary_keys or []
        try:
            properties: dict = schema["properties"]
        except KeyError as e:
            msg = f"Schema for '{full_table_name}' does not define properties: {schema}"
            raise RuntimeError(msg) from e
        for property_name, property_jsonschema in properties.items():
            is_primary_key = property_name in primary_keys
            columns.append(
                sa.Column(
                    property_name,
                    self.to_sql_type(property_jsonschema, is_primary_key),
                    primary_key=is_primary_key,
                ),
            )

        _ = sa.Table(table_name, meta, *columns)
        meta.create_all(self._engine)


class Db2Sink(SQLSink):
    """IBM Db2 target sink class."""

    connector_class = DB2Connector

    def __init__(self, *args, **kwargs):
        """Initialize the Sink."""
        super().__init__(*args, **kwargs)
        self.load_table_name = self.generate_load_table_name()

    def generate_load_table_name(self):
        """generate a name for the loading table."""
        random_chars = "".join([choice(ascii_lowercase) for _ in range(5)])
        return "load_" + self.table_name + "_" + random_chars

    @property
    def full_load_table_name(self) -> str:
        """Return the fully qualified table name.

        Returns:
            The fully qualified table name.
        """
        return self.connector.get_fully_qualified_name(
            table_name=self.load_table_name,
            schema_name=self.schema_name,
            db_name=self.database_name,
        )

    def drop_load_table(self):
        drop_sql = sa.text(f"DROP TABLE {self.full_load_table_name}")
        with self.connector._connect() as conn, conn.begin():  # noqa: SLF001
            conn.execute(drop_sql)

    @property
    def object_and_array_columns(self):
        object_cols = [
            name
            for name, x in self.schema["properties"].items()
            if "object" == x["type"] or "object" in x["type"]
        ]
        array_cols = [
            name
            for name, x in self.schema["properties"].items()
            if "array" == x["type"] or "array" in x["type"]
        ]
        return object_cols + array_cols

    @staticmethod
    def deduplicate_records(records, key_properties):
        seen = set()
        deduplicated_records = []
        for rec in reversed(records):
            key = tuple([rec[k] for k in key_properties])
            if key not in seen:
                deduplicated_records.append(rec)
            seen.add(key)
        return list(reversed(deduplicated_records))

    def process_batch(self, context: dict) -> None:
        """Process a batch with the given batch context.

        Conforms array and object types and calls self.bulk_insert_records.
        This is necessary since IBM DB2 does not have native JSON types.

        Data is inserted into a loading table, and the final table is
        updated via an merge upsert statement. Then the loading table is dropped.

        If duplicates are present, the last record is kept.

        Args:
            context: Stream partition or context dictionary.
        """

        if self.key_properties:
            records = self.deduplicate_records(context["records"], self.key_properties)
        else:
            records = context["records"]
        for c in self.object_and_array_columns:
            for rec in records:
                if c in rec:
                    rec[c] = (
                        json.dumps(rec[c])
                        if isinstance(rec[c], (list, dict))
                        else rec[c]
                    )
        self.connector.prepare_table(
            self.full_load_table_name,
            schema=self.schema,
            primary_keys=self.key_properties,
            as_temp_table=False,
        )
        self.connector.prepare_table(
            self.full_table_name,
            schema=self.schema,
            primary_keys=self.key_properties,
            as_temp_table=False,
        )

        self.bulk_insert_records(
            full_table_name=self.full_load_table_name,
            schema=self.schema,
            records=records,
        )
        self.merge_upsert_from_table(
            from_table_name=self.full_load_table_name,
            target_table_name=self.full_table_name,
            join_keys=self.key_properties,
        )
        self.drop_load_table()

    def merge_upsert_from_table(
        self, target_table_name: str, from_table_name: str, join_keys: list[str]
    ) -> None:
        """Issue a MERGE statement to upsert data to the final table.

        Given the final table & load tables have 3 colummns: col1, col2 & col3
        where col1 is the join key, This method will issue the following MERGE statement.

            ```
            MERGE INTO final_tbl ft
            USING load_final_tbl_abc lt
            ON (ft.col1 = lt.col1)
            WHEN MATCHED THEN UPDATE
            SET
              col2 = lt.col2
            , col3 = lt.col3
            WHEN NOT MATCHED THEN
            INSERT (col1, col2, col3)
            VALUES (lt.col1, lt.col2, lt.col3);
            ```
        """
        join_exprs = [f'ft."{c}" = lt."{c}"' for c in join_keys]
        final_columns = [f'"{c}"' for c in self.schema["properties"].keys()]
        load_columns = [f"lt.{c}" for c in final_columns]
        update_exprs = [
            f'"{c}" = lt."{c}"'
            for c in self.schema["properties"].keys()
            if c not in join_keys
        ]
        merge_query = f"""
            MERGE INTO {target_table_name} ft
            USING {from_table_name} lt
            ON ({' AND '.join(join_exprs)})
            WHEN MATCHED THEN UPDATE
              SET {", ".join(update_exprs)}
            WHEN NOT MATCHED THEN
              INSERT ({', '.join(final_columns)})
              VALUES ({', '.join(load_columns)});
            """

        merge_stmt = sa.text(dedent(merge_query).strip())

        with self.connector._connect() as conn, conn.begin():
            conn.execute(merge_stmt)
