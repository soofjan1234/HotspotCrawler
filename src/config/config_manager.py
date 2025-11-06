import os
import platform
import yaml

class ConfigManager:
    """配置管理类，负责处理系统检测和路径配置"""
    
    def __init__(self):
        # 检测操作系统类型
        self.system = platform.system()  # 'Windows', 'Darwin' (Mac), etc.
        
        # 获取项目根目录（使用相对路径）
        self.project_root = self._get_project_root()
        
        # 初始化配置
        self._init_paths()
        self._init_user_agents()
        self._load_yaml_config()
    
    def _get_project_root(self):
        """获取项目根目录的绝对路径"""
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return current_dir
    
    def _init_paths(self):
        """初始化路径配置"""
        # 媒体文件保存目录（使用相对路径）
        self.media_base_dir = os.path.join(self.project_root, 'media')
        
        # 内容文件路径（使用相对路径）
        self.content_file = os.path.join(self.project_root, '内容.txt')
        
        # 文章ID记录文件路径
        self.article_id_file = os.path.join(self.project_root, 'toutiao_article_id.txt')
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
    
    def _init_user_agents(self):
        """初始化用户代理配置"""
        # 根据不同系统提供合适的用户代理
        if self.system == 'Darwin':  # Mac
            self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        elif self.system == 'Windows':  # Windows
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        else:  # 其他系统
            self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.media_base_dir, exist_ok=True)
        # 文章ID文件所在目录不需要额外创建，因为已经在project_root中
    
    def _load_yaml_config(self):
        """从yaml配置文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # 设置is_debug配置，默认为True
                self.is_debug = config.get('isDebug', True)
        except Exception as e:
            # 如果读取配置文件失败，设置默认值
            print(f"警告: 无法读取配置文件 {self.config_file}: {e}")
            self.is_debug = True
    
    def get_system_info(self):
        """获取系统信息"""
        return {
            'system': self.system,
            'project_root': self.project_root,
            'media_base_dir': self.media_base_dir,
            'content_file': self.content_file,
            'article_id_file': self.article_id_file,
            'is_debug': self.is_debug
        }