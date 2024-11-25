import cv2
import numpy as np
from io import BytesIO
import requests

class ImageProcessor:
    @staticmethod
    def process_image(image_data, method):
        """根据指定方法处理图像"""
        # 将二进制图像数据转换为numpy数组
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        processors = {
            'gaussian_blur': ImageProcessor.gaussian_blur,
            'edge_detection': ImageProcessor.edge_detection,
            'color_quantization': ImageProcessor.color_quantization
        }
        
        if method in processors:
            return processors[method](img)
        else:
            raise ValueError(f"未知的处理方法: {method}")

    @staticmethod
    def gaussian_blur(img):
        """方法1：高斯模糊"""
        try:
            # 应用15x15的高斯模糊
            result = cv2.GaussianBlur(img, (15, 15), 0)
            return "高斯模糊处理完成"
        except Exception as e:
            return f"高斯模糊处理失败: {str(e)}"

    @staticmethod
    def edge_detection(img):
        """方法2：边缘检测"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # 应用Canny边缘检测
            edges = cv2.Canny(gray, 100, 200)
            return "边缘检测处理完成"
        except Exception as e:
            return f"边缘检测处理失败: {str(e)}"

    @staticmethod
    def color_quantization(img):
        """方法3：颜色量化"""
        try:
            # 将图像转换为K=8种颜色
            data = img.reshape((-1, 3))
            data = np.float32(data)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 8
            _, labels, centers = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            result = centers[labels.flatten()]
            result = result.reshape(img.shape)
            return "颜色量化处理完成"
        except Exception as e:
            return f"颜色量化处理失败: {str(e)}" 