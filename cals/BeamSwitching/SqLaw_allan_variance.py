# -*- coding: utf-8 -*-
from pylab import *
import time
import logging

from DateTime import UnixTime_to_MPL
from Math.statistics import allan_variance
from text import select_files
from AV_common import *

segment = {
  "Load1": [ 2097, 8774],
  "Load2": [ 8903, 9451],
  "Sky1":  [ 9480,10161],
  "Sky2":  [10290,17677]}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

datadir = select_files("SqLaw*")
logger.debug("Data directory is %s", datadir)
files = select_files(datadir+"/*")
logger.debug("Files to be processed: %s", files)

fd = open(files)
lines = fd.readlines()
fd.close()

mpltime = []
IF = {1: [], 2: []}
data_groups = {}
for line in lines:
  data = line.strip().split()
  seconds = float(data[0])
  mpltime.append(UnixTime_to_MPL(seconds))
  int_sec = int(seconds)
  fracsec = seconds % 1
  timestruct = time.gmtime(seconds)
  timestring = time.strftime("%Y-%j %H:%M:%S",timestruct)+str(fracsec)
  IF[1].append(float(data[2]))
  IF[2].append(float(data[3]))
IF[1] = array(IF[1])
IF[2] = array(IF[2])
data_groups[1] = excise_load_transitions(IF[1], minsize=100)
data_groups[2] = excise_load_transitions(IF[2], minsize=100)
logger.info("Data groups: %s", data_groups)

figno = 0
fig = {}

for seg in segment.keys():
  figno += 1; fig[figno] = figure(figno)
  plot_date(mpltime[segment[seg][0]:segment[seg][1]],
            IF[1][segment[seg][0]:segment[seg][1]], '.', label="IF 1")
  plot_date(mpltime[segment[seg][0]:segment[seg][1]],
            IF[2][segment[seg][0]:segment[seg][1]], '.', label="IF 2")
  title(seg+" Raw Square Law Detector")
  ylabel("Volts")
  fig[figno].autofmt_xdate()
  legend(numpoints=1)
  grid()

  figno += 1; fig[figno] = figure(figno)
  smv = 25
  boxcar = smv*[0]+smv*[0.04]+smv*[0]
  smoothed1 = convolve(IF[1],boxcar,mode='same')
  plot_date(mpltime,smoothed1,'-',label="IF 1")
  smoothed2 = convolve(IF[2],boxcar,mode='same')
  plot_date(mpltime,smoothed2,'-',label="IF 2")
  grid()
  legend()
  title("Smoothed Square Law Detector")
  ylabel("Volts")
  fig[figno].autofmt_xdate()

  figno+=1; fig[figno] = figure(figno)
  first = segment[seg][0]
  last  = segment[seg][1]
  numpts = last-first
  start = mpltime[first]
  stop  = mpltime[last]
  timestep = (stop-start)*86400/numpts
  ints1,alvar1 = allan_variance(IF[1][first:last])
  loglog(array(ints1)*timestep, alvar1, label="IF 1")
  ints2,alvar2 = allan_variance(IF[2][first:last])
  loglog(array(ints2)*timestep, alvar2, label="IF 2")
  grid()
  legend()
  xlabel("Integration time (sec)")
  ylabel("Variance (V$^2$)")
  title(seg+" Allan variance")
  show()
