from fastapi import Depends
from .connection import get_db_connection
from .query_runner import QueryRunner

def get_query_runner(connection = Depends(get_db_connection)):
    return QueryRunner(connection)