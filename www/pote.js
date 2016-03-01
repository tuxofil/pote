// ----------------------------------------------------------------------
// Configuration variables

var base_url = '/pote';
var rest_url = base_url + '/rest/';
var refresh_period = 1; // in seconds

// ----------------------------------------------------------------------
// Internal variables. Do not touch.

var encoded_tests = "[]";
var encoded_jobs = "[]";
var encoded_finished_jobs = "[]";

// ----------------------------------------------------------------------
// Functions

/**
 * Called when user clicks on new job submission button.
 */
function addJob(){
    if(!document.getElementById("dvStatus").isOnline){
	alert('The server is offline. Try again later.');
	return;
    }
    var edUser = document.getElementById("edUser");
    var edEnvo = document.getElementById("edEnvo");
    var edTest = document.getElementById("edTest");
    // make a sanity check for input data
    if(!edUser.value){
	alert("Test owner name is not defined!");
	return;
    }
    if(!edEnvo.value){
	alert("Environment is not selected!");
	return;
    }
    if(!edTest.value){
	alert("Test set is not selected!");
	return;
    }
    // generate a request object
    var obj =
	{user: edUser.value,
	 envo: edEnvo.selectedIndex - 1,
	 test: edTest.value};
    var encoded = JSON.stringify(obj);
    // send the request
    var req = createReqObject();
    req.open("POST", rest_url + "job", false);
    req.setRequestHeader("Content-type", "application/json");
    req.send(encoded);
    if(req.status != 201){
	alert('Failed! The server says:\n\n' + req.responseText);
	return;
    }
    // clear controls
    edUser.value = '';
    edEnvo.selectedIndex = 0;
    edTest.selectedIndex = 0;
}

/**
 * Periodic task which updates the page.
 */
function updateControls(){
    var req = createReqObject();
    req.onreadystatechange = function(event){
	if(req.readyState != 4) return;
	var dvStatus = document.getElementById("dvStatus");
	var server_status = req.status == 204;
	if(dvStatus.isOnline != server_status){
	    if(server_status){
		dvStatus.innerHTML = "<span class=online>ONLINE</span>";
	    }else{
		dvStatus.innerHTML = "<span class=offline>OFFLINE</span>";
	    }
	}
	dvStatus.isOnline = server_status;
	if(dvStatus.isOnline){
	    // server is online. update rest of controls
	    updateEnvos();
	    updateTestSets();
	    updateJobList();
	    updateFinishedJobList();
	}
	// schedule next update
	setTimeout('updateControls()', refresh_period * 1000);
    };
    req.open("GET", rest_url + "ping", true);
    req.send();
}

/**
 * Updates drop down list with available environments.
 * Called from updateControls().
 */
function updateEnvos(){
    var req = createReqObject();
    req.open("GET", rest_url + "envo", false);
    req.send();
    if(req.status != 200) return;
    var edEnvo = document.getElementById("edEnvo");
    var envos = JSON.parse(req.responseText)
    if(envos.length != edEnvo.length - 1){
	// envos count has been changed.
	// TODO: make incremental update of the <select> element
	while(edEnvo.length) edEnvo.remove(0);
	edEnvo.add(document.createElement("option"));
	for(var i = 0; i < envos.length; i++){
	    var option = document.createElement("option");
	    option.text = envos[i][0];
	    option.value = envos[i][1];
	    edEnvo.add(option)
	}
    }
}

/**
 * Updates drop down list with available test sets.
 * Called from updateControls().
 */
function updateTestSets(){
    var req = createReqObject();
    req.open("GET", rest_url + "test", false);
    req.send();
    if(req.status != 200) return;
    if(encoded_tests != req.responseText){
	// test set has been changed.
	encoded_tests = req.responseText;
	tests = JSON.parse(encoded_tests);
	var edTest = document.getElementById("edTest");
	// TODO: make incremental update of the <select> element
	while(edTest.length) edTest.remove(0);
	edTest.add(document.createElement("option"));
	for(var i = 0; i < tests.length; i++){
	    var option = document.createElement("option");
	    option.text = tests[i];
	    option.value = tests[i];
	    edTest.add(option)
	}
    }
}

/**
 * Update the table with running jobs.
 * Called from updateControls().
 */
function updateJobList(){
    var req = createReqObject();
    req.open("GET", rest_url + "job", false);
    req.send();
    if(req.status != 200) return;
    if(encoded_jobs != req.responseText){
	// job list has been changed
	encoded_jobs = req.responseText;
	jobs = JSON.parse(req.responseText);
	var tbJobs = document.getElementById("tbJobs");
	// TODO: make incremental table update
	while(tbJobs.rows.length) tbJobs.deleteRow(0);
	for(var i = 0; i < jobs.length; i++){
	    var row = tbJobs.insertRow(tbJobs.rows.length);
	    row.insertCell(0).innerHTML = unixTimeToString(jobs[i].time);
	    row.insertCell(1).innerHTML = jobs[i].user;
	    row.insertCell(2).innerHTML = jobs[i].envo;
	    row.insertCell(3).innerHTML = jobs[i].test;
	    row.insertCell(4).innerHTML = formatStartStopTime(jobs[i].started);
	    row.insertCell(5).innerHTML = formatStatus(jobs[i]);
	}
    }
}

/**
 * Update the table with finished jobs.
 * Called from updateControls().
 */
function updateFinishedJobList(){
    var req = createReqObject();
    req.open("GET", rest_url + "archive", false);
    req.send();
    if(req.status != 200) return;
    if(encoded_finished_jobs != req.responseText){
	// job list has been changed
	encoded_finished_jobs = req.responseText;
	jobs = JSON.parse(req.responseText);
	var tbArchive = document.getElementById("tbArchive");
	// TODO: make incremental table update
	while(tbArchive.rows.length) tbArchive.deleteRow(0);
	for(var i = 0; i < jobs.length; i++){
	    var row = tbArchive.insertRow(tbArchive.rows.length);
	    row.className = (jobs[i].status == "done")?"succeeded":"failed";
	    row.insertCell(0).innerHTML = unixTimeToString(jobs[i].time);
	    row.insertCell(1).innerHTML = jobs[i].user;
	    row.insertCell(2).innerHTML = jobs[i].envo;
	    row.insertCell(3).innerHTML = jobs[i].test;
	    row.insertCell(4).innerHTML = formatStartStopTime(jobs[i].started);
	    row.insertCell(5).innerHTML = formatStartStopTime(jobs[i].stopped);
	    row.insertCell(6).innerHTML = formatDuration(jobs[i]);
	    row.insertCell(7).innerHTML = formatStatus(jobs[i]);
	    if(jobs[i].log){
		var url = base_url + "/log/" + jobs[i].id + "/" + jobs[i].log;
		row.insertCell(8).innerHTML =
		    "<a target='_blank' href='" + url + "'>" +
		    "<img src='" + base_url + "/utilities-terminal.png'>" +
		    "</a>";
	    }else{
		row.insertCell(8).innerHTML = "&nbsp;";
	    }
	}
    }
}

// ----------------------------------------------------------------------
// Utility functions

/**
 * Format Job status.
 */
function formatStatus(job){
    if(job.status == "failed" && job.reason)
	return job.status.toUpperCase() + "<br>" + job.reason;
    return job.status.toUpperCase()
}

/**
 * Format Job start/stop time.
 */
function formatStartStopTime(time){
    return (time)?unixTimeToString(time):"&nbsp;";
}

/**
 * Format Job run duration.
 */
function formatDuration(job){
    var formatted = "";
    if(job.stopped && job.started){
	var duration = Math.round(job.stopped - job.started);
	var factors = [[3600, "h"],
		       [60, "m"],
		       [1, "s"]];
	for(var i = 0; i < factors.length; i++){
	    var factor = factors[i][0];
	    var suffix = factors[i][1];
	    var count = Math.floor(duration / factor)
	    if(count){
		duration -= count * factor;
		formatted += String(count) + suffix;
	    }
	}
	return (formatted)?formatted:"~0s";
    }
    return "&nbsp;"
}

/**
 * Convert Unix timestamp to local date and time, using
 * current browser locale.
 */
function unixTimeToString(seconds){
    var dt = new Date(seconds * 1000);
    return dt.toLocaleDateString() + " " + dt.toLocaleTimeString();
}

/**
 * Create AJAX request object.
 */
function createReqObject(){
    if(window.XMLHttpRequest){
	return new XMLHttpRequest();
    }else{
	// Internet Explorer
	return new ActiveXObject("Microsoft.XMLHTTP");
    }
}
