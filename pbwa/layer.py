import logging
import sys
import os
import glob
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from yowsup.layers.protocol_media.protocolentities     import *
from yowsup.layers.protocol_media.mediauploader        import MediaUploader
from yowsup.common.tools                               import Jid
from yowsup.common                                     import YowConstants

class EchoLayer(YowInterfaceLayer):
    # Params
    def SetParams(self, ImagePath, AdminNumber = None, GetCaption = None):
      if not os.path.exists (ImagePath):
        print ("ImagePath does not exist: " + ImagePath)
        raise
      self.ImagePath = ImagePath
      self.AdminNumber = AdminNumber
      self.GetCaption = GetCaption
      self.FileTypes = ('*.jpg', '*.JPG')
      self.ReceiveCount = 0
      self.NotFoundCount = 0
      self.ImageCount = 0
      self.DuplicateCount = 0
      if self.AdminNumber:
        self.AdminNumber += '@' + YowConstants.DOMAIN
      if not self.GetCaption:
        self.GetCaption = lambda f: os.path.basename (f)
    
    # Get image file list
    def GetFiles (self, SubString = None):
      # Get list of all files
      files = []
      for t in self.FileTypes:
        files.extend(glob.glob (os.path.join (self.ImagePath, t)))
      
      # Optional: Search for substring
      if SubString:
        files = [s for s in files if SubString in s]

      return files
    
    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
      self.ReceiveCount += 1
      From = messageProtocolEntity.getFrom()
      # Send receipt
      receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), From, 'read', messageProtocolEntity.getParticipant())
      self.toLower(receipt)
      
      # Get message text
      text = messageProtocolEntity.getBody()
      
      logging.info ("Message " + From + ": " + text)

      # Check if it's a picture number
      if text.isdigit ():
        # Get matching images
        files = self.GetFiles (text)

        if files:
          # Send image
          self.image_send(From, files[0], self.GetCaption (files[0]))
          self.ImageCount += 1
        else:
          # Image nof found, send error message
          outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            'Bild Nummer ' + messageProtocolEntity.getBody() + ' nicht gefunden',
            to = From)

          self.toLower(outgoingMessageProtocolEntity)
          self.NotFoundCount += 1
        
        return
      
      # Check for message from admin
      print (From)
      if From == self.AdminNumber:
        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            "Receive: %u, NotFound: %u, Images: %u, Duplicate: %u" % (self.ReceiveCount, self.NotFoundCount, self.ImageCount, self.DuplicateCount),
            to = From)

        self.toLower(outgoingMessageProtocolEntity)
          
          
    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        #ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        #self.toLower(ack)
        self.toLower(entity.ack())
    
    @ProtocolEntityCallback("ack")
    def onAck(self, entity):
        if entity.getClass() == "message":
            print (entity.getId(), "Sent")
        
        
    # Image functions
    # Copied from yowsup-cli
    def image_send(self, number, path, caption = None):
        self.media_send(number, path, RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, caption)
        
    def media_send(self, number, path, mediaType, caption = None):
        jid = Jid.normalize(number)
        entity = RequestUploadIqProtocolEntity(mediaType, filePath=path)
        successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, mediaType, path, successEntity, originalEntity, caption)
        errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)
        self._sendIq(entity, successFn, errorFn)

    def doSendMedia(self, mediaType, filePath, url, to, ip = None, caption = None):
        if mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE:
          entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
          entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to)
        elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO:
          entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        self.toLower(entity)

    def onRequestUploadResult(self, jid, mediaType, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):

        if resultRequestUploadIqProtocolEntity.isDuplicate():
            print ("DUPLICATE")
            self.DuplicateCount += 1
            self.doSendMedia(mediaType, filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
                             resultRequestUploadIqProtocolEntity.getIp(), caption)
        else:
            successFn = lambda filePath, jid, url: self.doSendMedia(mediaType, filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
            mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
                                      resultRequestUploadIqProtocolEntity.getUrl(),
                                      resultRequestUploadIqProtocolEntity.getResumeOffset(),
                                      successFn, self.onUploadError, self.onUploadProgress, async=False)
            mediaUploader.start()

    def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
        logging.error("Request upload for file %s for %s failed" % (path, jid))

    def onUploadError(self, filePath, jid, url):
        logging.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

    def onUploadProgress(self, filePath, jid, url, progress):
        sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
        sys.stdout.flush()