var socket = io("http://127.0.0.1:5000/");

const getQOSButton = document.querySelector("#getQos")
getQOSButton.addEventListener('click', function () {
  console.log("Hello World");
  socket.emit("testPath");
})

socket.on("test_response", function (msg) {
  console.log(msg);
})

socket.on("connect_response", function (msg) {
  console.log(msg);
})