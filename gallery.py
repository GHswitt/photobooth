'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pygame
import pygbutton
import os
import logging

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


class arrow(object):
  up_points = [[0, 500], [500, 0], [1000, 500], [666, 500], [666, 2000], [333, 2000], [333, 500]]
  down_points = [[333, 0], [666, 0], [666, 1500], [1000, 1500], [500, 2000], [0, 1500], [333, 1500]]

  # Constructor
  def __init__ (self, type, screen, position=[0,0], size=[50, 100], color=(0,255,0)):
    self.screen = screen
    self.position = position
    self.size = size
    self.color = color

    if (type == 0):
      self.points = self.up_points
    elif (type == 1):
      self.points = self.down_points

    #points = copy.deepcopy (self.up_points)
    
    # Scale points to new size
    xscale = float(1000) / self.size[0]
    yscale = float(2000) / self.size[1]
    for i in range(len(self.points)):
      self.points[i][0] = int (self.points[i][0] / xscale)
      self.points[i][1] = int (self.points[i][1] / yscale)

    # Add position
    self.AddOffset (self.points, position)

    # Calculate mouse area
    self.mouse_area = [[0, 0], [0, 0]]
    self.mouse_area[0] = position
    for i in self.points:
      if i[0] > self.mouse_area[1][0]:
	self.mouse_area[1][0] = i[0]
      if i[1] > self.mouse_area[1][1]:
	self.mouse_area[1][1] = i[1]
    
  # Add position
  def AddOffset (self, points, offset):
    for i in range(len(points)):
      points[i][0] += offset[0]
      points[i][1] += offset[1]
      
  # Draw
  def draw (self):
    pygame.draw.polygon (self.screen, self.color, self.points, 0)

  # Check if pressed
  def pressed (self, mouse):
    if mouse[0] < self.mouse_area[0][0]:
      return False
    if mouse[1] < self.mouse_area[0][1]:
      return False
    if mouse[0] > self.mouse_area[1][0]:
      return False
    if mouse[1] > self.mouse_area[1][1]:
      return False
    return True

# Scale using aspect ratio
def Scale (source, target):
  if (source[0] > target[0] or source[1] > target[1]):
    image_aspect = float (source[0]) / source[1]
    target_aspect = float (target[0]) / target[1]
    new_width = target[0]
    new_height = target[1]

    if (target_aspect > image_aspect):
      # Target is wider than source
      new_height = int (target[0] / image_aspect)
      if (new_height > target[1]):
	# Higher than target, reduce both
	new_width = int (new_width / (float (new_height) / target[1]))
	new_height = target[1]
    else:
      # Target is higher or same
      new_width = int (target[1] * image_aspect)
      if (new_width > target[0]):
	# Wider than target, reduce both
	new_height = int (new_height / (float (new_width) / target[0]))
	new_width = target[0]

    return [new_width, new_height]
  else:
    return []
    
class gallery(object):

  # Constructor
  def __init__(self, size, x=3, y=3):
    self.width = size[0]
    self.height = size[1]
    self.x = x
    self.y = y
    self.button_size = [250, (size[1]-200) / 2 - 10]
    self.button_back_rect = [self.width-self.button_size[0], 0, self.button_size[0], 200]
    self.surface = pygame.Surface (size)
    self.button_back = pygbutton.PygButton (self.button_back_rect, 'Zurueck', bgcolor=GREEN)
    self.button_up = arrow(0, self.surface, [self.width-self.button_size[0], self.button_back_rect[3]], self.button_size)
    self.button_down = arrow(1, self.surface, [self.width-self.button_size[0], self.height - self.button_size[1]-1], self.button_size)
    self.font = pygame.font.Font(None, 32)
    self.thumbnail_folder = 'thumbnail/'

    logging.info ("%ux%u, %ux%u fields" % (size[0], size[1], x, y))
    if os.access (self.thumbnail_folder, os.W_OK):
      logging.info ("Thumbnail folder: %s" % (self.thumbnail_folder))
    else:
      logging.error ('No access to folder: ' + self.thumbnail_folder)

  # Create thumbnail
  def CreateThumbnail (self, Filename):
    if not os.access (Filename, os.R_OK):
      logging.warning ('No access to ' + Filename)
      return
    if not os.path.exists (self.thumbnail_folder):
      os.makedirs (self.thumbnail_folder)
    if not os.access (self.thumbnail_folder, os.W_OK):
      logging.warning ('No access to ' + self.thumbnail_folder)
      return
      
    # Load and convert
    img = pygame.image.load (Filename).convert ()
    
    # Scale if required, preserving aspect ratio
    scale = Scale (img.get_size (), [640, 480])
    if (scale):
      img = pygame.transform.smoothscale (img, scale)

    filename, extension = os.path.splitext(Filename)
    thumbnail = self.thumbnail_folder + os.path.basename (filename) + 't' + extension
    logging.info ('Creating thumbnail ' + thumbnail)
    pygame.image.save (img, thumbnail)

  # Draw gallery
  def Draw (self, ImageList, Position = 0, TextList = []):
    # Calculate position
    if (Position > len(ImageList)-1):
      Position = len(ImageList)-1
      logging.warning ("Position > ImageList")
    
    self.surface.fill (BLACK)

    # Calculate size of each image
    iwidth = int ((self.width - self.button_size[0]) / self.x)
    iheight = int (self.height / self.y)

    logging.debug ("Field size: %ux%u" % (iwidth, iheight))

    count = 0
    for image in ImageList[Position:]:
      # End condition
      if count >= (self.x * self.y):
	break

      # Calculate position
      pos = [int (count % self.x) * iwidth, int (count / self.x) * iheight]
      
      # Check for thumbnail
      name, ext = os.path.splitext(image)
      thumbnail = self.thumbnail_folder + os.path.basename (name) + 't' + ext
      if not os.path.isfile (thumbnail):
	# Create thumbnail
	self.CreateThumbnail (image)
	
      # Load thumbnail
      if not os.access (thumbnail, os.R_OK):
	logging.error ("Can't access " + thumbnail)
	continue

      img = pygame.image.load (thumbnail).convert ()
	
      # Scale image if required
      scale = Scale (img.get_size (), [iwidth, iheight])
      if scale:
	#img = pygame.transform.smoothscale (img, (new_width, new_height))
	img = pygame.transform.scale (img, scale)
	
      # Draw
      self.surface.blit (img, pos)
      
      # Add text
      if TextList:
	text = self.font.render (TextList[Position + count], True, YELLOW)
	#text.get_height ()
	self.surface.blit (text, pos)

      # Next
      count += 1

    # Draw buttons
    self.button_back.draw (self.surface)
    if (Position >= (self.x * self.y)):
      self.button_up.draw ()
    if ((len(ImageList) - Position) > (self.x * self.y)):
      self.button_down.draw ()

    # Return gallery surface
    return self.surface

  # Get selection
  def GetSelection (self, pos):
    if (pos[0] > (self.width - self.button_size[0]) or pos[1] > self.height):
      return -1;

    # Calculate size of each image
    iwidth = int ((self.width - self.button_size[0]) / self.x)
    iheight = int (self.height / self.y)

    sel = (pos[1] / iheight) * self.x
    sel += (pos[0]-1) / iwidth
    
    return int (sel)

  def Ticks (self, Message=''):
    if not self.TickStart:
      self.CurrentTicks = pygame.time.get_ticks ()
      self.TickStart = True
    else:
      print Message + " Ticks: " + str (pygame.time.get_ticks () - self.CurrentTicks)
      self.CurrentTicks = pygame.time.get_ticks ()

  # Run gallery
  def Run (self, screen, ImageList, TextList = []):
    if not ImageList:
      logging.warning ("No images")
      return -2

    Position = 0
    while True:
      # Draw images
      surface = self.Draw (ImageList, Position, TextList)
      screen.blit (surface, [0,0])
      pygame.display.flip ()

      # Wait for event
      while True:
	event = pygame.event.wait ()
	if (event.type == pygame.QUIT) or ('click' in self.button_back.handleEvent(event)):
	  logging.info ("Back")
	  return -1
	elif not event.type == pygame.MOUSEBUTTONUP:
	  continue
	
	if self.button_down.pressed (event.pos):
	  # Down
	  NewPosition = Position + (self.x * self.y)
	  if (NewPosition <= len (ImageList)-1):
	    Position = NewPosition
	    logging.info ('Down')
	    break
	elif self.button_up.pressed (event.pos):
	  # Up
	  NewPosition = Position - (self.x * self.y)
	  if (NewPosition < 0):
	    NewPosition = 0
	  Position = NewPosition
	  logging.info ('Up')
	  break
	  
	# Get selection
	selection = self.GetSelection (event.pos) + Position
	
	if ((selection < len (ImageList)) and (selection >= 0)):
	  logging.info ('Selection ' + str (selection))
	  return selection
