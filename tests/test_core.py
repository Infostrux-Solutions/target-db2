"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import typing as t

import pytest
from singer_sdk.testing import get_target_test_class
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    Table,
    create_engine,
    insert,
    select,
)
from sqlalchemy.schema import DropTable

from target_db2.connector import JSONVARCHAR
from target_db2.target import TargetDb2

if t.TYPE_CHECKING:
    from sqlalchemy.engine.base import Engine


SAMPLE_CONFIG: dict[str, t.Any] = {
    "host": "localhost",
    "port": 50000,
    "user": "db2inst1",
    "password": "pass1",
    "database": "testdb",
    "default_target_schema": "DB2INST1",
}
db2_connection_string = (
    "ibm_db_sa://{user}:{password}@{host}:{port}/{database}:PROTOCOL=TCPIP;".format(
        **SAMPLE_CONFIG
    )
)


@pytest.fixture()
def db2() -> Engine:
    """Create a sqlalchemy engine to interact with Db2."""
    return create_engine(db2_connection_string)


def test_column_objectvarchar(db2: Engine) -> None:
    """Test that python objects are properly serialized and deserialized by sqlalchemy.

    Ensure that inserts work & returned records are converted back to python objects
    """
    test_metadata = MetaData()
    tablename = "test_column_jsonvarchar"
    test_table = Table(
        tablename,
        test_metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("jsondata", JSONVARCHAR(1000)),
    )
    records = [
        {"jsondata": {"hello": 0}},
        {"jsondata": {"hello": 1}},
        {"jsondata": {"hello": 2}},
        {"jsondata": {"hello": 3}},
        {"jsondata": {"hello": 4}},
        {"jsondata": {"hello": 5}},
        {"jsondata": {"hello": 6}},
        {"jsondata": {"hello": 7}},
        {"jsondata": {"hello": 8}},
        {"jsondata": {"hello": 9}},
    ]
    records_hello_sum = 45
    test_metadata.create_all(db2)
    with db2.connect() as conn, conn.begin():
        conn.execute(insert(test_table), records)

    with db2.connect() as conn, conn.begin():
        test_records = conn.execute(select(test_table)).all()  # type: ignore[arg-type]

    # test insert success
    assert len(test_records) == len(records)

    # test json attribute access
    assert sum(rec.jsondata["hello"] for rec in test_records) == records_hello_sum

    with db2.connect() as conn, conn.begin():
        conn.execute(DropTable(test_table))  # type: ignore[arg-type]


# Run standard built-in target tests from the SDK:
StandardTargetTests = get_target_test_class(
    target_class=TargetDb2,
    config=SAMPLE_CONFIG,
)


class TestTargetDb2(StandardTargetTests):  # type: ignore[misc, valid-type]
    """Standard Target Tests."""
