#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow重试策略

提供智能的重试机制和错误处理逻辑
"""

import time
import logging
import random
from typing import Callable, Any, Optional, Type, Union
from functools import wraps
from enum import Enum

from ..models.config import RAGFlowConfig

logger = logging.getLogger(__name__)


class RetryMode(Enum):
    """重试模式"""
    FIXED = "fixed"          # 固定延迟
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"        # 线性增长
    RANDOM = "random"        # 随机延迟


class RetryStrategy:
    """重试策略管理器"""

    def __init__(self, config: RAGFlowConfig):
        self.config = config
        self.retry_mode = RetryMode.EXPONENTIAL
        self.max_retries = config.max_retries
        self.base_delay = config.retry_delay
        self.max_delay = 60.0
        self.jitter = True
        self.retryable_exceptions = self._get_retryable_exceptions()

    def _get_retryable_exceptions(self) -> tuple:
        """获取可重试的异常类型"""
        try:
            from ..models.config import RAGFlowAPIError, RAGFlowConnectionError
            return (
                RAGFlowConnectionError,
                ConnectionError,
                TimeoutError,
                OSError,
            )
        except ImportError:
            # 如果RAGFlow异常类不可用，使用基础异常类型
            return (
                ConnectionError,
                TimeoutError,
                OSError,
            )

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        # 检查重试次数
        if attempt >= self.max_retries:
            return False

        # 检查异常类型
        return isinstance(exception, self.retryable_exceptions)

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.retry_mode == RetryMode.FIXED:
            delay = self.base_delay

        elif self.retry_mode == RetryMode.LINEAR:
            delay = self.base_delay * (attempt + 1)

        elif self.retry_mode == RetryMode.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)

        elif self.retry_mode == RetryMode.RANDOM:
            delay = self.base_delay * (1 + random.random())

        else:
            delay = self.base_delay

        # 应用最大延迟限制
        delay = min(delay, self.max_delay)

        # 添加抖动避免雷群效应
        if self.jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数并在失败时重试"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    logger.error(f"执行失败，不再重试: {str(e)}")
                    raise

                delay = self.calculate_delay(attempt)
                logger.warning(f"执行失败 (尝试 {attempt + 1}/{self.max_retries + 1})，"
                             f"将在 {delay:.2f}s 后重试: {str(e)}")

                time.sleep(delay)

        # 所有重试都失败了
        logger.error(f"所有重试都失败了，最后错误: {str(last_exception)}")
        raise last_exception

    def __call__(self, func: Callable) -> Callable:
        """装饰器用法"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute_with_retry(func, *args, **kwargs)
        return wrapper


class BackoffStrategy:
    """退避策略"""

    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """指数退避"""
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

    @staticmethod
    def linear_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """线性退避"""
        delay = base_delay * (attempt + 1)
        return min(delay, max_delay)

    @staticmethod
    def fixed_backoff(attempt: int, base_delay: float = 1.0) -> float:
        """固定延迟"""
        return base_delay

    @staticmethod
    def jittered_backoff(attempt: int, base_delay: float = 1.0, jitter_factor: float = 0.1) -> float:
        """抖动延迟"""
        delay = base_delay * (attempt + 1)
        jitter_range = delay * jitter_factor
        return delay + random.uniform(-jitter_range, jitter_range)


class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        """装饰器用法"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("熔断器状态: OPEN -> HALF_OPEN")
                else:
                    raise Exception("熔断器处于开启状态，拒绝执行")

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("熔断器状态: HALF_OPEN -> CLOSED")
                return result

            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"熔断器状态: {self.state} (失败次数: {self.failure_count})")

                raise

        return wrapper


def retry_on_exception(retries: int = 3, delay: float = 1.0,
                      backoff: str = "exponential", exceptions: tuple = (Exception,)):
    """简单的重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == retries:
                        break

                    if backoff == "exponential":
                        wait_time = delay * (2 ** attempt)
                    elif backoff == "linear":
                        wait_time = delay * (attempt + 1)
                    else:
                        wait_time = delay

                    logger.warning(f"重试 {attempt + 1}/{retries + 1}: {str(e)}")
                    time.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator


class Bulkhead:
    """舱壁模式 - 限制并发请求数量"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.current_concurrent = 0
        self.queue = []

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.current_concurrent >= self.max_concurrent:
                raise Exception("超过最大并发限制")

            self.current_concurrent += 1
            try:
                return func(*args, **kwargs)
            finally:
                self.current_concurrent -= 1
        return wrapper


class TimeoutHandler:
    """超时处理器"""

    @staticmethod
    def with_timeout(timeout_seconds: float):
        """设置超时装饰器"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"函数执行超时 ({timeout_seconds}s)")

                # 设置信号处理器
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout_seconds))

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # 取消超时
                    signal.alarm(0)

            return wrapper
        return decorator