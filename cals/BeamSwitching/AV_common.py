# -*- coding: utf-8 -*-
import logging

module_logger = logging.getLogger(__name__)

def TeXify(text):
  newtext = text.replace('_','\_')
  return newtext

def excise_load_transitions(data, threshold=3, minsize=1000):
  residuals = 2*data[1:-1] - data[:-2] - data[2:]
  rms = residuals.std()
  std_dev = residuals/rms
  outliers = (abs(std_dev) > threshold).nonzero()[0]
  if outliers[0] > minsize:
    groups = [[0,outliers[0]]]
  else:
    groups = []
  for index in range(1,len(outliers)-1):
    if outliers[index+1] - outliers[index] > minsize:
      groups.append([outliers[index],outliers[index+1]])
  return groups 
