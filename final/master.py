import socket
import json
import threading
from datetime import datetime
from load_balance import LoadBalancer
import time
import argparse

class Master:
    def __init__(self, host='0.0.0.0', port=5001, lb_algorithm='least_loaded'):
        self.host = host
        self.port = port
        self.slaves = {}  # 存储所有slave的信息
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.slave_sockets = {}  # 存储slave的socket连接
        self.task_queue = []  # 存储待处理的任务
        self.lb_algorithm = lb_algorithm  # 负载均衡算法
        self.load_balancer = LoadBalancer()  # 创建负载均衡器实例
        self.start_time = None  # 任务开始时间
        self.completed_tasks = 0  # 已完成的任务数
        self.total_tasks = 0  # 总任务数
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
            for i in range(1000)
        ]
        self.total_tasks = len(self.task_queue)
        print(f"已生成 {self.total_tasks} 个任务")

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
                
                message = json.loads(data)
                if 'task_complete' in message:  # 处理任务完成消息
                    self.completed_tasks += 1
                    if self.completed_tasks == self.total_tasks:
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print(f"\n所有任务已完成！")
                        print(f"总耗时: {total_time:.2f} 秒")
                        print(f"平均每个任务耗时: {total_time/self.total_tasks:.2f} 秒")
                else:  # 处理心跳消息
                    self.slaves[address] = {
                        'last_heartbeat': datetime.now(),
                        'stats': message
                    }
                    print(f"从 {address} 收到心跳数据: {message}")
                
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
        # 使用指定的算法选择最佳节点
        best_node = self.load_balancer.select_best_node(self.slaves, self.lb_algorithm)
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
        self.start_time = time.time()  # 记录开始时间
        print(f"开始分发任务，时间: {datetime.fromtimestamp(self.start_time)}")
        
        while True:
            if not self.task_queue:
                if self.completed_tasks < self.total_tasks:
                    time.sleep(1)  # 等待所有任务完成
                    continue
                else:
                    time.sleep(5)
                    continue
            
            if not self.slaves:
                print("等待可用的slave节点...")
                time.sleep(5)
                continue
            
            task = self.task_queue.pop(0)  # 获取队列中的第一个任务
            success = self.assign_task(task)
            
            if not success:
                self.task_queue.insert(0, task)  # 如果分配失败，将任务放回队列
                time.sleep(1)
            else:
                print(f"已分发: {self.total_tasks - len(self.task_queue)}/{self.total_tasks} 任务")
                print(f"已完成: {self.completed_tasks}/{self.total_tasks} 任务")
            
            time.sleep(0.1)  # 控制分发速率

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Master节点')
    parser.add_argument('--algorithm', 
                      choices=['round_robin', 'weighted_round_robin', 'least_loaded'],
                      default='least_loaded',
                      help='选择负载均衡算法: round_robin, weighted_round_robin 或 least_loaded')
    
    args = parser.parse_args()
    
    master = Master(lb_algorithm=args.algorithm)
    print(f"使用负载均衡算法: {args.algorithm}")
    master.start() 