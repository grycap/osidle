#!/usr/bin/env python3
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
import sys
from common import *
from storage import Storage
import json
from rawdata import RawData
from dataseries import DataSeries


def correctArguments(args, beginTime, endTime):
    # Convert the thresholds to bytes
    args.threshold_disk = toBytes(args.threshold_disk)
    if args.threshold_disk is None:
        p_error("invalid expression for disk threshold")
        sys.exit(1)

    args.threshold_nic = toBytes(args.threshold_nic)
    if args.threshold_nic is None:
        p_error("invalid expression for disk threshold")
        sys.exit(1)

    if args.fromdate is not None:
        args.fromdate = toDate(args.fromdate, beginTime, endTime)
        p_debugv("fromdate: ", args.fromdate)
        if args.fromdate is None:
            p_error("invalid expression for fromdate")
            sys.exit(1)

    if args.todate is not None:
        args.todate = toDate(args.todate, beginTime, endTime)
        p_debugv("todate: ", args.todate)
        if args.todate is None:
            p_error("invalid expression for todate")
            sys.exit(1)

    return args

if __name__ == "__main__":
    from uuid import UUID
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-W", "--custom-file", dest="customoptions", default=None, help="file with custom options for specific vm IDs", type=str)
    parser.add_argument("-F", "--from", dest="fromdate", type=str, default="begin", help="make the analysis from this date. Valid expressions are [<reference>-]<count>[suffix], where reference is a choice between the keywords 'now', 'begin', 'end', 'lastweek'... (if ommited, will be set to 'now'), and <suffix> may be a choice between 's', 'm', 'h', 'd', 'w', 'M' and 'y'. Default: 'begin' (i.e. beggining of the data)")
    parser.add_argument("-T", "--to", dest="todate", help="make the analysis up to this date. The format is the same than '--from' parameter. Default: 'end' (i.e. the last timestamp avaliable)", type=str, default="end")
    parser.add_argument("-d", "--database", dest="database", help="database to use", default="monitoring.sqlite3")
    parser.add_argument("-C", "--no-cpu", dest="analysis_cpu", help="do not consider CPU usage for the analysis", action="store_false", default=True)
    parser.add_argument("-D", "--no-disk", dest="analysis_disk", help="do not consider DISK usage for the analysis", action="store_false", default=True)
    parser.add_argument("-N", "--no-network", dest="analysis_nic", help="do not consider NETWORK usage for the analysis", action="store_false", default=True)
    parser.add_argument("--threshold-disk", dest="threshold_disk", help="threshold for the disk usage (in units/second); accepts suffix B, K, M, G (default is Bytes)", type=str, default="4K")
    parser.add_argument("--threshold-nic", dest="threshold_nic", help="threshold for the nic usage (in units/second); accepts suffix B, K, M, G (default is Bytes)", type=str, default="4K")
    parser.add_argument("-f", "--format", dest="format", help="output format", choices = ["json", "csv", "excel"], default="json")
    parser.add_argument("-p", "--pretty", dest="pretty", help="pretty print the output", action="store_true", default=False)
    parser.add_argument("-l", "--level", dest="level", help="level of detail severity for the analysis", choices = ["strict", "medium", "loose"], default="loose")
    parser.add_argument("-S", "--summarize", dest="summarize", help="summarize the usage for the VMs", action="store_true", default=False)
    parser.add_argument("-U", "--under-threshold", dest="threshold_summarize", help="summary will show only VMs under this threshold of puntuation (from 0 to 10)", type=int, default=3)
    parser.add_argument("-o", "--sort", dest="sort", help="Sort the output descending by estimated usage of the VM", action="store_true", default=False)
    parser.add_argument("-i", "--vm-id", dest="vmids", action="append", help="id of the VMs to be analyzed (can appear multiple times)", type=str)
    parser.add_argument("-v", "--verbose", dest="verbose", help="verbose", action="store_true", default=False)
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", help="verbose more", action="store_true", default=False)
    parser.add_argument("--include-eval-data", dest="include_eval_data", action="store_true", default=False, help="include data used for evaluation")
    parser.add_argument("--include-stats", dest="include_stats", help="include the stats in the output", action="store_true", default=False)
    parser.add_argument("--dump-data", dest="dumpdata", action="store_true", default=False, help="dump the data that would be used for the analysis and finalizes")
    parser.add_argument("--info", dest="info", action="store_true", default=False, help="get the information about the data available and exit")
    parser.add_argument("--vmlist", dest="vmlist", action="store_true", default=False, help="if getting information, dump the list of available VMs")

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        sys.exit(1)
    except SystemExit as e:
        p_error(e)
        sys.exit(1)

    if args.verbose:
        setVerbose(1)
    if args.verbosemore:
        setVerbose(2)

    # Connect to the database (if possible)
    storage = Storage(args.database)
    storage.connect()

    # Get the begin and end time of the data
    beginTime = storage.getmint()
    endTime = storage.getmaxt()

    # Correct the arguments using the keywords and special values
    args = correctArguments(args, beginTime, endTime)

    # Get information
    if args.info:
        print("Information about the data available:")
        print("  - first entry:", beginTime)
        print("  - last entry:", endTime)
        print("  - available vms:", len(storage.getvms()))
        if args.vmlist:
            print("  - available vm ids:", "\n      ".join(["", *storage.getvms()]))
        sys.exit(0)

    # Now the default options for each of the specific VM is the options passed in the commandline
    parser.set_defaults(**args.__dict__)

    # Store the default args
    defaultargs = args

    # Custom options for the specific VMs
    customoptions = {}

    if args.customoptions is not None:
        with open(args.customoptions, "r") as f:
            optionsvms = [ l.split("#")[0].strip().split(":") for l in f.readlines() ]
            for options in optionsvms:
                if len(options) == 1 or len(options) == 2:
                    uuid = options[0]
                    try:
                        UUID(uuid)
                        validuuid = True
                    except ValueError:
                        p_warning("invalid uuid {}".format(uuid))

                    if validuuid:
                        if len(options) == 1:
                            # This may be a special case to deactivate the analysis
                            customoptions[uuid] = {}
                        else:
                            customargs, errorargs = parser.parse_known_args(options[1].split())
                            customargs = correctArguments(customargs, beginTime, endTime)

                            if len(errorargs) > 0:
                                p_warning("invalid custom options for {}".format(uuid))

                            customoptions[uuid] = customargs

    # Now get the VM ids to deal with
    if args.vmids is not None:
        vms = args.vmids
    else:
        vms = storage.getvms()

    # Obtain the stats for the different VMs
    rawdata = {}
    for vm in vms:
        p_debug("reading entries for vm {}".format(vm))
        vmdata = storage.getvmdata(vm, args.fromdate, args.todate)
        p_debug("{} entries found".format(len(vmdata)))

        if len(vmdata) == 0:
            continue

        rawdata[vm] = RawData(vmdata, args)

    # If only wanted to get the data, dump it an finalize
    if args.dumpdata:
        for vm, data in rawdata.items():
            print(data.dumpdata(args.format, args.pretty, transform_fnc=lambda x: (vm, *x)))
        sys.exit(0)

    # Now prepare the results for the analysis
    if args.format == 'json':
        result = {}
    else:
        result = []

    f_stats = []
    f_evaluation = []
    f_data = []
    h_data = []
    h_stats = []
    h_evaluation = [ "ID", "Overall" ]

    # Depending on what we want to get from the analysis, we prepare the different headers and the data
    if args.analysis_cpu:
        f_stats = [ *f_stats, "stats.cpu.min", "stats.cpu.max", "stats.cpu.mean", "stats.cpu.median" ]
        h_stats = [ *h_stats, "CPU min", "CPU max", "CPU mean", "CPU median" ]
        f_evaluation = [ *f_evaluation, "cpu.score" ]
        h_evaluation = [ *h_evaluation, "P. CPU" ]
        f_data = [ *f_data, "cpu.data" ]
        h_data = [ *h_data, "cpu 0-10", "cpu 10-20", "cpu 20-30", "cpu 30-40", "cpu 40-50", "cpu 50-60", "cpu 60-70", "cpu 70-80", "cpu 80-90", "cpu 90-100" ]
    if args.analysis_disk:
        f_stats = [ *f_stats, "stats.disk.min", "stats.disk.max", "stats.disk.mean", "stats.disk.median" ]
        h_stats = [ *h_stats, "Disk min", "Disk max", "Disk mean", "Disk median" ]
        f_evaluation = [ *f_evaluation, "disk.score" ]
        h_evaluation = [ *h_evaluation, "P. disk" ]
        f_data = [ *f_data, "disk.data" ]
        h_data = [ *h_data, "disk 0-10", "disk 10-20", "disk 20-30", "disk 30-40", "disk 40-50", "disk 50-60", "disk 60-70", "disk 70-80", "disk 80-90", "disk 90-100" ]
    if args.analysis_nic:
        f_stats = [ *f_stats, "stats.nic.min", "stats.nic.max", "stats.nic.mean", "stats.nic.median" ]
        h_stats = [ *h_stats, "NIC min", "NIC max", "NIC mean", "NIC median" ]
        f_evaluation = [ *f_evaluation, "nic.score" ]
        h_evaluation = [ *h_evaluation, "P. score" ]
        f_data = [ *f_data, "nic.data" ]
        h_data = [ *h_data, "nic 0-10", "nic 10-20", "nic 20-30", "nic 30-40", "nic 40-50", "nic 50-60", "nic 60-70", "nic 70-80", "nic 80-90", "nic 90-100" ]

    # Now get the analysis
    for vm, data in rawdata.items():
        p_debug("evaluating data for vm {}".format(vm))
        _stats = DataSeries(data, args)

        stats = _stats.stats
        evaluation = _stats.evaluation

        total = 0
        total_n = 0

        # Calculate the overall score from the evaluation
        # TODO: check whether to use the 2nd value or not (this is more strict)
        if args.analysis_cpu:
            total += evaluation["cpu"]["score"]
            total_n += 1
        if args.analysis_nic:
            total += evaluation["nic"]["score"]
            total_n += 1
        if args.analysis_disk:
            total += evaluation["disk"]["score"]
            total_n += 1
        
        overall = round(total / max(1, total_n), 2)

        # If wanted to dump the stats, add them to the evaluation
        if args.include_stats:
            evaluation["stats"] = stats

        # Depending on the format, retrieve the data
        if args.format == "json":
            evaluation["overall"] = overall

            if not args.include_eval_data:
                del evaluation["cpu"]["data"]
                del evaluation["disk"]["data"]
                del evaluation["nic"]["data"]
                del evaluation["cpu"]["data2"]
                del evaluation["disk"]["data2"]
                del evaluation["nic"]["data2"]

            result[vm] = evaluation
        else:
            evaluation["cpu"]["data"] = [ "" if x == 0 else x for x in evaluation["cpu"]["data"] ]
            evaluation["disk"]["data"] = [ "" if x == 0 else x for x in evaluation["disk"]["data"] ]
            evaluation["nic"]["data"] = [ "" if x == 0 else x for x in evaluation["nic"]["data"] ]

            result.append(
                (vm, overall, *get_fields(evaluation, f_evaluation), *get_fields(evaluation, f_data), *get_fields(evaluation, f_stats))
            )

    # Finally, dump the data, depending on the format (moreover we'll sort it and summarize the data, depending on the options)
    if args.format == "json":
        if args.summarize:
            result = { k:v for k,v in result.items() if v["overall"] < args.threshold_summarize }

        result = sorted(result.items(), key=lambda x: x[1]["overall"], reverse=True)
        if args.pretty:
            print(json.dumps(result, indent=4))
        else:
            print(json.dumps(result))
    else:
        if args.summarize:
            result = [ x for x in result if x[1] < args.threshold_summarize ]

        if args.sort:
            result = sorted(result, key=lambda x: x[1], reverse=True)

        headers = [ *h_evaluation ]
        if args.include_eval_data:
            headers = [ *headers, *h_data ]
        if args.include_stats:
            headers = [ *headers, *h_stats ]

        if args.format == "excel":
            print(";".join(headers))
            print("\n".join( [ ";".join([str(x).replace(".", ",") for x in y]) for y in result ]))
        else:
            print(",".join(headers))
            print("\n".join( [ ",".join([str(x) for x in y]) for y in result ]))