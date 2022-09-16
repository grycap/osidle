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
