# -*- coding: utf-8 -*-
"""
Examine minical data
"""
import time
import sys
from pylab import *
from numpy import array

logfile = "/usr/local/RA_data/logs/dss43/Krx43_control.log"

logfd = open(logfile,'r')
logdata = logfd.readlines()
logfd.close()

def find_next_minical(logdata,current_index):
  found = False
  index = current_index
  while not found:
    if logdata[index][:15] == "Minical data at":
      return index
    else:
      index += 1
    if index == len(logdata):
      return None

def get_minical_index():
  done = False
  index = 0
  indices = []
  while not done:
    new_index = find_next_minical(logdata,index)
    if new_index != None:
      if new_index < 1131:
        pass
      else:
        indices.append(new_index)
      index = new_index+1
    else:
      break
  return indices

def get_minical_data(logdata,index):
  P = {}
  ptr = index
  start_time = time.strptime(logdata[ptr].strip()[16:])
  ptr += 1
  # Get the raw data
  readings = ['load','sky','load+ND','sky+ND']
  P = {}
  for item in readings:
    P[item] = {}
  while logdata[ptr][:3] == "Ch.":
    feed = int(logdata[ptr][3])
    parts = logdata[ptr].strip().split()
    reading = parts[1].strip(':')
    try:
      readings.index(reading)
    except:
      pass
    else:
      P[reading][feed] = float(parts[2])
    ptr += 1
  # get the processed data
  end_time = time.strptime(logdata[ptr].strip()[19:])
  ptr+=1
  results = {}
  # process four feeds/polarizations
  for i in range(4):
    feed = int(logdata[ptr].strip().split()[1])
    ptr += 1
    # process three result tuples
    for j in range(3):
      parts = logdata[ptr].strip().split(':')
      #print parts
      if results.has_key(parts[0]):
        pass
        #print "'results' has key",parts[0]
      else:
        #print "'results' does not have key",parts[0]
        results[parts[0]] = {}
      #print results
      results[parts[0]][feed] = eval(parts[1])
      ptr += 1
    ND = float(logdata[ptr].strip().split(':')[1])
    ptr += 1
    nonLin = float(logdata[ptr].strip().split(':')[1])
    ptr += 1
  return start_time,P,end_time,results,ND,nonLin

indices = get_minical_index()
print len(indices),"minicals found"
for i in range(len(indices)):
  print '%3d: %s' % (i,logdata[indices[i]].strip())
index = int(raw_input("Select minical by number (-1 to quit): "))
if index < 0:
  sys.exit(0)
else:
  stuff = get_minical_data(logdata,indices[index])
heading =  time.asctime(stuff[0])+" to "+time.asctime(stuff[2])
x = []
y = []
FeedName = {}
FeedName[1] = "Feed 1 Pol 1"
FeedName[2] = "Feed 1 Pol 2"
FeedName[3] = "Feed 2 Pol 1"
FeedName[4] = "Feed 2 Pol 1"
for feed in range(1,5):
  x = stuff[3]['Linear Ts'][feed]
  y =array(stuff[3]['Corrected Ts'][feed]) \
           - array(stuff[3]['Linear Ts'][feed])
  plot(x,y,'-o',label=FeedName[feed]
                +" T(sky) = "
                + ("%5.2f" % (stuff[3]['Corrected Ts'][feed][0])))
  title(heading)
  xlabel("Linear Tsys (K)")
  ylabel("Corrected - Linear Tsys (K)")
  print "Feed",feed,"T(sky) = ",stuff[3]['Corrected Ts'][feed][0]
legend(loc="upper center")
grid()
show()