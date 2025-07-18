#!/usr/bin/env python3
"""
测试实体抽取智能体和关系抽取智能体的溯源信息输出

验证ECE和REE智能体是否正确输出source_sentence字段
"""

import json
import sys
from config import config
from agents.ece_agent import create_ece_agent
from agents.ree_agent import create_ree_agent


def test_ece_agent():
    """测试实体抽取智能体的source_sentence输出"""
    print("🧪 测试ECE智能体（实体抽取）...")
    
    # 获取LLM配置
    llm_config = config.llm_config_gpt4
    
    # 本体论示例
    ontology_json = """
    {
        "node_labels": ["人物", "机构", "技术", "时间"],
        "relationship_types": ["工作于", "发明", "研究", "发生于"]
    }
    """
    
    # 创建ECE智能体
    ece_agent = create_ece_agent(llm_config, ontology_json)
    
    # 测试文本
    test_text = """
    张三是北京大学的教授，专门研究人工智能。他在2020年发明了一种新的深度学习算法。
    李四在清华大学工作，专注于计算机视觉技术的研究。
    """
    
    print(f"📝 测试文本：{test_text}")
    
    try:
        # 调用智能体
        response = ece_agent.generate_reply(
            messages=[{"role": "user", "content": test_text}]
        )
        
        print(f"🤖 ECE智能体响应：{response}")
        
        # 解析JSON - 处理可能的markdown代码块包装
        json_text = response.strip()
        if json_text.startswith("```json"):
            # 移除markdown代码块标记
            json_text = json_text[7:]  # 移除 "```json"
            if json_text.endswith("```"):
                json_text = json_text[:-3]  # 移除结尾的 "```"
        elif json_text.startswith("```"):
            # 移除普通代码块标记
            json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
        
        json_text = json_text.strip()
        
        # 解析JSON
        entities = json.loads(json_text)
        
        # 验证结果
        validation_results = validate_ece_output(entities)
        
        if validation_results["success"]:
            print("✅ ECE智能体测试通过！")
            print(f"📊 提取了 {len(entities)} 个实体")
            for entity in entities:
                print(f"  - {entity['text']} ({entity['label']}) - 来源句子: {entity['source_sentence'][:50]}...")
        else:
            print("❌ ECE智能体测试失败！")
            for error in validation_results["errors"]:
                print(f"  ❗ {error}")
        
        return validation_results["success"], entities
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        print(f"响应内容: {response}")
        return False, []
    except Exception as e:
        print(f"❌ ECE智能体测试出错: {e}")
        return False, []


def test_ree_agent(entities):
    """测试关系抽取智能体的source_sentence输出"""
    print("\n🧪 测试REE智能体（关系抽取）...")
    
    if not entities:
        print("⚠️ 没有实体数据，跳过REE测试")
        return False
    
    # 获取LLM配置
    llm_config = config.llm_config_gpt4
    
    # 实体JSON字符串
    entities_json = json.dumps(entities, ensure_ascii=False)
    
    # 关系类型
    relationship_types = ["工作于", "发明", "研究", "发生于"]
    
    # 创建REE智能体
    ree_agent = create_ree_agent(llm_config, entities_json, relationship_types)
    
    # 测试文本（与ECE相同）
    test_text = """
    张三是北京大学的教授，专门研究人工智能。他在2020年发明了一种新的深度学习算法。
    李四在清华大学工作，专注于计算机视觉技术的研究。
    """
    
    print(f"📝 测试文本：{test_text}")
    print(f"🔗 输入实体：{len(entities)} 个")
    
    try:
        # 调用智能体
        response = ree_agent.generate_reply(
            messages=[{"role": "user", "content": test_text}]
        )
        
        print(f"🤖 REE智能体响应：{response}")
        
        # 解析JSON - 处理可能的markdown代码块包装
        json_text = response.strip()
        if json_text.startswith("```json"):
            # 移除markdown代码块标记
            json_text = json_text[7:]  # 移除 "```json"
            if json_text.endswith("```"):
                json_text = json_text[:-3]  # 移除结尾的 "```"
        elif json_text.startswith("```"):
            # 移除普通代码块标记
            json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
        
        json_text = json_text.strip()
        
        # 解析JSON
        relations = json.loads(json_text)
        
        # 验证结果
        validation_results = validate_ree_output(relations, entities)
        
        if validation_results["success"]:
            print("✅ REE智能体测试通过！")
            print(f"📊 提取了 {len(relations)} 个关系")
            for relation in relations:
                print(f"  - {relation['source_entity_id']} → {relation['target_entity_id']} ({relation['relationship_type']})")
                print(f"    来源句子: {relation['source_sentence'][:50]}...")
        else:
            print("❌ REE智能体测试失败！")
            for error in validation_results["errors"]:
                print(f"  ❗ {error}")
        
        return validation_results["success"]
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        print(f"响应内容: {response}")
        return False
    except Exception as e:
        print(f"❌ REE智能体测试出错: {e}")
        return False


def validate_ece_output(entities):
    """验证ECE智能体的输出格式"""
    errors = []
    
    if not isinstance(entities, list):
        errors.append("输出必须是列表格式")
        return {"success": False, "errors": errors}
    
    required_keys = ["text", "label", "unique_id", "source_sentence"]
    
    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            errors.append(f"实体 {i} 必须是字典格式")
            continue
        
        # 检查必需的键
        for key in required_keys:
            if key not in entity:
                errors.append(f"实体 {i} 缺少必需字段: {key}")
            elif not isinstance(entity[key], str) or not entity[key].strip():
                errors.append(f"实体 {i} 的字段 {key} 必须是非空字符串")
    
    return {"success": len(errors) == 0, "errors": errors}


def validate_ree_output(relations, entities):
    """验证REE智能体的输出格式"""
    errors = []
    
    if not isinstance(relations, list):
        errors.append("输出必须是列表格式")
        return {"success": False, "errors": errors}
    
    # 建立实体ID索引
    entity_ids = {entity["unique_id"] for entity in entities}
    
    required_keys = ["source_entity_id", "target_entity_id", "relationship_type", "source_sentence"]
    
    for i, relation in enumerate(relations):
        if not isinstance(relation, dict):
            errors.append(f"关系 {i} 必须是字典格式")
            continue
        
        # 检查必需的键
        for key in required_keys:
            if key not in relation:
                errors.append(f"关系 {i} 缺少必需字段: {key}")
            elif not isinstance(relation[key], str) or not relation[key].strip():
                errors.append(f"关系 {i} 的字段 {key} 必须是非空字符串")
        
        # 检查实体ID是否存在
        if "source_entity_id" in relation and relation["source_entity_id"] not in entity_ids:
            errors.append(f"关系 {i} 的 source_entity_id '{relation['source_entity_id']}' 不存在于实体列表中")
        
        if "target_entity_id" in relation and relation["target_entity_id"] not in entity_ids:
            errors.append(f"关系 {i} 的 target_entity_id '{relation['target_entity_id']}' 不存在于实体列表中")
    
    return {"success": len(errors) == 0, "errors": errors}


def main():
    """主测试函数"""
    print("🎯 开始测试溯源信息强制输出...")
    print("=" * 60)
    
    # 测试ECE智能体
    ece_success, entities = test_ece_agent()
    
    # 测试REE智能体
    ree_success = test_ree_agent(entities)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 测试结果汇总：")
    print(f"  ECE智能体（实体抽取）: {'✅ 通过' if ece_success else '❌ 失败'}")
    print(f"  REE智能体（关系抽取）: {'✅ 通过' if ree_success else '❌ 失败'}")
    
    if ece_success and ree_success:
        print("\n🎉 所有测试通过！智能体已成功遵循溯源信息输出要求。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查智能体配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 