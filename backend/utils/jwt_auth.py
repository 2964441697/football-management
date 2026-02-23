"""
JWT 认证工具模块

提供 JWT token 的生成、验证和装饰器功能
"""
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g

logger = logging.getLogger(__name__)

# 常量定义
TOKEN_EXPIRE_HOURS = 24
TOKEN_REFRESH_HOURS = 168  # 7 days


def generate_token(user_id: int, username: str, role: str) -> dict:
    """
    生成 JWT access token 和 refresh token
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
    
    Returns:
        包含 access_token 和 refresh_token 的字典
    """
    secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
    
    # Access token
    access_payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
    
    # Refresh token
    refresh_payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_REFRESH_HOURS),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': TOKEN_EXPIRE_HOURS * 3600
    }


def verify_token(token: str) -> dict:
    """
    验证 JWT token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的 payload 字典，验证失败返回 None
    """
    if not token:
        return None
    
    secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_token_from_request() -> str:
    """
    从请求头中提取 token
    
    Returns:
        token 字符串，不存在返回 None
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def login_required(f):
    """
    登录验证装饰器
    
    验证请求是否携带有效的 JWT token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'error': '未提供认证令牌', 'code': 'TOKEN_MISSING'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': '认证令牌无效或已过期', 'code': 'TOKEN_INVALID'}), 401
        
        if payload.get('type') != 'access':
            return jsonify({'error': '令牌类型错误', 'code': 'TOKEN_TYPE_ERROR'}), 401
        
        # 将用户信息存储到 g 对象中
        g.current_user = {
            'id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    管理员权限装饰器
    
    验证用户是否为管理员
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.current_user.get('role') != 'admin':
            return jsonify({'error': '需要管理员权限', 'code': 'ADMIN_REQUIRED'}), 403
        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles: list):
    """
    角色权限装饰器
    
    Args:
        allowed_roles: 允许的角色列表
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user_role = g.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'error': '权限不足',
                    'code': 'PERMISSION_DENIED',
                    'required_roles': allowed_roles
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def optional_login(f):
    """
    可选登录装饰器
    
    如果携带 token 则验证并设置用户信息，否则设置为 None
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if token:
            payload = verify_token(token)
            if payload and payload.get('type') == 'access':
                g.current_user = {
                    'id': payload.get('user_id'),
                    'username': payload.get('username'),
                    'role': payload.get('role')
                }
            else:
                g.current_user = None
        else:
            g.current_user = None
        
        return f(*args, **kwargs)
    return decorated_function


def refresh_access_token(refresh_token: str) -> dict:
    """
    使用 refresh token 刷新 access token
    
    Args:
        refresh_token: refresh token 字符串
    
    Returns:
        新的 token 字典，失败返回 None
    """
    payload = verify_token(refresh_token)
    
    if not payload:
        return None
    
    if payload.get('type') != 'refresh':
        return None
    
    # 从数据库获取用户信息
    from models import User
    user = User.query.get(payload.get('user_id'))
    
    if not user:
        return None
    
    return generate_token(user.id, user.username, user.role)
