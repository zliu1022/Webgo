#coding=utf-8
# 2018-07-04 initial version

from bottle import abort, Bottle
from bottle import route, run, template
from bottle import get, post, request # or route
import time
import threading

import time

import os, sys
import leelaz
import json

executable = "c:/go/leela-zero/leelaz.exe"
weight = '-wc:/go/weight/62b5417b64c46976795d10a6741801f15f857e5029681a42d02c9852097df4b9.gz'
port = 32002

is_japanese_rules = False
is_handicap_game = False
board_size = 19
komi = 7.5
seconds_per_search = 10
verbosity = 2

lz = leelaz.CLI(board_size=board_size,
                  executable=executable,
                  is_handicap_game=is_handicap_game,
                  komi=komi,
                  seconds_per_search=seconds_per_search,
                  verbosity=verbosity)

def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - long(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp

app = Bottle()
lz.start(weight)
on_off = True
#wsock = 1
th = 1

def send_analyze(wsock):
    global on_off
    global lz
    print "thread %s is running" % threading.current_thread().name

    #localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
    interval = 100
    analyze_count = 2
    cmd = "lz-analyze %d" % interval # send analyze per second 
    lz.p.stdin.write(cmd + "\n")
    sleep_per_try = interval/1000
    tries = 0
    success_count = 0
    ret={"cmd":"", "para":"", "result":""}

    #while on_off and tries <= analyze_count and lz.p is not None:
    while on_off and lz.p is not None:
        time.sleep(sleep_per_try)
        tries += 1
        # Readline loop
        while True:
            s = lz.stdout_thread.readline()
            #print s
            if (len(s) > 3): 
                success_count += 1

                s_array = s.split("info move ")
                #print "s_array: %s " % s_array
                re = []
                for analyz_orig in s_array:
                    #print "analyz_orig: %s " % analyz_orig
                    analyz_response={"x":-1, "y":-1, "move":"", "visits":1, "winrate":1, "order":1, "pv":""}
                    
                    analyz = analyz_orig.split(" ")
                    #print "analyz: %s " % analyz
                    if (len(analyz)<10) :continue
                    analyz_response["move"]=analyz[0]
                    if(analyz[0]=="pass"):
                        analyz_response["x"] = board_size
                        analyz_response["y"] = board_size
                    else:
                        analyz_response["x"] = 'ABCDEFGHJKLMNOPQRST'.find(analyz[0][0])
                        analyz_response["y"] = board_size - int(analyz[0][1:])
                    analyz_response["visits"]=analyz[2]
                    analyz_response["winrate"]=analyz[4]
                    analyz_response["order"]=analyz[6]
                    analyz_response["pv"]=" ".join(analyz[8:])
                    
                    re.append(analyz_response)
                    if(len(re)>30) : break

                localtime = get_time_stamp();
                if (len(re)>0):
                    print "time: %s success %d INFO: %s" % (localtime, success_count, re[0])
                else :
                    print "time: %s success %d INFO: %s" % (localtime, success_count, "END")
                #print "success: %d" % success_count
                #print "INFO: %s (len:%d)" % (re[0], len(re))
                #print ""
                try:
                    ret["cmd"]="time";
                    ret["result"]=localtime;
                    wsock.send(json.dumps(ret))

                    ret["cmd"]="lz-analyze";
                    ret["result"]=re;
                    wsock.send(json.dumps(ret))

                except WebSocketError:
                    cmd = ""
                    on_off = False
                    if lz.p is not None:
                        print "WebSocketError lz.p is not None"
                        lz.p.stdin.write(cmd + "\n")
                    else:
                        print "WebSocketError lz.p is None"
                    #lz.stop()
                    break
            # No output, so break readline loop and sleep and wait for more
            if s == "":
                #print "success: %d" % success_count
                break
    if success_count :
        cmd = ""
        if lz.p is not None:
            print "if lz.p is not None"
            lz.p.stdin.write(cmd + "\n")
            time.sleep(sleep_per_try)
            (so,se) = lz.drain()
            print "stdout"
            print "".join(so)
            print "stderr"
            print "".join(se)
        else:
            print "if lz.p is None"
        return re

    print "thread %s ended" % threading.current_thread().name

@app.route('/websocket')
def handle_websocket():
    #global wsock
    global lz
    global th
    global on_off
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
                    on_off = False
                    th.join()
                    ret["result"] = "ok"
                    wsock.send(json.dumps(ret))
                else:
                    on_off = True
                    th = threading.Thread(target=send_analyze, args=(wsock,), name='analyze-thread')
                    th.start()
                continue

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

            if (cmd[0]=="play"):
                print "play %s %s" % (cmd[1], cmd[2])
                #leelaz.play(cmd[1], cmd[2])
                lz.send_command('play %s %s' % (cmd[1], cmd[2]), sleep_per_try = 0.01)
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="play-and-analyze"):
                print "stopping lz-analyze..."
                on_off = False
                th.join()

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
                else:
                    x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                    y = board_size - int(move["y"])
                    color = 'B' if move["c"]==1 else 'W'
                    print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                    lz.send_command('play %s %s%d' % (color, x,y), sleep_per_try = 0.01)

                print "starting lz-analyze..."
                on_off = True
                th = threading.Thread(target=send_analyze, args=(wsock,), name='analyze-thread')
                th.start()
                
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue;

            if (cmd[0]=="undo"):
                lz.send_command('undo')
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="undo-and-analyze"):
                print "stopping lz-analyze..."
                on_off = False
                th.join()

                print "undo"
                lz.send_command('undo')

                print "starting lz-analyze..."
                on_off = True
                th = threading.Thread(target=send_analyze, args=(wsock,), name='analyze-thread')
                th.start()

                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

            if (cmd[0]=="clear_board"):
                lz.send_command('clear_board')
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
                    else:
                        x = 'ABCDEFGHJKLMNOPQRST'[move["x"]]
                        y = board_size - int(move["y"])
                        color = 'B' if move["c"]==1 else 'W'
                        print "%3d (%s %s %s) -> play %s %s%d" % (no, move["x"], move["y"], move["c"], color, x, y)
                        lz.send_command('play %s %s%d' % (color, x,y), sleep_per_try = 0.01)
                    no += 1
                    ret["result"] = "%d" % no
                    wsock.send(json.dumps(ret))
                ret["result"] = "ok"
                wsock.send(json.dumps(ret))
                continue

        except WebSocketError:
            #lz.stop()
            on_off = False
            #th.join()
            break

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
server = WSGIServer(("0.0.0.0", port), app,
    handler_class=WebSocketHandler)
server.serve_forever()
