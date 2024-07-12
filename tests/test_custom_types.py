import pytest
import sqlalchemy as sa
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    select,
)

from target_db2.connector import JSONVARCHAR

creds = {
    "user": "db2inst1",
    "password": "pass1",
    "host": "localhost",
    "port": "50000",
    "database": "testdb",
}

varchar_length = 10000
TEST_SCHEMA = "test_custom_types"
db2_connection_string = "ibm_db_sa://{user}:{password}@{host}:{port}/{database}".format(
    **creds
)

metadata = MetaData()
test_table = Table(
    "test",
    metadata,
    Column("pk", Integer, primary_key=True, autoincrement=True),
    Column("col1", String(varchar_length)),
    Column("col2", Integer),
)


@pytest.fixture()
def db():
    engine = create_engine(db2_connection_string)
    with engine.connect() as conn, conn.begin():
        if not conn.dialect.has_schema(conn, TEST_SCHEMA):
            conn.execute(sa.schema.CreateSchema(TEST_SCHEMA))
    yield engine
    custom_types_metadata = MetaData(schema=TEST_SCHEMA)
    custom_types_metadata.reflect(engine)
    print(dir(custom_types_metadata))


def test_column_objectvarchar(db):
    """Test that python objects are properly serialized and deserialized by sqlalchemy.

    Ensure that inserts work & returned records are converted back to python objects
    """
    test_metadata = MetaData(schema=TEST_SCHEMA)
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
    test_metadata.create_all(db)
    with db.connect() as conn, conn.begin():
        conn.execute(insert(test_table), records)

    with db.connect() as conn, conn.begin():
        test_records = conn.execute(select(test_table)).all()

    # test insert success
    assert len(test_records) == len(records)

    # test json attribute access
    assert sum(rec.jsondata["hello"] for rec in test_records) == records_hello_sum

    with db.connect() as conn, conn.begin():
        conn.execute(sa.schema.DropTable(test_table))
