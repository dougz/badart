/** @type{?function()} */
var puzzle_init;

/** @type{number} */
var waiter_id;

/** @type{Storage} */
var localStorage;

class Message {
    constructor() {
	/** @type{string} */
	this.method;
	/** @type{?string} */
	this.text;
	/** @type{?string} */
	this.countdown_text;
	/** @type{?number} */
	this.end_time;
	/** @type{?string} */
	this.image;
	/** @type{?string} */
	this.preload;
	/** @type{?string} */
	this.width;
	/** @type{?string} */
	this.title;
	/** @type{?string} */
	this.url;
    }
}
