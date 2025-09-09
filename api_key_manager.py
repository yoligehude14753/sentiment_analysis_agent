import os
import json
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class APIKeyManager:
    """API密钥管理器 - 安全地处理API密钥的输入、验证和存储"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.key_file = self.config_dir / ".api_keys"
        self.cipher_key_file = self.config_dir / ".cipher_key"
        
    def _get_cipher_key(self):
        """获取或创建加密密钥"""
        if self.cipher_key_file.exists():
            with open(self.cipher_key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.cipher_key_file, 'wb') as f:
                f.write(key)
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.cipher_key_file, 0o600)
            return key
    
    def _encrypt_data(self, data):
        """加密数据"""
        key = self._get_cipher_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data):
        """解密数据"""
        try:
            key = self._get_cipher_key()
            f = Fernet(key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return None
    
    def save_api_key(self, api_key, provider="dashscope"):
        """保存API密钥（加密存储）"""
        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")
        
        # 验证API密钥格式
        if provider == "dashscope" and not api_key.startswith("sk-"):
            raise ValueError("阿里云DashScope API密钥格式错误，应该以'sk-'开头")
        
        # 加密存储
        encrypted_key = self._encrypt_data(api_key.strip())
        
        config_data = {}
        if self.key_file.exists():
            try:
                with open(self.key_file, 'r') as f:
                    config_data = json.load(f)
            except:
                config_data = {}
        
        config_data[provider] = {
            "key": encrypted_key,
            "hash": hashlib.sha256(api_key.strip().encode()).hexdigest()[:16]  # 用于验证
        }
        
        with open(self.key_file, 'w') as f:
            json.dump(config_data, f)
        
        # 设置文件权限（仅所有者可读写）
        os.chmod(self.key_file, 0o600)
        
        print(f"✅ {provider} API密钥已安全保存")
    
    def get_api_key(self, provider="dashscope"):
        """获取API密钥"""
        # 首先检查环境变量
        env_key = os.getenv("DASHSCOPE_API_KEY")
        if env_key and env_key.strip():
            return env_key.strip()
        
        # 然后检查加密存储的密钥
        if self.key_file.exists():
            try:
                with open(self.key_file, 'r') as f:
                    config_data = json.load(f)
                
                if provider in config_data:
                    encrypted_key = config_data[provider]["key"]
                    decrypted_key = self._decrypt_data(encrypted_key)
                    if decrypted_key:
                        return decrypted_key
            except:
                pass
        
        return None
    
    def is_api_key_configured(self, provider="dashscope"):
        """检查API密钥是否已配置"""
        return self.get_api_key(provider) is not None
    
    def validate_api_key(self, api_key, provider="dashscope"):
        """验证API密钥格式"""
        if not api_key or not api_key.strip():
            return False, "API密钥不能为空"
        
        if provider == "dashscope":
            if not api_key.startswith("sk-"):
                return False, "阿里云DashScope API密钥格式错误，应该以'sk-'开头"
            
            if len(api_key) < 20:
                return False, "API密钥长度过短"
        
        return True, "API密钥格式正确"
    
    def remove_api_key(self, provider="dashscope"):
        """删除API密钥"""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'r') as f:
                    config_data = json.load(f)
                
                if provider in config_data:
                    del config_data[provider]
                    
                    with open(self.key_file, 'w') as f:
                        json.dump(config_data, f)
                    
                    print(f"✅ {provider} API密钥已删除")
                    return True
            except:
                pass
        
        return False
    
    def get_key_status(self, provider="dashscope"):
        """获取密钥状态信息"""
        api_key = self.get_api_key(provider)
        if not api_key:
            return {
                "configured": False,
                "source": None,
                "masked_key": None
            }
        
        # 检查密钥来源
        env_key = os.getenv("DASHSCOPE_API_KEY")
        source = "environment" if env_key else "encrypted_storage"
        
        # 创建掩码显示
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else api_key[:4] + "*" * (len(api_key) - 4)
        
        return {
            "configured": True,
            "source": source,
            "masked_key": masked_key
        }

# 全局实例
api_key_manager = APIKeyManager()

def ensure_api_key_configured():
    """确保API密钥已配置，如果没有则提示用户输入"""
    if not api_key_manager.is_api_key_configured():
        print("\n" + "="*50)
        print("🔑 API密钥配置")
        print("="*50)
        print("检测到尚未配置阿里云DashScope API密钥")
        print("请访问 https://dashscope.aliyun.com/ 获取您的API密钥")
        print("\n选择配置方式：")
        print("1. 通过Web界面配置（推荐）")
        print("2. 通过命令行输入")
        print("3. 设置环境变量")
        
        choice = input("\n请选择配置方式 (1-3): ").strip()
        
        if choice == "1":
            print("\n请在Web界面的'配置'页面输入您的API密钥")
            print("启动应用后访问: http://localhost:8000/config")
            return False
        
        elif choice == "2":
            while True:
                api_key = input("\n请输入您的DashScope API密钥: ").strip()
                
                is_valid, message = api_key_manager.validate_api_key(api_key)
                if is_valid:
                    try:
                        api_key_manager.save_api_key(api_key)
                        print("✅ API密钥配置成功！")
                        return True
                    except Exception as e:
                        print(f"❌ 保存API密钥失败: {e}")
                else:
                    print(f"❌ {message}")
                    retry = input("是否重新输入？(y/n): ").strip().lower()
                    if retry != 'y':
                        break
        
        elif choice == "3":
            print("\n请设置环境变量：")
            print("Windows: set DASHSCOPE_API_KEY=your_api_key_here")
            print("Linux/Mac: export DASHSCOPE_API_KEY=your_api_key_here")
            print("或在.env文件中添加: DASHSCOPE_API_KEY=your_api_key_here")
            return False
        
        return False
    
    return True 