import socket
import json
import threading
import time
from flask import Flask, render_template
import signal
import sys

app = Flask(__name__)

class Monitor:
    def __init__(self, master_host='localhost', master_port=5008):
        self.master_address = (master_host, master_port)
        self.cluster_status = {'master_status': 'unknown', 'slaves': []}
        self.running = True
        self.status_thread = None
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        print("\n正在关闭监控系统...")
        self.running = False
        sys.exit(0)
        
    def get_cluster_status(self):
        monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            monitor_socket.connect(self.master_address)
            message = {
                'type': 'status_request'
            }
            monitor_socket.send(json.dumps(message).encode())
            status = json.loads(monitor_socket.recv(4096).decode())
            self.cluster_status = status
        except Exception as e:
            print(f"获取状态失败: {e}")
        finally:
            monitor_socket.close()
            
    def update_status_loop(self):
        while self.running:
            self.get_cluster_status()
            time.sleep(5)

monitor = Monitor()

@app.route('/')
def show_status():
    return render_template('monitor.html', status=monitor.cluster_status, time=time)

def start_monitor():
    monitor.status_thread = threading.Thread(target=monitor.update_status_loop)
    monitor.status_thread.daemon = True
    monitor.status_thread.start()
    app.run(host='0.0.0.0', port=5005)

if __name__ == '__main__':
    start_monitor() 