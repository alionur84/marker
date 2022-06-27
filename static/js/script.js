// hides or displays io_form when io switch changes state
var ioform = document.getElementById("removableform");


function handleClick(){
	var pos = "İkinci Öğretim";
	var neg = "İkinci Öğretim Yok";
	var iobutton_label = document.getElementById("io_switch_label");
	var grad_but = document.getElementById("grad_switch")
	var orgun_from_label = document.getElementById("orgun_form_label");
	if(iobutton_label.innerHTML == pos){
		iobutton_label.innerHTML = neg;
		ioform.style.display = "none";


	} else if (iobutton_label.innerHTML == neg) {
		iobutton_label.innerHTML = pos;
		ioform.style.display = "block";
		grad_but.checked = false;
		orgun_from_label.innerHTML = "Örgün Şablon"


	};
};

function IoOFF(){
	var iobutton = document.getElementById("ioswitch");
	var iobutton_label = document.getElementById("io_switch_label");
	var grad_but = document.getElementById("grad_switch");
	var orgun_from_label = document.getElementById("orgun_form_label");
	var pos = "İkinci Öğretim";
	var neg = "İkinci Öğretim Yok";
	iobutton.checked = false;
	iobutton_label.innerHTML = neg;
	ioform.style.display = "none";
	orgun_from_label.innerHTML = "Lisansüstü Şablon"
	if (grad_but.checked == false){
		iobutton_label.innerHTML = pos;
		ioform.style.display = "block";
		iobutton.checked = true;
		orgun_from_label.innerHTML = "Örgün Şablon"
	};

};
