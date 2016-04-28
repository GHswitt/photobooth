# photobooth
Photobooth software written in Python. Uses FlashAir WLAN SD-Card, touch display and photo printer.

My system setup looks like this:

* IR-Remote (for triggering the camera)
* Camera with FlashAir WLAN SD-card
* System with WLAN, Touchdisplay (or normal display and mouse)
* Photo printer

## Features

* Watch for new JPEG files on FlashAIR card
* Show newest image on display after capturing
* Create thumbnails for gallery
* Show all images in a simple gallery
* Resize image for printing (when required)
* Print an image on a connected printer (CUPS)
* Mark images as printed and add them to a list
* Opens HTTP port on 8080 to watch current screen and logfile from remote devices (smartphone)
* Resize image for web usage
* Upload image to static webserver gallery
* Show URL and QRCode of image in the webserver gallery
* Local HTTP supports showing the current image for remote screen (e.g. tablet on wall in another room)
* WhatsApp image serving support: You send an image number to a number running yowsup and get the image to your phone 
* Underexposure warning support
* Admin Telegram support (telepot): Receive errors and warnings, receive underexposed images

## Screenshots
**Main view**
![alt text](docs/PB_20160427.jpg "Main view")
**Gallery view**
![alt text](docs/PB_Galerie_20160427.jpg "Gallery view")

## Requirements
* pygame
* pillow
* cups (for printing)
* paramiko (for web upload)
* rsync (for web upload)
* pyqrcode (for QRCode display)
* yowsup (WhatsApp support)
* telepot (Remote control and status)

## Installation
''TODO''

## Configuration
''TODO''
