# 转自https://blog.csdn.net/lyshark_csdn/article/details/127393711
# coding=utf-8
# Author:LZY/我不是盘神
# Software:PyCharm
# Time:2023/3/18 22:29:01
# File:MyPing.py
import time, struct
import socket, select


class MyPing():
    # 发送原始套接字
    def raw_socket(self, dst_addr, imcp_packet):
        rawsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
        send_request_ping_time = time.time()
        rawsocket.sendto(imcp_packet, (dst_addr, 80))
        return send_request_ping_time, rawsocket

    # 计算校验和
    def chesksum(self, data):
        n = len(data)
        m = n % 2
        sum = 0
        for i in range(0, n - m, 2):
            sum += (data[i]) + ((data[i + 1]) << 8)
            sum = (sum >> 16) + (sum & 0xffff)
        if m:
            sum += (data[-1])
            sum = (sum >> 16) + (sum & 0xffff)
        answer = ~sum & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    # 通过域名获取主机地址
    def get_host_address(self, host):
        dst_addr = socket.gethostbyname(host)
        return dst_addr

    # 接受到数据包
    def request_ping(self, data_type, data_code, data_checksum, data_ID, data_Sequence, payload_body):
        #  把字节打包成二进制数据
        imcp_packet = struct.pack('>BBHHH32s', data_type, data_code, data_checksum, data_ID, data_Sequence,
                                  payload_body)
        # 获取校验和
        icmp_chesksum = self.chesksum(imcp_packet)
        #  把校验和传入，再次打包
        imcp_packet = struct.pack('>BBHHH32s', data_type, data_code, icmp_chesksum, data_ID, data_Sequence,
                                  payload_body)
        return imcp_packet

    # 相应数据包,解包执行
    def reply_ping(self, send_request_ping_time, rawsocket, data_Sequence, timeout=3):
        while True:
            # 实例化select对象（非阻塞），可读，可写为空，异常为空，超时时间
            what_ready = select.select([rawsocket], [], [], timeout)
            # 等待时间 wait_for_time = (time.time() - started_select)
            wait_for_time = (time.time() - send_request_ping_time)
            # 没有返回可读的内容，判断超时
            if what_ready[0] == []:
                return -1
            # 记录接收时间
            time_received = time.time()
            # 设置接收的包的字节为1024
            received_packet, addr = rawsocket.recvfrom(1024)
            # 获取接收包的icmp头
            icmpHeader = received_packet[20:28]
            # 反转编码
            type, code, r_checksum, packet_id, sequence = struct.unpack(">BBHHH", icmpHeader)
            if type == 0 and sequence == data_Sequence:
                return time_received - send_request_ping_time
            # 数据包的超时时间判断
            timeout = timeout - wait_for_time
            if timeout <= 0:
                return -1

    # 向特定地址发送一条ping命令
    def send_ping(self, address):
        data_type = 8
        data_code = 0
        data_checksum = 0
        data_ID = 0
        data_Sequence = 1
        payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'

        # 请求ping数据包的二进制转换
        icmp_packet = self.request_ping(data_type, data_code, data_checksum, data_ID, data_Sequence, payload_body)
        # 连接套接字,并将数据发送到套接字
        send_request_ping_time, rawsocket = self.raw_socket(address, icmp_packet)
        # 数据包传输时间
        times = self.reply_ping(send_request_ping_time, rawsocket, data_Sequence)
        if times > 0:
            return_time = int(times * 1000)
            return return_time
        else:
            return -1

