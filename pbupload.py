'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import paramiko
import os
import sys
import glob
import threading
import logging
import Queue
import time
import gallery
import subprocess

# PB upload class
class sftp(object):

  def __init__(self, Host, User):
    self.Host = Host
    self.User = User

    self.Connected = False
    self.UploadE = None
    self.UploadT = None

    # Get private key for connection
    self.pkeyfile = os.path.expanduser('~/.ssh/id_rsa')
    key = paramiko.RSAKey
    if not os.path.isfile (self.pkeyfile):
        # Try DSA
        self.pkeyfile = os.path.expanduser('~/.ssh/id_dsa')
        Key = paramiko.DSSKey
    try:
        self.ssh_key = key.from_private_key_file (self.pkeyfile)
        logging.info('Using SSH keyfile: %s' % self.pkeyfile)
    except IOError, e:
        logging.error('Unable to find RSA or DSA SSH keyfile: %s' % str(e))
        raise

    # Upload queue and thread
    self.UploadQ = Queue.Queue ()
    self.UploadE = threading.Event ()
    self.UploadT = threading.Thread (target = self.UploadThread)
    self.UploadT.start ()

  def stop (self):
    # Stop thread
    if self.UploadE:
      self.UploadE.set ()
      self.UploadT.join ()
      self.UploadE = None

    # Close SFTP connection
    if self.Connected:
      self.sftp.close()
      self.transport.close()
      self.Connected = None    

  def Connect (self):
    # Connect
    try:
      # SSH transport
      self.transport = paramiko.Transport ((self.Host, 22))
      # Connect with private key
      self.transport.connect (username = self.User, pkey = self.ssh_key)
      logging.info ('Connected to  ' + self.User + '@' + self.Host)
      self.Connected = True
      # Start SFTP client
      self.sftp = paramiko.SFTPClient.from_transport (self.transport)
    except paramiko.AuthenticationException, e:
      self.logger.error("Connect failed: %s" % str(e))
      self.Connected = False

    return self.Connected

  # Upload thread
  def UploadThread (self):
    logging.info ('Upload thread started')

    while not self.UploadE.is_set ():
      # Get next item, timeout after 3s to check exit event
      try:
        item = self.UploadQ.get (True, 3)
      except Queue.Empty:
        continue

      # Connect if not connected
      while not self.UploadE.is_set () and ((self.Connected and not self.transport.is_authenticated ()) or not self.Connected):
        self.Connect ()
        time.sleep (5)

      # Create remote path (if it does not exist)
      try:
        self.sftp.chdir (item['RemotePath'])
      except IOError:
        self.sftp.mkdir (item['RemotePath'])
        self.sftp.chdir (item['RemotePath'])
        logging.info ('Created ' + self.User + '@' + self.Host + ':' + item['RemotePath'])

      # Upload
      try:
        self.sftp.put (item['Local'], os.path.basename (item['Local']))
        logging.info ('Uploaded ' + item['Local'] + ' to ' + item['RemotePath'])
        self.UploadQ.task_done ()
      except:
        # Upload failed, queue again
        logging.error ('Uploading ' + item['Local'] + ' to ' + item['RemotePath'] + ' failed')
        self.UploadQ.task_done ()
        self.UploadQ.put (item)

    logging.info ('Upload thread finished')

  # Upload
  def put (self, Local, RemotePath):
    # Add to queue
    self.UploadQ.put ({'Local': Local, 'RemotePath': RemotePath})


# PB upload class
class pfweb(object):

  def __init__(self, Name, Host, User, WebPath, WebSize = [1600, 1600], LocalPath = None):
    self.Name = Name or ''
    self.LocalPath = LocalPath or 'web';
    self.Host = Host
    self.User = User
    self.WebPath = WebPath
    self.WebSize = WebSize

    # Upload queue and thread
    self.UploadQ = Queue.Queue ()
    self.UploadE = threading.Event ()
    self.UploadT = threading.Thread (target = self.UploadThread)
    self.UploadT.start ()

  def stop (self):
    # Stop thread
    if self.UploadE:
      self.UploadE.set ()
      self.UploadT.join ()
      self.UploadE = None

  # Update local gallery
  def UpdateGallery (self):
    # Update gallery
    ret = subprocess.call (['/home/panel/PhotoFloat/scanner/main.py', 
                          os.path.join (self.LocalPath, 'albums'),
                          os.path.join (self.LocalPath, 'cache')])
    
    if ret:
      logging.error ("Calling PhotoFloat scanner failed: " + str(ret))
      return False
    
    return True
    
  # Add to gallery
  def AddToGallery (self, File):
    # Resize to web folder
    gallery.ResizeEXIF (File, os.path.join (self.LocalPath, "albums", self.Name, os.path.basename (File)), self.WebSize)
  
  # Upload thread
  def UploadThread (self):
    logging.info ('Upload thread started')

    while not self.UploadE.is_set ():
      # Get next item, timeout after 3s to check exit event
      try:
        item = self.UploadQ.get (True, 3)
      except Queue.Empty:
        continue

      # Resize to web folder
      self.AddToGallery (item)
      
      # Update gallery
      if not self.UpdateGallery ():
        # Upload failed, queue again
        self.UploadQ.task_done ()
        self.UploadQ.put (item)
        continue
      
      # Upload gallery
      ret = subprocess.call (['./pb_web_rsync.sh', self.Host, self.User, self.WebPath])
      
      if ret:
        logging.error ("RSync failed: " + str(ret))
        # Upload failed, queue again
        self.UploadQ.task_done ()
        self.UploadQ.put (item)
        continue
      
      logging.info ('Added ' + item + ' to gallery')
      self.UploadQ.task_done ()

    logging.info ('Upload thread finished')

  # Upload
  def put (self, Local):
    # Add to queue
    self.UploadQ.put (Local)

  # Add all images from folder, if not already in album
  def addFolder (self, Folder):
    newfiles = glob.glob (os.path.join (Folder, '*.JPG'))
    newfiles += glob.glob (os.path.join (Folder, '*.jpg'))
    oldfiles = glob.glob (os.path.join (self.LocalPath, "albums", self.Name, '*.JPG'))
    oldfiles += glob.glob (os.path.join (self.LocalPath, "albums", self.Name, '*.JPG'))
    newset = set([os.path.basename(x) for x in newfiles])
    oldset = set([os.path.basename(x) for x in oldfiles])
    missing = [os.path.join (Folder, x) for x in (newset - oldset)]
    for x in missing:
      logging.info ('Added missing: ' + x)
      self.AddToGallery (x)

    self.UpdateGallery ()
