'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import os
import subprocess
import glob

# pktriggercord class
class pktrigger(object):

  def __init__(self):
    self.image_folder = ''
    self.image_prefix = 'IMPK'
    # Get image count
    self.image_count = glob.glob (self.image_folder + self.image_prefix + '*.JPG')
    if not self.image_count:
      self.image_count = 0
    else:
      self.image_count = self.image_count.sort (reverse = True)
      self.image_count = int (self.image_count[0][4:7])
    print self.image_count
    
  def sync_new_file (self):
    File = self.image_folder + self.image_prefix + str (self.image_count)
    ret = subprocess.call (['pktriggercord-cli', '--file_format=JPEG', '--noshutter', '--output_file=' + File])
    if ret:
      return ''
    self.image_count += 1
    return File + '-0000.jpg'
