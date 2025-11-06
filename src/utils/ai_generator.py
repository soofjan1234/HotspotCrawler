#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文案生成工具模块
提供从文本文件读取内容并使用AI生成新文案的功能
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_generator')


class AIGenerator:
    """
    AI文案生成器类
    封装与AI API的交互，提供从文本文件生成新文案的功能
    """
    
    def __init__(self, api_key: str, api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"):
        """
        初始化AI生成器
        
        Args:
            api_key: API访问密钥
            api_url: API请求地址，默认为火山引擎Ark地址
        """
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def read_text_file(self, file_path: str) -> Optional[str]:
        """
        读取文本文件内容
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文件内容字符串，如果读取失败返回None
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            logger.info(f"成功读取文件: {file_path}, 内容长度: {len(content)} 字符")
            return content
            
        except UnicodeDecodeError:
            logger.error(f"文件编码错误，无法读取: {file_path}")
            return None
        except Exception as e:
            logger.error(f"读取文件时发生错误: {str(e)}")
            return None
    
    def generate_content(self, prompt: str, model: str = "volcengine_byteplus-llama-3-8b-instruct", 
                         temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """
        调用AI API生成内容
        
        Args:
            prompt: 提示词
            model: 使用的模型名称
            temperature: 生成温度，控制创造性
            max_tokens: 最大生成长度
            
        Returns:
            生成的文案内容，如果失败返回None
        """
        try:
            # 构造请求数据
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的文案生成助手，擅长根据提供的内容创建高质量、吸引人的文案。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 发送请求
            logger.info(f"正在调用AI API，模型: {model}")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30  # 30秒超时
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and result['choices']:
                    generated_text = result['choices'][0]['message']['content']
                    logger.info(f"AI内容生成成功，长度: {len(generated_text)} 字符")
                    return generated_text
                else:
                    logger.error(f"API返回格式错误: {result}")
                    return None
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("网络连接错误")
            return None
        except Exception as e:
            logger.error(f"生成内容时发生错误: {str(e)}")
            return None
    
    def generate_from_file(self, file_path: str, instruction: str = "请基于以下内容生成一篇有吸引力的文案") -> Optional[str]:
        """
        从文本文件生成新文案
        
        Args:
            file_path: 输入文本文件路径
            instruction: 生成指导说明
            
        Returns:
            生成的文案，如果失败返回None
        """
        # 读取文件内容
        content = self.read_text_file(file_path)
        if not content:
            return None
        
        # 构造提示词
        prompt = f"{instruction}\n\n原始内容:\n{content}"
        
        # 生成新文案
        return self.generate_content(prompt)
    
    def batch_generate(self, file_paths: List[str], instruction: str = "请基于以下内容生成一篇有吸引力的文案") -> Dict[str, Optional[str]]:
        """
        批量处理文件并生成文案
        
        Args:
            file_paths: 文件路径列表
            instruction: 生成指导说明
            
        Returns:
            文件名到生成文案的映射字典
        """
        results = {}
        
        for file_path in file_paths:
            logger.info(f"开始处理文件: {file_path}")
            result = self.generate_from_file(file_path, instruction)
            file_name = os.path.basename(file_path)
            results[file_name] = result
            
        return results


def create_ai_generator(config_manager):
    """
    从配置管理器创建AI生成器实例
    
    Args:
        config_manager: 配置管理器实例
        
    Returns:
        AIGenerator实例
    """
    # 从配置中获取API密钥
    api_key = config_manager.get('apiKey')
    if not api_key:
        raise ValueError("配置中未找到API密钥")
    
    return AIGenerator(api_key)

