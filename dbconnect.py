import mysql.connector
from mysql.connector import Error
import pandas as pd


def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")


def execute_query_adr(connection, query, adr):
    cursor = connection.cursor()
    try:
        cursor.execute(query, adr)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")


def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")


def read_query_adr(connection, query, adr):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query, adr)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")


# connection = create_db_connection(
#    "database-1.cxksdtctbisg.us-east-1.rds.amazonaws.com", "admin", "London2022!!", "new_schema")

#df = read_query(connection, "SELECT * FROM Users")

# print(df)
