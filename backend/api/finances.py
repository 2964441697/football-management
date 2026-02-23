"""
财务管理API路由

提供财务记录的CRUD操作接口：
- GET /api/finances/ - 获取所有财务记录
- POST /api/finances/ - 创建财务记录
- GET /api/finances/<id> - 获取单个财务记录
- PUT /api/finances/<id> - 更新财务记录
- DELETE /api/finances/<id> - 删除财务记录
"""
import logging
import os
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import Finance, Team
from extensions import db
from utils.jwt_auth import login_required, admin_required, optional_login
from utils.base_crud import handle_api_errors, APIError
from utils.pagination import Pagination, PaginatedResult

logger = logging.getLogger(__name__)

bp = Blueprint('finances', __name__)


@bp.route('/', methods=['GET'])
@handle_api_errors
@optional_login
def list_finances():
    """获取财务记录列表"""
    # 使用 joinedload 预加载关联关系
    query = Finance.query.options(joinedload(Finance.team))
    
    # 筛选参数
    team_id = request.args.get('team_id', type=int)
    category = request.args.get('category')
    
    if team_id:
        query = query.filter(Finance.team_id == team_id)
    if category:
        query = query.filter(Finance.category == category)
    
    # 分页
    pagination = Pagination.from_request(default_per_page=20, max_per_page=100)
    paginated = pagination.paginate_query(query.order_by(Finance.id.desc()))
    
    items = [f.to_dict() for f in paginated.items]
    result = PaginatedResult(items, paginated.total, paginated.page, paginated.per_page)
    
    return jsonify(result.to_dict())


@bp.route('/<int:finance_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_finance(finance_id):
    """获取单个财务记录"""
    f = Finance.query.get(finance_id)
    if not f:
        raise APIError('财务记录不存在', 404)
    return jsonify(f.to_dict())


@bp.route('/', methods=['POST'])
@handle_api_errors
@login_required
def create_finance():
    """创建财务记录"""
    data = request.json or {}
    
    # 验证必填字段
    team_id = data.get('team_id')
    category = data.get('category')
    amount = data.get('amount')
    
    if not team_id:
        raise APIError('team_id 是必填字段', 400)
    if not category:
        raise APIError('category 是必填字段', 400)
    if amount is None:
        raise APIError('amount 是必填字段', 400)
    
    # 验证球队是否存在
    team = Team.query.get(team_id)
    if not team:
        raise APIError('球队不存在', 404)
    
    # 验证金额
    if not isinstance(amount, (int, float)):
        raise APIError('amount 必须是数字', 400)
    
    finance = Finance(
        team_id=team_id,
        category=category,
        amount=amount,
        note=data.get('note'),
        record_date=data.get('record_date')
    )
    db.session.add(finance)
    db.session.commit()
    
    logger.info(f"财务记录创建成功: {team.name} - {category} - {amount}")
    
    return jsonify(finance.to_dict()), 201


@bp.route('/<int:finance_id>', methods=['PUT'])
@handle_api_errors
@login_required
def update_finance(finance_id):
    """更新财务记录"""
    f = Finance.query.get(finance_id)
    if not f:
        raise APIError('财务记录不存在', 404)
    
    data = request.json or {}
    
    # 验证金额
    amount = data.get('amount')
    if amount is not None and not isinstance(amount, (int, float)):
        raise APIError('amount 必须是数字', 400)
    
    # 验证球队
    team_id = data.get('team_id')
    if team_id is not None:
        team = Team.query.get(team_id)
        if not team:
            raise APIError('球队不存在', 404)
        f.team_id = team_id
    
    if 'category' in data:
        f.category = data['category']
    if 'amount' in data:
        f.amount = data['amount']
    if 'note' in data:
        f.note = data['note']
    if 'record_date' in data:
        f.record_date = data['record_date']
    
    db.session.commit()
    
    logger.info(f"财务记录更新成功: ID={finance_id}")
    
    return jsonify(f.to_dict())


@bp.route('/<int:finance_id>', methods=['DELETE'])
@handle_api_errors
@login_required
def delete_finance(finance_id):
    """删除财务记录"""
    f = Finance.query.get(finance_id)
    if not f:
        raise APIError('财务记录不存在', 404)
    
    db.session.delete(f)
    db.session.commit()
    
    logger.info(f"财务记录删除成功: ID={finance_id}")
    
    return jsonify({'status': 'deleted', 'id': finance_id})


@bp.route('/batch-delete', methods=['POST'])
@handle_api_errors
@admin_required
def batch_delete_finances():
    """批量删除财务记录（仅管理员）"""
    data = request.json or {}
    ids = data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        raise APIError('请提供要删除的ID列表', 400)
    
    deleted_count = 0
    for finance_id in ids:
        f = Finance.query.get(finance_id)
        if f:
            db.session.delete(f)
            deleted_count += 1
    
    db.session.commit()
    
    logger.info(f"批量删除财务记录成功: 共删除 {deleted_count} 条")
    
    return jsonify({
        'status': 'deleted',
        'deleted_count': deleted_count
    })


@bp.route('/reset-ids', methods=['POST'])
@handle_api_errors
@admin_required
def reset_finance_ids():
    """重置财务记录ID（仅管理员，仅开发环境）"""
    if os.getenv('FLASK_ENV', 'development') != 'development':
        raise APIError('仅允许在开发环境执行此操作', 403)
    
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
    db.session.execute(db.text("SET @new_id = 0"))
    db.session.execute(db.text("UPDATE finances SET id = @new_id := @new_id + 1 ORDER BY id"))
    db.session.execute(db.text("ALTER TABLE finances AUTO_INCREMENT = 1"))
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
    db.session.commit()
    
    logger.info("财务记录ID重置成功")
    
    return jsonify({'message': 'ID重置成功'})


@bp.route('/team/<int:team_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_finances_by_team(team_id):
    """获取指定球队的财务记录"""
    team = Team.query.get(team_id)
    if not team:
        raise APIError('球队不存在', 404)
    
    finances = Finance.query.filter_by(team_id=team_id).order_by(Finance.record_date.desc()).all()
    return jsonify([f.to_dict() for f in finances])


@bp.route('/summary/team/<int:team_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_finance_summary_by_team(team_id):
    """获取指定球队的财务汇总"""
    team = Team.query.get(team_id)
    if not team:
        raise APIError('球队不存在', 404)
    
    finances = Finance.query.filter_by(team_id=team_id).all()
    
    total_income = sum(float(f.amount) for f in finances if f.amount and f.amount > 0)
    total_expense = sum(float(f.amount) for f in finances if f.amount and f.amount < 0)
    
    return jsonify({
        'team_id': team_id,
        'team_name': team.name,
        'total_income': total_income,
        'total_expense': abs(total_expense),
        'balance': total_income + total_expense,
        'record_count': len(finances)
    })
