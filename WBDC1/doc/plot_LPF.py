from pylab import *

data = loadtxt("LPF.csv", skiprows=9, delimiter=',')
freqs = data[:,0]
S11 = data[:,1]
S12 = data[:,5]
plot(freqs/1e6, S11, label="S11")
plot(freqs/1e6, S12, label="S12")
grid()
legend(loc="lower left")
xlim(0,1200)
ylim(-45,5)
xlabel("Frequency (MHz)")
ylabel("Level (dB)")
title("S-parameters")
show()
