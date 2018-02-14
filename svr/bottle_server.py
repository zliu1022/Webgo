#coding=utf-8
import time
from bottle import route, run, template
from bottle import get, post, request # or route

from ctypes import *
import sys, time, getopt
import numpy as np

import json

################################################################
name = 'Zen7'
version = '0.3'

Threads = 8
Strength = 1
#Strength = 15000#count, 45000 means 1500*30s, very powerful machine think 30s

ZenDLL = 'c:\go\zen7\Zen.dll'
Komi = 7.5
BoardSize = 19
Handicap = 0

Sgf = []
PlayerBlack, PlayerWhite, ResultStr='','',''
move=[] #playlist[]
playlist=[]
movestr=[] #str
gameinfo=[] #suitable to dict data type
# unknown: CA FF-4 RU TC TT C AP GM-1 GN DT BR WR TM
# known: SZ PB PW KM HA RE
gamelen=0
passcount=0

MaxSimulations = 29#MaxSimulations = 1000000000 zliu: it's MCTS Playout, only 29 MCTS will be 1 NN eval
MaxTime = 1000000000.0#MaxTime = c_float(1000000000.0), Time*Games/s=Playout
PnLevel = 3
PnWeight = c_float(1.0)
VnMixRate = c_float(0.75)
ResignRate=0.0

ThinkInterval=1
Top=[]

SabakiFlat = 1 #0:off 1:on
################################################################

def Reply(S):
  sys.stdout.write('= ' + S + '\n\n')
  sys.stdout.flush()

def Print(S):
  sys.stderr.write(S + '\n')
  sys.stderr.flush()

def Help():
  Print("Allowed options:")
  Print(" -h [ --help ]".ljust(32) + "Show all allowed options.")
  Print(" -t [ --threads ] arg (=1)".ljust(32) + "Set the number of threads.")
  Print(" -s [ --strength ] arg (=10000)".ljust(32) + "Set the playing strength.")
  Print(" -d [ --dll ] arg (=.\Zen.dll)".ljust(32) + "Set the path of Zen.dll.")
  sys.exit()

try: opts, args = getopt.getopt(sys.argv[1:], "ht:s:d:", ["help", "threads=", "strength=","dll="])
except getopt.GetoptError: Help()

if args != []: Help()

for opt, arg in opts:
  if opt in ['-h','--help']: Help()
  if opt in ['-t','--threads']:
    if not arg.isdigit() or int(arg) < 1: Help()
    Threads = int(arg)
    continue
  if opt in ['-s','--strength']:
    if not arg.isdigit() or int(arg) < 1: Help()
    Strength = int(arg)
    continue
  if opt in ['-d','--dll']:
    if arg[-7:].lower() != 'zen.dll': Help()
    ZenDLL = arg
    continue
  Help()

try: Zen = CDLL(ZenDLL)
except WindowsError: Help()

Print(ZenDLL + ' load ok')

### Zen7's address, 36 total
ZenAddStone = Zen[1] #bool ZenAddStone(int,int,int)
ZenIsInitialized = Zen[14] #bool ZenIsInitialized(void)
ZenIsLegal = Zen[15] #bool ZenIsLegal(int,int,int)
ZenIsSuicide = Zen[16] #bool ZenIsSuicide(int,int,int)
ZenIsThinking = Zen[17] #bool ZenIsThinking(void)
ZenPlay = Zen[20] #bool ZenPlay(int,int,int)
ZenUndo = Zen[35] #bool ZenUndo(int)
ZenGetBestMoveRate = Zen[4] #int ZenGetBestMoveRate(void)
ZenGetBoardColor = Zen[5] #int ZenGetBoardColor(int,int)
ZenGetHistorySize = Zen[6] #int ZenGetHistorySize(void)
ZenGetNextColor = Zen[7] #int ZenGetNextColor(void)
ZenGetNumBlackPrisoners = Zen[8] #int ZenGetNumBlackPrisoners(void)
ZenGetNumWhitePrisoners = Zen[9] #int ZenGetNumWhitePrisoners(void)
ZenClearBoard = Zen[2] #void ZenClearBoard(void)
ZenFixedHandicap = Zen[3] #void ZenFixedHandicap(int)
def ZenGetPolicyKnowledge():
  k = ((c_int * 19) * 19)()
  Zen[10](k)
  return k

def print19(t):
  for i in range(0, 19):
    l=[]
    for j in range(0, 19):
      l.append( '%5d' % t[i][j] )
    print(' '.join(l))

def ZenGetTerritoryStatictics():
  t = ((c_int * 19) * 19)()
  Zen[11](t)
  return t

ZenGetTopMoveInfo = Zen[12] #void ZenGetTopMoveInfo(int,int &,int &,int &,float &,char *,int)
ZenInitialize = Zen[13] #void ZenInitialize(char const *)
ZenMakeShapeName = Zen[18] #void ZenMakeShapeName(int,int,int,char *,int)
ZenPass = Zen[19] #void ZenPass(int)
ZenReadGeneratedMove = Zen[21] #void ZenReadGeneratedMove(int &,int &,bool &,bool &)
ZenSetBoardSize = Zen[22] #void ZenSetBoardSize(int)
ZenSetKomi = Zen[23] #void ZenSetKomi(float)
ZenSetMaxTime = Zen[24] #void ZenSetMaxTime(float)
ZenSetNextColor = Zen[25] #void ZenSetNextColor(int)
ZenSetNumberOfSimulations = Zen[26] #void ZenSetNumberOfSimulations(int)
ZenSetNumberOfThreads = Zen[27] #void ZenSetNumberOfThreads(int)
ZenSetPnLevel = Zen[28] #void ZenSetPnLevel(int)
ZenSetPnWeight = Zen[29] #void ZenSetPnWeight(float)
ZenSetVnMixRate = Zen[30] #void ZenSetVnMixRate(float)
ZenStartThinking = Zen[31] #void ZenStartThinking(int)
ZenStopThinking = Zen[32] #void ZenStopThinking(void)
ZenTimeLeft = Zen[33] #void ZenTimeLeft(int,int,int)
ZenTimeSettings = Zen[34] #void ZenTimeSettings(int,int,int)

def PrintTop(len):
  for N in range(0, len):
    X, Y, P, W, S = c_int(0), c_int(0), c_int(0), c_float(0), create_string_buffer(100)
    ret = ZenGetTopMoveInfo(N, byref(X), byref(Y), byref(P), byref(W), S, 99)
    Print('ret: %d %d,%d %d %.2f %s' % (ret,X.value,Y.value,P.value,W.value,S.value))

def showboard():
  Print("")
  #Print("Last move %2d %2d %1d" % (playlist[gamelen-1][0],playlist[gamelen-1][1],playlist[gamelen-1][2]))
  Print("Passes: %d            Black (X) Prisoners: %d" % (passcount,ZenGetNumBlackPrisoners() ))
  Print("%s to move    White (O) Prisoners: %d" % ("Black (X)" if ZenGetNextColor()==2 else "White (O)",ZenGetNumWhitePrisoners()))
  Print("")
  gamelen=len(playlist)
  Print('Game len: %d' % gamelen)
  Print("   a b c d e f g h j k l m n o p q r s t")
  for i in range(0, 19):
    line = "%2d" % (19-int(i))
    last=0
    for j in range(0, 19):
      if ((j==playlist[gamelen-1][0]) and (i==playlist[gamelen-1][1])):
        line += "(%s)" % ("." if ZenGetBoardColor(j,i) == 0 else "X" if ZenGetBoardColor(j,i) == 2 else "O")
        last=1
      else:
        if last==0:
          line += " %s" % ("." if ZenGetBoardColor(j,i) == 0 else "X" if ZenGetBoardColor(j,i) == 2 else "O")
        else:
          last=0
          line += "%s" % ("." if ZenGetBoardColor(j,i) == 0 else "X" if ZenGetBoardColor(j,i) == 2 else "O")
        #print '%s' % "." if ZenGetBoardColor(j,i) == 0 else "X" if ZenGetBoardColor(j,i) == 2 else "O" ,
    line += "%2d" % (19-int(i))
    Print(line)
  Print("   a b c d e f g h j k l m n o p q r s t")
  Print("")
  Print("Black time: ??:??:??")
  Print("White time: ??:??:??")
  Print("")

def ZenGenMove(C):
    X, Y, P, W, S = c_int(0), c_int(0), c_int(0), c_float(0), create_string_buffer(100)
    F1, F2 = c_bool(0), c_bool(0)

    ZenStartThinking(C)

    while ZenIsThinking() != -0x80000000:
      time.sleep(ThinkInterval)
      #Print('')
      for N in range(0, 1):
        ret = ZenGetTopMoveInfo(N, byref(X), byref(Y), byref(P), byref(W), S, 99)
        #Print('ret: %d %d %.2f %s' % (ret,P.value,W.value,S.value))
        if P.value == 0:
          #Print('P.value==0')
          break
        if (P.value>=Strength) :
          #Print('P.value>=Strength')
          ZenStopThinking()
          break
        ItemB = [X.value, Y.value, P.value, W.value, S.value, '+', '+', '+']
        Print('%s %s[%s] -> %8d [%s],%s%% [%s], %s' % (('W' if C== 1 else 'B'), ItemB[4].split()[0].ljust(4), \
          ItemB[5], ItemB[2], ItemB[6], ('%.2f' % (ItemB[3] * 100)).rjust(6), ItemB[7], ItemB[4]))
      #time.sleep(ThinkInterval)

    ZenStopThinking()#zliu: maybe useless
    Print('')
    #Print('   Prisoners: Black %d, White %d %s-%s %d %.2f%%' % (ZenGetNumBlackPrisoners(), ZenGetNumWhitePrisoners(), name, version, P.value, W.value*100) )
    Print('   %s-%s %d %.2f%%' % (name, version, P.value, W.value*100) )
    TopA = []
    for N in range(0, 20):
      ret = ZenGetTopMoveInfo(N, byref(X), byref(Y), byref(P), byref(W), S, 99)
      if P.value == 0:
        break
      ItemB = [X.value, Y.value, P.value, W.value, S.value, '+', '+', '+']
      TopA.append(ItemB)
      Print('%s %s[%s] -> %8d [%s],%s%% [%s], %s' % (('W' if C== 1 else 'B'), ItemB[4].split()[0].ljust(4), \
        ItemB[5], ItemB[2], ItemB[6], ('%.2f' % (ItemB[3] * 100)).rjust(6), ItemB[7], ItemB[4]))
    Print('')
    return TopA

def final_score():
  str=''
  bt,wt=[0]*10,[0]*10
  t=ZenGetTerritoryStatictics()
  for i in range(0, 19):
    for j in range(0, 19):
      if t[i][j] > 900: bt[9]+=1
      if t[i][j] > 800: bt[8]+=1
      if t[i][j] > 700: bt[7]+=1
      if t[i][j] > 600: bt[6]+=1
      if t[i][j] > 500: bt[5]+=1
      if t[i][j] > 400: bt[4]+=1
      if t[i][j] > 300: bt[3]+=1
      if t[i][j] > 200: bt[2]+=1
      if t[i][j] > 100: bt[1]+=1
      if t[i][j] > 0: bt[0]+=1

      if t[i][j] < -900: wt[9]+=1
      if t[i][j] < -800: wt[8]+=1
      if t[i][j] < -700: wt[7]+=1
      if t[i][j] < -600: wt[6]+=1
      if t[i][j] < -500: wt[5]+=1
      if t[i][j] < -400: wt[4]+=1
      if t[i][j] < -300: wt[3]+=1
      if t[i][j] < -200: wt[2]+=1
      if t[i][j] < -100: wt[1]+=1
      if t[i][j] < 0: wt[0]+=1
  Print('Total: %d Komi: %.1f' % (gamelen, Komi))
  for j in range(0,9):
    i=9-j
    Print('%3d Black: %d White: %d Result: %.1f' % (i*100, bt[i],wt[i],bt[i]-wt[i]-Komi))
  rt9=bt[9]-wt[9]-Komi
  if rt9>0 : str='B+%.1f' % rt9
  else: str='W+%.1f' % -rt9
  return str
 
ZenInitialize('')
ZenSetNumberOfThreads(Threads)
ZenSetNumberOfSimulations(MaxSimulations)
ZenSetMaxTime(c_float(MaxTime))
ZenSetBoardSize(BoardSize)
ZenSetKomi(c_float(Komi))

Print('Zen Initialize ok(%d)' % ZenIsInitialized())
Print('Threads: %d' % Threads)
Print('MaxSimulations: %d (playouts, MCTS search)' % MaxSimulations)
Print('MaxTime: %.1f' % MaxTime)
Print('ResignRate: %.2f' % ResignRate)

Print('Strength: %d (counts, NN eval)' % Strength)
Print('BoardSize: %d' % BoardSize)
Print('Komi: %.1f' % Komi)
Print('')

ZenSetPnLevel(3)
ZenSetPnWeight(c_float(1.0))
ZenSetVnMixRate(c_float(0.75))

ZenClearBoard()

@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)

@get('/login') # or @route('/login')
def login():
    return '''
        <form action="/login" method="post">
            Username: <input name="username" type="text" />
            Password: <input name="password" type="password" />
            <input value="Login" type="submit" />
        </form>
    '''

def check_login(username, password):
  if username=="a" and password=="b" :
    return 1
  else:
    return 0

@post('/login') # or @route('/login', method='POST')
def do_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    if check_login(username, password):
        return "<p>Your login information was correct.</p>"
    else:
        return "<p>Login failed.</p>"

@get('/clear_board')
def clear_board():
    #boardsize = request.forms.get('size')
    #komi = request.forms.get('komi')
    ZenClearBoard()
    return json.dumps({"result":"ok"})

@get('/undo')
def undo():
    ZenUndo(1)
    return json.dumps({"result":"ok"})

@post('/play') # or @route('/go/play', method='POST')
def do_play():
    x = int(request.forms.get('x'))
    y = int(request.forms.get('y'))
    color = int(request.forms.get('color'))
    #print "client: %s(%d %d)" % ('B' if color==1 else 'W',x,y)
    #time.sleep(5)

    if (color==1) : C=2
    else: C=1
    print "ZenPlay %s(%d %d) GTP: %s%d" % ('B' if C==2 else 'W',x,y, 'ABCDEFGHJKLMNOPQRST'[x],BoardSize-y)
    ret = ZenPlay(x, y, C)

    C = ZenGetNextColor()
    Top = ZenGenMove(C)
    ZenPlay(Top[0][0],Top[0][1],C)

    rp=[]
    for i in range(0, len(Top)):
        print Top[i]
        rp.append({'x':Top[i][0],'y':Top[i][1],'color':1 if C==2 else -1, 'count':Top[i][2], 'winrate':int(Top[i][3]*1000)/10.0, 'seq':Top[i][4]})
    #print json.dumps(rp)
    return json.dumps(rp)

run(host='localhost', port=32001)

