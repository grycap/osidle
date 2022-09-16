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
import paramiko
import io
import subprocess
import shlex
from .virsh2osidle import readDomains
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

class OSIdleSSHClient(paramiko.SSHClient):
    def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, environment=None):
        # This is the regular method, but also returns the status (inspired in https://stackoverflow.com/a/3563211/14699733)
        chan = self._transport.open_session(timeout=timeout)
        if get_pty:
            chan.get_pty()
        chan.settimeout(timeout)
        if environment:
            chan.update_environment(environment)
        chan.exec_command(command)
        stdin = chan.makefile_stdin("wb", bufsize)
        stdout = chan.makefile("r", bufsize)
        stderr = chan.makefile_stderr("r", bufsize)
        return stdin, stdout, stderr, chan.recv_exit_status()

    @classmethod
    def remoteConnection(cls, hostname, username, keyFilename = None, port = 22, proxyHostname = None, proxyUsername = None, proxyKeyFilename = None):
        """A method to make a remote connection, using a proxy (if needed)
        """
        # This method makes use of this example: https://github.com/paramiko/paramiko/issues/1018#issuecomment-744151656
        client = cls()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sock = None

        if proxyHostname:
            gatewayClient = cls.remoteConnection(proxyHostname, username if proxyUsername is None else proxyUsername, proxyKeyFilename)
            if gatewayClient is None:
                return False
            sock = gatewayClient.get_transport().open_channel('direct-tcpip', (hostname, port), ('', 0))

        kwargs = dict( hostname = hostname, port = port, username = username, key_filename = keyFilename, sock = sock)
        try:
            client.connect(**kwargs)
        except paramiko.SSHException as e:
            p_error(f"failed to connect {hostname} using proxy {proxyHostname} ({e})")
            client = None

        return client        
    
    @classmethod
    def connectTo(cls, hostname, username, keyFilename = None, port = 22, sock = None):
        # This method makes use of this example: https://github.com/paramiko/paramiko/issues/1018#issuecomment-744151656
        client = cls()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = dict( hostname = hostname, port = port, username = username, key_filename = keyFilename, sock = sock)
        try:
            client.connect(**kwargs)
        except paramiko.SSHException as e:
            p_error(f"failed to connect {hostname} ({e})")
            client = None

        return client        

    @classmethod
    def getProxySock(cls, hostname, port, proxyHostname, proxyUsername, proxyKeyFilename = None, proxyPort = 22):
        proxyClient = cls.connectTo(proxyHostname, proxyUsername, proxyKeyFilename, proxyPort)
        if proxyClient is None:
            return None
        return proxyClient.get_transport().open_channel('direct-tcpip', (hostname, port), ('', 0))

class MonitorClusterSSH(Monitor):
    def __init__(self, db, frontEndHostname = None, hostnames = [], frontEndUsername = "osidle", frontEndPrivateKey = None, virshDomstatsCommand = None):
        super().__init__(db)
        self._hostnames = hostnames
        self._username = frontEndUsername
        self._privateKeyFile = frontEndPrivateKey
        self._hostname = frontEndHostname
        self._sshClient = None
        self._vm_pool = {}
        self._virshDomstatsCommand = virshDomstatsCommand
        
        if virshDomstatsCommand is None:
            raise Exception("Need a virsh command line to get the list of VMs in one host and to get the info of the domains in one host")

        self._monitorVM_callback = self._monitorVMsLocal
        if self._hostname is not None:
            self._monitorVM_callback = self._monitorVMsSSH
            if not self._sshConnect():
                return False

    def _sshConnect(self, reconnect = False):
        # If no SSH connection needed, 
        if self._hostname is None:
            return True

        shouldConnect = False
        if self._sshClient is None:
            shouldConnect = True
        else:
            if not self._sshClient.get_transport().is_active():
                shouldConnect = True
        if reconnect:
            shouldConnect = True

        if not shouldConnect:
            return True
        try:
            # Uses the passwordless configuration of the user that runs the app; the alternative is to use a private key file, using [key_filename] parameter
            p_debug(f"connecting to host {self._hostname}")
            sshClient = OSIdleSSHClient.remoteConnection(hostname = self._hostname, username = self._username, keyFilename=self._privateKeyFile)
            self._sshClient = sshClient
            return True
        except Exception as e:
            p_error(f"An error occurred when connecting to {self._hostname}: {e}")
            self._sshClient = None
            return False

    def _sshRun(self, command):
        if not self._sshConnect():
            return False
        try:
            stdin, stdout, stderr, exitStatus = self._sshClient.exec_command(command)
        except paramiko.SSHException as e:
            try:
                # Force re-connect just in case that the connection was closed
                if not self._sshConnect(True):
                    return False
                stdin, stdout, stderr, exitStatus = self._sshClient.exec_command(command)
            except paramiko.SSHException as e:
                return False
        return stdin, stdout, stderr, exitStatus

    def check(self):
        return self._sshConnect()

    def _monitorVMsSSH(self, hostname):
        try:
            stdin, stdout, stderr, exitStatus = self._sshRun(self._virshDomstatsCommand.format(hostname = hostname))
        except paramiko.SSHException as e:
            p_error(f"exception getting the VMs from {hostname}: {e}")
        if exitStatus != 0:
            return False
        return stdout

    def _monitorVMsLocal(self, hostname):
        assert("Not tested!")
        try:
            process = subprocess.run(args=shlex.split(self._virshDomstatsCommand.format(hostname = hostname)), capture_output=True)
        except Exception as e:
            p_error(f"exception getting the VMs from {hostname}: {e}")
        if process.returncode != 0:
            return False
        return io.BytesIO(process.stdout)

    def updateVMs(self):
        for hostname in self._hostnames:
            if hostname not in self._pending_vms:
                self._pending_vms.append(hostname)
        p_debug("list of hosts to monitor updated")

    def monitorVMs(self, limit=None, walltime=0, conflicting_alert=False, filter_fnc=lambda x: x):
        count = 0
        failed = 0

        p_debugv("{} hosts pending of monitorisation".format(len(self._pending_vms)))
        p_debugv(f"hostnames: {', '.join(self._pending_vms)}")

        t0 = datetime.now().timestamp()

        while (count < limit) and (len(self._pending_vms) > 0) and (walltime > 0):
            nextId = self._pending_vms.pop(0)

            serverInfo = self._monitorVM_callback(nextId)

            # Get the VM info
            if serverInfo == False:
                failed += 1
                p_error(f"failed to obtain info about VM {nextId}")
            else:
                domains = readDomains(serverInfo.read().decode("UTF-8"))
                if domains is not None:
                    p_debug(f"obtained {len(domains)} VMs from host {nextId}")
                    p_debugv(f"vm ids: {', '.join(list(domains.keys()))}")

                    for vmId in domains:
                        serverInfo = domains[vmId]
                        self._db.savevm(vmId, filter_fnc(serverInfo))

                count += 1
                t1 = datetime.now().timestamp()
                walltime = walltime - (t1 - t0)
                p_debugv("still have {} seconds to monitor in this block".format(walltime))
                t0 = t1

        p_debug("{} hosts monitored".format(count))
        return failed

def osidle_monitor_virsh():
    config = Configuration({
            "DEFAULT": {
                # Comma separated list of hostnames whose VMs are to be monitored
                "HOSTNAMES": "",
                # The commandline to use to obtain the stats of the domains in one host. Please include {hostname} where the name of the host should be included in the commandline
                "VIRSH_DOMSTAT": 'virsh -c qemu+ssh://root@{hostname}/system?socket=/var/run/libvirt/libvirt-sock domstats --raw --list-running',
                # The amount of hosts to monitor at once (default: 5)
                "MONITORING_BLOCKSIZE": 5,
                # The amount of time that can be dedicated to monitor a block of Hosts (default: 5 seconds)
                "MONITORING_BLOCK_TIME": 5,
                # The amount of time that the monitor waits before the next monitorization (default: 5)
                "MONITORING_INTERVAL": 5,
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
                # The front-end to connect (in case that this is not running from the front-end; it needs virsh connectivity to the internal nodes)
                "FRONTEND_HOSTNAME": ("", lambda x: None if x == "" else x),
                # The user name to connect to the front-end
                "FRONTEND_USERNAME": ("", lambda x: None if x == "" else x),
                # The file containing the private key to connect to the front-end
                "FRONTEND_PRIVATEKEY_FILE": ("", lambda x: None if x == "" else x),
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
    parser.add_argument("-b", "--block-size", dest="blocksize", default=configuration["MONITORING_BLOCKSIZE"], help="The maximum number of hosts to be monitored in a row", type=int)
    parser.add_argument("-t", "--block-time", dest="blocktime", type=int, default=configuration["MONITORING_BLOCK_TIME"], help="The maximum time to be used to monitor a block of hosts")
    parser.add_argument("-C", "--cooldown", dest="cooldown", default=configuration["MONITORING_INTERVAL"], type=int, help="Once a monitoring interval has finished, the amount of seconds to wait before the next monitorisation")
    parser.add_argument("-u", "--vm-update", dest="vmupdate", default=configuration["MONITORING_FULL_INTERVAL"], type=int, help="Time between full updates of the VM list and starting the monitorization of the hosts again")
    parser.add_argument("-l", "--main-loop", dest="mainloop", default=configuration["MAIN_LOOP_INTERVAL"], type=int, help="Main loop interval; the default is {} second and it is not advisable to change it".format(MAIN_LOOP_INTERVAL))
    parser.add_argument("-N", "--notification", dest="notification", type=str, default=configuration["NOTIFICATION_COMMAND"], help="Command to be executed when an error happens; the error message will be passed in the stdin")
    parser.add_argument("-d", "--database", dest="database", help="database to use (at this point, only is valid a sqlite3 file)", default=configuration["DATABASE"])
    parser.add_argument("-v", "--verbose", dest="verbose", help="verbose mode", action="store_true", default=configuration["VERBOSE"])
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", help="verbose more mode", action="store_true", default=configuration["DEBUG"])
    parser.add_argument("--frontend-username", dest="frontend_username", help="The user name to connect to the front-end", default=configuration["FRONTEND_USERNAME"])
    parser.add_argument("--frontend-pkey-file", dest="frontend_pkey", help="The file containing the private key to connect to the front-end", default=configuration["FRONTEND_PRIVATEKEY_FILE"])
    parser.add_argument("--frontend-hostname", dest="frontend_hostname", help="The front-end to connect (in case that this is not running from the front-end; it needs virsh connectivity to the internal nodes)", default=configuration["FRONTEND_HOSTNAME"])
    parser.add_argument("-r", "--remove-unneeded-data", dest="storerawdata", help="Remove the unneeded data before storing it", action="store_false", default=configuration["STORE_RAW_DATA"])
    parser.add_argument("--virsh-vm-domstats", dest="virshDomstats", help="The command to obtain the stats of the VMs from a host", default=configuration["VIRSH_DOMSTAT"])
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument("-H", "--hostnames", default=configuration["HOSTNAMES"], help="Comma separated list of hostnames whose VMs are to be monitored", type=str)

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

    # Connect to the database (if possible)
    p_debugv("connecting to the database {}".format(args.database))
    storage = Storage(args.database)
    storage.connect()

    # Prepare the monitor
    monitor = MonitorClusterSSH(storage, hostnames = [ x for x in map(lambda x: x.strip(), args.hostnames.split(",")) if x != "" ], frontEndHostname = args.frontend_hostname, 
        frontEndUsername=args.frontend_username, frontEndPrivateKey=args.frontend_pkey, virshDomstatsCommand=args.virshDomstats)

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

                    failed = monitor.monitorVMs(args.blocksize, args.blocktime, False, filter_fnc)
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
