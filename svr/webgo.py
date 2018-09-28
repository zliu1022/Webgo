#coding=utf-8
# 2018-07-04 initial version
# 2018-09-27 zen7 & leelaz

from bottle import abort, Bottle
from bottle import route, run, template
from bottle import get, post, request # or route
import time
import threading

import time

import os, sys
import leelaz
from Zen7 import *
import json

if (len(sys.argv)==2):
    board_size = int(sys.argv[1])
else:
    board_size = 19

if (board_size == 19):
    komi = 7.5
    executable = "c:/go/leela-zero-0.13-win64-cpu/leelaz-0.13-win64-cpu-elf-liz-gz-anlyz.exe"
    weight = '-wc:/go/weight/d351f06e446ba10697bfd2977b4be52c3de148032865eaaf9efc9796aea95a0c.gz'
    port = 32019
else:
    komi = 6.5
    executable = "C:/go/9/leelaz-0.13-win64-cpu-elf-liz-gz-anlyz-9.exe"
    weight = "-wC:/go/9/9-128x20.gz"
    port = 32009


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
ZenDLL='c:\go\zen7\Zen.dll'
Threads=4
ResignRate=0.1
ThinkInterval=0.1
PrintInterval=1

Z=ZEN(ZenDLL,board_size, komi, Strength, Threads, ResignRate, ThinkInterval, PrintInterval)

app = Bottle()

def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - long(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp

@app.route('/websocket')
def handle_websocket():
    #global wsock
    global lz
    th_lz, th_zen7=0,0
    analyze_type=0 # 0:lz(default), 1:zen7
    ret={"cmd":"", "para":"", "result":""}
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        print "ws error"
        abort(400, 'Expected WebSocket request.')
    print "web socket client connect"
    while True:
        time.sleep(0.5)
        try:
            message = wsock.receive()
            if message : 
                cmd = message.split(" ")
            else:
                continue
            print "cmd: %s" % cmd
            ret["cmd"] = cmd[0]
            ret["para"] = cmd[1:]

            if (cmd[0]=="hello"):
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="lz-analyze"):
                if (cmd[1]=="off"):
                    if analyze_type==0:
                        lz.analyzeStatus = False
                        th_lz.join()
                    else:
                        Z.analyzeStatus=False
                        th_zen7.join()
                    ret["result"] = "ok"
                    wsock.send(json.dumps(ret))
                else:
                    if (cmd[1]=="leelaz"):
                        analyze_type=0
                    elif (cmd[1]=="zen7"):
                        analyze_type=1

                    if analyze_type==0:
                        lz.analyzeStatus = True
                        th_lz = threading.Thread(target=lz.gen_analyze, args=(wsock,), name='analyze-thread')
                        th_lz.start()
                    else:
                        th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                        th_zen7.start()
                continue

            '''
            if (cmd[0]=="leelaz-start"):
                print "leelaz starting ... "
                #if lz: lz.stop()
                lz.start()
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="leelaz-stop"):
                print "leelaz stopped ... "
                #lz.stop()
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue
            '''

            if (cmd[0]=="play"):
                print "play %s %s" % (cmd[1], cmd[2])
                lz.send_command('play %s %s' % (cmd[1], cmd[2]), sleep_per_try = 0.01)
                Z.play(cmd[1].lower(), cmd[2].lower())
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="play-and-analyze"):
                print "stopping lz-analyze..."
                if analyze_type==0:
                    lz.analyzeStatus = False
                    th_lz.join()
                else:
                    Z.analyzeStatus=False
                    th_zen7.join()

                movelist = json.loads(cmd[1])
                ret["para"] = len(movelist)
                if (len(movelist) == 0 ):
                    print "play-and-analyze 0 error"
                    continue
                #print "play-and-analyze ... %d (movelist[0]: %d %d %d)" % (len(movelist), movelist[0]["x"], movelist[0]["y"], movelist[0]["c"])
                no = 1
                move = movelist[0]
                if (len(move)==1):
                    color = 'B' if move["c"]==1 else 'W'
                    print "%3d (pass %s) -> play %s pass" % (no, move["c"], color)
                    lz.send_command('play %s pass' % color, sleep_per_try = 0.01)
                    Z.play(color.lower(), "pass")
                else:
                    x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                    y = board_size - int(move["y"])
                    color = 'B' if move["c"]==1 else 'W'
                    print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                    lz.send_command('play %s %s%d' % (color, x,y), sleep_per_try = 0.01)
                    Z.play(color.lower(), ('%s%d' % (x,y)).lower())

                print "starting lz-analyze..."
                if analyze_type==0:
                    lz.analyzeStatus = True
                    th_lz = threading.Thread(target=lz.gen_analyze, args=(wsock,), name='analyze-thread')
                    th_lz.start()
                else:
                    th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                    th_zen7.start()
                
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue;

            if (cmd[0]=="undo"):
                lz.send_command('undo')
                Z.ZenUndo(1)
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="undo-and-analyze"):
                print "stopping lz-analyze..."
                if analyze_type==0:
                    lz.analyzeStatus = False
                    th_lz.join()
                else:
                    Z.analyzeStatus=False
                    th_zen7.join()

                print "undo"
                lz.send_command('undo')
                Z.ZenUndo(1)

                print "starting lz-analyze..."
                if analyze_type==0:
                    lz.analyzeStatus = True
                    th_lz = threading.Thread(target=lz.gen_analyze, args=(wsock,), name='analyze-thread')
                    th_lz.start()
                else:
                    th_zen7 = threading.Thread(target=Z.gen_analyze, args=(wsock,), name='gen-analyze')
                    th_zen7.start()

                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="clear_board"):
                lz.send_command('clear_board')
                Z.clear()
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="playlist"):
                movelist = json.loads(cmd[1])
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
                        Z.play(color.lower(), "pass")
                    else:
                        x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                        y = board_size - int(move["y"])
                        color = 'B' if move["c"]==1 else 'W'
                        print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                        lz.send_command('play %s %s%d' % (color, x,y), sleep_per_try = 0.01)
                        Z.play(color.lower(), ('%s%d' % (x,y)).lower())
                    ret["result"] = "%d" % no
                    wsock.send(json.dumps(ret))
                    no += 1
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

        except WebSocketError:
            lz.analyzeStatus = False
            Z.analyzeStatus=False
            break

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

import socket
myname=socket.getfqdn(socket.gethostname())
myaddr=socket.gethostbyname(myname)
print 'listening', port, 'at', myaddr, myname

server = WSGIServer(("0.0.0.0", port), app,
    handler_class=WebSocketHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    lz.stop()
