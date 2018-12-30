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
				link = location.href.split("?")[0]+'?sgf=1.sgf&move=50';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>AlphaGo vs Lee Sedol</p>'; 

				link = location.href.split("?")[0]+'?sgf=2.sgf&move=50';
				sgfstr += '<p><a class="wgo-sgflib" + href=\''+link+'\'/>AlphaGo vs AlphaGo</p>'; 

				player.showMessage(sgfstr);
				// player.showMessage('<h1>'+WGo.t('sgflib')+'</h1><p><input class="wgo-sgflib" type="text" value=\''+link+'\' onclick="this.select(); event.stopPropagation()"/></p>');
			},
		}
	});
}

WGo.Player.sgflib = sgflib;
WGo.i18n.en["sgflib"] = "Kifu Library";

})(WGo);
