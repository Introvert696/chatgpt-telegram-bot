import sqlite3
import datetime

PATH_TO_DB = "log/log.db"


def createDb():
    try:
        connection = sqlite3.connect(PATH_TO_DB)
        cursor = connection.cursor()
        create_table_sql = '''
        create table if not exists log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            username TEXT,
            user_id INT,
            message TEXT NOT NULL,
            create_at datetime NOT NULL
        );
        '''
        cursor.execute(create_table_sql)
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as ex:
        return ex


def inlog(type, username, user_id, message):
    try:

        connection = sqlite3.connect(PATH_TO_DB)
        cursor = connection.cursor()
        insert_sql = '''
        Insert into log (type,username,user_id,message,create_at) values (?,?,?,?,?)
        '''
        cursor.execute(insert_sql, (type, username, user_id,
                       message, datetime.datetime.now()))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as ex:
        return ex
