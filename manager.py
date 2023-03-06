#!/usr/bin/python3

import configparser
import subprocess
import atexit
import sys
import readline


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
    command_remove("node", "all", 1)
    print("Bye.")

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

def run_command_no_echo(command):
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_command(command):
    subprocess.run(command, shell=True)


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
            "image": image}


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
            sys.exit(0)
            
        elif user_input == "help" or user_input == "?":
            print_help()
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


def command_migrate(src, dst, name):
    if src == dst:
        print("src and dst is the same node")
    else:
        ret = check_existence(name)
        if ret == 1:
            if src == "1" and dst == "2":
                priority = array_node1.get_priority_by_name(name)
                command_remove("container", name, 0)
                command_deploy(priority, "2", name, 0)
                print("Container [{}] migrates from node [1] to node [2].".format(name))
            elif src == "2":
                print("Container [{}] exists on node [1].".format(name))
        elif ret == 2:
            if src == "2" and dst == "1":
                priority = array_node2.get_priority_by_name(name)
                command_remove("container", name, 0)
                command_deploy(priority, "1", name, 0)
                print("Container [{}] migrates from node [2] to node [1].".format(name))
            elif src == "1":
                print("Container [{}] exists on node [2].".format(name))
        else:
            print("Container [{}] dose not exist.".format(name))


############## main logic ##############

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

atexit.register(cleanup)

print_welcome()

while True:
    
    user_input = get_input()
    if user_input == -1:
        continue
    
    if user_input["command"] == "deploy":
        command_deploy(user_input["priority"], user_input["node"], user_input["name"], 1)
        
    elif user_input["command"] == "migrate":
        command_migrate(user_input["src"], user_input["dst"], user_input["name"])
    
    elif user_input["command"] == "deploy_auto":
        print("Not implemented")
    
    elif user_input["command"] == "show":
        command_show(user_input["content"])
        
    elif user_input["command"] == "remove":
        command_remove(user_input["scope"], user_input["name"], 1)
