import unittest
import math
import datetime
import download
import database

class TestDownload(unittest.TestCase):

    def test_year_day(self):
        d = download.parse_year_day(2015, 1.5)
        self.assertEqual(d.year, 2015)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 1)
        self.assertEqual(d.hour, 12)

        d = download.parse_year_day(2016, 243+1.0/6)
        self.assertEqual(d.year, 2016)
        self.assertEqual(d.month, 8)
        self.assertEqual(d.day, 30)
        self.assertEqual(d.hour, 4)

    def test_table_merge(self):
        table1 = [("year", "day", "date", "d"),
                  (2016, 100, datetime.datetime(2016, 3, 4, 10, 0, 0), 1),
                  (2016, 101, datetime.datetime(2016, 3, 5, 10, 0, 0), 1),
                  (2016, 102, datetime.datetime(2016, 3, 6, 10, 0, 0), 1),
                  (2016, 104, datetime.datetime(2016, 3, 8, 10, 0, 0), 1)]
        table2 = [("year", "day", "date", "d"),
                  (2016, 100, datetime.datetime(2016, 3, 4, 10, 0, 0), 2),
                  (2016, 101, datetime.datetime(2016, 3, 5, 10, 0, 0), 2),
                  (2016, 102, datetime.datetime(2016, 3, 6, 10, 0, 0), 2),
                  (2016, 103, datetime.datetime(2016, 3, 7, 10, 0, 0), 2),
                  (2016, 104, datetime.datetime(2016, 3, 8, 10, 0, 0), 2)]
        table3 = [("year", "day", "date", "d"),
                  (2016, 101, datetime.datetime(2016, 3, 5, 10, 0, 0), 3),
                  (2016, 102, datetime.datetime(2016, 3, 6, 10, 0, 0), 3),
                  (2016, 103, datetime.datetime(2016, 3, 7, 10, 0, 0), 3),
                  (2016, 104, datetime.datetime(2016, 3, 8, 10, 0, 0), 3)]
        tmerge = download.merge_rows({"t1": table1, "t2": table2, "t3":table3})
        self.assertEqual(len(tmerge[1]), 5)
        self.assertTrue(math.isnan(tmerge[1][0][tmerge[0].index("t3d")]))
        self.assertTrue(math.isnan(tmerge[1][3][tmerge[0].index("t1d")]))
        return

    def test_aggregate(self):
        data = [("year", "day", "d1", "d2")]
        for i in range(1000):
            data.append(("2016", str(123+float(i)/96), i, 2*i))
        aggdata = download.rows_aggregate_hourly(data)
        self.assertEqual(aggdata[0][2], "date")
        self.assertEqual(len(aggdata), 251)
        return

    def test_aggregate_daily(self):
        # check for new year bug
        data = [("year", "day", "d1", "d2")]
        for i in range(600):
            if 362+float(i)/96 < 367:
                data.append(("2016", str(362+float(i)/96), i, 2*i))
            else:
                data.append(("2017", str(362+float(i)/96-366), i, 2*i))
        aggdata = download.rows_aggregate_daily(data)
        self.assertEqual(max(a[2] for a in aggdata[1:]),
                         datetime.datetime(2017, 1, 2, 0, 0, tzinfo=datetime.timezone.utc))
        #self.assertEqual(aggdata[0][2], "date")
        #self.assertEqual(len(aggdata), 251)
        return

class TestDatabase(unittest.TestCase):

    def test_extract(self):
        d = database.extract("itm5", ["date", "mc1salinity", "ad2up"])
        self.assertTrue("date" in d)
        self.assertTrue("mc1salinity" in d)
        self.assertTrue("ad2up" in d)
        self.assertTrue(isinstance(d.get("date", None), list))
        self.assertTrue(isinstance(d.get("mc1salinity", None), list))
        self.assertTrue(isinstance(d.get("ad2up", None), list))
        return

    def test_extract_custom_retfields(self):
        d = database.extract("itm5", ["date", "mc1salinity", "ad2up"],
                             retfields=["time", "salinity", "upvel"])
        self.assertTrue("time" in d)
        self.assertTrue("salinity" in d)
        self.assertTrue("upvel" in d)
        self.assertTrue(isinstance(d.get("time", None), list))
        self.assertTrue(isinstance(d.get("salinity", None), list))
        self.assertTrue(isinstance(d.get("upvel", None), list))
        return

if __name__ == "__main__":
    unittest.main()
