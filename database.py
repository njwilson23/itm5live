import atexit
import os
import math
import urllib.parse
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
    if f == "date":
        return v.isoformat()
    if math.isnan(v):
        return None
    else:
        return v

def extract(fields, retfields=None):
    """ given a list of field (*fields*), return an iterator of dictionaries
    containing rows from the db """
    if retfields is None:
        retfields = fields
    else:
        if len(retfields) != len(fields):
            raise ValueError("return field names and table field names must be"
                             " equal length")
    cur = CONN.cursor()

    cur.execute("SELECT " + ",".join(fields) + " FROM itm5;")
    result = cur.fetchall()
    return [{f_:fmt(f, v) for f,f_,v in zip(fields, retfields, record)}
            for record in result]

def update(header, rows):
    """ given a list of fields (*header*) and a list of lists of data (*rows*),
    update database with all rows more recent than the last db entry.
    """
    cur = CONN.cursor()
    cur.execute("SELECT * FROM itm5 ORDER BY date;")
    if cur.rowcount != 0:
        cur.scroll(cur.rowcount-1)
        result = cur.fetchone()
    else:
        result = None

    if result is not None:
        last_date = result[2]
        new_rows = [row for row in rows if row[0] > last_date]
    else:
        new_rows = rows

    LOG.info("adding %d new rows" % len(new_rows))
    if len(new_rows) == 0:
        return

    try:
        expr = ("INSERT INTO itm5 "
                "("+ ",".join(colname_munger(n) for n in header) +")"
                " VALUES (" + ",".join(["%s" for _ in range(len(header))]) + ");")
        cur.executemany(expr, new_rows)
        CONN.commit()

    except Exception as e:
        CONN.rollback();
        traceback.print_exc(e)
    finally:
        cur.close()

