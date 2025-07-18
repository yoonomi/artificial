"""
推理工具演示脚本

演示如何使用推理工具集进行知识图谱的模式发现、假设验证和推理关系创建。
"""

import logging
from tools.graph_db import GraphDB
from tools.reasoning_tools import execute_reasoning_pipeline
from config import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_demo_data(db: GraphDB):
    """
    设置演示数据
    创建一些模拟的人物、机构和项目关系
    """
    print("🛠️  设置演示数据...")
    
    # 清理旧数据
    cleanup_query = """
    MATCH (n) WHERE n.name IN [
        '张伟', '李明', '王强', '刘芳', '陈杰',
        '北京大学', '清华大学', 'AI研究所',
        '深度学习项目', '机器视觉项目', '自然语言处理项目'
    ] DETACH DELETE n
    """
    db.execute_query(cleanup_query)
    
    # 创建人物节点
    people_queries = [
        "CREATE (p:人物 {name: '张伟', age: 35, position: '教授'})",
        "CREATE (p:人物 {name: '李明', age: 28, position: '博士生'})",
        "CREATE (p:人物 {name: '王强', age: 32, position: '副教授'})",
        "CREATE (p:人物 {name: '刘芳', age: 26, position: '硕士生'})",
        "CREATE (p:人物 {name: '陈杰', age: 40, position: '研究员'})",
    ]
    
    # 创建机构节点
    org_queries = [
        "CREATE (o:机构 {name: '北京大学', type: '大学', established: 1898})",
        "CREATE (o:机构 {name: '清华大学', type: '大学', established: 1911})",
        "CREATE (o:机构 {name: 'AI研究所', type: '研究所', established: 2010})",
    ]
    
    # 创建项目节点
    project_queries = [
        "CREATE (p:项目 {name: '深度学习项目', type: '研究项目', budget: 500000})",
        "CREATE (p:项目 {name: '机器视觉项目', type: '应用项目', budget: 300000})",
        "CREATE (p:项目 {name: '自然语言处理项目', type: '基础研究', budget: 400000})",
    ]
    
    # 执行创建查询
    all_queries = people_queries + org_queries + project_queries
    for query in all_queries:
        db.execute_query(query)
    
    # 创建关系（包含详细的source_sentence信息）
    relationships = [
        # 工作关系
        ("""
        MATCH (p:人物 {name: '张伟'}), (o:机构 {name: '北京大学'})
        CREATE (p)-[:工作于 {
            position: '计算机科学教授',
            start_date: '2015-09-01',
            source_sentence: '张伟教授自2015年起在北京大学计算机科学系担任教授，主要研究方向为深度学习和人工智能。'
        }]->(o)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '王强'}), (o:机构 {name: '北京大学'})
        CREATE (p)-[:工作于 {
            position: '副教授',
            start_date: '2018-03-01',
            source_sentence: '王强博士于2018年加入北京大学，担任计算机科学系副教授，专注于机器学习算法研究。'
        }]->(o)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '陈杰'}), (o:机构 {name: 'AI研究所'})
        CREATE (p)-[:工作于 {
            position: '高级研究员',
            start_date: '2010-06-01',
            source_sentence: '陈杰研究员是AI研究所的创始成员之一，负责自然语言处理方向的研究工作。'
        }]->(o)
        """, {}),
        
        # 学习关系
        ("""
        MATCH (p:人物 {name: '李明'}), (o:机构 {name: '北京大学'})
        CREATE (p)-[:就读于 {
            degree: '博士',
            start_date: '2020-09-01',
            advisor: '张伟',
            source_sentence: '李明于2020年进入北京大学计算机科学系攻读博士学位，师从张伟教授，研究深度学习理论。'
        }]->(o)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '刘芳'}), (o:机构 {name: '清华大学'})
        CREATE (p)-[:就读于 {
            degree: '硕士',
            start_date: '2021-09-01',
            source_sentence: '刘芳在清华大学攻读计算机科学硕士学位，主要研究计算机视觉和图像处理技术。'
        }]->(o)
        """, {}),
        
        # 项目参与关系
        ("""
        MATCH (p:人物 {name: '张伟'}), (proj:项目 {name: '深度学习项目'})
        CREATE (p)-[:参与 {
            role: '项目负责人',
            start_date: '2021-01-01',
            source_sentence: '张伟教授作为项目负责人，领导深度学习项目的整体研究方向和技术路线规划。'
        }]->(proj)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '李明'}), (proj:项目 {name: '深度学习项目'})
        CREATE (p)-[:参与 {
            role: '核心开发者',
            start_date: '2021-03-01',
            source_sentence: '李明在深度学习项目中负责算法实现和实验验证，是项目的核心技术骨干。'
        }]->(proj)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '王强'}), (proj:项目 {name: '机器视觉项目'})
        CREATE (p)-[:参与 {
            role: '技术顾问',
            start_date: '2021-06-01',
            source_sentence: '王强副教授为机器视觉项目提供技术指导，协助解决关键算法难题。'
        }]->(proj)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '刘芳'}), (proj:项目 {name: '机器视觉项目'})
        CREATE (p)-[:参与 {
            role: '研究助理',
            start_date: '2022-01-01',
            source_sentence: '刘芳作为研究助理参与机器视觉项目，负责数据处理和模型训练工作。'
        }]->(proj)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '陈杰'}), (proj:项目 {name: '自然语言处理项目'})
        CREATE (p)-[:参与 {
            role: '项目负责人',
            start_date: '2020-01-01',
            source_sentence: '陈杰研究员主导自然语言处理项目的研究，在语言模型和文本理解方面取得重要进展。'
        }]->(proj)
        """, {}),
        
        # 合作关系
        ("""
        MATCH (p1:人物 {name: '张伟'}), (p2:人物 {name: '陈杰'})
        CREATE (p1)-[:合作 {
            project: '跨机构AI合作',
            start_date: '2021-05-01',
            source_sentence: '张伟教授与陈杰研究员在人工智能领域建立了深度合作关系，共同推进相关技术发展。'
        }]->(p2)
        """, {}),
    ]
    
    # 执行关系创建查询
    for query, params in relationships:
        db.execute_query(query, params)
    
    print("✅ 演示数据设置完成")


def main():
    """主演示函数"""
    print("🧠 推理工具演示开始")
    print("=" * 60)
    
    try:
        # 连接数据库
        print("🔗 连接Neo4j数据库...")
        db = GraphDB(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )
        
        if not db.connected:
            print("❌ 数据库连接失败，请检查Neo4j是否正在运行")
            return
        
        print("✅ 数据库连接成功")
        
        # 设置演示数据
        setup_demo_data(db)
        
        # 查看当前图谱状态
        print("\n📊 当前图谱状态:")
        node_count_query = "MATCH (n) RETURN labels(n) as label, count(n) as count"
        node_counts = db.execute_query(node_count_query)
        for result in node_counts:
            label = result['label'][0] if result['label'] else 'Unknown'
            print(f"   {label}: {result['count']} 个节点")
        
        rel_count_query = "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count"
        rel_counts = db.execute_query(rel_count_query)
        for result in rel_counts:
            print(f"   {result['type']}: {result['count']} 个关系")
        
        # 执行推理管道
        print("\n🧠 开始执行推理分析...")
        print("-" * 40)
        
        # 执行推理管道（使用'中'阈值以便看到更多结果）
        pipeline_result = execute_reasoning_pipeline(db, confidence_threshold='中')
        
        # 详细输出结果
        print(f"\n📈 推理分析结果:")
        print(f"   🔍 发现的模式数量: {pipeline_result['patterns_found']}")
        print(f"   ✅ 验证通过的模式: {pipeline_result['patterns_verified']}")
        print(f"   🔗 成功创建的推理关系: {pipeline_result['relationships_created']}")
        print(f"   ❌ 创建失败的关系: {len(pipeline_result['failed_creations'])}")
        
        # 显示成功创建的关系
        if pipeline_result['created_relationships']:
            print(f"\n🔗 新发现的推理关系:")
            for i, rel in enumerate(pipeline_result['created_relationships'], 1):
                print(f"   {i}. {rel['relationship']}:")
                entities = rel['entities']
                if 'person1' in entities and 'person2' in entities:
                    print(f"      👥 {entities['person1']} ↔ {entities['person2']}")
                    if 'organization' in entities:
                        print(f"      🏢 通过机构: {entities['organization']}")
                    elif 'project' in entities:
                        print(f"      📂 通过项目: {entities['project']}")
                elif 'mentor' in entities and 'student' in entities:
                    print(f"      👨‍🏫 {entities['mentor']} → {entities['student']}")
                    if 'institution' in entities:
                        print(f"      🏛️  在机构: {entities['institution']}")
                print(f"      📋 模式类型: {rel['pattern_type']}")
                print()
        
        # 显示失败的创建
        if pipeline_result['failed_creations']:
            print(f"\n❌ 创建失败的关系:")
            for i, fail in enumerate(pipeline_result['failed_creations'], 1):
                print(f"   {i}. {fail['pattern_type']}: {fail['error']}")
        
        # 查看最终的图谱状态
        print(f"\n📊 推理后的图谱状态:")
        final_node_counts = db.execute_query(node_count_query)
        for result in final_node_counts:
            label = result['label'][0] if result['label'] else 'Unknown'
            print(f"   {label}: {result['count']} 个节点")
        
        final_rel_counts = db.execute_query(rel_count_query)
        for result in final_rel_counts:
            print(f"   {result['type']}: {result['count']} 个关系")
        
        # 专门显示推理关系
        inferred_query = """
        MATCH (a)-[r]->(b) 
        WHERE r.type = 'INFERRED'
        RETURN a.name as source, type(r) as rel_type, b.name as target, r.confidence as confidence
        """
        inferred_rels = db.execute_query(inferred_query)
        
        if inferred_rels:
            print(f"\n🧠 推理关系详情:")
            for rel in inferred_rels:
                print(f"   {rel['source']} --[{rel['rel_type']}]--> {rel['target']} (置信度: {rel['confidence']})")
        
        print(f"\n{pipeline_result['execution_summary']}")
        
        print("\n🎉 推理工具演示完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 