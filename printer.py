'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import cups
import os
import gallery
import pygame
import logging

# Printer class
class printer(object):

  def __init__(self, Name):
    self.Name = None
    self.JobId = None
    self.conn = cups.Connection ()
    printers = self.conn.getPrinters ()
    logging.debug (printers)
    if Name in printers:
      self.Name = Name
      logging.info ('Printer: ' + Name)
    else:
      logging.error ('Printer not found: ' + Name)

  def isPresent(self):
    if self.Name:
      return True
    return False
  
  def getState(self):
    attr = self.conn.getPrinterAttributes (self.Name, requested_attributes=['printer-state'])
    return attr['printer-state']

  def printFile(self, File):
    logging.info ('Print file: ' + File)
    if not os.access (File, os.R_OK):
      logging.error ('No access to file: ' + File)
    image = pygame.image.load (File).convert()
    size = image.get_size ()
    if size[1] > 1600:
      # Convert
      logging.info ("Image width > 1600, scaling...")
      size = gallery.Scale (size, [2400, 1600])
      scaled = pygame.transform.smoothscale (image, size)
      filename, extension = os.path.splitext(File)
      File = os.path.basename (filename) + 'p' + extension
      pygame.image.save (scaled, File)
    # Print
    self.JobId = self.conn.printFile (self.Name, File, File, {"StpBorderLess" : "True", "StpImageType" : "Photo"})
    logging.info ("Print JobId: " + str (self.JobId))

  def jobsFinished(self):
    jobs = self.conn.getJobs ()
    if not jobs:
      return True
    return False

class print_history(object):
  # Constructor
  def __init__(self, Filename):
    self.Filename = Filename
    # Read file
    try:
      f = open (Filename, 'r')
      self.data = f.readlines ()
      f.close ()
    except:
      self.data = []
      logging.warn ("File read error: " + Filename)
 
  # Add name to print_history
  def Add (self, Filename):
    # Check if name exists in list
    if (os.path.basename (Filename) + '\n') in self.data:
      return
    logging.info ("Adding " + os.path.basename (Filename))
    self.data.append (os.path.basename (Filename) + '\n')
 
  # Check if file is in history
  def Check (self, Filename):
    if (os.path.basename (Filename) + '\n') in self.data:
      return True
    return False
   
  # Save history
  def Save (self):
    try:
      f = open (self.Filename, 'w+')
      f.writelines (self.data)
      f.close ()
    except:
      logging.error ("File write error: " + self.Filename)

  # Count
  def Count (self):
    return len (self.data)
