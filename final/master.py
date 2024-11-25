import socket
import json
import threading
from datetime import datetime
from load_balance import LoadBalancer
import time

class Master:
    def __init__(self, host='0.0.0.0', port=5001):
        self.host = host
        self.port = port
        self.slaves = {}  # 存储所有slave的信息
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.slave_sockets = {}  # 存储slave的socket连接
        self.task_queue = []  # 存储待处理的任务
        self.generate_tasks()  # 生成任务队列

    def generate_tasks(self):
        """生成1000个随机任务，包含随机的图片尺寸和处理方法"""
        import random
        
        # 可用的图像处理方法
        processing_methods = ['gaussian_blur', 'edge_detection', 'color_quantization']
        
        self.task_queue = [
            {
                'task_id': i,
                'task_type': 'image_process',
                'data': {
                    'size': random.randint(100, 1000),
                    'method': random.choice(processing_methods)
                }
            }
            for i in range(10)
        ]
        print(f"已生成 {len(self.task_queue)} 个任务")

    def start(self):
        print(f"Master启动于 {self.host}:{self.port}")
        # 启动任务分发线程
        task_thread = threading.Thread(target=self.task_dispatcher)
        task_thread.daemon = True
        task_thread.start()
        
        while True:
            client_socket, address = self.socket.accept()
            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address)
            )
            client_handler.start()

    def handle_client(self, client_socket, address):
        print(f"新的slave连接：{address}")
        self.slave_sockets[address] = client_socket
        
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                heartbeat_data = json.loads(data)
                self.slaves[address] = {
                    'last_heartbeat': datetime.now(),
                    'stats': heartbeat_data
                }
                print(f"从 {address} 收到心跳数据: {heartbeat_data}")
                
            except Exception as e:
                print(f"处理客户端 {address} 数据时出错: {e}")
                break
        
        client_socket.close()
        if address in self.slaves:
            del self.slaves[address]
        if address in self.slave_sockets:
            del self.slave_sockets[address]
        print(f"客户端 {address} 断开连接")

    def assign_task(self, task_data):
        # 使用LoadBalancer选择最佳节点
        best_node = LoadBalancer.select_best_node(self.slaves)
        if not best_node:
            print("没有可用的slave节点")
            return False
            
        try:
            # 发送任务到选中的slave
            task_message = {
                'type': 'task',
                'data': task_data
            }
            self.slave_sockets[best_node].send(json.dumps(task_message).encode('utf-8'))
            print(f"任务已分配给节点 {best_node}")
            return True
        except Exception as e:
            print(f"分配任务失败: {e}")
            return False

    def task_dispatcher(self):
        """任务分发器"""
        while True:
            if not self.task_queue:  # 如果任务队列为空
                print("所有任务已分发完成")
                time.sleep(5)  # 等待5秒后继续检查
                continue
            
            if not self.slaves:  # 如果没有可用的slave
                print("等待可用的slave节点...")
                time.sleep(1)
                continue
            
            # 使用LoadBalancer选择最佳节点
            best_node = LoadBalancer.select_best_node(self.slaves)
            if best_node:
                task = self.task_queue.pop(0)  # 获取队列中的第一个任务
                self.assign_task(task)
                print(f"剩余任务数量: {len(self.task_queue)}")
            
            time.sleep(0.1)  # 控制分发速率

if __name__ == '__main__':
    master = Master()
    master.start() 