function click_send(page){
	// var competition = document.getElementByName('competition').value;
	var competitions = document.getElementsByName('competition');
	var competition ='none';
	for (i in competitions){
		if (competitions[i].checked){
			competition = competitions[i].value
			break;
		}
	}
	if (competition == 'none'){
		alert('please choose a competition');
	}
	else{
		parent.location = page + '?competition=' + competition;
	}
}

function maybe_submit(check){
	var form = document.getElementById('table_form');
	if (check == 'False') form.submit(); 
	else{
		var fence = document.getElementById('fence').value;
		if (fence == 'none') alert('please choose a fence');
		else form.submit();
	}
}

var t = 5;
var stopper;

// if (parent.location.pathname.indexOf('submit') != -1){
	// document.addEventListener('DOMContentLoaded', redirect_slow);
// }

function redirect_slow(){
	redirect_write();
	stopper = setInterval(redirect_write, 1000);
}

function redirect_write(){
	if (t <= 0){
		clearInterval(stopper);
		parent.location = '/';
		return;
	}
	else{
		document.getElementById('redirect_msg').innerHTML = 'Redirecting to home in ' + t + '.';
		t -= 1;
	}
}

function stop(){
	clearInterval(stopper);
	document.getElementById('redirect_msg').innerHTML = '';
}