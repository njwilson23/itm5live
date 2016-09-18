import os
import urllib.request
import json
import zipfile
import logging

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

def dat2csv(d):
    """ returns a json object with variable names as keys and vectors of
    variables as values """
    s = d.decode("utf-8")
    if "aquadopp" in s[:20]:
        fields = ["year", "day", "pressure", "temperature", "east", "north", "up"]
    elif "microcat" in s[:20]:
        fields = ["year", "day", "temperature", "salinity", "pressure"]
    else:
        raise IOError("unknown header: '{0}'".format(s[:20]))
    data = s.split("\n", 2)[2]
    lines = data.split("\n")
    csvrows = [",".join(fields)]
    for line in lines[2:]:
        csvrows.append(",".join(line.split()))
    return csvrows

def savetocsv(d, dirname="static/data"):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    for name in d:
        LOG.info("parsing {0}".format(name))
        try:
            csvrows = dat2csv(d[name])
            csvname = name.replace(".dat", ".csv")
            with open(os.path.join(dirname, csvname), "w") as f:
                f.write("\n".join(csvrows))
        except Exception as e:
            LOG.error(e)
    return

def dat2json(d):
    """ returns a json object with variable names as keys and vectors of
    variables as values """
    s = d.decode("utf-8")
    lines = s.split("\n")
    header = lines[1]
    fields = header.split()
    data = [[] for field in fields]
    for line in lines[2:]:
        for i, val in enumerate(line.split()):
            data[i].append(val)
    datadict = {field:records for field, records in zip(fields, data)}
    return json.dumps(datadict)


def savetojson(d, dirname="static/data"):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    for name in d:
        LOG.info("parsing {0}".format(name))
        try:
            j = dat2json(d[name])
            jsonname = name.replace(".dat", ".json")
            with open(os.path.join(dirname, jsonname), "w") as f:
                f.write(j)
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
    if d is not None:
        savetocsv(d)
    else:
        print("error")
