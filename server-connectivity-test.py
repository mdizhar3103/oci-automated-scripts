import subprocess as sp
import sys

def read_file(filename):
    with open(filename, 'r', encoding="utf-8") as file_data:
        lines = file_data.readlines()

    return lines


def status_of_servers(ip):
    with open("Status-of-Servers.txt", 'a+', encoding="utf-8") as new_file:
        new_file.writelines(ip)


def check_server_status(server_ips):
    for ip in server_ips:
        cmd = sp.getstatusoutput("ping -a -n 2 {}".format(ip))
        print(cmd)
        print("=" * 100)
        if cmd[0] == 0:
            print("Server Present Able to Ping: ", ip)
            DNS = cmd[1].split("\n")[1].split()[1]
            status_of_servers("{}\n".format(DNS))
        else:
            status_of_servers("XXXXXXXXX {} XXXXXXXXX".format(ip))
            print("NA")


if __name__ == "__main__":
    filename = sys.argv[1]
    servers = read_file(filename)
    check_server_status(servers)
