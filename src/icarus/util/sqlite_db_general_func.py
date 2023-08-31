import sqlite3
from sqlite3 import Error
import pandas as pd
import os
import numpy as np


__all__ = ['create_database', 'create_table', 'connect_database', 'check_if_database_exit', 'check_if_table_exist',
           'add_dataframe_to_database', 'create_table_with_columns', 'infer_sql_data_types']


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


def check_if_database_exit(db_file: str) -> bool:
    """
    Check if database exist
    :param db_file: url to database file
    :return: if database exit, return True, else return False.
    """
    if not os.path.exists(r'D:\icarus_test\data1.db'):
        return False
    else:
        return True


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


def add_dataframe_to_database(conn: sqlite3.Connection, data_frame: pd.DataFrame, table_name: str, primary_keys: list) -> None:
    """
    add dataframe to database as a table
    :param primary_keys:
    :param table_name: table name
    :param conn: database connection
    :param data_frame: dataframe
    :return: None
    """
    if not check_if_table_exist(conn, table_name):
        column_dict = infer_sql_data_types(data_frame)
        create_table_with_columns(conn, table_name, column_dict, primary_keys)
    data_frame.to_sql(table_name, conn, if_exists='append', index=False)


def create_table_with_columns(conn: sqlite3.Connection, table_name: str, column_dict: dict, primary_keys: list) -> None:
    """
    create a table in database with the columns' information
    :param conn: database connection
    :param table_name: name of database table
    :param column_dict: columns dictionary
    :param primary_keys: primary keys used to source data
    :return: None
    """
    columns = ', '.join([f'{col} {col_type}' for col, col_type in column_dict.items()])
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns}, PRIMARY KEY ({', '.join(primary_keys)}))"
    conn.execute(query)
    conn.commit()


# get the dataframe column name and datatype.
def infer_sql_data_types(data_frame: pd.DataFrame) -> str:
    """
    Infer datatype for dataframe columns.
    :param data_frame: dataframe which will be saved in database
    :return: string value of column name and data type.
    """
    sql_data_types = {}

    for column_name, column_data in data_frame.iteritems():
        if column_data.dtype == np.int64:
            sql_data_types[column_name] = 'INTEGER'
        elif column_data.dtype == np.float64:
            sql_data_types[column_name] = 'REAL'
        elif column_data.dtype == np.object:
            # For string data, you might want to use VARCHAR or TEXT
            max_length = column_data.str.len().max()
            if max_length <= 255:
                sql_data_types[column_name] = f'VARCHAR({max_length})'
            else:
                sql_data_types[column_name] = 'TEXT'
        elif column_data.dtype == np.datetime64:
            sql_data_types[column_name] = 'DATETIME'
        else:
            # Default to TEXT for other cases
            sql_data_types[column_name] = 'TEXT'

    return sql_data_types
