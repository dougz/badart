goog.require('goog.dom');
goog.require('goog.dom.classlist');
goog.require('goog.dom.TagName');
goog.require('goog.events');
goog.require('goog.events.KeyCodes');
goog.require('goog.net.XhrIo');
goog.require("goog.json.Serializer");

class BadArtCountdown {
    constructor(msg, end_time) {
	this.msg = msg;
	this.end_time = end_time;
	this.timer = setInterval(goog.bind(this.update_timer, this), 1000);
    }

    update_timer() {
	var now = (new Date()).getTime() / 1000.0;
	var s = this.end_time - now;
	if (s < 0) s = 0;
	var min = Math.trunc(s/60);
	var sec = Math.trunc(s%60);
	var text = this.msg + " " + min + ":" + (""+sec).padStart(2, "0") + ".";
	badart.countdown_span.innerHTML = text;
    }

    finish() {
	clearInterval(this.timer);
	badart.countdown_span.innerHTML = "";
    }
}


class BadArtDispatcher {
    constructor() {
	this.methods = {
	    "show_message": this.show_message,
	    "prompt_open": this.prompt_open,
	    "show_image": this.show_image,
	    "play_audio": this.play_audio,
	    "add_chat": this.add_chat,
            "players": this.players,
	}
    }

    /** @param{Message} msg */
    dispatch(msg) {
	this.methods[msg.method](msg);
    }

    /** @param{Message} msg */
    show_message(msg) {
	badart.gallery.style.display = "none";
	badart.entry.style.display = "none";
	badart.message.style.display = "block";
	badart.message.innerHTML = msg.text;

	if (msg.end_time) {
	    if (badart.countdown) {
		badart.countdown.finish();
	    }
	    badart.countdown = new BadArtCountdown(msg.countdown_text, msg.end_time);
	}
    }

    /** @param{Message} msg */
    prompt_open(msg) {
	badart.open.style.display = "inline";
	badart.gallery.style.display = "none";
	badart.entry.style.display = "none";
	badart.message.style.display = "block";
	badart.message.innerHTML = msg.text;
    }

    /** @param{Message} msg */
    players(msg) {
        var el = goog.dom.getElement("players");
        el.innerHTML = "<b>Players:</b> " + msg.players;
    }

    /** @param{Message} msg */
    show_image(msg) {
	if (msg.end_time) {
	    if (badart.countdown == null) {
		badart.countdown = new BadArtCountdown("The gallery will close in", msg.end_time);
	    }
	} else {
	    if (badart.countdown) {
		badart.countdown.finish();
	    }
	}
	badart.gallery.style.display = "block";
	badart.message.style.display = "none";
	badart.open.style.display = "none";
	if (msg.title) {
	    goog.dom.classlist.add(badart.art, "framed");
	    badart.caption.style.display = "flex";
	    badart.entry.style.display = "none";
	    badart.title.innerHTML = msg.title;
	    badart.text.value = "";
	} else {
	    goog.dom.classlist.remove(badart.art, "framed");
	    badart.caption.style.display = "none";
	    badart.entry.style.display = "flex";
	    if (document.activeElement.tagName != "INPUT") badart.text.focus();
	}

	badart.art.src = msg.image;
	badart.preload.src = msg.preload;
    }

    /** @param{Message} msg */
    play_audio(msg) {
	if (msg.url) {
	    var audio = new Audio(msg.url);
	    audio.play();
	}
    }

    /** @param{Message} msg */
    add_chat(msg) {
	var curr = goog.dom.getChildren(badart.chat);
	if (curr.length > 3) {
	    goog.dom.removeNode(curr[0]);
	}
	var el = goog.dom.createDom("P");
        el.innerHTML = msg.text;
	badart.chat.appendChild(el);
    }
}

function badart_submit(e) {
    var answer = badart.text.value;
    if (answer == "") return;
    badart.text.value = "";
    var username = badart.who.value;
    localStorage.setItem("name", username);
    var msg = badart.serializer.serialize({"answer": answer, "who": username});
    goog.net.XhrIo.send("/artsubmit", Common_expect_204, "POST", msg);
    e.preventDefault();
}


function badart_onkeydown(e) {
    if (e.keyCode == goog.events.KeyCodes.ENTER) {
	badart_submit(e);
    }
}

function badart_send_name() {
    var name = badart.who.value;
    if (name != badart.sent_name) {
        badart.sent_name = name;
        var msg = badart.serializer.serialize({"who": name});
        goog.net.XhrIo.send("/artname", Common_expect_204, "POST", msg);
    }
}

var badart = {
    body: null,
    gallery: null,
    open: null,
    art: null,
    caption: null,
    entry: null,
    title: null,
    waiter: null,
    text: null,
    who: null,
    chat: null,
    message: null,
    preload: null,
    countdown_span: null,
    countdown: null,
    serializer: null,
    sent_name: null,
}

puzzle_init = function() {
    badart.serializer = new goog.json.Serializer();

    badart.body = goog.dom.getElement("puzz");
    badart.gallery = goog.dom.getElement("gallery");
    badart.open = goog.dom.getElement("open");
    badart.art = goog.dom.getElement("art");
    badart.caption = goog.dom.getElement("caption");
    badart.entry = goog.dom.getElement("entry");
    badart.text = goog.dom.getElement("text");
    badart.title = goog.dom.getElement("title");
    badart.who = goog.dom.getElement("who");
    badart.who.value = localStorage.getItem("name");
    badart.chat = goog.dom.getElement("chat");
    badart.message = goog.dom.getElement("message");
    badart.countdown_span = goog.dom.getElement("countdown");
    badart.preload = goog.dom.getElement("preload");

    goog.events.listen(goog.dom.getElement("text"),
		       goog.events.EventType.KEYDOWN,
		       badart_onkeydown);
    goog.events.listen(goog.dom.getElement("artsubmit"),
		       goog.events.EventType.CLICK,
		       badart_submit);
    goog.events.listen(badart.open,
		       goog.events.EventType.CLICK,
		       goog.bind(goog.net.XhrIo.send, null, "/artopen"));

    badart.waiter = new Common_Waiter(new BadArtDispatcher(), "/artwait", 0, null, null);
    badart.waiter.start();

    setInterval(badart_send_name, 1000);
}

