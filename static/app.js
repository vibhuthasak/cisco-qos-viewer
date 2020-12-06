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

const charts = []
const qosValuesRoot = []

const getQOSButton = document.querySelector("#getQos")
const chartGrid = document.querySelector("#chart-grid")

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

// QOS status listner
socket.on("qos_status", function (msg) {
  let qosValues = msg["qos_values"]
  console.log(qosValues)
  for (let i = 0; i < qosValues.length; i++) {
    updateChart(i, [qosValues[i][1], qosValues[i][2]])
  }
})

function updateChart(chartObjectIndex, dataset) {
  let chartObject = charts[chartObjectIndex]
  console.log(chartObject.data.datasets[0].data)
  try {
    chartObject.data.datasets[0].data.push(dataset[0]);
    chartObject.data.datasets[1].data.push(dataset[1]);
    chartObject.data.labels = [...Array(chartObject.data.datasets[0].data.length).keys()]
    chartObject.update();
  } catch (e) {
    console.log(e)
  }
}

// QOS information listener
socket.on("qos_info", function (msg) {
  console.log(msg)
  let policyClasses = msg["policy_classes"]
  let middleValue = policyClasses.length / 2
  let col1 = []
  let col2 = []
  for (let i = 0; i < policyClasses.length; i++) {
    let row = `<canvas id="chartIndex_${i}" width="500" height="300"></canvas>`
    if (i < middleValue) {
      col1.push(row)
    } else {
      col2.push(row)
    }
    // chartGrid.innerHTML += row
  }
  let joined = `
  <div>
    ${col1.join(" ")}
  </div>
  <div style="margin-left:5rem">
    ${col2.join(" ")}
  </div>
  `
  chartGrid.innerHTML += joined
  for (let i = 0; i < policyClasses.length; i++) {
    let getChartElementForPolicy = document.getElementById(`chartIndex_${i}`)
    charts.push(new Chart(getChartElementForPolicy.getContext('2d'), {
      type: 'line',
      data: chartData,
      options: chartOptions
    }));

    // Adding title for the chart
    charts[i].options.title.text = policyClasses[i]
  }
})
