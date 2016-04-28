'''
Created Apr, 2016

Licence: GNU AGPL

@author: Sebastian Witt
'''

import sys
import time
import random
import datetime
import telepot
import logging

class pbBot:
  def __init__ (self, Token, AdminId = None):
    self.Token = Token
    self.AdminId = AdminId

    self.bot = telepot.Bot(Token)
    self.bot.message_loop(self.handle)

  def handle(self, msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    #print msg
    #print (content_type, chat_type, chat_id)

    if content_type != 'text':
      return

    text = msg['text']
 
    logging.info (str(chat_id) + ": " + text)

    if not self.AdminId and text == 'IamAdmin':
      self.AdminId = chat_id
      self.bot.sendMessage(self.AdminId, 'You are now admin')
      logging.info (str(chat_id) + " is now Admin")
      return
      
    if self.AdminId and chat_id != self.AdminId:
      logging.warn ('Message not from Admin')
      return
      
  def sendMessage (self, Message):
    if not self.AdminId:
      logging.error ("Admin not connected")
      return
    self.bot.sendMessage(self.AdminId, Message)

  def sendPhoto (self, Image, Caption):
    if not self.AdminId:
      logging.error ("Admin not connected")
      return
    self.bot.sendPhoto(self.AdminId, Image, caption = Caption)