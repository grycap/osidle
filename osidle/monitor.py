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
import time
from .common import *
from .osconnect import getServers, getServerInfo, Token
from datetime import datetime
from .storage import Storage, remove_unneeded_data
from .runcommand import runcommand_e
import argparse
from .configuration import Configuration
import os 
from .version import VERSION

# The main loop interval (in seconds, 1 second is fine)
MAIN_LOOP_INTERVAL = 1

# The idea is to be kind with the system: make monitorings of MONITORING_VM_BLOCK_TIME seconds, monitoring up to MONITORING_VM_BLOCKSIZE VMs
#   and then wait MONITORING_VM_INTERVAL before trying to monitor the next VM block

class Monitor:
    def __init__(self, db):
        self._token = Token()
        self._pending_vms = []
        self._db = db

    def check(self):
        return self._token.renewIfNeeded()

    def updateVMs(self):
        servers = getServers(self._token)
        if servers is None:
            p_error("failed to obtain servers from OpenStack")
            return False
            
        p_debug("{} servers obtained".format(len(servers)))

        for x in servers:
            id = x["id"]
            if id not in self._pending_vms:
                self._pending_vms.append(id)

    def havePendingVMs(self):
        return len(self._pending_vms)

    def monitorVMs(self, limit = None, walltime = 0, conflicting_alert = False, filter_fnc = lambda x: x):
        count = 0
        failed = 0

        p_debugv("{} VMs pending of monitorisation".format(len(self._pending_vms)))

        t0 = datetime.now().timestamp()

        while (count < limit) and (len(self._pending_vms) > 0) and (walltime > 0):
            nextId = self._pending_vms.pop(0)

            # Get the VM info
            serverInfo = getServerInfo(self._token, nextId)
            if serverInfo is None:
                failed += 1
                p_error("failed to obtain VM info from OpenStack")

            # Get the VM status
            if conflicting_alert and ('conflictingRequest' in serverInfo):
                p_warning("{} has conflicting request".format(nextId))
                serverInfo = None
            
            if serverInfo is not None:
                self._db.savevm(nextId, filter_fnc(serverInfo))

            count += 1
            t1 = datetime.now().timestamp()
            walltime = walltime - (t1 - t0)
            p_debugv("still have {} seconds to monitor in this block".format(walltime))
            t0 = t1

        p_debug("{} VMs monitored".format(count))
        return failed

def osidle_monitor():
    config = Configuration({
            "DEFAULT": {
                # The amount of VMs to retrieve at once (default: 25)
                "MONITORING_VM_BLOCKSIZE": 25,
                # The amount of time that can be dedicated to monitor a block of VMs (default: 5)
                "MONITORING_VM_BLOCK_TIME": 5,
                # The amount of time that the monitor waits before the next monitorization (default: 5)
                "MONITORING_VM_INTERVAL": 5,
                # The amount of time that the monitor waits before updating the list of running VMs (default: 600)
                "MONITORING_FULL_INTERVAL": 600,
                # The main loop interval (in seconds, 1 second is fine)
                "MAIN_LOOP_INTERVAL": 1,
                # The amount of time that the monitor waits before notifying for errors, again (default: 21600; i.e. 6 hours)
                "NOTIFICATION_INTERVAL": 21600,
                # The command that will be used to notify the admin for errors in the monitor; the errors will be passed in the standard input (default: None)
                "NOTIFICATION_COMMAND": ("", lambda x: None if x == "" else x),
                # A message to show that the monitor is running (default: "osidled is running")
                "STILL_ALIVE_MESSAGE": "--- osidled is running",
                # The amount of time that the monitor waits before showing a message that the monitor is still running (default: 14400; i.e. 4 hours)
                "STILL_ALIVE_MESSAGE_INTERVAL": 14400,
                # The database file where the monitor will store the data (default: /var/lib/osidled/osidled.db)
                "DATABASE": "/var/lib/osidled/osidled.db",
                # Run the monitor in verbose mode, showing more messages (default: False)
                "VERBOSE": False,
                # Run the monitor in debug mode, showing much more messages (default: False)
                "DEBUG": False,
                # The username to connect to the OpenStack server (default: None)
                "OS_USERNAME": ("", lambda x: None if x == "" else x),
                # The password to connect to the OpenStack server (default: None)
                "OS_PASSWORD": ("", lambda x: None if x == "" else x),
                # The authentication URL to connect to the OpenStack server (default: None)
                "OS_AUTH_URL": ("", lambda x: None if x == "" else x),
                # In case that a VM is not running, OpenStack returns a "conflicting error" and osidle monitor will notify about them. This option allows to ignore such errors (default: False)
                "SILENCE_CONFLICTING": False,
                # By default, osidle monitor will store the raw data obtained for each VM. Changing this option allows to store only the data that will use osidle (default: True, to store the raw data)
                "STORE_RAW_DATA": True,
            }
        }
    )

    parser = argparse.ArgumentParser(allow_abbrev=False, add_help = False)
    parser.add_argument("-c", "--config", default=None, dest="configurationfile", help = "Use this configuration file")

    configargs, _ = parser.parse_known_args()

    if configargs.configurationfile is not None:
        (configfiles, configuration) = config.read([ configargs.configurationfile ])
        if len(configfiles) == 0:
            p_error("failed to read configuration file")
            exit(1)
    else:
        (configfiles, configuration) = config.read([ "./osidled.conf", "/etc/osidle/osidled.conf", "/etc/osidled.conf", "/etc/default/osidled.conf" ], False)

    configuration = configuration["DEFAULT"]
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit.')
    parser.add_argument("-b", "--block-size", dest="blocksize", default=configuration["MONITORING_VM_BLOCKSIZE"], help="The maximum number of VMs to be monitored in a row", type=int)
    parser.add_argument("-t", "--block-time", dest="blocktime", type=int, default=configuration["MONITORING_VM_BLOCK_TIME"], help="The maximum time to be used to monitor a block of VMs")
    parser.add_argument("-C", "--cooldown", dest="cooldown", default=configuration["MONITORING_VM_INTERVAL"], type=int, help="Once a monitoring interval has finished, the amount of seconds to wait before the next monitorisation")
    parser.add_argument("-u", "--vm-update", dest="vmupdate", default=configuration["MONITORING_FULL_INTERVAL"], type=int, help="Time between full updates of the VM list and starting the monitorization of the VMs again")
    parser.add_argument("-l", "--main-loop", dest="mainloop", default=configuration["MAIN_LOOP_INTERVAL"], type=int, help="Main loop interval; the default is {} second and it is not advisable to change it".format(MAIN_LOOP_INTERVAL))
    parser.add_argument("-N", "--notification", dest="notification", type=str, default=configuration["NOTIFICATION_COMMAND"], help="Command to be executed when an error happens; the error message will be passed in the stdin")
    parser.add_argument("-d", "--database", dest="database", help="database to use (at this point, only is valid a sqlite3 file)", default=configuration["DATABASE"])
    parser.add_argument("-s", "--silence-conflicting", dest="conflicting", help="Hide the 'conflicting request' alerts", action="store_false", default=configuration["SILENCE_CONFLICTING"])
    parser.add_argument("-v", "--verbose", dest="verbose", help="verbose mode", action="store_true", default=configuration["VERBOSE"])
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", help="verbose more mode", action="store_true", default=configuration["DEBUG"])
    parser.add_argument("-U", "--os-username", dest="username", help="OpenStack username (if not set, will be obtained using OS_USERNAME env var)", default=configuration["OS_USERNAME"])
    parser.add_argument("-P", "--os-password", dest="password", help="OpenStack password  (if not set, will be obtained using OS_PASSWORD env var)", default=configuration["OS_PASSWORD"])
    parser.add_argument("-H", "--os-auth", dest="keystone", help="OpenStack keytsone authentication endpoint (if not set, will be obtained using OS_AUTH_URL env var)", default=configuration["OS_AUTH_URL"])
    parser.add_argument("-r", "--remove-unneeded-data", dest="storerawdata", help="Remove the unneeded data before storing it", action="store_false", default=configuration["STORE_RAW_DATA"])
    parser.add_argument('--version', action='version', version=VERSION)

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        sys.exit(1)

    if args.verbose:
        setVerbose(1)
    if args.verbosemore:
        setVerbose(2)

    if len(configfiles) > 0:
        p_debug("Reading configuration from {}".format(", ".join(configfiles)))

    if args.username is not None:
        os.environ['OS_USERNAME'] = args.username
    if args.password is not None:
        os.environ['OS_PASSWORD'] = args.password
    if args.keystone is not None:
        os.environ['OS_AUTH_URL'] = args.keystone

    # Connect to the database (if possible)
    p_debugv("connecting to the database {}".format(args.database))
    storage = Storage(args.database)
    storage.connect()

    # Prepare the monitor
    monitor = Monitor(storage)

    if not monitor.check():
        p_error("failed to connect to OpenStack")
        sys.exit(1)

    # Start the main loop
    t0_vm = 0
    t0_full = 0
    t00 = datetime.now().timestamp()
    p_info("starting the monitoring loop")
    tN_0 = 0
    filter_fnc = lambda x: x

    # List of errors
    error_list = []

    if not args.storerawdata:
        p_debug("removing the unneeded data")
        filter_fnc = remove_unneeded_data

    while True:
        try:
            t1 = datetime.now()
            t1 = t1.timestamp()

            if len(error_list) > 0:
                if t1 - tN_0 > configuration["NOTIFICATION_INTERVAL"]:
                    tN_0 = t1

                    if args.notification is not None:
                        p_debug("notifying using command {}".format(args.notification))
                        retcode, cout, cerr = runcommand_e(args.notification, strin = "\n".join(error_list).encode("utf-8"))
                        p_debug("notification command returned {}".format(retcode))
                        p_debugv("notification command stdout: {}".format(cout))
                        p_debugv("notification command stderr: {}".format(cerr))

                    p_error("{} errors happened during the last {} seconds".format(len(error_list), configuration["NOTIFICATION_INTERVAL"]))
                    error_list = []

            if (t0_vm + args.blocktime) < t1:
                if monitor.havePendingVMs():
                    p_debug("monitorising up to {} vms".format(args.blocksize))

                    failed = monitor.monitorVMs(args.blocksize, args.blocktime, args.conflicting, filter_fnc)
                    if failed > 0:
                        p_debug("failed to monitor {} vms".format(failed))
                        error_list.append(s_error("failed to monitor {} vms".format(failed)))

                t0_vm = datetime.now().timestamp()

            if (t0_full + args.vmupdate) < t1:
                p_debug("full monitorisation")

                monitor.updateVMs()

                t0_vm = datetime.now().timestamp()
                t0_full = t0_vm

            if t1 - t00 > configuration["STILL_ALIVE_MESSAGE_INTERVAL"]:
                p_info(configuration["STILL_ALIVE_MESSAGE"])
                t00 = t1

        except Exception as e:
            p_error('Error: {}'.format(e))
            error_list.append(s_error(str(e)))

        p_debugv("wait {}".format(args.mainloop))
        time.sleep(args.mainloop)

if __name__ == "__main__":
    osidle_monitor()