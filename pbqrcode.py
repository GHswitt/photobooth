'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pyqrcode
import StringIO

# PB qrcode class
class qrcode(object):

  def __init__(self, Text):
    self.code = pyqrcode.create (Text, error = 'M')

  # Get image as string in RGB
  def GetRGBString(self):
    code = str (self.code.text (quiet_zone = 2))

    width = code.find ('\n')
    height = code.count ('\n')
    code = code.translate (None, '\n')
    code = code.replace ('1', b'\x00\x00\x00')
    code = code.replace ('0', b'\xFF\xFF\xFF')
    
    return (width, height), code


