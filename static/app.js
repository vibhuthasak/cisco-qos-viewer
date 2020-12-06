var socket = io("http://127.0.0.1:5000/");

const chartOptions = {
  responsive: false,
  maintainAspectRatio: true,
  title: {
    display: true,
    text: "",
    fontSize: 18,
    fontColor: "Black"
  },
  legand: {
    display: false
  },
  scales: {
    yAxes: [{
      ticks: {
        beginAtZero: true,
      },
      gridLines: {
        color: "black",
        borderDash: [2, 5],
      },
      scaleLabel: {
        display: true,
        labelString: "kbps",
        fontColor: "black"
      }
    }]
  },
  tooltips: {
    enabled: false
  }
}

const chartData = {
  labels: [],
  datasets: [{
    label: "Matched",
    borderColor: 'rgb(0, 0, 255)',
    fill: false,
    data: [],
  }, {
    label: "Dropped",
    borderColor: 'rgb(255, 0, 0)',
    fill: false,
    data: [],
  }]
}

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
