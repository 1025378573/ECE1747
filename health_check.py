import socket
import json
import time
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HealthChecker:
    def __init__(self, master_host='localhost', master_port=5008):
        self.master_address = (master_host, master_port)
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        logging.info("正在关闭健康检查...")
        self.running = False
        sys.exit(0)
        
    def check_node_health(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect(self.master_address)
            sock.send(json.dumps({'type': 'health_check'}).encode())
            response = json.loads(sock.recv(1024).decode())
            return response.get('status') == 'ok'
        except Exception as e:
            logging.error(f"健康检查失败: {e}")
            return False
        finally:
            sock.close()
            
    def run(self):
        while self.running:
            health = self.check_node_health()
            status = "正常" if health else "异常"
            logging.info(f"主节点状态: {status}")
            time.sleep(60)

if __name__ == '__main__':
    import sys
    master_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    master_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5008
    
    checker = HealthChecker(master_host, master_port)
    checker.run() 