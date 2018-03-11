#!/usr/bin/python


# -*- Python -*-

#*****************************************************************
#
#
# WARRANTY:
# Use all material in this file at your own risk. Hiranmoy Basak
# makes no claims about any material contained in this file.
#
# Contact: hiranmoy.iitkgp@gmail.com


#!/usr/bin/python
import os
import sys
import time
import datetime
import commands

from urllib import urlopen
from urllib import quote

import settings


gDebugMode = 1
gLogFile = "/home/ethos/gpu_crash.log"
gRigName = commands.getstatusoutput("cat /etc/hostname")[1]
gLocName = commands.getstatusoutput("/opt/ethos/sbin/ethos-readconf loc")[1]
disconnectCount = 0
waitForReconnect = 1
firstError = 0

def DumpActivity(dumpStr):
  print dumpStr
  pLogFile = open(gLogFile, "a")
  pLogFile.write("%s @ %s\n" % (dumpStr, str(datetime.datetime.now())))
  pLogFile.close()

def RebootRig():
  miner_hashes = map( float, commands.getstatusoutput("cat /var/run/ethos/miner_hashes.file")[1].split("\n")[-1].split() )
  miner_hashes = [ int(x) for x in miner_hashes ]
  DumpActivity("Rebooting (" + str(miner_hashes) + ")")
  uptime = int(float(commands.getstatusoutput("cat /proc/uptime")[1].split()[0]))
  m, s = divmod(uptime, 60)
  h, m = divmod(m, 60)
  msg = quote(str(gLocName) + " Reboot uptime " + str(h) + ":" + str(m) + ":" + str(s))
  if (settings.telegram == 1):
    urlopen("https://api.telegram.org/"+str(settings.telegramAPI)+"&text=" + msg).read()
  os.system("sudo hard-reboot")
  os.system("sudo reboot")

# wait till 3 minutes runtime, so we can be sure that mining did start
while( float(commands.getstatusoutput("cat /proc/uptime")[1].split()[0]) < 3 * 60):
  time.sleep(5)
  
numGpus = int(commands.getstatusoutput("cat /var/run/ethos/gpucount.file")[1])
if (numGpus != settings.GpuNum):
  RebootRig()

# start checking
while 1:
  miner_hashes = map( float, commands.getstatusoutput("cat /var/run/ethos/miner_hashes.file")[1].split("\n")[-1].split() )
  miner_hashes = [ int(x) for x in miner_hashes ] # have them without comma
  numRunningGpus = len(filter(lambda a: a > 0, miner_hashes))
  CPULoad = float(commands.getstatusoutput(sys.path[0] + "/sysload.php")[1])

  if (numRunningGpus != numGpus or CPULoad > 3):
    if (numRunningGpus <= 2):
      waitForReconnect = 1
    if (waitForReconnect == 1):
      # all GPUs dead. propably TCP disconnect / pool issue
      # we wait 12 times to resolve these issues. this equals to 3 minutes. most likely appears with nicehash.
      disconnectCount += 1
      if (disconnectCount > 12):
        DumpActivity("Waiting for hashes back: " + str(disconnectCount))
        RebootRig()
        break
      else:
        time.sleep(15)
        continue
    if (firstError == 1):
      RebootRig()
      break
    else:
      firstError = 1
      time.sleep(15)
  else:
    waitForReconnect = 0
    disconnectCount = 0
    firstError = 0

  time.sleep(15)


