import telnetlib


class QOSThread:
    def __init__(self, interface, password, hostip):
        self.interface = interface
        self.password = password
        self.telnet = telnetlib.Telnet(hostip)

        # Send varialbles
        self.input_policy = ""
        self.output_policy = ""
        self.police_rate = ""
        self.input_policies = {}
        self.output_policies = {}
        self.input_policies_index = []
        self.output_policies_index = []

    def loginToRouter(self):
        self.telnet.read_until(b"Password:")
        self.telnet.write(self.password + b"\n")

    def getServicePolicies(self):
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

    def begin(self):
        self.loginToRouter()
        self.getServicePolicies()
        self.getPoliceRate()
        self.getServicePoliciesForInt()

    def run(self):
        self.begin()
        self.qosGenerator()


def main():
    interfaceName = "FastEthernet0/1.100"
    interfaceUserPwd = "dialog@123"
    interfaceIp = "5.5.5.5"
    thread = QOSThread(interfaceName, interfaceUserPwd, interfaceIp)
    thread.run()
