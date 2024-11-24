import random
import cv2
import numpy as np
from torchvision.models.detection import maskrcnn_resnet50_fpn
import torch

def random_crop(image):
    height, width = image.shape[:2]
    # 随机生成裁剪的大小（50%-90%的原始大小）
    crop_height = random.randint(int(height * 0.5), int(height * 0.9))
    crop_width = random.randint(int(width * 0.5), int(width * 0.9))
    
    # 随机生成裁剪的起始点
    x = random.randint(0, width - crop_width)
    y = random.randint(0, height - crop_height)
    
    # 执行裁剪
    cropped = image[y:y+crop_height, x:x+crop_width]
    return cropped

def add_noise(image):
    # 生成高斯噪声
    row, col, ch = image.shape
    mean = 0
    sigma = 25
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)
    noisy = image + gauss
    
    # 确保像素值在0-255之间
    noisy = np.clip(noisy, 0, 255)
    return noisy.astype(np.uint8)

def instance_segmentation(image):
    # 使用预训练的Mask R-CNN模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = maskrcnn_resnet50_fpn(pretrained=True)
    model.eval()
    model.to(device)
    
    # 预处理图像
    image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
    image_tensor = image_tensor.unsqueeze(0).to(device)
    
    # 进行实例分割
    with torch.no_grad():
        prediction = model(image_tensor)
    
    # 在原图上绘制分割结果
    masks = prediction[0]['masks']
    if len(masks) > 0:
        mask = masks[0, 0].cpu().numpy()
        image[mask > 0.5] = [255, 0, 0]  # 用红色标记第一个检测到的对象
    
    return image

def random_processing(image):
    methods = [random_crop, add_noise, instance_segmentation]
    method = random.choice(methods)
    return method(image) 