import telnetlib
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(
    app, async_mode=None, ping_interval=100, ping_timeout=100, path="/qosSocketIO"
)


class QOSThread:
    def __init__(self, interface, password, hostip):
        self.interface = interface.encode()
        self.password = password.encode()
        self.telnet = telnetlib.Telnet(hostip)

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

    def begin(self):
        self.loginToRouterAndEnable()
        self.getServicePolicies()
        self.getChildPolicies()
        self.getClassMaps()

    def run(self):
        self.begin()
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
        while True:
            self.getQos()


def main():
    interfaceName = "FastEthernet0/1.100"
    interfaceUserPwd = "cisco"
    interfaceIp = "5.5.5.2"
    thread = QOSThread(interfaceName, interfaceUserPwd, interfaceIp)
    thread.run()


@socketio.on("connect")
def connect():
    print(f"Client Connected {request.sid}")
    emit("connect_response", {"Status": 200})


@socketio.on("disconnect")
def disconnect():
    print(f"Client Disconnected {request.sid}")


if __name__ == "__main__":
    socketio.run(app)
