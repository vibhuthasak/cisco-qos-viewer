const socket = io();

const charts = []

const getQOSButton = document.querySelector("#getQos")
const getQOSLabel = document.querySelector("#getQosLabel")
const bandwidthButton = document.querySelector("#allowBandWidth")
const chartGrid = document.querySelector("#chart-grid")
const informationContainer = document.querySelector(".information-container")

const interfaceName = document.querySelector("#iname")
const interfaceIp = document.querySelector("#iip")
const interfacePwd = document.querySelector("#ipassword")

getQOSButton.addEventListener('click', function () {
  let allowBandwidth = bandwidthButton.checked
  let qosValues = {
    interfaceName: interfaceName.value,
    interfaceIp: interfaceIp.value,
    interfacePwd: interfacePwd.value,
    allowBandwidth: allowBandwidth
  }
  if (getQOSButton.checked) {
    chartGrid.innerHTML = ""
    socket.emit("getQOS", qosValues);
    getQOSLabel.innerText = "Stop QOS"
  } else {
    console.log("Stop QOS")
    socket.emit("stopQOS");
    getQOSLabel.innerText = "Start QOS"
  }
})

function timeout(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

socket.on("restart_qos", async function () {
  clearChartInstances()
  let allowBandwidth = bandwidthButton.checked
  let qosValues = {
    interfaceName: interfaceName.value,
    interfaceIp: interfaceIp.value,
    interfacePwd: interfacePwd.value,
    allowBandwidth: allowBandwidth
  }
  await timeout(5000);
  socket.emit("getQOS", qosValues);
  getQOSLabel.innerText = "Stop QOS"
})

socket.on("test_response", function (msg) {
  console.log(msg);
})

socket.on("connect_response", function (msg) {
  console.log(msg);
})

function clearChartInstances() {
  let chartInstanceList = Object.values(Chart.instances)
  chartInstanceList.forEach(chartInstance => {
    chartInstance.destroy()
  })
}

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
  let chartObject = Object.values(Chart.instances)[chartObjectIndex]
  let maxBandwidth = chartObject.data.datasets[2].data[0]
  chartObject.data.datasets[0].data.push(dataset[0]);
  chartObject.data.datasets[1].data.push(dataset[1]);
  chartObject.data.datasets[2].data.push(maxBandwidth);
  chartObject.data.labels = [...Array(chartObject.data.datasets[0].data.length).keys()]
  chartObject.update();
}

// QOS information listener
socket.on("qos_info", function (msg) {
  console.log(msg)
  chartGrid.innerHTML = ""
  let policyClasses = msg["policy_classes"]
  let middleValue = policyClasses.length / 2
  policyClasses[0][0] = "Total Traffic"
  policyClasses[middleValue][0] = "Total Traffic"

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
    let maxBandWidth = policyClasses[i][1]
    let chartData = {
      labels: [],
      datasets: [{
        label: "Matched",
        borderColor: 'rgb(0, 255, 0)',
        fill: false,
        data: [],
      }, {
        label: "Dropped",
        borderColor: 'rgb(255, 0, 0)',
        fill: false,
        data: [],
      }, {
        label: "Max",
        borderColor: 'rgb(0, 0, 255)',
        fill: false,
        data: [maxBandWidth == 0 ? 0 : maxBandWidth / 1000],
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
    console.log(Chart.instances)
    // Adding title for the chart
    Object.values(Chart.instances)[i].options.title.text = policyClasses[i][0]
  }
})

socket.on("error_info", function (msg) {
  alert(msg["description"])
})

socket.on("notification", function (msg) {
  informationContainer.appendChild(createNotificationNodeFromHtml((msg["description"])))
})

function createNotificationNodeFromHtml(innerText) {
  let h3 = document.createElement("h3");
  h3.innerText = innerText;
  h3.classList.add("notification-msg")
  return h3
}