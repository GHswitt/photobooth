'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pygame
import cups
import pygbutton
import card
import sys
import os
import glob
import gallery
import printer
import logging
import pbweb
#import pktrigger

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

  # Last file
  current_file = None
  
  # Printer
  printer = None    

  # Gallery
  gallery = None

  # Constructor
  def __init__(self, FlashAirAddress, PrinterName):
    logging.basicConfig (filename='pb.log', level=logging.DEBUG, format='%(asctime)s %(levelname)-7s %(module)-8s/%(funcName)-8s: %(message)s')
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
    
    # Setup FlashAir card
    self.fa = card.connection (FlashAirAddress, 80, 3000)
    logging.info ('FlashAir address: ' + FlashAirAddress)

    # Image folder
    self.image_folder = 'images/'
    if os.access (self.image_folder, os.W_OK):
      logging.info ('Image folder: ' + self.image_folder)
    else:
      logging.error ('No access to image folder: ' + self.image_folder)

    # Printer
    logging.info ('Printer: ' + PrinterName)
    self.printer = printer.printer (PrinterName)

    # Print history
    self.phistory = printer.print_history ('print_history.txt')

    # Gallery
    self.gallery = gallery.gallery (self.screen_size, 4, 3)

    # State
    self.state = state.pb_none

    # Status & Counters
    self.status_message = ''
    self.count_images = len (glob.glob (self.image_folder + '*.JPG'))
    self.count_prints = self.phistory.Count ()

    logging.info ('Init image count: ' + str (self.count_images))
    logging.info ('Init print count: ' + str (self.count_prints))

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
      return
    
    self.fa_path = latest_dir.directory_name + '/' + latest_dir.file_name
    logging.info ('FlashAir: Latest directory: ' + self.fa_path)
	  
  # Check for new write event on card
  def CheckWriteEvent (self):
    # Get timestamp of last write event
    Status, Event = self.fa.send_command (card.command.Get_time_stamp_of_write_event)
    
    if Status:
      logging.warning ('FlashAir: Get write timestamp failed')
      self.status_message = 'Keine Verbindung'
      #self.WriteMessage ("Keine Verbindung")
      #self.state = state.pb_error
      return False

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
    text = font.render ('Gedruckt: ' + str (self.count_prints), True, WHITE)
    self.screen.blit (text, [self.image_size[0] + 5, 5 + 4*size[1]])
    if Message:
      self.status_message = Message
    if self.status_message:
      text = font.render (self.status_message, True, WHITE)
      self.screen.blit (text, [self.image_size[0] + 5, 5 + 0*size[1]])
    if Message:
      pygame.display.flip()
    
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

    # Update status message
    self.status_message = os.path.basename (File)

  # -------- Main Program Loop -----------
  def MainLoop (self):
    self.state = state.pb_waiting

    web = pbweb.pbWeb ()
    web.start ()

    # Get latest directory
    self.UpdateRemoteDirectory ()

    while not self.done:
      # --- Limit to 1 frames per second
      self.clock.tick(1)
      
      # --- Main event loop
      for event in pygame.event.get():
	if 'click' in self.button_print.handleEvent(event) and self.button_print.bgcolor == GREEN:
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

      # Get timestamp of last write event
      if ((self.state == state.pb_waiting) or (self.state == state.pb_error)) and self.CheckWriteEvent ():
	self.state = state.pb_capture
      #self.state = state.pb_capture

      if (self.state == state.pb_capture):
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
	  self.count_images = len (glob.glob (self.image_folder + '*.JPG'))
	  # Create thumbnail
	  self.gallery.CreateThumbnail (self.current_file)
	  self.state = state.pb_display

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
	# Gallery, get list of files
	files = glob.glob (self.image_folder + '*.JPG')
	files.sort (reverse = True)
	TextList = []
	for file in files:
	  if self.phistory.Check (file):
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
	
      # Handle print button
      if self.state == state.pb_error:
	self.WriteMessage ("Fehler :-(", True)
	self.button_print.bgcolor = RED
      elif self.state == state.pb_waiting and \
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
      if self.current_file and self.phistory.Check (self.current_file):
	self.button_print.caption = "Bereits gedruckt"
      else:
	self.button_print.caption = "Drucken"

      # --- Drawing code should go here
      self.WriteStatus ()
      self.button_print.draw (self.screen)
      self.button_gallery.draw (self.screen)

      # --- Go ahead and update the screen with what we've drawn.
      pygame.display.flip()
  
      # Capture screen
      pygame.image.save (self.screen, 'screen.jpg')
    # Close the window and quit.
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()

    web.stop ()
    web.join ()
