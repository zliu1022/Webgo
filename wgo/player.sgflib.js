(function(WGo, undefined) {

"use strict";

var sgflib = {
	active: true,
	query: {},
};

var handle_hash = function(player) {
	try {
		sgflib.query = JSON.parse('{"'+window.location.hash.substr(1).replace('=', '":')+'}');
	}
	catch(e) {
		sgflib.query = {};
	}
}

// add hashchange event
window.addEventListener("hashchange", function() {
	if(window.location.hash != "" && sgflib.active) {
		handle_hash();

		for(var key in sgflib.query) {
			var p_el = document.getElementById(key);
			if(p_el && p_el._wgo_player) p_el._wgo_player.goTo(move_from_hash);
		}
	}
});

// save hash query (after DOM is loaded - you can turn this off by setting WGo.Player.sgflib.active = false;
window.addEventListener("DOMContentLoaded", function() {
	if(window.location.hash != "" && sgflib.active) {
		handle_hash();
	}
});

// scroll into view of the board
window.addEventListener("load", function() {
	if(window.location.hash != "" && sgflib.active) {
		for(var key in sgflib.query) {
			var p_el = document.getElementById(key);
			if(p_el && p_el._wgo_player) {
				p_el.scrollIntoView();
				break;
			}
		}
	}
});

var move_from_hash = function() {
	if(sgflib.query[this.element.id]) {
		return sgflib.query[this.element.id].goto;
	}
}

WGo.Player.default.move = move_from_hash;

// add menu item
if(WGo.BasicPlayer && WGo.BasicPlayer.component.Control) {
	WGo.BasicPlayer.component.Control.menu.push({
		constructor: WGo.BasicPlayer.control.MenuItem,
		args: {
			name: "sgflib",
			click: function(player) {
				var link = location.href.split("#")[0]+'#'+player.element.id+'={"goto":'+JSON.stringify(player.kifuReader.path)+'}';
				var sgfstr = '<h3>'+WGo.t('sgflib')+'</h3>';
				//sgfstr += '<p><input class="wgo-sgflib" type="text" value=\''+link+'\' onclick="this.select(); event.stopPropagation()"/></p>';
				link = location.href.split("?")[0]+'?sgf=0.sgf&move=0';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>空棋盘</p>'; 

				link = location.href.split("?")[0]+'?sgf=1.sgf&move=102';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>AlphaGo vs Lee Sedol</p>'; 

				link = location.href.split("?")[0]+'?sgf=2.sgf&move=30';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>阿尔法(黑)vs柯洁(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=3.sgf&move=37';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>久保松胜喜代(黑)vs吴清源(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=4.sgf&move=68';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>赤星因彻(黑)vs本因坊丈和(白)(三妙手)</p>'; 

				link = location.href.split("?")[0]+'?sgf=5.sgf&move=127';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>安田秀策(黑)vs幻庵因硕(白)(耳赤之局)</p>'; 

				link = location.href.split("?")[0]+'?sgf=6.sgf&move=160';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>吴清源(黑)vs本因坊秀哉(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=7.sgf&move=50';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>施襄夏(黑)vs范西屏(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=8.sgf&move=102';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>AlphaGo Master(黑)vsAlphaGo Zero(白)(第一局)</p>'; 

				link = location.href.split("?")[0]+'?sgf=9.sgf&move=102';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>李世石(黑)vsAlphaGo(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=10.sgf&move=69';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>武宫正树(黑)vs林海峰(白)</p>'; 

				link = location.href.split("?")[0]+'?sgf=11.sgf&move=43';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>雁金准一(黑)vs本因坊秀哉(白)</p>'; 

				//link = location.href.split("?")[0]+'?sgf=12.sgf&move=50';
				//sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/></p>'; 

				player.showMessage(sgfstr);
				// player.showMessage('<h1>'+WGo.t('sgflib')+'</h1><p><input class="wgo-sgflib" type="text" value=\''+link+'\' onclick="this.select(); event.stopPropagation()"/></p>');
			},
		}
	});
}

WGo.Player.sgflib = sgflib;
WGo.i18n.en["sgflib"] = "Kifu Library";

})(WGo);
