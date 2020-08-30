var neo=function(){var cookies={};var cookiesloaded=false;function getCookies(){cookiestrings=decodeURIComponent(document.cookie).split(';');for(var i=0;i<cookiestrings.length;i++){cookiestrings[i]=cookiestrings[i].trim();[key,value]=cookiestrings[i].split("=");cookies[key]=value;}
cookiesloaded=true;}
document.addEventListener("load",getCookies);function setCookie(key,val,session=true){if(!cookiesloaded){getCookies();}
cookies[key]=val;if(!session){var d=new Date();d.setTime(d.getTime()+(500*24*60*60*1000));expirestr="expires="+d.toUTCString();}
else{expirestr=""}
document.cookie=encodeURIComponent(key)+'='+encodeURIComponent(val)+';'+expirestr;}
function getCookie(key){if(!cookiesloaded){getCookies();}
return cookies[key];}
function saveCookies(){for(var c in cookies){document.cookie=encodeURIComponent(c)+'='+encodeURIComponent(cookies[c])*'';}}
function xhttpreq(url,data={},method="GET",callback=function(){},json=true){xhttp=new XMLHttpRequest();function curry(){if(this.readyState==4){callback(this);}}
xhttp.onreadystatechange=curry;xhttp.open(method,url,true);body=""
if(method=="GET"){url+="?";for(var key in data){url+=encodeURIComponent(key)+"="+encodeURIComponent(data[key])+"&";}}
else{if(json){body=JSON.stringify(data);xhttp.setRequestHeader("Content-Type","application/json");xhttp.responseType="json";}
else{for(var key in data){body+=encodeURIComponent(key)+"="+encodeURIComponent(data[key])+"&";}}}
xhttp.send(body);console.log("Sent XHTTP request to",url)}
function xhttprequest(url,data={},method="GET",json=true){var p=new Promise(resolve=>xhttpreq(url,data,method,resolve,json));return p;}
function now(){return Math.floor(Date.now()/1000);}
return{getCookie:getCookie,setCookie:setCookie,getCookies:getCookies,saveCookies:saveCookies,xhttpreq:xhttpreq,xhttprequest:xhttprequest,now:now}}();document.addEventListener('DOMContentLoaded',function(){var elements=document.getElementsByClassName("seekable");for(var i=0;i<elements.length;i++){elements[i].addEventListener("click",function(evt){var elmnt=evt.currentTarget;var percentage=evt.offsetX/elmnt.offsetWidth;percentage=Math.max(0,Math.min(100,percentage));elmnt.firstElementChild.style.width=(percentage*100)+"%";var callback=elmnt.getAttribute("data-seekcallback");window[callback](percentage);})}
var elements=document.getElementsByClassName("scrollseekable");for(var i=0;i<elements.length;i++){elements[i].addEventListener("wheel",function(evt){var elmnt=evt.currentTarget;var currentPercentage=elmnt.firstElementChild.offsetWidth/elmnt.offsetWidth;var sensitivity=elmnt.getAttribute("data-scrollsensitivity")||1;var percentage=currentPercentage-evt.deltaY*sensitivity/1000;percentage=Math.max(0,Math.min(1,percentage));elmnt.firstElementChild.style.width=(percentage*100)+"%";var callback=elmnt.getAttribute("data-seekcallback");window[callback](percentage);})}
var elements2=document.getElementsByClassName("update");var functions=[]
for(var i=0;i<elements2.length;i++){updatefunc=elements2[i].getAttribute("data-updatefrom");functions.push([elements2[i],updatefunc])}
const SMOOTH_UPDATE=true;const update_delay=SMOOTH_UPDATE?40:500;function supervisor(){for(let entry of functions){var[element,func]=entry
window[func](element);}
setTimeout(supervisor,update_delay);}
if(functions.length>0){supervisor();}
var body=document.getElementsByTagName("BODY")[0]
if(body.getAttribute("data-linkinterceptor")!=undefined){var interceptor=eval(body.getAttribute("data-linkinterceptor"));function interceptClickEvent(e){var href;var target=e.target||e.srcElement;if(target.tagName==='A'&&!target.classList.contains("no-intercept")){href=target.getAttribute('href');e.preventDefault();history.pushState({},"",href);interceptor();}}
document.addEventListener('click',interceptClickEvent);}},false);document.addEventListener('keyup',function(evt){if(evt.srcElement.tagName=="INPUT"){return;}
var elements=document.querySelectorAll('[data-hotkey]');for(let e of elements){if(e.getAttribute("data-hotkey")==evt.code){evt.preventDefault();e.onclick();break;}}},false);function dragover(evt){evt.preventDefault();}
function readImageFile(evt,crop=false){evt.preventDefault();var element=this;var file=evt.dataTransfer.files[0];var reader=new FileReader();reader.onload=(function(evt){parseImage(reader.result,element,crop);});reader.readAsArrayBuffer(file);}
function parseImage(buffer,element,crop){var binary='';var bytes=new Uint8Array(buffer);var len=bytes.byteLength;for(var i=0;i<len;i++){binary+=String.fromCharCode(bytes[i]);}
b64=window.btoa(binary);cropImage(b64,element,crop)
}
function cropImage(b64,element,crop){var img=new Image;img.src="data:image/png;base64,"+b64;img.onload=function(){if(crop){x=element.offsetWidth;y=element.offsetHeight;var canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');wid=img.width;heig=img.height;wid_resize=x/wid;heig_resize=y/heig;resize=Math.max(wid_resize,heig_resize);use_wid=x/resize;use_heig=y/resize;new_wid=wid*resize;new_heig=heig*resize;crop_left=(new_wid-x)/(2*resize);crop_top=(new_heig-y)/(2*resize);canvas.width=x;canvas.height=y;ctx.drawImage(img,crop_left,crop_top,use_wid,use_heig,0,0,x,y);done=canvas.toDataURL();}
else{var canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');canvas.width=img.width;canvas.height=img.height;ctx.drawImage(img,0,0);done=canvas.toDataURL();}
element.style.backgroundImage="url('"+done+"')";var callback=element.getAttribute("data-uploader");if(callback!=undefined){eval(callback)(done);}}}
document.addEventListener('DOMContentLoaded',function(){var elements=document.getElementsByClassName("changeable-image");for(var i=0;i<elements.length;i++){elements[i].ondragover=dragover;elements[i].ondrop=readImageFile;}})