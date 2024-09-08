//
// functions
//

function validateForm() {
  var x = document.forms["myForm"]["filename"].value;
  var y = document.forms["myForm"]["filedesc"].value;
  var input, file;
  var addString = "lower";
  var maxSize   = 150*1024*1024;
  if (x == null || x == "") {
    alert("File must be filled out");
    return false;
  }
  if (y == null || y == "") {
    alert("Please input the file description");
    return false;
  }
  if (!window.FileReader) {
    alert("The file API isn't supported on this browser yet.");
    return;
  }
  input = document.getElementById('fileinput');
  if (!input) {
    alert("Um, couldn't find the fileinput element.");
    return;
  }
  else if (!input.files) {
    alert("This browser doesn't seem to support the `files` property of file inputs.");
    return;
  }
  else if (!input.files[0]) {
    alert("p", "Please select a file before clicking 'Load'");
    return;
  }
  else {
    file = input.files[0]; console.log(file);

    document.getElementById("fileLM").value = file.lastModified;
    document.getElementById("fileLMD").value = file.lastModifiedDate;
    //filenew = document.getElementById('fileinput').files[0];
    //document.getElementById("fileLM").value = filenew.lastModifiedDate;

    if (file.size > maxSize) { 
      alert("Your file " + file.name + " is " + file.size + " bytes in size (bigger than allowed " + maxSize + " bytes).");
      return false;
    } 
  }
}

function newPopup(url) {
  popupWindow = window.open(
		url,'popUpWindow','height=400,width=600,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,directories=no,status=no,titlebar=no')
}

function closeWin() { 
  myWindow.close(); 
}

function listbox_move(listID,direction){
  var listbox=document.getElementById(listID);
  var selIndex=listbox.selectedIndex;
  if(-1==selIndex){alert("Please select an option to move.");
  return;
  }
  var increment=-1;
  if(direction=='up') increment=-1;else increment=1;
  if((selIndex+increment)<0||(selIndex+increment)>(listbox.options.length-1)){return;}
  var selValue=listbox.options[selIndex].value;var selText=listbox.options[selIndex].text;listbox.options[selIndex].value=listbox.options[selIndex+increment].value
listbox.options[selIndex].text=listbox.options[selIndex+increment].text
listbox.options[selIndex+increment].value=selValue;listbox.options[selIndex+increment].text=selText;listbox.selectedIndex=selIndex+increment;
}

function listbox_moveacross(sourceID,destID){
  var src=document.getElementById(sourceID);
  var dest=document.getElementById(destID);

  for(var count=0;count<src.options.length;count++){if(src.options[count].selected==true){var option=src.options[count];var newOption=document.createElement("option");newOption.value=option.value;newOption.text=option.text;newOption.selected=true;try{dest.add(newOption,null);src.remove(count,null);}catch(error){dest.add(newOption);src.remove(count);}
count--;}}
}

function listbox_selectall(listID,isSelect){
  var listbox=document.getElementById(listID);
  for(var count=0;count<listbox.options.length;count++)
  { listbox.options[count].selected=isSelect; }
}

function validateNotif() {
  var x = document.forms["myForm"]["valTo"].value;
  if (x == null || x == "") {
    alert("To: must be filled out");
    return false;
  } else {
    listbox_selectall('d1', true);
    listbox_selectall('d2', true);
    return true;
  }
}

function SureConfirm()
{
  if (confirm("Are you sure ?")) {
    return true;
  } else {
    return false;
  }
}
