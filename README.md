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
* Resize image for web usage (Finished)
* Upload image to static webserver gallery (Finished)
* Show URL and QRCode of image in the webserver gallery (Finished)

New features (some parts finished, but not yet committed):
* Local HTTP supports showing the current image for remote screen (e.g. tablet on wall in another room) (Finished)
* WhatsApp image serving support: You send an image number to a number running yowsup and get the image to your phone (Finished)
* Admin Telegram support (telepot): Control photobooth, get log, status, receive error messages, ... (WIP)
* Underexposure warning support (for example if the flash does not work): Send warning to Admin via Telegram (WIP)
* Green screen support (WIP)
