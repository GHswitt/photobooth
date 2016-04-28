'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pb
import sys

def LoadConfig(ConfigFile):
  try:
    f = open(ConfigFile, 'r')
    Config = {}
    for line in f:
      line = line.strip()
      # Ignore comments
      if len(line) and line[0] in ('#',';'):
        continue
      # Ignore trailing comments
      line = line.split(';', 1)[0].split('=', 1)
      # Get name and value
      Name = line[0].strip()
      Value = line[1].strip()
      Config[Name] = Value
    return Config
  except IOError:
    print("Config not found: %s" % ConfigFile)
    sys.exit(1)


pb = pb.photobooth (LoadConfig ('config'))

pb.MainLoop ()
