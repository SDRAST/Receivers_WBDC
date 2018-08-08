from pylab import *


data = loadtxt("data-F1E")
dB = data[:,0]
uW = data[:,1]
mV = data[:,2]
p1 = polyfit(uW, mV, 1)
p2 = polyfit(uW, mV, 2)
f1 = poly1d(p1)
f2 = poly1d(p2)
scatter(uW,mV)
plot(uW, f1(uW), label="linear")
plot(uW, f2(uW), label="quadratic")
grid()
legend()
xlabel("Power (uW)")
ylabel("Detector (V)")
title("Detector F1E")
show()