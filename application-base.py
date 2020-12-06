import telnetlib


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

    # def getPoliceRate(self):
    #     self.telnet.write(b"sh run policy-map " + self.input_policy.encode() + b"\n")
    #     self.telnet.read_until(b"#")
    #     bps = self.telnet.read_until(b"#").decode("utf-8")
    #     for l2 in bps.splitlines():
    #         if "police rate" in l2:
    #             self.police_rate = l2.split()[2]
    #             break

    # def getServicePoliciesForInt(self):
    #     self.input_policies[self.input_policy] = []
    #     self.output_policies[self.output_policy] = []
    #     self.input_policies_index.append(self.input_policy)
    #     self.output_policies_index.append(self.output_policy)

    #     output_policy_found = False
    #     self.telnet.write(
    #         b"sh policy-map int "
    #         + self.interface
    #         + b' | include "Policy|input|output" '
    #         + b"\n"
    #     )
    #     policies = self.telnet.read_until(b"#").decode("utf-8")

    #     for l3 in policies.splitlines():
    #         l3split = l3.split()
    #         if "output:" in l3split:
    #             output_policy_found = True

    #         if "Policy" in l3split:
    #             if output_policy_found:
    #                 self.output_policies[" ".join(l3split[1:])] = []
    #                 self.output_policies_index.append(" ".join(l3split[1:]))
    #             else:
    #                 self.input_policies[" ".join(l3split[1:])] = []
    #                 self.input_policies_index.append(" ".join(l3split[1:]))

    # def qosGenerator(self):
    #     total_policies_index = self.input_policies_index + self.output_policies_index
    #     output_list = []
    #     output_list.append(self.police_rate)
    #     for index in range(20):
    #         matched_count = 0
    #         del output_list[1:]
    #         self.telnet.write(
    #             b"sh policy-map int "
    #             + self.interface
    #             + b' | include  "Matched|Total Dropped|output" '
    #             + b"\n"
    #         )
    #         output_policy_found_1 = False
    #         matchedRate = self.telnet.read_until(b"#").decode("utf-8")

    #         for l4 in matchedRate.splitlines():
    #             l4split = l4.split()
    #             if "output:" in l4split:
    #                 output_policy_found_1 = True

    #             if "Matched" in l4split:
    #                 value = l4split[-1]
    #                 if output_policy_found_1:
    #                     self.output_policies[
    #                         total_policies_index[matched_count]
    #                     ].append([value])
    #                 else:
    #                     self.input_policies[total_policies_index[matched_count]].append(
    #                         [value]
    #                     )
    #                 # matched_count += 1
    #             if "Dropped" in l4split:
    #                 dropvalue = l4split[-1]
    #                 if output_policy_found_1:
    #                     self.output_policies[total_policies_index[matched_count]][
    #                         index
    #                     ].append(dropvalue)
    #                 else:
    #                     self.input_policies[total_policies_index[matched_count]][
    #                         index
    #                     ].append(dropvalue)
    #                 matched_count += 1
    #         output_list.append(self.input_policies)
    #         output_list.append(self.output_policies)
    #         print(output_list)

    def begin(self):
        self.loginToRouterAndEnable()
        self.getServicePolicies()
        self.getChildPolicies()
        self.getClassMaps()

    def run(self):
        self.begin()
        print(self.input_policy)
        print(self.output_policy)
        print(self.police_rate)
        print(self.input_child_policies)
        print(self.output_child_policies)
        print(self.policy_classes)


def main():
    interfaceName = "FastEthernet0/1.100"
    interfaceUserPwd = "dialog@123"
    interfaceIp = "5.5.5.5"
    thread = QOSThread(interfaceName, interfaceUserPwd, interfaceIp)
    thread.run()
