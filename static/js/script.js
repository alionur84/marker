// hides or displays io_form when io switch changes state
var ioform = document.getElementById("removableform");


function handleClick(){
	var pos = "İkinci Öğretim";
	var neg = "İkinci Öğretim Yok";
	var iobutton = document.getElementById("io_switch_label");
	if(iobutton.innerHTML == pos){
		iobutton.innerHTML = neg;
		ioform.style.display = "none";

	} else if (iobutton.innerHTML == neg) {
		iobutton.innerHTML = pos;
		ioform.style.display = "block";
	};
};


