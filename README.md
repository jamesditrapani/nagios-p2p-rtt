# Nagions P2P RTT
Python check plugin for Nagios/Icinga to monitor latency across a point-to-point interface. 

## How
Using the PyATS Framework, this check logs into the given device, determines remote and local addressing based on the Interface passed, polls the remote end with a directly connected Source & outputs Nagios PERF data for graphing/monitoring purposes.

## Installation
Clone directly from Github into your `plugins-contrib` directory:
```bash
git clone https://github.com/jamesditrapani/nagios-p2p-rtt
```

**Please ensure you pip install -r requirements.txt in the environment your Icinga/Nagios workers will execute from**

## Setup
Setup is fairly simple and only requires the modification of the username/password combination used to access the network devices. The credentials are stored within `check_p2p_rtt.py` in the `__init__()` function. Modify the schema with your credentials:

```python
self.device: {
  'ip': self.ip,
  'protocol': 'ssh',
  'type': 'router',
  'os': self.os,
  'username': 'xxxx',
  'password': 'xxxx',
  'enable_password': 'xxxx'
}
```

## Usage
### Args
* **--interface**: Interface to poll across, used to determine local/remote IPs of the P2P Link (Interface must be a /31 or /30!). Required field. 
* **--device**: Hostname of the device. This must match the hostname configured or a PyATS Unicon Error will be thrown. Required field.
* **--os**: Network OS running on the device (junos, iosxe, iosxr, eos). Used to Parse response data. Required field.
* **--mgmtip**: IP used to create a SSH session. Required field.
* **--count**: How many ICMP Echos are sent across the link. Not required, default = 10.

### Icinga/Nagios
Define a check command in your Icinga Commands configuration similar to below:
```bash
object CheckCommand "check_ptp_rtt" {
  import "plugin-check-command"
  command = [ PluginContribDir + "/check_p2p_rtt.py" ]
  arguments = {
    "-d" = {
      value = "$name$"
      description = "Device Hostname"
      required = true
    }
    "-i" = {
      value = "$interface$"
      description = "Interface"
      required = true
    }
    "-o" = {
      value = "$nos$"
      description = "Devices OS"
    }
    "-m" = {
      value = "$address$"
      description = "Devices Management IP"
    }
  }
  vars.nos = "$host.vars.nos$"
  vars.name = "$host.name$"
}
```

And apply a service similar to the below to the host you wish to check, you need to ensure that the vars are passed to the check:
```bash
apply Service "check_ptp_rtt-core1.x-TenGigabitEthernet0/0/1" {
  import "generic-service"
  check_command = "check_ptp_rtt"
  display_name = "PTP Latency - TenGigabitEthernet0/0/1"
  vars.enable_perfdata = true
  enable_perfdata = true
  vars.nos = host.vars.nos
  vars.hostname = host.name
  vars.interface = "TenGigabitEthernet0/0/1"
  assign where host.name == "core1.x"
}
```

### CLI
```bash
[root@mon3][~]
/etc/icinga2/plugins-contrib/check_p2p_rtt.py -i TenGigabitEthernet0/0/1 -d core1.x -o iosxe -m 192.168.1.2
OK: Packet loss = 0%, RTA = 15ms | rtmin=15;;;; rtavg=15;;;; rtmax=16;;;; pl=0;;;;
```

## Release History
* 0.0.1
    * Initial Release

## Meta

James Di Trapani – [@jamesditrapani](https://twitter.com/jamesditrapani) – james[at]ditrapani.com.au

[https://github.com/jamesditrapani/](https://github.com/jamesditrapani/)


## License
[GPL 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
