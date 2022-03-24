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
import sys
from .common import *
from .storage import Storage
import json
from .rawdata import RawData
from .dataseries import DataSeries
from .version import VERSION
from uuid import UUID
from tqdm import tqdm
import argparse
import os
import xlsxwriter
import math

def dataset_to_barchart(data, lower = None, upper = None):

    if data is None:
        return ""

    barchart_graphics = [
        '\u2581',
        '\u2582',
        '\u2583',
        '\u2584',
        '\u2585',
        '\u2586',
        '\u2587',
        '\u2588',
    ]
    if upper is None:
        upper = max(data)
    if lower is None:
        lower = min(data)
    if lower == upper:
        return barchart_graphics[0] * len(data)

    res = ""
    for d in data:
        v = (d - lower) / (upper - lower)
        p = round(v * (len(barchart_graphics) - 1))
        if p < 0:
            p = 0
        if p >= len(barchart_graphics):
            p = len(barchart_graphics) - 1
        res = res + barchart_graphics[p]
    return res

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

class OutputFile:
    def __init__(self, fname, overwrite = False) -> None:
        self._closed = False
        if (fname is None) or (fname == "-"):
            self.f = sys.stdout
        else:
            # If file exists abort
            if not overwrite and os.path.isfile(fname):
                raise Exception("file '{}' already exists".format(fname))
            try:
                self.f = open(fname, "w")
            except:
                raise Exception("error opening file '{}'".format(fname))
    def print(self, data):
        if self._closed:
            raise Exception("file already closed")
        self.f.write(data)
    def println(self, data):
        self.print(data + "\n")
    def close(self):
        if self._closed:
            raise Exception("file already closed")
        self._close = True
        self.f.close()

def osidle_analysis():
    parser = argparse.ArgumentParser(allow_abbrev=False)

    parser.add_argument("-q", "--quiet", action="store_true" , help="use the quiet mode (suppress any output except from the resulting analysis, either from the file or stdout)", default=False, dest="quiet")
    parser.add_argument("-r", "--remove-unknown", action="store_true" , help="remove VMs without valid data in the interval", default=False, dest="removeunknown")
    parser.add_argument("-O", "--output", dest="outputfile", default="-", help="output to this file (default: stdout)", type=str)
    parser.add_argument("--overwrite", dest="overwrite", action="store_true", help="overwrite output file if already exists")
    parser.add_argument("-W", "--custom-file", dest="customoptions", default=None, help="file with custom options for specific vm IDs", type=str)
    parser.add_argument("-F", "--from", dest="fromdate", type=str, default="begin", help="make the analysis from this date. Valid expressions are [<reference>-]<count>[suffix], where reference is a choice between the keywords 'now', 'begin', 'end', 'lastweek'... (if ommited, will be set to 'now'), and <suffix> may be a choice between 's', 'm', 'h', 'd', 'w', 'M' and 'y'. Default: 'begin' (i.e. beggining of the data)")
    parser.add_argument("-T", "--to", dest="todate", help="make the analysis up to this date. The format is the same than '--from' parameter. Default: 'now'", type=str, default="now")
    parser.add_argument("-d", "--database", dest="database", help="database to use", default="/var/lib/osidled/osidled.db")
    parser.add_argument("-C", "--no-cpu", dest="analysis_cpu", help="do not consider CPU usage for the analysis", action="store_false", default=True)
    parser.add_argument("-D", "--no-disk", dest="analysis_disk", help="do not consider DISK usage for the analysis", action="store_false", default=True)
    parser.add_argument("-N", "--no-network", dest="analysis_nic", help="do not consider NETWORK usage for the analysis", action="store_false", default=True)
    parser.add_argument("--threshold-disk", dest="threshold_disk", help="threshold for the disk usage (in units/second); accepts suffix B, K, M, G (default is Bytes)", type=str, default="4K")
    parser.add_argument("--threshold-nic", dest="threshold_nic", help="threshold for the nic usage (in units/second); accepts suffix B, K, M, G (default is Bytes)", type=str, default="4K")
    parser.add_argument("-f", "--format", dest="format", help="output format", choices = ["json", "csv", "excel", "shell"], default="json")
    parser.add_argument("-p", "--pretty", dest="pretty", help="pretty print the output", action="store_true", default=False)
    parser.add_argument("-l", "--level", dest="level", help="level of detail severity for the analysis", choices = ["hard", "medium", "soft", "softer"], default="soft")
    parser.add_argument("-S", "--summarize", dest="summarize", help="summarize the usage for the VMs", action="store_true", default=False)
    parser.add_argument("-U", "--under-threshold", dest="threshold_summarize", help="summary will show only VMs under this threshold of puntuation (from 0 to 10)", type=int, default=3)
    parser.add_argument("-o", "--sort", dest="sort", help="Sort the output descending by estimated usage of the VM", action="store_true", default=False)
    parser.add_argument("-i", "--vm-id", dest="vmids", action="append", help="id of the VMs to be analyzed (can appear multiple times)", type=str)
    parser.add_argument("-v", "--verbose", dest="verbose", help="verbose", action="store_true", default=False)
    parser.add_argument("--full-report", dest="fullreport", help="this is a shorthand for --include-eval-data, --include-eval-data-graph and --include-stats", action="store_true", default=False)
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", help="verbose more", action="store_true", default=False)
    parser.add_argument("--include-eval-data", dest="include_eval_data", action="store_true", default=False, help="include data used for evaluation")
    parser.add_argument("--include-eval-data-graph", dest="include_eval_data_graph", action="store_true", default=False, help="include data used for evaluation but using a graphical representation (uses utf-8 encoding)")
    parser.add_argument("--include-stats", dest="include_stats", help="include the stats in the output", action="store_true", default=False)
    parser.add_argument("--dump-data", dest="dumpdata", action="store_true", default=False, help="dump the data that would be used for the analysis and finalizes")
    parser.add_argument("--info", dest="info", action="store_true", default=False, help="get the information about the data available and exit")
    parser.add_argument("--vmlist", dest="vmlist", action="store_true", default=False, help="if getting information, dump the list of available VMs")
    parser.add_argument('--version', action='version', version=VERSION)

    args = parser.parse_args()

    if not args.quiet:
        if args.verbose:
            setVerbose(1)
        if args.verbosemore:
            setVerbose(2)

    # Connect to the database (if possible)
    storage = Storage(args.database)
    storage.connect()

    # Get the begin and end time of the data
    p_debugv("getting information from the database")
    beginTime = storage.getmint()
    endTime = storage.getmaxt()

    # Correct the arguments using the keywords and special values
    if args.fullreport:
        args.include_eval_data = True
        args.include_eval_data_graph = True
        args.include_stats = True
        
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

    # Prepare the output file
    if args.format != "excel":
        try:
            p_debugv("Opening output file {}".format(args.outputfile))
            output_file = OutputFile(args.outputfile, args.overwrite)
        except Exception as e:
            p_error("Error: {}".format(str(e)))
            sys.exit(1)
    else:
        if args.outputfile == "-":
            args.outputfile = "/dev/stdout"

        if args.outputfile == "/dev/stdout":
            p_error("Excel output format is not supported for stdout")
            sys.exit(1)

        if not args.overwrite and os.path.isfile(args.outputfile):
            p_error("file '{}' already exists".format(args.outputfile))
            sys.exit(1)

        try:
            workbook = xlsxwriter.Workbook(args.outputfile)
        except Exception as e:
            p_error("Error: {}".format(str(e)))
            sys.exit(1)

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
                        p_debugv("custom options for {}: {}".format(uuid, options[1]))
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

    if not args.quiet:
        pbar = tqdm(total=len(vms), desc="Processing VMs", unit="VMs")
    for vm in vms:
        if not args.quiet and getVerbose() == 0:
            pbar.update(1)
        p_debug("reading entries for vm {}".format(vm))
        vmdata = storage.getvmdata(vm, args.fromdate, args.todate)
        p_debugv("{} entries found".format(len(vmdata)))

        if len(vmdata) == 0:
            continue

        rawdata[vm] = RawData(vmdata, args)

    # Close the progress bar to avoid weird output
    if not args.quiet:
        pbar.close()

    # If only wanted to get the data, dump it an finalize
    if args.dumpdata:
        for vm, data in rawdata.items():
            output_file.println(data.dumpdata(args.format, args.pretty, transform_fnc=lambda x: (vm, *x)))
        sys.exit(0)

    # Now prepare the results for the analysis
    if args.format == 'json' or args.format == 'shell':
        result = {}
    else:
        result = []

    f_stats = []
    f_evaluation = []
    f_data = []
    h_data = []
    h_stats = []
    fmt_stats = []
    fmt_evaluation = []
    fmt_data = []
    h_evaluation = [ "ID", "Overall" ]

    # This is only for excel output
    fmt_evaluation = [ None, "0.00" ]

    # Depending on what we want to get from the analysis, we prepare the different headers and the data
    if args.analysis_cpu:
        if args.include_stats:
            f_stats = [ *f_stats, "stats.cpu.min", "stats.cpu.max", "stats.cpu.mean", "stats.cpu.median" ]
            h_stats = [ *h_stats, "CPU min", "CPU max", "CPU mean", "CPU median" ]
            fmt_stats = [ *fmt_stats, 10, 10, 10, 10 ]
        f_evaluation = [ *f_evaluation, "cpu.score" ]
        h_evaluation = [ *h_evaluation, "P. CPU" ]
        fmt_evaluation = [ *fmt_evaluation, "0.00" ]
        if args.include_eval_data:
            f_data = [ *f_data, "cpu.data", "cpu.cores" ]
            h_data = [ *h_data, "cpu 0-10", "cpu 10-20", "cpu 20-30", "cpu 30-40", "cpu 40-50", "cpu 50-60", "cpu 60-70", "cpu 70-80", "cpu 80-90", "cpu 90-100", "Suggested cores" ]
            fmt_data = [ *fmt_data, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 0 ]
        if args.include_eval_data_graph:
            f_data = [ *f_data, "cpu.graph" ]
            h_data = [ *h_data, "cpu graph" ]
            fmt_data = [ *fmt_data, None ]

    if args.analysis_disk:
        if args.include_stats:
            f_stats = [ *f_stats, "stats.disk.min", "stats.disk.max", "stats.disk.mean", "stats.disk.median" ]
            h_stats = [ *h_stats, "Disk min", "Disk max", "Disk mean", "Disk median" ]
            fmt_stats = [ *fmt_stats, 0, 0, 0, 0 ]
        f_evaluation = [ *f_evaluation, "disk.score" ]
        h_evaluation = [ *h_evaluation, "P. disk" ]
        fmt_evaluation = [ *fmt_evaluation, "0.00" ]
        if args.include_eval_data:
            f_data = [ *f_data, "disk.data" ]
            h_data = [ *h_data, "disk 0-10", "disk 10-20", "disk 20-30", "disk 30-40", "disk 40-50", "disk 50-60", "disk 60-70", "disk 70-80", "disk 80-90", "disk 90-100" ]
            fmt_data = [ *fmt_data, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 ]
        if args.include_eval_data_graph:
            f_data = [ *f_data, "disk.graph" ]
            h_data = [ *h_data, "disk graph" ]
            fmt_data = [ *fmt_data, None ]
    if args.analysis_nic:
        if args.include_stats:
            f_stats = [ *f_stats, "stats.nic.min", "stats.nic.max", "stats.nic.mean", "stats.nic.median" ]
            h_stats = [ *h_stats, "NIC min", "NIC max", "NIC mean", "NIC median" ]
            fmt_stats = [ *fmt_stats, 0, 0, 0, 0 ]
        f_evaluation = [ *f_evaluation, "nic.score" ]
        h_evaluation = [ *h_evaluation, "P. nic" ]
        fmt_evaluation = [ *fmt_evaluation, "0.00" ]
        if args.include_eval_data:
            f_data = [ *f_data, "nic.data" ]
            h_data = [ *h_data, "nic 0-10", "nic 10-20", "nic 20-30", "nic 30-40", "nic 40-50", "nic 50-60", "nic 60-70", "nic 70-80", "nic 80-90", "nic 90-100" ]
            fmt_data = [ *fmt_data, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 ]
        if args.include_eval_data_graph:
            f_data = [ *f_data, "nic.graph" ]
            h_data = [ *h_data, "nic graph" ]
            fmt_data = [ *fmt_data, None ]

    # Now get the analysis
    if not args.quiet:
        pbar = tqdm(total=len(rawdata), desc="Analyzing the data", unit="VMs")

    for vm, data in rawdata.items():
        if not args.quiet and (getVerbose() == 0):
            pbar.update(1)

        p_debug("evaluating data for vm {}".format(vm))
        _stats = DataSeries(data, args)

        stats = _stats.stats
        evaluation = _stats.evaluation
        evaluation["cpu"]["cores"] = math.ceil(_stats.stats["cpu"]["max"]) if _stats.stats["cpu"] is not None else 0

        # Calculate the overall score from the evaluation
        # TODO: check whether to use the 2nd value or not (this is more strict)
        scores = []

        if args.analysis_cpu and evaluation["cpu"]["score"] is not None:
            scores.append(evaluation["cpu"]["score"])

        if args.analysis_nic and evaluation["nic"]["score"] is not None:
            scores.append(evaluation["nic"]["score"])

        if args.analysis_disk and evaluation["disk"]["score"] is not None:
            scores.append(evaluation["disk"]["score"])
        
        # If wanted to remove the unknown values, we do it here
        if (len(scores) == 0) and args.removeunknown:
            p_debugv("removing vm {} because it has no valid data".format(vm))
            continue

        # In the "softer" mode, we overweight the maxium score, so that the VM profile is taken into account
        if args.level == "softer":
            if len(scores) > 0:
                scores = [ *scores, max(scores)]

        overall = round(sum(scores) / len(scores), 2) if len(scores) > 0 else 0

        # If wanted to dump the stats, add them to the evaluation
        if args.include_stats:
            evaluation["stats"] = stats

        # Add the graph data to the information just in case it is needed
        evaluation["cpu"]["graph"] = dataset_to_barchart(evaluation["cpu"]["data"], 0, 1)
        evaluation["disk"]["graph"] = dataset_to_barchart(evaluation["disk"]["data"], 0, 1)
        evaluation["nic"]["graph"] = dataset_to_barchart(evaluation["nic"]["data"], 0, 1)

        # Depending on the format, retrieve the data
        if args.format == "json" or args.format == "shell":
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
            evaluation["cpu"]["data"] = [ "" if x == 0 else x for x in evaluation["cpu"]["data"] ] if evaluation["cpu"]["data"] is not None else [ ]
            evaluation["disk"]["data"] = [ "" if x == 0 else x for x in evaluation["disk"]["data"] ] if evaluation["disk"]["data"] is not None else [ ]
            evaluation["nic"]["data"] = [ "" if x == 0 else x for x in evaluation["nic"]["data"] ] if evaluation["nic"]["data"] is not None else [ ]

            result.append(
                (vm, overall, *get_fields(evaluation, f_evaluation), *get_fields(evaluation, f_data), *get_fields(evaluation, f_stats))
            )

    # Close the progress bar to avoid weird output
    if not args.quiet:
        pbar.close()

    # Finally, dump the data, depending on the format (moreover we'll sort it and summarize the data, depending on the options)
    if args.format == "json" or args.format == "shell":
        if args.summarize:
            result = { k:v for k,v in result.items() if v["overall"] < args.threshold_summarize }

        if args.sort:
            result = dict(sorted(result.items(), key=lambda x: x[1]["overall"], reverse=True))

    else:
        if args.summarize:
            result = [ x for x in result if x[1] < args.threshold_summarize ]

        if args.sort:
            result = sorted(result, key=lambda x: x[1], reverse=True)

    if args.format == "json":
        if args.pretty:
            output_file.println(json.dumps(result, indent=4))
        else:
            output_file.println(json.dumps(result))
    elif args.format == "shell":
        fields = [ "disk.score", "cpu.score", "nic.score", "overall" ]
        if args.include_eval_data_graph:
            fields = [ *fields, "disk.graph", "cpu.graph", "nic.graph" ]
        if args.include_eval_data:
            fields = [ *fields, "cpu.cores" ]
        if args.include_stats:
            fields = [ *fields, 
                "stats.disk.min", "stats.disk.max", "stats.disk.mean", "stats.disk.median", 
                "stats.cpu.min", "stats.cpu.max", "stats.cpu.mean", "stats.cpu.median", 
                "stats.nic.min", "stats.nic.max", "stats.nic.mean", "stats.nic.median" 
            ]
        c = 0

        for vm, _r in result.items():
            output = [
                "ID_{}={}".format(c, vm)
            ]
            _r = [ x if x is not None else "" for x in get_fields(_r, fields) ]
            for i in range(len(fields)):
                output.append("{}_{}={}".format(fields[i].replace(".", "_"), c, _r[i]))
            output_file.println("\n".join(output))
            c += 1
    else:
        headers = [ *h_evaluation ]
        format = [ *fmt_evaluation ]
        if args.include_eval_data or args.include_eval_data_graph:
            headers = [ *headers, *h_data ]
            format = [ *format, *fmt_data ]
        if args.include_stats:
            headers = [ *headers, *h_stats ]
            format = [ *format, *fmt_stats ]

        if args.format == "excel":
            # Create the excel file
            formats = {}

            worksheet = workbook.add_worksheet()
            for h in headers:
                worksheet.write(0, headers.index(h), h)

            for i in range(len(result)):
                for j in range(len(headers)):

                    c_fmt = None
                    if format[j] is not None:
                        if j not in formats:
                            formats[j] = workbook.add_format({
                                "num_format": format[j]
                            })
                        c_fmt = formats[j]
                        
                    if c_fmt is None:
                        worksheet.write(i+1, j, result[i][j])
                    else:
                        worksheet.write(i+1, j, result[i][j], c_fmt)
            workbook.close()
        else:
            output_file.println(",".join(headers))
            output_file.println("\n".join( [ ",".join([str(x) for x in y]) for y in result ]))        

if __name__ == "__main__":
    osidle_analysis()