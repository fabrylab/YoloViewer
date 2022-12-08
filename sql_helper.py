import sqlite3
import numpy as np
def connect(db_file):
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
columns = ['timestamp','frame','x','y','w','h','p','angle','long_axis','short_axis','radial_position','measured_velocity','cell_id',
                    'stress','strain','area','pressure','vel_fit_error','vel','vel_grad','eta','eta0','delta','tau','omega','Gp1','Gp2','k','alpha']
def create_table(db_file):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        sql_create_data_table = "CREATE TABLE IF NOT EXISTS data ("
        for var in columns:
            sql_create_data_table += f'{var} real,'
        sql_create_data_table += ' UNIQUE(timestamp,x,y,w,h,p))'
        print(sql_create_data_table)
        c.execute(sql_create_data_table)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def write_ellipses(db_file,entries):
    #entries (x,6)
    print('ENTRIES.SHAPE',entries.shape)
    try:
        conn = connect(db_file)
        c = conn.cursor()

        c.executemany("INSERT INTO data(x,y,w,h,p,frame,timestamp) VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING", entries)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def write_mechanical(db_file,df):
    sql_question_marks = ""
    sql_add_mechanical = "INSERT OR REPLACE INTO data("
    for var in columns:
        sql_add_mechanical += f'{var},'
        sql_question_marks += '?,'
    sql_add_mechanical = sql_add_mechanical[:-1] + ') VALUES (' + sql_question_marks[:-1] + ')'#ON CONFLICT DO REPLACE'#REPLACE'
    print(sql_add_mechanical)
    entries = df[columns].to_numpy()
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.executemany(sql_add_mechanical,entries)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def fetch_all(db_file):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM data")
        print(c.fetchall())
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def fetch_ellipses_larger_t0(db_file, t0):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.execute("SELECT timestamp,frame,x,y,w,h,p FROM data WHERE timestamp > (?);",(t0,))
        items = c.fetchall()
        conn.commit()
        conn.close()
        return items

    except sqlite3.Error as e:
        print(e)

def fetch_larger_t0(db_file, t0):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM data WHERE timestamp > (?);",(t0,))
        items = c.fetchall()
        conn.commit()
        conn.close()
        return items

    except sqlite3.Error as e:
        print(e)


def clear_db(db_file):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.execute("DROP TABLE data")
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

# NOT working, unknown reason
def fetch_larger_t0_json(db_file, t0):
    try:
        conn = connect(db_file)
        c = conn.cursor()
        c.execute("SELECT json_object(*) FROM data WHERE timestamp > (?);",(t0,))
        items = c.fetchall()
        conn.commit()
        conn.close()
        return items

    except sqlite3.Error as e:
        print(e)