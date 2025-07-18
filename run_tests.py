"""
测试运行脚本

提供便捷的测试执行接口，支持不同类型和范围的测试。
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, cwd: Path = None) -> int:
    """运行命令并返回退出码"""
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"错误: 命令 '{cmd[0]}' 未找到")
        return 1


def run_source_sentence_test():
    """运行溯源信息测试"""
    print("🧪 运行溯源信息测试...")
    print("=" * 60)
    
    # 运行test_source_sentence.py
    cmd = [sys.executable, "test_source_sentence.py"]
    return run_command(cmd)


def run_end_to_end_test():
    """运行端到端溯源信息测试"""
    print("🧪 运行端到端溯源信息测试...")
    print("=" * 60)
    
    # 运行test_end_to_end_with_source.py
    cmd = [sys.executable, "test_end_to_end_with_source.py"]
    return run_command(cmd)


def check_dependencies():
    """检查测试依赖"""
    try:
        import pytest
        import pytest_asyncio
        import pytest_cov
        print("✓ 测试依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少测试依赖: {e}")
        print("请运行: pip install pytest pytest-asyncio pytest-cov")
        return False


def run_unit_tests(coverage: bool = False, verbose: bool = False):
    """运行单元测试"""
    print("运行单元测试...")
    
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=agents",
            "--cov=tools",
            "--cov=api",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    return run_command(cmd)


def run_integration_tests(verbose: bool = False):
    """运行集成测试"""
    print("运行集成测试...")
    
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_chief_ontologist_test():
    """运行首席本体论专家测试"""
    print("运行首席本体论专家测试...")
    
    cmd = [sys.executable, "agents/chief_ontologist.py"]
    return run_command(cmd)


def run_reasoning_test():
    """运行推理智能体测试"""
    print("运行推理智能体测试...")
    
    cmd = [sys.executable, "test_reasoning_agent.py"]
    return run_command(cmd)


def run_system_test():
    """运行系统测试"""
    print("运行系统测试...")
    
    cmd = [sys.executable, "main_with_reasoning.py"]
    return run_command(cmd)


def run_all_tests():
    """运行所有测试"""
    print("🚀 运行所有测试...")
    print("=" * 80)
    
    tests = [
        ("首席本体论专家", run_chief_ontologist_test),
        ("溯源信息测试", run_source_sentence_test),
        ("端到端溯源测试", run_end_to_end_test),
        ("推理智能体", run_reasoning_test),
        ("系统集成", run_system_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试...")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result == 0
        except Exception as e:
            print(f"❌ {test_name}测试执行出错: {e}")
            results[test_name] = False
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总:")
    print("-" * 40)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📈 总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查系统配置。")
        return 1


def run_benchmark_tests():
    """运行性能基准测试"""
    print("运行性能基准测试...")
    
    # 这里可以添加性能测试逻辑
    print("性能测试功能待实现...")
    return 0


def run_database_tests():
    """运行数据库相关测试"""
    print("运行数据库测试...")
    
    # 测试数据库连接
    try:
        from tools.graph_db import GraphDB
        
        db = GraphDB()
        if db.test_connection():
            print("✓ 数据库连接测试通过")
            return 0
        else:
            print("✗ 数据库连接测试失败")
            return 1
    except Exception as e:
        print(f"✗ 数据库测试出错: {e}")
        return 1


def run_api_tests():
    """运行API测试"""
    print("运行API测试...")
    
    # 这里可以添加API测试逻辑
    print("API测试功能待实现...")
    return 0


def run_agent_tests():
    """运行智能体专项测试"""
    print("运行智能体专项测试...")
    
    agent_tests = [
        ("首席本体论专家", run_chief_ontologist_test),
        ("溯源信息测试", run_source_sentence_test),
        ("推理智能体", run_reasoning_test)
    ]
    
    results = {}
    
    for test_name, test_func in agent_tests:
        print(f"\n🤖 {test_name}测试...")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result == 0
        except Exception as e:
            print(f"❌ {test_name}测试执行出错: {e}")
            results[test_name] = False
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("🤖 智能体测试结果:")
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 所有智能体测试通过！")
        return 0
    else:
        print("⚠️ 部分智能体测试失败。")
        return 1


def clean_test_artifacts():
    """清理测试产生的临时文件"""
    print("清理测试临时文件...")
    
    artifacts = [
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        "**/__pycache__/",
        "**/*.pyc",
        "**/*.pyo"
    ]
    
    import glob
    import shutil
    
    for pattern in artifacts:
        for path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"删除文件: {path}")
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"删除目录: {path}")
            except Exception as e:
                print(f"清理 {path} 时出错: {e}")
    
    print("清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AutoGen 项目测试工具")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all", "unit", "integration", "agents", "database", 
            "api", "benchmark", "ontologist", "reasoning", 
            "system", "source-sentence", "end-to-end", "clean"
        ],
        help="选择测试类型"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告（仅适用于单元测试）"
    )
    
    args = parser.parse_args()
    
    print("🧪 AutoGen 测试工具")
    print("=" * 50)
    
    # 根据选择的测试类型运行相应测试
    if args.test_type == "all":
        return run_all_tests()
    elif args.test_type == "unit":
        if not check_dependencies():
            return 1
        return run_unit_tests(coverage=args.coverage, verbose=args.verbose)
    elif args.test_type == "integration":
        if not check_dependencies():
            return 1
        return run_integration_tests(verbose=args.verbose)
    elif args.test_type == "agents":
        return run_agent_tests()
    elif args.test_type == "database":
        return run_database_tests()
    elif args.test_type == "api":
        return run_api_tests()
    elif args.test_type == "benchmark":
        return run_benchmark_tests()
    elif args.test_type == "ontologist":
        return run_chief_ontologist_test()
    elif args.test_type == "reasoning":
        return run_reasoning_test()
    elif args.test_type == "system":
        return run_system_test()
    elif args.test_type == "source-sentence":
        return run_source_sentence_test()
    elif args.test_type == "end-to-end":
        return run_end_to_end_test()
    elif args.test_type == "clean":
        clean_test_artifacts()
        return 0
    else:
        print(f"未知的测试类型: {args.test_type}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 