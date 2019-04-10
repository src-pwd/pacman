#!/usr/bin/env python3

# pacman.pyw
# By David Reilly

# Modified by Andy Sommerville, 8 October 2007:
# - Changed hard-coded DOS paths to os.path calls
# - Added constant SCRIPT_PATH (so you don't need to have pacman.pyw and res in your cwd, as long
# -   as those two are in the same directory)
# - Changed text-file reading to accomodate any known EOLn method (\n, \r, or \r\n)
# - I (happily) don't have a Windows box to test this. Blocks marked "WIN???"
# -   should be examined if this doesn't run in Windows
# - Added joystick support (configure by changing JS_* constants)
# - Added a high-score list. Depends on wx for querying the user's name

import pygame, sys, os, random
from pygame.locals import *
from engine import *

from constants import *
from game import thisGame, thisLevel, player, ghosts, thisFruit
from util import *

def CheckIfCloseButton(events):
    for event in events:
        if event.type == QUIT:
            sys.exit(0)


old = False
def CheckInputs():
    global old

    if thisGame.mode == 1:
        if pygame.key.get_pressed()[pygame.K_RIGHT] or (
                js != None and js.get_axis(JS_XAXIS) > 0):
            if not thisLevel.CheckIfHitWall(
                (player.x + player.speed, player.y),
                (player.nearestRow, player.nearestCol)):
                player.velX = player.speed
                player.velY = 0

        elif pygame.key.get_pressed()[pygame.K_LEFT] or (
                js != None and js.get_axis(JS_XAXIS) < 0):
            if not thisLevel.CheckIfHitWall(
                (player.x - player.speed, player.y),
                (player.nearestRow, player.nearestCol)):
                player.velX = -player.speed
                player.velY = 0

        elif pygame.key.get_pressed()[pygame.K_DOWN] or (
                js != None and js.get_axis(JS_YAXIS) > 0):
            if not thisLevel.CheckIfHitWall(
                (player.x, player.y + player.speed),
                (player.nearestRow, player.nearestCol)):
                player.velX = 0
                player.velY = player.speed

        elif pygame.key.get_pressed()[pygame.K_UP] or (
                js != None and js.get_axis(JS_YAXIS) < 0):
            if not thisLevel.CheckIfHitWall(
                (player.x, player.y - player.speed),
                (player.nearestRow, player.nearestCol)):
                player.velX = 0
                player.velY = -player.speed
        elif pygame.key.get_pressed()[pygame.K_d] != old:
            old = pygame.key.get_pressed()[pygame.K_d]
            if old:
                return thisGame.DumpStats()

    if pygame.key.get_pressed()[pygame.K_ESCAPE]:
        sys.exit(0)

    elif thisGame.mode == 3:
        if pygame.key.get_pressed()[pygame.K_RETURN] or (
                js != None and js.get_button(JS_STARTBUTTON)):
            thisGame.StartNewGame()


thisLevel.LoadLevel(thisGame.GetLevelNum())

window = pygame.display.set_mode(thisGame.screenSize,
                                 pygame.DOUBLEBUF | pygame.HWSURFACE)

# initialise the joystick
if pygame.joystick.get_count() > 0:
    if JS_DEVNUM < pygame.joystick.get_count():
        js = pygame.joystick.Joystick(JS_DEVNUM)
    else:
        js = pygame.joystick.Joystick(0)
    js.init()
else:
    js = None

while True:

    CheckIfCloseButton(pygame.event.get())

    if thisGame.mode == 1:
        # normal gameplay mode
        CheckInputs()

        thisGame.modeTimer += 1
        player.Move()
        for i in range(0, 4, 1):
            ghosts[i].Move()
        thisFruit.Move()

    elif thisGame.mode == 2:
        # waiting after getting hit by a ghost
        thisGame.modeTimer += 1

        if thisGame.modeTimer == 90:
            thisLevel.Restart()

            thisGame.lives -= 1
            if thisGame.lives == -1:
                thisGame.updatehiscores(thisGame.score)
                thisGame.SetMode(3)
                thisGame.drawmidgamehiscores()
            else:
                thisGame.SetMode(4)

    elif thisGame.mode == 3:
        # game over
        CheckInputs()

    elif thisGame.mode == 4:
        # waiting to start
        thisGame.modeTimer += 1

        if thisGame.modeTimer == 90:
            thisGame.SetMode(1)
            player.velX = player.speed

    elif thisGame.mode == 5:
        # brief pause after munching a vulnerable ghost
        thisGame.modeTimer += 1

        if thisGame.modeTimer == 30:
            thisGame.SetMode(1)

    elif thisGame.mode == 6:
        # pause after eating all the pellets
        thisGame.modeTimer += 1

        if thisGame.modeTimer == 60:
            thisGame.SetMode(7)
            oldEdgeLightColor = colors.edgeLightColor
            oldEdgeShadowColor = colors.edgeShadowColor
            oldFillColor = colors.fillColor

    elif thisGame.mode == 7:
        # flashing maze after finishing level
        thisGame.modeTimer += 1

        whiteSet = [10, 30, 50, 70]
        normalSet = [20, 40, 60, 80]

        if not whiteSet.count(thisGame.modeTimer) == 0:
            # member of white set
            colors.edgeLightColor = (255, 255, 255, 255)
            colors.edgeShadowColor = (255, 255, 255, 255)
            colors.fillColor = (0, 0, 0, 255)
            GetCrossRef()
        elif not normalSet.count(thisGame.modeTimer) == 0:
            # member of normal set
            colors.edgeLightColor = oldEdgeLightColor
            colors.edgeShadowColor = oldEdgeShadowColor
            colors.fillColor = oldFillColor
            GetCrossRef()
        elif thisGame.modeTimer == 150:
            thisGame.SetMode(8)

    elif thisGame.mode == 8:
        # blank screen before changing levels
        thisGame.modeTimer += 1
        if thisGame.modeTimer == 10:
            thisGame.SetNextLevel()

    thisGame.SmartMoveScreen()

    screen.blit(img_Background, (0, 0))

    if not thisGame.mode == 8:
        thisLevel.DrawMap()

        if thisGame.fruitScoreTimer > 0:
            if thisGame.modeTimer % 2 == 0:
                thisGame.DrawNumber(
                    2500, (thisFruit.x - thisGame.screenPixelPos[0] - 16,
                           thisFruit.y - thisGame.screenPixelPos[1] + 4))

        for i in range(0, 4, 1):
            ghosts[i].Draw()
        thisFruit.Draw()
        player.Draw()

        if thisGame.mode == 3:
            screen.blit(thisGame.imHiscores, (32, 256))

    if thisGame.mode == 5:
        thisGame.DrawNumber(thisGame.ghostValue // 2,
                            (player.x - thisGame.screenPixelPos[0] - 4,
                             player.y - thisGame.screenPixelPos[1] + 6))

    thisGame.DrawScore()

    pygame.display.flip()

    clock.tick(60)
