#coding=utf-8
# 2018-07-04 initial version
# 2018-09-27 zen7 & leelaz

from bottle import abort, Bottle
from bottle import route, run, template
from bottle import get, post, request # or route
import time
import threading

import os, sys
import leelaz
from Zen7 import *
import json

if (len(sys.argv)==2):
    board_size = int(sys.argv[1])
else:
    board_size = 19

port = 32019
if os.name == 'posix': # mac os or linux
    if (board_size == 19):
        komi = 7.5
        executable = './dist/leelaz'
        weight = '-w./dist/network.gz'
    elif (board_size == 13):
        komi = 7.5
        executable = './dist/leelaz-13'
        weight = '-w./dist/network-13.gz'
    elif (board_size == 9):
        komi = 6.5
        executable = './dist/leelaz-9'
        weight = '-w./dist/network-9.gz'
    else:
        print 'invalid board size'
        sys.exit()        
else:
    if (board_size == 19):
        komi = 7.5
        executable = "./dist/leelaz.exe"
        weight = '-w./dist/network.gz'
    else:
        komi = 6.5
        executable = "./dist/leelaz-9.exe"
        weight = '-w./dist/network-9.gz'

seconds_per_search = 10
verbosity = 2
lz = leelaz.CLI(board_size=board_size,
    executable=executable,
    is_handicap_game=False,
    komi=komi,
    seconds_per_search=seconds_per_search,
    verbosity=verbosity)
lz.start(weight)

Strength=15000
name = 'Zen7'
dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
#ZenDLL=sys.path[0]+'/Zen.dll'
print dirname
ZenDLL=dirname + '/Zen.dll'

Threads=4
ResignRate=0.1
ThinkInterval=0.1
PrintInterval=1

MaxSimulations=1000000000
MaxTime=1000000000.0
PnLevel=3
PnWeight=1.0
VnMixRate=0.75

Z=None
if os.path.isfile(ZenDLL):
    Z=ZEN(name, ZenDLL,board_size, komi, Strength, Threads, ResignRate, ThinkInterval, PrintInterval, MaxSimulations, MaxTime, PnLevel, PnWeight, VnMixRate)

app = Bottle()

def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - long(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp

sgfstr="(;CA[UTF-8]GM[1]FF[4]AP[Webgo]ST[2]DT[%s]\n"\
    "PW[LeelaZero]WR[9p]PB[LeelaZero]BR[9p]\n"\
    "SZ[%d]KM[%.1f]RU[Chinese]OT[3x60 byo-yomi]\n;"
sgfmove=[]
def save_latestsgf():
    global board_size, komi
    global sgfmove, sgfstr

    datastr = time.strftime("%Y%m%d", time.localtime()) 
    strhead = sgfstr % (datastr, board_size, komi)

    strmove = '\n;'.join(sgfmove)
    print strmove
    filestr = strhead + strmove + "\n)"

    sgfname="./sgf/latest.sgf"
    with open(sgfname, "w") as fd:
        fd.write(filestr)
        fd.close()
        print "writing to %s ... done" % sgfname

th_lz, th_zen7=0,0
analyze_type=0 # 0:lz(default), 1:zen7

@app.route('/websocket')
def handle_websocket():
    global lz
    global analyze_type
    global sgfmove, sgfstr

    tmpstr = ''
    
    ret={"cmd":"", "para":"", "result":""}
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        print "ws error"
        abort(400, 'Expected WebSocket request.')
    print "web socket client connect", wsock
    while True:
        time.sleep(0.5)
        try:
            message = wsock.receive()
            if message : 
                cmd = message.split(" ")
            else:
                continue
            print
            print "CMD: %s %s" % (get_time_stamp(), cmd)
            print
            ret["cmd"] = cmd[0]
            ret["sess"] = cmd[1]
            ret["para"] = cmd[2:]

            if (cmd[0]=="hello"):
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="time"):
                ret["result"] = get_time_stamp()
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="lz-analyze"):
                if (cmd[2]=="off"):
                    if analyze_type==0:
                        tmpstr = '\n'
                        lz.send_command(tmpstr, sleep_per_try = 0.01, nowait=True)
                    else:
                        Z.analyzeStatus=False
                        th_zen7.join()

                    ret["result"] = "ok"
                    wsock.send(json.dumps(ret))
                else:
                    if (cmd[2]=="leelaz"):
                        analyze_type=0
                    elif (cmd[2]=="zen7"):
                        if Z<>None: analyze_type=1

                    if analyze_type==0:
                        lz.analyzeSess = cmd[1]
                        lz.analyzeInterval = int(cmd[3])
                        lz.analyzeStatus = True
                        lz.analyzeSend = True
                        th_lz = threading.Thread(target=lz.gen_analyze, args=(wsock,), name='analyze-thread')
                        th_lz.start()
                    else:
                        Z.analyzeSess = cmd[1]
                        Z.analyzeStatus = True
                        th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                        th_zen7.start()
                continue

            if (cmd[0]=="play-and-analyze"):
                lz.analyzeSend = False
                if analyze_type==1: 
                    Z.analyzeStatus=False
                    th_zen7.join()

                movelist = json.loads(cmd[2])
                ret["para"] = len(movelist)
                if (len(movelist) == 0 ):
                    print "play-and-analyze error"
                    continue
                no = 1
                move = movelist[0]

                tmpstr = ''
                if ((len(move)==1) or (move["x"]==board_size and move["y"]==board_size)):
                    color = 'B' if move["c"]==1 else 'W'
                    print "%3d (pass %s) -> play %s pass" % (no, move["c"], color)
                    tmpstr = format('play %s pass' % color)
                    if Z<>None: Z.play(color.lower(), "pass")

                    sgfmove.append("%s[]"%(color))
                else:
                    x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                    y = board_size - int(move["y"])
                    color = 'B' if move["c"]==1 else 'W'
                    print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                    tmpstr = format('play %s %s%d' % (color, x,y))
                    if Z<>None: Z.play(color.lower(), ('%s%d' % (x,y)).lower())

                    sgf_x = 'abcdefghijklmnopqrs'[move["x"]]
                    sgf_y = 'abcdefghijklmnopqrs'[move["y"]]
                    sgfmove.append("%s[%s%s]"%(color,sgf_x,sgf_y))

                if analyze_type==0:
                    tmpstr = tmpstr + '\n' + format("lz-analyze %d" % lz.analyzeInterval)
                    lz.analyzeSend = True
                    lz.analyzeSess = cmd[1]
                else:
                    tmpstr = tmpstr + '\n'
                    Z.analyzeStatus=False
                    Z.analyzeSess = cmd[1]
                    th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                    th_zen7.start()
                lz.send_command(tmpstr, sleep_per_try = 0.01, nowait=True)                    

                save_latestsgf()
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue;

            if (cmd[0]=="undo-and-analyze"):
                lz.analyzeSend = False
                if analyze_type==1:
                    Z.analyzeStatus=False
                    th_zen7.join()

                tmpstr = 'undo'
                if Z<>None: Z.ZenUndo(1)

                sgfmove.pop()
                
                if analyze_type==0:
                    tmpstr = tmpstr + '\n' + format("lz-analyze %d" % lz.analyzeInterval)
                    lz.analyzeSend = True
                    lz.analyzeSess = cmd[1]
                else:
                    tmpstr = tmpstr + '\n'
                    Z.analyzeStatus=False
                    Z.analyzeSess = cmd[1]
                    th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                    th_zen7.start()
                lz.send_command(tmpstr, sleep_per_try = 0.01, nowait=True)

                save_latestsgf()

                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="clear_board"):
                r = lz.send_command('clear_board')
                if r==-1: 
                    print "clear_board error restart lz"
                    lz.stop()
                    lz.start(weight)
                if Z<>None: Z.clear()
                sgfmove=[]
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="playlist"):
                movelist = json.loads(cmd[2])
                ret["para"] = len(movelist)
                if (len(movelist) == 0 ):
                    print "playlist 0 error"
                    continue
                print "playlist ... %d (movelist[0]: %d %d %d)" % (len(movelist), movelist[0]["x"], movelist[0]["y"], movelist[0]["c"])
                no = 1
                for move in movelist:
                    if (len(move)==1):
                        color = 'B' if move["c"]==1 else 'W'
                        print "%3d (pass %s) -> play %s pass" % (no, move["c"], color)
                        lz.send_command('play %s pass' % color, sleep_per_try = 0.01)
                        if Z<>None: Z.play(color.lower(), "pass")

                        sgfmove.append("%s[]"%(color))
                    else:
                        x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                        y = board_size - int(move["y"])
                        color = 'B' if move["c"]==1 else 'W'
                        print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                        lz.send_command('play %s %s%d' % (color, x,y), sleep_per_try = 0.01)
                        if Z<>None: Z.play(color.lower(), ('%s%d' % (x,y)).lower())

                        sgf_x = 'abcdefghijklmnopqrs'[move["x"]]
                        sgf_y = 'abcdefghijklmnopqrs'[move["y"]]
                        sgfmove.append("%s[%s%s]"%(color,sgf_x,sgf_y))

                    save_latestsgf()
                    ret["result"] = "%d" % no
                    wsock.send(json.dumps(ret))
                    no += 1
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

        except WebSocketError:
            print "web socket client WebSocketError break", wsock
            lz.analyzeStatus = False
            if Z<>None: Z.analyzeStatus=False
            break

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
HandlerClass = SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"
httpdport = 8000
server_address = ('0.0.0.0', httpdport)
HandlerClass.protocol_version = Protocol
httpd = ServerClass(server_address, HandlerClass)
sa = httpd.socket.getsockname()

def httpdworker(sa,port):
    print "httpserver listening", sa[1], 'at', sa[0]
    httpd.serve_forever()
    print "closing httpd"

th_httpd = threading.Thread(target=httpdworker, args=(sa,httpdport,), name='httpd-thread')
th_httpd.start()

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler


import socket
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        print "fail connect"
        ip = "127.0.0.1"
    finally:
        s.close()
 
    return ip

#myname=socket.getfqdn(socket.gethostname()) # will not work under macos with only mifi
#myaddr=socket.gethostbyname(myname)
#print 'websocket listening', port, 'at', myaddr, myname

myaddr = get_host_ip()
print 'websocket listening', port, 'at', myaddr

print('please enter URL: http://%s:%d/webgo.html' % (myaddr,httpdport))

server = WSGIServer(("0.0.0.0", port), app,
    handler_class=WebSocketHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    if analyze_type==0 and th_lz!=0:
        lz.analyzeStatus = False
        th_lz.join()
    if analyze_type==1 and th_zen7!=0:
        Z.analyzeStatus=False
        th_zen7.join()
    lz.stop()
    httpd.shutdown()
    th_httpd.join()
