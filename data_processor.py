"""
数据处理器模块
负责处理CSV文件上传、数据分析和结果输出
"""

import pandas as pd
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from text_deduplicator import DuplicateDetectionManager
from ali_llm_client import AliLLMClient


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化数据处理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.llm_client = AliLLMClient()
        self.deduplicator = DuplicateDetectionManager({
            'similarity_threshold': 0.85,
            'hamming_threshold': 4
        })
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 存储已处理的数据
        self.processed_data = {}
        self.duplicate_groups = {}
    
    def process_csv_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        处理CSV文件上传
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            处理结果
        """
        try:
            # 保存文件
            file_path = os.path.join(self.data_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 验证数据格式
            if 'content' not in df.columns:
                return {
                    "success": False,
                    "error": "CSV文件必须包含'content'列",
                    "filename": filename
                }
            
            # 数据预处理
            df = self._preprocess_dataframe(df)
            
            # 文本去重处理
            df = self._process_duplicates(df)
            
            # 保存处理后的数据
            processed_filename = f"processed_{filename}"
            processed_path = os.path.join(self.data_dir, processed_filename)
            df.to_csv(processed_path, index=False)
            
            # 存储处理结果
            self.processed_data[filename] = {
                "file_path": processed_path,
                "total_rows": len(df),
                "unique_rows": len(df[df['is_duplicate'] == False]),
                "duplicate_rows": len(df[df['is_duplicate'] == True]),
                "duplicate_groups": len(df['duplicate_group'].dropna().unique()),
                "processed_time": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "filename": filename,
                "total_rows": len(df),
                "unique_rows": len(df[df['is_duplicate'] == False]),
                "duplicate_rows": len(df[df['is_duplicate'] == True]),
                "duplicate_groups": len(df['duplicate_group'].dropna().unique()),
                "message": f"文件上传成功，共处理{len(df)}行数据"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"文件处理失败: {str(e)}",
                "filename": filename
            }
    
    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        预处理数据框
        
        Args:
            df: 原始数据框
            
        Returns:
            预处理后的数据框
        """
        # 添加唯一ID
        df['text_id'] = [f"text_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(df))]
        
        # 清理内容列
        df['content'] = df['content'].fillna('').astype(str)
        
        # 添加发布时间列（如果没有的话）
        if 'publish_time' not in df.columns:
            df['publish_time'] = datetime.now()
        else:
            # 尝试解析时间
            try:
                df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
                df['publish_time'] = df['publish_time'].fillna(datetime.now())
            except:
                df['publish_time'] = datetime.now()
        
        # 添加文本长度列
        df['content_length'] = df['content'].str.len()
        
        return df
    
    def _process_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理文本重复
        
        Args:
            df: 数据框
            
        Returns:
            处理重复后的数据框
        """
        # 准备数据用于重复检测
        texts_for_detection = []
        for idx, row in df.iterrows():
            texts_for_detection.append({
                'id': row['text_id'],
                'content': row['content'],
                'publish_time': row.get('publish_time', '')
            })
        
        # 执行批量重复检测
        duplicated_results = self.deduplicator.detect_duplicates(texts_for_detection)
        
        # 将结果映射回数据框
        result_map = {item['id']: item for item in duplicated_results}
        
        # 初始化去重相关列
        df['is_duplicate'] = False
        df['duplicate_with'] = None
        df['duplicate_group'] = None
        df['similarity_score'] = 0.0
        df['hamming_distance'] = None
        df['simhash_value'] = None
        
        # 更新数据框
        for idx, row in df.iterrows():
            text_id = row['text_id']
            if text_id in result_map:
                result = result_map[text_id]
                df.at[idx, 'is_duplicate'] = result['is_duplicate']
                df.at[idx, 'duplicate_with'] = result['duplicate_id'] if result['duplicate_id'] != '无' else None
                df.at[idx, 'duplicate_group'] = f"group_{result['duplicate_id']}" if result['duplicate_id'] != '无' else None
                df.at[idx, 'similarity_score'] = result['duplication_rate']
                df.at[idx, 'hamming_distance'] = result.get('hamming_distance')
                df.at[idx, 'simhash_value'] = result.get('simhash_value')
        
        return df
    
    def analyze_sentiment_batch(self, batch_size: int = 10, start_index: int = 0) -> Dict[str, Any]:
        """
        批量分析情感
        
        Args:
            batch_size: 批处理大小
            start_index: 起始索引
            
        Returns:
            分析结果
        """
        try:
            # 获取已处理的数据
            if not self.processed_data:
                return {
                    "success": False,
                    "error": "没有可分析的数据，请先上传CSV文件"
                }
            
            # 获取第一个处理过的文件
            filename = list(self.processed_data.keys())[0]
            file_path = self.processed_data[filename]["file_path"]
            
            # 读取数据
            df = pd.read_csv(file_path)
            
            # 只分析非重复的文本
            unique_df = df[df['is_duplicate'] == False].copy()
            
            if len(unique_df) == 0:
                return {
                    "success": False,
                    "error": "没有找到非重复的文本进行分析"
                }
            
            # 计算批处理范围
            end_index = min(start_index + batch_size, len(unique_df))
            batch_df = unique_df.iloc[start_index:end_index]
            
            results = []
            
            for idx, row in batch_df.iterrows():
                try:
                    # 分析单条文本
                    analysis_result = self._analyze_single_text(row)
                    results.append({
                        "text_id": row['text_id'],
                        "content_preview": row['content'][:100] + "..." if len(row['content']) > 100 else row['content'],
                        "analysis": analysis_result,
                        "duplicate_info": {
                            "is_duplicate": row['is_duplicate'],
                            "similarity_score": row['similarity_score'],
                            "hamming_distance": row['hamming_distance'],
                            "duplicate_group": row['duplicate_group']
                        }
                    })
                except Exception as e:
                    results.append({
                        "text_id": row['text_id'],
                        "content_preview": row['content'][:100] + "..." if len(row['content']) > 100 else row['content'],
                        "analysis": {"error": f"分析失败: {str(e)}"},
                        "duplicate_info": {
                            "is_duplicate": row['is_duplicate'],
                            "similarity_score": row['similarity_score'],
                            "hamming_distance": row['hamming_distance'],
                            "duplicate_group": row['duplicate_group']
                        }
                    })
            
            return {
                "success": True,
                "total": len(unique_df),
                "analyzed": len(results),
                "start_index": start_index,
                "end_index": end_index,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"批量分析失败: {str(e)}"
            }
    
    def _analyze_single_text(self, row: pd.Series) -> Dict[str, Any]:
        """
        分析单条文本
        
        Args:
            row: 数据行
            
        Returns:
            分析结果
        """
        content = row['content']
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(content)
        
        # 调用LLM进行分析
        response = self.llm_client.analyze_sentiment(prompt)
        
        # 解析响应
        analysis_result = self._parse_analysis_response(response)
        
        return analysis_result
    
    def _build_analysis_prompt(self, content: str) -> str:
        """
        构建分析提示词
        
        Args:
            content: 文本内容
            
        Returns:
            提示词
        """
        prompt = f"""
请对以下新闻文本进行全面的舆情分析，包括：

1. 新闻摘要：提取核心信息，总结主要事件
2. 涉及企业：识别文本中提到的企业名称
3. 标签识别：根据标签体系进行分类标注
4. 情感等级：判断风险等级

文本内容：
{content}

请按照以下格式返回分析结果：
{{
    "summary": "新闻摘要",
    "companies": ["企业1", "企业2"],
    "tags": ["标签1", "标签2"],
    "sentiment_level": {{
        "level": "情感等级",
        "reason": "分析原因"
    }}
}}

请确保分析准确、客观，标签识别要严格按照标签体系进行。
"""
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        解析分析响应
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的结果
        """
        try:
            # 尝试解析JSON响应
            import json
            result = json.loads(response)
            return result
        except:
            # 如果解析失败，返回原始响应
            return {
                "summary": "解析失败",
                "companies": [],
                "tags": [],
                "sentiment_level": {
                    "level": "未知",
                    "reason": response
                }
            }
    
    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """
        获取重复文本统计信息
        
        Returns:
            统计信息
        """
        return self.deduplicator.get_statistics()
    
    def get_duplicate_groups(self) -> Dict[str, Any]:
        """
        获取重复文本组信息
        
        Returns:
            重复组信息
        """
        return self.deduplicator.get_all_duplicates()
    
    def get_duplicate_info(self, text_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定文本的重复信息
        
        Args:
            text_id: 文本ID
            
        Returns:
            重复信息
        """
        return self.deduplicator.get_duplicate_info(text_id)
    
    def export_results(self, filename: str = None) -> str:
        """
        导出分析结果
        
        Args:
            filename: 导出文件名
            
        Returns:
            导出文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sentiment_analysis_results_{timestamp}.csv"
        
        export_path = os.path.join(self.data_dir, filename)
        
        # 获取所有处理过的数据
        all_results = []
        for filename, info in self.processed_data.items():
            file_path = info["file_path"]
            df = pd.read_csv(file_path)
            
            # 添加文件名标识
            df['source_file'] = filename
            all_results.append(df)
        
        if all_results:
            # 合并所有结果
            combined_df = pd.concat(all_results, ignore_index=True)
            
            # 导出到CSV
            combined_df.to_csv(export_path, index=False, encoding='utf-8-sig')
            
            return export_path
        else:
            raise ValueError("没有可导出的数据")
    
    def get_data_info(self) -> Dict[str, Any]:
        """
        获取数据基本信息
        
        Returns:
            数据信息
        """
        if not self.processed_data:
            return {
                "total_records": 0,
                "columns": [],
                "sample_data": []
            }
        
        # 获取第一个文件的信息
        filename = list(self.processed_data.keys())[0]
        file_path = self.processed_data[filename]["file_path"]
        
        df = pd.read_csv(file_path)
        
        return {
            "total_records": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(5).to_dict('records')
        }
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息
        """
        if not self.processed_data:
            return {
                "total_records": 0,
                "columns": [],
                "time_statistics": {},
                "sample_titles": []
            }
        
        # 获取第一个文件的信息
        filename = list(self.processed_data.keys())[0]
        file_path = self.processed_data[filename]["file_path"]
        
        df = pd.read_csv(file_path)
        
        # 时间统计
        time_stats = {}
        if 'publish_time' in df.columns:
            try:
                df['publish_time'] = pd.to_datetime(df['publish_time'])
                time_stats = {
                    "earliest": df['publish_time'].min().strftime("%Y-%m-%d"),
                    "latest": df['publish_time'].max().strftime("%Y-%m-%d")
                }
            except:
                time_stats = {"earliest": "未知", "latest": "未知"}
        
        # 重复统计
        duplicate_stats = {
            "total_texts": len(df),
            "unique_texts": len(df[df['is_duplicate'] == False]),
            "duplicate_texts": len(df[df['is_duplicate'] == True]),
            "duplicate_groups": len(df['duplicate_group'].dropna().unique()),
            "average_similarity": df['similarity_score'].mean() if 'similarity_score' in df.columns else 0
        }
        
        return {
            "total_records": len(df),
            "columns": list(df.columns),
            "time_statistics": time_stats,
            "duplicate_statistics": duplicate_stats,
            "sample_titles": df['content'].head(5).str[:50].tolist() if 'content' in df.columns else []
        } 