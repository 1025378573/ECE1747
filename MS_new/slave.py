import cv2
import os
import socket
import pickle
import struct
from image_processing import random_processing

class Slave:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.processed_count = 0
        
    def start(self):
        """启动从节点服务器"""
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"Slave 节点启动在 {self.host}:{self.port}")
        
        while True:
            conn, addr = self.socket.accept()
            print(f"接收到来自 {addr} 的连接")
            
            # 接收图像数据
            data_size = struct.unpack('>L', conn.recv(4))[0]
            print(f"准备接收 {data_size} 字节的数据")
            
            data = b''
            while len(data) < data_size:
                data += conn.recv(4096)
            print(f"接收完成，实际接收 {len(data)} 字节")
            
            # 解析接收到的数据
            print("开始解析图像数据...")
            image_data = pickle.loads(data)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            print(f"图像大小: {image.shape}")
            
            # 处理图像
            print("开始处理图像...")
            processed_image = random_processing(image)
            print(f"处理后图像大小: {processed_image.shape}")
            
            # 发送处理完成信号
            print("发送处理完成信号...")
            conn.sendall(b'done')
            
            self.processed_count += 1
            print(f"已处理图像数量: {self.processed_count}")
            conn.close()
            print("连接关闭\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    
    slave = Slave(args.host, args.port)
    slave.start()