#
#    Copyright 2022 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import sqlite3
import json
from .common import p_error, p_warning, p_debugv, p_debug, p_info
from datetime import datetime, timedelta

DEFAULT_FILENAME = "monitoring.sqlite3"

def _sql(cursor, query, params = ()):
    p_debugv("{}: {}".format(query,params))
    result = cursor.execute(query, params)
    return result

class Storage:
    def __init__(self, filename = None):
        if filename is None:
            filename = DEFAULT_FILENAME
        self._filename = filename
        self._conn = None

    def connect(self):
        conn = None
        try:
            conn = sqlite3.connect(self._filename)
        except Exception as e:
            p_error("Could not connect to database: {}".format(e))
            conn = None

        if conn is not None:
            self._conn = conn
            self._createDB()
    
    def _createDB(self):
        cursor = self._conn.cursor()
        cursor.execute("create table if not exists \
            vmmonitor (\
                id integer PRIMARY KEY AUTOINCREMENT, \
                t datetime DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'NOW')), \
                vmid varchar(36) NOT NULL,\
                data text\
            )")
        self._conn.commit()

    def isConnected(self):
        return self._conn is not None

    def getmaxt(self):
        if not self.isConnected():
            return None

        cursor = self._conn.cursor()
        cursor.execute("select t from vmmonitor order by t desc limit 1")
        try:
            return datetime.strptime(cursor.fetchone()[0], "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception as e:
            # Just in case the DB is not initialized
            return None

    # Obtains the min available timestamp (i.e. the first time that the system was started)
    def getmint(self):
        if not self.isConnected():
            return None

        cursor = self._conn.cursor()
        cursor.execute("select t from vmmonitor order by t asc limit 1")
        try:
            return datetime.strptime(cursor.fetchone()[0], "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception as e:
            # Just in case the DB is not initialized
            return None

    def savevm(self, vmid, info):
        if not self.isConnected():
            return False

        cursor = self._conn.cursor()
        cursor.execute("insert into vmmonitor (vmid, data) values (?, ?)", (vmid, json.dumps(info)))
        self._conn.commit()
        return True

    def getvmdata(self, vmid, fromDate = None, toDate = None):
        if not self.isConnected():
            return []

        cursor = self._conn.cursor()

        if (fromDate is None) and (toDate is None):
            _sql(cursor, "select t, data from vmmonitor where vmid = ? order by t asc", (vmid,))
            # cursor.execute("select t, data from vmmonitor where vmid = ? order by t asc", (vmid,))
        elif (fromDate is None):
            fromDate = fromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select t, data from vmmonitor where vmid = ? and t >= ? order by t asc", (vmid, fromDate))
        elif (toDate is None):
            toDate = toDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select t, data from vmmonitor where vmid = ? and t <= ? order by t asc", (vmid, toDate))
        else:
            fromDate = fromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            toDate = toDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select t, data from vmmonitor where vmid = ? and t >= ? and t <= ? order by t asc", (vmid, fromDate, toDate))
            
        # TODO: filter the data and return the objects in the right format
        result = []
        for (t, data) in cursor.fetchall():
            data = json.loads(data)
            data["t"] = t
            data["s"] = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            result.append(data)
        
        return result
        # return [ {"t": datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ"), "i": json.loads(data)} for (t, data) in cursor.fetchall() ]

    def getvms(self, fromDate = None, toDate = None):
        if not self.isConnected():
            return []

        cursor = self._conn.cursor()
        # cursor.execute("select vmid from vmmonitor group by vmid")

        if (fromDate is None) and (toDate is None):
            _sql(cursor, "select vmid from vmmonitor group by vmid")
            # cursor.execute("select t, data from vmmonitor where vmid = ? order by t asc", (vmid,))
        elif (fromDate is None):
            fromDate = fromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select vmid from vmmonitor group by vmid where t >= ?", (fromDate))
        elif (toDate is None):
            toDate = toDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select vmid from vmmonitor group by vmid where t <= ?", (toDate))
        else:
            fromDate = fromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            toDate = toDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "select vmid from vmmonitor group by vmid where t >= ? and t <= ?", (fromDate, toDate))

        return [ x for (x,) in cursor ]

    def delete(self, keepFromDate, keepToDate):
        if not self.isConnected():
            return False

        cursor = self._conn.cursor()

        if (keepFromDate is None) and (keepToDate is None):
            raise Exception("refusing to wipe the whole database")
        elif (keepFromDate is None):
            keepToDate = keepToDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "delete from vmmonitor where t > ?", (keepToDate,))
        elif (keepToDate is None):
            keepFromDate = keepFromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "delete from vmmonitor where t < ?", (keepFromDate,))
        else:
            keepFromDate = keepFromDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            keepToDate = keepToDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            _sql(cursor, "delete from vmmonitor where t < ? or t > ?", (keepFromDate, keepToDate))

        self._conn.commit()
        return cursor.rowcount

    def vaccuum(self):
        if not self.isConnected():
            return False

        cursor = self._conn.cursor()
        _sql(cursor, "vacuum")
        self._conn.commit()
        return True

    def filterdata(self, filter_fnc, pre_fnc = None, post_fnc = None):
        if not self.isConnected():
            return False

        cursor1 = self._conn.cursor()

        _sql(cursor1, "select count(*) from vmmonitor")
        count = cursor1.fetchone()[0]

        if (callable(pre_fnc)):
            pre_fnc(count)

        cursor2 = self._conn.cursor()
        _sql(cursor1, "select id, vmid, t, data from vmmonitor")
        for (id, vmid, t, data) in cursor1:
            data = json.loads(data)
            data = filter_fnc(vmid, t, data)
            if data is not None:
                cursor2.execute("update vmmonitor set data = ? where id = ?", (json.dumps(data), id))

        self._conn.commit()

        if (callable(post_fnc)):
            post_fnc()

        return True

def remove_unneeded_data(data):
    if 'conflictingRequest' in data:
        return data
    if 'itemNotFound' in data:
        return data
        
    return {
        "cpu_details": [ { "time": x["time"] } for x in data["cpu_details"] ],
        "disk_details": [ { "read_bytes": x["read_bytes"],  "write_bytes": x["write_bytes"]} for x in data["disk_details"] ],
        "nic_details": [ { "mac_address": x["mac_address"], "rx_octets": x["rx_octets"], "tx_octets": x["tx_octets"] } for x in data["nic_details"] ],
        "num_cpus": data["num_cpus"],
        "num_disks": data["num_disks"],
        "num_nics": data["num_nics"],
        "uptime": data["uptime"],
        "state": data["state"],
    }
