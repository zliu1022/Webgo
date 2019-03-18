# Webgo

# Introduction
Using web browser to visit game go AI program in remote computer.
Remote computer can be personal computer or cloud compute service, now Webgo server part can support leela zero in windows, mac or linux and support Zen6,Zen7 in windows.
Then you can play game or analyze kifu with AI.

![screenshot](screenshot/chinese.PNG)

# Dependency and acknowledge
1. Web page based on WGo.js.
2. Server side based on [Leela Analysis Scripts](https://github.com/lightvector/leela-analysis)
3. Server side depends on Python module: bottle, gevent and gevent-websocket
4. Also use some sabaki theme, which is my favorite go UI

# Server Configuration
Change to your own leelazero executable path and weights in ```svr\webgo.py```
```
executable = "c:/github/Webgo/dist/leelaz.exe"
weight = '-wc:/github/Webgo/dist/v1.gz'
```
Change the command line option in leelaz.py
```
xargs = ['-t8', '--gpu', '0', '--gpu', '1']
```

# Start Server and play with it
server side, under cmd.exe run:
```
cd Webgo
c:\python2.7\python svr\webgo.py
```

Then on pad/phone open any web browser
```
http://your_ip：8000/webgo.html?sgf=1.sgf&move=50
```

# Using Webgo in mac
1. Install brew using ruby
```
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```
2. git clone branch
```
git clone -b next https://github.com/gcp/leela-zero.git
```
3. install boost
```
brew install boost
```
4. Compile leelaz with boardsize 9 or 19
5. using curl -O or ftp to get weight
6. full-tuner
7. install pip， bottle, gevent, gevent-websocket
```
sudo easy_install pip
sudo pip install bottle
pip install --user greenlet
pip install --user gevent
pip install --user gevent-websocket
```
If failed, maybe need to install pyenv, then using pyenv to install another version python
pyenv global 2.7.11 to switch version, but wish you lucky

# Using Webgo server in google cloud
1. Compile and run leelazero
Please refer to readme of [leela-zero](https://github.com/leela-zero/leela-zero/blob/master/README.md)
2. Install Webgo
sudo apt install python-minimal
sudo apt install python-pip
pip install bottle gevent gevent-websocket
mkdir github
cd github
git clone https://github.com/zliu1022/Webgo.git -b next Webgo-next
cd Wegbo-next
mkdir dist
3. Config engine and weights
cp leelaz ~/github/Webgo/dist/leelaz
cp network.gz ~/github/Webgo/dist/network.gz
4. run server and open firewall's corresponding port
python svr/webgo.py

# License

The code is released under the AGPLv3 or later.
