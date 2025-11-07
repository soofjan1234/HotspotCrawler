import requests
import os
import re
from bs4 import BeautifulSoup
import time
from config.config_manager import ConfigManager

class MediaDownloader:
    """媒体文件下载器类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        # 获取爬虫配置
        crawler_config = self.config_manager.get('crawler', {})
        # 获取图片数量限制配置，如果没有设置则默认不限制（设置为0）
        self.max_images_per_article = crawler_config.get('max_images_per_article', 0)
        # 获取重试次数配置，如果没有设置则默认重试3次
        self.max_retries = crawler_config.get('max_retries', 3)
        # 获取超时时间配置，如果没有设置则默认30秒
        self.timeout = crawler_config.get('timeout', 30)
    
    def download_images(self, image_urls, save_dir):
        downloaded_images = []
        
        # 检查是否需要限制图片数量
        if self.max_images_per_article > 0:
            image_urls = image_urls[:self.max_images_per_article]
              
        for i, img_url in enumerate(image_urls):
            # 实现重试机制
            retries = 0
            success = False
            
            while retries <= self.max_retries and not success:
                try:
                    # 确保URL是完整的
                    if not img_url.startswith(('http://', 'https://')):
                        # 头条图片通常使用//开头，需要补充协议
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        else:
                            break
                    
                    # 获取图片扩展名
                    img_ext = img_url.split('.')[-1].split('?')[0]  # 获取扩展名，去掉可能的查询参数
                    if len(img_ext) > 5:  # 如果扩展名太长，可能不是真的扩展名
                        img_ext = 'jpg'
                    
                    # 保存图片
                    img_name = f"image_{i + 1}.{img_ext}"
                    img_path = os.path.join(save_dir, img_name)
                    
                    # 下载图片
                    response = requests.get(img_url, timeout=self.timeout)
                    if response.status_code == 200:
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        downloaded_images.append(img_path)
                        print(f"  已下载图片 {i + 1}/{len(image_urls)}")
                        success = True
                    elif retries < self.max_retries:
                        retries += 1
                        wait_time = 1 * retries  # 指数退避策略
                        print(f"  图片下载失败，状态码: {response.status_code}，将在{wait_time}秒后重试({retries}/{self.max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"  图片下载失败，状态码: {response.status_code}，已达到最大重试次数")
                        break
                except Exception as e:
                    if retries < self.max_retries:
                        retries += 1
                        wait_time = 1 * retries  # 指数退避策略
                        print(f"  下载图片失败: {str(e)}，将在{wait_time}秒后重试({retries}/{self.max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"  下载图片失败: {str(e)}，已达到最大重试次数")
                        break
            
            # 正常延迟，避免请求过快
            if success:
                time.sleep(1)
        return downloaded_images
    
    def extract_and_download_videos(self, html_content, save_dir):
        downloaded_videos = []
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            video_elements = soup.find_all('video')
                
            print(f"找到 {len(video_elements)} 个视频元素")
            
            for i, video in enumerate(video_elements):
                # 获取视频源URL
                video_url = None
                try:
                    if video.get('src'):
                        video_url = video.get('src')
                    else:
                        # 查找source标签
                        source = video.find('source')
                        if source and source.get('src'):
                            video_url = source.get('src')
                    
                    # 如果找不到直接的视频URL，尝试查找data-src或其他可能的属性
                    if not video_url:
                        video_url = video.get('data-src') or video.get('data-video-url')
                    
                    # 还可以尝试通过正则表达式查找视频URL
                    if not video_url:
                        video_match = re.search(r'videoUrl[\\s]*:[\\s]*["\'](.*?)["\']', html_content, re.S)
                        if video_match:
                            video_url = video_match.group(1)
                except Exception as e:
                    print(f"  提取视频URL失败: {str(e)}")
                    continue
                
                if video_url:
                    # 确保URL是完整的
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    elif not video_url.startswith(('http://', 'https://')):
                        continue
                    
                    # 保存视频
                    video_name = f"video_{i + 1}.mp4"  # 假设视频都是mp4格式
                    video_path = os.path.join(save_dir, video_name)
                    
                    # 实现重试机制
                    retries = 0
                    success = False
                    
                    while retries <= self.max_retries and not success:
                        try:
                            print(f"  正在下载视频 {i + 1}/{len(video_elements)}")
                            # 下载视频（注意：视频文件可能很大，这里简化处理）
                            response = requests.get(video_url, stream=True, timeout=self.timeout)
                            if response.status_code == 200:
                                with open(video_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                                        if chunk:
                                            f.write(chunk)
                                downloaded_videos.append(video_path)
                                print(f"  视频下载完成")
                                success = True
                            elif retries < self.max_retries:
                                retries += 1
                                wait_time = 2 * retries  # 视频下载重试间隔稍长
                                print(f"  视频下载失败，状态码: {response.status_code}，将在{wait_time}秒后重试({retries}/{self.max_retries})")
                                time.sleep(wait_time)
                            else:
                                print(f"  视频下载失败，状态码: {response.status_code}，已达到最大重试次数")
                                break
                        except Exception as e:
                            if retries < self.max_retries:
                                retries += 1
                                wait_time = 2 * retries  # 视频下载重试间隔稍长
                                print(f"  下载视频失败: {str(e)}，将在{wait_time}秒后重试({retries}/{self.max_retries})")
                                time.sleep(wait_time)
                            else:
                                print(f"  下载视频失败: {str(e)}，已达到最大重试次数")
                                break
                    
                    # 视频下载间隔更长一些，避免请求过快
                    if success:
                        time.sleep(2)
        except Exception as e:
            print(f"  提取视频信息失败: {str(e)}")
        return downloaded_videos