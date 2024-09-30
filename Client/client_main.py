'''
Author: CPBook 3222973652@qq.com
Date: 2024-09-30 08:43:47
LastEditors: CPBook 3222973652@qq.com
LastEditTime: 2024-09-30 17:01:54
FilePath: \AutoLogV3\Client\client_main.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
#$language="python3"
#$interface="1.0"

#coding=utf8

import os
import re
import sys
import json
import time
import queue
import socket
import datetime
import logging
import threading

from logging.handlers import TimedRotatingFileHandler

log_file_path = ""

# 字符串位数补齐
def pad_number_in_string(input_str, pad_length=2):
    """
    补齐字符串中的数字部分，使其长度达到指定长度。
    
    :param input_str: 输入字符串，例如 "COM1"
    :param pad_length: 要补齐到的位数，默认为2
    :return: 补齐后的字符串，例如 "COM01"
    """
    # 使用正则表达式替换数字部分
    return re.sub(r'\d+', lambda x: x.group().zfill(pad_length), input_str)

# 日志模块
def setup_logger():
    global log_file_path

    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'Log')

    # 创建日志文件夹，如果不存在的话
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取日志文件的路径
    log_file_path = os.path.join(log_dir, '%Y-%m-%d.log')

    # 创建一个logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # 设置默认的日志级别

    # 创建一个handler，用于写入日志文件
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when='midnight',  # 每天午夜生成新的日志文件
        interval=1,  # 每1天
        backupCount=7  # 保留最近7天的日志文件
    )
    file_handler.setLevel(logging.DEBUG)  # 设置handler的日志级别

    # 再创建一个handler，用于输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # 控制台只输出错误信息

    # 定义handler的输出格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 通信模块
class Command:
    def __init__(self, rv_logger, rv_socket):
        self.logger = rv_logger
        self.socket = rv_socket

        self.status_manager = self.status_manager
        self.message_queue = self.socket.message_queue
        self.crt = SCRTControl()
        self.parsing = False
        self.hearting = False

        CMD_HANDSHAKE = {"cmd": "handshake", "para": "[]"}
        CMD_HEARTBEAT = {"cmd": "heartbeat", "para": "[]"}

        self.logger.info("Command Initiated")

    # 发消息
    def send_message(self, message):
        self.socket.send_message(message)

    # 发心跳
    def send_heartbeats(self):
            while self.hearting:
                self.send_message(CMD_HANDSHAKE)
                time.sleep(0.1)

    # 停止心跳线程
    def stop_heartbeat_thread(self):
        self.hearting = True

    # 启动心跳线程
    def start_heartbeat_thread(self):
        self.hearting = True
        heartbeat_thread = threading.Thread(target=self.send_heartbeats)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        self.logger.info("Heartbeat Thread Started")

    # 停止消息解析
    def stop_message_parser():
        self.parsing = False

    # 启动消息解析
    def start_message_parser(self):
        self.parsing = True
        while self.parsing:
            if not self.message_queue.empty():
                message = self.message_queue.get()
                self.logger.debug(f'Parse Message: {message}')

                command = message.get('cmd')
                if command == 'start':
                    # self.working = True
                    # self.tab.start()
                elif command == 'stop':
                    # self.tab.stop()
                    # self.working = False
                elif command == 'init':
                    # filepath = message.get('filepath')
                    # filename = message.get('filename')
                    # self.log(f"Executing config command with filepath: {filepath}, filename: {filename}")
                    # self.tab.set_work_session_config_path(filepath, filename)
                else:
                    self.log(f"Unknown Message: {message}")

# SecureCRT控制模块
class SCRTControl:
    def __init__(self, rv_logger):
        self.objTab = crt.GetScriptTab()
        self.logger = rv_logger

        self.tab_list = []

        self.logger.info("SCRTControl Initiated")

    def open_tab(self, com_list, path):
        objConfig = crt.OpenSessionConfiguration()
        if objConfig.GetOption("Protocol Name") == "Serial":
            self.clean_tab()

            at_log_path = os.path.join(path, f"%Y%M%D_%h%m%s_%S.log")

            objConfig.SetOption("Stop Bits", 0)
            objConfig.SetOption("Data Bits", 8)
            objConfig.SetOption("Protocol Name", "Serial")
            objConfig.SetOption("Baud Rate", 115200)
            objConfig.SetOption("DTR Flow Control", 0)
            objConfig.SetOption("CTS Flow", 0)
            objConfig.SetOption("RTS Flow Control", 0)
            objConfig.SetOption("XON Flow", 0)
            objConfig.SetOption("RTS Flow Control", 0)
            # objConfig.SetOption("Start Log Upon Connect",1)  #连接时输出日志
            objConfig.SetOption("Verify Retrieve File Status",2) #日志为追加模式
            objConfig.SetOption("New Log File At Midnight",1)# 跨日新日志
            objConfig.SetOption("Custom Log Message Connect","Session Connect")# 连接 前缀
            objConfig.SetOption("Custom Log Message Disconnect","Session Disconnect")#断连 前缀
            objConfig.SetOption("Custom Log Message Each Line","[%Y-%M-%D %h:%m:%s]")#行 前缀
            objConfig.SetOption("Log Filename V2",at_log_path)


            for com in com_list:                
                objConfig.SetOption("Com Port", com)
                objTab = objConfig.ConnectInTab()
                objtab.Caption = f"AutoSerial-{pad_number_in_string(com)}"
                self.tab_list.append(objTab)
        else:
            self.logger.error("默认配置协议非串口,选择SecureCRT->Options->Edit Default Session...->Connection->Termial->Serial,然后选择左边仅修改默认配置即可")
            crt.Dialog.MessageBox(f"默认配置不匹配,查看日志进行修改,当前日志路径:{log_file_path}")

    def clean_tab(self):
        index = crt.GetTabCount()
        remove_tab_list = []
        while index:
            objTab = crt.GetTab(index)
            if objTab.index != crt.GetScriptTab().index:
                remove_tab_list.append(objTab)
            index--

        for objTab in remove_tab_list:
            objTab.Close()

    def com_connect(self):
        for objTab in self.tab_list:
            objTab.Session.Connect()

    def com_disconnect(self):
        for objTab in self.tab_list:
            objTab.Session.Disconnect()

    def start_log(self):
        self.stop_log()

        for objTab in self.tab_list:
            objectTab.Session.LogUsingSessionOptions()

    def stop_log(self):
        for objTab in self.tab_list:
            if objTab.Session.Logging
                objectTab.Session.Log(False)



    


# 状态管理模块
class StatusManager:
    def __init__(self, rv_logger):
        self.logger = rv_logger

        self.socket_connected = False

        self.working = False #False means Not Work
        self.logger.info("StatusManager Initiated")


# 套接字模块
class SocketClient:
    def __init__(self, rv_logger, rv_status_manage, host='localhost', port=12345):
        self.logger = rv_logger
        self.status_manager = rv_status_manage

        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_queue = queue.Queue()

        self.connected = False
        self.status_manager.socket_connected = False

        self.running = True
        self.working = False
        
        self.logger.info("StatusManager Initiated")

    def close(self):
        if self.connected:
            self.running = False
            self.sock.close()
            
            self.connected = False
            self.status_manager.socket_connected = False

            self.logger.info("Connection closed")

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))

            self.connected = True
            self.status_manager.socket_connected = True

            self.logger.info(f"Connected to {self.host}:{self.port}")

            # self.start_heartbeat_thread()
            self.start_message_listener_thread()
            # self.execute_commands()

        except ConnectionRefusedError:
            self.logger.error(f"Failed to connect to {self.host}:{self.port}")

    def start_message_listener_thread(self):
        if self.connected:
            listener_thread = threading.Thread(target=self.listen_for_messages)
            listener_thread.daemon = True
            listener_thread.start()
            self.logger.info("Message Listener Thread Started")
        else:
            self.logger.error("Not Connected To Listener")

    def monitor_buffer_size(self, buffer):
        while self.running:
            self.logger.debug(f"Buffer Size: {len(buffer)} Bytes")
            time.sleep(5)  # 每5秒检查一次

    def listen_for_messages(self):
        buffer = b''  # 缓冲区用于存储接收到的数据
        # monitor_thread = threading.Thread(target=self.monitor_buffer_size, args=(buffer,))
        # monitor_thread.daemon = True
        # monitor_thread.start()
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                buffer += data
                
                while len(buffer) > 0:
                    try:
                        # 寻找 JSON 消息的结束位置（每个 JSON 消息以换行符 '\n' 结束）
                        message_end = buffer.find(b'\n')
                        if message_end == -1:
                            # 如果没有找到结束符，则跳出循环等待更多数据
                            break
                        
                        message_data = buffer[:message_end]
                        message = json.loads(message_data.decode())
                        buffer = buffer[message_end + 1:]  # 移除已处理的消息
                        
                        self.logger.debug(f"Received message: {message}")
                        self.message_queue.put(message)
                    except json.JSONDecodeError:
                        # 如果解析失败，可能是数据不完整，跳出当前循环等待更多数据
                        break
            except ConnectionResetError:
                self.logger.error(f"Server Disconnected Unexpectedly")
                break
            except Exception as e:
                self.log(f"Error Receiving Message: {e}")
                break

    def send_message(self, message):
        if self.connect:
            json_msg = json.dumps(message).encode()
            self.sock.sendall(json_msg + b'\n')
            self.logger.debug(f"Sent Message: {message}")
        else:









# main
logger = setup_logger()
logger.info('**********Client Started**********')

# 初始化各个模块
status_manager = StatusManager(logger)
clien_socket = SocketClient(logger,status_manager)
command = Command(logger,clien_socket)

clien_socket.connect()

if status_manager.socket_connected:
    # 启动心跳线程
    command.start_heartbeat_thread()

    # 启动消息解析,crt类只能在主线程使用
    command.start_message_parser()



