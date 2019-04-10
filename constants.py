import os
import sys
import pygame
from engine import *

SCRIPT_PATH = sys.path[0]

# NO_GIF_TILES -- tile numbers which do not correspond to a GIF file
# currently only "23" for the high-score list
NO_GIF_TILES = [23]

NO_WX = 1  # if set, the high-score code will not attempt to ask the user his name
USER_NAME = "User"  # USER_NAME=os.getlogin() # the default user name if wx fails to load or NO_WX

# Joystick defaults - maybe add a Preferences dialog in the future?
JS_DEVNUM = 0  # device 0 (pygame joysticks always start at 0). if JS_DEVNUM is not a valid device, will use 0
JS_XAXIS = 0  # axis 0 for left//right (default for most joysticks)
JS_YAXIS = 1  # axis 1 for up//down (default for most joysticks)
JS_STARTBUTTON = 0  # button number to start the game. this is a matter of personal preference, and will vary from device to device

clock = pygame.time.Clock()

img_Background = pygame.image.load(
    os.path.join(SCRIPT_PATH, "res", "backgrounds", "1.gif")).convert()

#snd_pellet = {}
#snd_pellet[0] = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "pellet1.wav"))
#snd_pellet[1] = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "pellet2.wav"))
#snd_powerpellet = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "powerpellet.wav"))
#snd_eatgh = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "eatgh2.wav"))
#snd_fruitbounce = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "fruitbounce.wav"))
#snd_eatfruit = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "eatfruit.wav"))
#snd_extralife = pygame.mixer.Sound(
#    os.path.join(SCRIPT_PATH, "res", "sounds", "extralife.wav"))

ghostcolor = {}
ghostcolor[0] = (255, 0, 0, 255)
ghostcolor[1] = (255, 128, 255, 255)
ghostcolor[2] = (128, 255, 255, 255)
ghostcolor[3] = (255, 128, 0, 255)
ghostcolor[4] = (50, 50, 255, 255)  # blue, vulnerable ghost
ghostcolor[5] = (255, 255, 255, 255)  # white, flashing ghost

tileIDName = {}  # gives tile name (when the ID# is known)
tileID = {}  # gives tile ID (when the name is known)
tileIDImage = {}  # gives tile image (when the ID# is known)

class Colors:
    def __init__(self):
        self.edgeLightColor = (255, 255, 0, 255)
        self.edgeShadowColor = (255, 150, 0, 255)
        self.fillColor = (0, 255, 255, 255)
        self.pelletColor = (255, 255, 255, 255)

colors = Colors()
