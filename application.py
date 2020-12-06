from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from multiprocessing import Process
import telnetlib

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(
    app, async_mode=None, ping_interval=100, ping_timeout=100, path="/qosSocketIO"
)


class QOSThread:
    def __init__(self, interface, userName, password):
        # super(QOSThread, self).__init__()
        self.interface = interface.encode()
        self.userName = userName.encode()
        self.password = password.encode()
        self.telnet = telnetlib.Telnet("localhost")
        # self.telnet.set_debuglevel(2)

        # Send varialbles
        self.input_policy = ""
        self.output_policy = ""
        self.police_rate = ""
        self.input_policies = {}
        self.output_policies = {}
        self.input_policies_index = []
        self.output_policies_index = []

        self.stringInterface = interface

    def loginToBe(self):
        emit(
            "qos_status", {"Status": 200, "Info": f"Logging to {self.stringInterface}"}
        )
        self.telnet.read_until(b"Username:")
        self.telnet.write(self.userName + b"\n")
        self.telnet.read_until(b"Password:")
        self.telnet.write(self.password + b"\n")

    def getServicePolicy(self):
        emit("qos_status", {"Status": 200, "Info": f"Logged to {self.stringInterface}"})
        emit(
            "qos_status",
            {
                "Status": 200,
                "Info": f"Getting Service Policies from {self.stringInterface}",
            },
        )
        self.telnet.write(b"sh run int " + self.interface + b"\n")
        service_policy = self.telnet.read_until(b"!").decode("utf-8")
        for l1 in service_policy.splitlines():
            if "service-policy input" in l1:
                self.input_policy = l1.split()[-1]
            if "service-policy output" in l1:
                self.output_policy = l1.split()[-1]
                break

    def getPoliceRate(self):
        self.telnet.write(b"sh run policy-map " + self.input_policy.encode() + b"\n")
        self.telnet.read_until(b"#")
        bps = self.telnet.read_until(b"#").decode("utf-8")
        for l2 in bps.splitlines():
            if "police rate" in l2:
                self.police_rate = l2.split()[2]
                break

    def getServicePoliciesForInt(self):
        self.input_policies[self.input_policy] = []
        self.output_policies[self.output_policy] = []
        self.input_policies_index.append(self.input_policy)
        self.output_policies_index.append(self.output_policy)

        output_policy_found = False
        self.telnet.write(
            b"sh policy-map int "
            + self.interface
            + b' | include "Policy|input|output" '
            + b"\n"
        )
        policies = self.telnet.read_until(b"#").decode("utf-8")

        for l3 in policies.splitlines():
            l3split = l3.split()
            if "output:" in l3split:
                output_policy_found = True

            if "Policy" in l3split:
                if output_policy_found:
                    self.output_policies[" ".join(l3split[1:])] = []
                    self.output_policies_index.append(" ".join(l3split[1:]))
                else:
                    self.input_policies[" ".join(l3split[1:])] = []
                    self.input_policies_index.append(" ".join(l3split[1:]))

    def qosGenerator(self):
        emit(
            "qos_status",
            {"Status": 200, "Info": f"Getting QOS from {self.stringInterface}"},
        )
        total_policies_index = self.input_policies_index + self.output_policies_index
        output_list = []
        output_list.append(self.police_rate)
        for index in range(20):
            matched_count = 0
            del output_list[1:]
            self.telnet.write(
                b"sh policy-map int "
                + self.interface
                + b' | include  "Matched|Total Dropped|output" '
                + b"\n"
            )
            output_policy_found_1 = False
            matchedRate = self.telnet.read_until(b"#").decode("utf-8")

            for l4 in matchedRate.splitlines():
                l4split = l4.split()
                if "output:" in l4split:
                    output_policy_found_1 = True

                if "Matched" in l4split:
                    value = l4split[-1]
                    if output_policy_found_1:
                        self.output_policies[
                            total_policies_index[matched_count]
                        ].append([value])
                    else:
                        self.input_policies[total_policies_index[matched_count]].append(
                            [value]
                        )
                    # matched_count += 1
                if "Dropped" in l4split:
                    dropvalue = l4split[-1]
                    if output_policy_found_1:
                        self.output_policies[total_policies_index[matched_count]][
                            index
                        ].append(dropvalue)
                    else:
                        self.input_policies[total_policies_index[matched_count]][
                            index
                        ].append(dropvalue)
                    matched_count += 1
            output_list.append(self.input_policies)
            output_list.append(self.output_policies)
            print(output_list)
            emit("qos_out_response", output_list)
            socketio.sleep(2)

    def begin(self):
        self.loginToBe()
        self.getServicePolicy()
        self.getPoliceRate()
        self.getServicePoliciesForInt()

    def run(self):
        self.begin()
        try:
            self.qosGenerator()
        except ConnectionResetError:
            emit("qos_status", {"Status": 400, "Info": "ConnectionReset"})
        except EOFError:
            emit("qos_status", {"Status": 400, "Info": "Telnet connection closed"})
        except Exception as error:
            emit("qos_status", {"Status": 400, "Info": error})

@socketio.on("generate_qos")
def qosGenerator(message):
    print("Starting QOS Thread")
    interfaceName = message["interfaceName"].strip()
    interfaceUserName = message["userName"].strip()
    interfaceUserPwd = message["password"].strip()
    if len(interfaceName) < 3 || len(interfaceName) < 3 || len(interfaceUserPwd) < 3:
        emit("open_tunnel_response", {"Status": 400, "Info": "Invalid Parameter"})
    else:
        thread = QOSThread(interfaceName, interfaceUserName, interfaceUserPwd)
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