/**
 * Webgo -- Web-Server Game Go Analyzer
 * Code licensed under AGPLv3:
 * http://www.fsf.org/licensing/licenses/agpl-3.0.html
 *
 */

(function(WGo) {

"use strict";

// board mousemove callback for edit move - adds highlighting
/*
var play_board_mouse_move = function(x,y) {
	if(this.player.frozen || (this._lastX == x && this._lastY == y)) return;
	
	this._lastX = x;
	this._lastY = y;
	
	if(this._last_mark) {
		this.board.removeObject(this._last_mark);
	}
	
	if(x != -1 && y != -1 && this.player.kifuReader.game.isValid(x,y)) {
		this._last_mark = {
			type: "outline",
			x: x,
			y: y, 
			c: this.player.kifuReader.game.turn
		};
		this.board.addObject(this._last_mark);
	}
	else {
		delete this._last_mark;
	}
}

// board mouseout callback for edit move	
var play_board_mouse_out = function() {
	if(this._last_mark) {
		this.board.removeObject(this._last_mark);
		delete this._last_mark;
		delete this._lastX;
		delete this._lastY;
	}
}
*/

// get differences of two positions as a change object (TODO create a better solution, without need of this function)
var analyze_pos_diff = function(old_p, new_p) {
	var size = old_p.size, add = [], remove = [];
	
	for(var i = 0; i < size*size; i++) {
		if(old_p.schema[i] && !new_p.schema[i]) remove.push({x:Math.floor(i/size),y:i%size});
		else if(old_p.schema[i] != new_p.schema[i]) add.push({x:Math.floor(i/size),y:i%size,c:new_p.schema[i]});
	}
	
	return {
		add: add,
		remove: remove
	}
}

WGo.Player.Analyze = {};

/**
 * Toggle play mode.
 */
	
WGo.Player.Analyze = function(player, board) {
	this.player = player;
	this.board = board;
	this.analyze = false;
}

WGo.Player.Analyze.prototype.set = function(set) {
	if(!this.analyze && set) {
		// save original kifu reader
		//this.originalReader = this.player.kifuReader;
		
		// create new reader with cloned kifu
		//this.player.kifuReader = new WGo.KifuReader(this.player.kifu.clone(), this.originalReader.rememberPath, this.originalReader.allow_illegal, this.originalReader.allow_illegal);
		
		// go to current position
		//this.player.kifuReader.goTo(this.originalReader.path);
		
		// register edit listeners
		this._ev_click = this._ev_click || this.play.bind(this);
		/*this._ev_move = this._ev_move || play_board_mouse_move.bind(this);
		this._ev_out = this._ev_out || play_board_mouse_out.bind(this);*/
		
		this.board.addEventListener("click", this._ev_click);
		/*this.board.addEventListener("mousemove", this._ev_move);
		this.board.addEventListener("mouseout", this._ev_out);*/

        /*first_bn=player.components.Control.widgets[2].element.childNodes[0]
        multiprev_bn=player.components.Control.widgets[2].element.childNodes[1]

        multinext_bn=player.components.Control.widgets[2].element.childNodes[5]
        last_bn=player.components.Control.widgets[2].element.childNodes[6]*/

        prev_bn=player.components.Control.widgets[2].element.childNodes[2]
        next_bn=player.components.Control.widgets[2].element.childNodes[4]

        next_bn.addEventListener("click",next_fn);
        next_bn.addEventListener("touchstart",next_fn_touch);
        //next_bn.addEventListener("touchend",next_fn);

        prev_bn.addEventListener("click",prev_fn);
        prev_bn.addEventListener("touchstart",prev_fn_touch);
        //prev_bn.addEventListener("touchend",prev_fn);

        var stamp=update_sess();
        ws.send("clear_board " + stamp);

        menu_analyze=1;
		this.analyze = true;
	}
	else if(this.analyze && !set) {
        console.log("Analyze set 1->0 send lz-analyze off, leela_start: ", leela_start);
        var stamp=update_sess();
        ws.send("lz-analyze " + stamp + " off");
        console.log("close analyze, remove lastObj", lastObj);
        console.log("close analyze, remove lastvarObj", lastvarObj);
        console.log("close analyze, add objbeforevar", objbeforevar);
        player.board.removeObject(lastObj);
        player.board.removeObject(lastvarObj);
        player.board.addObject(objbeforevar);
        showvar="";
        lastObj=[];
        lastvarObj=[];
        lastvarpv="";
        objbeforevar = [];

		// go to the last original position
		//this.originalReader.goTo(this.player.kifuReader.path);
		
		// change object isn't actual - update it, not elegant solution, but simple
		//this.originalReader.change = analyze_pos_diff(this.player.kifuReader.getPosition(), this.originalReader.getPosition());
		
		// update kifu reader
		//this.player.kifuReader = this.originalReader;
		//this.player.update(true);
		
		// remove edit listeners
		this.board.removeEventListener("click", this._ev_click);
		/*this.board.removeEventListener("mousemove", this._ev_move);
		this.board.removeEventListener("mouseout", this._ev_out);*/

        next_bn.removeEventListener("click",next_fn);
        next_bn.removeEventListener("touchstart",next_fn_touch);

        prev_bn.removeEventListener("click",prev_fn);
        prev_bn.removeEventListener("touchstart",prev_fn_touch);

        menu_analyze=0;
		this.analyze = false;
	}
}

WGo.Player.Analyze.prototype.play = function(x,y) {

    /*
    console.log('');
	console.log(
		'isValid: ',this.player.kifuReader.game.isValid(x, y),
		'position: ', 	this.player.kifuReader.game.position.get(x, y),
		'game.turn:',    this.player.kifuReader.game.turn,
		'node.turn:',	this.player.kifuReader.node.turn);
	console.log('node:      ', player.kifuReader.node);
	console.log('node.move: ', player.kifuReader.node.move);
    console.log('game:      ', player.kifuReader.game);
    */

	// coordinate should on board
	if(!this.player.kifuReader.game.isOnBoard(x, y)){
		return;
	}

	// empty or stone&rate
	if(player.board.obj_arr[x][y][0]){
		console.log(player.board.obj_arr[x][y][0]);
	}

	// can judge KO and suicide but can't play in the kifu
	if(!this.player.kifuReader.game.isValid(x, y) && (this.player.kifuReader.game.position.get(x, y)==0)  ){
		return;
	}

    var analyzemode = document.getElementsByClassName("wgo-menu-item wgo-menu-item-analyze")
    if ( (analyzemode.length == 0) || (analyzemode[0].classList.length!=3) ){ // no wgo-selected
        console.log("normal mode")
        return;
    }
    
    player.board.removeObject(lastObj);
    player.board.removeObject(lastvarObj);
    showvar="";
    lastObj=[];
    lastvarObj=[];
    lastvarpv="";
    
    player.board.addObject(objbeforevar);
    objbeforevar = [];
    
    var movelist = [];

	if(this.player.kifuReader.game.position.get(x, y)!=0 ){
		movelist.push({x:x, y:y, c:this.player.kifuReader.node.move.c})
	}else{
		movelist.push({x:x, y:y, c:this.player.kifuReader.game.turn})
    }
    var stamp=update_sess();
	ws.send("play-and-analyze " + stamp + " " + JSON.stringify(movelist));

	if(this.player.frozen || !this.player.kifuReader.game.isValid(x, y)) return;
	this.player.kifuReader.node.appendChild(new WGo.KNode({
		move: {
			x: x, 
			y: y, 
			c: this.player.kifuReader.game.turn
		}, 
		_edited: true
	}));
	this.player.next(this.player.kifuReader.node.children.length-1);
    
}

if(WGo.BasicPlayer && WGo.BasicPlayer.component.Control) {
	WGo.BasicPlayer.component.Control.menu.push({
		constructor: WGo.BasicPlayer.control.MenuItem,
		args: {
			name: "analyze",
			togglable: true,
			click: function(player) { 
				this._analyze = this._analyze || new WGo.Player.Analyze(player, player.board);
				this._analyze.set(!this._analyze.analyze);
				return this._analyze.analyze;
			},
			init: function(player) {
				var _this = this;
				player.addEventListener("frozen", function(e) {
					_this._disabled = _this.disabled;
					if(!_this.disabled) _this.disable();
				});
				player.addEventListener("unfrozen", function(e) {
					if(!_this._disabled) _this.enable();
					delete _this._disabled;
				});
			},
		}
	}); 
}

var RATE = {
    stone: {
        draw: function(args, board) {
            var xr = board.getX(args.x),
                yr = board.getY(args.y),
                sr = board.stoneRadius;
            var font = "verdana" //calibri is WGo's default

            // draw circle
            this.beginPath();
            this.arc(xr-board.ls, yr-board.ls, sr*1.15, 0, 2*Math.PI, true);
            this.fillStyle = args.style;
            this.fill();

            //draw line
            this.beginPath();
            this.lineWidth = 1;
            this.strokeStyle="green";
            this.moveTo(xr-0.9*sr, yr);
            this.lineTo(xr+0.9*sr, yr);
            this.stroke();

            // draw winrate
            this.fillStyle = "white";
            if(args.winrate.length == 1) this.font = Math.round(sr*1.05)+"px "+font;
            else if(args.winrate.length == 2) this.font = Math.round(sr*1.05)+"px "+font;
            else if(args.winrate.length == 3) this.font = Math.round(sr*1.05)+"px "+font;
            else this.font = Math.round(sr*1.1)+"px "+font;

            this.beginPath();
            this.textBaseline="bottom";
            this.textAlign="center";
            this.fillText(args.winrate, xr, yr+0.14*sr, 1.8*sr);
            
            // draw visits
            this.fillStyle = "white";
            if(args.visits.length == 1) this.font = Math.round(sr*0.8)+"px "+font;
            else if(args.visits.length == 2) this.font = Math.round(sr*0.8)+"px "+font;
            else if(args.visits.length == 3) this.font = Math.round(sr*0.8)+"px "+font;
            else this.font = Math.round(sr*0.8)+"px "+font;

            this.beginPath();
            this.textBaseline="top";
            this.textAlign="center";
            this.fillText(args.visits, xr, yr-0.14*sr, 1.9*sr);
        },
    },
    /*grid: {
			draw: function(args, board) {
				//if(!is_here_stone(board, args.x, args.y) && !args._nodraw) {
					var xr = board.getX(args.x),
						yr = board.getY(args.y),
						sr = board.stoneRadius;
					this.clearRect(xr-sr,yr-sr,2*sr,2*sr);
				//}
			},
			clear: function(args, board) {
				//if(!is_here_stone(board, args.x, args.y))  {
					args._nodraw = true;
					redraw_layer(board, "grid");
					delete args._nodraw;
				//}
			}
		},*/
};

// last draw rate-circle
var lastObj=[];

// last variation chain
var lastvarObj=[];
var lastvarpv="";
var lastpassstr="";
var lastdupstr="";
// stone on board before draw variation
var objbeforevar=[];

// status of menu analyze
var menu_analyze=0;

// status of engine
var leela_start=0;

var host_name=window.location.hostname;
var ws_str="ws://"+host_name+":32019/websocket"
//var analyze_type="zen7"
var analyze_type="leelaz"

var ws_alive = false;
var ws = new WebSocket(ws_str);
init_ws();

var analyze_interval = 50;
var sess=-1;
var update_sess = function(){
    var stamp=Date.now();
    /*
    var d = new Date();
    var str_month = "";
    if (d.getMonth()<9) {
        str_month = "0" + (d.getMonth()+1);
    } else {
        str_month = (d.getMonth(+1));
    }
    var stamp = d.getFullYear() + "-" + str_month + "-" + d.getDate() + " " +
        d.getHours() + ":" + d.getMinutes() + ":" + d.getSeconds() + "." + d.getMilliseconds();
    */
    sess=stamp;
    return stamp;
}

var prev_bn={};
var next_bn={};

var next_fn_count=0;

var next_fn = function(){
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    console.log("next button pressed ", next_fn_count);
    next_fn_count+=1;
    next_fn_touch();
}
var next_fn_touch=function(){
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    var curmove = player.kifuReader.node.move;
    console.log("next button touched ", next_fn_count);
    console.log(curmove.x, curmove.y, curmove.c)
    next_fn_count+=1;

    var analyzemode = document.getElementsByClassName("wgo-menu-item wgo-menu-item-analyze")
    if ( (analyzemode.length == 0) || (analyzemode[0].classList.length!=3) ){ // no wgo-selected
        console.log("normal mode")
        //elem_content.innerText += " normal mode";
        return;
    }
    
    //console.log("next_fn_touch remove lastObj", lastObj);
    //console.log("next_fn_touch remove lastvarObj", lastvarObj);
    player.board.removeObject(lastObj);
    player.board.removeObject(lastvarObj);
    showvar="";
    lastObj=[];
    lastvarObj=[];
    lastvarpv="";
    
    player.board.addObject(objbeforevar);
    objbeforevar = [];
    
    var movelist = [];
    movelist.push({x:curmove.x, y:curmove.y, c:curmove.c})
    if(curmove && !curmove.pass) { // not home and not pass
        player.board.addObject({x:curmove.x, y:curmove.y, c:curmove.c});
    }
    var stamp=update_sess();
    ws.send("play-and-analyze " + stamp + " " + JSON.stringify(movelist));
}

var prev_fn_count=0;
var prev_fn=function(){
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    console.log("previous button pressed ", prev_fn_count);
    prev_fn_count+=1;
    prev_fn_touch();
}
var prev_fn_touch=function(){
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    var curmove = player.kifuReader.node.move;
    console.log("previous button touched ", prev_fn_count);
    if (curmove) {
        console.log(curmove.x, curmove.y, curmove.c)
    } else {
        console.log("prev to home");
    }
    prev_fn_count+=1;
    
    var analyzemode = document.getElementsByClassName("wgo-menu-item wgo-menu-item-analyze")
    if ( (analyzemode.length == 0) || (analyzemode[0].classList.length!=3) ){ // no wgo-selected
        console.log("normal mode")
        //elem_content.innerText += " normal mode";
        return;
    }
    player.board.removeObject(lastObj);
    player.board.removeObject(lastvarObj);
    showvar="";
    lastObj=[];
    lastvarObj=[];
    lastvarpv="";
    
    player.board.addObject(objbeforevar);
    objbeforevar = [];
    
    if(curmove && !curmove.pass) { // not home and not pass
        player.board.addObject({x:curmove.x, y:curmove.y, c:curmove.c});
        console.log("prev_fn_touch addObject ", curmove);
    }
    var stamp=update_sess();
    ws.send("undo-and-analyze " + stamp);
}

var timeId = setInterval(function(){
    if (menu_analyze == 0) {
        if (ws_alive == false) {
            console.log("server is down, reconnecting ... ", ws.readyState);
            ws = new WebSocket(ws_str);
            init_ws();
        } else {
            var stamp=update_sess();
            ws.send("time " + stamp);
            ws_alive = false;
        }
    } else {
        if (leela_start == 0) {
            console.log("engine is down, reconnecting ... ", ws.readyState);
            ws_alive = false;
            ws = new WebSocket(ws_str);
            init_ws();
        } else {
            leela_start = 0;
        }
    }
}, 5000);

var log_obj = function (obj) {
    console.log("log_obj: ", obj.length);
    if (obj.length==0) {
        return;
    }
    for (var i=0; i<obj.length; i++) {
        console.log("log_obj: ", obj[i].x,obj[i].y,obj[i].c);
    }
}

function send_playlist() {
    var n = player.kifu.root;
    var setup = n.setup;
    var movelist = [];

    // first place stone
    if (setup){
        for ( var i=0; i< setup.length; i++) {
            movelist.push({x:setup[i].x, y:setup[i].y, c:setup[i].c})
        }
    }
    
    // empty board and no stone has been added
    if ( (player.kifuReader.path.m==0) && (movelist.length==0) ){
        var stamp=update_sess();
        ws.send("lz-analyze " + stamp + " " + analyze_type + " " + analyze_interval);
        return;
    }

    // then play move
    for ( var i=0; i< player.kifuReader.path.m; i++) {
        if (n.children.length!=0) {
            if (player.kifuReader.path[i+1]) {
                n = n.children[player.kifuReader.path[i+1]];
            } else {
                n = n.children[0];
            }
        }
        if(n.move.pass) {
            movelist.push({x:n.move.x, y:n.move.y, c:n.move.c}) // this should be pass
            //movelist.push({c:n.move.c})
        } else {
            movelist.push({x:n.move.x, y:n.move.y, c:n.move.c})
        }
    }
    var stamp=update_sess();
    ws.send("playlist " + stamp + " " + JSON.stringify(movelist));
}

function init_ws() {
ws.onopen = function() {
    //show some hint info
    console.log("websocket onopen: ", ws.readyState);
    ws_alive = true;

    if (menu_analyze == 1){
        send_playlist();
    }

    var elem_white=document.getElementsByClassName("wgo-box-wrapper wgo-player-wrapper wgo-white")[0];
    var elem_black=document.getElementsByClassName("wgo-box-wrapper wgo-player-wrapper wgo-black")[0];
    var black_click = function() {
        console.log("black_click");
        //elem_black.style.boxShadow = "0px 0px 15px 1.5px #95B8E7"
        //elem_white.style.boxShadow = "none"

        var stamp=update_sess();
        ws.send("hello " + stamp);
    }
    var black_touch = function() {
        console.log("black_touch");
    }
    var white_click = function() {
        console.log("white_click");
        //elem_black.style.boxShadow = "none"
        //elem_white.style.boxShadow = "0px 0px 15px 1.5px #95B8E7"

        var stamp=update_sess();
        ws.send("time " + stamp);
    }
    var white_touch = function() {
        console.log("white_touch");
    }
    elem_black.addEventListener("click", black_click);
    //elem_black.addEventListener("touchstart", black_touch);
    elem_white.addEventListener("click", white_click);
    //elem_white.addEventListener("touchstart", white_touch);

};

ws.error = function() {
    console.log("websocket error: ", ws, ws.readyState);
};

ws.close = function() {
    console.log("websocket close: ", ws, ws.readyState);
};

ws.onmessage = function (evt) {
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    var displayWidth=elem_content.offsetWidth;
    var elem_notification = document.getElementsByClassName("wgo-notification")[0];
    var ret = JSON.parse(evt.data);

    if(ret.cmd=="hello"){
        console.log("RESP: hello");
    }else if(ret.cmd=="time"){
        ws_alive = true;
        if (ret.sess != sess){
            console.log("wrong sess: ", ret.sess, sess-ret.sess);
            return;
        }
        console.log("RESP: ", ret.result);
    }else if(ret.cmd=="clear_board"){
        leela_start = 1;
        elem_content.innerText="= "+ret.cmd+" "+ret.result;
        if(ret.result=="ok"){
            send_playlist();
        }
    }else if(ret.cmd=="playlist"){
        leela_start = 1;
        if(ret.result=="ok"){
            var stamp=update_sess();
            ws.send("lz-analyze " + stamp + " " + analyze_type + " " + analyze_interval);
            elem_notification.style.display="none";
        }else{
            elem_notification.innerText="= "+ret.cmd+"-"+ret.para+" "+ret.result;
            elem_notification.style.display="";
        }
    }else if(ret.cmd=="lz-analyze"){
        if(ret.result=="ok"){
            // only lz-analyze sess off return ok
            leela_start = 0;
            //elem_content.innerText="= "+ret.cmd+"-"+ret.para+" "+ret.result;
        } else {
            leela_start = 1;
            if (ret.sess != sess){
                console.log("wrong sess: ", ret.sess, sess-ret.sess);
                return;
            }
            // new create <a>
            if(document.getElementById("0")==null){
            //if(elem_content.children.length==0 || elem_content.children[0].className=="wgo-info-list"){
                elem_content.innerText="= "+ret.cmd+ "-"+ displayWidth +"-"+ ret.result.length;
                for(var i = 0; (i < 33); i++) {
                    //var existingLength = ret.result[i].move.length + " " + ret.result[i].visits.length + 3 + 4;
                    //elem_content.innerHTML += "<p><a href=\"javascript:void(0)\" id=\"" + ret.result[i].move + "\" onclick=\"show_var(this)\" value=\"Q16 Y15\">" + ret.result[i].move + " " + ret.result[i].visits  + " " + Math.round(ret.result[i].winrate/10)/10 +"%" + " " + ret.result[i].pv.slice(0,displayWidth/8) + "..." + "</a>" + "</p>";
                    //elem_content.innerHTML += "<p><a href=\"javascript:void(0)\" id=\"" + ret.result[i].move + "\" onclick=\"show_var(this)\" value=\"Q16 Y15\">" + ret.result[i].move + " " + ret.result[i].visits  + " " + Math.round(ret.result[i].winrate/10)/10 +"%" + " " + ret.result[i].pv.slice(0,30) + "..." + "</a>" + "</p>";
                    
                    var elp = document.createElement("p");
                    var ela = document.createElement("a");
                    ela.href = "javascript:void(0)";
                    ela.id = i;
                    ela.onclick = function(){
                        show_var(this);
                    };
                    elp.appendChild(ela);
                    elp.style.display="none";
                    elem_content.appendChild(elp);
                }
            }
            // modify <a> text
            for(var i = 0; (i < 33); i++) {
                //elem_content.innerText="= "+ret.cmd+ "-"+ displayWidth +"-"+ ret.result.length;
                var ela = elem_content.children[i].children[0];
                if(i < ret.result.length) {
                    //ela.title = ret.result[i].move;
                    ela.text = ret.result[i].move + " " + ret.result[i].visits  + " " + Math.round(ret.result[i].winrate/10)/10 +"%" + " " + ret.result[i].pv.slice(0,displayWidth/8) + "...";
                    ela.name = ret.result[i].move;
                    elem_content.children[i].style.display="";
                }else{
                    elem_content.children[i].style.display="none";
                }
            }

            if(ret.result.length!=0){
                var obj=[];
                // favorite color list:
                //var style = ["#F22F08", "#F03625", "#C0334D", "#720017", "#D6618F", "#8D2F23", "#F1931B", "#522E75", "#D50B53", "#824CA7", "#14325C"];
                var style = ["#C0334D", "#D6618F", "#F1931B"];
                var x=-1,y=-1,winrate="",visits="";
                for(var i = 0; i < ret.result.length; i++) {
                    if ( (showvar!="") && (ret.result[i].move!=showvar)){
                        continue;
                    }
                    x = ret.result[i].x;
                    y = ret.result[i].y;
                    if ((x==player.kifuReader.game.size) || (y==player.kifuReader.game.size)) {
                        continue;
                    }
                    var rt = parseInt(ret.result[i].winrate,0);
                    if (i==0){
                        rt = Math.round(rt/100);
                    }else{
                        rt = Math.round(rt/10)/10;
                    }
                    winrate = rt.toString(10);
                    var vn = parseInt(ret.result[i].visits,0);
                    if (vn > 999999) {
                        visits = Math.floor(vn/100000)/10 + "m";
                    } else if (vn > 9999){
                        visits = Math.floor(vn/100)/10 + "k";
                    }else{
                        visits = ret.result[i].visits;
                    }
                    if (i<style.length) {
                        obj.push( {x:x,y:y, type:RATE, winrate:winrate, visits:visits, style:style[i]} );
                    } else {
                        obj.push( {x:x,y:y, type:RATE, winrate:winrate, visits:visits, style:style[style.length-1]} );
                    }
                }
                player.board.removeObject(lastObj);
                lastObj = obj.concat();
                obj=[];
                player.board.addObject(lastObj);

                if (showvar!="") {
                    player.board.removeObject(lastvarObj);
                    player.board.addObject(objbeforevar);

                    for(var i = 0; i < ret.result.length; i++) {
                        if (ret.result[i].move==showvar){
                            elem_notification.innerText = showvar;
                            elem_notification.style.display="";
                            if (lastpassstr!=""){
                                elem_notification.innerText += lastpassstr;
                            }
                            if (lastdupstr!=""){
                                elem_notification.innerText += lastdupstr;
                            }

                            var pv = ret.result[i].pv.trim(" ");
                            if (lastvarpv==pv){
                                console.log("addObject same");
                                player.board.addObject(lastvarObj);
                                return;
                            }
                            lastvarpv=pv;
                            lastpassstr="";
                            lastdupstr="";

                            var xlist="ABCDEFGHJKLMNOPQRST";
                            var pvlist=pv.split(" ");
                            var varobj=[];
                            var curc=player.kifuReader.game.turn;
                            var passstr="";
                            var dupstr="";
                            var tmpobjbeforevar = [];
                            for(var j = 0; j < pvlist.length; j++) {
                                if ( pvlist[j]=="pass" ){
                                    passstr += j+1 + ",";
                                    curc = -1*curc;
                                    continue;
                                }
                                if ( j==0 ){
                                    curc = -1*curc;
                                    continue;
                                }
                                var tmpdupstr="";
                                // if pvlist[j] duplicate with earlier pvlist[0:j-1] add to dupstr, change color and cont
                                for(var k = 0; k < j-1; k++) {
                                    if (pvlist[k]==pvlist[j]) {
                                        dupstr += (j+1) + "=" + (k+1) +"(" + pvlist[j] + ") ";
                                        tmpdupstr = dupstr;
                                        break;
                                    }
                                }
                                if (tmpdupstr!="") {
                                    curc = -1*curc;
                                    continue;
                                }
                                var varx=xlist.indexOf(pvlist[j][0]);
                                var vary=player.kifuReader.game.size-parseInt(pvlist[j].slice(1,pvlist[j].length));
                                
                                if(player.board.obj_arr[varx][vary][0] && !(player.board.obj_arr[varx][vary][0].type)){
                                    tmpobjbeforevar.push( player.board.obj_arr[varx][vary][0] );
                                }

                                //console.log(pvlist[j] + " -> " + varx + ", " + vary);
                                varobj.push( {x:varx,y:vary, c: curc} );
                                varobj.push( {x:varx,y:vary, type:WGo.Board.drawHandlers.LB, text:j+1} );
                                curc = -1*curc;
                            }
                            if (passstr!=""){
                                passstr = " " + passstr + "=pass";
                                elem_notification.innerText = passstr;
                                lastpassstr = passstr;
                            }
                            if (dupstr!=""){
                                dupstr = " " + dupstr;
                                elem_notification.innerText += dupstr;
                                lastdupstr = dupstr;
                            }
                            
                            log_obj(tmpobjbeforevar);
                            objbeforevar = tmpobjbeforevar.concat();
                            tmpobjbeforevar = [];

                            lastvarObj = varobj.concat();
                            varobj = [];
                            player.board.addObject(lastvarObj);
                            console.log("addObject new ");
                            break;
                        }
                    }
                } else {
                    elem_notification.style.display="none";
                    if(lastvarObj.length!=0){
                        console.log("close var, remove lastvarObj");
                        player.board.removeObject(lastvarObj);
                        lastvarObj = [];
                        lastvarpv = "";
                    }
                    if(objbeforevar.length!=0){
                        console.log("close var, add objbeforevar");
                        player.board.addObject(objbeforevar);
                        objbeforevar = [];
                    }
                }
            }
        }
    }else if(ret.cmd=="undo-and-analyze"){
        leela_start = 1;
    }else if(ret.cmd=="play-and-analyze"){
        leela_start = 1;
    }
};

}

WGo.i18n.en["analyze"] = "Analyze";

})(WGo);
