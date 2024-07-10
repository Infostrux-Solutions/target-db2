from singer_sdk.sinks import SQLSink

from target_db2.connector import DB2Connector


class Db2Sink(SQLSink):
    """IBM Db2 target sink class."""

    connector_class = DB2Connector
