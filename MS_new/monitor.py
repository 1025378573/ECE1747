import time
import psutil
import threading

class Monitor:
    def __init__(self):
        self.start_time = None
        self.is_monitoring = False
        self.stats = {
            'cpu_usage': [],
            'memory_usage': [],
            'processing_times': [],
            'total_images': 0,
            'processed_images': 0
        }
        
    def start_monitoring(self):
        """开始监控系统资源"""
        self.start_time = time.time()
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join()
            
    def _monitor_resources(self):
        """监控系统资源的线程函数"""
        while self.is_monitoring:
            self.stats['cpu_usage'].append(psutil.cpu_percent())
            self.stats['memory_usage'].append(psutil.virtual_memory().percent)
            time.sleep(1)
            
    def record_processing_time(self, processing_time):
        """记录单个图像的处理时间"""
        self.stats['processing_times'].append(processing_time)
        self.stats['processed_images'] += 1
        
    def set_total_images(self, total):
        """设置需要处理的总图像数"""
        self.stats['total_images'] = total
        
    def report_status(self):
        """生成监控报告"""
        if not self.start_time:
            return "监控尚未开始"
            
        total_time = time.time() - self.start_time
        avg_processing_time = sum(self.stats['processing_times']) / len(self.stats['processing_times']) if self.stats['processing_times'] else 0
        avg_cpu_usage = sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage']) if self.stats['cpu_usage'] else 0
        avg_memory_usage = sum(self.stats['memory_usage']) / len(self.stats['memory_usage']) if self.stats['memory_usage'] else 0
        
        report = f"""
系统运行报告:
总运行时间: {total_time:.2f} 秒
处理图像数量: {self.stats['processed_images']}/{self.stats['total_images']}
平均处理时间: {avg_processing_time:.2f} 秒/图像
平均CPU使用率: {avg_cpu_usage:.1f}%
平均内存使用率: {avg_memory_usage:.1f}%
        """
        return report 