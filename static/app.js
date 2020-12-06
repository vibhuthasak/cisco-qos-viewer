var socket = io("http://127.0.0.1:5000/", { path: '/qosSocketIO' });

const getQOSButton = document.querySelector("#getQos")
getQOSButton.addEventListener('click', function () {
  console.log("Hello World");
  socket.emit("testPath");
})

socket.on("test_response", function (msg) {
  console.log(msg);
})