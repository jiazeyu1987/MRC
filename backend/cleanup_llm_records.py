#!/usr/bin/env python3
"""
LLM记录清理脚本

定期清理过期的LLM交互记录文件，包括：
- 压缩归档旧文件
- 删除过期文件
- 生成清理报告

使用方法：
python cleanup_llm_records.py [--dry-run] [--force]
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.llm_file_record_service import llm_file_record


def main():
    parser = argparse.ArgumentParser(description='清理LLM交互记录文件')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要清理的文件，不实际删除')
    parser.add_argument('--force', action='store_true', help='强制清理，不询问确认')
    parser.add_argument('--days', type=int, help='自定义保留天数（覆盖默认设置）')
    parser.add_argument('--report', action='store_true', help='生成详细的清理报告')

    args = parser.parse_args()

    print("=" * 60)
    print("LLM交互记录清理工具")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 获取清理前的统计信息
        print("\n1. 获取当前统计信息...")
        before_stats = llm_file_record.get_statistics()
        print(f"   总交互数: {before_stats.get('total_interactions', 0)}")
        print(f"   成功交互: {before_stats.get('successful_interactions', 0)}")
        print(f"   失败交互: {before_stats.get('failed_interactions', 0)}")
        print(f"   会话数: {before_stats.get('total_sessions', 0)}")

        if args.days:
            # 临时修改保留天数
            original_session_retention = llm_file_record.session_retention_days
            original_error_retention = llm_file_record.error_retention_days
            llm_file_record.session_retention_days = args.days
            llm_file_record.error_retention_days = min(args.days, 30)  # 错误文件最多保留30天
            print(f"   临时保留天数: 会话文件 {args.days} 天, 错误文件 {min(args.days, 30)} 天")

        if args.dry_run:
            print("\n2. 模拟运行模式 - 不会实际删除文件")
            print("   以下文件将被清理:")

            # 分析将要清理的文件
            base_dir = Path("logs/llm_interactions")
            cutoff_date = datetime.now() - timedelta(days=args.days or llm_file_record.session_retention_days)

            files_to_delete = []
            total_size = 0

            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = Path(root) / file
                        try:
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_date:
                                file_size = file_path.stat().st_size
                                files_to_delete.append(file_path)
                                total_size += file_size
                        except OSError:
                            continue

            print(f"   文件数量: {len(files_to_delete)}")
            print(f"   总大小: {total_size / (1024*1024):.2f} MB")

            if args.report and files_to_delete:
                print("\n   详细文件列表:")
                for file_path in sorted(files_to_delete):
                    relative_path = file_path.relative_to(base_dir)
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    size = file_path.stat().st_size
                    print(f"   - {relative_path} ({mtime.strftime('%Y-%m-%d')}, {size} bytes)")
        else:
            print("\n2. 执行清理...")

            if not args.force:
                response = input("确认要执行清理吗？(y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("清理已取消")
                    return

            # 执行清理
            llm_file_record.cleanup_old_files()
            print("   清理完成")

        # 恢复原始设置
        if args.days:
            llm_file_record.session_retention_days = original_session_retention
            llm_file_record.error_retention_days = original_error_retention

        # 获取清理后的统计信息
        if not args.dry_run:
            print("\n3. 获取清理后统计信息...")
            after_stats = llm_file_record.get_statistics()
            print(f"   总交互数: {after_stats.get('total_interactions', 0)}")
            print(f"   成功交互: {after_stats.get('successful_interactions', 0)}")
            print(f"   失败交互: {after_stats.get('failed_interactions', 0)}")
            print(f"   会话数: {after_stats.get('total_sessions', 0)}")

            # 计算清理效果
            total_diff = before_stats.get('total_interactions', 0) - after_stats.get('total_interactions', 0)
            session_diff = before_stats.get('total_sessions', 0) - after_stats.get('total_sessions', 0)

            if total_diff > 0 or session_diff > 0:
                print(f"\n   清理效果:")
                print(f"   - 删除交互记录: {total_diff} 条")
                print(f"   - 删除会话记录: {session_diff} 个")

        # 生成存储信息报告
        if args.report:
            print("\n4. 存储信息报告:")
            storage_info = after_stats.get('storage_info', {})
            for storage_type, info in storage_info.items():
                count = info.get('count', 0)
                size_mb = info.get('size', 0) / (1024 * 1024)
                print(f"   {storage_type}: {count} 文件, {size_mb:.2f} MB")

        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()