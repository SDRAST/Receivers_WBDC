"""
Calibrate PIN diode attenuators

This is for the canonical TAMS  22F1EL, 22F1HU, 22F2EU and 22F2HL configuration
which is 1: F1P1 21-22, 2: F1P2 22-23, 3: F2P1 22-23 and 4: F2P2 21-22, shown
here::
                         .---.
       .----.      +--I--|\ /|--IF1--PM1
 R1E --|----|--P1--M     | X |
       |    |      +--Q--|/ \|--IF2
       |    |            '---' 
       |    |            .---.
       |    |      +--I--|\ /|--IF1
 R1H --|----|--P2--M     | X |
       '----'      +--Q--|/ \|--IF2--PM2
                         '---'
                          
                         .---.
       .----.      +--I--|\ /|--IF1--PM3
 R2E --|----|--P1--M     | X |
       |    |      +--Q--|/ \|--IF2
       |    |            '---' 
       |    |            .---.
       |    |      +--I--|\ /|--IF1
 R2H --|----|--P2--M     | X |
       '----'      +--Q--|/ \|--IF2--PM4
                         '---'
So the WBDC2 configuration is::
* cross-over switch (not shown) uncrossed (default).
* polarization hybrids bypassed (default).
* IF hybrids crossed (default).
"""
import logging
import numpy as NP
import time
from pylab import *
from scipy.interpolate import interp1d
import dill as pickle

from support.pyro import get_device_server

from MonitorControl import ClassInstance
from MonitorControl.Receivers.WBDC.WBDC2.WBDC2hwif import WBDC2hwif

module_logger = logging.getLogger(__name__)

def get_atten_IDs(filename):
  """
  Read data from a comma-separated data file

  Row 1 - reference (input) power level
  Row 2 - bias voltage
  Row 3 - total resistance in control voltage circuit
  Row 4 - serial number
  Row 5 - Receiver chain
  Row 6 - Frequency and polarization of channel
  Rows 7+ contain the data, with control voltage in column 0.

  @return:  power (dict of floats), ctlvolts (dict of floats), refpower (list of str)
  """
  serialnos = loadtxt(filename, delimiter=',', skiprows=3, dtype=str)[0,1:]
  rxs =       loadtxt(filename, delimiter=',', skiprows=4, dtype=str)[0,1:]
  headers =   loadtxt(filename, delimiter=',', skiprows=5, dtype=str)[0,1:]
  ID = {}
  for index in range(0, len(headers), 2):
    chanIDa = rxs[index]+'-'+headers[index].replace(' ','-')
    chanIDb = rxs[index]+'-'+headers[index+1].replace(' ','-')
    ID[chanIDa] = serialnos[index]+'A'
    ID[chanIDb] = serialnos[index]+'B'
  return ID

#---------------------------- functions for splines -----------------

def sampling_points(vmin, vmax, vstep=None):
  """
  Create a nicely spaced set of sampling points at which to evaluate
  
  @param vmin : minimum abscissa
  @type  vmin : float
  
  @param vmax : maximum abscissa
  @type  vmax : float
  
  @param vstep : optional abscissa step size
  @type  vstep : float or None
  
  @return: tuple
  """
  if vstep == None:
    vrange = float(vmax)-float(vmin)
    module_logger.debug("sampling_points: range=%f", vrange)
    appr_vstep = abs(vrange/100.)
    module_logger.debug("sampling_points: appr. step = %f", appr_vstep)
    vstep_order_of_magnitude = int(floor(log10(appr_vstep)))
    module_logger.debug("sampling_points: order of magnitude = %d",
                        vstep_order_of_magnitude)
    vstep = pow(10.,vstep_order_of_magnitude)
    module_logger.debug("sampling_points: step=%f", vstep)
  i_start = int(vmin/vstep)
  i_stop = int(vmax/vstep)
  module_logger.debug("sampling points: multiplier from %d to %d",
                      i_start,i_stop)
  if i_stop > i_start:
    if i_start*vstep < vmin:
      i_start = i_start+1
    if i_stop*vstep > vmax:
      i_stop = i_stop-1
    return i_start*vstep, i_stop*vstep, vstep
  else:
    if i_stop*vstep < vmax:
      i_stop = i_stop+1
    return i_start*vstep, i_stop*vstep, -vstep
  
def interpolate(att_spline, indices, range_info=None):
  """
  Interpolate a dict of splines over their ranges

  @param att_spline : dict of spline interpolators
  @type  att_spline : dict of interp1d instances

  @param indices : keys of the X and Y arrays to be fitted
  @type  indices : type of X and Y keys

  @param range_info : (start, stop, step); default: (-10, 0.5, 0.1)
  @type  range_info : dict of tuples of floats
  @return: dict of interp1d instances, sample points (min, max, step)
  """
  v = {}
  db = {}
  module_logger.debug("interpolate: ranges are %s", range_info)
  for index in indices:
    if range_info:
      v[index] = arange(*range_info[index])
    else:
      v[index] = arange(-10, 0.5, 0.1)
    module_logger.debug("interpolate: %s at \n%s", index, v[index])
    db[index] = att_spline[index](v[index])
  return v, db

def get_derivative(db, indices, Vstep=0.1):
  """
  Gets the derivatives of a set of vectors
  """
  slopes = {}
  for index in indices:
    slopes[index] = (db[index][1:]-db[index][:-1])/Vstep
  return slopes

#----------------------- functions for plotting results -----------------------

colors = ['b','g','r','c','m','y','k']

def column_marker(column):
  """
  Unique markers modulo 7
  """
  if (column)//7 == 0:
    marker = 'x'
  elif (column)//7 == 1:
    marker = '+'
  else:
    marker = 'd'
  return marker

def rezero_data(V, P, refs):
  """
  Plot measured data
  """
  att = {}
  keys = V.keys()
  keys.sort()
  for key in keys:
    index = keys.index(key)
    att[key] = []
    for pwr in P[key]:
      att[key].append(pwr - float(refs[index]))
    att[key] = NP.array(att[key])
  return att

def plot_data(V, P, refs):
  """
  Plot measured data
  """
  grid()
  xlim(-13,1)
  xlabel('Control Volts (V)')
  ylabel('Insertion Loss (dB)')
  title("Attenuation Curves")
  keys = V.keys()
  keys.sort()
  for key in keys:
    index = keys.index(key)
    plot(V[key], att[key], ls='-', marker=column_marker(index),
         label=key)
  legend(loc='lower left', numpoints=1)
  
def plot_fit(V, att, v, db, labels, keys, Vstep=0.1, toplabel=""):
  # plot data
  allkeys = V.keys()
  allkeys.sort()
  for key in keys:
    index = allkeys.index(key)
    plot(V[key], att[key], color=colors[index % 7],
         marker=column_marker(index), ls='', label=key)
  # plot fits
  for key in keys:
    index = allkeys.index(key)
    plot(v[key], db[key],  color=colors[index % 7], ls='-')
  grid()
  legend(numpoints=1)
  xlabel('Control Volts (V)')
  ylabel('Insertion Loss (dB)')
  title(toplabel) # title('Cubic spline interpolation on dB')                                        #!

def plot_gradients(v, gradient, keys):
  """
  """
  allkeys = v.keys()
  allkeys.sort()
  for key in keys:
    index = allkeys.index(key)
    plot(v[key][1:], gradient[key], color=colors[index % 7],
         marker=column_marker(index), ls='-', label=key)
  grid()
  xlabel('Control Volts (V)')
  ylabel('Insertion Loss Gradient (dB/V)')
  title('Attenuation interpolation')
  legend(loc='lower left')


 
if __name__ == "__main__":
  from socket import gethostname
  logging.basicConfig(level=logging.WARNING)
  mylogger = logging.getLogger()
  mylogger.setLevel(logging.INFO)
  
  # need this for the power meters
  fe = get_device_server("FE_server-krx43", "crux")
  print "Feed 1 load is:",fe.set_WBDC(13) # set feed 1 to sky
  print "Feed 2 load is:",fe.set_WBDC(15) # set feed 2 to sky
  #print fe.set_WBDC(14) # set feed 1 to load
  #print fe.set_WBDC(16) # set feed 2 to load
  for pm in ['PM1', 'PM2', 'PM3', 'PM4']:
    # set PMs to dBm
    print fe.set_WBDC(400+int(pm[-1]))
    
  # use direct WBDC control
  rx = WBDC2hwif('WBDC2')
  crossed = rx.get_Xswitch_state()
  if crossed:
    mylogger.warning(" cross-switch in set")
  pol_secs = {'R1-22': rx.pol_sec['R1-22'], 'R2-22': rx.pol_sec['R2-22']}
  attenuators = {
     'R1-22-E': pol_secs['R1-22'].atten['R1-22-E'],
		 'R1-22-H': pol_secs['R1-22'].atten['R1-22-H'],
		 'R2-22-E': pol_secs['R2-22'].atten['R2-22-E'],
		 'R2-22-H': pol_secs['R2-22'].atten['R2-22-H']}
  
  pkeys = pol_secs.keys(); pkeys.sort()
  akeys = attenuators.keys(); akeys.sort()
  mylogger.debug(" pol section keys: %s", pkeys)
  mylogger.debug(" attenuator keys: %s", akeys)
  
  powers  = {} # dict of lists of measured powers keyed on attenuator
  for atn in akeys:
    powers[atn] = []
  for attenuation in range(0,20):
    for atn in akeys:
	    attenuators[atn].set_atten(attenuation)
    time.sleep(0.5)
    # read all the power meters
    response = fe.read_pms()
    data =  []
    for index in range(len(response)):
	    powers[akeys[index]].append(response[index][2])
  print powers
 
  for pm in ['PM1', 'PM2', 'PM3', 'PM4']:
    # set PMs to W
    print fe.set_WBDC(390+int(pm[-1]))
"""
  cv = {}
  pkeys = powers.keys()
  pkeys.sort()
  refs = []
  for key in pkeys:
    cv[key] = NP.array(ctl_volts)
    refs.append(powers[key][0])
  ID = get_atten_IDs('wbdc2_data.csv')

  # re-zero the data
  att = rezero_data(cv, powers, refs)

  # Now do the fitting:
  att_spline,  V_sample_range   = get_splines(cv, att, pkeys)
  ctlV_spline, att_sample_range = get_splines(att, cv, pkeys)

  # verify the fits
  v, dB    = interpolate(att_spline,  pkeys, V_sample_range)
  db, ctlV = interpolate(ctlV_spline, pkeys, att_sample_range)

  # save the data
  module_path = "/usr/local/lib/python2.7/DSN-Sci-packages/MonitorControl/Receivers/WBDC/WBDC2/"
  splfile = open(module_path+"splines.pkl","wb")
  pickle.dump(((att_spline, V_sample_range),
               (ctlV_spline,att_sample_range)), splfile)
  splfile.close()

  # plot the data
  figure(1)
  plot_data(cv, powers, refs)
  xlim(-10,+1)

  # plot the fits
  figure(2)
  plot_fit(cv, att, v, dB, pkeys, pkeys,
           toplabel='Cubic spline interpolation on dB')
  figure(3)
  plot_fit(cv, att, ctlV, db, pkeys, pkeys,
           toplabel='Cubic spline interpolation on V')

  # get the slopes
  att_gradient = get_derivative(dB, pkeys)
  # analyze the slopes
  figure(4)
  plot_gradients(v, att_gradient, pkeys)

  show()
"""  
  
