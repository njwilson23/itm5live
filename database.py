""" Functions for extracting and updating PostGres tables """

import atexit
import os
import math
import urllib.parse
import traceback
import psycopg2

if "DATABASE_URL" in os.environ:
    urllib.parse.uses_netloc.append("postgres")
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

    CONN = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
else:
    dbname = "itm5db"
    user="natw"
    host=os.environ.get("DATABASE_URL", "/var/run/postgresql")
    CONN = psycopg2.connect("dbname=%s user=%s host=%s" % (dbname, user, host))

atexit.register(CONN.close)

def fmt(f, v):
    if f.startswith("date"):
        return v.isoformat()
    try:
        if math.isnan(float(v)):
            return None
    except TypeError:
        return v
    return v

def extract(table, fields, retfields=None):
    """ given a list of field (*fields*), return an iterator of dictionaries
    containing rows from the db """
    if retfields is None:
        retfields = fields
    else:
        if len(retfields) != len(fields):
            raise ValueError("return field names and table field names must be"
                             " equal length")
    cur = CONN.cursor()

    cur.execute("SELECT " + ",".join(fields) + " FROM " + table + " ORDER BY date;")
    result = cur.fetchall()
    retdict = {k:[] for k in retfields}
    for record in result:
        for f, rf, v in zip(fields, retfields, record):
            retdict[rf].append(fmt(f, v))
    return retdict

def update_column(tablename, data, dates, colname, log=None):
    """ given a list of dates and a column of data, update database """
    cur = CONN.cursor()

    expr = ("INSERT INTO {1} (date, {0}) VALUES (%s, %s) "
            "ON CONFLICT (date) "
            "DO UPDATE SET {0}=%s "
            "WHERE {1}.date=%s".format(colname, tablename))

    try:
        cur.executemany(expr, list(zip(dates, data, data, dates)))
        CONN.commit()
    except Exception as e:
        CONN.rollback()
        if log is not None:
            log.error(colname, e)
        else:
            print("error:", colname, e)
    finally:
        cur.close()
    return

def colname_munger(name):
    return name.replace("itm5micro", "mc").replace("itm5adop", "ad").replace("_", "")

