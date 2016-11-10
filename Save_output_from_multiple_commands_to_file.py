"""
This is a barebones script written to SSH to a Brocade device, run a series of commands and save the command
output to a file.  The script prompts the user for the IP address to which to connect, a username and 
password, and the name of the file in which the commands are listed, one per line.  If said file does  
no exist before the script is initiated, the user could create the file and save it in another window
when that prompt appears.


"""

import re
import sys
import time
import paramiko
import datetime

def get_cmd_output(sub_command,sub_delay):
  """
  This codechunk issues a command to a Brocade device and stores the output 
  of that command in a variable.  It requires that you are already connected
  to the device via a paramiko ssh session.  It is invoked using:
  variableContainingCommandOutput = get_cmd_output(command,0.250)
  where command represents the command to be issued and the number is a tunable
  timeout parameter which can be adjusted to a larger number for extremely
  slow connections.
  """
  ######Initialize counter and ouput variables
  counter = 0
  command_output = ""
  #Next, send the command
  my_shell.send("%s\n" % sub_command)
  timercount = 0

  #This while loop assures the device is ready to return data
  while not my_shell.recv_ready():
    time.sleep(sub_delay)
    timercount = timercount + 1
    if timercount > 50:
      print "Connection FAILED!!!!"
      sys.exit()

  #The device is ready to provide data. This structure reads a chunk
  #of data, adds it to the data so far, then waits until the device
  #is ready to provide more data and repeats until the device stops
  #providing data for while
  while my_shell.recv_ready():
    counter = counter + 1
    this_output_chunk = my_shell.recv(100000)
    command_output = command_output + this_output_chunk
    timercount = 0
    #print "\nCounter is %d\nAnd cumm var is\n%s" %(counter, command_output)
    while not my_shell.recv_ready():
      time.sleep(sub_delay)
      timercount = timercount + 1
      if timercount > 20:
        #print "Output complete"
        break
  return command_output

#Prompt user for IP address of target device and store in variable "host"
host = raw_input("Enter IP address: ")
#Prompt user for username and store response in variable "user"
user = raw_input("Enter username: ")
#Prompt user for password and store in variable "pw"
pw = raw_input("Enter password: ")
#The following three lines use the paramiko library to establish an SSH session to the target
sshSession = paramiko.SSHClient()
sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sshSession.connect(host,username=user,password=pw)
#This is why one should comment in real time.  I think the next line creates the shell so I can 
#issue a series of commands without having to terminate and reopen the session for each command.
my_shell = sshSession.invoke_shell()
#The next line creates a text string representing the date and time and stores in variable "timestamp"
timestamp = time.strftime("%Y%m%d") + "_" + time.strftime("%H%M")
#The next lines send "ena" and "skip" to the device
my_shell.send("ena\n")
time.sleep(0.500)
my_shell.send("skip\n")
time.sleep(0.500)
#"sho run | i hostname" is sent and the resulting dialog is saved in variable "sho_hostname_resp"
my_shell.send("sho run | i hostname\n")
time.sleep(0.500)
sho_hostname_resp = my_shell.recv(1000)
#The variable is evaluated using the regex 'r".+\n.*hostname\s([^\s\n\r]+)"' and the result is stored in var "reresult"
reresult = re.search(r".+\n.*hostname\s([^\s\n\r]+)",sho_hostname_resp)
#The actual hostname of the device is stored in variable "host". This assumes that a hostname is explicitly configured
#on the device using the syntax "hostname <HOSTNAME>"
host = reresult.group(1)
#Create an output file  name and open the file
output_file_name = host + "_" + timestamp + ".txt"
output_file = open(output_file_name, 'a')
#Prompt the user for the name of the file containing the commands to be executed
commands_to_be_sent_file = raw_input("Enter the filename containing the commands: ")
command_inputs = open(commands_to_be_sent_file)
#Read the first command
current_command = command_inputs.readline()
while current_command:
  current_command_resp = get_cmd_output(current_command,0.05)
  output_file.write(current_command_resp)
  current_command = command_inputs.readline()
