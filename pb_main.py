'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import pb

pb = pb.photobooth (Name = 'Test',
    FlashAirAddress = '192.168.2.100',
    UploadHost = 'webhost.de',
    UploadUser = 'pb',
    UploadPath = '/var/www/homepage/public/pb',
    QRPath = 'http://webhost.de/pb/#!/test',
    #WhatsAppNumber = '0123 456789')
    WhatsAppNumber = None)

pb.MainLoop ()
