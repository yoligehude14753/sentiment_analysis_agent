#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV数据导入脚本
用于将舆情数据CSV文件导入到SQLite数据库中
"""

import os
import sys
from database_manager import UnifiedDatabaseManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    # CSV文件路径
    csv_path = r"C:\Users\anyut\Desktop\建投需求\舆情解析\舆情数据.csv"
    
    # 检查文件是否存在
    if not os.path.exists(csv_path):
        logger.error(f"CSV文件不存在: {csv_path}")
        print(f"错误：CSV文件不存在: {csv_path}")
        print("请检查文件路径是否正确")
        return
    
    try:
        # 初始化统一数据库管理器
        logger.info("初始化数据库...")
        db_manager = UnifiedDatabaseManager()
        
        # 获取舆情数据库
        sentiment_db = db_manager.get_sentiment_database()
        
        # 导入CSV数据
        logger.info(f"开始导入CSV数据: {csv_path}")
        result = sentiment_db.import_csv_data(csv_path, chunk_size=1000)
        
        if result['success']:
            logger.info("数据导入成功!")
            print("=" * 50)
            print("数据导入成功!")
            print(f"总行数: {result['total_rows']}")
            print(f"成功导入: {result['imported']}")
            print(f"跳过行数: {result['skipped']}")
            print(f"消息: {result['message']}")
            print("=" * 50)
            
            # 显示统计信息
            logger.info("获取数据统计信息...")
            stats = sentiment_db.get_statistics()
            
            if stats['success']:
                print("\n数据统计信息:")
                print(f"总记录数: {stats['statistics']['total_records']}")
                
                if stats['statistics']['sentiment_distribution']:
                    print("\n情感等级分布:")
                    for level, count in stats['statistics']['sentiment_distribution'].items():
                        print(f"  {level}: {count}")
                
                if stats['statistics']['industry_distribution']:
                    print("\n行业分布 (前10):")
                    for industry, count in stats['statistics']['industry_distribution'].items():
                        print(f"  {industry}: {count}")
                
                if stats['statistics']['company_distribution']:
                    print("\n公司分布 (前10):")
                    for company, count in stats['statistics']['company_distribution'].items():
                        print(f"  {company}: {count}")
            
        else:
            logger.error(f"数据导入失败: {result['message']}")
            print(f"错误：数据导入失败: {result['message']}")
            if 'error' in result:
                print(f"详细错误: {result['error']}")
    
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        print(f"程序执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
