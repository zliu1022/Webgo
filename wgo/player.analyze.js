
(function(WGo) {

// board mousemove callback for edit move - adds highlighting
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
		this.originalReader = this.player.kifuReader;
		
		// create new reader with cloned kifu
		this.player.kifuReader = new WGo.KifuReader(this.player.kifu.clone(), this.originalReader.rememberPath, this.originalReader.allow_illegal, this.originalReader.allow_illegal);
		
		// go to current position
		this.player.kifuReader.goTo(this.originalReader.path);
		
		// register edit listeners
		this._ev_click = this._ev_click || this.play.bind(this);
		this._ev_move = this._ev_move || play_board_mouse_move.bind(this);
		this._ev_out = this._ev_out || play_board_mouse_out.bind(this);
		
		this.board.addEventListener("click", this._ev_click);
		this.board.addEventListener("mousemove", this._ev_move);
		this.board.addEventListener("mouseout", this._ev_out);
		
		this.analyze = true;
	}
	else if(this.analyze && !set) {
		// go to the last original position
		this.originalReader.goTo(this.player.kifuReader.path);
		
		// change object isn't actual - update it, not elegant solution, but simple
		this.originalReader.change = analyze_pos_diff(this.player.kifuReader.getPosition(), this.originalReader.getPosition());
		
		// update kifu reader
		this.player.kifuReader = this.originalReader;
		this.player.update(true);
		
		// remove edit listeners
		this.board.removeEventListener("click", this._ev_click);
		this.board.removeEventListener("mousemove", this._ev_move);
		this.board.removeEventListener("mouseout", this._ev_out);
		
		this.analyze = false;
	}
}

WGo.Player.Analyze.prototype.play = function(x,y) {
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
                
                if (leela_start == 0 ) {
                    ws.send("clear_board");
                } else {
                    ws.send("lz-analyze off");
                }

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
            font = "verdana" //calibri is WGo's default
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
            font = "verdana"; //calibri
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

var lastObj=[];
var lastvarObj=[];
var lastvarpv="";
var leela_start=0;
var host_name=window.location.host;
var ws_str="ws://"+host_name+":32002/websocket"
var ws = new WebSocket(ws_str);
ws.onopen = function() {
    //show some hint info
};

ws.onmessage = function (evt) {
    var elem_content = document.getElementsByClassName("wgo-comment-text")[0];
    var elem_notification = document.getElementsByClassName("wgo-notification")[0];
    ret = JSON.parse(evt.data);
    if(ret.cmd=="time"){
        //show time code
    }else if(ret.cmd=="clear_board"){
        elem_content.innerText="= "+ret.cmd+" "+ret.result;
        if(ret.result=="ok"){
            leela_start=1;
            
            if (player.kifuReader.path.m==0){
                ws.send("lz-analyze 100");
                return;
            }

            var n = player.kifu.root;
            var movelist = [];
            for ( i=0; i< player.kifuReader.path.m; i++) {
                if (n.children.length!=0) {
                    if (player.kifuReader.path[i+1]) {
                        n = n.children[player.kifuReader.path[i+1]];
                    } else {
                        n = n.children[0];
                    }
                }
                if(n.move.pass) {
                    movelist.push({x:n.move.x, y:n.move.y, c:n.move.c})
                } else {
                    movelist.push({x:n.move.x, y:n.move.y, c:n.move.c})
                }
            }
            ws.send("playlist " + JSON.stringify(movelist));
        }
    }else if(ret.cmd=="leelaz-stop"){
        elem_content.innerText="= "+ret.cmd+" "+ret.result;
        if(ret.result=="ok"){
            leela_start=0;
        }
    }else if(ret.cmd=="playlist"){
        if(ret.result=="ok"){
            ws.send("lz-analyze 100");
            elem_notification.style.display="none";
        }else{
            elem_notification.innerText="= "+ret.cmd+"-"+ret.para+" "+ret.result;
            elem_notification.style.display="";
        }
    }else if(ret.cmd=="lz-analyze"){
        if(ret.result=="ok"){
            elem_content.innerText="= "+ret.cmd+"-"+ret.para+" "+ret.result;
            player.board.removeObject(lastObj);
            player.board.removeObject(lastvarObj);
            leela_start = 0;
            show_var="";
        } else {
            elem_content.innerText="= "+ret.cmd+ "-"+ ret.result.length + "\r\n";
            for(var i = 0; (i < 29 && i < ret.result.length); i++) {
                elem_content.innerHTML += "<p><a href=\"javascript:void(0)\" id=\"" + ret.result[i].move + "\" onclick=\"show_var(this)\" value=\"Q16 Y15\">" + ret.result[i].move + " " + ret.result[i].visits  + " " + Math.round(ret.result[i].winrate/10)/10 +"%" + " " + ret.result[i].pv.slice(0,28) + "..." + "</a>" + "</p>";
            }
            if(ret.result.length!=0){
                var obj=[];
                // favorite color list:
                //var style = ["#F22F08", "#F03625", "#C0334D", "#720017", "#D6618F", "#8D2F23", "#F1931B", "#522E75", "#D50B53", "#824CA7", "#14325C"];
                var style = ["#C0334D", "#D6618F", "#F1931B"];
                var x=-1,y=-1,winrate="",visits="";
                for(var i = 0; i < ret.result.length; i++) {
                    x = ret.result[i].x;
                    y = ret.result[i].y;
                    if ((x==19) || (y==19)) {
                        continue;
                    }
                    rt = parseInt(ret.result[i].winrate,0);
                    if (i==0){
                        rt = Math.round(rt/100);
                    }else{
                        rt = Math.round(rt/10)/10;
                    }
                    winrate = rt.toString(10);
                    var vn = parseInt(ret.result[i].visits,0);
                    if (vn > 9999){
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
                console.log("remove " + lastObj.length + " add " + obj.length);
                player.board.removeObject(lastObj);
                lastObj = obj;
                player.board.addObject(obj);
                
                if (showvar!="") {
                    for(var i = 0; i < ret.result.length; i++) {
                        if (ret.result[i].move==showvar){
                            elem_notification.innerText="= "+ "showvar " + showvar + " " + ret.result[i].pv;
                            elem_notification.style.display="";
                            console.log("showvar: " + ret.result[i].pv);
                            
                            var pv = ret.result[i].pv.trim(" ");
                            if (lastvarpv==pv){
                                player.board.addObject(lastvarObj);
                                console.log("add var again " + lastvarObj.length);
                                return;
                            }
                            lastvarpv=pv;

                            var xlist="ABCDEFGHJKLMNOPQRST";
                            var pvlist=pv.split(" ");
                            var varobj=[];
                            var curc=player.kifuReader.node.move.c;
                            for(var j = 0; j < pvlist.length; j++) {
                                varx=xlist.indexOf(pvlist[j][0]);
                                vary=19-parseInt(pvlist[j].slice(1,pvlist[j].length));
                                //console.log(pvlist[j] + " -> " + x + ", " + y);
                                if (j==0){
                                    continue;
                                }
                                varobj.push( {x:varx,y:vary, c: curc} );
                                if (curc==WGo.B) {
                                    curc=WGo.W;
                                }else{
                                    curc=WGo.B;
                                }
                                varobj.push( {x:varx,y:vary, type:WGo.Board.drawHandlers.LB, text:j} );
                            }
                            console.log("remove var " + lastvarObj.length + " add " + varobj.length);
                            player.board.removeObject(lastvarObj);
                            lastvarObj = varobj;
                            player.board.addObject(varobj);
                            break;
                        }
                    }
                } else {
                    elem_notification.style.display="none";
                    player.board.removeObject(lastvarObj);
                    console.log("remove var " + lastvarObj.length);
                }
            }
        }
    }
};


WGo.i18n.en["analyze"] = "Analyze";

})(WGo);
