"""
用户认证API路由

提供用户认证相关接口：
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- POST /api/auth/refresh - 刷新token
- GET /api/auth/me - 获取当前用户信息
- PUT /api/auth/update - 更新用户信息
- PUT /api/auth/change-password - 修改密码
- PUT /api/auth/role - 修改用户角色（admin专用）
"""
import logging
import os
import re
import time
from flask import Blueprint, request, jsonify, g
from models import User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.jwt_auth import (
    generate_token, 
    login_required, 
    admin_required, 
    refresh_access_token,
    optional_login
)

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)

# 常量定义
ALLOWED_ROLES = ['admin', 'coach', 'viewer']
MIN_USERNAME_LENGTH = 3
MIN_PASSWORD_LENGTH = 6
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'viewer')
        
        # 参数验证
        if not all([username, email, password]):
            return jsonify({'error': '缺少必要字段'}), 400
        
        if len(username) < MIN_USERNAME_LENGTH:
            return jsonify({'error': f'用户名至少{MIN_USERNAME_LENGTH}个字符'}), 400
        
        if len(password) < MIN_PASSWORD_LENGTH:
            return jsonify({'error': f'密码至少{MIN_PASSWORD_LENGTH}个字符'}), 400
        
        if not validate_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        if role not in ALLOWED_ROLES:
            return jsonify({'error': '无效的角色'}), 400
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        # 生成 token
        tokens = generate_token(user.id, user.username, user.role)
        
        logger.info(f"用户注册成功: {username}")
        
        return jsonify({
            'user': user.to_dict(),
            **tokens
        }), 201
        
    except Exception as e:
        logger.error(f"注册错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': '用户名或密码为空'}), 400
        
        # 支持用户名或邮箱登录
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not user.password_hash:
            return jsonify({'error': '用户密码未设置'}), 401
        
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 生成 token
        tokens = generate_token(user.id, user.username, user.role)
        
        logger.info(f"用户登录成功: {username}")
        
        return jsonify({
            'user': user.to_dict(),
            **tokens
        }), 200
        
    except Exception as e:
        logger.error(f"登录错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/refresh', methods=['POST'])
def refresh():
    """刷新 access token"""
    try:
        data = request.json or {}
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': '缺少 refresh_token'}), 400
        
        tokens = refresh_access_token(refresh_token)
        
        if not tokens:
            return jsonify({'error': 'refresh_token 无效或已过期'}), 401
        
        return jsonify(tokens), 200
        
    except Exception as e:
        logger.error(f"刷新token错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    try:
        user = User.query.get(g.current_user['id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"获取用户信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/update', methods=['PUT'])
@login_required
def update_user():
    """更新用户信息"""
    try:
        data = request.json or {}
        user = User.query.get(g.current_user['id'])
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 更新用户名
        new_username = data.get('username', '').strip()
        if new_username and new_username != user.username:
            if len(new_username) < MIN_USERNAME_LENGTH:
                return jsonify({'error': f'用户名至少{MIN_USERNAME_LENGTH}个字符'}), 400
            if User.query.filter(User.username == new_username, User.id != user.id).first():
                return jsonify({'error': '用户名已存在'}), 400
            user.username = new_username
        
        # 更新邮箱
        new_email = data.get('email', '').strip()
        if new_email and new_email != user.email:
            if not validate_email(new_email):
                return jsonify({'error': '邮箱格式不正确'}), 400
            if User.query.filter(User.email == new_email, User.id != user.id).first():
                return jsonify({'error': '邮箱已存在'}), 400
            user.email = new_email
        
        db.session.commit()
        
        logger.info(f"用户信息更新成功: {user.username}")
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"更新用户信息错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    try:
        data = request.json or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': '参数不完整'}), 400
        
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return jsonify({'error': f'新密码至少{MIN_PASSWORD_LENGTH}个字符'}), 400
        
        user = User.query.get(g.current_user['id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if not check_password_hash(user.password_hash, old_password):
            return jsonify({'error': '原密码错误'}), 400
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        logger.info(f"用户密码修改成功: {user.username}")
        
        return jsonify({'message': '密码修改成功'}), 200
        
    except Exception as e:
        logger.error(f"修改密码错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传用户头像"""
    try:
        user = User.query.get(g.current_user['id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if 'avatar' not in request.files:
            return jsonify({'error': '请选择图片'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': '请选择图片'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的图片格式'}), 400
        
        # 创建上传目录
        base_dir = os.path.dirname(os.path.dirname(__file__))
        avatars_dir = os.path.join(base_dir, 'static', 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)
        
        # 删除旧头像
        if user.avatar:
            old_path = os.path.join(base_dir, user.avatar.lstrip('/'))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        
        # 保存新头像
        ext = os.path.splitext(file.filename)[1] if file.filename else '.png'
        filename = secure_filename(f"avatar_{user.id}_{int(time.time())}{ext}")
        file_path = os.path.join(avatars_dir, filename)
        file.save(file_path)
        
        avatar_url = f'/static/avatars/{filename}'
        user.avatar = avatar_url
        db.session.commit()
        
        logger.info(f"用户头像上传成功: {user.username}")
        
        return jsonify({'avatar': avatar_url}), 200
        
    except Exception as e:
        logger.error(f"上传头像错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500


@bp.route('/role', methods=['PUT'])
@admin_required
def update_user_role():
    """修改用户角色（仅管理员）"""
    try:
        data = request.json or {}
        target_user_id = data.get('user_id')
        new_role = data.get('role')
        
        if not target_user_id or not new_role:
            return jsonify({'error': '参数不完整'}), 400
        
        if new_role not in ALLOWED_ROLES:
            return jsonify({'error': '无效的角色'}), 400
        
        target_user = User.query.get(int(target_user_id))
        if not target_user:
            return jsonify({'error': '目标用户不存在'}), 404
        
        # 防止管理员降级自己
        if target_user.id == g.current_user['id'] and new_role != 'admin':
            return jsonify({'error': '不能降级自己的权限'}), 400
        
        target_user.role = new_role
        db.session.commit()
        
        logger.info(f"用户角色修改成功: {target_user.username} -> {new_role}")
        
        return jsonify({
            'user': target_user.to_dict(),
            'message': '角色修改成功'
        }), 200
        
    except Exception as e:
        logger.error(f"修改用户角色错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户列表（仅管理员）"""
    try:
        users = User.query.all()
        return jsonify([u.to_dict() for u in users]), 200
        
    except Exception as e:
        logger.error(f"获取用户列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/roles/choices', methods=['GET'])
def get_role_choices():
    """获取角色选项列表"""
    return jsonify([
        {'value': role, 'label': label} 
        for role, label in User.ROLE_CHOICES
    ]), 200


@bp.route('/backgrounds', methods=['GET'])
@optional_login
def get_backgrounds():
    """获取背景图片列表"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backgrounds_dir = os.path.join(base_dir, '..', 'frontend', 'public', 'backgrounds')
        backgrounds_dir = os.path.normpath(backgrounds_dir)
        
        if not os.path.exists(backgrounds_dir):
            return jsonify([]), 200
        
        backgrounds = []
        for filename in os.listdir(backgrounds_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                backgrounds.append({
                    'id': f'bg_{filename}',
                    'name': filename.rsplit('.', 1)[0],
                    'type': 'image',
                    'value': f'/backgrounds/{filename}'
                })
        
        return jsonify(backgrounds), 200
        
    except Exception as e:
        logger.error(f"获取背景列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/backgrounds/upload', methods=['POST'])
@admin_required
def upload_background():
    """上传背景图片（仅管理员）"""
    try:
        if 'background' not in request.files:
            return jsonify({'error': '请选择图片'}), 400
        
        file = request.files['background']
        if file.filename == '':
            return jsonify({'error': '请选择图片'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的图片格式'}), 400
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backgrounds_dir = os.path.join(base_dir, '..', 'frontend', 'public', 'backgrounds')
        backgrounds_dir = os.path.normpath(backgrounds_dir)
        os.makedirs(backgrounds_dir, exist_ok=True)
        
        # 获取下一个编号
        existing_files = os.listdir(backgrounds_dir)
        bg_numbers = []
        for f in existing_files:
            match = re.match(r'background(\d+)\.(jpg|jpeg|png|gif|webp)', f, re.IGNORECASE)
            if match:
                bg_numbers.append(int(match.group(1)))
        
        next_num = max(bg_numbers, default=0) + 1
        ext = file.filename.rsplit('.', 1)[1].lower()
        secure_name = f"background{next_num}.{ext}"
        file_path = os.path.join(backgrounds_dir, secure_name)
        file.save(file_path)
        
        logger.info(f"背景图片上传成功: {secure_name}")
        
        return jsonify({
            'id': f'bg_{secure_name}',
            'name': f'背景{next_num}',
            'type': 'image',
            'value': f'/backgrounds/{secure_name}'
        }), 200
        
    except Exception as e:
        logger.error(f"上传背景错误: {str(e)}")
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500


@bp.route('/backgrounds/<string:bg_id>', methods=['DELETE'])
@admin_required
def delete_background(bg_id):
    """删除背景图片（仅管理员）"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backgrounds_dir = os.path.join(base_dir, '..', 'frontend', 'public', 'backgrounds')
        backgrounds_dir = os.path.normpath(backgrounds_dir)
        
        if not os.path.exists(backgrounds_dir):
            return jsonify({'error': '背景目录不存在'}), 404
        
        # 从 bg_id 提取文件名
        if bg_id.startswith('bg_'):
            filename = bg_id[3:]
        else:
            filename = bg_id
        
        file_path = os.path.join(backgrounds_dir, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"背景图片删除成功: {filename}")
            return jsonify({'message': '删除成功'}), 200
        else:
            return jsonify({'error': '背景不存在'}), 404
        
    except Exception as e:
        logger.error(f"删除背景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
