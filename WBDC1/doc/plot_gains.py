# -*- coding: utf-8 -*-
from pylab import *
import numpy as NP

figure(1)
data = NP.loadtxt("KBandFilter.csv",skiprows=2)
plot(data[:,0],data[:,1],label="18 GHz")
plot(data[:,0],data[:,2],label="20 GHz")
plot(data[:,0],data[:,3],label="26 GHz")
xlabel("Frequency (GHz)")
ylabel(r"$|S_{21}|$ (Linear voltage gain)")
title("WBDC RF bandpass filters")
legend()
grid()

figure(2)
plot(data[:,0]-18.,data[:,1],label="18 GHz")
plot(data[:,0]-20.,data[:,2],label="20 GHz")
plot(data[:,0]-26.,data[:,3],label="26 GHz")
xlabel(r"$\Delta$F (GHz)")
ylabel(r"$|S_{21}|$ (Linear voltage gain)")
title("WBDC RF bandpass filters")
xlim(-2.,2.)
legend()
grid()

show()
