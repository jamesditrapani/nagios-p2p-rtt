#!/usr/bin/env python
"""
  check_p2p_rtt -

    Nagios check to graph minimum, average and max ICMP RTT across a point-to-point interface using the PyATS Framework.

    Requires:
    - interface: What interface is the check going to pill across?
    - os: What is the device OS, this is required as it helps us determine the correct parsers.
    - device: Hostname of the device.
    - mgmtip: IP the device can be reached via SSH

"""

__author__ = 'James Di Trapani <james@ditrapani.com.au>'

from genie.testbed import load

from unicon.core.errors import SubCommandFailure, ConnectionError

import re, time, sys, ipaddress, argparse

class CriticalPingCheck(Exception): pass
class WarningPingCheck(Exception): pass

class PingCheck():
  """

    Works out the local & remote IP on the given P2P interface based on subnet configured (Must be /30 or /31). 
    Polls with correct source and outputs response data in correct Nagios perfdata format with corresponding exit codes.

    https://nagios-plugins.org/doc/guidelines.html

  """
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
    structure = {'devices': {
        self.device: {
          'ip': self.ip,
          'protocol': 'ssh',
          'type': 'router',
          'os': self.os,
          'username': 'xxxx',
          'password': 'xxxx',
          'enable_password': 'xxxx'
        }
      }
    }
    testbed = load(structure)
    self.terminal = testbed.devices[self.device]
    try:
      self.terminal.connect(init_exec_commands=[], init_config_commands=[], log_stdout=False)
    except ConnectionError:
      raise CriticalPingCheck(f'SSH timed out while trying to connect to {self.device}')

  def logic(self):
    local, remote = self.get_ip(self.interface)
    self.test_ping(local, remote)

  def get_ip(self, interface):
    int_info = self.terminal.parse(f'show interfaces {interface}')
    ip_info = int_info[list(int_info.keys())[0]]['ipv4']

    # Quick check for secondary IPs
    if len(ip_info) > 1:
      raise WarningPingCheck(f'Interface {interface} on {self.device} has more than 1 subnet configured!')

    key = list(ip_info.keys())[0]

    if ip_info[key]['prefix_length'] not in ['31', '30']:
      raise WarningPingCheck(f'Prefix Length for {key} is not a /31 or /30')

    try:
      local = ip_info[key]['ip']
      network = ipaddress.ip_network(key, strict=False)
      remote = [ip for ip in network.hosts() if str(ip) != local][0]
      return local, remote
    except Exception as e:
      raise CriticalPingCheck(e) from e

  def test_ping(self, source, destination):
    try:
      result = self.terminal.ping(src_addr=source, addr=destination, extd_ping='yes')
      match = re.search(r'round-trip min\/avg\/max = (?P<min>\d+)\/(?P<avg>\d+)\/(?P<max>\d+) ms', result)
      rmin, ravg, rmax = match.group('min'), match.group('avg'), match.group('max')
      print(f'OK: ICMP Echo/Echo Reply Success | rtmin={rmin};;;; rtavg={ravg};;;; rtmax={rmax};;;;') 
      sys.exit(0)
    except SubCommandFailure as e:
      # SubCommandFailure thrown when output fails
      raise CriticalPingCheck(f'P2P ICMP Check to {destination} from {source} Failed!')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--interface', required=True)
  parser.add_argument('-d', '--device', required=True)
  parser.add_argument('-o', '--os', required=True)
  parser.add_argument('-m', '--mgmtip', required=True)
  args, unknown = parser.parse_known_args()

  try:
    run = PingCheck(
      device = args.device,
      interface = args.interface,
      ip = args.mgmtip,
      os = args.os
    )
    run.logic()
  except CriticalPingCheck as e:
    print(f'CRITICAL: {e}')
    sys.exit(2)
  except (WarningPingCheck, Exception) as e:
    print(f'WARNING: {e}')
    sys.exit(1)

  sys.exit(3)
