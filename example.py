# coding=UTF-8
# Author:LZY/我不是盘神
# Software:PyCharm
# Time:2023/3/1 11:29:12
# File:example.py
import requests
import socket
import pywifi
import threading
import time

KEYWORD = "ChinaNet"
MAX_CONNECT_TRY = 3


class WifiScanner:
    def __init__(self):
        self.wifi = pywifi.PyWiFi()
        self.interface = self.wifi.interfaces()[0]
        self.result = []
        self.lock = threading.Lock()

    def scan(self):
        self.interface.scan()
        result = self.interface.scan_results()
        with self.lock:
            self.result = result

    def filter(self):
        filtered_result = []
        for wifi in self.result:
            if KEYWORD in wifi.ssid and wifi.signal > -80 and wifi.akm[0] == pywifi.const.AUTH_ALG_OPEN:
                filtered_result.append(wifi)
        return filtered_result

    def connect(self, wifi):
        profile = pywifi.Profile()
        profile.ssid = wifi.ssid
        profile.auth = pywifi.const.AUTH_ALG_OPEN
        profile.akm.append(pywifi.const.AKM_TYPE_NONE)

        self.interface.disconnect()
        self.interface.remove_all_network_profiles()
        tmp_profile = self.interface.add_network_profile(profile)

        for i in range(MAX_CONNECT_TRY):
            if self.interface.status() in [pywifi.const.IFACE_DISCONNECTED, pywifi.const.IFACE_INACTIVE]:
                self.interface.connect(tmp_profile)
                if self.interface.status() == pywifi.const.IFACE_CONNECTED:
                    print(f"Connected to {wifi.ssid} with signal strength {wifi.signal}")
                    break
            elif self.interface.status() == pywifi.const.IFACE_CONNECTED:
                break


class WifiConnector:
    def __init__(self):
        self.scanner = WifiScanner()

    def run(self):
        global ssid
        threads = []
        for i in range(10):
            t = threading.Thread(target=self.scanner.scan)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        filtered_results = self.scanner.filter()

        for result in filtered_results:
            ssid = result.ssid

        if len(filtered_results) == 1:
            self.scanner.connect(filtered_results[0])
            print(f"只有一个信号:{ssid}")
            return True
        elif len(filtered_results) >= 2:
            print(f"网络环境有多个信号,筛选信号最好的结果是:{ssid}")
            sorted_results = sorted(filtered_results, key=lambda x: x.signal, reverse=True)
            self.scanner.connect(sorted_results[0])
            return True
        else:
            print("环境非校园网")
            return False


def main():
    def get_host_ip():
        global s
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    url = 'http://10.10.11.14/portal.do?wlanuserip=' + get_host_ip() + '&wlanacname=XF_BRAS'

    headers = 2
    data = 1

    requests.post(url=url, data=data, headers=headers)


def connect_school_network() -> int:
    start_time = time.time()
    connector = WifiConnector()
    connector.run()
    time.sleep(2)  # 延迟1秒等待wifi连接
    end_time = time.time()
    takes_time = int(end_time - start_time)
    print(f'连接校园网共耗时{takes_time}秒')
    return takes_time


if __name__ == "__main__":
    connect_school_network()
    main()
