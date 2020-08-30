# -*- coding: utf-8 -*-
from pylab import *
import logging

from Radio_Astronomy import dBm_to_watts
from Math.statistics import allan_variance
from text import select_files
from AV_common import *

segment = {"Load": [99300,134600], "Sky": [135307, 158756]}

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

datadir = select_files("ACME*")
logger.debug("Data directory is %s", datadir)
files = select_files(datadir+"/*")
logger.debug("Files to be processed: %s", files)


fig = {}; figno = 0
pwr_dBm = {}
pwr_W = {}
figno += 1; fig[figno] = figure(figno)
data_groups = {}
for f in files:
  fd = open(f,'r')
  rawdata = fd.readlines()
  fd.close()
  samples = []
  for line in rawdata:
    parts = line.strip().split(',')
    timestr = parts[0]
    second = datestr2num(timestr)
    data = parts[1:]
    numdata = len(data)
    for index in range(numdata):
      datetime = second + float(index)/numdata/86400
      samples.append([datetime,float(data[index])])
  pwr_dBm[f] = array(samples)
  t = pwr_dBm[f][:,0]
  d = pwr_dBm[f][:,1]
  data_groups[f] = excise_load_transitions(d)
  pwr_W[f] = dBm_to_watts(pwr_dBm[f][:,1])
  plot_date(t,d,'.',label=TeXify(f))
legend(loc='lower right', numpoints=1)
grid()
ylabel("Power (dBm)")
fig[figno].autofmt_xdate()
title("Raw Data")
logger.info("Data groups: %s", data_groups)

for seg in segment.keys():
  figno += 1; fig[figno] = figure(figno)
  smv = 10
  boxcar = smv*[0]+smv*[1/float(smv)]+smv*[0]
  for f in files:
    t = pwr_dBm[f][segment[seg][0]:segment[seg][1],0]
    d = pwr_dBm[f][segment[seg][0]:segment[seg][1],1]
    plot_date(t,d,'-',label=TeXify(f))
  ylabel("Power (dBm)")
  grid()
  legend(loc='center right', numpoints=1)
  fig[figno].autofmt_xdate()
  title(seg+" data only")

  figno += 1; fig[figno] = figure(figno)
  for f in files:
    timestep = (pwr_dBm[f][1,0]-pwr_dBm[f][0,0])*86400
    pwr = pwr_W[f][segment[seg][0]:segment[seg][1]]
    ints,alvar = allan_variance(pwr)
    loglog(array(ints)*timestep, alvar,label=TeXify(f))
  grid()
  legend(loc="lower left")
  xlabel("Integration time (sec)")
  ylabel("Residual variance (W$^2$)")
  title("Allan variance of "+seg)

  figno += 1; fig[figno] = figure(figno)
  difs = (pwr_W[files[0]][segment[seg][0]:segment[seg][1]]
         -pwr_W[files[1]][segment[seg][0]:segment[seg][1]])
  ints,alvar = allan_variance(difs)
  loglog(array(ints)*timestep, alvar)
  grid()
  title(seg+" Power Differenced")
  xlabel("Integration time (sec)")
  ylabel("Variance (W$^2$)")
  show()