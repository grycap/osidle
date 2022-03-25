# OpenStack IDLE VM Detector (osidle)
This project tries to analyze the usage of the different servers (Virtual Machines) in an OpenStack deployment.

Using `osidle` it is possible to obtain a list of all the servers in OpenStack, along with a score of how much they are used.

In the next example:

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

After each VM ID, the following information is available:
- Overall score: the average score of usage of the VM in the period. It is the mean of the usage scores of the VM, and it is between 0 and 10.
- CPU score: the score for the usage of the CPU in the period. 10 would mean that the VM uses 100% of the CPU, while 0 would mean that the VM is not using any CPU.
- Disk score: the score for the disk usage in the period. 10 would mean that the VM uses 100% of the disk, while 0 would mean that the VM is not using any disk.
- NIC score: the score for using the network in the period. 10 would mean that the VM uses 100% of the NIC, while 0 would mean that the VM is not using any NIC.
- CPU graph: is a chart that represents the usage of the CPU in the period. The chart is divided into 10 parts (0-10%, 10-20%, ..., 90-100%), and each part represents the percentage of time the CPU was using the corresponding percentage.
- Disk graph: is a chart that represents the usage of the disk in the period.
- NIC graph: is a chart that represents the usage of the NIC in the period.

Using this information, it is possible to identify those VMs that are a candidate to be powered off due to the lack of usage.

## Motivation

The motivation for this project is that in a private cloud, users usually __launch VM and forget that they have been started__. This happens mainly because the users are not billed for the usage of private resources. But for the owner and the sysadmins, these _"launch-and-forgotten"_ servers are a headache: 1st because the resources are finite (private clouds are not Amazon's AWS clouds), and 2nd because using the resources prevent from rebooting the hosting servers (thus interrupt maintenance of the facilities).

Moreover, according to the evidence, __users tend to overestimate the number of resources their servers need__ to run. And this is especially true when the resources are "free" (i.e. do not cost money). Instead, when a user starts a server in Amazon AWS, he tries to control the resources better because more resources mean more money. 

Amazon AWS will not complain about paying for extra unneeded resources (Amazon wants to get your money, and if you asked to spend more money... it is your choice). But the sysadmin wants to have enough resources for its users without buying new resources.

And as a last thought, the sysadmins also offer a reduced set of flavours for the VMs that do not cover all the use cases. So maybe a user needs an amount of memory that is only offered along with 8 cores, but the user may only need 2 cores. In this case, the sysadmin is responsible for __overproviding resources for the VM flavours__. If many VMs face this case, the sysadmin should re-consider the resources for each flavour or even create new flavours.

As a summary, the use cases for this project are
1. to try to detect which servers are candidates to be powered off because they are not used.
1. to try to detect overestimated servers, to try to resize them
1. to try to detect the lack of flavours with the appropriate amount of resources

## Levels of analysis

`osidle` implements a number of different levels of analysis: `softer`, `soft`, `medium` and `hard`. Using each of the levels, it is possible to obtain more information about the VMs and the infrastructure.

The different levels of analysis correspond to the metrics used to evaluate the VMs.

- The current version of `osidle` consider the following levels of usage for the CPU:
    - `soft` and `softer`: consider that the VM have only 1 core. That means that the usage of the cores is summed up (see ["Evaluating the CPU"](#evaluating-the-cpu)).
    - `medium`: consider that the VM has an amount of cores that matches the maximum CPU requested by the VM (see ["Evaluating the CPU"](#evaluating-the-cpu)).
    - `hard`: consider that the VM has the actual amount of cores.

- For the case of the disk and the network, the current version of `osidle` considers the following levels of usage (see ["Evaluation of idle resources"](#evaluation-of-idle-resources)):
    - `soft` and `softer`: consider that the epsilon for forward-sharing of data is 0.85.
    - `medium`: consider that the epsilon for forward-sharing of data is 0.75.
    - `hard`: consider that the epsilon for forward-sharing of data is 0.5.

> `osidle` also implements an alternate method for evaluation of the VMs, but it is not used in the current version (it is under development).

### Discussion

A VM that has 4 cores but is using only 1 core at 100% in a period should be considered as "used". If using a _strict_ analysis, the VM would obtain a CPU score of 2.5. And if it is evaluated along with a low usage of disk and NIC, it would obtain an overall score under 1. As a result, it would be considered as a candidate to be powered off.

But the decision of having 4 cores available for that VM is not made by the user. But the user may have been forced to get such an amount of cores because of the flavours available. Maybe the user wanted more memory and less cores, but he could not find any suitable flavour. This is why the sysadmin should re-evaluate the flavours.

# Workflow

This server has two parts:
1. A __monitor__ that periodically contacts OpenStack and gets the metrics for the usage of the servers
2. An application that can be used to __analyze the data__
3. An application to discard old data

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
# By default, osidle monitor will store the raw data obtained for each VM. Changing this option allows to store only the data that will use osidle (default: True, to store the raw data)
STORE_RAW_DATA = True
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
* --level: the hardness of the analysis to consider that a VM is used. Possible values: `softer`, `soft`, `medium` or `hard`. Default: `soft`
    > _Note:_ In the `hard` level a VM is considered fully used (i.e. the score of usage in all metrics is 10) if it is using 100% of CPU all the time and it is using 100% of transference and disk (according to the thresholds) all the time.
* --custom-file: a file containing custom rules to be used in the analysis. Default: `None`
    > _Note:_ The file contains one line per specific rules to apply to a VM in the format `<vm id>:<command line parameters>`. The command line parameters used to run the application will be considered the default ones, and the parameters passed in the file `--custom-file` option will be added to them.
* --verbose, --verbose-more, --version, --help, --quiet: are the common well-known flags for many applications. 

#### Levels of analysis

There are 4 levels of analysis:
- `hard`: this type of analysis is not advised for most common platforms. It considers that a VM is fully used if it is using 100% of CPU all the time and it is using 100% of transference and disk (according to the thresholds) all the time, and considers a low `epsilon` for forward-sharing of data in disk and network analysis.
- `medium`: This analysis considers that a VM is fully used if it was using 100% of the cores requested at maximum (the recommended amount of cores), and considers a medium `epsilon` for forward-sharing of data in disk and network analysis.
- `soft`: This analysis considers that a VM is fully used if it was using 100% of a single core. It also considers a high `epsilon` for forward-sharing of data in disk and network analysis, so that the analysis is not too sensitive to the VM's usage. This is the default value.
- `softer`: Is the same as `soft` but it overweights the maximum score to calculate the overall score. The purpose of this calculation is to reward a specific VM profile: e.g. if a VM was intended for CPU intensive tasks, it will have a higher score in CPU than in other metrics. The same is valid for disk-intensive VMs or network-intensive VMs.

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

### Utilities

`osidle-packdb` is included, to reduce the size of the database by removing old entries, and reducing the size of the existing data.

The data can be reduced because the data stored in the database is the raw data produced by OpenStack. This is made in this way, just in case that the data needs to to be inspected. `osidle-packdb` removes the unneeded fields from the data.

On the other side, the analysis of the data may have a sense for a period of time. `osidle` has no purpose of being an accounting tool, and so it is advisable to discard the registries that would fall out of the analysis period, for sure. The `osidle-packdb` utility can be used to remove the data that is not needed anymore.

Please refer to the documentation of the `osidle-packdb` command for more details (i.e. `--help` option).

Some of the options of the `osidle-packdb` command are:

* --quiet: use the quiet mode
* --yes: answer yes to all questions
* --no-backup: do not backup the database before packing it (have in mind that the database will be modified and the changes cannot be undone)
* --backup-filename: name of the file in which to store the backup of the database. If not provided, a new file will be created using a timestamp.
* --overwrite: overwrite the backup file if it already exists
* --keep-from: discard any sample before this date. 
    > _Note:_ It is possible to use the following format: `[<reference>-]count[<unit>]`. Where reference is one of `now`, `begin`, `end`, `lastweek`..., and count is an integer. The unit is one of `s`, `m`, `h`, `d`, `w`, `M`, `y`. For example, `--keep-from=now-1M` will discard the samples taken before 1 month ago.
* --keep-to: discard any sample after this date. The format is the same than `--keep-from` parameter. 
* --database: the database file to use (Default: /var/lib/osidled/osidled.db)
* --minimize: remove the unneeded data from the entries in the database

## Evaluation of idle resources

Evaluating whether a VM is idle or not is a complex task from the sysadmin's point of view. The only one that knows if the VM is used is the user that is using it. But the sysadmin needs to know if the VM is idle or not to manage the resources better.

> This section pretends not to be a complete guide to evaluating idle resources. It is just a description of how it is done in `osidle`.

`osidle` obtains the information from the data provided by the hypervisor: the accumulated disk, cpu and nic usage of the VM from the last time that it was powered on. To be able to analyze the variations of the usage of the VM, the hypervisor is asked about the resources consumed by each VM, at different times (each 600 seconds by default). Then, the data is linearized by subtracting the previous value from the current one. And this is how `osidle` knows about the fluctuations in the usage of the resources in the time.

### Evaluating the CPU
Evaluating the CPU may be somehow easy, because it is easy to obtain the percentage of used CPU. Then if we consider a residual amount of CPU dedicated to the processes of the OS, we may estimate the percentage of CPU actually used by the VM.

But this may not be enough by itself, because most VMs have multiple cores and so, the usage of the CPU tend to be very low for most use cases. As an example, consider python applications, which are mostly sequential. A fully used VM will use less than 200% of the CPU (while having 800% available for a 8-core VM). That would mean that the VM is used at less than 25% of its capacity. And if we consider also a low usage of the disk and the network, the VM may be used at less than 10% of its capacity.

Requiring 8 cores in the previous example may be a bad decission of the user who requested the VM. But maybe the user had no choice if the application needed an amount of memory that is not available for flavors with less than 8 cores. In such case, the user was somehow forced to use a VM with 8 cores. So the VM should not be penalized for this.

At the end, strictly speaking, the VM was using 25% of its capacity... _but it is used_. Maybe the sysadmin should create a new flavor with less cores and suggest the user to resize the VM to use it. But the VM should not be a candidate to be powered off.

`osidle` enables to evaluate the CPU usage considering that the VM has a different number of cores. So, depending on the level of analysis, the actual number of cores will be considered as if the VM had a different number of cores:
- `hard` level: the number of cores is considered as if the VM had the same number of cores as the flavor it was created with.
- `medium` level: the number of cores is considered as if the VM had the number of cores that matches the amount of CPU requested by the VM in the period of analysis. For example, if the VM had a flavor with 8 cores, and the VM requested a CPU of 2.5, the number of cores will be considered as if the VM had 3 cores.
- `soft` and `softer` levels: the number of cores is considered as if the VM had 1 single core. So that an aggregated amount of usage of the CPU of more than 100% will be considered as a full usage of the VM.

### Evaluating the disk and the network usage
Evaluating this kind of resources is more complex than the CPU. While evaluating the CPU had the approach of evaluating the percentage of CPU used, evaluating the disk and the network usage had to consider the amount of data that was transferred and not the percentage of usage of these resources.

Let's focus on the disk, but the analysis is the same for the network. 

`osidle` considers a data rate for the disk (reading and writting), and establishes a threshold that would mean that the VM is "very used" (i.e. the maximum score of disk usage). 

The problem is that a VM may use a lot of disk in a second, just because the disk is very fast. If the disk was slow, it would be also considered as "very used" for a longer time. Then the second VM is being rewarded for its usage of the disk, but not for being used for a longer time. And it happens because of saturation of the threshold.

`osidle` tries to mitigate this kind of unfairness by applying a filter to the transference of data, so that excess of disk usage over the saturation threshold is considered for the next period of analysis in a fraction (called `epsilon` during this document).

## Using `osidle` to re-think the flavors 

TBD

## Real world example

Here it is included an script that analyzes the usage of the VMs in a openstack platform, and sends e-mails to the users to warn them about the VMs that are not used.

The script is called `osidle-notify` and it is included in `/etc/osidled/` folder. In our premises, it is installed in the `/usr/sbin` directory, and it is executed by cron weekly (*) the credentials have to be updated to the openstack deployment.

```bash
#!/bin/bash
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
function send_an_email() {
    local FROM_MAIL="adminserver@my.server.com"
    local MAIL_SERVER=smtp.my.server.com
    local EMAIL="${2:-adminserver@my.server.com}"
    local TEXT="$1"
    local SUBJECT="${3:-[osidle] idle VM detected}"

    # send a copy to the admin
    echo "$TEXT" | sendEmail -t "$EMAIL" -bcc "$ADMIN_MAIL" -u "$SUBJECT" -s "$MAIL_SERVER" -f "$FROM_MAIL" -o message-charset=utf-8
}

function vm_url() {
    while [ $# -gt 0 ]; do
            echo "https://openstack.my.server.com/horizon/admin/instances/$1/detail"
            shift
    done
}

# These are variables for openstack command
export OS_PROJECT_DOMAIN_NAME=Default
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=ADMIN_PASSWORD
export OS_AUTH_URL=https://openstack.my.server.com:5000/v3
export OS_IDENTITY_API_VERSION=3
export OS_IMAGE_API_VERSION=2
export OS_AUTH_TYPE=password

# Prepare a filename to store the analysis (I want to be unique to keep it)
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ANALISIS_FNAME="${TIMESTAMP}_osidle.csv"

# Analyze the platform
osidle --format csv --from 2w -r --sort -O $ANALISIS_FNAME --summarize --under-threshold 1 -q
if [ "$?" != "0" ]; then
        send_an_email "an error occurred when executing osidle"
        exit 1
fi

# Get the list of VMs which are candidate to be powered off
MAQUINAS="$(cat "$ANALISIS_FNAME" | tail -n +2 | awk -F',' '{print $1}')"

# Retrieve the list of users in openstack
_LIST_ID=()
_LIST_USER=()
_LIST_EMAIL=()
n=0
USERLIST="$(openstack user list -f csv -c ID -c Name -c Email --long | tail -n +2)"
while IFS=',' read _ID _USER _EMAIL; do
    _LIST_ID[$n]="${_ID:1:-1}"
    _LIST_USER[$n]="${_USER:1:-1}"
    _LIST_EMAIL[$n]="${_EMAIL:1:-1}"
    n=$((n+1))
done <<< "$USERLIST"

# Now retrieve the owner for the detected VMs and send an email
n=0
_SERVER_IDS=()
_SERVER_REST=()
for _ID in $MAQUINAS; do
    eval "$(openstack server show "$_ID" -f shell)"
    _USER=$user_id
    for ((i=0;i<${#_LIST_ID[@]};i++)); do
        if [ "${_LIST_ID[$i]}" == "$user_id" ]; then
            _USER="${_LIST_USER[$i]}"
            _EMAIL="${_LIST_EMAIL[$i]}"
            break
        fi
    done

    eval "$(osidle --format shell -i "$_ID" --full-report -q)"
    CPU_MEAN="$(echo "$stats_cpu_mean_0 100" | awk '{printf "%f", $1*$2}')"
    TEXTO="
Dear user,

We have detected that your VM $_ID has not been idle during the past 2 weeks. The VM was created on $created

The usage profile is the next:

CPU: $cpu_graph_0; mean usage: ${CPU_MEAN}% score: $cpu_score_0/10 (*)
DISK: $disk_graph_0; score: $disk_score_0/10 (*)
NETWORK: $nic_graph_0; score: $nic_score_0/10 (*)

(*) the chart represents (from left to right) the time in the period that the VM has been using each resource 0-10%, 10-20%, ..., 90-100%.

Please consider to power off the VM if it is not used, to share the resources with other VMs.

You can check the details of the VM at:
$(vm_url $_ID)

Thank you for your attention."
    if [ "$_EMAIL" == "" ]; then
        TEXTO="
[user $_ID ($_USER) has not an email set]

$TEXTO"
    fi
    send_an_email "$TEXTO" "$_EMAIL"
done

# Send the summary to the admin
send_an_email "
Hi,

some VMs have not been idle during the past 2 weeks:

$(vm_url $MAQUINAS)

Regards"
```