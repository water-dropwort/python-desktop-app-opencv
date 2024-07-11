const canvas = document.getElementById('imgviewer-canvas');
const ctx = canvas.getContext('2d');
const ws = new WebSocket('ws://localhost:8080');
const img = new Image();
const startbtn = document.getElementById('controller-startbtn');
const stopbtn = document.getElementById('controller-stopbtn');

ws.onopen = function() {
    console.log('WebSocket connection opened');
};

ws.onmessage = function(event) {
    const imageData = event.data;
    img.src = 'data:image/jpeg;base64,' + imageData;

    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function() {
    console.log('WebSocket connection closed');
};

startbtn.onclick = function() {
    ws.send("start");
    console.log("startbtn clicked");
};

stopbtn.onclick = function() {
    ws.send("stop");
    console.log("stopbtn clicked");
};
