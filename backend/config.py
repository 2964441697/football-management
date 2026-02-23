"""
配置文件

从环境变量加载应用配置，包括数据库连接字符串和密钥
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 生成更安全的默认密钥
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-9f8a7b6c5d4e3f2g1h0i9j8k7l6m5n4o3p2q1r0s')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///football.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    
    # 数据库连接池配置 (仅对 MySQL/PostgreSQL 有效，SQLite 会忽略)
    _db_url = os.getenv('DATABASE_URL', 'sqlite:///football.db')
    if _db_url and 'sqlite' not in _db_url:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 120,
            'pool_pre_ping': True
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时

class DevelopmentConfig(Config):
    DEBUG = True
    # 开发环境允许所有本地地址
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]

class ProductionConfig(Config):
    DEBUG = False
    
    def __init__(self):
        super().__init__()
        # 生产环境强制检查安全配置
        self._validate_production_config()
    
    @staticmethod
    def _validate_production_config():
        """验证生产环境必须的安全配置"""
        secret_key = os.getenv('SECRET_KEY')
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        
        # 检查是否设置了自定义密钥
        if not secret_key or secret_key.startswith('dev-'):
            raise ValueError(
                "生产环境必须设置 SECRET_KEY 环境变量！"
                "请在 .env 文件中添加: SECRET_KEY=<your-secure-random-key>"
                "\n可以使用以下命令生成: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        
        if not jwt_secret or jwt_secret.startswith('dev-'):
            raise ValueError(
                "生产环境必须设置 JWT_SECRET_KEY 环境变量！"
                "请在 .env 文件中添加: JWT_SECRET_KEY=<your-secure-random-key>"
                "\n可以使用以下命令生成: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        
        # 检查密钥长度
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY 长度必须至少为 32 个字符")
        
        if len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET_KEY 长度必须至少为 32 个字符")

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
