"""Redis缓存服务

提供高性能的数据缓存功能，支持步骤进度和LLM交互数据的缓存
"""

import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Union, Dict, List
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from flask import current_app
from app import db


class CacheService:
    """Redis缓存服务类"""

    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self.default_ttl = 300  # 5分钟默认TTL
        self.logger = logging.getLogger(__name__)

        if REDIS_AVAILABLE:
            self._initialize_redis()

    def _initialize_redis(self):
        """初始化Redis连接"""
        try:
            # 从环境变量获取Redis配置
            redis_host = current_app.config.get('REDIS_HOST', 'localhost')
            redis_port = current_app.config.get('REDIS_PORT', 6379)
            redis_db = current_app.config.get('REDIS_DB', 0)
            redis_password = current_app.config.get('REDIS_PASSWORD', None)

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            self.logger.info("Redis cache service initialized successfully")

        except Exception as e:
            self.enabled = False
            self.logger.warning(f"Redis not available, cache disabled: {str(e)}")

    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        return f"{prefix}:{identifier}"

    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return pickle.dumps(value).hex()

    def _deserialize_value(self, value: str, use_pickle: bool = False) -> Any:
        """反序列化值"""
        if not value:
            return None

        try:
            if use_pickle:
                return pickle.loads(bytes.fromhex(value))
            else:
                return json.loads(value)
        except (json.JSONDecodeError, ValueError, TypeError, pickle.UnpicklingError):
            self.logger.warning(f"Failed to deserialize cached value: {value[:100]}...")
            return None

    def get(self, key: str, default: Any = None, use_pickle: bool = False) -> Any:
        """获取缓存值"""
        if not self.enabled:
            return default

        try:
            cached_value = self.redis_client.get(key)
            if cached_value is None:
                return default

            return self._deserialize_value(cached_value, use_pickle)

        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {str(e)}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None, use_pickle: bool = False) -> bool:
        """设置缓存值"""
        if not self.enabled:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized_value = self._serialize_value(value)

            if self.redis_client.setex(key, ttl, serialized_value):
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled:
            return True

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.enabled:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """清除缓存"""
        if not self.enabled:
            return 0

        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                return self.redis_client.flushdb()
        except Exception as e:
            self.logger.error(f"Cache clear error: {str(e)}")
            return 0

    def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存键 (alias for clear)"""
        return self.clear(pattern)

    def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self.enabled:
            return 0

        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            self.logger.error(f"Cache increment error for key {key}: {str(e)}")
            return 0

    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间"""
        if not self.enabled:
            return False

        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            self.logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False


class StepProgressCache:
    """步骤进度专用缓存"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)

    def get_session_progress(self, session_id: int, include_details: bool = False) -> Optional[Dict]:
        """获取会话进度缓存"""
        key = self.cache._get_cache_key('step_progress', f"session_{session_id}_details_{include_details}")
        return self.cache.get(key)

    def set_session_progress(self, session_id: int, progress_data: Dict, ttl: int = 600) -> bool:
        """设置会话进度缓存"""
        key = self.cache._get_cache_key('step_progress', f"session_{session_id}_details_{progress_data.get('include_details', False)}")
        return self.cache.set(key, progress_data, ttl)

    def invalidate_session_progress(self, session_id: int) -> bool:
        """清除会话进度缓存"""
        pattern = self.cache._get_cache_key('step_progress', f"session_{session_id}_*")
        return self.cache.clear(pattern)

    def get_flow_visualization(self, session_id: int) -> Optional[Dict]:
        """获取流程可视化缓存"""
        key = self.cache._get_cache_key('flow_viz', f"session_{session_id}")
        return self.cache.get(key)

    def set_flow_visualization(self, session_id: int, viz_data: Dict, ttl: int = 300) -> bool:
        """设置流程可视化缓存"""
        key = self.cache._get_cache_key('flow_viz', f"session_{session_id}")
        return self.cache.set(key, viz_data, ttl)


class LLMInteractionCache:
    """LLM交互专用缓存"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)

    def get_session_interactions(self, session_id: int, page: int = 1, per_page: int = 50) -> Optional[Dict]:
        """获取会话LLM交互缓存"""
        key = self.cache._get_cache_key('llm_interactions', f"session_{session_id}_page_{page}_perpage_{per_page}")
        return self.cache.get(key)

    def set_session_interactions(self, session_id: int, interactions_data: Dict, ttl: int = 180) -> bool:
        """设置会话LLM交互缓存"""
        key = self.cache._get_cache_key('llm_interactions', f"session_{session_id}_page_{interactions_data.get('pagination', {}).get('page', 1)}_perpage_{interactions_data.get('pagination', {}).get('per_page', 50)}")
        return self.cache.set(key, interactions_data, ttl)

    def get_llm_interaction_details(self, interaction_id: int) -> Optional[Dict]:
        """获取LLM交互详情缓存"""
        key = self.cache._get_cache_key('llm_detail', f"interaction_{interaction_id}")
        return self.cache.get(key)

    def set_llm_interaction_details(self, interaction_id: int, details: Dict, ttl: int = 600) -> bool:
        """设置LLM交互详情缓存"""
        key = self.cache._get_cache_key('llm_detail', f"interaction_{interaction_id}")
        return self.cache.set(key, details, ttl)

    def invalidate_session_llm_data(self, session_id: int) -> bool:
        """清除会话LLM数据缓存"""
        pattern = self.cache._get_cache_key('llm_interactions', f"session_{session_id}_*")
        return self.cache.clear(pattern)

    def get_session_statistics(self, session_id: int, days: int = 7) -> Optional[Dict]:
        """获取会话统计缓存"""
        key = self.cache._get_cache_key('llm_stats', f"session_{session_id}_days_{days}")
        return self.cache.get(key)

    def set_session_statistics(self, session_id: int, stats: Dict, ttl: int = 300) -> bool:
        """设置会话统计缓存"""
        key = self.cache._get_cache_key('llm_stats', f"session_{session_id}_days_{days}")
        return self.cache.set(key, stats, ttl)

    def get_system_metrics(self) -> Optional[Dict]:
        """获取系统指标缓存"""
        key = self.cache._get_cache_key('system', 'metrics')
        return self.cache.get(key)

    def set_system_metrics(self, metrics: Dict, ttl: int = 60) -> bool:
        """设置系统指标缓存"""
        key = self.cache._get_cache_key('system', 'metrics')
        return self.cache.set(key, metrics, ttl)

    def get_usage_trends(self, days: int = 30) -> Optional[Dict]:
        """获取使用趋势缓存"""
        key = self.cache._get_cache_key('usage_trends', f"days_{days}")
        return self.cache.get(key)

    def set_usage_trends(self, trends: Dict, ttl: int = 3600) -> bool:
        """设置使用趋势缓存"""
        key = self.cache._get_cache_key('usage_trends', f"days_{days}")
        return self.cache.set(key, trends, ttl)


class RealtimeUpdateCache:
    """实时更新专用缓存"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)

    def get_active_sessions(self) -> Optional[List]:
        """获取活跃会话列表缓存"""
        key = self.cache._get_cache_key('realtime', 'active_sessions')
        return self.cache.get(key)

    def set_active_sessions(self, sessions: List, ttl: int = 30) -> bool:
        """设置活跃会话列表缓存"""
        key = self.cache._get_cache_key('realtime', 'active_sessions')
        return self.cache.set(key, sessions, ttl)

    def get_connection_stats(self) -> Optional[Dict]:
        """获取连接统计缓存"""
        key = self.cache._get_cache_key('realtime', 'connection_stats')
        return self.cache.get(key)

    def set_connection_stats(self, stats: Dict, ttl: int = 60) -> bool:
        """设置连接统计缓存"""
        key = self.cache._get_cache_key('realtime', 'connection_stats')
        return self.cache.set(key, stats, ttl)


def cache_result(ttl: Optional[int] = None, key_prefix: str = "", use_pickle: bool = False):
    """缓存结果装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            cache_service = get_cache_service()

            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, use_pickle=use_pickle)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            cache_service.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """清理特定模式的缓存"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = get_cache_service()
            cache_service.clear(pattern)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局缓存服务实例
_cache_service_instance = None

def get_cache_service() -> CacheService:
    """获取缓存服务实例（单例模式）"""
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    return _cache_service_instance

def get_step_progress_cache() -> StepProgressCache:
    """获取步骤进度缓存实例"""
    return StepProgressCache(get_cache_service())

def get_llm_interaction_cache() -> LLMInteractionCache:
    """获取LLM交互缓存实例"""
    return LLMInteractionCache(get_cache_service())

def get_realtime_update_cache() -> RealtimeUpdateCache:
    """获取实时更新缓存实例"""
    return RealtimeUpdateCache(get_cache_service())


class KnowledgeBaseCache:
    """知识库专用缓存"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)
        self.KB_LIST_TTL = 900  # 15分钟TTL，符合Requirement 1.5

    def get_knowledge_bases_list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Optional[Dict]:
        """获取知识库列表缓存"""
        # 创建缓存键，包含所有查询参数
        cache_key_parts = [
            f"page_{page}",
            f"perpage_{per_page}",
            f"sort_{sort_by}_{sort_order}"
        ]

        if status:
            cache_key_parts.append(f"status_{status}")

        if search:
            cache_key_parts.append(f"search_{hash(search)}")

        cache_key_suffix = "_".join(cache_key_parts)
        key = self.cache._get_cache_key('knowledge_bases_list', cache_key_suffix)

        return self.cache.get(key)

    def set_knowledge_bases_list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        data: Dict = None
    ) -> bool:
        """设置知识库列表缓存"""
        if not data:
            return False

        # 创建与获取方法相同的缓存键
        cache_key_parts = [
            f"page_{page}",
            f"perpage_{per_page}",
            f"sort_{sort_by}_{sort_order}"
        ]

        if status:
            cache_key_parts.append(f"status_{status}")

        if search:
            cache_key_parts.append(f"search_{hash(search)}")

        cache_key_suffix = "_".join(cache_key_parts)
        key = self.cache._get_cache_key('knowledge_bases_list', cache_key_suffix)

        return self.cache.set(key, data, ttl=self.KB_LIST_TTL)

    def get_knowledge_base_statistics(self) -> Optional[Dict]:
        """获取知识库统计缓存"""
        key = self.cache._get_cache_key('knowledge_base', 'statistics')
        return self.cache.get(key)

    def set_knowledge_base_statistics(self, stats: Dict) -> bool:
        """设置知识库统计缓存"""
        key = self.cache._get_cache_key('knowledge_base', 'statistics')
        return self.cache.set(key, stats, ttl=self.KB_LIST_TTL)

    def get_ragflow_datasets_list(self) -> Optional[List]:
        """获取RAGFlow数据集列表缓存"""
        key = self.cache._get_cache_key('ragflow', 'datasets_list')
        return self.cache.get(key)

    def set_ragflow_datasets_list(self, datasets: List) -> bool:
        """设置RAGFlow数据集列表缓存"""
        key = self.cache._get_cache_key('ragflow', 'datasets_list')
        return self.cache.set(key, datasets, ttl=self.KB_LIST_TTL)

    def get_knowledge_base_by_id(self, kb_id: int) -> Optional[Dict]:
        """获取特定知识库缓存"""
        key = self.cache._get_cache_key('knowledge_base', f"id_{kb_id}")
        return self.cache.get(key)

    def set_knowledge_base_by_id(self, kb_id: int, kb_data: Dict) -> bool:
        """设置特定知识库缓存"""
        key = self.cache._get_cache_key('knowledge_base', f"id_{kb_id}")
        return self.cache.set(key, kb_data, ttl=self.KB_LIST_TTL)

    def get_knowledge_base_by_ragflow_id(self, ragflow_id: str) -> Optional[Dict]:
        """通过RAGFlow ID获取知识库缓存"""
        key = self.cache._get_cache_key('knowledge_base', f"ragflow_{ragflow_id}")
        return self.cache.get(key)

    def set_knowledge_base_by_ragflow_id(self, ragflow_id: str, kb_data: Dict) -> bool:
        """通过RAGFlow ID设置知识库缓存"""
        key = self.cache._get_cache_key('knowledge_base', f"ragflow_{ragflow_id}")
        return self.cache.set(key, kb_data, ttl=self.KB_LIST_TTL)

    def invalidate_knowledge_base_cache(self, kb_id: Optional[int] = None) -> bool:
        """手动刷新知识库缓存 - 支持单个或全部清除"""
        try:
            if kb_id:
                # 清除特定知识库的所有缓存
                patterns = [
                    self.cache._get_cache_key('knowledge_base', f"id_{kb_id}"),
                    self.cache._get_cache_key('knowledge_base', f"ragflow_*"),
                ]

                for pattern in patterns:
                    self.cache.clear(pattern)

                self.logger.info(f"已清除知识库 {kb_id} 的缓存")
            else:
                # 清除所有知识库相关缓存（手动刷新）
                patterns = [
                    self.cache._get_cache_key('knowledge_bases_list', '*'),
                    self.cache._get_cache_key('knowledge_base', '*'),
                    self.cache._get_cache_key('ragflow', '*'),
                ]

                for pattern in patterns:
                    self.cache.clear(pattern)

                self.logger.info("已手动刷新所有知识库缓存")

            return True

        except Exception as e:
            self.logger.error(f"清除知识库缓存失败: {str(e)}")
            return False

    def get_last_refresh_time(self) -> Optional[datetime]:
        """获取上次刷新时间"""
        key = self.cache._get_cache_key('knowledge_base', 'last_refresh')
        timestamp = self.cache.get(key)
        if timestamp:
            try:
                return datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return None
        return None

    def set_last_refresh_time(self) -> bool:
        """设置上次刷新时间"""
        key = self.cache._get_cache_key('knowledge_base', 'last_refresh')
        timestamp = datetime.utcnow().isoformat()
        return self.cache.set(key, timestamp, ttl=86400)  # 24小时


class ConversationHistoryCache:
    """对话历史专用缓存"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)
        self.CONVERSATION_TTL = 3600  # 1小时TTL用于用户会话期间

    def get_conversation_history(
        self,
        knowledge_base_id: int,
        user_session_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None
    ) -> Optional[Dict]:
        """获取对话历史缓存"""
        # 构建缓存键
        cache_parts = [
            f"kb_{knowledge_base_id}",
            f"page_{page}",
            f"perpage_{per_page}"
        ]

        if user_session_id:
            cache_parts.append(f"session_{user_session_id}")

        if status_filter:
            cache_parts.append(f"status_{status_filter}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('conversation_history', cache_key_suffix)

        return self.cache.get(key)

    def set_conversation_history(
        self,
        knowledge_base_id: int,
        history_data: Dict,
        user_session_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """设置对话历史缓存"""
        if not history_data:
            return False

        # 构建与获取方法相同的缓存键
        cache_parts = [
            f"kb_{knowledge_base_id}",
            f"page_{page}",
            f"perpage_{per_page}"
        ]

        if user_session_id:
            cache_parts.append(f"session_{user_session_id}")

        if status_filter:
            cache_parts.append(f"status_{status_filter}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('conversation_history', cache_key_suffix)

        # 使用指定的TTL或默认TTL
        cache_ttl = ttl or self.CONVERSATION_TTL

        return self.cache.set(key, history_data, ttl=cache_ttl)

    def get_conversation_detail(self, conversation_id: int) -> Optional[Dict]:
        """获取特定对话详情缓存"""
        key = self.cache._get_cache_key('conversation_detail', f"id_{conversation_id}")
        return self.cache.get(key)

    def set_conversation_detail(
        self,
        conversation_id: int,
        detail_data: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """设置特定对话详情缓存"""
        if not detail_data:
            return False

        key = self.cache._get_cache_key('conversation_detail', f"id_{conversation_id}")
        cache_ttl = ttl or self.CONVERSATION_TTL

        return self.cache.set(key, detail_data, ttl=cache_ttl)

    def get_user_session_conversations(
        self,
        user_session_id: str,
        knowledge_base_id: Optional[int] = None
    ) -> Optional[List]:
        """获取用户会话期间的对话列表缓存"""
        cache_parts = [f"session_{user_session_id}"]

        if knowledge_base_id:
            cache_parts.append(f"kb_{knowledge_base_id}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('user_conversations', cache_key_suffix)

        return self.cache.get(key)

    def set_user_session_conversations(
        self,
        user_session_id: str,
        conversations: List,
        knowledge_base_id: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """设置用户会话期间的对话列表缓存"""
        cache_parts = [f"session_{user_session_id}"]

        if knowledge_base_id:
            cache_parts.append(f"kb_{knowledge_base_id}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('user_conversations', cache_key_suffix)
        cache_ttl = ttl or self.CONVERSATION_TTL

        return self.cache.set(key, conversations, ttl=cache_ttl)

    def add_conversation_to_session(
        self,
        user_session_id: str,
        conversation_data: Dict,
        knowledge_base_id: Optional[int] = None
    ) -> bool:
        """向用户会话缓存添加新对话"""
        try:
            # 获取当前会话的对话列表
            current_conversations = self.get_user_session_conversations(
                user_session_id, knowledge_base_id
            ) or []

            # 在列表开头添加新对话（最新的在前）
            current_conversations.insert(0, conversation_data)

            # 限制缓存的对话数量（保留最近50个）
            current_conversations = current_conversations[:50]

            # 更新缓存
            return self.set_user_session_conversations(
                user_session_id, current_conversations, knowledge_base_id
            )

        except Exception as e:
            self.logger.error(f"添加对话到会话缓存失败: {str(e)}")
            return False

    def invalidate_conversation_cache(
        self,
        conversation_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
        user_session_id: Optional[str] = None
    ) -> bool:
        """清除对话历史缓存"""
        try:
            if conversation_id:
                # 清除特定对话缓存
                key = self.cache._get_cache_key('conversation_detail', f"id_{conversation_id}")
                self.cache.delete(key)
                self.logger.info(f"已清除对话 {conversation_id} 的缓存")

            if knowledge_base_id:
                # 清除特定知识库的对话历史缓存
                pattern = self.cache._get_cache_key('conversation_history', f"kb_{knowledge_base_id}_*")
                self.cache.clear(pattern)
                self.logger.info(f"已清除知识库 {knowledge_base_id} 的对话历史缓存")

            if user_session_id:
                # 清除特定用户会话的缓存
                pattern = self.cache._get_cache_key('user_conversations', f"session_{user_session_id}_*")
                self.cache.clear(pattern)
                self.logger.info(f"已清除用户会话 {user_session_id} 的对话缓存")

            return True

        except Exception as e:
            self.logger.error(f"清除对话缓存失败: {str(e)}")
            return False

    def get_conversation_statistics(
        self,
        knowledge_base_id: Optional[int] = None,
        days: int = 7
    ) -> Optional[Dict]:
        """获取对话统计缓存"""
        cache_parts = [f"days_{days}"]

        if knowledge_base_id:
            cache_parts.append(f"kb_{knowledge_base_id}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('conversation_stats', cache_key_suffix)

        return self.cache.get(key)

    def set_conversation_statistics(
        self,
        stats: Dict,
        knowledge_base_id: Optional[int] = None,
        days: int = 7,
        ttl: int = 600  # 10分钟
    ) -> bool:
        """设置对话统计缓存"""
        cache_parts = [f"days_{days}"]

        if knowledge_base_id:
            cache_parts.append(f"kb_{knowledge_base_id}")

        cache_key_suffix = "_".join(cache_parts)
        key = self.cache._get_cache_key('conversation_stats', cache_key_suffix)

        return self.cache.set(key, stats, ttl=ttl)

    def invalidate_all_conversation_cache(self) -> bool:
        """清除所有对话相关缓存"""
        try:
            patterns = [
                self.cache._get_cache_key('conversation_history', '*'),
                self.cache._get_cache_key('conversation_detail', '*'),
                self.cache._get_cache_key('user_conversations', '*'),
                self.cache._get_cache_key('conversation_stats', '*'),
            ]

            for pattern in patterns:
                self.cache.clear(pattern)

            self.logger.info("已清除所有对话历史缓存")
            return True

        except Exception as e:
            self.logger.error(f"清除所有对话缓存失败: {str(e)}")
            return False


def get_knowledge_base_cache() -> KnowledgeBaseCache:
    """获取知识库缓存实例"""
    return KnowledgeBaseCache(get_cache_service())


def get_conversation_history_cache() -> ConversationHistoryCache:
    """获取对话历史缓存实例"""
    return ConversationHistoryCache(get_cache_service())