#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加测试数据来验证导出功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from result_database_new import ResultDatabase
import hashlib
from datetime import datetime

def add_test_data():
    """添加测试数据到结果数据库"""
    print("开始添加测试数据...")
    
    # 初始化数据库
    result_db = ResultDatabase('data/analysis_results.db')
    
    # 测试数据
    test_cases = [
        {
            'title': '某科技公司涉嫌财务造假被立案调查',
            'content': '据监管部门消息，某知名科技公司因涉嫌财务造假被立案调查，可能虚增收入约15亿元，面临重大处罚风险。该公司股价应声下跌，投资者损失惨重。',
            'source': '财经时报',
            'publish_time': '2025-01-27 10:30:00'
        },
        {
            'title': '新能源企业获得重大技术突破',
            'content': '某新能源公司在电池技术领域取得重大突破，新技术可将电池续航能力提升50%，获得多项国际专利认证，预计将带来显著的市场优势和业绩提升。',
            'source': '科技日报',
            'publish_time': '2025-01-27 11:15:00'
        },
        {
            'title': '生物医药公司药物试验失败',
            'content': '某生物医药公司的三期临床试验宣告失败，新药未能达到预期疗效指标，研发投入面临损失风险，公司股价大幅下跌，投资者信心受挫。',
            'source': '医药观察',
            'publish_time': '2025-01-27 12:00:00'
        }
    ]
    
    saved_count = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n正在添加第 {i+1} 条测试数据: {test_case['title']}")
        
        content_text = test_case['content']
        
        # 生成摘要和重复度检测
        summary = content_text[:150] + "..." if len(content_text) > 150 else content_text
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        duplicate_id = f"hash_{content_hash[:8]}"
        
        # 模拟分析结果
        if '造假' in content_text or '失败' in content_text:
            sentiment_level = '负面二级（显著风险）'
            sentiment_reason = '文本包含财务造假、试验失败等负面信息，对企业经营和投资者利益造成显著风险。'
        elif '突破' in content_text or '提升' in content_text:
            sentiment_level = '正面'
            sentiment_reason = '文本提到技术突破、性能提升等正面信息，对企业发展前景有积极影响。'
        else:
            sentiment_level = '中性'
            sentiment_reason = '文本内容相对中性，无明显正面或负面倾向。'
        
        # 构建标签结果
        tag_results_dict = {}
        tag_names = [
            "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
            "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
            "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
        ]
        
        # 模拟标签匹配
        for tag_name in tag_names:
            if tag_name == "重大违法违规" and '造假' in content_text:
                tag_results_dict[tag_name] = {
                    'belongs': True,
                    'reason': '文本明确提到财务造假和立案调查，属于重大违法违规行为。'
                }
            elif tag_name == "收入与成本" and '造假' in content_text:
                tag_results_dict[tag_name] = {
                    'belongs': True,
                    'reason': '涉及虚增收入，直接关联收入与成本真实性问题。'
                }
            elif tag_name == "研发与技术" and '技术' in content_text:
                tag_results_dict[tag_name] = {
                    'belongs': True,
                    'reason': '文本涉及技术突破和专利认证，属于研发与技术范畴。'
                }
            elif tag_name == "市场传闻与负面报道" and ('下跌' in content_text or '失败' in content_text):
                tag_results_dict[tag_name] = {
                    'belongs': True,
                    'reason': '文本报道了股价下跌、试验失败等负面消息。'
                }
            else:
                tag_results_dict[tag_name] = {
                    'belongs': False,
                    'reason': '文本内容与该标签不匹配。'
                }
        
        # 构建保存数据
        save_data = {
            'original_id': i + 1,  # 使用序号
            'title': test_case['title'],
            'content': content_text,
            'summary': summary,
            'source': test_case['source'],
            'publish_time': test_case['publish_time'],
            'sentiment_level': sentiment_level,
            'sentiment_reason': sentiment_reason,
            'companies': '',  # 暂不识别具体企业名称
            'duplicate_id': duplicate_id,
            'duplication_rate': 0.0,
            'processing_time': 800 + i * 100,  # 模拟处理时间
            'tag_results': tag_results_dict
        }
        
        # 保存到数据库
        save_result = result_db.save_analysis_result(save_data)
        
        if save_result['success']:
            saved_count += 1
            print(f"✓ 数据保存成功，ID: {save_result['id']}")
        else:
            print(f"✗ 数据保存失败: {save_result['message']}")
    
    print(f"\n测试数据添加完成，成功添加 {saved_count} 条数据")
    
    # 验证数据
    print("\n验证添加的数据...")
    results = result_db.get_analysis_results(page=1, page_size=10)
    
    if results['success']:
        print(f"✓ 数据库中共有 {results['total']} 条记录")
        
        for i, result in enumerate(results['data']):
            print(f"\n第 {i+1} 条记录:")
            print(f"  原始ID: {result['original_id']}")
            print(f"  标题: {result['title']}")
            print(f"  情感等级: {result['sentiment_level']}")
            print(f"  重复ID: {result['duplicate_id']}")
            
            # 统计匹配的标签
            matched_tags = []
            for tag_name in tag_names:
                if result.get(f'tag_{tag_name}') == '是':
                    matched_tags.append(tag_name)
            
            if matched_tags:
                print(f"  匹配标签: {', '.join(matched_tags)}")
            else:
                print("  匹配标签: 无")
    else:
        print(f"✗ 数据验证失败: {results.get('message', '未知错误')}")
    
    print("\n测试数据准备完成，可以进行导出测试了！")

if __name__ == "__main__":
    add_test_data()
