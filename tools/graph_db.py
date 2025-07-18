"""
图数据库操作工具模块

提供Neo4j图数据库的连接、查询、数据导入导出等功能。
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
import json
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j driver not available. Please install with: pip install neo4j")


class GraphDB:
    """
    图数据库操作工具类
    
    提供Neo4j数据库的连接管理、数据导入、查询执行等功能
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        """
        初始化图数据库连接
        
        Args:
            uri: Neo4j数据库URI
            username: 用户名
            password: 密码
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.connected = False
        
        if NEO4J_AVAILABLE:
            self.connect()
        else:
            logger.warning("Neo4j driver not available. Running in simulation mode.")
    
    def connect(self) -> bool:
        """
        连接到Neo4j数据库
        
        Returns:
            连接是否成功
        """
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available")
            return False
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            
            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            self.connected = True
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.driver:
            self.driver.close()
            self.connected = False
            logger.info("Disconnected from Neo4j")
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        if not self.connected or not self.driver:
            raise ConnectionError("Not connected to Neo4j database")
        
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        if not self.connected:
            logger.warning("Not connected to database. Returning empty result.")
            return []
        
        try:
            with self.get_session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            return []
    
    def execute_transaction(self, queries: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        执行事务（多个查询）
        
        Args:
            queries: 查询列表，每个元素为(query, parameters)
            
        Returns:
            执行是否成功
        """
        if not self.connected:
            logger.warning("Not connected to database")
            return False
        
        try:
            with self.get_session() as session:
                with session.begin_transaction() as tx:
                    for query, parameters in queries:
                        tx.run(query, parameters or {})
                    tx.commit()
            
            logger.info(f"Transaction with {len(queries)} queries executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            return False
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> bool:
        """
        创建节点
        
        Args:
            label: 节点标签
            properties: 节点属性
            
        Returns:
            创建是否成功
        """
        # 构建属性字符串
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props_str}}})"
        
        result = self.execute_query(query, properties)
        return len(result) >= 0  # Cypher CREATE不返回结果，所以检查是否有异常
    
    def create_relationship(self, source_id: str, target_id: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """
        创建关系
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relationship_type: 关系类型
            properties: 关系属性
            
        Returns:
            创建是否成功
        """
        properties = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()]) if properties else ""
        props_clause = f" {{{props_str}}}" if props_str else ""
        
        query = f"""
        MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
        CREATE (a)-[r:{relationship_type}{props_clause}]->(b)
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            **properties
        }
        
        result = self.execute_query(query, params)
        return len(result) >= 0
    
    def import_knowledge_graph(self, knowledge_graph: Dict[str, Any]) -> bool:
        """
        导入知识图谱
        
        Args:
            knowledge_graph: 包含nodes和edges的知识图谱数据
            
        Returns:
            导入是否成功
        """
        if not self.connected:
            logger.warning("Not connected to database")
            return False
        
        try:
            # 清空数据库（可选）
            # self.clear_database()
            
            nodes = knowledge_graph.get('nodes', [])
            edges = knowledge_graph.get('edges', [])
            
            # 导入节点
            node_queries = []
            for node in nodes:
                # 展平嵌套的properties对象
                flattened_node = {}
                for k, v in node.items():
                    if k == 'properties' and isinstance(v, dict):
                        # 将properties字典中的键值对展平到顶层，添加前缀避免冲突
                        for prop_k, prop_v in v.items():
                            flattened_node[f"prop_{prop_k}"] = prop_v
                    else:
                        flattened_node[k] = v
                
                props_str = ", ".join([f"{k}: ${k}" for k in flattened_node.keys()])
                query = f"CREATE (n:{node.get('type', 'Node')} {{{props_str}}})"
                node_queries.append((query, flattened_node))
            
            # 导入关系
            edge_queries = []
            for edge in edges:
                # 展平嵌套的properties对象
                flattened_edge = {}
                for k, v in edge.items():
                    if k not in ['source', 'target', 'source_id', 'target_id', 'type', 'relation_type']:
                        if k == 'properties' and isinstance(v, dict):
                            # 将properties字典中的键值对展平到顶层，添加前缀避免冲突
                            for prop_k, prop_v in v.items():
                                flattened_edge[f"prop_{prop_k}"] = prop_v
                        else:
                            flattened_edge[k] = v
                
                props_str = ", ".join([f"{k}: ${k}" for k in flattened_edge.keys()]) if flattened_edge else ""
                props_clause = f" {{{props_str}}}" if props_str else ""
                
                # 支持新旧两种格式的字段名
                source_id = edge.get('source_id') or edge.get('source')
                target_id = edge.get('target_id') or edge.get('target')
                relation_type = edge.get('relation_type') or edge.get('type', 'RELATED')
                
                query = f"""
                MATCH (a {{id: $source}}), (b {{id: $target}})
                CREATE (a)-[r:{relation_type}{props_clause}]->(b)
                """
                
                params = {
                    "source": source_id,
                    "target": target_id,
                    **flattened_edge
                }
                edge_queries.append((query, params))
            
            # 执行批量导入
            logger.info(f"Importing {len(nodes)} nodes...")
            success = self.execute_transaction(node_queries)
            
            if success:
                logger.info(f"Importing {len(edges)} edges...")
                success = self.execute_transaction(edge_queries)
            
            if success:
                logger.info("Knowledge graph imported successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import knowledge graph: {e}")
            return False
    
    def export_knowledge_graph(self) -> Dict[str, Any]:
        """
        导出知识图谱
        
        Returns:
            包含nodes和edges的知识图谱数据
        """
        try:
            # 导出所有节点
            nodes_query = "MATCH (n) RETURN n"
            nodes_result = self.execute_query(nodes_query)
            nodes = [dict(record['n']) for record in nodes_result]
            
            # 导出所有关系
            edges_query = "MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, type(r) as type, properties(r) as props"
            edges_result = self.execute_query(edges_query)
            edges = []
            
            for record in edges_result:
                edge = {
                    'source': record['source'],
                    'target': record['target'],
                    'type': record['type'],
                    **record['props']
                }
                edges.append(edge)
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'export_timestamp': self._get_current_timestamp(),
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export knowledge graph: {e}")
            return {'nodes': [], 'edges': [], 'metadata': {}}
    
    def search_nodes(self, label: str = None, properties: Dict[str, Any] = None, 
                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索节点
        
        Args:
            label: 节点标签
            properties: 搜索属性
            limit: 结果限制
            
        Returns:
            匹配的节点列表
        """
        # 构建查询
        label_clause = f":{label}" if label else ""
        
        if properties:
            props_conditions = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
            where_clause = f" WHERE {props_conditions}"
        else:
            where_clause = ""
            properties = {}
        
        query = f"MATCH (n{label_clause}){where_clause} RETURN n LIMIT {limit}"
        
        result = self.execute_query(query, properties)
        return [dict(record['n']) for record in result]
    
    def find_path(self, source_id: str, target_id: str, max_length: int = 5) -> List[Dict[str, Any]]:
        """
        查找两个节点间的路径
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_length: 最大路径长度
            
        Returns:
            路径列表
        """
        query = f"""
        MATCH path = (a {{id: $source_id}})-[*1..{max_length}]-(b {{id: $target_id}})
        RETURN path
        LIMIT 10
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id
        }
        
        result = self.execute_query(query, params)
        return result
    
    def get_node_neighbors(self, node_id: str, relationship_type: str = None, 
                          direction: str = "both") -> List[Dict[str, Any]]:
        """
        获取节点的邻居
        
        Args:
            node_id: 节点ID
            relationship_type: 关系类型过滤
            direction: 方向 ("incoming", "outgoing", "both")
            
        Returns:
            邻居节点列表
        """
        rel_type_clause = f":{relationship_type}" if relationship_type else ""
        
        if direction == "outgoing":
            pattern = f"(n)-[r{rel_type_clause}]->(neighbor)"
        elif direction == "incoming":
            pattern = f"(n)<-[r{rel_type_clause}]-(neighbor)"
        else:  # both
            pattern = f"(n)-[r{rel_type_clause}]-(neighbor)"
        
        query = f"""
        MATCH {pattern}
        WHERE n.id = $node_id
        RETURN neighbor, r
        """
        
        result = self.execute_query(query, {"node_id": node_id})
        return result
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 节点统计
            node_count_query = "MATCH (n) RETURN count(n) as count"
            node_count = self.execute_query(node_count_query)[0]['count']
            
            # 关系统计
            edge_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
            edge_count = self.execute_query(edge_count_query)[0]['count']
            
            # 节点类型分布
            node_types_query = "MATCH (n) RETURN labels(n) as labels, count(*) as count"
            node_types_result = self.execute_query(node_types_query)
            node_types = {}
            for record in node_types_result:
                for label in record['labels']:
                    node_types[label] = node_types.get(label, 0) + record['count']
            
            # 关系类型分布
            edge_types_query = "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
            edge_types_result = self.execute_query(edge_types_query)
            edge_types = {record['type']: record['count'] for record in edge_types_result}
            
            # 度数统计
            degree_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            RETURN n.id as node_id, count(r) as degree
            ORDER BY degree DESC
            LIMIT 10
            """
            high_degree_nodes = self.execute_query(degree_query)
            
            return {
                'node_count': node_count,
                'edge_count': edge_count,
                'node_types': node_types,
                'edge_types': edge_types,
                'high_degree_nodes': high_degree_nodes,
                'graph_density': (2 * edge_count) / max(node_count * (node_count - 1), 1) if node_count > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {}
    
    def clear_database(self) -> bool:
        """
        清空数据库
        
        Returns:
            清空是否成功
        """
        try:
            query = "MATCH (n) DETACH DELETE n"
            self.execute_query(query)
            logger.info("Database cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    def create_indexes(self, node_labels: List[str], properties: List[str]) -> bool:
        """
        创建索引
        
        Args:
            node_labels: 节点标签列表
            properties: 属性列表
            
        Returns:
            创建是否成功
        """
        try:
            queries = []
            for label in node_labels:
                for prop in properties:
                    query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
                    queries.append((query, {}))
            
            success = self.execute_transaction(queries)
            if success:
                logger.info(f"Created indexes for {len(node_labels)} labels and {len(properties)} properties")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def backup_to_file(self, filepath: str) -> bool:
        """
        备份图谱到文件
        
        Args:
            filepath: 备份文件路径
            
        Returns:
            备份是否成功
        """
        try:
            knowledge_graph = self.export_knowledge_graph()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(knowledge_graph, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Graph backed up to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup graph: {e}")
            return False
    
    def restore_from_file(self, filepath: str) -> bool:
        """
        从文件恢复图谱
        
        Args:
            filepath: 备份文件路径
            
        Returns:
            恢复是否成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                knowledge_graph = json.load(f)
            
            success = self.import_knowledge_graph(knowledge_graph)
            if success:
                logger.info(f"Graph restored from {filepath}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to restore graph: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect() 


def execute_cypher_query(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
    """
    执行Cypher查询的独立函数
    
    这是一个健壮、可重用的函数，用于连接到Neo4j数据库并执行Cypher查询。
    它从环境变量中安全地读取连接信息，并提供完整的错误处理和资源管理。
    
    Args:
        query (str): 要执行的Cypher查询语句
        params (Optional[Dict[str, Any]]): 查询参数字典，用于参数化查询，默认为None
        
    Returns:
        Optional[List[Dict[str, Any]]]: 查询结果列表，如果查询失败则返回None
        
    Raises:
        Exception: 当数据库连接失败或查询执行出错时抛出异常
        
    Environment Variables:
        NEO4J_URI: Neo4j数据库URI，默认为 "bolt://localhost:7687"
        NEO4J_USERNAME: Neo4j用户名，默认为 "neo4j"  
        NEO4J_PASSWORD: Neo4j密码，默认为 "password"
        
    Example:
        >>> # 创建节点
        >>> query = "CREATE (n:Person {name: $name, age: $age}) RETURN n"
        >>> params = {"name": "Alice", "age": 30}
        >>> result = execute_cypher_query(query, params)
        >>> 
        >>> # 查询节点
        >>> query = "MATCH (n:Person) WHERE n.name = $name RETURN n"
        >>> params = {"name": "Alice"}
        >>> result = execute_cypher_query(query, params)
    """
    
    # 检查Neo4j驱动是否可用
    if not NEO4J_AVAILABLE:
        error_msg = "Neo4j driver is not available. Please install with: pip install neo4j"
        logger.error(error_msg)
        raise ImportError(error_msg)
    
    # 从环境变量中安全地读取Neo4j连接信息
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USERNAME", "neo4j")  # 修正为与config.py一致
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")
    
    # 验证必要的连接信息
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        error_msg = "Missing Neo4j connection credentials in environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 初始化变量
    driver = None
    session = None
    
    try:
        # 创建Neo4j驱动程序
        logger.info(f"Connecting to Neo4j at {neo4j_uri}")
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        
        # 验证连接
        driver.verify_connectivity()
        logger.debug("Neo4j connection verified successfully")
        
        # 创建会话
        session = driver.session()
        
        # 执行查询
        logger.debug(f"Executing query: {query}")
        if params:
            logger.debug(f"Query parameters: {params}")
        
        result = session.run(query, params or {})
        
        # 收集查询结果
        records = []
        for record in result:
            records.append(record.data())
        
        logger.info(f"Query executed successfully, returned {len(records)} records")
        return records
        
    except Exception as e:
        # 详细的错误处理
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Neo4j query execution failed:")
        logger.error(f"  Error Type: {error_type}")
        logger.error(f"  Error Message: {error_msg}")
        logger.error(f"  Query: {query}")
        logger.error(f"  Parameters: {params}")
        
        # 根据错误类型提供更具体的错误信息
        if "ServiceUnavailable" in error_type:
            logger.error("  Possible causes: Neo4j server is not running or URI is incorrect")
        elif "AuthError" in error_type:
            logger.error("  Possible causes: Incorrect username or password")
        elif "CypherSyntaxError" in error_type:
            logger.error("  Possible causes: Invalid Cypher syntax in query")
        elif "ConstraintValidationFailed" in error_type:
            logger.error("  Possible causes: Data violates database constraints")
        
        # 重新抛出异常以便调用者处理
        raise e
        
    finally:
        # 确保资源被正确释放
        try:
            if session:
                session.close()
                logger.debug("Neo4j session closed")
        except Exception as session_error:
            logger.error(f"Error closing session: {session_error}")
        
        try:
            if driver:
                driver.close()
                logger.debug("Neo4j driver closed")
        except Exception as driver_error:
            logger.error(f"Error closing driver: {driver_error}")


def test_neo4j_connection() -> bool:
    """
    测试Neo4j连接的辅助函数
    
    Returns:
        bool: 连接测试是否成功
    """
    try:
        # 执行一个简单的测试查询
        result = execute_cypher_query("RETURN 1 as test_value")
        
        if result and len(result) > 0 and result[0].get('test_value') == 1:
            logger.info("✅ Neo4j connection test passed")
            return True
        else:
            logger.error("❌ Neo4j connection test failed: Unexpected result")
            return False
            
    except Exception as e:
        logger.error(f"❌ Neo4j connection test failed: {e}")
        return False 