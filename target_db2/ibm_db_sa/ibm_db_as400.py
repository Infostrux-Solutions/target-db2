from sqlalchemy import __version__ as SA_Version  # type:ignore[attr-defined]

SA_Version = [int(ver_token) for ver_token in SA_Version.split(".")[0:2]]
if SA_Version < [2, 0]:
    pass
else:
    pass
from ibm_db_sa.ibm_db import DB2Dialect_ibm_db
from ibm_db_sa.reflection import AS400Reflector


class AS400Dialect(DB2Dialect_ibm_db):
    _reflector_cls = AS400Reflector
