import socket
import json
import time
import psutil
import threading
import requests
import os

class Slave:
    def __init__(self, master_host='localhost', master_port=5001):
        self.master_host = master_host
        self.master_port = master_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def connect(self):
        try:
            self.socket.connect((self.master_host, self.master_port))
            print(f"已连接到master: {self.master_host}:{self.master_port}")
            return True
        except Exception as e:
            print(f"连接master失败: {e}")
            return False

    def collect_stats(self):
        # 获取CPU线程数
        cpu_count = psutil.cpu_count()
        # 获取CPU使用率列表（每个CPU核心的使用率）
        cpu_percent_per_cpu = psutil.cpu_percent(interval=1, percpu=True)
        # 计算空闲线程数（简化计算：认为使用率低于50%的核心为空闲）
        idle_threads = sum(1 for cpu in cpu_percent_per_cpu if cpu < 50)
        
        stats = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'total_cpu_threads': cpu_count,
            'idle_cpu_threads': idle_threads,
            'timestamp': time.time()
        }
        return stats

    def send_heartbeat(self):
        while self.running:
            try:
                stats = self.collect_stats()
                self.socket.send(json.dumps(stats).encode('utf-8'))
                time.sleep(1)
            except Exception as e:
                print(f"发送心跳失败: {e}")
                break
        
        self.running = False

    def handle_task(self, task_data):
        """处理从master接收到的任务"""
        print(f"开始处理任务: {task_data}")
        
        def task_worker():
            from image_tasks import ImageProcessor
            
            task_type = task_data.get('task_type')
            if task_type == 'image_process':
                data = task_data.get('data', {})
                size = data.get('size')
                method = data.get('method')
                
                try:
                    # 下载图片
                    url = f"https://picsum.photos/{size}"
                    response = requests.get(url, allow_redirects=True)
                    
                    if response.status_code == 200:
                        # 处理图片
                        result = ImageProcessor.process_image(response.content, method)
                        print(f"任务 {task_data['task_id']} 完成: {result}")
                    else:
                        print(f"任务 {task_data['task_id']} 失败: HTTP状态码 {response.status_code}")
                
                except Exception as e:
                    print(f"任务 {task_data['task_id']} 失败: {str(e)}")
        
        # 创建新线程处理任务
        task_thread = threading.Thread(target=task_worker)
        task_thread.start()

    def receive_data(self):
        """接收来自master的数据"""
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                if message.get('type') == 'task':
                    self.handle_task(message.get('data'))
                    
            except Exception as e:
                print(f"接收数据失败: {e}")
                break

    def start(self):
        if self.connect():
            self.running = True
            # 启动心跳线程
            heartbeat_thread = threading.Thread(target=self.send_heartbeat)
            heartbeat_thread.start()
            
            # 启动数据接收线程
            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.start()

    def stop(self):
        self.running = False
        self.socket.close()

if __name__ == '__main__':
    slave = Slave()
    try:
        slave.start()
        while slave.running: 
            time.sleep(1)
    except KeyboardInterrupt: # 按Ctrl+C停止
        print("正在停止slave...")
        slave.stop() 