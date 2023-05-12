import sqlite3
from sqlite3 import Error

__all__ = ['create_database', 'create_table', 'connect_database', 'check_if_table_exist']


# create database
def create_database(db_file: str) -> None:
    """ create a database connection to a SQLite database
    :param db_file: database directory and name
    :return:
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f'created {db_file}!')
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
            print(f'database {db_file} closed!')


# create table
def create_table(conn: sqlite3.Connection, create_table_sql: str):
    """ create a table from the create_table_sql statement
    :param conn: sqlite3.Connection object
    :param create_table_sql: a CREATE TABLE sql statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


# create connection to the database
def connect_database(db_file: str) -> sqlite3.Connection:
    """ create a database connection to a SQLite database
    :rtype: object
    :param db_file: database url
    :return: sqlite3.Connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            return conn


def check_if_table_exist(conn: sqlite3.Connection, table_name: str) -> bool:
    """
    Check if table exist in database
    :param conn: database connection
    :param table_name: table_name
    :return: if table exist in database, return True, else return False.
    """
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name= '{table_name}';"
    _tables = \
        conn.cursor().execute(query).fetchall()
    return len(_tables) > 0
