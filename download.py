import datetime
import itertools
import math
import os
import statistics
import sys
import urllib.request
import zipfile

import logging

import database

URL = "ftp://ftp.whoi.edu/whoinet/itpdata/itm5data.zip"

# Set up logging
LOG = logging.getLogger("download")
_handler = logging.FileHandler("download.log")
_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_handler.setFormatter(_formatter)
LOG.addHandler(_handler)


LOG.setLevel(logging.WARNING)

def getdatafromWHOI():
    DATA = {}

    try:
        res = urllib.request.urlretrieve(URL)
    except Exception as e:
        # log failure
        LOG.error(e)
        return None
    try:
        zf = zipfile.ZipFile(res[0])

        for name in zf.namelist():
            with zf.open(name) as f:
                DATA[name] = f.read()

    finally:
        os.remove(res[0])
    LOG.info("data retrieved from {0}".format(URL))
    return DATA

def dat2rows(d):
    s = d.decode("utf-8")
    if "aquadopp" in s[:20]:
        fields = ["year", "day", "pressure", "temperature", "east", "north", "up"]
    elif "microcat" in s[:20]:
        fields = ["year", "day", "temperature", "salinity", "pressure"]
    elif "longitude" in s[:30]:
        return None
    else:
        raise IOError("unknown header: '{0}'".format(s[:20]))
    data = s.split("\n", 2)[2]
    lines = data.split("\n")
    rows = [fields]
    for line in lines[2:]:
        if (len(line) != 0) and (line[0] != "%"):
            rows.append(line.split())
    return rows

def parse_year_day(year, day):
    return datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=day-1)

def rows_aggregate_hourly(rows):
    """ create hourly aggregates and insert "date" column into position 2 """
    aggfields = [f for f in rows[0]]
    aggfields.insert(2, "date")
    aggrows = [aggfields]

    year = int(rows[1][0])
    day = float(rows[1][1])
    prevdate = parse_year_day(year, day)
    iprev = 1
    i = 2
    while i != len(rows):
        year = int(rows[i][0])
        day = float(rows[i][1])
        date = parse_year_day(year, day)
        if i == iprev:
            # reset prevdate after forming aggregate
            prevdate = date
        elif (date.hour != prevdate.hour) or (i == len(rows)-1):
            # aggregate from iprev to i inclusive
            newrow = []
            for j in range(len(rows[i])):
                newrow.append(statistics.mean([float(rows[_i][j]) for _i in range(iprev, i+1)]))
            newrow.insert(2, datetime.datetime(year, prevdate.month, prevdate.day,
                                               prevdate.hour, 0, 0,
                                               tzinfo=datetime.timezone.utc))
            aggrows.append(newrow)
            iprev = i+1
        i += 1
    return aggrows

def merge_rows(rowdict):
    dates = [r[2] for r in itertools.chain(*(rows[1:] for rows in rowdict.values()))]
    dates = list(set(dates))
    dates.sort()

    mergedfields = ["date"]
    mergedrows = [[d] for d in dates]

    for prefix, rows in rowdict.items():

        for j, name in enumerate(rows[0]):
            if name not in ("year", "day", "date"):
                mergedfields.append(prefix + name)

                idx_ptr = 0
                row_ptr = 1
                while idx_ptr != len(dates):
                    if row_ptr == len(rows):
                        mergedrows[idx_ptr].append(math.nan)
                        idx_ptr += 1
                    elif dates[idx_ptr] == rows[row_ptr][2]:
                        mergedrows[idx_ptr].append(rows[row_ptr][j])
                        idx_ptr += 1
                        row_ptr += 1
                    elif dates[idx_ptr] > rows[row_ptr][2]:
                        row_ptr += 1
                    else:
                        mergedrows[idx_ptr].append(math.nan)
                        idx_ptr += 1
    return mergedfields, mergedrows

def savetocsv(d, dirname="static/data"):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    for name in d:
        LOG.info("parsing {0}".format(name))
        try:
            rows = dat2rows(d[name])
            if rows is None:
                LOG.warn("no data returned from {0}".format(name))
            else:
                csvname = name.replace(".dat", ".csv")
                with open(os.path.join(dirname, csvname), "w") as f:
                    f.write("\n".join([",".join(r) for r in rows]))
        except Exception as e:
            LOG.error(e)
    return

if __name__ == "__main__":

    LOG.setLevel(logging.DEBUG)

    # emit logs to stdout when in debug mode
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    _handler.setFormatter(_formatter)
    LOG.addHandler(_handler)

    d = getdatafromWHOI()
    if d is None:
        LOG.error("no data recieved")
        sys.exit(1)

    # make a local copy of data
    savetocsv(d)

    # update database
    r = {}
    r_agg = {}
    for name in d:
        r[name] = dat2rows(d[name])
        if r[name] is not None:
            r_agg[name.replace(".dat", "_")] = rows_aggregate_hourly(r[name])

    header, data = merge_rows(r_agg)
    database.update(header, data, log=LOG)
