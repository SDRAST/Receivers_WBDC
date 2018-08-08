from pylab import *

for filename in ['series1Ka.txt',
                 'series3K-1.0V.txt',
                 'series3K-1.5V.txt',
                 'series3K.txt',
                 'series4.3K-1.5V.txt',
                 'series5.7-1.5V.txt',
                 'series6.5K-1.5V.txt']:
  print "Plotting",filename
  fd = open(filename,'r')
  bias = fd.readline().split()[3]
  ohms = fd.readline().split()[3]
  fd.close()
  label = bias+" "+ohms
  skiprows = 2
  data = loadtxt(filename, skiprows=skiprows)
  V = data[:,0]
  P  = data[:,1]
  plot(V, P, marker='o', label=label)
grid(True)
xlabel("Control Voltage (V)")
ylabel("Power (dBm)")
legend(loc='lower left')
show()