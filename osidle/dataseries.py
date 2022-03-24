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
from .common import *
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
    if count == 0:
        return None

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

# DEPRECATED:
# This method converts a series that has a repetition of values into a series that has a different repetition of values, by making the value proportional to the new repetition rate;
#   Column "t" is the repetition amount and the total amount for such repetition is in column "c"; the idea is to make the series continuous and to make the new distribution of values
#   i.e. ((40,100), (30, 90), (50, 200)) can be converted into ((30,75), (30, 25+60), (30, ...) ...)
def _cluster(serie, t, c, tsize, skip=0):
    n_serie = []
    p_e = 0
    p_disk_e = 0

    for row in serie:
        e = row[t]
        disk = row[c]
        disk_e = disk / e

        # Calculate the amount for the first block (if there are remaining values to clusterize)
        if p_e != 0:

            # No esta bien calculado: el nuevo e es tsize o p_e + e como maximo: es p_e + max(e - p_e, tsize - p_e) )

            n_e = min(e - p_e, tsize - p_e)
            n_disk = disk_e * n_e + p_disk_e * p_e
            n_serie.append((n_e + p_e, n_disk))
            e = e - n_e

        # Now the central amount
        n = int(e // tsize)
        n_serie.extend([(tsize, disk_e * tsize)] * n)

        # Calculate the rest
        p_e = e - n * tsize
        p_disk_e = disk_e

    if p_e > 0:
        n_serie.append((p_e, p_disk_e * p_e))

    return n_serie

# The idea of this function is to make a filter to the data, so that if a timestep the value saturates (i.e. gets upper to a threshold), the value is set to the threshold
#   and the remaining amount is added to the next timestep, so that the value is not lost. But the amount added is not the whole amount; instead, it is minored by the
#   an epsilon value.
# The underlying use case is the following:
#   - a VM downloads 10 Gb in just 1 minute, but this is because of the network (either the local endpoint or the remote endpoint)
#   - the same VM may have been downloaded the same amount of data in 1 hour, because the network was slower.
#   - both VMs have been used. If the threshold was 8Kbps, both VMs pass the threshold but the first has a lower score because it was downloading less time.
# Using this filter, the evaluation mechanism tries to be more fair. If the epsilon is too big, the big transferences will be overrated while the small ones will be underrated.
#   * At the end, this is a subjective matter, bucause the actual fact is that the first VM has used the network less time than the second one. So the second VM has been "used"
#     more time than the first one.
def _filter_saturation(serie, t, c, threshold, eps = 0.5):
    for c_s in range(0, len(serie)):
        e = serie[c_s][t]
        disk = serie[c_s][c]

        if disk > threshold:
            diff_disk = disk - threshold
            if (c_s < (len(serie) - 1)):
                e_next = serie[c_s + 1][t]
                n_val = ((serie[c_s + 1][c] * e_next) + (diff_disk * e * eps)) / e_next
                serie[c_s + 1][c] = n_val
            serie[c_s][c] = threshold

def _evaluate_fragment(fragment, minval = 0, maxval = 10):
    # Calculate the points according to the position in the deciles os quartiles
    #   > in quartiles will have 4 pct of usage in 0-25%, 25-50%, 50-75% and 75-100%; 
    if fragment is None:
        return None

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
        self._data_series = [ [x["e"], x["tcpu"]/x["e"], x["tdisk"]/x["e"], x["tnic"]/x["e"]] for x in _data ]
        # n_data_series = _cluster(self._data_series, 0, 2, 60)
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
        eps = 0.75
        if self._params["level"] == "medium":
            eps = 0.75
            ncpu = max(math.ceil(stats["cpu"]["max"]) if stats["cpu"] is not None else 1, 1)
            diskdata = stats["disk"]["median"] if stats["disk"] is not None else None
            nicdata = stats["nic"]["median"] if stats["nic"] is not None else None
            cpudata = stats["cpu"]["median"] if stats["cpu"] is not None else None
        elif self._params["level"] == "hard":
            eps = 0.25
            ncpu = self._vminfo["ncpu"]
            diskdata = stats["disk"]["min"] if stats["disk"] is not None else None
            nicdata = stats["nic"]["min"] if stats["nic"] is not None else None
            cpudata = stats["cpu"]["min"] if stats["cpu"] is not None else None
        elif self._params["level"] == "softer":
            eps = 0.85
            ncpu = 1
            diskdata = stats["disk"]["min"] if stats["disk"] is not None else None
            nicdata = stats["nic"]["min"] if stats["nic"] is not None else None
            cpudata = stats["cpu"]["min"] if stats["cpu"] is not None else None
        else:
            eps = 0.85
            ncpu = 1
            diskdata = stats["disk"]["mean"] if stats["disk"] is not None else None
            nicdata = stats["nic"]["mean"] if stats["nic"] is not None else None
            cpudata = stats["cpu"]["mean"] if stats["cpu"] is not None else None

        # Now we'll filter the disk information and the network to mitigate the impact of saturation
        _filter_saturation(self._data_series, 0, 2, self._params["threshold_disk"], eps)
        _filter_saturation(self._data_series, 0, 3, self._params["threshold_nic"], eps)

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
                "score2": round(min(10 * diskdata / self._params["threshold_disk"], 10), 2) if diskdata is not None else None,
                "data2": diskdata
            },
            "nic": {
                "score": _evaluate_fragment(decile["nic"]),
                "data": decile["nic"],
                "score2": round(min(10 * nicdata / self._params["threshold_nic"], 10), 2) if nicdata is not None else None,
                "data2": nicdata
            },
            "cpu": {
                "score": _evaluate_fragment(decile["cpu"]),
                "data": decile["cpu"],
                "score2": round(min(10 * cpudata / ncpu, 10), 2) if cpudata is not None else None,
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
