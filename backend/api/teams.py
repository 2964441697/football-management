"""
球队管理API路由

提供球队的CRUD操作接口：
- GET /api/teams/ - 获取所有球队（带分页和搜索）
- POST /api/teams/ - 创建球队
- GET /api/teams/<id> - 获取单个球队
- PUT /api/teams/<id> - 更新球队
- DELETE /api/teams/<id> - 删除球队
"""
import logging
import os
from flask import Blueprint, request, jsonify
from models import Team
from extensions import db
from utils.base_crud import BaseCRUD, handle_api_errors, validate_range
from utils.jwt_auth import login_required, admin_required, optional_login
from sqlalchemy import text

logger = logging.getLogger(__name__)

bp = Blueprint('teams', __name__)

# 初始化 CRUD
team_crud = BaseCRUD(Team, resource_name='球队')

# 验证规则
VALIDATION_RULES = {
    'founded_year': (
        validate_range(1800, 2030),
        'founded_year 必须是 1800-2030 之间的整数'
    ),
    'budget': (
        validate_range(0, None),
        'budget 必须是非负数'
    )
}


@bp.route('/', methods=['GET'])
@handle_api_errors
@optional_login
def list_teams():
    """获取球队列表（带分页和搜索）"""
    return team_crud.get_list(
        search_fields=['name', 'home_stadium'],
        default_order='id'
    )


@bp.route('/<int:team_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_team(team_id):
    """获取单个球队"""
    return team_crud.get_by_id(team_id)


@bp.route('/', methods=['POST'])
@handle_api_errors
@login_required
def create_team():
    """创建球队"""
    return team_crud.create(
        required_fields=['name'],
        optional_fields=['logo', 'home_stadium', 'founded_year', 'budget'],
        validation_rules=VALIDATION_RULES
    )


@bp.route('/<int:team_id>', methods=['PUT'])
@handle_api_errors
@login_required
def update_team(team_id):
    """更新球队"""
    return team_crud.update(
        team_id,
        updatable_fields=['name', 'logo', 'home_stadium', 'founded_year', 'budget'],
        validation_rules=VALIDATION_RULES
    )


@bp.route('/<int:team_id>', methods=['DELETE'])
@handle_api_errors
@login_required
def delete_team(team_id):
    """删除球队"""
    return team_crud.delete(team_id)


@bp.route('/batch-delete', methods=['POST'])
@handle_api_errors
@admin_required
def batch_delete_teams():
    """批量删除球队（仅管理员）"""
    data = request.json or {}
    ids = data.get('ids', [])
    return team_crud.batch_delete(ids)


@bp.route('/reset-ids', methods=['POST'])
@handle_api_errors
@admin_required
def reset_team_ids():
    """重置球队ID（仅管理员，仅开发环境）"""
    if os.getenv('FLASK_ENV', 'development') != 'development':
        return jsonify({'error': '仅允许在开发环境执行此操作'}), 403
    
    try:
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(text("SET @new_id = 0"))
        db.session.execute(text("UPDATE teams SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(text("ALTER TABLE teams AUTO_INCREMENT = 1"))
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        
        logger.info("球队ID重置成功")
        
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        logger.error(f"重置ID错误: {str(e)}")
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
