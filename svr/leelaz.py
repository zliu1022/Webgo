import os
import sys
import re
import time
import hashlib
from Queue import Queue, Empty
#from threading import Thread
import threading
from subprocess import Popen, PIPE, STDOUT
import json
from geventwebsocket import WebSocketError

update_regex = r'Nodes: ([0-9]+), Win: ([0-9]+\.[0-9]+)\% \(MC:[0-9]+\.[0-9]+\%\/VN:[0-9]+\.[0-9]+\%\), PV:(( [A-Z][0-9]+)+)'
update_regex_no_vn = r'Nodes: ([0-9]+), Win: ([0-9]+\.[0-9]+)\%, PV:(( [A-Z][0-9]+)+)'

status_regex = r'MC winrate=([0-9]+\.[0-9]+), NN eval=([0-9]+\.[0-9]+), score=([BW]\+[0-9]+\.[0-9]+)'
status_regex_no_vn = r'MC winrate=([0-9]+\.[0-9]+), score=([BW]\+[0-9]+\.[0-9]+)'

move_regex = r'^([A-Z][0-9]+) -> +([0-9]+) \(W: +(\-?[0-9]+\.[0-9]+)\%\) \(U: +(\-?[0-9]+\.[0-9]+)\%\) \(V: +([0-9]+\.[0-9]+)\%: +([0-9]+)\) \(N: +([0-9]+\.[0-9]+)\%\) PV: (.*)$'
move_regex_no_vn = r'^([A-Z][0-9]+) -> +([0-9]+) \(U: +(\-?[0-9]+\.[0-9]+)\%\) \(R: +([0-9]+\.[0-9]+)\%: +([0-9]+)\) \(N: +([0-9]+\.[0-9]+)\%\) PV: (.*)$'

best_regex = r'([0-9]+) visits, score (\-? ?[0-9]+\.[0-9]+)\% \(from \-? ?[0-9]+\.[0-9]+\%\) PV: (.*)'
stats_regex = r'([0-9]+) visits, ([0-9]+) nodes(?:, ([0-9]+) playouts)(?:, ([0-9]+) p/s)'
bookmove_regex = r'([0-9]+) book moves, ([0-9]+) total positions'
finished_regex = r'= ([A-Z][0-9]+|resign|pass)'

#Start a thread that perpetually reads from the given file descriptor
#and pushes the result on to a queue, to simulate non-blocking io. We
#could just use fcntl and make the file descriptor non-blocking, but
#fcntl isn't available on windows so we do this horrible hack.
class ReaderThread:
    def __init__(self,fd):
        self.queue = Queue()
        self.fd = fd
        self.stopped = False
    def stop(self):
        #No lock since this is just a simple bool that only ever changes one way
        self.stopped = True
    def loop(self):
        while not self.stopped and not self.fd.closed:
            line = None
            #fd.readline() should return due to eof once the process is closed
            #at which point
            try:
                line = self.fd.readline()
            except IOError:
                time.sleep(0.2)
                pass
            if line is not None and len(line) > 0:
                self.queue.put(line)

    def readline(self):
        try:
            line = self.queue.get_nowait()
        except Empty:
            return ""
        return line

    def read_all_lines(self):
        lines = []
        while True:
            try:
                line = self.queue.get_nowait()
            except Empty:
                break
            lines.append(line)
        return lines


def start_reader_thread(fd):
    rt = ReaderThread(fd)
    def begin_loop():
        rt.loop()

    t = threading.Thread(target=begin_loop)
    t.start()
    return rt

class CLI(object):
    def __init__(self, board_size, executable, is_handicap_game, komi, seconds_per_search, verbosity):
        self.history=[]
        self.executable = executable
        self.verbosity = verbosity
        self.board_size = board_size
        self.is_handicap_game = is_handicap_game
        self.komi = komi
        self.seconds_per_search = seconds_per_search + 1 #add one to account for lag time
        self.p = None
        self.analyzeStatus=False
        self.analyzeSend=False

    def gen_analyze(self,wsock):
        print "leelaz thread %s is running" % threading.current_thread().name
        print wsock

        #localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
        interval = 20
        analyze_count = 2
        cmd = "lz-analyze %d" % interval # send analyze per second 
        self.p.stdin.write(cmd + "\n")
        sleep_per_try = interval/1000
        tries = 0
        success_count = 0
        ret={"cmd":"", "para":"", "result":""}

        #while self.analyzeStatus and tries <= analyze_count and lz.p is not None:
        while self.analyzeStatus and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            # Readline loop
            while True:
                s = self.stdout_thread.readline()
                #print s
                if (len(s) > 3): 
                    success_count += 1

                    s_array = s.split("info move ")
                    if (len(s_array)>=1) : print "s_array[0]: %s " % s_array[0]
                    if (len(s_array)>=2) : print "s_array[1]: %s " % s_array[1]
                    re = []
                    for analyz_orig in s_array:
                        #print "analyz_orig: %s " % analyz_orig
                        analyz_response={"x":-1, "y":-1, "move":"", "visits":1, "winrate":1, "order":1, "pv":""}
                        
                        analyz = analyz_orig.split(" ")
                        #print "analyz: %s " % analyz
                        if (len(analyz)<10) :continue
                        analyz_response["move"]=analyz[0]
                        if(analyz[0]=="pass"):
                            analyz_response["x"] = self.board_size
                            analyz_response["y"] = self.board_size
                        else:
                            analyz_response["x"] = 'ABCDEFGHJKLMNOPQRST'.find(analyz[0][0])
                            analyz_response["y"] = self.board_size - int(analyz[0][1:])
                        analyz_response["visits"]=analyz[2]
                        analyz_response["winrate"]=analyz[4]
                        analyz_response["prior"]=analyz[6]
                        analyz_response["order"]=analyz[8]
                        analyz_response["pv"]=" ".join(analyz[10:])
                        
                        re.append(analyz_response)
                        if(len(re)>5) : break

                    '''
                    localtime = get_time_stamp();
                    if (len(re)>0):
                        print "time: %s success %d INFO: %s" % (localtime, success_count, re[0])
                    else :
                        print "time: %s success %d INFO: %s" % (localtime, success_count, "END")
                    '''
                    #print "success: %d" % success_count
                    #print "INFO: %s (len:%d)" % (re[0], len(re))
                    #print ""
                    try:
                        #ret["cmd"]="time";
                        #ret["result"]=localtime;
                        #wsock.send(json.dumps(ret))

                        ret["cmd"]="lz-analyze";
                        ret["result"]=re;
                        #print ret
                        #print
                        if self.analyzeSend == True:
                            wsock.send(json.dumps(ret))
                    except WebSocketError:
                        cmd = ""
                        self.analyzeStatus = False
                        if self.p is not None:
                            print "WebSocketError lz.p is not None"
                            self.p.stdin.write(cmd + "\n")
                        else:
                            print "WebSocketError lz.p is None"
                        break
                # No output, so break readline loop and sleep and wait for more
                if s == "":
                    #print "success: %d" % success_count
                    break
        if success_count :
            cmd = ""
            if self.p is not None:
                print "if lz.p is not None"
                self.p.stdin.write(cmd + "\n")
                time.sleep(sleep_per_try)
                (so,se) = self.drain()
                print "stdout"
                print "".join(so)
                print "stderr"
                print "".join(se)
            else:
                print "if lz.p is None"
            return re

        print "thread %s ended" % threading.current_thread().name

    def convert_position(self, pos):
        abet = 'abcdefghijklmnopqrstuvwxyz'
        mapped = 'abcdefghjklmnopqrstuvwxyz'
        pos = '%s%d' % (mapped[abet.index(pos[0])], self.board_size-abet.index(pos[1]))
        return pos

    def parse_position(self, pos):
        #Pass moves are the empty string in sgf files
        if pos == "pass":
            return ""

        abet = 'abcdefghijklmnopqrstuvwxyz'
        mapped = 'abcdefghjklmnopqrstuvwxyz'

        X = mapped.index(pos[0].lower())
        Y = self.board_size-int(pos[1:])

        return "%s%s" % (abet[X], abet[Y])

    def history_hash(self):
        H = hashlib.md5()
        for cmd in self.history:
            _, c, p = cmd.split()
            H.update(c[0] + p)
        return H.hexdigest()

    def add_move(self, color, pos):
        if pos == '' or pos =='tt':
            pos = 'pass'
        else:
            pos = self.convert_position(pos)
        cmd = "play %s %s" % (color, pos)
        self.history.append(cmd)

    def pop_move(self):
        self.history.pop()

    def clear_history(self):
        self.history = []

    def whoseturn(self):
        if len(self.history) == 0:
            if self.is_handicap_game:
                return "white"
            else:
                return "black"
        elif 'white' in self.history[-1]:
            return 'black'
        else:
            return 'white'

    def parse_status_update(self, message):
        M = re.match(update_regex, message)
        if M is None:
            M = re.match(update_regex_no_vn, message)

        if M is not None:
            visits = int(M.group(1))
            winrate = self.to_fraction(M.group(2))
            seq = M.group(3)
            seq = [self.parse_position(p) for p in seq.split()]

            return {'visits': visits, 'winrate': winrate, 'seq': seq}
        return {}

    # Drain all remaining stdout and stderr current contents
    def drain(self):
        so = self.stdout_thread.read_all_lines()
        se = self.stderr_thread.read_all_lines()
        return (so,se)

    # Send command and wait for ack
    def send_command(self, cmd, expected_success_count=1, drain=True, timeout=20, sleep_per_try = 0.1, nowait=True):
        self.p.stdin.write(cmd + "\n")
        tries = 0
        success_count = 0
        while tries * sleep_per_try <= timeout and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            # Readline loop
            while True:
                s = self.stdout_thread.readline()
                if (len(s)): print "STDOUT: ", s
                if (nowait): s = '='
                # Leela follows GTP and prints a line starting with "=" upon success.
                if s.strip()[0:1] == '=':
                    success_count += 1
                    if success_count >= expected_success_count:
                        if drain:
                            so,se = self.drain()
                            print "STDOUT: ", so
                            print "STDERR: ", se
                            #print >>sys.stdout, so
                            #print >>sys.stderr, se
                        return
                # No output, so break readline loop and sleep and wait for more
                if s == "":
                    break
        raise Exception("Failed to send command '%s' to Leela" % (cmd))

    #cpu version
    #def wait_start(self, expected_string="BLAS Core: Haswell", drain=True, timeout=20):
    def wait_start(self, expected_string="Detecting residual layers", drain=True, timeout=20):
    #gpu version
    #def wait_start(self, expected_string="Max workgroup dimensions", drain=True, timeout=20):
        sleep_per_try = 1
        tries = 0
        while tries * sleep_per_try <= timeout and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            print " %d seconds" % tries
            # Readline loop
            while True:
                s1 = self.stdout_thread.readline()
                print "STDOUT: ", s1
                #s = self.stderr_thread.read_all_lines()
                s = self.stderr_thread.readline()
                print "STDERR: ", s
                if s.find(expected_string)!=-1:
                    print "leela zero started %d seconds" % tries
                    if drain:
                        so,se = self.drain()
                    return
                if s == "":
                    break
                
        raise Exception("Failed to wait start Leela zero")

    def lz_analyze(self, interval=100, analyze_count=2):
        cmd = "lz-analyze %d" % interval # send analyze per second 
        self.p.stdin.write(cmd + "\n")
        sleep_per_try = interval/100
        tries = 0
        success_count = 0
        re = []
        while tries <= analyze_count and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            # Readline loop
            while True:
                s = self.stdout_thread.readline()
                #print s
                if (len(s) > 3): 
                    success_count += 1
                    re.append(s)
                    a = re[len(re)-1].split(" info move ")
                    print a[0]
                # No output, so break readline loop and sleep and wait for more
                if s == "":
                    print "success: %d" % success_count
                    break
        if success_count :
            cmd = ""
            self.p.stdin.write(cmd + "\n")
            time.sleep(sleep_per_try)
            (so,se) = self.drain()
            print "stdout"
            print "".join(so)
            print "stderr"
            print "".join(se)
            return re

        raise Exception("Failed to send command '%s' to Leela" % (cmd))

    def start(self, weight):
        #xargs = ['--puct', '0.5', '--softmax_temp', '2.0', '--fpu_reduction', '0.25']
        #xargs = ['-t8', '--gpu', '0', '--gpu', '1']
	#xargs = ['-t8', '--batchsize',  '16',  '--precision', 'half', '--disable-frac-backup', '--gpu', '0', '--gpu', '1', '--gpu', '2', '--gpu', '3']
        xargs = []

        if self.verbosity > 0:
            print >>sys.stderr, "Starting leela-zero..."
            print >>sys.stderr, self.executable
            print >>sys.stderr, weight

        p = Popen([self.executable, '--gtp', weight] + xargs, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout)
        self.stderr_thread = start_reader_thread(p.stderr)

        #time.sleep(5)
        self.wait_start()
        if self.verbosity > 0:
            print >>sys.stderr, "Setting board size %d and komi %.1f to Leela" % (self.board_size, self.komi)

        self.send_command('boardsize %d' % (self.board_size))
        self.send_command('komi %f' % (self.komi))
        #self.send_command('time_settings 0 %d 1' % (self.seconds_per_search))
        
    def stop(self):
        if self.verbosity > 0:
            print >>sys.stderr, "Stopping leela..."

        if self.p is not None:
            p = self.p
            stdout_thread = self.stdout_thread
            stderr_thread = self.stderr_thread
            self.p = None
            self.stdout_thread = None
            self.stderr_thread = None
            stdout_thread.stop()
            stderr_thread.stop()
            try:
                p.stdin.write('exit\n')
            except IOError:
                pass
            time.sleep(0.1)
            try:
                p.terminate()
            except OSError:
                pass

    def playmove(self, pos):
        color = self.whoseturn()
        self.send_command('play %s %s' % (color, pos))
        self.history.append(cmd)

    def reset(self):
        self.send_command('clear_board')

    def boardstate(self):
        self.send_command("showboard",drain=False)
        (so,se) = self.drain()
        return "".join(se)

    def name(self):
        self.send_command("name",drain=False)
        (so,se) = self.drain()
        return "".join(so)

    def version(self):
        self.send_command("version",drain=False)
        (so,se) = self.drain()
        return "".join(so)

    def list_commands(self):
        self.send_command("list_commands",drain=False)
        (so,se) = self.drain()
        return "".join(so)

    def goto_position(self):
        count = len(self.history)
        cmd = "\n".join(self.history)
        self.send_command(cmd,expected_success_count=count)

    def analyze(self):
        p = self.p
        if self.verbosity > 1:
            print >>sys.stderr, "Analyzing state:"
            print >>sys.stderr, self.whoseturn(), "to play"
            print >>sys.stderr, self.boardstate()

        self.send_command('time_left black %d 1\n' % (self.seconds_per_search))
        self.send_command('time_left white %d 1\n' % (self.seconds_per_search))

        cmd = "genmove %s\n" % (self.whoseturn())
        p.stdin.write(cmd)

        updated = 0
        stderr = []
        stdout = []

        while updated < 20 + self.seconds_per_search * 2 and self.p is not None:
            O,L = self.drain()
            stdout.extend(O)
            stderr.extend(L)

            D = self.parse_status_update("".join(L))
            if 'visits' in D:
                if self.verbosity > 0:
                    print >>sys.stderr, "Visited %d positions" % (D['visits'])
                updated = 0
            updated += 1
            if re.search(finished_regex, ''.join(stdout)) is not None:
                if re.search(stats_regex, ''.join(stderr)) is not None or re.search(bookmove_regex, ''.join(stderr)) is not None:
                    break
            time.sleep(1)

        p.stdin.write("\n")
        time.sleep(1)
        O,L = self.drain()
        stdout.extend(O)
        stderr.extend(L)

        stats, move_list = self.parse(stdout, stderr)
        if self.verbosity > 0:
            print >>sys.stderr, "Chosen move: %s" % (stats['chosen'])
            if 'best' in stats:
                print >>sys.stderr, "Best move: %s" % (stats['best'])
                print >>sys.stderr, "Winrate: %f" % (stats['winrate'])
                print >>sys.stderr, "Visits: %d" % (stats['visits'])

        return stats, move_list

    def to_fraction(self, v):
        v = v.strip()
        return 0.01 * float(v)

    def parse(self, stdout, stderr):
        if self.verbosity > 2:
            print >>sys.stderr, "LEELA STDOUT"
            print >>sys.stderr, "".join(stdout)
            print >>sys.stderr, "END OF LEELA STDOUT"
            print >>sys.stderr, "LEELA STDERR"
            print >>sys.stderr, "".join(stderr)
            print >>sys.stderr, "END OF LEELA STDERR"

        stats = {}
        move_list = []

        flip_winrate = self.whoseturn() == "white"
        def maybe_flip(winrate):
            return ((1.0 - winrate) if flip_winrate else winrate)

        finished=False
        summarized=False
        for line in stderr:
            line = line.strip()
            if line.startswith('================'):
                finished=True

            M = re.match(bookmove_regex, line)
            if M is not None:
                stats['bookmoves'] = int(M.group(1))
                stats['positions'] = int(M.group(2))

            M = re.match(status_regex, line)
            if M is not None:
                stats['mc_winrate'] = maybe_flip(float(M.group(1)))
                stats['nn_winrate'] = maybe_flip(float(M.group(2)))
                stats['margin'] = M.group(3)

            M = re.match(status_regex_no_vn, line)
            if M is not None:
                stats['mc_winrate'] = maybe_flip(float(M.group(1)))
                stats['margin'] = M.group(2)

            M = re.match(move_regex, line)
            if M is not None:
                pos = self.parse_position(M.group(1))
                visits = int(M.group(2))
                W = maybe_flip(self.to_fraction(M.group(3)))
                U = maybe_flip(self.to_fraction(M.group(4)))
                Vp = maybe_flip(self.to_fraction(M.group(5)))
                Vn = int(M.group(6))
                N = self.to_fraction(M.group(7))
                seq = M.group(8)
                seq = [self.parse_position(p) for p in seq.split()]

                info = {
                    'pos': pos,
                    'visits': visits,
                    'winrate': W, 'mc_winrate': U, 'nn_winrate': Vp, 'nn_count': Vn,
                    'policy_prob': N, 'pv': seq
                }
                move_list.append(info)

            M = re.match(move_regex_no_vn, line)
            if M is not None:
                pos = self.parse_position(M.group(1))
                visits = int(M.group(2))
                U = maybe_flip(self.to_fraction(M.group(3)))
                R = maybe_flip(self.to_fraction(M.group(4)))
                Rn = int(M.group(5))
                N = self.to_fraction(M.group(6))
                seq = M.group(7)
                seq = [self.parse_position(p) for p in seq.split()]

                info = {
                    'pos': pos,
                    'visits': visits,
                    'winrate': U, 'mc_winrate': U, 'r_winrate': R, 'r_count': Rn,
                    'policy_prob': N, 'pv': seq
                }
                move_list.append(info)

            if finished and not summarized:
                M = re.match(best_regex, line)
                if M is not None:
                    stats['best'] = self.parse_position(M.group(3).split()[0])
                    stats['winrate'] = maybe_flip(self.to_fraction(M.group(2)))

                M = re.match(stats_regex, line)
                if M is not None:
                    stats['visits'] = int(M.group(1))
                    summarized=True

        M = re.search(finished_regex, "".join(stdout))
        if M is not None:
            if M.group(1) == "resign":
                stats['chosen'] = "resign"
            else:
                stats['chosen'] = self.parse_position(M.group(1))

        if 'bookmoves' in stats and len(move_list)==0:
            move_list.append({'pos': stats['chosen'], 'is_book': True})
        else:
            required_keys = ['mc_winrate', 'margin', 'best', 'winrate', 'visits']
            for k in required_keys:
                if k not in stats:
                    print >>sys.stderr, "WARNING: analysis stats missing data %s" % (k)

            move_list = sorted(move_list, key = (lambda info: 1000000000000000 if info['pos'] == stats['best'] else info['visits']), reverse=True)
            move_list = [info for (i,info) in enumerate(move_list) if i == 0 or info['visits'] > 0]

            #In the case where leela resigns, rather than resigning, just replace with the move Leela did think was best
            if stats['chosen'] == "resign":
                stats['chosen'] = stats['best']

        return stats, move_list
