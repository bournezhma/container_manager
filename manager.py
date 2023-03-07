#!/usr/bin/python3

import configparser
import subprocess
import atexit
import sys
import readline
import os
import time
import threading
import queue


readline.parse_and_bind('tab: complete')
def complete(text, state):
    options = ["deploy", "migrate", "show", "remove", "exit", "help"]
    matches = [opt for opt in options if opt.startswith(text)]
    if state < len(matches):
        return matches[state]
    else:
        return None
readline.set_completer(complete)


readline.parse_and_bind('"\e[A": history-search-backward')
readline.parse_and_bind('"\e[B": history-search-forward')
HISTORY_PATH = ".command_history"
readline.read_history_file(HISTORY_PATH)
def add_history(line):
    readline.add_history(line)
def save_history():
    readline.write_history_file(HISTORY_PATH)

atexit.register(save_history)


def cleanup():
    message_queue.insert_message("exit")
    command_remove("node", "all", 1)
    print("Bye.")


class EventList:
    def __init__(self):
        self.strings = []

    def insert(self, new_string):
        self.strings.append(new_string)

    def print_all(self):
        for string in self.strings:
            print(string)
    
    def clear(self):
        self.strings = []

event_list = EventList()

class ContainerArray:
    def __init__(self):
        self.data = []
    
    def insert(self, name, priority):
        self.data.append({'name': name, 'priority': priority})
    
    def find(self, name):
        for item in self.data:
            if item['name'] == name:
                return 1
        return 0
    
    def delete(self, name):
        for item in self.data:
            if item['name'] == name:
                self.data.remove(item)
                return 1
        return 0
    
    def clear(self):
        self.data = []
    
    def print_name(self):
        names = [item['name'] for item in self.data]
        return ' '.join(names)
    
    def get_priority_by_name(self, name):
        for item in self.data:
            if item['name'] == name:
                return item['priority']
        return None
    
    def update_priority_by_name(self, name, new_priority):
        for item in self.data:
            if item['name'] == name:
                item['priority'] = new_priority
                return 1
        return 0
    
array_node1 = ContainerArray()
array_node2 = ContainerArray()

def run_command_no_echo(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_command_return(cmd):
    return subprocess.check_output(cmd, shell=True)


def run_command(cmd):
    subprocess.run(cmd, shell=True)


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")

    connection = config["connection"]
    network = config["network"]
    priority = config["priority"]
    image = config["image"]

    remote_host = connection.get("remote_host")
    remote_user = connection.get("remote_user")
    local_interface = network.get("local_interface")
    remote_interface = network.get("remote_interface")
    throughput_low = network.get("throughput_low")
    throughput_medium = network.get("throughput_medium")
    throughput_high = network.get("throughput_high")
    cal_period = network.get("cal_period")
    priority_cpu_low = priority.get("priority_cpu_low")
    priority_mem_low = priority.get("priority_mem_low")
    priority_cpu_medium = priority.get("priority_cpu_medium")
    priority_mem_medium = priority.get("priority_mem_medium")
    priority_cpu_high = priority.get("priority_cpu_high")
    priority_mem_high = priority.get("priority_mem_high")
    image = image.get("image")

    return {"remote_host": remote_host, "remote_user": remote_user, "local_interface": local_interface, "remote_interface": remote_interface, \
            "priority_cpu_low": priority_cpu_low, "priority_mem_low": priority_mem_low, "priority_cpu_medium": priority_cpu_medium, \
            "priority_mem_medium": priority_mem_medium, "priority_cpu_high": priority_cpu_high, "priority_mem_high": priority_mem_high, \
            "image": image, "cal_period": cal_period, "throughput_low": throughput_low, "throughput_medium": throughput_medium, "throughput_high": throughput_high}


def get_input():
    while True:
        user_input = input("\n>>> ")
        
        if user_input == "deploy --auto":
            return {"command": "deploy_auto"}
        
        elif user_input.startswith("deploy"):
            args = user_input.split()
            if len(args) == 4:
                priority = args[1]
                node = args[2]
                name = args[3]
                if priority in ["low", "medium", "high"] and node in ["1", "2"] and name:
                    return {"command": "deploy", "priority": priority, "node": node, "name": name}
            print("Wrong command. Using 'deploy low/medium/high 1/2 xxx' or 'deploy --auto'")
            print("See '?' or 'help'")
        
        elif user_input.startswith("migrate"):
            args = user_input.split()
            if len(args) == 4:
                src = args[1]
                dst = args[2]
                name = args[3]
                if src in ["1", "2"] and dst in ["1", "2"] and name:
                    return {"command": "migrate", "src": src, "dst": dst, "name": name}
            print("Wrong command. Using 'migrate 1/2 1/2 xxx'")
            print("See '?' or 'help'")

        elif user_input.startswith("show"):
            content = user_input.split()[1]
            if content in ["deployment", "priority"]:
                return {"command": "show", "content": content}
            print("Wrong command. Using 'show deployment/priority'")
            print("See '?' or 'help'")
            
        elif user_input.startswith("remove"):
            args = user_input.split()
            scope = args[1]
            name = args[2]
            if scope in ["node", "container"]:
                return {"command": "remove", "scope": scope, "name": name}
            print("Wrong command. Using 'remove node 1/2/all' or 'remove container xxx'")
            print("See '?' or 'help'")
            
        elif user_input == "exit" or user_input == "quit":
            message_queue.insert_message("exit")
            sys.exit(0)
            
        elif user_input == "help" or user_input == "?":
            print_help()
            
        elif user_input == "test":
            return {"command": "test"}
            
        else:
            print("'{}' is not a command.".format(user_input))
            print("See '?' or 'help'")
        return -1

def print_welcome():
    print("Welcome to the manager CLI.")
    print("Type \"?\" or \"help\" to get information about how to use this CLI.")

def print_help():
    print("To deploy a container on one node with priority or update priority:")
    print("     deploy PRIORITY(low/medium/high) NODE(1/2) NAME")
    print("     e.g., deploy low 1 container_name")
    print("To start automated deployment based on network conditions:")
    print("     deploy --auto")
    print("To migrate a container:")
    print("     migrate SRC(1/2) DST(1/2) NAME")
    print("     e.g., migrate 1 2 container_name")
    print("To list the deployment:")
    print("     show deployment")
    print("To list the priority:")
    print("     show priority")
    print("To remove all containers on a node:")
    print("     remove node NODE(1/2)")
    print("     e.g., remove node 1")
    print("To remove a container with name:")
    print("     remove container NAME")
    print("     e.g., remove container container_name")        
    print("To exit and clean up all containers:")
    print("     exit/quit")
    print("To show this information:")
    print("     help/?")    
    
def check_existence(name):
    ret = 0
    if array_node1.find(name) == 1:
        ret = 1
    elif array_node2.find(name) == 1:
        ret = 2
    return ret

def command_deploy(priority, node, name, PRINT):
    
    ret = check_existence(name)
    
    if priority == "low":
        priority_cpu = priority_cpu_low
        priority_mem = priority_mem_low
    elif priority == "medium":
        priority_cpu = priority_cpu_medium
        priority_mem = priority_mem_medium
    elif priority == "high":
        priority_cpu = priority_cpu_high
        priority_mem = priority_mem_high
        
    if node == "1":
        if ret == 1:
            if array_node1.get_priority_by_name(name) == priority:
                if PRINT == 1:
                    print("Container [{}] already exists on node [1], and priority [{}] keep unchanged.".format(name, priority))
            else:
                local_command = f"docker update --cpu-shares {priority_cpu} --memory {priority_mem} {name}"
                run_command_no_echo(local_command)
                if PRINT == 1:
                    print("Container [{}] already exists on node [1], but priority is changed from [{}] to [{}].".format(name, array_node1.get_priority_by_name(name), priority))
                array_node1.update_priority_by_name(name, priority)
        elif ret == 2:
            print("Container [{}] already exists on node [2] with priority [{}].".format(name, array_node2.get_priority_by_name(name)))
        elif ret == 0:
            local_command = f"docker run -itd --network host --name {name} --cpu-shares {priority_cpu} --memory {priority_mem} {image}"
            run_command_no_echo(local_command)
            array_node1.insert(name, priority)
            if PRINT == 1:
                print("Container [{}] has been created on node [1] with priority [{}].".format(name, priority))
    elif node == "2":
        if ret == 2:
            if array_node2.get_priority_by_name(name) == priority:
                if PRINT == 1:
                    print("Container [{}] already exists on node [2], and priority [{}] keep unchanged.".format(name, priority))
            else:
                remote_command = f"ssh {remote_user}@{remote_host} docker update --cpu-shares {priority_cpu} --memory {priority_mem} {name}"
                run_command_no_echo(remote_command)
                if PRINT == 1:
                    print("Container [{}] already exists on node [2], but priority is changed from [{}] to [{}].".format(name, array_node2.get_priority_by_name(name), priority))
                array_node2.update_priority_by_name(name, priority)
        elif ret == 1:
            if PRINT == 1:
                print("Container [{}] already exists on node [1] with priority [{}].".format(name, array_node1.get_priority_by_name(name)))
        elif ret == 0:
            remote_command = f"ssh {remote_user}@{remote_host} docker run -itd --network host --name {name} --cpu-shares {priority_cpu} --memory {priority_mem} {image}" 
            run_command_no_echo(remote_command)
            array_node2.insert(name, priority)
            if PRINT == 1:
                print("Container [{}] has been created on node [2] with priority [{}].".format(name, priority))


def command_remove(scope, name, PRINT):
    if scope == "node":
        if name == "1":
            containers = array_node1.print_name()
            local_command = f"docker rm -f {containers}"
            run_command_no_echo(local_command)
            array_node1.clear()
            if PRINT == 1:
                print("All containers on node1 has been removed.")
        elif name == "2":
            containers = array_node2.print_name()
            remote_command = f"ssh {remote_user}@{remote_host} docker rm -f {containers}"
            run_command_no_echo(remote_command)
            array_node2.clear()
            if PRINT == 1:
                print("All containers on node2 has been removed.")
        elif name == "all":
            containers = array_node1.print_name()
            local_command = f"docker rm -f {containers}"
            run_command_no_echo(local_command)
            array_node1.clear()
            containers = array_node2.print_name()
            remote_command = f"ssh {remote_user}@{remote_host} docker rm -f {containers}"
            run_command_no_echo(remote_command)
            array_node2.clear()
            if PRINT == 1:
                print("All containers on all nodes has been removed.")
        else:
            if PRINT == 1:
                print("No such a node.")
    elif scope == "container":
        found = 0
        if array_node1.delete(name) == 1:
            local_command = f"docker rm -f {name}"
            run_command_no_echo(local_command)
            found = 1
            if PRINT == 1:
                print("Container [{}] on node [1] has been removed.".format(name))
        elif array_node2.delete(name) == 1:
            remote_command = f"ssh {remote_user}@{remote_host} docker rm -f {name}"
            run_command_no_echo(remote_command)
            found = 1
            if PRINT == 1:
                print("Container [{}] on node [2] has been removed.".format(name))
        if found != 1:
            if PRINT == 1:
                print("No such a container.")
        

def command_show(content):
    if content == "deployment":
        local_command = "docker ps"
        remote_command = f"ssh {remote_user}@{remote_host} docker ps"
    elif content == "priority":
        local_command = "docker stats --no-stream"
        remote_command = f"ssh {remote_user}@{remote_host} docker stats --no-stream"

    print("节点1：")
    run_command(local_command)
    print("--------------------------------------------------------------------------------------------------------------------------------------------")
    print("节点2：")
    run_command(remote_command)


def command_migrate(src, dst, name, PRINT):
    if src == dst:
        if PRINT == 1:
            print("src and dst is the same node")
    else:
        ret = check_existence(name)
        if ret == 1:
            if src == "1" and dst == "2":
                priority = array_node1.get_priority_by_name(name)
                command_remove("container", name, 0)
                command_deploy(priority, "2", name, 0)
                if PRINT == 1:
                    print("Container [{}] migrates from node [1] to node [2].".format(name))
            elif src == "2":
                if PRINT == 1:
                    print("Container [{}] exists on node [1].".format(name))
        elif ret == 2:
            if src == "2" and dst == "1":
                priority = array_node2.get_priority_by_name(name)
                command_remove("container", name, 0)
                command_deploy(priority, "1", name, 0)
                if PRINT == 1:
                    print("Container [{}] migrates from node [2] to node [1].".format(name))
            elif src == "1":
                if PRINT == 1:
                    print("Container [{}] exists on node [2].".format(name))
        else:
            if PRINT == 1:
                print("Container [{}] dose not exist.".format(name))


last_rx_packets = [0, 0]

def calculate_rx_rate():
    global last_rx_packets
    
    while True:
        with open(f"/sys/class/net/{local_interface}/statistics/rx_packets", "r") as f:
            local_rx_packets = int(f.read().strip())

        cmd = f"ssh {remote_user}@{remote_host} cat /sys/class/net/{remote_interface}/statistics/rx_packets"
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        remote_rx_packets = int(stdout.decode().strip())

        local_rx_rate = local_rx_packets - last_rx_packets[0]
        remote_rx_rate = remote_rx_packets - last_rx_packets[1]

        last_rx_packets[0] = local_rx_packets
        last_rx_packets[1] = remote_rx_packets

        yield (local_rx_rate, remote_rx_rate)

        time.sleep(cal_period)


last_event = -1
name1 = "service_enrty_A"
name2 = "service_entry_B"

def handle_event5(event):
    global last_event
    if last_event == 5:
        # command_remove("container", name2, 0)
        message_queue.insert_message("remove container " + name2 + " 0")
        return event + f" [{name2}] has been removed from node [1]."
    else:
        return event

def deploy_strategy(local_rx_rate, remote_rx_rate, time):
    global last_event
    event = ""
    if (remote_rx_rate != 0) ^ (local_rx_rate != 0):
        if (last_event != 0) and (remote_rx_rate > 0) and (remote_rx_rate < throughput_low):
            # command_migrate("1", "2", name1, 0)
            message_queue.insert_message("migrate 1 2 " + name1 + " 0")
            # command_deploy("low", "2", name1, 0)
            message_queue.insert_message("deploy low 2 " + name1 + " 0")
            event = f"Event@{time}s: [{name1}] has been deployed on node [2] with priority [low]."
            event = handle_event5(event)
            last_event = 0
        if (last_event != 1) and (remote_rx_rate > throughput_low) and (remote_rx_rate < throughput_medium):
            # command_migrate("1", "2", name1, 0)
            message_queue.insert_message("migrate 1 2 " + name1 + " 0")
            # command_deploy("medium", "2", name1, 0)
            message_queue.insert_message("deploy medium 2 " + name1 + " 0")
            event =  f"Event@{time}s: [{name1}] has been deployed on node [2] with priority [medium]."
            event = handle_event5(event)
            last_event = 1
        if (last_event != 2) and (local_rx_rate > 0) and (local_rx_rate < throughput_low):
            # command_migrate("2", "1", name1, 0)
            message_queue.insert_message("migrate 2 1 " + name1 + " 0")
            # command_deploy("low", "1", name1, 0)
            message_queue.insert_message("deploy low 1 " + name1 + " 0")
            event = f"Event@{time}s: [{name1}] has been deployed on node [1] with priority [low]."
            event = handle_event5(event)
            last_event = 2
        if (last_event != 3) and (local_rx_rate > throughput_low) and (local_rx_rate < throughput_medium):
            # command_migrate("2", "1", name1, 0)
            message_queue.insert_message("migrate 2 1 " + name1 + " 0")
            # command_deploy("medium", "1", name1, 0)
            message_queue.insert_message("deploy medium 1 " + name1 + " 0")
            event = f"Event@{time}s: [{name1}] has been deployed on node [1] with priority [medium]."
            event = handle_event5(event)
            last_event = 3
        if (last_event != 4) and (local_rx_rate > throughput_medium) and (local_rx_rate < throughput_high):
            # command_migrate("2", "1", name1, 0)
            message_queue.insert_message("migrate 2 1 " + name1 + " 0")
            # command_deploy("high", "1", name1, 0)
            message_queue.insert_message("deploy high 1 " + name1 + " 0")
            event = f"Event@{time}s: [{name1}] has been deployed on node [1] with priority [high]."
            event = handle_event5(event)
            last_event = 4
        if (last_event != 5) and (local_rx_rate > throughput_high):
            # command_migrate("2", "1", name1, 0)
            message_queue.insert_message("migrate 2 1 " + name1 + " 0")
            # command_deploy("high", "1", name1, 0)
            message_queue.insert_message("deploy high 1 " + name1 + " 0")
            # command_deploy("high", "1", name2, 0)
            message_queue.insert_message("deploy high 1 " + name2 + " 0")
            event = f"Event@{time}s: [{name1}] and [{name2}] have been deployed on node [1] with priority [high]."
            last_event = 5
            
    if event != "":
        event_list.insert(event)
    


def command_deploy_auto():
    rx_rate_generator = calculate_rx_rate()
    time_elapsed = 0
    
    while True:
        try:
            local_rx_rate, remote_rx_rate = next(rx_rate_generator)
            time_elapsed += cal_period
            os.system('clear')
            print("Automatically adjust the deployment of containers based on network throughput")
            print("Type 'Ctrl + C' to quit.")
            print(f"\nTime elapsed: {time_elapsed} s")
            print(f"Node [1] RX rate: {local_rx_rate} pps")
            print(f"Node [2] RX rate: {remote_rx_rate} pps")
            event_list.print_all()
            deploy_strategy(local_rx_rate, remote_rx_rate, time_elapsed)
        except KeyboardInterrupt:
            event_list.clear()
            break;
            


class MessageQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def insert_message(self, message):
        self.queue.put(message)

    def process_messages(self):
        while True:
            message = self.queue.get()
            args = message.split()
            if args[0] == "deploy":
                if len(args) == 5:
                    command_deploy(args[1], args[2], args[3], int(args[4]))
                else:
                    print("wrong msg")
            elif args[0] == "migrate":
                if len(args) == 5:
                    command_migrate(args[1], args[2], args[3], int(args[4]))
                else:
                    print("wrong msg")
            elif args[0] == "remove":
                if len(args) == 4:
                    command_remove(args[1], args[2], int(args[3]))
                else:
                    print("wrong msg")
            elif args[0] == "exit":
                break

message_queue = MessageQueue()


########################################
############## main logic ##############
########################################

rx_pkt_local_last = 0
rx_pkt_local_cur = 0
rx_pkt_remote_last = 0
rx_pkt_remote_cur = 0

config = read_config()
remote_host = config["remote_host"]
remote_user = config["remote_user"]
local_interface = config["local_interface"]
remote_interface = config["remote_interface"]
priority_cpu_low = config["priority_cpu_low"]
priority_mem_low = config["priority_mem_low"]
priority_cpu_medium = config["priority_cpu_medium"]
priority_mem_medium = config["priority_mem_medium"]
priority_cpu_high = config["priority_cpu_high"]
priority_mem_high = config["priority_mem_high"]
image = config["image"]
cal_period = int(config["cal_period"])
throughput_low = int(config["throughput_low"])
throughput_medium = int(config["throughput_medium"])
throughput_high = int(config["throughput_high"])

atexit.register(cleanup)

print_welcome()

t = threading.Thread(target=message_queue.process_messages)
t.start()

while True:
    
    user_input = get_input()
    if user_input == -1:
        continue
    
    if user_input["command"] == "deploy":
        command_deploy(user_input["priority"], user_input["node"], user_input["name"], 1)
        # message_queue.insert_message("deploy "+user_input["priority"]+" "+user_input["node"]+" "+user_input["name"]+" 1")
        
    elif user_input["command"] == "migrate":
        command_migrate(user_input["src"], user_input["dst"], user_input["name"], 1)
        # message_queue.insert_message("migrate "+user_input["src"]+" "+user_input["dst"]+" "+user_input["name"]+" 1")
        
    elif user_input["command"] == "deploy_auto":
        command_deploy_auto()
    
    elif user_input["command"] == "show":
        command_show(user_input["content"])
        
    elif user_input["command"] == "remove":
        command_remove(user_input["scope"], user_input["name"], 1)
        # message_queue.insert_message("remove "+user_input["scope"]+" "+user_input["name"]+" 1")
        
    elif user_input["command"] == "test":
        message_queue.insert_message("migrate 2 1 " + name1 + " 1")
            # command_deploy("low", "1", name1, 0)
        message_queue.insert_message("deploy low 1 " + name1 + " 1")
        pass
