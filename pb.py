'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pygame
import cups
import pygbutton
import card
#from urllib.parse import urlparse
#import argparse
#import socket
import sys
import os
import glob
import re
#from os.path import expanduser
#import time
import gallery
import printer
import logging
import pbweb
import pbupload
import pbqrcode
#import pktrigger
import StringIO
import PIL.Image
import pbtelepot

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)



class state(object):
    pb_none=0
    pb_error=1
    pb_nocon=11
    pb_waiting=2
    pb_capture=3
    pb_display=4
    pb_print=5
    pb_printing=6
    pb_gallery=7
    
class photobooth(object):
  # Set the width and height of the screen [width, height]
  screen_size = (1366, 768)
  image_size = (int (screen_size[0]*0.8), int (screen_size[1]))
  button_print_rect = (image_size[0], 200, screen_size[0] - image_size[0], screen_size[1] / 2 - 100)
  button_gallery_rect = (image_size[0], screen_size[1] / 2 + 100, screen_size[0] - image_size[0], screen_size[1] / 2 - 100)
  screen = None
  font = None
  clock = None

  button_print = None
  button_gallery = None

  # Current state
  state = None

  # Loop until the user clicks the close button.
  done = False

  ## FlashAir card variables
  # FlashAir card
  fa = None
  # Remote path
  fa_path = '/DCIM'
  # Timestamp of last write event
  fa_LastWriteEvent = 0

  # PKTriggercord
  #pk = pktrigger.pktrigger ()
  
  # Printer
  printer = None    
  phistory = None

  # Gallery
  gallery = None

  # Constructor
  def __init__(self, Config):
    logging.basicConfig (filename='pb.log', level=logging.INFO, format='%(asctime)s %(levelname)-7s %(module)-8s/%(funcName)-8s: %(message)s')
    #root = logging.getLogger ()
    #root.setLevel (logging.DEBUG)
    #fh = logging.FileHandler ('pb.log')
    #fh.setFormatter (pbFormatter ('%(asctime)s %(levelname)-7s %(module)-8s/%(funcName)-8s: %(message)s'))
    #root.addHandler (fh)
    
    # Init pygame
    pygame.init()
    pygame.display.set_caption("Photobooth")
    #pygame.mouse.set_visible (False)
    
    # Set display mode
    self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN)
    logging.info ('Screen size: ' + str (self.screen_size))
    
    # This is a font we use to draw text on the screen (size 36)
    self.font = pygame.font.Font(None, 68)
 
    # Used to manage how fast the screen updates
    self.clock = pygame.time.Clock()

    # Print and gallery button
    self.button_print = pygbutton.PygButton (self.button_print_rect, 'Drucken', bgcolor=RED)
    self.button_gallery = pygbutton.PygButton (self.button_gallery_rect, 'Galerie', bgcolor=GREEN)
    
    # Project name
    self.name = Config['Name'] if 'Name' in Config else 'Test'
    logging.info ('Name: ' + self.name)

    # Setup FlashAir card
    self.fa_address = Config['FlashAirAddress'] if 'FlashAirAddress' in Config else '1.2.3.4'
    self.fa = card.connection (self.fa_address, 80, 10)
    logging.info ('FlashAir address: ' + self.fa_address)
    self.connected = False

    # Last file
    self.current_file = None
  
    # Image folder
    self.image_folder = os.path.join ('images', self.name)
    if not os.path.exists (self.image_folder):
      os.makedirs (self.image_folder)
    if os.access (self.image_folder, os.W_OK):
      logging.info ('Image folder: ' + self.image_folder)
    else:
      logging.error ('No access to image folder: ' + self.image_folder)

    # Printer
    if 'PrinterName' in Config:
      logging.info ('Printer: ' + Config['PrinterName'])
      self.printer = printer.printer (Config['PrinterName'])

      # Print history
      self.phistory = printer.print_history (os.path.join (self.image_folder, 'print_history.txt'))

    # Upload
    if 'UploadHost' in Config:
      UploadSize = [int(Config['UploadSize'])]*2
      self.upload = pbupload.pfweb (self.name, Config['UploadHost'], Config['UploadUser'], Config['UploadPath'], UploadSize)
      # Add missing files
      self.upload.addFolder (self.image_folder)
    else:
      self.upload = None
    
    # QRCode path
    self.QRPath = Config['QRPath'] if 'QRPath' in Config else None

    # WhatsApp support
    self.WhatsAppNumber = Config['WhatsAppNumber'] if 'WhatsAppNumber' in Config else None

    # Underexposure detection
    self.UEThreshold = int(Config['UEThreshold']) if 'UEThreshold' in Config else 0

    # Telegram bot
    if 'TGBotToken' in Config:
      AdminId = int(Config['TGAdminId']) if 'TGAdminId' in Config else None
      self.TGBot = pbtelepot.pbBot (Config['TGBotToken'], AdminId)
      self.TGBot.sendMessage ('Photobooth started')
    else:
      self.TGBot = None
    
    # Gallery
    self.gallery = gallery.gallery (self.screen_size, 4, 3)

    # State
    self.state = state.pb_none

    # Status & Counters
    self.status_message = ''
    self.count_images = len (self.GetFileList ())
    logging.info ('Init image count: ' + str (self.count_images))
    
    if self.phistory:
      # Add number of prints
      self.count_prints = self.phistory.Count ()
      logging.info ('Init print count: ' + str (self.count_prints))

    # Current image
    self.current_image = None

  # Get image file list
  def GetFileList (self):
    ret = glob.glob (os.path.join (self.image_folder, '*.JPG'))
    ret += glob.glob (os.path.join (self.image_folder, '*.jpg'))
    return ret

  # Find newest directory
  def UpdateRemoteDirectory (self):
    # Get file/directory list
    (status, outlist)=self.fa.get_file_list(self.fa_path)
    
    # Find newest directory
    latest_dir = None
    latest_time = 0
    latest_date = 0
    for d in outlist:
      if not d.attribute_Directly:
        continue
      if d.date > latest_date:
        latest_date = d.date
        latest_time = d.time
        latest_dir = d
      elif d.date == latest_date and d.time > latest_time:
        latest_time = d.time
        latest_dir = d
	
    if not latest_dir:
      logging.warning ('FlashAir: Did not find latest directory')
      if self.TGBot:
        self.TGBot.sendMessage ('Warn: FlashAir: Did not find latest directory')
      return
    
    self.fa_path = latest_dir.directory_name + '/' + latest_dir.file_name
    logging.info ('FlashAir: Latest directory: ' + self.fa_path)
    
  # Ping card
  def PingFA (self):
    res = os.system ("ping -c 1 -w2 " + self.fa_address + " >/dev/null 2>&1");
    if res == 0:
      return True
    return False

  # Check for new write event on card
  def CheckWriteEvent (self):
    # Ping
    #if not self.PingFA ():
    #  self.fa_LastWriteEvent = 0
    #  logging.warning ('FlashAir: Ping failed')
    #  self.status_message = 'Keine Kamera'
    #  return False

    # Get timestamp of last write event
    Status, Event = self.fa.send_command (card.command.Get_time_stamp_of_write_event)
    
    if Status:
      # Reset write event
      self.fa_LastWriteEvent = 0
      self.status_message = 'Keine Verbindung'
      if self.connected:
        logging.warning ('FlashAir: Get write timestamp failed')
        if self.TGBot:
          self.TGBot.sendMessage ('Warn: FlashAir disconnected!')
      self.connected = False
      return False

    if not self.connected:
      logging.info ('FlashAir: Connected')
      self.status_message = 'Verbunden'
      self.connected = True
      if self.TGBot:
        self.TGBot.sendMessage ('Info: FlashAir connected')

    Event = int (Event)

    if Event > self.fa_LastWriteEvent:
      logging.debug ('FlashAir: Write event:' + str (Event))
      self.fa_LastWriteEvent = Event
      return True

  # Write message
  def WriteMessage (self, Message, Erase=False, Position=0):
    if Erase:
      self.screen.fill (BLACK)

    text = self.font.render (Message, True, WHITE)
    size = text.get_size ()
    pos = [self.image_size[0]/2 - size[0]/2, self.image_size[1]/2 - size[1]/2]
    if Position:
      pos[1] += size[1]
    self.screen.blit (text, pos)
    pygame.display.flip()

  # Write status
  def WriteStatus (self, Message = ''):
    # Clear area
    pygame.draw.rect (self.screen, BLACK, [self.image_size[0], 0, self.screen_size[0]-1, 200])
    font = pygame.font.Font(None, 40)
    text = font.render ('Fotos: ' + str (self.count_images), True, WHITE)
    size = text.get_size ()
    self.screen.blit (text, [self.image_size[0] + 5, 5 + 3*size[1]])
    if self.printer:
      text = font.render ('Gedruckt: ' + str (self.count_prints), True, WHITE)
      self.screen.blit (text, [self.image_size[0] + 5, 5 + 4*size[1]])
    if Message:
      self.status_message = Message
    if self.status_message:
      text = font.render (self.status_message, True, WHITE)
      self.screen.blit (text, [self.image_size[0] + 5, 5 + 0*size[1]])
    if Message:
      pygame.display.flip()
  
  # Draw QRCode
  def DrawQRCode (self, File):
    if not self.QRPath:
      return
    if not File:
      return

    # Build QR code
    address = self.QRPath + '/' + os.path.basename (File).lower ()
    qr = pbqrcode.qrcode (address)
    # Get QR code as RGB string
    qrsize, rgb = qr.GetRGBString ()
    # Create PyGame image from RGB string
    qrimg = pygame.image.fromstring (rgb, qrsize, 'RGB')
    qrimg = pygame.transform.scale (qrimg, (200,200))
    qrsize = qrimg.get_size ()
    qrpos = [self.image_size[0] - qrsize[0] - 1, self.image_size[1] - qrsize[1] - 1]
    self.screen.blit (qrimg, qrpos)
    # Draw web address as text
    font = pygame.font.Font(None, 30)
    text = font.render (address, True, WHITE)
    size = text.get_size ()
    self.screen.blit (text, [qrpos[0] - size[0] - 1, self.image_size[1] - size[1] - 1])
    
  # Draw WhatsApp number
  def DrawWhatsApp (self, File):
    if not self.WhatsAppNumber:
      return
    if not File:
      return
    
    # Get image number
    ImageNr = re.findall ('\d+', os.path.basename (File))
    if not ImageNr:
      return
    
    # Draw text
    font = pygame.font.Font(None, 30)
    text = font.render ('Sende ' + str(ImageNr[0]) + ' an WhatsApp ' + self.WhatsAppNumber, True, WHITE)
    size = text.get_size ()
    self.screen.blit (text, [0, self.image_size[1] - size[1] - 1])
    
  # Capture
  def Capture (self):
    self.WriteStatus ("Bitte warten...")
    #pygame.draw.rect (self.screen, BLACK, [0, 0, self.image_size[0], self.image_size[1]])
    #self.WriteMessage ("Bitte warten...", False)
    logging.info ('FlashAir: Sync')

    newfile = self.fa.sync_new_pictures_since_start (self.fa_path, self.image_folder)
    #newfile = self.pk.sync_new_file ()

    #if (not os.access (lastfile, os.R_OK)):
    if not newfile:
      logging.info ('FlashAir: No new file')
      self.state = state.pb_display
    else:
      logging.info ('FlashAir: New file ' + newfile)
      self.current_file = newfile
      self.count_images = len (self.GetFileList ())
      # Create thumbnail
      self.gallery.CreateThumbnail (self.current_file)
      self.state = state.pb_display
      
      # Upload
      if self.upload:
        self.upload.put (self.current_file)
            
  # Display
  def Display (self, File=''):
    if not File:
      File = self.current_file
    if not File:
      return
    if not os.access (File, os.R_OK):
      logging.warning ('No access to file: ' + File)
      return
    
    logging.info ('Display: ' + File)

    # Load and convert image
    image = pygame.image.load(File)
    image.convert()

    # Scale if required
    size = image.get_size ()    
    scale = gallery.Scale (size, self.image_size)
    if scale:
      image = pygame.transform.scale (image, scale)

    # Draw to screen
    pygame.draw.rect (self.screen, BLACK, [0, 0, self.image_size[0], self.image_size[1]])
    self.screen.blit (image, [0, 0])

    # Save current image
    self.current_image = image

    # Draw QRCode
    self.DrawQRCode (File)
    
    # Draw WhatsApp
    self.DrawWhatsApp (File)
      
    # Update status message
    self.status_message = os.path.basename (File)

    # Check exposure
    if self.UEThreshold:
      ts = image.copy ()
      t = pygame.transform.threshold (ts, image, ( 0,0,0 ), [40]*3, ( 255,255,255 ), 0)
      size = image.get_size ()
      uep = t*100 / (size[0] * size[1])
      logging.info (os.path.basename (File) + ': UE value ' + str (uep) + '%')
      if uep >= self.UEThreshold:
        logging.warn ('Underexposure!')
        if self.TGBot:
          img = self.GetImageJPEG (True)
          self.TGBot.sendPhoto (img, 'Warn: Underexposure: ' + self.status_message + ' ' + str (uep) + '%')
          img.close ()

  # Get current image as JPEG
  def GetImageJPEG(self, Stream = False):
    if not self.current_image:
      return None
    # Get current image as RGB
    RGB = pygame.image.tostring (self.current_image, 'RGB')
    # Load to Pillow
    Img = PIL.Image.frombytes ('RGB', self.current_image.get_size (), RGB)
    output = StringIO.StringIO()
    # Set name so others can get the extension
    setattr (output, 'name', 'a.jpg')
    # Save as JPEG
    Img.save(output, format="JPEG")
    if Stream:
      output.seek(0)
      return output
    else:
      data = output.getvalue()
      output.close()
    return data
    
  # Gallery
  def Gallery (self):
    # Get list of files
    files = self.GetFileList ()
    files.sort (reverse = True)
    TextList = []
    for file in files:
      if self.printer and self.phistory.Check (file):
        TextList.append (os.path.basename (file) + " (Gedruckt)")
      else:
        TextList.append (os.path.basename (file))
        
    # Show gallery
    selection = self.gallery.Run (self.screen, files, TextList)
    self.screen.fill (BLACK)
    # If image was selected, show it again
    if (selection >= 0):
      self.current_file = files[selection]
      self.state = state.pb_display
    else:
      self.state = state.pb_display
    
  # -------- Main Program Loop -----------
  def MainLoop (self):
    self.state = state.pb_waiting

    web = pbweb.pbWeb (self.GetImageJPEG)
    web.start ()

    # Get latest directory
    self.UpdateRemoteDirectory ()

    while not self.done:
      # --- Limit to 1 frames per second
      self.clock.tick(1)
      
      # --- Main event loop
      for event in pygame.event.get():
        if self.printer and 'click' in self.button_print.handleEvent(event) and self.button_print.bgcolor == GREEN:
          self.state = state.pb_print
          logging.info ("Button print")
        if 'click' in self.button_gallery.handleEvent(event):# and self.button_gallery.bgcolor == GREEN:
          self.state = state.pb_gallery
          logging.info ("Button gallery")
        if event.type == pygame.QUIT:
          self.done = True
          logging.info ("QUIT")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
          self.done = True
          logging.info ("Keyboard quit")

      # --- Game logic should go here
      if self.state == state.pb_error:
        self.screen.fill (BLACK)

      # Display last file
      if not self.current_file:
        files = self.GetFileList ()
        if files:
          files.sort (reverse = True)
          self.current_file = files[0]
          self.state = state.pb_display

      # Get timestamp of last write event
      if ((self.state == state.pb_waiting) or (self.state == state.pb_error)) and self.CheckWriteEvent ():
        self.state = state.pb_capture

      # Capture
      if (self.state == state.pb_capture):
        self.Capture ()

      # Display
      if self.state == state.pb_display:
        if self.current_file:
          self.Display ()
          self.status_message = os.path.basename (self.current_file)
        self.state = state.pb_waiting
      elif self.state == state.pb_print:
        # Start printing
        if not self.printer.isPresent:
          self.state = state.pb_error
        elif not self.printer.getState () == cups.IPP_PRINTER_IDLE:
          logging.warning ("Printer not idle")
          self.state = state.pb_error
        else:
          self.WriteMessage ("Drucken...")
          self.printer.printFile (self.current_file)
          self.state = state.pb_printing
      elif self.state == state.pb_printing:
        printer_state = self.printer.getState ()
        if printer_state == cups.IPP_PRINTER_IDLE and self.printer.jobsFinished ():
          self.Display ()
          self.WriteMessage ("Fertig")
          self.WriteMessage ("Bitte neues Foto machen", False, 1)
          self.phistory.Add (self.current_file)
          self.phistory.Save ()
          self.count_prints += 1
          self.state = state.pb_waiting
      elif self.state == state.pb_gallery:
        # Gallery
        self.Gallery ()

      # Handle print button
      if self.state == state.pb_error:
        self.WriteMessage ("Fehler :-(", True)
        self.button_print.bgcolor = RED
      elif self.printer and self.state == state.pb_waiting and \
                  self.current_file and \
                  not self.phistory.Check (self.current_file) and \
                  self.printer.getState () == cups.IPP_PRINTER_IDLE:
        self.button_print.bgcolor = GREEN
      else:
        self.button_print.bgcolor = YELLOW
          
      # Handle gallery button
      if self.state == state.pb_error:
        self.button_gallery.bgcolor = RED
      elif self.state == state.pb_waiting:
        self.button_gallery.bgcolor = GREEN
      else:
        self.button_gallery.bgcolor = YELLOW

      # Change print button caption if already printed
      if self.current_file and self.phistory and self.phistory.Check (self.current_file):
        self.button_print.caption = "Bereits gedruckt"
      else:
        self.button_print.caption = "Drucken"

      # --- Drawing code should go here
      self.WriteStatus ()
      if self.printer:
        self.button_print.draw (self.screen)
      self.button_gallery.draw (self.screen)

      # --- Go ahead and update the screen with what we've drawn.
      pygame.display.flip()
  
      # Capture screen
      pygame.image.save (self.screen, 'screen.jpg')
    
    # Stop uploader
    if self.upload:
      self.upload.stop ()

    web.stop ()
    web.join ()
    
    # Close the window and quit.
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()

    

    import sys, traceback, threading
    for thread_id, frame in sys._current_frames().iteritems():
      name = thread_id
      for thread in threading.enumerate():
        if thread.ident == thread_id:
           name = thread.name
      traceback.print_stack(frame)
