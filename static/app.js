var socket = io("http://127.0.0.1:5000/");

const getQOSButton = document.querySelector("#getQos")
getQOSButton.addEventListener('click', function () {
  console.log("Hello World");
  socket.emit("getQOS");
})

socket.on("test_response", function (msg) {
  console.log(msg);
})

socket.on("connect_response", function (msg) {
  console.log(msg);
})

socket.on("qos_status", function (msg) {
  console.log(msg);
})

socket.on("qos_info", function (msg) {
  console.log(msg);
})
