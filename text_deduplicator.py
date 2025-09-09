"""
基于SimHash的文本去重系统
实现参考阿里云PAI和海量数据相似度计算的最佳实践
"""

import hashlib
import re
import jieba
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
from datetime import datetime
import json
import redis
import logging

logger = logging.getLogger(__name__)

class SimHash:
    """SimHash算法实现"""
    
    def __init__(self, text: str, window_size: int = 6, hash_bits: int = 64):
        """
        初始化SimHash
        
        Args:
            text: 输入文本
            window_size: 滑动窗口大小，用于生成特征子串
            hash_bits: hash位数，默认64位
        """
        self.hash_bits = hash_bits
        self.window_size = window_size
        self.value = self._calculate_simhash(text)
    
    def _calculate_simhash(self, text: str) -> int:
        """计算文本的SimHash值"""
        # 文本预处理和分词
        tokens = self._tokenize(text)
        
        # 生成特征子串
        features = self._generate_features(tokens)
        
        # 计算权重向量
        weights = [0] * self.hash_bits
        
        for feature, count in features.items():
            # 计算特征的hash值
            feature_hash = hashlib.md5(feature.encode('utf-8')).hexdigest()
            feature_int = int(feature_hash, 16)
            
            # 对每一位进行加权
            for i in range(self.hash_bits):
                bit = (feature_int >> i) & 1
                if bit:
                    weights[i] += count
                else:
                    weights[i] -= count
        
        # 生成最终的SimHash值
        simhash_value = 0
        for i in range(self.hash_bits):
            if weights[i] > 0:
                simhash_value |= (1 << i)
        
        return simhash_value
    
    def _tokenize(self, text: str) -> List[str]:
        """文本分词和清理"""
        # 清理HTML标签和特殊字符
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 中文分词
        tokens = list(jieba.cut(text))
        
        # 过滤停用词和短词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        tokens = [token.strip() for token in tokens if len(token.strip()) > 1 and token.strip() not in stopwords]
        
        return tokens
    
    def _generate_features(self, tokens: List[str]) -> Dict[str, int]:
        """生成特征子串"""
        features = Counter()
        
        # 生成n-gram特征
        for i in range(len(tokens) - self.window_size + 1):
            window = tokens[i:i + self.window_size]
            feature = ''.join(window)
            features[feature] += 1
        
        # 如果tokens太短，使用单词作为特征
        if len(tokens) < self.window_size:
            for token in tokens:
                features[token] += 1
        
        return dict(features)
    
    def distance(self, other: 'SimHash') -> int:
        """计算汉明距离"""
        return bin(self.value ^ other.value).count('1')
    
    def __str__(self):
        return f"SimHash({hex(self.value)})"


class TextDeduplicator:
    """文本去重器"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,
                 hamming_threshold: int = 4,
                 num_blocks: int = 4,
                 use_redis: bool = False,
                 redis_config: Optional[Dict] = None):
        """
        初始化文本去重器
        
        Args:
            similarity_threshold: 相似度阈值
            hamming_threshold: 汉明距离阈值
            num_blocks: SimHash分块数量
            use_redis: 是否使用Redis存储索引
            redis_config: Redis配置
        """
        self.similarity_threshold = similarity_threshold
        self.hamming_threshold = hamming_threshold
        self.num_blocks = num_blocks
        self.use_redis = use_redis
        
        # 存储文本和SimHash值
        self.text_storage = {}  # text_id -> {'text': str, 'simhash': SimHash, 'publish_time': str}
        self.simhash_index = defaultdict(list)  # simhash_fragment -> [(text_id, simhash_value)]
        
        # Redis连接
        self.redis_client = None
        if use_redis and redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败: {e}")
                self.use_redis = False
    
    def add_text(self, text_id: str, text: str, publish_time: str = None) -> Dict[str, Any]:
        """
        添加文本到去重系统
        
        Args:
            text_id: 文本唯一标识
            text: 文本内容
            publish_time: 发布时间
            
        Returns:
            包含去重结果的字典
        """
        if publish_time is None:
            publish_time = datetime.now().isoformat()
        
        # 生成SimHash
        simhash = self.generate_simhash(text)
        
        # 查找相似文本
        similar_texts = self._find_similar_texts(simhash)
        
        # 存储文本信息
        self.text_storage[text_id] = {
            'text': text,
            'simhash': simhash,
            'publish_time': publish_time
        }
        
        # 更新索引
        self._update_index(text_id, simhash)
        
        # 构建返回结果
        if similar_texts:
            # 找到最相似的文本
            best_match = min(similar_texts, key=lambda x: x[1])  # 按汉明距离排序
            similar_text_id, hamming_distance = best_match
            
            # 计算相似度
            similarity = 1 - (hamming_distance / 64)  # 64是SimHash的位数
            
            return {
                'is_duplicate': similarity >= self.similarity_threshold,
                'duplicate_with': similar_text_id,
                'duplicate_group': f"group_{similar_text_id}",
                'similarity': similarity,
                'hamming_distance': hamming_distance,
                'simhash_value': hex(simhash.value)[2:].zfill(16)  # 去掉0x前缀，补齐16位
            }
        else:
            return {
                'is_duplicate': False,
                'duplicate_with': None,
                'duplicate_group': None,
                'similarity': 1.0,
                'hamming_distance': 0,
                'simhash_value': hex(simhash.value)[2:].zfill(16)  # 去掉0x前缀，补齐16位
            }
    
    def generate_simhash(self, text: str) -> SimHash:
        """生成文本的SimHash"""
        return SimHash(text, window_size=6)
    
    def _find_similar_texts(self, simhash: SimHash) -> List[Tuple[str, int]]:
        """查找相似文本"""
        similar_texts = []
        simhash_value = simhash.value
        
        # 生成SimHash分片用于索引查找
        fragments = self._generate_fragments(simhash_value)
        
        # 候选文本集合
        candidates = set()
        
        # 从每个分片索引中查找候选文本
        for fragment in fragments:
            if self.use_redis and self.redis_client:
                # 从Redis中查找
                redis_key = f"simhash_index:{fragment}"
                candidate_list = self.redis_client.lrange(redis_key, 0, -1)
                for candidate_data in candidate_list:
                    candidate_info = json.loads(candidate_data.decode('utf-8'))
                    candidates.add(candidate_info['text_id'])
            else:
                # 从内存索引中查找
                for text_id, _ in self.simhash_index[fragment]:
                    candidates.add(text_id)
        
        # 计算候选文本的汉明距离
        for candidate_id in candidates:
            if candidate_id in self.text_storage:
                candidate_simhash = self.text_storage[candidate_id]['simhash']
                hamming_distance = simhash.distance(candidate_simhash)
                
                # 如果汉明距离小于阈值，认为是相似文本
                if hamming_distance <= self.hamming_threshold:
                    similar_texts.append((candidate_id, hamming_distance))
        
        return similar_texts
    
    def _generate_fragments(self, simhash_value: int) -> List[str]:
        """生成SimHash分片"""
        fragments = []
        bits_per_fragment = 64 // self.num_blocks
        
        for i in range(self.num_blocks):
            start_bit = i * bits_per_fragment
            fragment_mask = (1 << bits_per_fragment) - 1
            fragment = (simhash_value >> start_bit) & fragment_mask
            fragments.append(f"block_{i}_{fragment:016x}")
        
        return fragments
    
    def _update_index(self, text_id: str, simhash: SimHash):
        """更新索引"""
        simhash_value = simhash.value
        fragments = self._generate_fragments(simhash_value)
        
        for fragment in fragments:
            if self.use_redis and self.redis_client:
                # 存储到Redis
                redis_key = f"simhash_index:{fragment}"
                index_data = {
                    'text_id': text_id,
                    'simhash_value': hex(simhash_value)[2:].zfill(16),  # 去掉0x前缀，补齐16位
                    'timestamp': datetime.now().isoformat()
                }
                self.redis_client.lpush(redis_key, json.dumps(index_data))
                
                # 设置过期时间（7天）
                self.redis_client.expire(redis_key, 7 * 24 * 3600)
            else:
                # 存储到内存索引
                self.simhash_index[fragment].append((text_id, simhash_value))
    
    def get_duplicate_info(self, text_id: str) -> Optional[Dict]:
        """获取文本的重复信息"""
        if text_id in self.text_storage:
            return self.text_storage[text_id]
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取去重统计信息"""
        return {
            'total_texts': len(self.text_storage),
            'index_fragments': len(self.simhash_index),
            'hamming_threshold': self.hamming_threshold,
            'similarity_threshold': self.similarity_threshold,
            'use_redis': self.use_redis
        }


class DuplicateDetectionManager:
    """重复检测管理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化重复检测管理器
        
        Args:
            config: 配置字典
        """
        default_config = {
            'similarity_threshold': 0.85,
            'hamming_threshold': 4,
            'num_blocks': 4,
            'use_redis': False,
            'redis_config': None
        }
        
        self.config = {**default_config, **(config or {})}
        self.deduplicator = TextDeduplicator(**self.config)
    
    def detect_duplicates(self, texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量检测重复文本
        
        Args:
            texts: 文本列表，每个元素包含id和content字段
            
        Returns:
            包含重复检测结果的文本列表
        """
        results = []
        
        for text_item in texts:
            text_id = str(text_item.get('id', ''))
            content = text_item.get('content', '')
            publish_time = text_item.get('publish_time', '')
            
            if not content:
                # 内容为空的情况
                result = {
                    **text_item,
                    'duplicate_id': '0000000000000000',  # 空内容的默认simhash值
                    'duplication_rate': 0.0,
                    'hamming_distance': None,
                    'simhash_value': '0000000000000000',  # 空内容的默认simhash值
                    'is_duplicate': False
                }
            else:
                # 执行重复检测
                duplicate_result = self.deduplicator.add_text(
                    text_id=text_id,
                    text=content,
                    publish_time=publish_time
                )
                
                # 构建结果
                result = {
                    **text_item,
                    'duplicate_id': duplicate_result['simhash_value'],  # 改为simhash值
                    'duplication_rate': round(duplicate_result['similarity'], 3),  # 保持相似度
                    'hamming_distance': duplicate_result['hamming_distance'],
                    'simhash_value': duplicate_result['simhash_value'],
                    'is_duplicate': duplicate_result['is_duplicate']
                }
            
            results.append(result)
        
        return results


# 使用示例
if __name__ == "__main__":
    # 创建重复检测管理器
    manager = DuplicateDetectionManager({
        'similarity_threshold': 0.7,
        'hamming_threshold': 10
    })
    
    # 测试数据
    test_texts = [
        {
            'id': 1,
            'content': '中原环保股份有限公司2025年度第一期科技创新债券成功发行。本次票据发行规模5亿元，发行期限5年，票面利率2.46%',
            'title': '郑州科创债发行实现"零的突破"'
        },
        {
            'id': 2,
            'content': '宜城市委副书记、市长肖平，宜城市委常委、副市长蒋代刚会同襄阳市经信局副局长冯晓濮，带队赴成都云图控股股份有限公司开展招商引资活动',
            'title': '宜城市招商专班赴成都开展招商引资活动'
        },
        {
            'id': 3,
            'content': '中原环保公司2025年度第一期科技创新债券成功发行。这次票据发行规模5亿元，发行期限5年，票面利率2.46%',
            'title': '郑州科创债发行取得突破'
        }
    ]
    
    # 执行重复检测
    results = manager.detect_duplicates(test_texts)
    
    # 输出结果
    for result in results:
        print(f"ID: {result['id']}")
        print(f"标题: {result['title']}")
        print(f"重复ID: {result['duplicate_id']}")
        print(f"重复度: {result['duplication_rate']}")
        print(f"汉明距离: {result['hamming_distance']}")
        print(f"SimHash: {result['simhash_value']}")
        print("-" * 50)
