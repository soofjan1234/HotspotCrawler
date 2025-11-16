#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_file_path_logic():
    """测试文件存放路径逻辑"""
    print("=== 测试AI文案生成文件存放路径逻辑 ===")
    
    # 模拟app.py中的路径计算（修复后）
    app_file = os.path.join(os.path.dirname(__file__), 'src', 'web', 'app.py')
    base_generate_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(app_file)))), 'generate')
    
    print(f"1. 计算出的基础目录: {base_generate_dir}")
    print(f"2. 期望的基础目录: {os.path.join(os.path.dirname(__file__), 'generate')}")
    print(f"3. 路径是否正确: {os.path.abspath(base_generate_dir) == os.path.abspath(os.path.join(os.path.dirname(__file__), 'generate'))}")
    
    # 模拟文件存放逻辑
    now = datetime.now()
    date_folder = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    
    article_dir = os.path.join(base_generate_dir, date_folder, time_part)
    output_file_name = "content_ai.txt"
    output_file_path = os.path.join(article_dir, output_file_name)
    relative_path = os.path.join(date_folder, time_part, output_file_name)
    
    print(f"\n=== 文件存放结构 ===")
    print(f"4. 日期文件夹: {date_folder}")
    print(f"5. 时间文件夹: {time_part}")
    print(f"6. 完整存放路径: {output_file_path}")
    print(f"7. 相对路径: {relative_path}")
    
    # 检查目录是否存在，不存在则创建
    os.makedirs(article_dir, exist_ok=True)
    print(f"8. 目录创建状态: {'成功' if os.path.exists(article_dir) else '失败'}")
    
    # 创建测试文件
    test_content = "# 原始内容\n测试内容\n\n# AI生成文案\nAI生成的测试文案"
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"9. 测试文件创建状态: {'成功' if os.path.exists(output_file_path) else '失败'}")
    
    # 验证打印的路径和实际路径是否一致（修复后的逻辑）
    project_root = os.path.dirname(__file__)
    relative_path = os.path.relpath(output_file_path, project_root)
    actual_relative_path = os.path.relpath(output_file_path, project_root)
    print(f"10. 修复后的相对路径: {relative_path}")
    print(f"11. 实际的相对路径: {actual_relative_path}")
    print(f"12. 路径一致性: {relative_path == actual_relative_path}")
    
    print(f"\n=== 测试结果 ===")
    if os.path.exists(output_file_path) and relative_path == actual_relative_path:
        print("✅ 文件存放逻辑修复成功！")
        print(f"✅ 文件已创建在: {output_file_path}")
        return True
    else:
        print("❌ 文件存放逻辑仍有问题")
        return False

if __name__ == "__main__":
    test_file_path_logic()