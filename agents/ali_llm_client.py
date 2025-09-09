import os
import json
import logging
import aiohttp
import time
from typing import Dict, Any, Optional, List
from config import Config

logger = logging.getLogger(__name__)

class AliLLMClient:
    """阿里云大模型API客户端"""
    
    def __init__(self):
        """初始化客户端"""
        self.api_key = Config.ALI_API_KEY
        self.base_url = Config.ALI_BASE_URL
        self.model = Config.ALI_MODEL_NAME
        self.timeout = 30  # 默认超时时间30秒
    
    async def generate_response(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """
        生成回复
        
        Args:
            prompt: 提示词
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            
        Returns:
            生成的回复文本
        """
        try:
            # 构建请求参数
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的IPO风险评估专家，负责分析文本的情感等级。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # 发送请求
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # 使用兼容模式API
                api_url = f"{self.base_url}/chat/completions"
                
                async with session.post(
                    api_url,
                    headers=headers,
                    json=request_data,
                    timeout=self.timeout
                ) as response:
                    response_data = await response.json()
                    
                    # 记录响应时间
                    elapsed_time = time.time() - start_time
                    logger.debug(f"LLM响应时间: {elapsed_time:.2f}秒")
                    
                    # 处理错误
                    if response.status != 200:
                        error_msg = response_data.get("error", {}).get("message", "未知错误")
                        logger.error(f"LLM API错误 ({response.status}): {error_msg}")
                        raise Exception(f"LLM API错误: {error_msg}")
                    
                    # 提取生成的文本
                    try:
                        generated_text = response_data["choices"][0]["message"]["content"]
                        return generated_text
                    except (KeyError, IndexError) as e:
                        logger.error(f"解析LLM响应失败: {str(e)}, 响应: {response_data}")
                        raise Exception(f"解析LLM响应失败: {str(e)}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"LLM API请求失败: {str(e)}")
            raise Exception(f"LLM API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}")
            raise Exception(f"LLM生成失败: {str(e)}")
