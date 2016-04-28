import logging
import os
from layer                                    import EchoLayer
from yowsup.layers                            import YowParallelLayer
from yowsup.layers.auth                       import YowAuthenticationProtocolLayer
from yowsup.layers.protocol_messages          import YowMessagesProtocolLayer
from yowsup.layers.protocol_media             import YowMediaProtocolLayer
from yowsup.layers.protocol_receipts          import YowReceiptProtocolLayer
from yowsup.layers.protocol_acks              import YowAckProtocolLayer
from yowsup.layers.network                    import YowNetworkLayer
from yowsup.layers.coder                      import YowCoderLayer
from yowsup.stacks                            import YowStack
from yowsup.common                            import YowConstants
from yowsup.layers                            import YowLayerEvent
from yowsup.stacks                            import YowStack, YOWSUP_CORE_LAYERS
from yowsup.layers.axolotl                    import YowAxolotlLayer
from yowsup.env                               import YowsupEnv
from yowsup.stacks                            import  YowStackBuilder

# Configuration
CREDENTIALS = ("4943214321", "Password")
ImagePath = '/home/pb/pb/albums/Test'
AdminNumber = '4912345678'
CaptionFunction = lambda f: 'http://webserver.com/pb/#!/test/' + os.path.basename (f).lower ()


if __name__==  "__main__":
    logging.basicConfig (filename='pbwa.log', level=logging.INFO, format='%(asctime)s %(levelname)-7s %(module)-8s/%(funcName)-8s: %(message)s')
    
    layers = (
        EchoLayer,
        YowParallelLayer([YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowMediaProtocolLayer, YowReceiptProtocolLayer,
                          YowAckProtocolLayer]), YowAxolotlLayer
    ) + YOWSUP_CORE_LAYERS

    stack = YowStack(layers)
    stack.setProp(YowAuthenticationProtocolLayer.PROP_CREDENTIALS, CREDENTIALS)         #setting credentials
    stack.setProp(YowNetworkLayer.PROP_ENDPOINT, YowConstants.ENDPOINTS[0])    #whatsapp server address
    stack.setProp(YowCoderLayer.PROP_DOMAIN, YowConstants.DOMAIN)              
    stack.setProp(YowCoderLayer.PROP_RESOURCE, YowsupEnv.getCurrent().getResource())          #info about us as WhatsApp client

    #stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))   #sending the connect signal

    #stackBuilder = YowStackBuilder()

    #stack = stackBuilder\
    #    .pushDefaultLayers(True)\
    #    .push(EchoLayer)\
    #    .build()
    
    # Set parameters
    l = stack.getLayer(-1)
    l.SetParams (ImagePath, AdminNumber, CaptionFunction)
    
    stack.setCredentials(CREDENTIALS)
    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
    
    # Main loop
    stack.loop()