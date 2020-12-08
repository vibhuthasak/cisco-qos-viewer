import telnetlib
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sys

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")


class QOSThread:
    def __init__(self, interface, password, hostip):
        self.interface = interface.encode()
        self.password = password.encode()
        self.telnet = telnetlib.Telnet(hostip)
        self.isRun = True

        # Send varialbles
        self.input_policy = ""
        self.output_policy = ""
        self.police_rate = ""
        self.input_child_policies = []
        self.output_child_policies = []
        self.policy_classes = []

    def loginToRouterAndEnable(self):
        self.telnet.read_until(b"Password:")
        self.telnet.write(self.password + b"\n")
        self.telnet.read_until(b">")
        self.telnet.write(b"en\n")
        self.telnet.read_until(b"Password:")
        self.telnet.write(self.password + b"\n")
        self.telnet.read_until(b"#", timeout=1)

    def getServicePolicies(self):
        self.telnet.write(
            b"sh policy-map interface "
            + self.interface
            + b" | include output:|input: \n"
        )
        service_policy = self.telnet.read_until(b"#").decode("utf-8")
        for l1 in service_policy.splitlines():
            if "Service-policy input:" in l1:
                self.input_policy = l1.split()[-1]
            if "Service-policy output:" in l1:
                self.output_policy = l1.split()[-1]
                break

    def getChildPolicies(self):
        self.telnet.read_until(b"#", timeout=1)
        self.telnet.write(
            b"sh policy-map interface "
            + self.interface
            + b" | include Service-policy \n"
        )
        service_policy = self.telnet.read_until(b"#").decode("utf-8")
        atInput = True
        for line in service_policy.splitlines():
            finalElement = line.split()[-1]
            if finalElement == self.output_policy:
                atInput = False
            if (
                (atInput)
                and ("Service-policy" in line)
                and (finalElement != self.input_policy)
            ):
                self.input_child_policies.append(finalElement)
            if (
                (not atInput)
                and ("Service-policy" in line)
                and (finalElement != self.output_policy)
            ):
                self.output_child_policies.append(finalElement)

    def getClassMaps(self):
        self.telnet.read_until(b"#", timeout=1)
        self.telnet.write(
            b"sh policy-map interface "
            + self.interface
            + b" | include Class-map"
            + b"\n"
        )
        class_maps = self.telnet.read_until(b"#").decode("utf-8")
        class_maps_list = []
        for line in class_maps.splitlines():
            if "Class-map:" in line:
                secondElement = line.strip().split()[-2]
                class_maps_list.append(secondElement)
        self.policy_classes = class_maps_list

    def getBandwidthPercentage(self):
        self.telnet.read_until(b"#", timeout=1)
        self.telnet.write(
            b"sh policy-map interface " + self.interface + b" | include burst" + b"\n"
        )
        police_rates = self.telnet.read_until(b"#").decode("utf-8")
        police_list = []
        for line in police_rates.splitlines():
            if "rate" in line:
                secondElement = line.strip().split()[1]
                police_list.append(secondElement)
        policies_with_police = list(zip(self.policy_classes, police_list)) * 2
        print(policies_with_police)
        self.policy_classes = policies_with_police

    def getQos(self):
        self.telnet.read_until(b"#", timeout=1)
        self.telnet.write(
            b"sh policy-map interface "
            + self.interface
            + b" | include 30 second offered rate"
            + b"\n"
        )
        offered_rates = self.telnet.read_until(b"#").decode("utf-8")
        offer_rate_list = []
        for line in offered_rates.splitlines():
            if "30 second offered rate" in line:
                offerrate = [int(s) for s in line.split() if s.isdigit()]
                offer_rate_list.append(offerrate)
        print(offer_rate_list)
        emit("qos_status", {"qos_values": offer_rate_list})
        socketio.sleep(8)

    def increaseBandWidth(self):
        emit("notification", {"description": "Increasing Bandwidth process started"})
        self.telnet.read_until(b"#", timeout=3)
        configurationText = generateBandwidthIncreaseText(
            self.input_policy, self.output_policy, self.interface
        )
        self.telnet.write(configurationText.encode)

    def begin(self):
        self.loginToRouterAndEnable()
        self.getServicePolicies()
        self.getChildPolicies()
        self.getClassMaps()
        self.getBandwidthPercentage()

    def run(self):
        self.isRun = True
        self.begin()
        emit("notification", {"description": "Getting Service Policies"})
        print("Input Policy:")
        print(self.input_policy)
        print("Output Policy:")
        print(self.output_policy)
        print("input_child_policies:")
        print(self.input_child_policies)
        print("output_child_policies:")
        print(self.output_child_policies)
        print("policy_classes:")
        print(self.policy_classes)
        emit(
            "qos_info",
            {
                "input-policy": self.input_policy,
                "output-policy": self.output_policy,
                "input_child_policies": self.input_child_policies,
                "output_child_policies": self.output_child_policies,
                "policy_classes": self.policy_classes,
            },
        )
        emit("notification", {"description": "Generating QOS"})
        while True:
            if self.isRun:
                self.getQos()
            else:
                print("Stopping QOS")
                break

    def stop(self):
        self.isRun = False


@socketio.on("getQOS")
def main(msg):
    print(msg)
    if (
        (len(msg["interfaceName"]) < 1)
        or (len(msg["interfaceIp"]) < 1)
        or (len(msg["interfacePwd"]) < 1)
    ):
        emit("error_info", {"status": 400, "description": "Bad Request"})
    else:
        try:
            interfaceName = msg["interfaceName"]
            interfaceUserPwd = msg["interfacePwd"]
            interfaceIp = msg["interfaceIp"]
            print(interfaceName, interfaceUserPwd, interfaceIp)
            thread = QOSThread(interfaceName, interfaceUserPwd, interfaceIp)
            thread.run()
        except:
            emit("error_info", {"status": 500, "description": sys.exc_info()[0]})


@socketio.on("connect")
def connect():
    print(f"Client Connected {request.sid}")
    emit("connect_response", {"Status": 200})
    emit("notification", {"description": "Connected to server"})


@socketio.on("disconnect")
def disconnect():
    print(f"Client Disconnected {request.sid}")


@socketio.on("testPath")
def testPath():
    print(f"Got test event")
    emit("test_response", {"Status": 200})


@app.route("/")
def hello():
    return render_template("index.html")


def matchLists(list1, list2):
    lengthList1 = len(list1)
    lengthList2 = len(list2)
    for _ in range(lengthList1 // 2 - lengthList2):
        list2.append("0")
    return list2


def generateBandwidthIncreaseText(oldInputPolicy, oldOutputPolicy, interfaceName):
    oldBandwidth = int(oldInputPolicy[0])
    newBandwidth = oldBandwidth + 1
    newInputPolicy = substituteCharFromList(oldInputPolicy, 0, newBandwidth)
    newOutputPolicy = substituteCharFromList(oldOutputPolicy, 0, newBandwidth)
    newConfiguration = f"""
end \n
configure terminal \n
interface {interfaceName} \n
no service-policy input {oldInputPolicy} \n
no service-policy output {oldOutputPolicy} \n
service-policy input {newInputPolicy} \n
service-policy output {newOutputPolicy} \n
end \n"""
    print(newConfiguration)
    return newConfiguration


def substituteCharFromList(string, index, subChar):
    stringList = list(string)
    stringList[index] = subChar
    return "".join(stringList)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
    socketio.run(app)
