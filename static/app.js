const socket = io("http://127.0.0.1:5000/");

const charts = []

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

// QOS status listener
socket.on("qos_status", function (msg) {
  let qosValues = msg["qos_values"]
  console.log(qosValues)
  // console.log(charts)
  for (let i = 0; i < qosValues.length; i++) {
    let data1 = qosValues[i][1]
    let data2 = qosValues[i][2]
    updateChart(i, [data1 === 0 ? 0 : data1 / 1000, data2 === 0 ? 0 : data2 / 1000])
  }
  // console.log(charts)
})

function updateChart(chartObjectIndex, dataset) {
  let chartObject = Chart.instances[chartObjectIndex]
  console.log(chartObject)
  chartObject.data.datasets[0].data.push(dataset[0]);
  chartObject.data.datasets[1].data.push(dataset[1]);
  chartObject.data.labels = [...Array(chartObject.data.datasets[0].data.length).keys()]
  chartObject.update();
}

// QOS information listener
socket.on("qos_info", function (msg) {
  console.log(msg)
  let policyClasses = msg["policy_classes"]
  let middleValue = policyClasses.length / 2
  policyClasses[0] = "Total Traffic"
  policyClasses[middleValue] = "Total Traffic"

  let inputPolicy = msg["input-policy"]
  let inputChildPolicy = msg["input_child_policies"][0]
  let outputPolicy = msg["output-policy"]
  let outputChildPolicy = msg["output_child_policies"][0]
  let col1 = []
  let col2 = []
  for (let i = 0; i < policyClasses.length; i++) {
    let row = `<canvas id="chartIndex_${i}" width="500" height="300"></canvas>`
    if (i < middleValue) {
      col1.push(row)
    } else {
      col2.push(row)
    }
  }
  let joined = `
  <div style="flex:1 1 auto; display: flex;flex-direction: column; align-items:center">
    <h3 style="text-align:center; font-size:1.5rem">${inputPolicy}</h3>
    <h3 style="text-align:center;margin-top:1rem">${inputChildPolicy}</h3>
    ${col1.join(" ")}
  </div>
  <div style="flex:1 1 auto; display: flex;flex-direction: column; align-items:center">
    <h3 style="text-align:center; font-size:1.5rem">${outputPolicy}</h3>
    <h3 style="text-align:center;margin-top:1rem">${outputChildPolicy}</h3>
    ${col2.join(" ")}
  </div>
  `
  chartGrid.innerHTML += joined
  for (let i = 0; i < policyClasses.length; i++) {
    let getChartElementForPolicy = document.getElementById(`chartIndex_${i}`)
    let chartData = {
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
    let chartOptions = {
      responsive: false,
      maintainAspectRatio: true,
      title: {
        display: true,
        text: "",
        fontSize: 18,
        fontColor: "Black"
      },
      legend: {
        display: true
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
    new Chart(getChartElementForPolicy.getContext('2d'), {
      type: 'line',
      data: chartData,
      options: chartOptions
    });

    // Adding title for the chart
    Chart.instances[i].options.title.text = policyClasses[i]
  }
})
