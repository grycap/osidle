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
from common import *
import math

def _reduce(d, func, init = 0):
    try:
        for k, v in d.items():
            init = func(init, v)
        return init
    except:
        for v in d:
            init = func(init, v)
        return init

# Calculate the basic stats of a serie of values with frequencies
# @param _data: series of rows of tuples where one of the columns is the amount of samples with the same value (set in other column); i.e. (samples, v1, v2, v3, ...)
# @param tpos: column of the amount of samples
# @param vpos: column of the value to calculate the stats
def basicstats(_data, tpos = 0, vpos = 1):
    values = [ (x[tpos], x[vpos]) for x in _data ]
    values.sort(key=lambda x: x[1])

    count = sum([ x[0] for x in values ])
    amount = sum([ x[0] * x[1] for x in values ])
    meanval = amount / count
    mpoint = count // 2
    mpos = 0

    for median_point in values:
        mpos += median_point[0]
        if mpos > mpoint:
            break

    deviation = math.sqrt(sum([ (x[1] - meanval)**2 for x in values ]) / (count - 1))

    if values[-1][1] == values[0][1]:
        pct_deviation = 0
    else:
        pct_deviation = deviation / (values[-1][1] - values[0][1])

    return {
        "min": values[0][1],
        "max": values[-1][1],
        "mean": meanval,
        "deviation": deviation,
        "pct_deviation": pct_deviation,
        "median": median_point[1],
    }

# Function analyzes the percentages of appearance of the values in a dataset, in each of a set of fragments of the possible space of values
#  The idea is to get a dataset that contains values within a certain range of values, then identify a range of possible values and to divide
#  such range in N fragments. Then count the number of times that the values of the dataset fall into each fragment.
#
#  e.g.: have the usage of CPU in each second of a period. The values are between 0 and 100. The range is 0-100% and if we wanted 4 fragments, we'll
#        have 4 fragments of 0-25%, 25-50%, 50-75% and 75-100% of the range. Then we'll analyze each value of the dataset and count how many times
#        it falls into each fragment. Finally, we'll divide per the total amount, to get the percentage of times of appearance of the values in each 
#        fragment.
#
# - The function is made somehow general, so that we could also cluster values in the dataset (e.g. (5 times, value 10), (8 times, value 20), etc.);
#   moreover the number of fragments can be set as parameter.
# - The range is provided as a parameter, and if values get out of this range, they will be absorbed by the borders of the range.
#
# @param data: dataset to analyze (an array of tuples, where there is an element that contains the values and the amount of times that the value appears)
# @param tpos: the column used to the times that a value is repeated (if None, each value will be counted as 1 time)
# @param vpos: the column used to the value to analyze

def _fragments(_data, tpos = None, vpos = 0, low = None, up = None, nfragments = 4):
    if len(_data) == 0:
        return None

    if tpos is None:
        serie = [ (1, x[vpos]) for x in _data ]
    else:
        serie = [ (x[tpos], x[vpos]) for x in _data ]

    if up is None:
        up = max([ x[1] for x in serie ])
    if low is None:
        low = min([ x[1] for x in serie ])

    w = (up - low) / nfragments
    total = 0
    fragments = [0] * nfragments
    for t, v in serie:
        p = int((v - low) // w)

        # Make the borders to absorve the values
        if p < 0: p = 0
        if p >= nfragments: p = nfragments - 1
        total += t
        fragments[p] += t

    result = [ t/total for t in fragments ]
    return result

def _evaluate_fragment(fragment, minval = 0, maxval = 10):
    # Calculate the points according to the position in the deciles os quartiles
    #   > in quartiles will have 4 pct of usage in 0-25%, 25-50%, 50-75% and 75-100%; 
    result = 0
    max_p = len(fragment)
    for p in range(0, max_p):
        result += p * fragment[p]
    result = round(maxval * result / (max_p - 1), 2)
    return result

class DataSeries:
    def __init__(self, rawdata, args):
        self._params = {
            "threshold_disk": args.threshold_disk,
            "threshold_nic": args.threshold_nic,
            "level": args.level,
        }

        # Now convert the data into a format ready to be analyzed (frequency, cpu (seconds/second), disk (bytes/second), nic(bytes/second))
        #   TODO(N): consider dividing the x["tcpu"] per ncpus to get the "for analysis" cpu time
        #       ANSWER: NO, because we want to be able to show the data; the "for analysis" cpu time is an internal value
        _data = rawdata.data
        self._data_series = [ (x["e"], x["tcpu"]/x["e"], x["tdisk"]/x["e"], x["tnic"]/x["e"]) for x in _data ]
        self._vminfo = {
            "ncpu": rawdata.ncpu,
            "nnic": rawdata.nnic,
            "ndisk": rawdata.ndisk,
        }

        self._stats = None 
        self._evaluation = None

    @property
    def stats(self):
        if self._stats is None:
            self._stats = self._calculate_stats()
        return self._stats

    @property
    def evaluation(self):
        if self._evaluation is None:
            self._evaluation = self._evaluate_stats(self.stats)
        return self._evaluation


    def _evaluate_stats(self, stats):
        if self._params["level"] == "medium":
            ncpu = self._vminfo["ncpu"] / 2
            diskdata = stats["disk"]["median"]
            nicdata = stats["nic"]["median"]
            cpudata = stats["cpu"]["median"]
        elif self._params["level"] == "strict":
            ncpu = self._vminfo["ncpu"]
            diskdata = stats["disk"]["min"]
            nicdata = stats["nic"]["min"]
            cpudata = stats["cpu"]["min"]
        else:
            ncpu = 1
            diskdata = stats["disk"]["mean"]
            nicdata = stats["nic"]["mean"]
            cpudata = stats["cpu"]["mean"]

        # Calculate the decile distribution for each value
        decile = { 
            "cpu": _fragments(self._data_series, 0, 1, 0, ncpu, 10),
            "disk": _fragments(self._data_series, 0, 2, 0, self._params["threshold_disk"], 10),
            "nic": _fragments(self._data_series, 0, 3, 0, self._params["threshold_nic"], 10),
        }

        evaluation = {
            "disk": {
                "score": _evaluate_fragment(decile["disk"]),
                "data": decile["disk"],
                "score2": round(min(10 * diskdata / self._params["threshold_disk"], 10), 2),
                "data2": diskdata
            },
            "nic": {
                "score": _evaluate_fragment(decile["nic"]),
                "data": decile["nic"],
                "score2": round(min(10 * nicdata / self._params["threshold_nic"], 10), 2),
                "data2": nicdata
            },
            "cpu": {
                "score": _evaluate_fragment(decile["cpu"]),
                "data": decile["cpu"],
                "score2": round(min(10 * cpudata / ncpu, 10), 2),
                "data2": cpudata
            }
        }
        return evaluation
            
    # This function obtains some stats for the data sample
    def _calculate_stats(self):
        # Get the stats
        result = {
            "cpu": basicstats(self._data_series, tpos = 0, vpos = 1),
            "disk": basicstats(self._data_series, tpos = 0, vpos = 2),
            "nic": basicstats(self._data_series, tpos = 0, vpos = 3),
        }
        return result
