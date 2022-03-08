# OpenStack IDLE VM Detector (osidle)
This project tries to analyze the usage of the different servers (Virtual Machines) in an OpenStack deployment.

The motivation for this project is that in a private cloud, users usually __launch VM and forget that they have been started__. This happens mainly because the users are not billed for the usage of private resources. But for the owner and the sysadmins, these _"launch-and-forgotten"_ servers are a headache: 1st because the resources are finite (private clouds are not Amazon's AWS clouds), and 2nd because using the resources prevent from rebooting the hosting servers (thus interrupt maintenance of the facilities).

Moreover, according to the evidence, __users tend to overestimate the number of resources their servers need__ to run. And this is especially true when the resources are "free" (i.e. do not cost money). Instead, when a user starts a server in Amazon AWS, he tries to control the resources better because more resources mean more money. 

Amazon AWS will not complain about paying for extra unneeded resources (Amazon wants to get your money, and if you asked to spend more money... it is your choice). But the sysadmin wants to have enough resources for its users without buying new resources.

And as a last thought, the sysadmins also offer a reduced set of flavours for the VMs that do not cover all the use cases. So maybe a user needs an amount of memory that is only offered along with 8 cores, but the user may only need 2 cores. In this case, the sysadmin is responsible for __overproviding resources for the VM flavours__. If many VMs face this case, the sysadmin should re-consider the resources for each flavour or even create new flavours.

As a summary, the use cases for this project are
1. to try to detect which servers are candidates to be powered off because they are not used.
1. to try to detect overestimated servers, to try to resize them
1. to try to detect the lack of flavours with the appropriate amount of resources

# Workflow

This server has two parts:
1. A __monitor__ that periodically contacts OpenStack and gets the metrics for the usage of the servers
2. An application that can be used to __analyze the data__

## Technical details

### Monitor

The monitor is a simple application that contacts the OpenStack server, retrieves the list of running servers and starts monitoring them.

- The list of servers is variable in time, but it is considered to be valid for a period of time. So the list of servers is retrieved each _MONITORING_FULL_INTERVAL_ seconds.

- The data of the servers that may be started between updating calls is not lost: the usage of these VMs will be retrieved in the next cycle, if they are still alive. It is important that this application is not for billing purposes: it is for detecting IDLE servers.

- To avoid a DDoS behaviour, the monitor checks the state of the servers in bursts: it retrieves the metrics for a set of MONITORING_VM_BLOCKSIZE servers at most, and it rests for MONITORING_VM_INTERVAL seconds before the next burst. Moreover, the burst is limited to last (at most) for MONITORING_VM_BLOCK_TIME seconds. If it passes such time, the burst will be interrupted and will rest according to MONITORING_VM_INTERVAL setting.

- The data is retrieved from the OpenStack server along with a timestamp. This is to enable a time-based analysis: it is not the same to use a 10% of CPU in 10 days, than using 100% of CPU for 1 day and 0% during the next 9 days.

- The data is stored in a __sqlite3__ database. Some other databases _may be considered in future releases __if it is of interest___.

- To reduce the amount of data in the database, the monitor will run a __consolidation task__ that will discard samples that are older than 


## Install

### Basic installation

`osidle` is built using python3, and it can be installed using pip3:

```console
pip3 install osidle
```

### From source

Alternatively, `osidle` can be installed from source.

```console
git clone https://github.com/dealfonso/osidle.git
cd osidle
python3 setup.py install
```

## Usage

`osidle` has a _monitor_ (i.e. `osidled`) and a command line application (i.e. `osidle`) that can be used to analyze the data. The monitor obtains the information from the OpenStack server and stores it in a database. Later the command line application can be used to analyze the data.

### Monitor (osidled)

The monitor can be run in background mode as a service, using the `systemd` unit file.

```console
$ systemctl start osidled
```

Then you can check the status of the service using journalctl:

```console
$ systemctl status osidled
```

The logs are stored in `/var/log/osidled.log`.

#### Monitoring configuration

Many options can be used to configure the monitor. Please refer to the documentation of the `osidled` command for more details (i.e. `--help` option).

Most of the options can be configured in the `/etc/osidled.conf` file using the next variables:

```conf
[DEFAULT]
# Run the monitor in verbose mode, showing more messages (default: False)
VERBOSE = False
# Run the monitor in debug mode, showing much more messages (default: False)
DEBUG = False
# The amount of VMs to retrieve at once (default: 25)
MONITORING_VM_BLOCKSIZE = 25
# The amount of time that can be dedicated to monitor a block of VMs (default: 5)
MONITORING_VM_BLOCK_TIME = 5
# The amount of time that the monitor waits before the next monitorization (default: 5)
MONITORING_VM_INTERVAL = 5
# The amount of time that the monitor waits before updating the list of running VMs (default: 600)
MONITORING_FULL_INTERVAL = 600
# The command that will be used to notify the admin for errors in the monitor; the errors will be passed in the standard input (default: None)
NOTIFICATION_COMMAND = 
# The amount of time that the monitor waits before notifying for errors, again (default: 21600; i.e. 6 hours)
NOTIFICATION_INTERVAL = 21600
# A message to show that the monitor is running (default: "osidled is running")
STILL_ALIVE_MESSAGE = --- osidled is running
# The amount of time that the monitor waits before showing a message that the monitor is still running (default: 14400; i.e. 4 hours)
STILL_ALIVE_MESSAGE_INTERVAL = 14400
# The database file where the monitor will store the data (default: /var/lib/osidled/osidled.db)
DATABASE = /var/lib/osidled/osidled.db
# The username to connect to the OpenStack server (default: None)
OS_USERNAME =
# The password to connect to the OpenStack server (default: None)
OS_PASSWORD =
# The authentication URL to connect to the OpenStack server (default: None)
OS_AUTH_URL =
# In case that a VM is not running, OpenStack returns a "conflicting error" and osidle monitor will notify about them. This option allows to ignore such errors (default: False)
SILENCE_CONFLICTING = False
```

#### Monitor in foreground

It is possible to run `osidled` from the commandline for debugging purposes, just using the `osidled` command. 

The basic usage of the monitor in the commandline is:

```console
$ osidled -v -c /etc/osidled.conf
```

### Analysis (osidle)

Once the monitor has obtained enough data, the analysis can be run. The analysis is done by the command line application `osidle`. Many options can be used to analyze the data. Please refer to the documentation of the `osidle` command for more details (i.e. `--help` option).

Some of the options are the next ones:

* --database: points to the sqlite3 file generated using `osidled`. Default: `/var/lib/osidled/osidled.db`
* --from: the starting date of the analysis. Default: the first timestamp available in the database.
    > _Note:_ It is possible to use the following format: `[<reference>-]count[<unit>]`. Where reference is one of `now`, `begin`, `end`, `lastweek`..., and count is an integer. The unit is one of `s`, `m`, `h`, `d`, `w`, `M`, `y`. For example, `--from=now-1d` will start the analysis from the last day.
* --to: the ending date of the analysis. Default: `now`.
    > _Note_: It is possible to use the same notation than for the `--from` option.
* --output: set the file where the results will be written. Default: `stdout`.
* --overwrite: overwrite the output file if it already exists. Default: `False`.
* --remove-unknown: remove those VMs for which the data is not available within the interval. Default: `False`.
* --format: the format of the output. The available formats are _json_, _csv_, _excel_ and _shell_. Default: `json`.
    > _Note:_ _excel_ is the same as _csv_ except for changing the separator from `,` to `;`, and using the `,` to separate decimals instead of `.`. 
* --pretty: try to output the results in a human-readable format. Default: `False`
* --summarize: show only those entries whose overall score is under a certain threshold. Default: `False`
* --under-threshold: the threshold for the `--summarize` option. Default: `3`
* --sort: sort the results by the overall score. Default: `False`
* --vm-id: the id of the VM to analyze. Default: `None`
    > _Note:_ The `--vm-id` parameter can be repeated to analyze multiple VMs.
* --no-cpu, --no-disk, --no-network: do not analyze the corresponding metrics. Default: `False` (i.e.: use the metrics)
* --threshold-disk, --threshold-nic: the threshold to consider that a VM has reached the full usage in the specific metric (i.e. the score of usage in such metric is 10). Default: `4K`
    > _Note:_ The threshold is expressed in bytes per second, and it accepts suffix B, K, M, G (default is `B` for Bytes).
* --dump-data, --info, --vmlist: obtain different information about the data available in the database.
* --include-eval-data: include the data used to evaluate the results. Default: `False`    
    > _Note:_ The evaluation data consists of data obtained from postprocessing the data series available. E.g. the percentage of time that the VM was using a percentage of CPU (clustered in deciles), or the percentage of time that the VM was using a specific rate of transference (clustered in deciles).
* --include-eval-data-graph: include the data used to evaluate the results using an easy to read graph (this option uses unicode charset). The graphs show the percentage of time of the VM in each decile of percentage usage (i.e. 0-10, 10-20, 20-30...). Default: `False`
* --include-stats: include the statistics of the data series. Default: `False`
    > _Note:_ The stats consists of basic stats: `min`, `max`, `mean`, `median` and `typical deviation`.
* --level: the hardness of the analysis to consider that a VM is used. Possible values: `loose`, `medium` or `strict`. Default: `loose`
    > _Note:_ In the `strict` level a VM is considered fully used (i.e. the score of usage in all metrics is 10) if it is using 100% of CPU all the time and it is using 100% of transference and disk (according to the thresholds) all the time.
* --custom-file: a file containing custom rules to be used in the analysis. Default: `None`
    > _Note:_ The file contains one line per specific rules to apply to a VM in the format `<vm id>:<command line parameters>`. The command line parameters used to run the application will be considered the default ones, and the parameters passed in the file `--custom-file` option will be added to them.
* --verbose, --verbose-more, --version, --help, --quiet: are the common well-known flags for many applications. 

#### Examples

**example 1: analysis with simple output**

```console
$ osidle --format csv -r --sort
ID,Overall,P. CPU,P. disk,P. nic
1afe17bc-7029-4612-b328-519f003ae2d7,10.0,10.0,10.0,10.0
314df20c-e05a-40fe-9b01-b722bd19831a,10.0,10.0,10.0,10.0
a16e1ee3-6ab7-4be9-bd8a-bc8c21ef1657,9.99,9.98,10.0,10.0
b1790317-d3fc-48e1-bf13-5cf9a1c4f3d6,9.81,9.44,10.0,10.0
ee96a7c8-610d-4112-9d3b-79fc02d6cc6d,9.44,8.33,10.0,10.0
5ebca45f-51dd-4214-a446-7930b98518eb,9.14,7.41,10.0,10.0
a26ddfe0-7aee-4acf-ba60-08433eaf5625,9.07,7.22,10.0,10.0
b4e59b49-5e74-48ab-89c5-e9598d80f650,8.89,6.67,10.0,10.0
e32c435a-24a4-4520-995a-a36d24da23fb,8.89,6.67,10.0,10.0
5c21917c-1898-4794-8564-935ce0d2df8b,8.33,5.35,10.0,9.65
819acb6b-f3f8-424a-8951-0b56cec4ccd8,8.3,4.89,10.0,10.0
f18ce9e1-09d8-4695-9744-5142a02b1127,7.54,2.62,10.0,10.0
6596bf60-72b7-4415-a626-2b56bdcb69f0,7.46,2.37,10.0,10.0
d9c09c65-3298-4f53-8d24-72166b68db50,7.44,3.38,10.0,8.94
b87741f6-f7be-4ff7-bdc5-180490831875,7.04,1.11,10.0,10.0
fb7e3bcb-eb41-4506-bf6b-e3c60e69ed1d,7.03,1.09,10.0,10.0
aa3461f2-0b85-41d6-976e-d068c2c696a3,6.87,10.0,0.6,10.0
73fa9b68-e2ef-4237-82d1-7e1f6fccfe1f,5.31,1.26,10.0,4.68
6892cfbc-8e4a-4094-8086-4218dce9b267,5.27,1.15,10.0,4.66
51e49247-077f-46da-9289-e0ab58afadd5,4.99,0.18,9.77,5.03
4ff8269d-996e-4ab0-a22f-dab6af335396,3.52,0.06,10.0,0.5
87ffa5bc-02f8-446e-a3d5-f48f3cb88afb,3.41,0.0,10.0,0.22
ccdf1453-7b1f-42ab-9171-4bd8caccd70c,2.32,3.16,1.43,2.38
d6bc1688-55de-48f1-93cd-4e14a6b01528,2.31,0.0,6.89,0.04
c8f6c5d7-88b4-4b1a-b389-79e66dc6aa9b,0.7,0.0,1.73,0.38
cb057c04-c90e-4733-ad4c-560e6703c803,0.62,0.0,1.85,0.0
17e13cd3-91f2-4098-b847-c0f3e0a08ddc,0.6,0.0,1.6,0.2
45ac6b3a-b697-48c4-8ecd-9a8b8d05f898,0.05,0.0,0.15,0.0
ec5dad43-ee0e-4980-aeca-8b116c0a281e,0.05,0.0,0.14,0.0
```

**example 2: analysis with stats for the last 2 weeks, including graphs of behavior**
```console
$ osidle --format csv -r --sort --include-eval-data-graph --from 2w
ID,Overall,P. CPU,P. disk,P. nic,cpu graph,disk graph,nic graph
1afe17bc-7029-4612-b328-519f003ae2d7,10.0,10.0,10.0,10.0,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
314df20c-e05a-40fe-9b01-b722bd19831a,10.0,10.0,10.0,10.0,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
a16e1ee3-6ab7-4be9-bd8a-bc8c21ef1657,9.95,9.84,10.0,10.0,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
51aaa1b7-953e-4e91-b66d-5930542bc5a3,9.84,9.53,10.0,10.0,▁▁▁▁▁▁▁▂▁▆,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
b1790317-d3fc-48e1-bf13-5cf9a1c4f3d6,9.81,9.44,10.0,10.0,▁▁▁▁▁▁▁▁▅▄,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
d8ab2848-6409-48de-b08b-875950703cd2,9.44,8.33,10.0,10.0,▁▁▁▁▁▁▄▁▁▅,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
5ebca45f-51dd-4214-a446-7930b98518eb,9.14,7.41,10.0,10.0,▁▁▁▁▃▂▁▂▁▄,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
8d333bb8-e22a-4dd9-a985-adcd705c4589,8.52,5.56,10.0,10.0,▁▁▁▁▁█▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
5490c981-f3a8-4974-9e51-0b0f193cbaae,8.46,5.37,10.0,10.0,▁▁▁▁▇▁▁▁▁▂,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
819acb6b-f3f8-424a-8951-0b56cec4ccd8,8.3,4.89,10.0,10.0,▂▁▁▁▄▂▁▁▁▂,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
251c39f6-91f1-4c6b-b283-af92724524ad,8.15,4.45,10.0,10.0,▁▁▁▁█▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
7a430a7f-ab2b-45ba-ab75-b94e4778171a,7.65,2.96,10.0,10.0,▁▁▃▆▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
710477c0-1dc6-41a7-82ea-278eca3f209a,7.42,4.38,10.0,7.87,▁▁▁▁█▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁█▁▁
6596bf60-72b7-4415-a626-2b56bdcb69f0,7.41,2.23,10.0,10.0,▁▁█▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
0365694c-5ddf-469c-a673-6ac12b4fe3b0,6.68,0.04,10.0,10.0,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
4d3821d8-acf7-4c54-8602-a91c71686eba,6.68,0.05,10.0,10.0,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
71ffacb4-43c5-486f-8fb0-c71d30ca740c,6.68,0.05,10.0,10.0,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁▁▁▁▁▁█
94aceec9-d8db-4222-82ca-eb8f6476df50,5.62,4.45,10.0,2.4,▁▁▁▁█▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁█▁▁▁▁▁▁▁
73fa9b68-e2ef-4237-82d1-7e1f6fccfe1f,5.34,1.25,10.0,4.77,▁▇▂▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁█▁▁▁▁▁
6892cfbc-8e4a-4094-8086-4218dce9b267,5.27,1.15,10.0,4.66,▁█▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,▁▁▁▁█▁▁▁▁▁
b344e0c6-6a96-4360-8514-bf3cb6840190,4.55,2.26,10.0,1.39,▆▁▁▁▁▁▁▁▁▃,▁▁▁▁▁▁▁▁▁█,▇▁▁▁▁▁▁▁▁▂
35324838-cf3b-4560-a86c-c2112f1cf961,3.4,0.0,10.0,0.21,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,█▁▁▁▁▁▁▁▁▁
0be615ae-2a69-4d16-98d5-b446ca89926c,3.38,0.0,10.0,0.15,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,█▁▁▁▁▁▁▁▁▁
3602d1c6-0fe1-4c89-9a68-2a63cbc6c04a,3.38,0.0,9.99,0.15,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▁▁▁▁█,█▁▁▁▁▁▁▁▁▁
d6bc1688-55de-48f1-93cd-4e14a6b01528,2.32,0.0,6.93,0.04,█▁▁▁▁▁▁▁▁▁,▁▁▁▁▁▂▆▂▁▁,█▁▁▁▁▁▁▁▁▁
1ed7acc4-2142-4795-bc54-7fef7e18dbd4,1.39,0.02,1.74,2.4,█▁▁▁▁▁▁▁▁▁,▅▂▁▁▁▁▁▁▁▂,▁▁█▁▁▁▁▁▁▁
b934037c-ed38-4e2f-9d03-73d0eb02fb51,0.61,0.0,1.6,0.22,█▁▁▁▁▁▁▁▁▁,▆▂▁▁▁▁▁▁▁▂,█▁▁▁▁▁▁▁▁▁
17e13cd3-91f2-4098-b847-c0f3e0a08ddc,0.59,0.0,1.62,0.16,█▁▁▁▁▁▁▁▁▁,▆▂▁▁▁▁▁▁▁▂,█▁▁▁▁▁▁▁▁▁
073e3fa3-2cc0-4312-86c1-65baf56ac86d,0.04,0.0,0.13,0.0,█▁▁▁▁▁▁▁▁▁,█▁▁▁▁▁▁▁▁▁,█▁▁▁▁▁▁▁▁▁
ec5dad43-ee0e-4980-aeca-8b116c0a281e,0.04,0.0,0.13,0.0,█▁▁▁▁▁▁▁▁▁,█▁▁▁▁▁▁▁▁▁,█▁▁▁▁▁▁▁▁▁
```

**example 3: getting the data for one VM in shell format**

```console
$ osidle --format shell --include-eval-data-graph --from 2w -i 710477c0-1dc6-41a7-82ea-278eca3f209a
ID_0=710477c0-1dc6-41a7-82ea-278eca3f209a
disk_score_0=10.0
cpu_score_0=4.38
nic_score_0=7.87
overall_0=7.42
disk_graph_0=▁▁▁▁▁▁▁▁▁█
cpu_graph_0=▁▁▁▁█▁▁▁▁▁
nic_graph_0=▁▁▁▁▁▁▁█▁▁
stats_disk_min_0=40671.65060497562
stats_disk_max_0=2994386.165308571
stats_disk_mean_0=47952.98713800534
stats_disk_median_0=43392.13966196343
stats_cpu_min_0=0.3941215875377581
stats_cpu_max_0=1.0847229915652363
stats_cpu_mean_0=0.4047715705165909
stats_cpu_median_0=0.40384832936874704
stats_nic_min_0=2730.3094882034097
stats_nic_max_0=207074.88944415632
stats_nic_mean_0=3186.7576530164206
stats_nic_median_0=2967.3510363628907
```

