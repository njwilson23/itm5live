""" Provides functions for pulling data from the WHOI server, constructing
tables, and computing aggregates """

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
    """ Download data from the WHOI server, decompress, and return a dictionary
    where keys are filenames and values are streams of text """
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
    """ Take a stream of text read from a file and return a list of lists
    containing the row-wise data. """
    s = d.decode("utf-8")
    if "aquadopp" in s[:20]:
        fields = ["year", "day", "pressure", "temperature", "east", "north", "up"]
    elif "microcat" in s[:20]:
        fields = ["year", "day", "temperature", "salinity", "pressure"]
    elif "longitude" in s[:30]:
        fields = ["year", "day", "longitude", "latitude", "GF", "NSAT", "HDOP"]
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
    """ convert a year and day number to a date """
    jan1 = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc)
    return jan1 + datetime.timedelta(days=day-1)

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
            newrow = [prevdate.year, day]
            newrow.append(datetime.datetime(prevdate.year, prevdate.month,
                                            prevdate.day, prevdate.hour, 0, 0,
                                            tzinfo=datetime.timezone.utc))
            for j in range(2, len(rows[i])):
                newrow.append(statistics.mean([float(rows[_i][j])
                                               for _i in range(iprev, i+1)]))
            aggrows.append(newrow)
            iprev = i+1
        i += 1
    return aggrows

def rows_aggregate_daily(rows):
    """ create daily aggregates and insert "date" column into position 2 """
    # create header
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
        elif (date.day != prevdate.day) or (i == len(rows)-1):
            # aggregate from iprev to i inclusive
            newrow = [prevdate.year, day]
            newrow.append(datetime.datetime(prevdate.year,
                                            prevdate.month,
                                            prevdate.day,
                                            0, 0, 0,
                                            tzinfo=datetime.timezone.utc))
            for j in range(2, len(rows[i])):
                newrow.append(statistics.mean([float(rows[_i][j])
                                               for _i in range(iprev, i+1)]))
            aggrows.append(newrow)
            iprev = i+1
        i += 1
    return aggrows

def merge_rows(rowdict):

    """ given a dictionary that maps filenames to lists of file rows, return a
    list of merged column names and a list of lists representing merged file
    contents

    That is, starting with

    {fnm1: [header1, row1_0, row1_1, row1_2...],
     fnm2: [header2, row2_0, row2_1, row2_2...],
     ...}

     return

     [fnm1_header1a, fnm1_header1b, ...
      fnm2_header1a, fnm2_header2b, ...
      ...]

     and

     [[row1_0a, row1_0b, ...
       row2_0a, row2_0b, ...],
      [row1_1a, row1_1b, ...
       row2_1a, row2_1b, ...],
      [row1_2a, row1_2b, ...
       row2_2a, row2_2b, ...], ...]
    """

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

def split_columns(rows):
    """ given a list of lists where the first list is column names, return a
    dictionary where keys are column names and values are data
    """
    names = rows[0]
    data = rows[1:]
    columns = {}
    for i, name in enumerate(names):
        columns[name] = [d[i] for d in data]
    return columns

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
        if name == "itm5rawlocs.dat":
            r_agg["positions"] = rows_aggregate_daily(r[name])
        elif r[name] is not None:
            r_agg[name.replace(".dat", "_")] = rows_aggregate_hourly(r[name])

    for name, rows in r_agg.items():
        if name == "positions":
            columns = split_columns(rows)
            for colname, data in columns.items():
                if colname in ("longitude", "latitude"):
                    LOG.info("updating {0}".format(colname))
                    database.update_column("geo_itm5", data, columns["date"], colname, log=LOG)
        else:
            prefix = database.colname_munger(name)
            columns = split_columns(rows)
            for colname, data in columns.items():
                if colname in ("temperature", "salinity", "pressure", "up", "east", "north"):
                    LOG.info("updating {0}".format(prefix+colname))
                    database.update_column("itm5", data, columns["date"], prefix+colname, log=LOG)

