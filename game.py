import os
import random
import pygame
import gc
import tracemalloc
from timeit import default_timer as timer

from constants import *
from path import path
from util import *
from engine import *
from ai import *
from math import copysign

collecting_stats = False

tracemalloc.start()

stats = {
        'min': 999999999999,
        'max': 0,
        'total': 0,
        'count': 0,
}


mem_stats = stats.copy()
time_stats = stats.copy()
step_stats = stats.copy()
stats_by_path_len = stats.copy()
stats_by_steps = stats.copy()
stats_by_distance = stats.copy()
efficiency = stats.copy() # path len by md
steps_by_len = stats.copy()
steps_by_distance = stats.copy()

stat = {
        'Memory usage': mem_stats,
        'Elapsed time': time_stats,
        'Made steps': step_stats,
        'Mem / path length': stats_by_path_len,
        'Mem / steps': stats_by_steps,
        'Mem / distance': stats_by_distance,
        'Len / distance': efficiency,
        'Steps / len': steps_by_len,
        'Steps / distance': steps_by_distance,
}

def ins(dct, val):
    dct['min'] = min(dct['min'], val)
    dct['max'] = max(dct['max'], val)
    dct['total'] += val
    dct['count'] += 1

def measure(finder, *args):
    if not collecting_stats:
        return finder.find_pred(*args)
    gc.collect()
    s1 = tracemalloc.take_snapshot()
    start = timer()
    path, steps = finder.find_pred(*args)
    if len(path) == 0: return path, 0
    end = timer()
    s2 = tracemalloc.take_snapshot()
    ps = s2.compare_to(s1, 'lineno')
    mem_usage = sum(map(lambda x: x.size_diff, ps))
    if mem_usage < 0: return path, 0
    elapsed = end - start
    src = args[0]
    dst = path[-1]
    dist = sum(map(lambda a: abs(a[0] - a[1]), zip(src, dst)))
    ins(mem_stats, mem_usage)
    ins(time_stats, elapsed)
    ins(step_stats, steps)
    ins(stats_by_path_len, mem_usage / len(path))
    ins(stats_by_steps, mem_usage / steps)
    ins(stats_by_distance, mem_usage / dist)
    ins(efficiency, len(path) / dist)
    ins(steps_by_len, steps / len(path))
    ins(steps_by_distance, steps / dist)
    return path, steps

class Game():
    def DumpStats(self):
        print('Stats:')
        for k, v in stat.items():
            if v['count'] > 0: v['avg'] = v['total'] / v['count']
            print('   ', k, v)

    def defaulthiscorelist(self):
        return [(100000, "David"), (80000, "Andy"), (60000, "Count Pacula"),
                (40000, "Cleopacra"), (20000, "Brett Favre"),
                (10000, "Sergei Pachmaninoff")]

    def gethiscores(self):
        """If res//hiscore.txt exists, read it. If not, return the default high scores.
               Output is [ (score,name) , (score,name) , .. ]. Always 6 entries."""
        try:
            f = open(os.path.join(SCRIPT_PATH, "res", "hiscore.txt"))
            hs = []
            for line in f:
                while len(line) > 0 and (line[0] == "\n" or line[0] == "\r"):
                    line = line[1:]
                while len(line) > 0 and (line[-1] == "\n" or line[-1] == "\r"):
                    line = line[:-1]
                score = int(line.split(" ")[0])
                name = line.partition(" ")[2]
                if score > 99999999: score = 99999999
                if len(name) > 22: name = name[:22]
                hs.append((score, name))
            f.close()
            if len(hs) > 6: hs = hs[:6]
            while len(hs) < 6:
                hs.append((0, ""))
            return hs
        except IOError:
            return self.defaulthiscorelist()

    def writehiscores(self, hs):
        """Given a new list, write it to the default file."""
        fname = os.path.join(SCRIPT_PATH, "res", "hiscore.txt")
        f = open(fname, "w")
        for line in hs:
            f.write(str(line[0]) + " " + line[1] + "\n")
        f.close()

    def getplayername(self):
        """Ask the player his name, to go on the high-score list."""
        if NO_WX: return USER_NAME
        try:
            import wx
        except:
            print("Pacman Error: No module wx. Can not ask the user his name!")
            print("     :(       Download wx from http:////www.wxpython.org//")
            print(
                "     :(       To avoid seeing this error again, set NO_WX in file pacman.pyw."
            )
            return USER_NAME
        app = wx.App(None)
        dlog = wx.TextEntryDialog(None, "You made the high-score list! Name:")
        dlog.ShowModal()
        name = dlog.GetValue()
        dlog.Destroy()
        app.Destroy()
        return name

    def updatehiscores(self, newscore):
        """Add newscore to the high score list, if appropriate."""
        hs = self.gethiscores()
        for line in hs:
            if newscore >= line[0]:
                hs.insert(hs.index(line), (newscore, self.getplayername()))
                hs.pop(-1)
                break
        self.writehiscores(hs)

    def makehiscorelist(self):
        "Read the High-Score file and convert it to a useable Surface."
        # My apologies for all the hard-coded constants.... -Andy
        f = pygame.font.Font(
            os.path.join(SCRIPT_PATH, "res", "VeraMoBd.ttf"), 10)
        scoresurf = pygame.Surface((276, 86), pygame.SRCALPHA)
        scoresurf.set_alpha(200)
        linesurf = f.render(" " * 18 + "HIGH SCORES", 1, (255, 255, 0))
        scoresurf.blit(linesurf, (0, 0))
        hs = self.gethiscores()
        vpos = 0
        for line in hs:
            vpos += 12
            linesurf = f.render(line[1].rjust(22) + str(line[0]).rjust(9), 1,
                                (255, 255, 255))
            scoresurf.blit(linesurf, (0, vpos))
        return scoresurf

    def drawmidgamehiscores(self):
        """Redraw the high-score list image after pacman dies."""
        self.imHiscores = self.makehiscorelist()

    def __init__(self):
        self.levelNum = 0
        self.score = 0
        self.lives = 3

        # game "mode" variable
        # 1 = normal
        # 2 = hit ghost
        # 3 = game over
        # 4 = wait to start
        # 5 = wait after eating ghost
        # 6 = wait after finishing level
        self.mode = 0
        self.modeTimer = 0
        self.ghostTimer = 0
        self.ghostValue = 0
        self.fruitTimer = 0
        self.fruitScoreTimer = 0
        self.fruitScorePos = (0, 0)

        self.SetMode(3)

        # camera variables
        self.screenPixelPos = (
            0, 0
        )  # absolute x,y position of the screen from the upper-left corner of the level
        self.screenNearestTilePos = (
            0, 0)  # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (
            0,
            0)  # offset in pixels of the screen from its nearest-tile position

        self.screenTileSize = (23, 21)
        self.screenSize = (self.screenTileSize[1] * 16,
                           self.screenTileSize[0] * 16)

        # numerical display digits
        self.digit = {}
        for i in range(0, 10, 1):
            self.digit[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "text",
                             str(i) + ".gif")).convert()
        self.imLife = pygame.image.load(
            os.path.join(SCRIPT_PATH, "res", "text", "life.gif")).convert()
        self.imGameOver = pygame.image.load(
            os.path.join(SCRIPT_PATH, "res", "text",
                         "gameover.gif")).convert()
        self.imReady = pygame.image.load(
            os.path.join(SCRIPT_PATH, "res", "text", "ready.gif")).convert()
        self.imLogo = pygame.image.load(
            os.path.join(SCRIPT_PATH, "res", "text", "logo.gif")).convert()
        self.imHiscores = self.makehiscorelist()

    def StartNewGame(self):
        self.levelNum = 1
        self.score = 0
        self.lives = 3

        self.SetMode(4)
        thisLevel.LoadLevel(thisGame.GetLevelNum())

    def AddToScore(self, amount):

        extraLifeSet = [25000, 50000, 100000, 150000]

        for specialScore in extraLifeSet:
            if self.score < specialScore and self.score + amount >= specialScore:
                #snd_extralife.play()
                thisGame.lives += 1

        self.score += amount

    def DrawScore(self):
        self.DrawNumber(self.score, (24 + 16, self.screenSize[1] - 24))

        for i in range(0, self.lives, 1):
            screen.blit(self.imLife,
                        (24 + i * 10 + 16, self.screenSize[1] - 12))

        screen.blit(thisFruit.imFruit[thisFruit.fruitType],
                    (4 + 16, self.screenSize[1] - 20))

        if self.mode == 3:
            screen.blit(
                self.imGameOver,
                (self.screenSize[0] // 2 - 32, self.screenSize[1] // 2 - 10))
        elif self.mode == 4:
            screen.blit(
                self.imReady,
                (self.screenSize[0] // 2 - 20, self.screenSize[1] // 2 + 12))

        self.DrawNumber(self.levelNum, (0, self.screenSize[1] - 12))

    def DrawNumber(self, number, xxx_todo_changeme):
        (x, y) = xxx_todo_changeme
        strNumber = str(number)

        for i in range(0, len(str(number)), 1):
            iDigit = int(strNumber[i])
            screen.blit(self.digit[iDigit], (x + i * 9, y))

    def SmartMoveScreen(self):

        possibleScreenX = player.x - self.screenTileSize[1] // 2 * 16
        possibleScreenY = player.y - self.screenTileSize[0] // 2 * 16

        if possibleScreenX < 0:
            possibleScreenX = 0
        elif possibleScreenX > thisLevel.lvlWidth * 16 - self.screenSize[0]:
            possibleScreenX = thisLevel.lvlWidth * 16 - self.screenSize[0]

        if possibleScreenY < 0:
            possibleScreenY = 0
        elif possibleScreenY > thisLevel.lvlHeight * 16 - self.screenSize[1]:
            possibleScreenY = thisLevel.lvlHeight * 16 - self.screenSize[1]

        thisGame.MoveScreen((possibleScreenX, possibleScreenY))

    def MoveScreen(self, xxx_todo_changeme1):
        (newX, newY) = xxx_todo_changeme1
        self.screenPixelPos = (newX, newY)
        self.screenNearestTilePos = (
            int(newY // 16), int(newX // 16)
        )  # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (newX - self.screenNearestTilePos[1] * 16,
                                  newY - self.screenNearestTilePos[0] * 16)

    def GetScreenPos(self):
        return self.screenPixelPos

    def GetLevelNum(self):
        return self.levelNum

    def SetNextLevel(self):
        self.levelNum += 1

        self.SetMode(4)
        thisLevel.LoadLevel(thisGame.GetLevelNum())

        player.velX = 0
        player.velY = 0
        player.anim_pacmanCurrent = player.anim_pacmanS

    def SetMode(self, newMode):
        player.path = []
        self.mode = newMode
        self.modeTimer = 0
        # print " ***** GAME MODE IS NOW ***** " + str(newMode)

class Level():
    def __init__(self):
        self.lvlWidth = 0
        self.lvlHeight = 0

        self.map = {}

        self.pellets = 0
        self.powerPelletBlinkTimer = 0

    def SetMapTile(self, xxx_todo_changeme23, newValue):
        (row, col) = xxx_todo_changeme23
        self.map[(row * self.lvlWidth) + col] = newValue

    def GetMapTile(self, xxx_todo_changeme24):
        (row, col) = xxx_todo_changeme24
        if row >= 0 and row < self.lvlHeight and col >= 0 and col < self.lvlWidth:
            return self.map[(row * self.lvlWidth) + col]
        else:
            return 0

    def IsWall(self, xxx_todo_changeme25):

        (row, col) = xxx_todo_changeme25
        if row > thisLevel.lvlHeight - 1 or row < 0:
            return True

        if col > thisLevel.lvlWidth - 1 or col < 0:
            return True

        # check the offending tile ID
        result = thisLevel.GetMapTile((row, col))

        # if the tile was a wall
        if result >= 100 and result <= 199:
            return True
        else:
            return False

    def CheckIfHitWall(self, xxx_todo_changeme26, xxx_todo_changeme27):

        (possiblePlayerX, possiblePlayerY) = xxx_todo_changeme26
        (row, col) = xxx_todo_changeme27
        numCollisions = 0

        # check each of the 9 surrounding tiles for a collision
        for iRow in range(row - 1, row + 2, 1):
            for iCol in range(col - 1, col + 2, 1):

                if (possiblePlayerX - (iCol * 16) <
                        16) and (possiblePlayerX - (iCol * 16) > -16) and (
                            possiblePlayerY - (iRow * 16) <
                            16) and (possiblePlayerY - (iRow * 16) > -16):

                    if self.IsWall((iRow, iCol)):
                        numCollisions += 1

        if numCollisions > 0:
            return True
        else:
            return False

    def CheckIfHit(self, xxx_todo_changeme28, xxx_todo_changeme29, cushion):

        (playerX, playerY) = xxx_todo_changeme28
        (x, y) = xxx_todo_changeme29
        if (playerX - x < cushion) and (playerX - x > -cushion) and (
                playerY - y < cushion) and (playerY - y > -cushion):
            return True
        else:
            return False

    def CheckIfHitSomething(self, xxx_todo_changeme30, xxx_todo_changeme31):

        (playerX, playerY) = xxx_todo_changeme30
        (row, col) = xxx_todo_changeme31
        for iRow in range(row - 1, row + 2, 1):
            for iCol in range(col - 1, col + 2, 1):

                if (playerX -
                    (iCol * 16) < 16) and (playerX - (iCol * 16) > -16) and (
                        playerY - (iRow * 16) < 16) and (playerY -
                                                         (iRow * 16) > -16):
                    # check the offending tile ID
                    result = thisLevel.GetMapTile((iRow, iCol))

                    if result == tileID['pellet']:
                        # got a pellet
                        thisLevel.SetMapTile((iRow, iCol), 0)
                        #snd_pellet[player.pelletSndNum].play()
                        player.pelletSndNum = 1 - player.pelletSndNum

                        thisLevel.pellets -= 1

                        thisGame.AddToScore(10)

                        if thisLevel.pellets == 0:
                            # no more pellets left!
                            # WON THE LEVEL
                            thisGame.SetMode(6)

                    elif result == tileID['pellet-power']:
                        # got a power pellet
                        thisLevel.SetMapTile((iRow, iCol), 0)
                        #snd_powerpellet.play()

                        thisGame.AddToScore(100)
                        thisGame.ghostValue = 200

                        thisGame.ghostTimer = 360
                        for i in range(0, 4, 1):
                            if ghosts[i].state == 1:
                                ghosts[i].state = 2

                    elif result == tileID['door-h']:
                        # ran into a horizontal door
                        for i in range(0, thisLevel.lvlWidth, 1):
                            if not i == iCol:
                                if thisLevel.GetMapTile(
                                    (iRow, i)) == tileID['door-h']:
                                    player.x = i * 16
                                    player.path = []

                                    if player.velX > 0:
                                        player.x += 16
                                    else:
                                        player.x -= 16

                    elif result == tileID['door-v']:
                        # ran into a vertical door
                        for i in range(0, thisLevel.lvlHeight, 1):
                            if not i == iRow:
                                if thisLevel.GetMapTile(
                                    (i, iCol)) == tileID['door-v']:
                                    player.y = i * 16
                                    player.path = []

                                    if player.velY > 0:
                                        player.y += 16
                                    else:
                                        player.y -= 16

    def GetGhostBoxPos(self):

        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.GetMapTile((row, col)) == tileID['ghost-door']:
                    return (row, col)

        return False

    def GetPathwayPairPos(self):

        doorArray = []

        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.GetMapTile((row, col)) == tileID['door-h']:
                    # found a horizontal door
                    doorArray.append((row, col))
                elif self.GetMapTile((row, col)) == tileID['door-v']:
                    # found a vertical door
                    doorArray.append((row, col))

        if len(doorArray) == 0:
            return False

        chosenDoor = random.randint(0, len(doorArray) - 1)

        if self.GetMapTile(doorArray[chosenDoor]) == tileID['door-h']:
            # horizontal door was chosen
            # look for the opposite one
            for i in range(0, thisLevel.lvlWidth, 1):
                if not i == doorArray[chosenDoor][1]:
                    if thisLevel.GetMapTile((doorArray[chosenDoor][0],
                                             i)) == tileID['door-h']:
                        return doorArray[chosenDoor], (
                            doorArray[chosenDoor][0], i)
        else:
            # vertical door was chosen
            # look for the opposite one
            for i in range(0, thisLevel.lvlHeight, 1):
                if not i == doorArray[chosenDoor][0]:
                    if thisLevel.GetMapTile(
                        (i, doorArray[chosenDoor][1])) == tileID['door-v']:
                        return doorArray[chosenDoor], (
                            i, doorArray[chosenDoor][1])

        return False

    def PrintMap(self):

        for row in range(0, self.lvlHeight, 1):
            outputLine = ""
            for col in range(0, self.lvlWidth, 1):

                outputLine += str(self.GetMapTile((row, col))) + ", "

            # print outputLine

    def DrawMap(self):

        self.powerPelletBlinkTimer += 1
        if self.powerPelletBlinkTimer == 60:
            self.powerPelletBlinkTimer = 0

        for row in range(-1, thisGame.screenTileSize[0] + 1, 1):
            outputLine = ""
            for col in range(-1, thisGame.screenTileSize[1] + 1, 1):

                # row containing tile that actually goes here
                actualRow = thisGame.screenNearestTilePos[0] + row
                actualCol = thisGame.screenNearestTilePos[1] + col

                useTile = self.GetMapTile((actualRow, actualCol))
                if not useTile == 0 and not useTile == tileID[
                        'door-h'] and not useTile == tileID['door-v']:
                    # if this isn't a blank tile

                    if useTile == tileID['pellet-power']:
                        if self.powerPelletBlinkTimer < 30:
                            screen.blit(
                                tileIDImage[useTile],
                                (col * 16 - thisGame.screenPixelOffset[0],
                                 row * 16 - thisGame.screenPixelOffset[1]))

                    elif useTile == tileID['showlogo']:
                        screen.blit(thisGame.imLogo,
                                    (col * 16 - thisGame.screenPixelOffset[0],
                                     row * 16 - thisGame.screenPixelOffset[1]))

                    elif useTile == tileID['hiscores']:
                        screen.blit(thisGame.imHiscores,
                                    (col * 16 - thisGame.screenPixelOffset[0],
                                     row * 16 - thisGame.screenPixelOffset[1]))

                    else:
                        screen.blit(tileIDImage[useTile],
                                    (col * 16 - thisGame.screenPixelOffset[0],
                                     row * 16 - thisGame.screenPixelOffset[1]))

    def LoadLevel(self, levelNum):

        self.map = {}

        self.pellets = 0

        f = open(
            os.path.join(SCRIPT_PATH, "res", "levels",
                         str(levelNum) + ".txt"), 'r')
        # ANDY -- edit this
        #fileOutput = f.read()
        #str_splitByLine = fileOutput.split('\n')
        lineNum = -1
        rowNum = 0
        useLine = False
        isReadingLevelData = False

        for line in f:

            lineNum += 1

            # print " ------- Level Line " + str(lineNum) + " -------- "
            while len(line) > 0 and (line[-1] == "\n" or line[-1] == "\r"):
                line = line[:-1]
            while len(line) > 0 and (line[0] == "\n" or line[0] == "\r"):
                line = line[1:]
            str_splitBySpace = line.split(' ')

            j = str_splitBySpace[0]

            if (j == "'" or j == ""):
                # comment // whitespace line
                # print " ignoring comment line.. "
                useLine = False
            elif j == "#":
                # special divider // attribute line
                useLine = False

                firstWord = str_splitBySpace[1]

                if firstWord == "lvlwidth":
                    self.lvlWidth = int(str_splitBySpace[2])
                    # print "Width is " + str( self.lvlWidth )

                elif firstWord == "lvlheight":
                    self.lvlHeight = int(str_splitBySpace[2])
                    # print "Height is " + str( self.lvlHeight )

                elif firstWord == "edgecolor":
                    # edge color keyword for backwards compatibility (single edge color) mazes
                    red = int(str_splitBySpace[2])
                    green = int(str_splitBySpace[3])
                    blue = int(str_splitBySpace[4])
                    colors.edgeLightColor = (red, green, blue, 255)
                    colors.edgeShadowColor = (red, green, blue, 255)

                elif firstWord == "edgelightcolor":
                    red = int(str_splitBySpace[2])
                    green = int(str_splitBySpace[3])
                    blue = int(str_splitBySpace[4])
                    colors.edgeLightColor = (red, green, blue, 255)

                elif firstWord == "edgeshadowcolor":
                    red = int(str_splitBySpace[2])
                    green = int(str_splitBySpace[3])
                    blue = int(str_splitBySpace[4])
                    colors.edgeShadowColor = (red, green, blue, 255)

                elif firstWord == "fillcolor":
                    red = int(str_splitBySpace[2])
                    green = int(str_splitBySpace[3])
                    blue = int(str_splitBySpace[4])
                    colors.fillColor = (red, green, blue, 255)

                elif firstWord == "pelletcolor":
                    red = int(str_splitBySpace[2])
                    green = int(str_splitBySpace[3])
                    blue = int(str_splitBySpace[4])
                    colors.pelletColor = (red, green, blue, 255)

                elif firstWord == "fruittype":
                    thisFruit.fruitType = int(str_splitBySpace[2])

                elif firstWord == "startleveldata":
                    isReadingLevelData = True
                    # print "Level data has begun"
                    rowNum = 0

                elif firstWord == "endleveldata":
                    isReadingLevelData = False
                    # print "Level data has ended"

            else:
                useLine = True

            # this is a map data line
            if useLine == True:

                if isReadingLevelData == True:

                    # print str( len(str_splitBySpace) ) + " tiles in this column"

                    for k in range(0, self.lvlWidth, 1):
                        self.SetMapTile((rowNum, k), int(str_splitBySpace[k]))

                        thisID = int(str_splitBySpace[k])
                        if thisID == 4:
                            # starting position for pac-man

                            player.homeX = k * 16
                            player.homeY = rowNum * 16
                            self.SetMapTile((rowNum, k), 0)

                        elif thisID >= 10 and thisID <= 13:
                            # one of the ghosts

                            ghosts[thisID - 10].homeX = k * 16
                            ghosts[thisID - 10].homeY = rowNum * 16
                            self.SetMapTile((rowNum, k), 0)

                        elif thisID == 2:
                            # pellet

                            self.pellets += 1

                    rowNum += 1

        # reload all tiles and set appropriate colors
        GetCrossRef()

        # load map into the pathfinder object
        path.ResizeMap((self.lvlHeight, self.lvlWidth))

        for row in range(0, path.size[0], 1):
            for col in range(0, path.size[1], 1):
                if self.IsWall((row, col)):
                    path.SetType((row, col), 1)
                else:
                    path.SetType((row, col), 0)

        # do all the level-starting stuff
        self.Restart()

    def Restart(self):

        for i in range(0, 4, 1):
            # move ghosts back to home

            ghosts[i].x = ghosts[i].homeX
            ghosts[i].y = ghosts[i].homeY
            ghosts[i].velX = 0
            ghosts[i].velY = 0
            ghosts[i].state = 1
            ghosts[i].speed = 1
            ghosts[i].Move()

            # give each ghost a path to a random spot (containing a pellet)
            (randRow, randCol) = (0, 0)

            while not self.GetMapTile(
                (randRow, randCol)) == tileID['pellet'] or (randRow,
                                                            randCol) == (0, 0):
                randRow = random.randint(1, self.lvlHeight - 2)
                randCol = random.randint(1, self.lvlWidth - 2)

            # print "Ghost " + str(i) + " headed towards " + str((randRow, randCol))
            ghosts[i].currentPath = path.FindPath(
                (ghosts[i].nearestRow, ghosts[i].nearestCol),
                (randRow, randCol))
            ghosts[i].FollowNextPathWay()

        thisFruit.active = False

        thisGame.fruitTimer = 0

        player.x = player.homeX
        player.y = player.homeY
        player.velX = 0
        player.velY = 0

        player.anim_pacmanCurrent = player.anim_pacmanS
        player.animFrame = 3

class Pacman():
    def __init__(self):
        path.pacman = self
        self.path_finder = IDFS()
        self.path = []
        self.x = 0
        self.y = 0
        self.velX = 0
        self.velY = 0
        self.speed = 2

        self.nearestRow = 0
        self.nearestCol = 0

        self.homeX = 0
        self.homeY = 0

        self.anim_pacmanL = {}
        self.anim_pacmanR = {}
        self.anim_pacmanU = {}
        self.anim_pacmanD = {}
        self.anim_pacmanS = {}
        self.anim_pacmanCurrent = {}

        for i in range(1, 9, 1):
            self.anim_pacmanL[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "pacman-l " + str(i) + ".gif")).convert()
            self.anim_pacmanR[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "pacman-r " + str(i) + ".gif")).convert()
            self.anim_pacmanU[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "pacman-u " + str(i) + ".gif")).convert()
            self.anim_pacmanD[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "pacman-d " + str(i) + ".gif")).convert()
            self.anim_pacmanS[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "pacman.gif")).convert()

        self.pelletSndNum = 0

    def GhostDistances(self, position=None):
        if position is not None:
            row, col = position
        else:
            row, col = self.nearestRow, self.nearestCol
        return [(abs(row- (ghosts[i].y + 8) // 16), abs(col - (ghosts[i].x + 8) // 16)) for i in range(0,4,1) if ghosts[i].state == 1]

    def Move(self):

        self.nearestRow = int(((self.y + 8) // 16))
        self.nearestCol = int(((self.x + 8) // 16))
        #print((self.nearestRow, self.nearestCol), '!!!', self.path)

        
        md = 1000
        if len(self.GhostDistances()):
            md = min(sum(x) for x in self.GhostDistances())

        if len(self.GhostDistances()) and md < 3:
            if isinstance(self.path, DFS):
                self.path, steps = self.path_finder.find_pred((self.nearestRow, self.nearestCol), lambda p: min(sum(x) for x in self.GhostDistances(p)) > md, get_neighbors_running)
                if not self.path:
                    self.path, steps = self.path_finder.find_pred((self.nearestRow, self.nearestCol), lambda p: min(sum(x) for x in self.GhostDistances(p)) > 4, get_neighbors)
            elif isinstance(self.path, Greedy):
                self.path, steps = self.path_finder.find_pred2((self.nearestRow, self.nearestCol), lambda p: min(sum(x) for x in self.GhostDistances(p)) > 4, get_neighbors, lambda p: 2 * (4 - min(sum(x) for x in self.GhostDistances(p))))
            else:
                self.path, steps = self.path_finder.find_pred((self.nearestRow, self.nearestCol), lambda p: min(sum(x) for x in self.GhostDistances(p)) > 4, get_neighbors)
            target = self.path[0]
            dt = (target[0] * 16 - self.y, target[1] * 16 - self.x)
            if dt[0] != 0 and dt[1] != 0:
                self.path.insert(0, (self.nearestRow, self.nearestCol))

        if len(self.path) == 0:
            self.path, steps = measure(self.path_finder, (self.nearestRow, self.nearestCol), lambda p: thisLevel.GetMapTile(p) in [tileID['pellet'], tileID['pellet-power']], get_neighbors)
        target = self.path[0]
        dt = (target[0] * 16 - self.y, target[1] * 16 - self.x)
        #print(dt)
        if dt == (0, 0):
            self.path = self.path[1:]
            if len(self.path): target = self.path[0]
            dt = (target[0] * 16 - self.y, target[1] * 16 - self.x)
        self.velX = copysign(self.speed, dt[1]) if dt[1] else 0
        self.velY = copysign(self.speed, dt[0]) if dt[0] else 0
        #print(self.velX, self.velY)
        

        # make sure the current velocity will not cause a collision before moving
        if not thisLevel.CheckIfHitWall(
            (self.x + self.velX, self.y + self.velY),
            (self.nearestRow, self.nearestCol)):

            self.x += self.velX
            self.y += self.velY

            # check for collisions with other tiles (pellets, etc)
            thisLevel.CheckIfHitSomething((self.x, self.y),
                                          (self.nearestRow, self.nearestCol))

            # check for collisions with the ghosts
            for i in range(0, 4, 1):
                if thisLevel.CheckIfHit((self.x, self.y),
                                        (ghosts[i].x, ghosts[i].y), 8):
                    # hit a ghost

                    if ghosts[i].state == 1:
                        # ghost is normal
                        thisGame.SetMode(2)

                    elif ghosts[i].state == 2:
                        # ghost is vulnerable
                        # give them glasses
                        # make them run
                        thisGame.AddToScore(thisGame.ghostValue)
                        thisGame.ghostValue = thisGame.ghostValue * 2
                        #snd_eatgh.play()

                        ghosts[i].state = 3
                        ghosts[i].speed = ghosts[i].speed * 4
                        # and send them to the ghost box
                        ghosts[i].x = ghosts[i].nearestCol * 16
                        ghosts[i].y = ghosts[i].nearestRow * 16
                        ghosts[i].currentPath = path.FindPath(
                            (ghosts[i].nearestRow, ghosts[i].nearestCol),
                            (thisLevel.GetGhostBoxPos()[0] + 1,
                             thisLevel.GetGhostBoxPos()[1]))
                        ghosts[i].FollowNextPathWay()

                        # set game mode to brief pause after eating
                        thisGame.SetMode(5)

            # check for collisions with the fruit
            if thisFruit.active == True:
                if thisLevel.CheckIfHit((self.x, self.y),
                                        (thisFruit.x, thisFruit.y), 8):
                    thisGame.AddToScore(2500)
                    thisFruit.active = False
                    thisGame.fruitTimer = 0
                    thisGame.fruitScoreTimer = 120
                    #snd_eatfruit.play()

        else:
            self.y = self.nearestRow * 16
            self.x = self.nearestCol * 16
            # we're going to hit a wall -- stop moving
            self.velX = 0
            self.velY = 0

        # deal with power-pellet ghost timer
        if thisGame.ghostTimer > 0:
            thisGame.ghostTimer -= 1

            if thisGame.ghostTimer == 0:
                for i in range(0, 4, 1):
                    if ghosts[i].state == 2:
                        ghosts[i].state = 1
                self.ghostValue = 0

        # deal with fruit timer
        thisGame.fruitTimer += 1
        if thisGame.fruitTimer == 500:
            pathwayPair = thisLevel.GetPathwayPairPos()

            if not pathwayPair == False:

                pathwayEntrance = pathwayPair[0]
                pathwayExit = pathwayPair[1]

                thisFruit.active = True

                thisFruit.nearestRow = pathwayEntrance[0]
                thisFruit.nearestCol = pathwayEntrance[1]

                thisFruit.x = thisFruit.nearestCol * 16
                thisFruit.y = thisFruit.nearestRow * 16

                thisFruit.currentPath = path.FindPath(
                    (thisFruit.nearestRow, thisFruit.nearestCol), pathwayExit)
                thisFruit.FollowNextPathWay()

        if thisGame.fruitScoreTimer > 0:
            thisGame.fruitScoreTimer -= 1

    def Draw(self):

        if thisGame.mode == 3:
            return False

        # set the current frame array to match the direction pacman is facing
        if self.velX > 0:
            self.anim_pacmanCurrent = self.anim_pacmanR
        elif self.velX < 0:
            self.anim_pacmanCurrent = self.anim_pacmanL
        elif self.velY > 0:
            self.anim_pacmanCurrent = self.anim_pacmanD
        elif self.velY < 0:
            self.anim_pacmanCurrent = self.anim_pacmanU

        screen.blit(self.anim_pacmanCurrent[self.animFrame],
                    (self.x - thisGame.screenPixelPos[0],
                     self.y - thisGame.screenPixelPos[1]))

        if thisGame.mode == 1:
            if not self.velX == 0 or not self.velY == 0:
                # only Move mouth when pacman is moving
                self.animFrame += 1

            if self.animFrame == 9:
                # wrap to beginning
                self.animFrame = 1

class ghost():
    def __init__(self, ghostID):
        self.x = 0
        self.y = 0
        self.velX = 0
        self.velY = 0
        self.speed = 1

        self.nearestRow = 0
        self.nearestCol = 0

        self.id = ghostID

        # ghost "state" variable
        # 1 = normal
        # 2 = vulnerable
        # 3 = spectacles
        self.state = 1

        self.homeX = 0
        self.homeY = 0

        self.currentPath = ""

        self.anim = {}
        for i in range(1, 7, 1):
            self.anim[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "ghost " + str(i) + ".gif")).convert()

            # change the ghost color in this frame
            for y in range(0, 16, 1):
                for x in range(0, 16, 1):

                    if self.anim[i].get_at((x, y)) == (255, 0, 0, 255):
                        # default, red ghost body color
                        self.anim[i].set_at((x, y), ghostcolor[self.id])

        self.animFrame = 1
        self.animDelay = 0

    def Draw(self):

        if thisGame.mode == 3:
            return False

        # ghost eyes --
        for y in range(4, 8, 1):
            for x in range(3, 7, 1):
                self.anim[self.animFrame].set_at((x, y), (255, 255, 255, 255))
                self.anim[self.animFrame].set_at((x + 6, y),
                                                 (255, 255, 255, 255))

                if player.x > self.x and player.y > self.y:
                    #player is to lower-right
                    pupilSet = (5, 6)
                elif player.x < self.x and player.y > self.y:
                    #player is to lower-left
                    pupilSet = (3, 6)
                elif player.x > self.x and player.y < self.y:
                    #player is to upper-right
                    pupilSet = (5, 4)
                elif player.x < self.x and player.y < self.y:
                    #player is to upper-left
                    pupilSet = (3, 4)
                else:
                    pupilSet = (4, 6)

        for y in range(pupilSet[1], pupilSet[1] + 2, 1):
            for x in range(pupilSet[0], pupilSet[0] + 2, 1):
                self.anim[self.animFrame].set_at((x, y), (0, 0, 255, 255))
                self.anim[self.animFrame].set_at((x + 6, y), (0, 0, 255, 255))
        # -- end ghost eyes

        if self.state == 1:
            # draw regular ghost (this one)
            screen.blit(self.anim[self.animFrame],
                        (self.x - thisGame.screenPixelPos[0],
                         self.y - thisGame.screenPixelPos[1]))
        elif self.state == 2:
            # draw vulnerable ghost

            if thisGame.ghostTimer > 100:
                # blue
                screen.blit(ghosts[4].anim[self.animFrame],
                            (self.x - thisGame.screenPixelPos[0],
                             self.y - thisGame.screenPixelPos[1]))
            else:
                # blue//white flashing
                tempTimerI = int(thisGame.ghostTimer // 10)
                if tempTimerI == 1 or tempTimerI == 3 or tempTimerI == 5 or tempTimerI == 7 or tempTimerI == 9:
                    screen.blit(ghosts[5].anim[self.animFrame],
                                (self.x - thisGame.screenPixelPos[0],
                                 self.y - thisGame.screenPixelPos[1]))
                else:
                    screen.blit(ghosts[4].anim[self.animFrame],
                                (self.x - thisGame.screenPixelPos[0],
                                 self.y - thisGame.screenPixelPos[1]))

        elif self.state == 3:
            # draw glasses
            screen.blit(tileIDImage[tileID['glasses']],
                        (self.x - thisGame.screenPixelPos[0],
                         self.y - thisGame.screenPixelPos[1]))

        if thisGame.mode == 6 or thisGame.mode == 7:
            # don't animate ghost if the level is complete
            return False

        self.animDelay += 1

        if self.animDelay == 2:
            self.animFrame += 1

            if self.animFrame == 7:
                # wrap to beginning
                self.animFrame = 1

            self.animDelay = 0

    def Move(self):

        self.x += self.velX
        self.y += self.velY

        self.nearestRow = int(((self.y + 8) // 16))
        self.nearestCol = int(((self.x + 8) // 16))

        if (self.x % 16) == 0 and (self.y % 16) == 0:
            # if the ghost is lined up with the grid again
            # meaning, it's time to go to the next path item

            if (self.currentPath):
                self.currentPath = self.currentPath[1:]
                self.FollowNextPathWay()

            else:
                self.x = self.nearestCol * 16
                self.y = self.nearestRow * 16

                # chase pac-man
                self.currentPath = path.FindPath(
                    (self.nearestRow, self.nearestCol),
                    (player.nearestRow, player.nearestCol))
                self.FollowNextPathWay()

    def FollowNextPathWay(self):

        # print "Ghost " + str(self.id) + " rem: " + self.currentPath

        # only follow this pathway if there is a possible path found!
        if not self.currentPath == False:

            if len(self.currentPath) > 0:
                if self.currentPath[0] == "L":
                    (self.velX, self.velY) = (-self.speed, 0)
                elif self.currentPath[0] == "R":
                    (self.velX, self.velY) = (self.speed, 0)
                elif self.currentPath[0] == "U":
                    (self.velX, self.velY) = (0, -self.speed)
                elif self.currentPath[0] == "D":
                    (self.velX, self.velY) = (0, self.speed)

            else:
                # this ghost has reached his destination!!

                if not self.state == 3:
                    # chase pac-man
                    self.currentPath = path.FindPath(
                        (self.nearestRow, self.nearestCol),
                        (player.nearestRow, player.nearestCol))
                    self.FollowNextPathWay()

                else:
                    # glasses found way back to ghost box
                    self.state = 1
                    self.speed = self.speed // 4

                    # give ghost a path to a random spot (containing a pellet)
                    (randRow, randCol) = (0, 0)

                    while not thisLevel.GetMapTile(
                        (randRow, randCol)) == tileID['pellet'] or (
                            randRow, randCol) == (0, 0):
                        randRow = random.randint(1, thisLevel.lvlHeight - 2)
                        randCol = random.randint(1, thisLevel.lvlWidth - 2)

                    self.currentPath = path.FindPath(
                        (self.nearestRow, self.nearestCol), (randRow, randCol))
                    self.FollowNextPathWay()

class Fruit():
    def __init__(self):
        # when fruit is not in use, it's in the (-1, -1) position off-screen.
        self.slowTimer = 0
        self.x = -16
        self.y = -16
        self.velX = 0
        self.velY = 0
        self.speed = 1
        self.active = False

        self.bouncei = 0
        self.bounceY = 0

        self.nearestRow = (-1, -1)
        self.nearestCol = (-1, -1)

        self.imFruit = {}
        for i in range(0, 5, 1):
            self.imFruit[i] = pygame.image.load(
                os.path.join(SCRIPT_PATH, "res", "sprite",
                             "fruit " + str(i) + ".gif")).convert()

        self.currentPath = ""
        self.fruitType = 1

    def Draw(self):

        if thisGame.mode == 3 or self.active == False:
            return False

        screen.blit(self.imFruit[self.fruitType],
                    (self.x - thisGame.screenPixelPos[0],
                     self.y - thisGame.screenPixelPos[1] - self.bounceY))

    def Move(self):

        if self.active == False:
            return False

        self.bouncei += 1
        if self.bouncei == 1:
            self.bounceY = 2
        elif self.bouncei == 2:
            self.bounceY = 4
        elif self.bouncei == 3:
            self.bounceY = 5
        elif self.bouncei == 4:
            self.bounceY = 5
        elif self.bouncei == 5:
            self.bounceY = 6
        elif self.bouncei == 6:
            self.bounceY = 6
        elif self.bouncei == 9:
            self.bounceY = 6
        elif self.bouncei == 10:
            self.bounceY = 5
        elif self.bouncei == 11:
            self.bounceY = 5
        elif self.bouncei == 12:
            self.bounceY = 4
        elif self.bouncei == 13:
            self.bounceY = 3
        elif self.bouncei == 14:
            self.bounceY = 2
        elif self.bouncei == 15:
            self.bounceY = 1
        elif self.bouncei == 16:
            self.bounceY = 0
            self.bouncei = 0
            #snd_fruitbounce.play()

        self.slowTimer += 1
        if self.slowTimer == 2:
            self.slowTimer = 0

            self.x += self.velX
            self.y += self.velY

            self.nearestRow = int(((self.y + 8) // 16))
            self.nearestCol = int(((self.x + 8) // 16))

            if (self.x % 16) == 0 and (self.y % 16) == 0:
                # if the fruit is lined up with the grid again
                # meaning, it's time to go to the next path item

                if len(self.currentPath) > 0:
                    self.currentPath = self.currentPath[1:]
                    self.FollowNextPathWay()

                else:
                    self.x = self.nearestCol * 16
                    self.y = self.nearestRow * 16

                    self.active = False
                    thisGame.fruitTimer = 0

    def FollowNextPathWay(self):

        # only follow this pathway if there is a possible path found!
        if not self.currentPath == False:

            if len(self.currentPath) > 0:
                if self.currentPath[0] == "L":
                    (self.velX, self.velY) = (-self.speed, 0)
                elif self.currentPath[0] == "R":
                    (self.velX, self.velY) = (self.speed, 0)
                elif self.currentPath[0] == "U":
                    (self.velX, self.velY) = (0, -self.speed)
                elif self.currentPath[0] == "D":
                    (self.velX, self.velY) = (0, self.speed)


player = Pacman()
thisGame = Game()
thisLevel = Level()
thisFruit = Fruit()

tile_list = None

def door_through(p):
    if thisLevel.GetMapTile(p) == tileID['door-h']:
        for i in range(0, thisLevel.lvlWidth, 1):
            if not i == p[1]:
                if thisLevel.GetMapTile(
                    (p[0], i)) == tileID['door-h']:
                    return (p[0], i)

    if thisLevel.GetMapTile(p) == tileID['door-v']:
        for i in range(0, thisLevel.lvlHeight, 1):
            if not i == p[1]:
                if thisLevel.GetMapTile(
                    (i, p[1])) == tileID['door-v']:
                    return (i, p[1])

def get_neighbors(p):
    global tile_list
    if not tile_list:
        tile_list = list(map(tileID.get, filter(lambda x: x.startswith('wall'), tileID.keys())))
    (x, y) = p
    res = []
    d = door_through(p)
    if d: res.append(d)
    for n in [(x+1,y),(x,y+1),(x-1,y),(x,y-1)]:
        (row, col) = n
        if not(row >= 0 and row < thisLevel.lvlHeight and col >= 0 and col < thisLevel.lvlWidth) \
                or thisLevel.GetMapTile(n) in tile_list:
            continue
        res.append(n)
    return res

def get_neighbors_running(p):
    neighbors = get_neighbors(p)
    res = []
    for n in neighbors:
        for ghost in ghosts:
            if (ghosts[i].y // 16 == n[0] or (ghosts[i].y + 8) // 16 == n[0]) and \
                    (ghosts[i].x // 16 == n[1] or (ghosts[i].x + 8) // 16 == n[1]):
                        continue
            res.append(n)
    return res


# create ghost objects
ghosts = {}
for i in range(0, 6, 1):
    # remember, ghost[4] is the blue, vulnerable ghost
    ghosts[i] = ghost(i)
