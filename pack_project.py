#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目打包脚本
用于将项目文件打包为压缩文件，排除venv虚拟环境、__pycache__等不需要的文件
"""

import os
import shutil
import zipfile
import datetime
import argparse
from pathlib import Path


def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))


def should_include(path, root_dir):
    """
    判断文件或目录是否应该包含在打包中
    
    Args:
        path: 文件或目录的路径
        root_dir: 项目根目录
    
    Returns:
        bool: 是否包含
    """
    # 获取相对路径
    rel_path = os.path.relpath(path, root_dir)
    
    # 排除venv目录
    if "venv" in rel_path.split(os.sep):
        return False
    
    # 排除__pycache__目录
    if "__pycache__" in rel_path.split(os.sep):
        return False
    
    # 排除.git目录
    if ".git" in rel_path.split(os.sep):
        return False
    
    # 排除打包脚本本身
    if path == os.path.abspath(__file__):
        return False
    
    # 排除媒体文件目录
    if "media" in rel_path.split(os.sep):
        return False

    if "generate" in rel_path.split(os.sep):
        return False   
    
    # 检查文件类型
    if os.path.isfile(path):
        # 包含.py, .txt, .md, .yml, .html文件
        allowed_extensions = ['.py', '.txt', '.md', '.yml', '.html']
        _, ext = os.path.splitext(path)
        return ext.lower() in allowed_extensions
    
    # 目录默认包含，但后续会检查内部文件
    return True


def create_zip_archive(root_dir, output_path, include_empty_dirs=True):
    """
    创建ZIP压缩文件
    
    Args:
        root_dir: 要打包的根目录
        output_path: 输出ZIP文件路径
        include_empty_dirs: 是否包含空目录
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 获取所有需要包含的文件和目录
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 过滤目录，移除不应该包含的目录
            dirnames[:] = [d for d in dirnames if should_include(os.path.join(dirpath, d), root_dir)]
            
            # 如果包含空目录且该目录应该被包含
            if include_empty_dirs and should_include(dirpath, root_dir):
                # 计算相对路径作为ZIP内部路径
                zip_path = os.path.relpath(dirpath, root_dir)
                # 确保路径格式正确
                if zip_path != '.':
                    # 添加空目录（需要以/结尾）
                    zipf.writestr(zip_path + '/', '')
            
            # 处理文件
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if should_include(file_path, root_dir):
                    # 计算相对路径作为ZIP内部路径
                    zip_path = os.path.relpath(file_path, root_dir)
                    # 添加文件到ZIP
                    zipf.write(file_path, zip_path)
                    print(f"已添加: {zip_path}")


def main():
    """主函数"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='项目打包脚本')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出ZIP文件路径（默认在当前目录生成带时间戳的文件名）')
    parser.add_argument('--include-empty-dirs', action='store_true',
                        help='包含空目录')
    args = parser.parse_args()
    
    # 获取项目根目录
    root_dir = get_project_root()
    
    # 确定输出文件路径
    if args.output:
        output_path = args.output
        # 确保有.zip扩展名
        if not output_path.endswith('.zip'):
            output_path += '.zip'
    else:
        # 生成带时间戳的文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(root_dir, f'HotspotCrawler_{timestamp}.zip')
    
    print(f"开始打包项目到: {output_path}")
    print(f"项目根目录: {root_dir}")
    
    try:
        # 创建ZIP压缩文件
        create_zip_archive(root_dir, output_path, args.include_empty_dirs)
        print(f"\n打包完成！输出文件: {output_path}")
        print(f"文件大小: {os.path.getsize(output_path) / 1024:.2f} KB")
    except Exception as e:
        print(f"打包过程中出错: {e}")
        # 如果输出文件已创建，尝试删除
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())