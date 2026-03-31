import time

from osidle.common import p_debug, p_debugv, setVerbose, p_error
from osidle.storage import Storage

def assign(object, keychain, value):
    if isinstance(keychain, str):
        keychain = keychain.split('.')
    key = keychain.pop(0).strip()
    if key not in object:
        object[key] = {}
    if len(keychain) > 0:
        assign(object[key], keychain, value)
    else:
        object[key] = value
    
def isnumeric(v):
    try:
        float(v)
        return True
    except ValueError:
        return False

def domname(x):
    return "one-{}".format(x)

def virsh2osidle(v):
    if "vcpu" not in v:
        return None
    o = {}

    if "vcpu" in v:
        o["cpu_details"] = [ { "time": d["time"] } for cpuid, d in v["vcpu"].items() if isnumeric(cpuid) ],
    if "block" in v:
        o["disk_details"] = [ { "read_bytes": d["rd"]["bytes"] if "rd" in d else 0, "write_bytes": d["wr"]["bytes"] if "wr" in d else 0 } for diskid, d in v["block"].items() if isnumeric(diskid) ],
    if "net" in v:
        o["nic_details"] = [ { "rx_octets": d["rx"]["bytes"] if "rx" in d else 0, "tx_octets": d["tx"]["bytes"] if "tx" in d else 0 } for nicid, d in v["net"].items() if isnumeric(nicid) ],

    return o


def readDomains(output):
    domains = {}
    domain_data = {}
    domain = None
    for l in output.splitlines():
        if l.startswith('Domain:'):
            if domain is not None:
                domains[domain] = convertToOSidle(domain_data)
                
            domain_data = {}
            domain = l.split(":")[1].strip()[1:-1]
            continue

        pos = l.find('=')
        if pos > 0:
            key = l[:pos]
            val = l[pos+1:]
            assign(domain_data, key, val)
        else:
            # Skipping unkown line
            pass
    if domain is not None:
        domains[domain] = convertToOSidle(domain_data)
    return domains

def convertToOSidle(domain):
    data = {
        "driver": "libvirt",
        "hypervisor": "kvm",
        "hypervisor_os": "linux",
        "uptime": round(float(domain["cpu"]["time"])*1e-9)
    }
    data["cpu_details"] = []
    data["disk_details"] = []
    data["nic_details"] = []
    for id, cpudata in domain["vcpu"].items():
        try:
            idint = int(id)
        except:
            continue
        data["cpu_details"].append(
            {
                "id": idint,
                "time": int(cpudata["time"])
            }
        )
    data["num_cpus"] = int(domain["vcpu"]["maximum"])

    for id, nicdata in domain["net"].items():
        try:
            idint = int(id)
        except:
            continue
        data["nic_details"].append(
            {
                "rx_drop": int(nicdata["rx"]["drop"]),
                "rx_octets": int(nicdata["rx"]["bytes"]),
                "rx_packets": int(nicdata["rx"]["pkts"]),
                "rx_errors": int(nicdata["rx"]["errs"]),
                "tx_drop": int(nicdata["tx"]["drop"]),
                "tx_octets": int(nicdata["tx"]["bytes"]),
                "tx_packets": int(nicdata["tx"]["pkts"]),
                "tx_errors": int(nicdata["tx"]["errs"]),
            }
        )

    data["num_nics"] = int(domain["net"]["count"])

    for id, diskdata in domain["block"].items():
        try:
            idint = int(id)
        except:
            continue
        data["disk_details"].append(
            {
                "errors_count": -1,
                "read_bytes": int(diskdata["rd"]["bytes"]),
                "read_requests": int(diskdata["rd"]["reqs"]),
                "write_bytes": int(diskdata["wr"]["bytes"]),
                "write_requests": int(diskdata["wr"]["reqs"]),
            }
        )

    data["num_disks"] = int(domain["block"]["count"])
    return data


def osidle_acquire_baremetal(proc_stat_file, proc_net_dev_file, proc_diskstats_file, timestamp = None, options = { 
    "clean_zeros": False,
    "exclude_interfaces": [],
    "exclude_disks": []
}):
    with open(proc_stat_file, "r") as f:
        proc_stat_data = f.read()
    with open(proc_net_dev_file, "r") as f:
        proc_net_dev_data = f.read()
    with open(proc_diskstats_file, "r") as f:
        proc_diskstats_data = f.read()

    timestamp = timestamp if timestamp is not None else int(time.time())

    # Convert the data to the format expected by osidle
    data = {
        "driver": "baremetal",
        "hypervisor": "none",
        "hypervisor_os": "linux",
        "uptime": timestamp,
        "cpu_details": [],
        "disk_details": [],
        "nic_details": []
    }

    # Convert the data from the proc_stat file    
    num_cpus = 0
    for line in proc_stat_data.splitlines():
        # We are getting the data from each core, so we are looking for lines starting with "cpu" followed by a number
        if line.startswith("cpu"):
            parts = line.split()
            cpu_id = int(parts[0][3:]) if parts[0] != "cpu" else None

            if cpu_id is None:
                continue

            total_time = sum(int(x) for x in parts[1:])
            idle_time = int(parts[4]) if len(parts) > 4 else 0
            data["cpu_details"].append({
                "id": cpu_id,
                "time": total_time,
                "idle_time": idle_time
            })

            num_cpus = max(num_cpus, cpu_id + 1)

    data["num_cpus"] = num_cpus

    # Convert the data from the proc_net_dev file
    for line in proc_net_dev_data.splitlines():
        if ":" in line:
            # filter out lo interface, as it is not a real network interface and it is not relevant for osidle
            if line.startswith("lo:"):
                continue

            # filter out interfaces specified in the exclude list

            parts = line.split(":")
            iface = parts[0].strip()

            excluded = False
            for exclude_iface in options["exclude_interfaces"]:
                if iface == exclude_iface:
                    excluded = True
                    break
                # Check if exclude_iface is a regex pattern that matches iface
                import re
                if re.match("^" + exclude_iface + "$", iface):
                    excluded = True
                    break
            
            if excluded:
                continue

            stats = parts[1].split()

            nic_details = {
                "name": iface,
                "rx_bytes": int(stats[0]),
                "rx_packets": int(stats[1]),
                "rx_errors": int(stats[2]),
                "rx_drop": int(stats[3]),
                "tx_bytes": int(stats[8]),
                "tx_packets": int(stats[9]),
                "tx_errors": int(stats[10]),
                "tx_drop": int(stats[11]),
                "rx_octets": int(stats[0]),
                "tx_octets": int(stats[8]),
            }

            if options["clean_zeros"]:
                if nic_details["rx_bytes"] == 0 and nic_details["tx_bytes"] == 0 and nic_details["rx_packets"] == 0 and nic_details["tx_packets"] == 0:
                    continue

            data["nic_details"].append(nic_details)

    data["num_nics"] = len(data["nic_details"])

    # Convert the data from the proc_diskstats file
    devices_names = []

    for line in proc_diskstats_data.splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        # We are looking for lines corresponding to disk devices, which have the format: major minor name ...; we will consider only the devices with a name starting with "sd" or "nvme"
        excluded = False
        for exclude_disk in options["exclude_disks"]:
            if parts[2] == exclude_disk:
                excluded = True
                break
            # Check if exclude_disk is a regex pattern that matches parts[2]
            import re
            if re.match("^" + exclude_disk + "$", parts[2]):
                excluded = True
                break

        if excluded:
            continue

        disk_details = {
            "name": parts[2],
            # Need to convert parts[3] and parts[7] from sectors to bytes; we will assume a sector size of 512 bytes, which is the most common sector size for modern disks
            "read_bytes": int(parts[5]) * 512,
            "write_bytes": int(parts[9]) * 512,
        }

        if options["clean_zeros"]:
            if disk_details["read_bytes"] == 0 and disk_details["write_bytes"] == 0:
                continue

        data["disk_details"].append(disk_details)
        devices_names.append(parts[2])

    valid_device_names = []
    for device_name in devices_names:
        parent_devices = [ d for d in devices_names if device_name.startswith(d) and d != device_name ]
        if len(parent_devices) == 0:
            valid_device_names.append(device_name)

    data["disk_details"] = [ d for d in data["disk_details"] if d["name"] in valid_device_names ]
    data["num_disks"] = len(data["disk_details"])
    return data

def osidle_convert_baremetal():
    import argparse
    import sys
    import re
    import os
    from os.path import basename
    from .version import VERSION
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help = True, description="This script is used to convert data from bare metal hosts into the format expected by osidle. It is used for testing purposes and it is not intended to be used in production environments.")
    parser.add_argument("-f", "--folder", dest="folder", default=".", help="The folder containing the files with the data to be converted", type=str)
    parser.add_argument("--proc-stat-format", dest="proc_stat_format", default="proc_stat.{timestamp}", help="The format of the files containing the output of the 'cat /proc/stat' command; the timestamp will be replaced by the actual timestamp of the file to be converted", type=str)
    parser.add_argument("--proc-net-dev-format", dest="proc_net_dev_format", default="proc_net_dev.{timestamp}", help="The format of the files containing the output of the 'cat /proc/net/dev' command; the timestamp will be replaced by the actual timestamp of the file to be converted", type=str)
    parser.add_argument("-I", "--exclude-interface", dest="exclude_interfaces", default=["lo"], help="The network interfaces to be excluded from the conversion; if not specified, no interfaces will be excluded; this option can be specified multiple times to exclude multiple interfaces", action="append")
    parser.add_argument("-z", "--clean-zeros", dest="clean_zeros", action="store_true", help="If specified, if a net dev or disk has all its values equal to zero, it will be excluded from the conversion; this is useful to exclude interfaces or disks that are not being used")
    parser.add_argument("-D", "--exclude-disks", dest="exclude_disks", default=['loop.*'], help="The disk devices to be excluded from the conversion; if not specified, no disk devices will be excluded; this option can be specified multiple times to exclude multiple disk devices; the disk devices will be matched against the name of the disk device in /proc/diskstats, so for example, to exclude all disks starting with 'sd', you can specify 'sd.*' as a regex pattern", action="append")
    parser.add_argument("-o", "--output-database", dest="database", default="osidle.db", help="The path to the SQLite database where the converted data will be stored", type=str)
    parser.add_argument("-O", "--overwrite-database", dest="overwrite_database", action="store_true", help="If specified, if the output database already exists, it will be overwritten; if not specified, if the output database already exists, the script will exit with an error")
    parser.add_argument("--proc-diskstats-format", dest="proc_diskstats_format", default="proc_diskstats.{timestamp}", help="The format of the files containing the output of the 'cat /proc/diskstats' command; the timestamp will be replaced by the actual timestamp of the file to be converted", type=str)
    parser.add_argument("-t", "--timecode", dest="timecode", default=None, help="The timecode of the file to be converted, in the format YYYYMMDDHHMMSS", type=str)
    parser.add_argument("-j", "--json", dest="json_output", action="store_true", help="If specified, the converted data will be printed in JSON format instead of being stored in the database")
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="If specified, the script will print more verbose output during the conversion process")
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", action="store_true", help="If specified, the script will print even more verbose output during the conversion process")
    parser.add_argument("-i", "--input-files", dest="input_files", default=None, nargs="+", help="The input files to be converted; if specified, the script will convert only the specified files instead of looking for files in the folder; the files should be specified in the format 'proc_stat:{timestamp}', 'proc_net_dev:{timestamp}' and 'proc_diskstats:{timestamp}', where {timestamp} is the timestamp of the file to be converted; this option can be specified multiple times to convert multiple files")

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        sys.exit(1)

    if args.verbose:
        setVerbose(1)
    if args.verbosemore:
        setVerbose(2)

    if not args.json_output:
        if args.database is None:
            p_error("Error: no output database specified; please specify a database file using the -o or --output-database option, or use the -j or --json option to print the converted data in JSON format")
            sys.exit(1)
        if os.path.exists(args.database):
            if not args.overwrite_database:
                p_error("Error: the specified database file already exists; please specify a different file or use the -O or --overwrite-database option to overwrite it")
                sys.exit(1)

    def timecode_to_seconds(timecode):
        from datetime import datetime
        dt = datetime.strptime(timecode, "%Y%m%d%H%M%S")
        return int(dt.timestamp())

    if args.input_files is not None:
        files = args.input_files
    else:
        if not os.path.isdir(args.folder):
            print("Error: the specified folder does not exist or is not a directory")
            sys.exit(1)
        files = os.listdir(args.folder)
        files = [ os.path.join(args.folder, f) for f in files if os.path.isfile(os.path.join(args.folder, f)) ]

    if args.timecode is None:
        # We are converting all the files in the folder provided that match the format specified in the arguments; we will look for files with the format proc_stat.{timestamp}, proc_net_dev.{timestamp} and proc_diskstats.{timestamp}
        proc_stat_files = [ f for f in files if re.match(args.proc_stat_format.replace("{timestamp}", ".*"), basename(f)) ]
        proc_net_dev_files = [ f for f in files if re.match(args.proc_net_dev_format.replace("{timestamp}", ".*"), basename(f)) ]
        proc_diskstats_files = [ f for f in files if re.match(args.proc_diskstats_format.replace("{timestamp}", ".*"), basename(f)) ]
    else:
        # Read the files with the data to be converted
        proc_stat_files = [ os.path.join(args.folder, args.proc_stat_format.format(timestamp=args.timecode)) ]
        proc_net_dev_files = [ os.path.join(args.folder, args.proc_net_dev_format.format(timestamp=args.timecode)) ]
        proc_diskstats_files = [ os.path.join(args.folder, args.proc_diskstats_format.format(timestamp=args.timecode)) ]

    valid_files = []
    i = 0

    p_debug("Found {} proc_stat files, {} proc_net_dev files and {} proc_diskstats files in the specified folder".format(len(proc_stat_files), len(proc_net_dev_files), len(proc_diskstats_files)))

    for f in proc_stat_files:
        i = i + 1
        proc_stat_file = f
        net_dev_file = None
        diskstats_file = None

        timestamp = re.match(args.proc_stat_format.replace("{timestamp}", "(.*)"), basename(f)).group(1)

        p_debugv("Analyzing {} proc_stat file: {}, timestamp: {}".format(i, proc_stat_file, timestamp))

        # Now look for the corresponding files in the other formats
        for f2 in proc_net_dev_files:
            if re.match(args.proc_net_dev_format.replace("{timestamp}", timestamp), basename(f2)):
                net_dev_file = f2
                break
        for f2 in proc_diskstats_files:
            if re.match(args.proc_diskstats_format.replace("{timestamp}", timestamp), basename(f2)):
                diskstats_file = f2
                break

        if net_dev_file is None or diskstats_file is None:
            p_debug("Skipping file {} because it does not have a corresponding file in the other formats".format(proc_stat_file))
            continue

        valid_files.append({ "timestamp": timestamp, "proc_stat_file": proc_stat_file, "net_dev_file": net_dev_file, "diskstats_file": diskstats_file })

    if len(valid_files) == 0:
        print("Error: no valid files found to convert; make sure that the specified folder contains files with the format specified in the arguments and that they have a corresponding file in the other formats")
        sys.exit(1)

    # Now sort the valid files by timestamp
    valid_files.sort(key=lambda x: x["timestamp"])

    p_debugv("Valid files to convert: {}".format(valid_files[:max(15, len(valid_files))]))

    resulting_data = []

    for files in valid_files:
        timestamp = files["timestamp"]
        proc_stat_file = files["proc_stat_file"]
        proc_net_dev_file = files["net_dev_file"]
        proc_diskstats_file = files["diskstats_file"]

        data = osidle_acquire_baremetal(proc_stat_file, proc_net_dev_file, proc_diskstats_file, timestamp=timecode_to_seconds(timestamp), options={
            "clean_zeros": args.clean_zeros,
            "exclude_interfaces": args.exclude_interfaces,
            "exclude_disks": args.exclude_disks
        })

        data["timestamp"] = timestamp
        resulting_data.append(data)

    if args.json_output:
        import json
        print(json.dumps(resulting_data, indent=4))
    else:
        if args.overwrite_database and os.path.exists(args.database):
            os.remove(args.database)
        storage = Storage(args.database)
        storage.connect()
        for data in resulting_data:
            storage.savevm("localhost", data, t=timecode_to_seconds(data["timestamp"]))