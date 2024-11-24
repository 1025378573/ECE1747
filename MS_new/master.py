import os
import time
import socket
import pickle
import struct
import cv2
from load_balancer import LoadBalancer
from monitor import Monitor
import concurrent.futures
from queue import Queue

class Master:
    def __init__(self, slave_nodes, load_balancer):
        """
        初始化主节点
        slave_nodes: list of tuple, 每个元素为 (host, port)
        """
        self.slave_nodes = slave_nodes
        self.load_balancer = load_balancer
        self.monitor = Monitor()
        self.task_queue = Queue()  # 任务队列
        self.slave_status = {node: True for node in slave_nodes}  # 记录节点状态
        
    def send_to_slave(self, image_path, slave_addr):
        """发送图像到从节点处理"""
        host, port = slave_addr
        
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
            
        # 编码图像数据
        _, img_encoded = cv2.imencode('.jpg', image)
        data = pickle.dumps(img_encoded)
        
        # 连接从节点
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # 发送数据
        sock.sendall(struct.pack('>L', len(data)))
        sock.sendall(data)
        
        # 接收处理完成信号
        result = sock.recv(4)
        
        sock.close()
        return result == b'done'
        
    def process_images(self, image_folder, algorithm='round_robin'):
        """处理指定文件夹中的所有图像"""
        images = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
        tasks = [os.path.join(image_folder, img) for img in images]
        
        # 将所有任务放入队列
        for task in tasks:
            self.task_queue.put(task)
            
        self.monitor.set_total_images(len(tasks))
        self.monitor.start_monitoring()
        
        start_time = time.time()
        
        # 创建工作线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.slave_nodes)) as executor:
            futures = []
            
            # 为每个从节点创建一个工作线程
            for slave_addr in self.slave_nodes:
                future = executor.submit(self.worker_thread, slave_addr)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures)
        
        self.monitor.stop_monitoring()
        print(self.monitor.report_status())
        
        end_time = time.time()
        print(f"所有图片处理完成，总耗时: {end_time - start_time:.2f}秒")
        
    def worker_thread(self, slave_addr):
        """工作线程函数，持续从队列获取任务并处理"""
        while True:
            try:
                task = self.task_queue.get_nowait()
            except Queue.Empty:
                break
                
            # 处理任务
            start_time = time.time()
            success = self.send_to_slave(task, slave_addr)
            
            if success:
                processing_time = time.time() - start_time
                self.monitor.record_processing_time(processing_time)
                # 更新负载均衡器中的节点性能记录
                self.load_balancer.update_node_performance(slave_addr, processing_time)
                self.slave_status[slave_addr] = True
            else:
                self.task_queue.put(task)
                self.slave_status[slave_addr] = False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--slaves', nargs='+', default=['localhost:5000'],
                      help='从节点地址列表，格式: host:port')
    parser.add_argument('--input', default='images', help='输入图像文件夹')
    parser.add_argument('--algorithm', default='round_robin', 
                      choices=['round_robin', 'random', 'least_connections', 
                              'weighted_round_robin', 'ip_hash'])
    args = parser.parse_args()
    
    # 解析从节点地址
    slave_nodes = []
    for addr in args.slaves:
        host, port = addr.split(':')
        slave_nodes.append((host, int(port)))
    
    lb = LoadBalancer()
    master = Master(slave_nodes, lb)
    master.process_images(args.input, algorithm=args.algorithm) 