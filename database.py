""" Functions for extracting and updating PostGres tables """
import os
import math
import urllib.parse
import psycopg2

def with_connection(func):
    """ decorator that injects a postgres connection as first argument to its function
    and returns a wrapped function without the first argument """
    def wrapped(*args, **kwargs):
        if "DATABASE_URL" in os.environ:
            conn = psycopg2.connect(database=URL.path[1:],
                                    user=URL.username,
                                    password=URL.password,
                                    host=URL.hostname,
                                    port=URL.port)
        else:
            dbname = "itm5db"
            user="natw"
            host=os.environ.get("DATABASE_URL", "/var/run/postgresql")
            conn = psycopg2.connect("dbname=%s user=%s host=%s" % (dbname, user, host))
        try:
            ret = func(conn, *args, **kwargs)
        except Exception as exc:
            conn.rollback()
            raise exc
        finally:
            conn.close()
        return ret
    return wrapped

if "DATABASE_URL" in os.environ:
    urllib.parse.uses_netloc.append("postgres")
    URL = urllib.parse.urlparse(os.environ["DATABASE_URL"])

def fmt(f, v):
    if f.startswith("date"):
        return v.isoformat()
    try:
        if math.isnan(float(v)):
            return None
    except TypeError:
        return v
    return v

@with_connection
def extract(conn, table, fields, retfields=None):
    """ given a list of fields (*fields*), return a dictionary containing
    columns from the db """
    if retfields is None:
        retfields = fields
    else:
        if len(retfields) != len(fields):
            raise ValueError("return field names and table field names must be"
                             " equal length")

    cur = conn.cursor()
    cur.execute("SELECT " + ",".join(fields) + " FROM " + table + " ORDER BY date;")
    result = cur.fetchall()
    retdict = {k:[] for k in retfields}
    for record in result:
        for f, rf, v in zip(fields, retfields, record):
            retdict[rf].append(fmt(f, v))
    return retdict

@with_connection
def update_column(conn, tablename, data, dates, colname, log=None):
    """ given a list of dates and a column of data, update database """
    expr = ("INSERT INTO {1} (date, {0}) VALUES (%s, %s) "
            "ON CONFLICT (date) "
            "DO UPDATE SET {0}=%s "
            "WHERE {1}.date=%s".format(colname, tablename))

    cur = conn.cursor()
    try:
        cur.executemany(expr, list(zip(dates, data, data, dates)))
        conn.commit()
    except Exception as e:
        conn.rollback()
        if log is not None:
            log.error(colname, e)
        else:
            print("error:", colname, e)
    finally:
        cur.close()
    return

def colname_munger(name):
    return name.replace("itm5micro", "mc").replace("itm5adop", "ad").replace("_", "")

