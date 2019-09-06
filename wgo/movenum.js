(function(WGo) {

    var MoveNum = function(player) {
		this.player = player;
		this.board = this.player.board;
		this.node = this.player.kifuReader.node;
		this.root = this.player.kifu.root;
		
		this.backup_markup = [];
		this.show_num = true;
    }

    MoveNum.prototype.find_last_node = function(curnode, num) {
        while (curnode) {
            if (curnode.parent && num!=0) {
				curnode = curnode.parent;
				num--;
            } else {
                return curnode;
            }
        }
        return null;
    }

    MoveNum.prototype.make_num_markup = function(root, node) {
        var curnode = root.children[0];
        var markup = [];
        var i = 1;
        while (curnode != node) {
            markup.push({
                type: "LB",
                text: String(i),
                x: curnode.move.x,
                y: curnode.move.y
            });
            if (curnode.children) {
                curnode = curnode.children[0];
                i++;
            } else {
                return markup;
            }
        }
        return markup;
    }

    MoveNum.prototype.shownum = function() {
		// show last 10 move numbers
		//var root = this.find_last_node(this.player.kifuReader.node, 10);
		//var markup = this.make_num_markup(root, this.node);

        var markup = this.make_num_markup(this.root, this.node);

		this.player.kifuReader.node.markup = markup;
		this.player.update();
    }

    MoveNum.prototype.start = function() {
        this.saved_state = this.board.getState();
		this.shownum();
		this.show_num = true;
    }

    MoveNum.prototype.end = function() {
		this.show_num = false;
        this.board.restoreState({
            objects: WGo.clone(this.saved_state.objects)
        });
    }

    WGo.MoveNum = MoveNum;

    if (WGo.BasicPlayer && WGo.BasicPlayer.component.Control) {
        WGo.BasicPlayer.component.Control.menu.push({
            constructor: WGo.BasicPlayer.control.MenuItem,
            args: {
                name: "MoveNum",
                togglable: true,
                click: function(player) {
                    if (this.selected) {
                        player.setFrozen(false);
                        this._MoveNum.end();
                        delete this._MoveNum;
                        return false;
                    } else {
                        this._MoveNum = new WGo.MoveNum(player);
                        this._MoveNum.start();
                        player.setFrozen(true);
                        return true;
                    }
                },
            }
        });
    }

    WGo.i18n.en["MoveNum"] = "Move Num";

}
)(WGo);

