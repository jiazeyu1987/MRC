import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid
import gzip
import shutil
from functools import wraps


class LLMFileRecordService:
    """LLM交互文件记录服务

    提供持久化的LLM提示词和返回值文件记录功能，
    支持按会话和日期分组，异步写入，自动清理等特性。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.base_dir = Path("logs/llm_interactions")
        self._ensure_directories()

        # 实时记录缓冲区
        self._real_time_buffer = []
        self._buffer_lock = threading.Lock()

        # 配置参数
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.session_retention_days = 90
        self.error_retention_days = 30
        self.buffer_size = 100
        self.flush_interval = 30  # 秒

        # 启动后台刷新线程
        self._start_flush_thread()

    def _ensure_directories(self):
        """确保必要的目录结构存在"""
        directories = [
            self.base_dir,
            self.base_dir / "by_session",
            self.base_dir / "by_date",
            self.base_dir / "errors",
            self.base_dir / "real_time",
            self.base_dir / "archive"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def record_interaction(self,
                         session_id: int,
                         role_name: str,
                         prompt: str,
                         response: str,
                         message_id: Optional[int] = None,
                         provider: str = "claude",
                         model: str = None,
                         step_id: Optional[int] = None,
                         round_index: Optional[int] = None,
                         success: bool = True,
                         error_message: Optional[str] = None,
                         performance_metrics: Optional[Dict] = None,
                         metadata: Optional[Dict] = None) -> str:
        """
        记录LLM交互到文件系统

        Args:
            session_id: 会话ID
            role_name: 角色名称
            prompt: 发送的提示词
            response: LLM返回结果
            message_id: 消息ID（可选，用于补充记录）
            provider: LLM提供商
            model: 模型名称
            step_id: 步骤ID
            round_index: 轮次索引
            success: 是否成功
            error_message: 错误信息
            performance_metrics: 性能指标
            metadata: 额外元数据

        Returns:
            str: 交互记录的唯一ID
        """
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # 构建交互记录
        interaction_record = {
            "id": interaction_id,
            "timestamp": timestamp.isoformat(),
            "session_id": session_id,
            "message_id": message_id,
            "role_name": role_name,
            "step_id": step_id,
            "round_index": round_index,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": response,
            "success": success,
            "error_message": error_message,
            "performance_metrics": performance_metrics or {},
            "metadata": metadata or {}
        }

        # 异步写入不同文件
        self._write_to_session_file(interaction_record)
        self._write_to_date_file(interaction_record)
        self._add_to_real_time_buffer(interaction_record)

        # 如果有错误，写入错误文件
        if not success or error_message:
            self._write_to_error_file(interaction_record)

        return interaction_id

    def _write_to_session_file(self, interaction: Dict):
        """写入会话专用文件"""
        date_str = interaction["timestamp"][:10]  # YYYY-MM-DD
        session_dir = self.base_dir / "by_session" / f"session_{interaction['session_id']}"
        session_dir.mkdir(exist_ok=True)

        file_path = session_dir / f"{date_str}.json"

        # 线程安全写入
        with threading.Lock():
            self._append_to_json_file(file_path, interaction)

    def _write_to_date_file(self, interaction: Dict):
        """写入日期汇总文件"""
        date_str = interaction["timestamp"][:10]
        file_path = self.base_dir / "by_date" / f"{date_str}_all_interactions.json"

        with threading.Lock():
            self._append_to_json_file(file_path, interaction)

    def _write_to_error_file(self, interaction: Dict):
        """写入错误专用文件"""
        date_str = interaction["timestamp"][:10]
        file_path = self.base_dir / "errors" / f"{date_str}_errors.json"

        with threading.Lock():
            self._append_to_json_file(file_path, interaction)

    def _append_to_json_file(self, file_path: Path, interaction: Dict):
        """安全地追加JSON数据到文件"""
        try:
            # 检查文件大小，必要时分割
            if file_path.exists() and file_path.stat().st_size > self.max_file_size:
                self._rotate_file(file_path)

            # 追加数据
            with open(file_path, 'a', encoding='utf-8') as f:
                json.dump(interaction, f, ensure_ascii=False, separators=(',', ':'))
                f.write('\n')

        except Exception as e:
            # 记录到错误日志
            print(f"写入LLM交互文件失败: {e}, 文件: {file_path}")

    def _rotate_file(self, file_path: Path):
        """文件轮转，避免单个文件过大"""
        if not file_path.exists():
            return

        # 移动到归档目录并压缩
        archive_dir = self.base_dir / "archive"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        archive_path = archive_dir / archive_name

        try:
            shutil.move(str(file_path), str(archive_path))

            # 压缩归档文件
            with open(archive_path, 'rb') as f_in:
                with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 删除未压缩文件
            archive_path.unlink()

        except Exception as e:
            print(f"文件轮转失败: {e}")

    def _add_to_real_time_buffer(self, interaction: Dict):
        """添加到实时缓冲区"""
        with self._buffer_lock:
            self._real_time_buffer.append(interaction)

            # 如果缓冲区满了，立即刷新
            if len(self._real_time_buffer) >= self.buffer_size:
                self._flush_real_time_buffer()

    def _flush_real_time_buffer(self):
        """刷新实时缓冲区到文件"""
        if not self._real_time_buffer:
            return

        buffer_copy = self._real_time_buffer.copy()
        self._real_time_buffer.clear()

        try:
            file_path = self.base_dir / "real_time" / "latest.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(buffer_copy, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"刷新实时缓冲区失败: {e}")

    def _start_flush_thread(self):
        """启动后台定时刷新线程"""
        def flush_worker():
            while True:
                try:
                    with self._buffer_lock:
                        self._flush_real_time_buffer()
                    threading.Event().wait(self.flush_interval)
                except Exception as e:
                    print(f"后台刷新线程错误: {e}")

        thread = threading.Thread(target=flush_worker, daemon=True)
        thread.start()

    def get_session_interactions(self, session_id: int, date: Optional[str] = None) -> List[Dict]:
        """获取指定会话的交互记录"""
        session_dir = self.base_dir / "by_session" / f"session_{session_id}"

        if not session_dir.exists():
            return []

        interactions = []

        # 如果指定了日期，只读取该日期的文件
        if date:
            file_path = session_dir / f"{date}.json"
            if file_path.exists():
                interactions.extend(self._read_json_file(file_path))
        else:
            # 读取所有日期的文件
            for file_path in session_dir.glob("*.json"):
                interactions.extend(self._read_json_file(file_path))

        # 按时间排序
        interactions.sort(key=lambda x: x.get("timestamp", ""))

        return interactions

    def get_latest_interactions(self, limit: int = 50) -> List[Dict]:
        """获取最新的交互记录"""
        file_path = self.base_dir / "real_time" / "latest.json"

        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                interactions = json.load(f)

            # 返回最新的limit条记录
            return interactions[-limit:] if len(interactions) > limit else interactions

        except Exception as e:
            print(f"读取最新交互记录失败: {e}")
            return []

    def get_date_interactions(self, date: str) -> List[Dict]:
        """获取指定日期的所有交互记录"""
        file_path = self.base_dir / "by_date" / f"{date}_all_interactions.json"

        if not file_path.exists():
            return []

        return self._read_json_file(file_path)

    def get_error_interactions(self, date: Optional[str] = None, days: int = 7) -> List[Dict]:
        """获取错误交互记录"""
        errors = []
        errors_dir = self.base_dir / "errors"

        if date:
            file_path = errors_dir / f"{date}_errors.json"
            if file_path.exists():
                errors.extend(self._read_json_file(file_path))
        else:
            # 获取最近几天的错误记录
            end_date = datetime.now()
            for i in range(days):
                target_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                file_path = errors_dir / f"{target_date}_errors.json"
                if file_path.exists():
                    errors.extend(self._read_json_file(file_path))

        return sorted(errors, key=lambda x: x.get("timestamp", ""), reverse=True)

    def _read_json_file(self, file_path: Path) -> List[Dict]:
        """读取JSON文件，支持行分隔的JSON格式"""
        interactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                if not content:
                    return []

                # 尝试解析为JSON数组
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        interactions.extend(data)
                    else:
                        interactions.append(data)
                except json.JSONDecodeError:
                    # 如果不是数组格式，按行解析
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                interaction = json.loads(line)
                                interactions.append(interaction)
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")

        return interactions

    def cleanup_old_files(self):
        """清理过期文件"""
        now = datetime.now()

        # 清理会话文件
        self._cleanup_directory(
            self.base_dir / "by_session",
            now,
            self.session_retention_days
        )

        # 清理日期文件
        self._cleanup_directory(
            self.base_dir / "by_date",
            now,
            self.session_retention_days
        )

        # 清理错误文件
        self._cleanup_directory(
            self.base_dir / "errors",
            now,
            self.error_retention_days
        )

    def _cleanup_directory(self, directory: Path, now: datetime, retention_days: int):
        """清理指定目录中的过期文件"""
        if not directory.exists():
            return

        cutoff_date = now - timedelta(days=retention_days)

        for file_path in directory.glob("*.json"):
            try:
                # 从文件名提取日期
                date_str = file_path.stem[:10]  # 假设格式为YYYY-MM-DD
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    file_path.unlink()

            except (ValueError, IndexError):
                # 如果无法解析日期，检查文件修改时间
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()

    def get_statistics(self) -> Dict[str, Any]:
        """获取记录统计信息"""
        stats = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "total_sessions": 0,
            "latest_interaction": None,
            "storage_info": {}
        }

        try:
            # 统计最近几天的数据
            recent_days = 7
            for i in range(recent_days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                interactions = self.get_date_interactions(date)

                stats["total_interactions"] += len(interactions)
                stats["successful_interactions"] += sum(1 for i in interactions if i.get("success", True))
                stats["failed_interactions"] += sum(1 for i in interactions if not i.get("success", True))

            # 统计会话数量
            session_dirs = list((self.base_dir / "by_session").glob("session_*"))
            stats["total_sessions"] = len(session_dirs)

            # 获取最新交互时间
            latest_interactions = self.get_latest_interactions(1)
            if latest_interactions:
                stats["latest_interaction"] = latest_interactions[0]["timestamp"]

            # 存储信息
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = Path(root) / file
                    size = file_path.stat().st_size
                    file_type = file_path.parent.name
                    if file_type not in stats["storage_info"]:
                        stats["storage_info"][file_type] = {"count": 0, "size": 0}
                    stats["storage_info"][file_type]["count"] += 1
                    stats["storage_info"][file_type]["size"] += size

        except Exception as e:
            print(f"获取统计信息失败: {e}")

        return stats


# 全局单例实例
llm_file_record = LLMFileRecordService()


def record_llm_interaction(session_id: int, role_name: str, prompt: str, response: str, **kwargs):
    """便捷的LLM交互记录函数"""
    return llm_file_record.record_interaction(
        session_id=session_id,
        role_name=role_name,
        prompt=prompt,
        response=response,
        **kwargs
    )


def get_session_llm_interactions(session_id: int) -> List[Dict]:
    """便捷的获取会话LLM交互记录函数"""
    return llm_file_record.get_session_interactions(session_id)


def get_latest_llm_interactions(limit: int = 50) -> List[Dict]:
    """便捷的获取最新LLM交互记录函数"""
    return llm_file_record.get_latest_interactions(limit)