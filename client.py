import socket
import json
import random
import time
import signal
import sys
import logging
from datetime import datetime
import os

class Client:
    def __init__(self, master_host='localhost', master_port=5008):
        self.master_address = (master_host, master_port)
        self.running = True
        self.algorithm_logs = {}
        self.start_time = None
        self.end_time = None
        signal.signal(signal.SIGINT, self._signal_handler) # 捕获Ctrl+C信号
        
    def _signal_handler(self, signum, frame):
        print("\n正在关闭客户端...")
        self.end_time = time.time()  # 记录结束时间
        self._save_summary_logs()
        self.running = False
        sys.exit(0)
        
    def submit_task(self, task):
        """
        向主节点提交任务并等待结果
        
        Args:
            task (dict): 任务信息字典，包含算法类型和图像处理参数
        
        Returns:
            dict: 从节点返回的处理结果
        """
        # 创建新的socket连接
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        try:
            # 连接到主节点
            client_socket.connect(self.master_address)
            
            # 构造任务消息
            message = {
                'type': 'task',
                'data': {
                    'type': 'image',
                    'operation': task['data']['operation'],
                    'image_path': task['data']['image_path'],
                    'algorithm': task['algorithm']
                }
            }
            client_socket.send(json.dumps(message).encode()) # 发送任务请求
            response = json.loads(client_socket.recv(1024).decode()) # 接收从节点响应
            
            # 记录任务执行情况
            if 'slave' in response:
                # 提取从节点端口号
                slave_port = response['slave'].split(':')[1]
                algorithm = task['algorithm']
                execution_time = response.get('execution_time', 0)
                
                # 初始化该从节点的统计信息（如果不存在）
                if slave_port not in self.algorithm_logs:
                    self.algorithm_logs[slave_port] = {}
                
                # 初始化该算法的统计信息（如果不存在）
                if algorithm not in self.algorithm_logs[slave_port]:
                    self.algorithm_logs[slave_port][algorithm] = {
                        'count': 0,
                        'total_time': 0
                    }
                
                # 更新统计信息
                self.algorithm_logs[slave_port][algorithm]['count'] += 1
                self.algorithm_logs[slave_port][algorithm]['total_time'] += execution_time
                
            return response
        finally:
            client_socket.close()
            
    def _save_summary_logs(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存从节点统计
        for slave_port, algorithms in self.algorithm_logs.items():
            log_filename = f"summary_slave_{slave_port}_{timestamp}.log"
            with open(log_filename, 'w') as f:
                f.write(f"从节点端口: {slave_port}\n")
                f.write("=" * 50 + "\n")
                
                for algorithm, stats in algorithms.items():
                    f.write(f"\n算法: {algorithm}\n")
                    f.write(f"总任务数: {stats['count']}\n")
                    f.write(f"总执行时间: {stats['total_time']:.2f}秒\n")
                    avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                    f.write(f"平均执行时间: {avg_time:.2f}秒\n")
                    f.write("-" * 30 + "\n")
        
        # 保存客户端整体执行时间统计
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            client_log_filename = f"client_{self.current_algorithm}_{timestamp}.log"
            with open(client_log_filename, 'w') as f:
                f.write(f"负载均衡算法: {self.current_algorithm}\n")
                f.write("=" * 50 + "\n")
                f.write(f"开始时间: {datetime.fromtimestamp(self.start_time)}\n")
                f.write(f"结束时间: {datetime.fromtimestamp(self.end_time)}\n")
                f.write(f"总运行时间: {total_time:.2f}秒\n")
                f.write(f"处理图片数量: {self.processed_images}\n")
                f.write(f"平均每张图片处理时间: {total_time/self.processed_images:.2f}秒\n")
                f.write("-" * 50 + "\n")

    def create_image_task(self, image_path, algorithm='round_robin'):
        operations = ['crop', 'noise', 'grayscale']
        
        return {
            'algorithm': algorithm,  # 使用指定的算法
            'data': {
                'type': 'image',
                'operation': random.choice(operations),
                'image_path': image_path
            }
        }

    def run(self):
        # 指定要使用的负载均衡算法
        self.current_algorithm = 'round_robi'  # 可以改为: 'least_connections', 'random', 'weighted_response_time'
        self.processed_images = 0
        
        # 获取image文件夹下的所有图片
        image_files = []
        for file in os.listdir('image'):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join('image', file))
        
        if not image_files:
            print("没有找到图片文件")
            return
            
        print(f"使用负载均衡算法: {self.current_algorithm}")
        try:
            self.start_time = time.time()  # 记录开始时间
            
            for image_path in image_files:
                task = self.create_image_task(image_path, self.current_algorithm)
                result = self.submit_task(task)
                self.processed_images += 1
                print(f"图片: {image_path}")
                print(f"操作: {task['data']['operation']}")
                print(f"算法: {self.current_algorithm}")
                print(f"执行结果: {result}")
                print("-" * 50)
                time.sleep(0.5)
            
            self.end_time = time.time()  # 记录结束时间
            self._save_summary_logs()
            print("\n所有图片处理完成，已生成汇总日志")
            print(f"总运行时间: {self.end_time - self.start_time:.2f}秒")
            self.running = False
                
        except KeyboardInterrupt:
            print("\n正在关闭客户端...")
            self.end_time = time.time()
            self._save_summary_logs()
        except Exception as e:
            print(f"错误: {e}")
            self.end_time = time.time()
            self._save_summary_logs()

if __name__ == '__main__':
    client = Client()
    client.run() 