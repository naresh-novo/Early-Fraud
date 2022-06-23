###########
# Module for loading up the sql queries for pandas exploration.
# Usage:
# from config import SQLQuery
# query = SQLQuery('api')
# query(sql_query_string)
###########

import pandas as pd
# from sqlalchemy.dialects import registry
# registry.register('snowflake','sqlalchemy','dialects')
from sqlalchemy import create_engine

import yaml
from collections import namedtuple
from urllib.parse import quote
import os

_Connection = {
    'postgresql': namedtuple('_PostgtesqlConnection', 'type db host port user pw'),
    'snowflake': namedtuple('_SnowflakeConnection', 'type db schema wh host user pw role'),
}


def _load_DB_credentials(filename=None):
    DBs = {}
    DB_NAMES = []
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(filename or dir_path + '/' + 'config.yaml', "r") as f:
        try:
            databases = yaml.safe_load(f)['databases']
            for key, config in databases.items():
                DBs[key] = _Connection[config['type']](**config)
                DB_NAMES.append(key)
        except Exception as e:
            raise e
        return DBs, DB_NAMES


_DBs, _DB_NAMES = _load_DB_credentials()

def _get_engine(connection_name, DBs=_DBs):
    conn = _DBs.get(connection_name, None)
    if conn:
        if conn.type == "snowflake":
            return create_engine(f"{conn.type}://{conn.user}:{quote(conn.pw)}@{conn.host}/{conn.db}/{conn.schema}?warehouse={conn.wh}&role={conn.role}")
        if conn.type == "postgresql":
            return create_engine(f"{conn.type}://{conn.user}:{quote(conn.pw)}@{conn.host}:{conn.port}/{conn.db}")
        else:
            raise Exception(f"Unsupported database/ warehouse {conn.type}")
    else:
        raise NameError(f'DB "{connection_name}" does not exist')


class SQLQuery:
    """
    Class for running queries on specific datastores
    Usage: 
    query = SQLQuery('api')  # Use any datastore supported 
    output = query("SELECT * FROM ...")
    (To get list of datasoores SQLQuery.list_DBs())
    """

    def __init__(self, db_name):
        if db_name not in _DB_NAMES:
            print(f"Qnknown DB {db_name} please choose from {_DB_NAMES}")
            raise ValueError(f"DB name {db_name} not defined")
        self.engine = _get_engine(db_name)

    def __call__(self, query_string):
        return pd.read_sql(query_string, self.engine)

    @staticmethod
    def list_DBs():
        return _DB_NAMES

    def __str__(self):
        return str(self.engine)


# Test the module - Check if connections are working
if __name__ == '__main__':
    print(_DB_NAMES)
    test_dbs = _DB_NAMES
    # test_dbs = ['snowflake']
    for db in test_dbs:
        try:
            query = SQLQuery(db)
            if db != 'snowflake':
                print(query("SELECT * FROM information_schema.tables limit 1"), db)
            else:
                print(
                    query("SELECT * FROM fivetran_db.information_schema.tables limit 1;"), db)
        except Exception as e:
            print("Test Failed")
            print(e)
            raise