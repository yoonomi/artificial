"""
推理智能体工具集

为推理智能体提供模式发现、假设验证和推理关系创建的核心功能。
这些工具通过确定性的逻辑来支持智能体的推理能力。
"""

import logging
import json
from typing import Dict, List, Any, Optional
from tools.graph_db import GraphDB
from config import config
import openai

logger = logging.getLogger(__name__)

# 预定义的模式查询
PATTERN_QUERIES = {
    "common_workplace": {
        "description": "寻找在同一机构工作的人员",
        "cypher": """
        MATCH (p1:人物)-[:工作于|任职于|就职于]->(o:机构)<-[:工作于|任职于|就职于]-(p2:人物) 
        WHERE id(p1) < id(p2) 
        RETURN p1.name AS person1, p2.name AS person2, o.name AS organization
        """,
        "inferred_relationship": "同事关系"
    },
    
    "common_education": {
        "description": "寻找在同一教育机构学习的人员",
        "cypher": """
        MATCH (p1:人物)-[:毕业于|就读于|学习于]->(e:机构)<-[:毕业于|就读于|学习于]-(p2:人物) 
        WHERE id(p1) < id(p2) 
        RETURN p1.name AS person1, p2.name AS person2, e.name AS education
        """,
        "inferred_relationship": "校友关系"
    },
    
    "collaboration_through_project": {
        "description": "寻找参与同一项目或论文的人员",
        "cypher": """
        MATCH (p1:人物)-[:参与|发表|合作]->(proj:论文|项目|系统)<-[:参与|发表|合作]-(p2:人物) 
        WHERE id(p1) < id(p2) 
        RETURN p1.name AS person1, p2.name AS person2, proj.name AS project
        """,
        "inferred_relationship": "合作关系"
    },
    
    "mentor_student_pattern": {
        "description": "寻找可能的师生关系模式",
        "cypher": """
        MATCH (senior:人物)-[:工作于]->(org:机构)<-[:学习于|就读于]-(junior:人物),
              (senior)-[:发表]->(paper:论文)<-[:参与]-(junior)
        WHERE senior.name <> junior.name
        RETURN senior.name AS mentor, junior.name AS student, org.name AS institution
        """,
        "inferred_relationship": "师生关系"
    },
    
    "technology_transfer": {
        "description": "寻找技术传承或影响关系",
        "cypher": """
        MATCH (p1:人物)-[:提出|发明]->(tech:技术|算法|模型)<-[:改进|基于|使用]-(p2:人物)
        WHERE p1.name <> p2.name
        RETURN p1.name AS innovator, p2.name AS follower, tech.name AS technology
        """,
        "inferred_relationship": "技术影响"
    }
}


def find_interesting_patterns(graph_db: GraphDB) -> List[Dict[str, Any]]:
    """
    在Neo4j图谱中主动寻找预设的、可能暗示隐含关系的模式
    
    Args:
        graph_db: 图数据库连接实例
        
    Returns:
        发现的模式列表，每个字典包含模式类型和相关实体信息
        格式: [{'type': 'common_workplace', 'entities': {...}, 'description': '...', 'inferred_relationship': '...'}, ...]
    """
    logger.info("开始寻找图谱中的有趣模式...")
    
    discovered_patterns = []
    
    for pattern_name, pattern_config in PATTERN_QUERIES.items():
        try:
            logger.info(f"执行模式查询: {pattern_name}")
            
            results = graph_db.execute_query(pattern_config["cypher"])
            
            for result in results:
                pattern_dict = {
                    'type': pattern_name,
                    'description': pattern_config['description'],
                    'inferred_relationship': pattern_config['inferred_relationship'],
                    'entities': result,
                    'confidence': 'unknown'  # 将由verify_hypothesis_from_text填充
                }
                discovered_patterns.append(pattern_dict)
                
            logger.info(f"模式 {pattern_name} 发现了 {len(results)} 个实例")
            
        except Exception as e:
            logger.error(f"执行模式查询 {pattern_name} 时出错: {e}")
            continue
    
    logger.info(f"总共发现 {len(discovered_patterns)} 个潜在模式")
    return discovered_patterns


def verify_hypothesis_from_text(pattern: Dict[str, Any], graph_db: GraphDB) -> Dict[str, Any]:
    """
    验证一个模式是否真的能构成一个有意义的隐含关系
    
    Args:
        pattern: 从find_interesting_patterns返回的模式字典
        graph_db: 图数据库连接实例
        
    Returns:
        更新后的字典，包含验证结果
        格式: {'pattern': ..., 'verification': '高|中|低', 'evidence_text': '...'}
    """
    logger.info(f"开始验证模式: {pattern['type']}")
    
    try:
        # 提取实体名称
        entities = pattern['entities']
        entity_names = list(entities.values())
        
        # 构建证据收集查询
        evidence_query = """
        MATCH (n)-[r]-(m) 
        WHERE n.name IN $entity_names OR m.name IN $entity_names
        AND r.source_sentence IS NOT NULL
        RETURN DISTINCT r.source_sentence AS sentence
        """
        
        evidence_results = graph_db.execute_query(evidence_query, {"entity_names": entity_names})
        
        # 合并证据文本
        evidence_sentences = [result['sentence'] for result in evidence_results if result.get('sentence')]
        evidence_text = " ".join(evidence_sentences[:10])  # 限制证据长度
        
        if not evidence_text.strip():
            logger.warning(f"未找到相关证据文本，模式: {pattern['type']}")
            pattern['verification'] = '低'
            pattern['evidence_text'] = ''
            pattern['reasoning'] = '缺乏足够的文本证据'
            return pattern
        
        # 构造LLM验证请求
        prompt = f"""
基于以下证据文本，请评估实体间是否存在 "{pattern['inferred_relationship']}" 的可能性。

模式类型: {pattern['description']}
涉及实体: {', '.join(f"{k}: {v}" for k, v in entities.items())}
推理关系: {pattern['inferred_relationship']}

证据文本:
{evidence_text}

请仔细分析证据，从以下选项中选择一个回答，并简要说明理由:
- 高: 有强烈证据支持该推理关系
- 中: 有一定证据但不够确凿  
- 低: 缺乏证据或证据不支持该关系

请以JSON格式回答:
{{"confidence": "高|中|低", "reasoning": "你的分析理由"}}
"""

        # 调用LLM进行验证
        llm_config = config.llm_config_gpt4
        
        client = openai.OpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config.get("base_url")
        )
        
        response = client.chat.completions.create(
            model=llm_config["model"],
            messages=[
                {"role": "system", "content": "你是一个专业的知识图谱分析专家，擅长从文本证据中推理实体间的隐含关系。"},
                {"role": "user", "content": prompt}
            ],
            temperature=llm_config["temperature"],
            max_tokens=500
        )
        
        # 解析LLM响应
        llm_response = response.choices[0].message.content.strip()
        
        try:
            # 尝试提取JSON内容（处理markdown代码块）
            json_content = llm_response
            
            # 如果响应包含markdown代码块，提取其中的JSON
            if '```json' in llm_response:
                start_marker = '```json'
                end_marker = '```'
                start_idx = llm_response.find(start_marker) + len(start_marker)
                end_idx = llm_response.find(end_marker, start_idx)
                if end_idx != -1:
                    json_content = llm_response[start_idx:end_idx].strip()
            elif '```' in llm_response:
                # 处理不带语言标识的代码块
                parts = llm_response.split('```')
                if len(parts) >= 3:
                    json_content = parts[1].strip()
            
            verification_result = json.loads(json_content)
            confidence = verification_result.get('confidence', '低')
            reasoning = verification_result.get('reasoning', '无法解析LLM响应')
        except json.JSONDecodeError:
            logger.warning(f"无法解析LLM响应为JSON: {llm_response}")
            confidence = '低'
            reasoning = f'LLM响应解析失败: {llm_response}'
        
        # 更新模式字典
        pattern['verification'] = confidence
        pattern['evidence_text'] = evidence_text
        pattern['reasoning'] = reasoning
        
        logger.info(f"模式验证完成: {pattern['type']}, 置信度: {confidence}")
        
    except Exception as e:
        logger.error(f"验证模式时出错: {e}")
        pattern['verification'] = '低'
        pattern['evidence_text'] = ''
        pattern['reasoning'] = f'验证过程出错: {str(e)}'
    
    return pattern


def create_inferred_relationship(verified_pattern: Dict[str, Any], graph_db: GraphDB) -> str:
    """
    将已验证的、高可能性的隐含关系写回图谱
    
    Args:
        verified_pattern: verify_hypothesis_from_text返回的且verification为'高'的字典
        graph_db: 图数据库连接实例
        
    Returns:
        包含成功或失败信息的字符串
    """
    logger.info(f"开始创建推理关系: {verified_pattern['type']}")
    
    try:
        # 检查验证结果
        if verified_pattern.get('verification') != '高':
            return f"跳过创建关系: 置信度不够高 ({verified_pattern.get('verification', '未知')})"
        
        entities = verified_pattern['entities']
        relationship_type = verified_pattern['inferred_relationship'].replace('关系', '').replace(' ', '_')
        
        # 根据模式类型确定实体对
        if verified_pattern['type'] in ['common_workplace', 'common_education', 'collaboration_through_project']:
            # 双向关系
            person1 = entities.get('person1') or entities.get('mentor') or entities.get('innovator')
            person2 = entities.get('person2') or entities.get('student') or entities.get('follower')
            
            if not person1 or not person2:
                return f"无法识别实体对: {entities}"
            
            # 创建双向推理关系
            relationship_properties = {
                'type': 'INFERRED',
                'confidence': verified_pattern['verification'],
                'reasoning': verified_pattern['reasoning'],
                'evidence_summary': verified_pattern['evidence_text'][:200] + '...' if len(verified_pattern['evidence_text']) > 200 else verified_pattern['evidence_text'],
                'pattern_type': verified_pattern['type']
            }
            
            # 创建第一个方向的关系
            query1 = f"""
            MATCH (a), (b) 
            WHERE a.name = $person1 AND b.name = $person2
            MERGE (a)-[r:推理_{relationship_type}]->(b)
            SET r += $properties
            RETURN r
            """
            
            # 创建第二个方向的关系  
            query2 = f"""
            MATCH (a), (b) 
            WHERE a.name = $person1 AND b.name = $person2
            MERGE (b)-[r:推理_{relationship_type}]->(a)
            SET r += $properties  
            RETURN r
            """
            
            params = {
                'person1': person1,
                'person2': person2,
                'properties': relationship_properties
            }
            
            # 执行查询
            result1 = graph_db.execute_query(query1, params)
            result2 = graph_db.execute_query(query2, params)
            
            if result1 and result2:
                success_msg = f"成功创建双向推理关系: {person1} <--> {person2} (关系类型: 推理_{relationship_type})"
                logger.info(success_msg)
                return success_msg
            else:
                error_msg = f"创建关系失败: 查询执行无结果"
                logger.error(error_msg)
                return error_msg
                
        elif verified_pattern['type'] in ['mentor_student_pattern', 'technology_transfer']:
            # 单向关系
            source = entities.get('mentor') or entities.get('innovator')
            target = entities.get('student') or entities.get('follower')
            
            if not source or not target:
                return f"无法识别源和目标实体: {entities}"
            
            relationship_properties = {
                'type': 'INFERRED',
                'confidence': verified_pattern['verification'],
                'reasoning': verified_pattern['reasoning'],
                'evidence_summary': verified_pattern['evidence_text'][:200] + '...' if len(verified_pattern['evidence_text']) > 200 else verified_pattern['evidence_text'],
                'pattern_type': verified_pattern['type']
            }
            
            query = f"""
            MATCH (a), (b) 
            WHERE a.name = $source AND b.name = $target
            MERGE (a)-[r:推理_{relationship_type}]->(b)
            SET r += $properties
            RETURN r
            """
            
            params = {
                'source': source,
                'target': target,
                'properties': relationship_properties
            }
            
            result = graph_db.execute_query(query, params)
            
            if result:
                success_msg = f"成功创建单向推理关系: {source} --> {target} (关系类型: 推理_{relationship_type})"
                logger.info(success_msg)
                return success_msg
            else:
                error_msg = f"创建关系失败: 查询执行无结果"
                logger.error(error_msg)
                return error_msg
        
        else:
            return f"未知的模式类型: {verified_pattern['type']}"
            
    except Exception as e:
        error_msg = f"创建推理关系时出错: {str(e)}"
        logger.error(error_msg)
        return error_msg


def execute_reasoning_pipeline(graph_db: GraphDB, confidence_threshold: str = '高') -> Dict[str, Any]:
    """
    执行完整的推理管道：发现模式 -> 验证假设 -> 创建关系
    
    Args:
        graph_db: 图数据库连接实例
        confidence_threshold: 置信度阈值，只有达到此阈值的关系才会被创建
        
    Returns:
        推理管道执行结果的汇总信息
    """
    logger.info("开始执行完整的推理管道...")
    
    pipeline_result = {
        'patterns_found': 0,
        'patterns_verified': 0,
        'relationships_created': 0,
        'created_relationships': [],
        'failed_creations': [],
        'execution_summary': ''
    }
    
    try:
        # 步骤1: 发现模式
        patterns = find_interesting_patterns(graph_db)
        pipeline_result['patterns_found'] = len(patterns)
        
        if not patterns:
            pipeline_result['execution_summary'] = '未发现任何有趣的模式'
            return pipeline_result
        
        # 步骤2: 验证假设
        verified_patterns = []
        for pattern in patterns:
            verified_pattern = verify_hypothesis_from_text(pattern, graph_db)
            verified_patterns.append(verified_pattern)
            if verified_pattern.get('verification') in ['高', '中'] and confidence_threshold in ['高', '中']:
                pipeline_result['patterns_verified'] += 1
            elif verified_pattern.get('verification') == confidence_threshold:
                pipeline_result['patterns_verified'] += 1
        
        # 步骤3: 创建关系
        for verified_pattern in verified_patterns:
            # 根据阈值决定是否创建关系
            verification = verified_pattern.get('verification')
            should_create = False
            
            if confidence_threshold == '高' and verification == '高':
                should_create = True
            elif confidence_threshold == '中' and verification in ['高', '中']:
                should_create = True
            elif confidence_threshold == '低' and verification in ['高', '中', '低']:
                should_create = True
            
            if should_create:
                result_msg = create_inferred_relationship(verified_pattern, graph_db)
                
                if "成功创建" in result_msg:
                    pipeline_result['relationships_created'] += 1
                    pipeline_result['created_relationships'].append({
                        'pattern_type': verified_pattern['type'],
                        'entities': verified_pattern['entities'],
                        'relationship': verified_pattern['inferred_relationship'],
                        'message': result_msg
                    })
                else:
                    pipeline_result['failed_creations'].append({
                        'pattern_type': verified_pattern['type'],
                        'entities': verified_pattern['entities'],
                        'error': result_msg
                    })
        
        # 生成执行摘要
        pipeline_result['execution_summary'] = f"""
推理管道执行完成:
- 发现模式: {pipeline_result['patterns_found']} 个
- 高置信度验证: {pipeline_result['patterns_verified']} 个  
- 成功创建关系: {pipeline_result['relationships_created']} 个
- 创建失败: {len(pipeline_result['failed_creations'])} 个
"""
        
        logger.info(pipeline_result['execution_summary'])
        
    except Exception as e:
        error_msg = f"推理管道执行出错: {str(e)}"
        logger.error(error_msg)
        pipeline_result['execution_summary'] = error_msg
    
    return pipeline_result 