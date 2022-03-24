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
import copy
from datetime import datetime, timedelta
import json

from osidle.common import p_warning

class RawData:
    def __init__(self, data, args):
        _data = RawData._convert(data)
        # TODO: discard the first sample as it is just the historic data?
        _data = _data[1:]
        self._data = RawData._get(_data, args.fromdate, args.todate)
        self._ncpu = None
        self._nnic = None
        self._ndisk = None

        if len(self._data) > 0:
            self._ncpu = self._data[0]["ncpu"]
            self._nnic = self._data[0]["nnic"]
            self._ndisk = self._data[0]["ndisk"]

    @property
    def ncpu(self):
        return self._ncpu

    @property
    def nnic(self):
        return self._nnic

    @property
    def ndisk(self):
        return self._ndisk
        
    def __str__(self):
        return self.dumpdata("json", True)

    def dumpdata(self, format, pretty = False, transform_fnc = None):
        if format == "csv" or format == "excel":
            lines = []
            for d in self._data:
                v = (d["T"], d["S"], d["e"], 
                    d["tcpu"], d["tdisk"], d["tnic"],
                    *d["cpu"], *[ v for x in d["disk"] for v in [ x["r"], x["w"] ] ] , # The CPUs
                    *[ v for x in d["nic"] for v in [ x["rx"], x["tx"] ] ]) # The NICs  
                if callable(transform_fnc):
                    v = transform_fnc(v)
                lines.append(v)

            if format == "csv":
                separador=","
                return "\n".join([ separador.join([str(v) for v in x ]) for x in lines ])
            else:
                separador = ";"
                return "\n".join([ separador.join([str(v).replace(".", ",") for v in x ]) for x in lines ])
        else:
            if pretty:
                return json.dumps(self._data, indent=4)
            else:
                return json.dumps(self._data)

    @property
    def data(self):
        return self._data

    @staticmethod
    def _get(data, fromDate = None, toDate = None):
        t_fromDate = fromDate.timestamp()
        t_toDate = toDate.timestamp()
        if (t_fromDate > t_toDate):
            return []

        _data = []
        for d in data:
            time_after_begin = max(0, t_fromDate - d["S"])
            time_before_end = max(0, d["S"] + d["e"] - t_toDate)
            e = d["e"] - time_after_begin - time_before_end

            if e == d["e"]:
                _data.append(d)
            else:
                # Duplicate d and update the data
                d = copy.deepcopy(d)
                fraction = e / d["e"]
                d["cpu"] = [ x * fraction for x in d["cpu"] ]
                d["disk"] = [ { "r": x["r"] * fraction, "w": x["w"] * fraction } for x in d["disk"] ]
                d["nic"] = [ { "rx": x["rx"] * fraction, "tx": x["tx"] * fraction } for x in d["nic"] ]
                d["S"] = d["S"] + time_after_begin
                d["e"] = e
                d["T"] = datetime.fromtimestamp(d["S"]).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                d["tcpu"] = d["tcpu"] * fraction
                d["tdisk"] = d["tdisk"] * fraction
                d["tnic"] = d["tnic"] * fraction
                _data.append(d)

        return _data

    # This function gets a data series and converts it to an incremental data series. It assumes that each of the samples in the input
    # data series is an absolute sample and so it converts it to an incremental data series by subtracting the previous sample from the
    # current one.
    # Returns a set of samples with the following data:
    #   - t: the timestamp where the sample was taken; 
    #   - s: t in seconds
    #   - T: the tiemstamp where the sample starts; 
    #   - S: T in seconds
    #   - e: the usage of the resources correspond to this continuous number of seconds
    #   - cpu, nic, disk: the usage of the CPU, NIC and DISK
    #   - ncpu, nnic, ndis: number of CPUs, NICs and DISKs
    #   - tcpu, tnic, tdisk: the aggregated amount of nanoseconds of CPU used, NIC tx and rx and DISK r and w
    @staticmethod
    def _convert(data):
        converted = []
        d0 = None

        for d in data:
            # Skip the samples that do not have information
            if "conflictingRequest" in d:
                continue
            if "itemNotFound" in d:
                continue

            d["tcpu"] = sum(x["time"] for x in d["cpu_details"]) * 1e-9
            d["tdisk"] = sum([ x["read_bytes"] + x["write_bytes"] for x in d["disk_details"] ])
            d["tnic"] = sum([ x["rx_octets"] + x["tx_octets"] for x in d["nic_details"] ])

            # If it is the first sample, we'll use it as the base but we need to convert it to a "pseudo-incremental" sample that
            # starts the series with values set to 0. It is needed to adjust the timestamp
            if d0 is None:
                # Clone d to create the fake first sample
                d0 = copy.deepcopy(d)

                # t is the timestamp of the sample (when it was obtained)
                t = datetime.strptime(d["t"], "%Y-%m-%dT%H:%M:%S.%fZ") - timedelta(seconds=d["uptime"])
                d0["t"] = t.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                # T is the timestamp where the sample starts (when the consumption of resources started)
                d0["T"] = d["t"]
                # e is the difference between the previous timestamp and this one
                d0["e"] = 0,
                # s is the timestamp (t) in seconds
                d0["s"] = t.timestamp() # d0["s"] - d0["uptime"]
                # S is the timestamp (s) in seconds
                d0["S"] = d0["s"]
                # Now clear the resource consumption as this is a "base sample" (e.g.) the VM was just started
                d0["uptime"] = 0
                for c in d0["cpu_details"]:
                    c['time'] = 0
                for x in d0["disk_details"]:
                    x['read_bytes'] = 0
                    x['write_bytes'] = 0
                for n in d0["nic_details"]:
                    n['rx_octets'] = 0
                    n['tx_octets'] = 0
                d0["tcpu"] = 0
                d0["tdisk"] = 0
                d0["tnic"] = 0

            # Calculate the current incremental sample by subtracting the previous sample from the current one (also conver cpu from nanoseconds to seconds)
            d1 = {
                "t": d['t'],
                "s": d['s'],
                "ncpu": len(d['cpu_details']),
                "ndisk": len(d['disk_details']),
                "nnic": len(d['nic_details']),
                "tcpu": sum(x["time"] for x in d["cpu_details"]) * 1e-9,
                "tdisk": sum([ x["read_bytes"] + x["write_bytes"] for x in d["disk_details"] ]),
                "tnic": sum([ x["rx_octets"] + x["tx_octets"] for x in d["nic_details"] ]),
            }
            # TODO: what to do with resized instances (either the number of CPUs or the number of NICs or the number of DISKs)

            if d0["tcpu"] > d1["tcpu"] or d0["tdisk"] > d1["tdisk"] or d0["tnic"] > d1["tnic"]:
                # The VM has been stopped and started again later; will not subtract the previous sample from the current one

                # We'll skip the sample, because we do not know the time from the previous sample: the requests between this and the previous one
                #   are conflicting and we cannot calculate the incremental consumption.

                # TODO: When a VM is stopped and started later, the amount of CPU is reset to 0...
                #   the same happens to disk and nic, but not the uptime. 
                p_warning("Skipping sample with negative number of CPUs, disks or NICs (the VM was probably shut down)")
            else:
                d1["tcpu"] = d1["tcpu"] - d0["tcpu"]
                d1["tdisk"] = d1["tdisk"] - d0["tdisk"]
                d1["tnic"] = d1["tnic"] - d0["tnic"]

                # TODO: now we have to calculate the values of T, S and e both for d and for d1
                # So we have to calculate the elapsed time, which is the difference between the timestamp of the previous sample and the current one
                d1["e"] = d["s"] - d0["s"]
                d1["S"] = d["s"] - d1["e"]
                d1["T"] = datetime.fromtimestamp(d1["S"]).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                # d1["tcpu"] = sum(d1["cpu"])
                # d1["tdisk"] = sum([ x for n in d1["disk"] for x in [n["r"], n["w"]]])
                # d1["tnic"] = sum([ x for n in d1["nic"] for x in [n["rx"], n["tx"]]])

                # Add the incremental sample to the result
                converted.append(d1)

            # Store the sample to be the reference for the previous one
            d0 = d

        return converted
