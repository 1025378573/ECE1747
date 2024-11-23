import socket
import json
import threading
import time
import logging
import cv2
import numpy as np
import os
import random
import signal

logging.basicConfig(filename='slave.log', level=logging.INFO)

class Slave:
    def __init__(self, master_host, master_port, slave_port):
        self.master_address = (master_host, master_port)
        self.port = slave_port
        self.tasks_completed = 0
        self.total_execution_time = 0
        self.algorithm_stats = {}  # 每次启动时重新开始统计
        self.running = True
        
        # 创建输出目录
        self.output_dir = f'output_slave_{self.port}'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建socket并添加重用选项
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 设置socket重用选项
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.listen(5)
        
        # 添加信号处理
        signal.signal(signal.SIGINT, self._signal_handler) # 捕获Ctrl+C信号
        signal.signal(signal.SIGTERM, self._signal_handler) # 捕获终止信号
    
    def process_image(self, image_path, operation):
        try:
            # 1. 开始加载图片
            load_start = time.time()
            print(f"开始加载图片: {image_path}")
            img = cv2.imread(image_path)
            # 增加图片尺寸以增加处理时间
            img = cv2.resize(img, (img.shape[1]*2, img.shape[0]*2))
            load_time = time.time() - load_start
            print(f"图片加载耗时: {load_time:.2f}秒")
            
            if img is None:
                raise Exception(f"无法读取图片: {image_path}")
            
            # 2. 开始处理图片
            process_start = time.time()
            print(f"开始处理图片, 操作: {operation}")
            
            filename = os.path.basename(image_path)
            base, ext = os.path.splitext(filename)
            
            if operation == 'crop':
                # 增加裁剪前的处理
                for _ in range(3):  # 多次处理以增加时间
                    img = cv2.GaussianBlur(img, (5, 5), 0)
                    img = cv2.medianBlur(img, 5)
                
                h, w = img.shape[:2]
                crop_size = min(h, w) // 2
                x = random.randint(0, w - crop_size)
                y = random.randint(0, h - crop_size)
                img = img[y:y+crop_size, x:x+crop_size]
                output_path = os.path.join(self.output_dir, f"{base}_cropped{ext}")
                
            elif operation == 'noise':
                # 增加多层次噪声
                for _ in range(3):  # 添加多层噪声
                    noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
                    img = cv2.add(img, noise)
                    # 添加椒盐噪声
                    prob = 0.05
                    thresh = 1 - prob 
                    for i in range(img.shape[0]):
                        for j in range(img.shape[1]):
                            rdn = random.random()
                            if rdn < prob:
                                img[i][j] = 0
                            elif rdn > thresh:
                                img[i][j] = 255
                
                output_path = os.path.join(self.output_dir, f"{base}_noisy{ext}")
                
            elif operation == 'grayscale':
                # 增加灰度处理的复杂度
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # 添加直方图均衡化
                img = cv2.equalizeHist(img)
                # 添加自适应阈值处理
                img = cv2.adaptiveThreshold(img, 255, 
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
                # 添加形态学操作
                kernel = np.ones((5,5), np.uint8)
                img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
                img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
                
                output_path = os.path.join(self.output_dir, f"{base}_gray{ext}")
                
            process_time = time.time() - process_start
            print(f"图片处理耗时: {process_time:.2f}秒")
            
            # 3. 开始保存图片
            save_start = time.time()
            print(f"开始保存图片: {output_path}")
            cv2.imwrite(output_path, img)
            save_time = time.time() - save_start
            print(f"图片保存耗时: {save_time:.2f}秒")
            
            # 计算总时间
            total_time = load_time + process_time + save_time
            print(f"总耗时: {total_time:.2f}秒")
            
            return output_path, {
                'load_time': load_time,
                'process_time': process_time,
                'save_time': save_time,
                'total_time': total_time
            }
            
        except Exception as e:
            print(f"处理图片时出错: {e}")
            raise
    
    def start(self):
        self._register_with_master()
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True) # 设置为守护线程
        heartbeat_thread.start()
        
        logging.info(f"从节点启动于端口 {self.port}")
        try:
            while self.running:
                try:
                    # 设置accept超时，这样可以定期检查running状态
                    self.socket.settimeout(1.0)
                    client_socket, address = self.socket.accept() 
                    threading.Thread(target=self._handle_task, 
                                     args=(client_socket,)).start() # 启动线程处理任务
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # 只在正常运行时记录错误
                        logging.error(f"接受连接错误: {e}")
        except KeyboardInterrupt:
            self._signal_handler(signal.SIGINT, None) # 捕获Ctrl+C信号
        finally:
            self._cleanup()
    
    def _register_with_master(self): # 注册到主节点
        master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        try:
            master_socket.connect(self.master_address)
            register_msg = {
                'type': 'register',
                'port': self.port
            }
            master_socket.send(json.dumps(register_msg).encode())
        finally:
            master_socket.close()
    
    def _handle_task(self, client_socket): # 处理任务
        try:
            data = client_socket.recv(1024).decode()
            message = json.loads(data)
            task_data = message['data']
            
            if task_data['type'] == 'image':
                print(f"接收到图片处理任务: {task_data['image_path']}")
                output_path, time_stats = self.process_image(
                    task_data['image_path'],
                    task_data['operation']
                )
                
                self.tasks_completed += 1
                self.total_execution_time += time_stats['total_time']
                
                # 更新算法统计
                algorithm = task_data['algorithm']
                self._update_algorithm_stats(algorithm, time_stats['total_time'])
                
                # 写入日志
                log_filename = f"slave_{self.port}_{algorithm}.log"
                with open(log_filename, 'a') as f:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] 操作: {task_data['operation']}\n")
                    f.write(f"[{timestamp}] 输入图片: {task_data['image_path']}\n")
                    f.write(f"[{timestamp}] 输出图片: {output_path}\n")
                    f.write(f"[{timestamp}] 图片加载时间: {time_stats['load_time']:.2f}秒\n")
                    f.write(f"[{timestamp}] 图片处理时间: {time_stats['process_time']:.2f}秒\n")
                    f.write(f"[{timestamp}] 图片保存时间: {time_stats['save_time']:.2f}秒\n")
                    f.write(f"[{timestamp}] 总执行时间: {time_stats['total_time']:.2f}秒\n")
                    f.write(f"[{timestamp}] 总任务数: {self.tasks_completed}\n")
                    f.write(f"[{timestamp}] 累计执行时间: {self.total_execution_time:.2f}秒\n")
                    f.write("-" * 50 + "\n")
                
                response = {
                    'status': 'success',
                    'execution_time': time_stats['total_time'],
                    'time_stats': time_stats,
                    'output_path': output_path
                }
                
            client_socket.send(json.dumps(response).encode())
            
        except Exception as e:
            logging.error(f"处理任务错误: {e}")
            response = {
                'status': 'error',
                'message': str(e)
            }
            client_socket.send(json.dumps(response).encode())
        finally:
            client_socket.close()
    
    def _send_heartbeat(self):
        while True:
            try:
                socket_hb = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_hb.connect(self.master_address)
                heartbeat_msg = {
                    'type': 'heartbeat',
                    'port': self.port,
                    'tasks': self.tasks_completed,
                    'total_execution_time': self.total_execution_time,
                    'algorithm_stats': self.algorithm_stats
                }
                socket_hb.send(json.dumps(heartbeat_msg).encode())
            except Exception as e:
                logging.error(f"心跳发送失败: {e}")
            finally:
                socket_hb.close()
            time.sleep(10)
    
    def _signal_handler(self, signum, frame): 
        print(f"\n正在关闭从节点 {self.port}...")
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        logging.info(f"从节点 {self.port} 已关闭")
        sys.exit(0)
    
    def _cleanup(self):
        """清理资源"""
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        logging.info(f"从节点 {self.port} 资源已清理")
    
    def _update_algorithm_stats(self, algorithm, execution_time):
        """更新算法统计信息"""
        if algorithm not in self.algorithm_stats:
            self.algorithm_stats[algorithm] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0
            }
        
        stats = self.algorithm_stats[algorithm]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        print(f"更新算法 {algorithm} 统计: 总任务数 {stats['count']}, 平均时间 {stats['avg_time']:.2f}秒")

if __name__ == '__main__':
    import sys
    master_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    master_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5008
    slave_port = int(sys.argv[3]) if len(sys.argv) > 3 else 5009
    
    slave = Slave(master_host, master_port, slave_port)
    slave.start() 