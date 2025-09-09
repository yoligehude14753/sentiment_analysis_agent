#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON转Excel转换器
将JSON文件转换为Excel格式
"""

import json
import pandas as pd
import os
from datetime import datetime

def json_to_excel(json_file_path, excel_file_path=None):
    """
    将JSON文件转换为Excel文件
    
    Args:
        json_file_path (str): JSON文件路径
        excel_file_path (str): 输出Excel文件路径，如果为None则自动生成
    """
    try:
        print(f"正在读取JSON文件: {json_file_path}")
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"JSON文件读取成功，数据条数: {len(data)}")
        
        # 如果数据是列表，直接转换为DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        # 如果数据是字典，尝试提取主要数据
        elif isinstance(data, dict):
            # 查找包含数据的键
            data_keys = [k for k, v in data.items() if isinstance(v, list) and len(v) > 0]
            if data_keys:
                print(f"找到数据键: {data_keys}")
                # 使用第一个包含数据的键
                df = pd.DataFrame(data[data_keys[0]])
                print(f"使用键 '{data_keys[0]}' 的数据，共 {len(df)} 行")
            else:
                # 如果没有找到列表数据，将整个字典转换为单行DataFrame
                df = pd.DataFrame([data])
        else:
            raise ValueError("不支持的数据格式")
        
        # 生成Excel文件名
        if excel_file_path is None:
            base_name = os.path.splitext(os.path.basename(json_file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file_path = f"exports/{base_name}_{timestamp}.xlsx"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(excel_file_path), exist_ok=True)
        
        print(f"正在转换为Excel格式...")
        print(f"数据列数: {len(df.columns)}")
        print(f"数据行数: {len(df)}")
        
        # 显示列名
        print(f"列名: {list(df.columns)}")
        
        # 转换为Excel
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='数据', index=False)
            
            # 创建数据概览sheet
            overview_data = {
                '统计信息': [
                    f'总行数: {len(df)}',
                    f'总列数: {len(df.columns)}',
                    f'转换时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    f'源文件: {json_file_path}'
                ]
            }
            overview_df = pd.DataFrame(overview_data)
            overview_df.to_excel(writer, sheet_name='概览', index=False)
        
        print(f"转换完成！Excel文件已保存到: {excel_file_path}")
        print(f"文件大小: {os.path.getsize(excel_file_path) / 1024 / 1024:.2f} MB")
        
        return excel_file_path
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    # JSON文件路径
    json_file = r"C:\sentiment-analysis-agent\exports\auto_export_after_dedup_20250827_124804.json"
    
    # 检查文件是否存在
    if not os.path.exists(json_file):
        print(f"错误: 文件不存在: {json_file}")
        return
    
    # 转换为Excel
    excel_file = json_to_excel(json_file)
    
    if excel_file:
        print(f"\n✅ 转换成功！")
        print(f"📁 Excel文件位置: {excel_file}")
        print(f"🔍 请检查输出目录: {os.path.dirname(excel_file)}")
    else:
        print("❌ 转换失败！")

if __name__ == "__main__":
    main()


















