"""
简化的应用配置

基于simple_llm.py的重写版本，专注于Anthropic集成
大幅简化LLM配置复杂度
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///multi_role_chat.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 简化的LLM服务配置 - 只支持Anthropic
    LLM_PROVIDER = 'anthropic'  # 固定为anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')  # 可以为None，让SDK自动寻找
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    ANTHROPIC_MAX_TOKENS = int(os.environ.get('ANTHROPIC_MAX_TOKENS', '4096'))

    # API配置
    API_HOST = os.environ.get('API_HOST') or '0.0.0.0'
    API_PORT = int(os.environ.get('API_PORT') or 5000)
    API_DEBUG = os.environ.get('API_DEBUG', 'False').lower() == 'true'

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/app.log'
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    # LLM专用日志配置
    LLM_LOG_FILE = os.environ.get('LLM_LOG_FILE') or 'logs/llm_requests.log'
    ENABLE_LLM_SPECIAL_LOG = os.environ.get('ENABLE_LLM_SPECIAL_LOG', 'true').lower() == 'true'

    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # 会话配置
    MAX_CONTEXT_MESSAGES = 50
    MAX_LOOP_COUNT = 10
    LLM_TIMEOUT = 60  # 秒

    # RAGFlow集成配置
    RAGFLOW_API_BASE_URL = os.environ.get('RAGFLOW_API_BASE_URL', '')
    RAGFLOW_API_KEY = os.environ.get('RAGFLOW_API_KEY', '')
    RAGFLOW_TIMEOUT = int(os.environ.get('RAGFLOW_TIMEOUT', '30'))
    RAGFLOW_MAX_RETRIES = int(os.environ.get('RAGFLOW_MAX_RETRIES', '3'))
    RAGFLOW_RETRY_DELAY = float(os.environ.get('RAGFLOW_RETRY_DELAY', '1.0'))
    RAGFLOW_VERIFY_SSL = os.environ.get('RAGFLOW_VERIFY_SSL', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 打印SQL语句


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}