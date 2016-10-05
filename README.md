# README

## Introduction

This is the code responsible for the ITM5LIVE dashboard at [itm5live.herokuapp.com](itm5live.herokuapp.com). It's not particularly good.

## Deployment

Set up Postgres tables on heroku

```bash
heroku pg:psql
```

Make the following tables

```sql
CREATE TABLE itm5 (
    year integer,
    day real,
    date timestamptz UNIQUE,
    mc1temperature real,
    mc1salinity real,
    mc1pressure real,
    mc2temperature real,
    mc2salinity real,
    mc2pressure real,
    mc3temperature real,
    mc3salinity real,
    mc3pressure real,
    mc4temperature real,
    mc4salinity real,
    mc4pressure real,
    ad1pressure real,
    ad1temperature real,
    ad1east real,
    ad1north real,
    ad1up real,
    ad2pressure real,
    ad2temperature real,
    ad2east real,
    ad2north real,
    ad2up real,
    ad3pressure real,
    ad3temperature real,
    ad3east real,
    ad3north real,
    ad3up real,
    ad4pressure real,
    ad4temperature real,
    ad4east real,
    ad4north real,
    ad4up real
    );

CREATE TABLE geo_itm5 (
    year integer,
    day real,
    date timestamptz UNIQUE,
    longitude real,
    latitude real
);
```

Push ITM5LIVE app to Heroku

```bash
git push heroku master
```

Log into Heroku and run the download script to initialize database with a fresh copy of data from the WHOI server

```bash
heroku run bash
python download.py
exit
```
