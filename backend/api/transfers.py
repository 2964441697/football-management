"""
转会管理API路由

提供转会记录的CRUD操作接口：
- GET /api/transfers/ - 获取所有转会
- POST /api/transfers/ - 创建转会
- GET /api/transfers/<id> - 获取单个转会
- PUT /api/transfers/<id> - 更新转会
- DELETE /api/transfers/<id> - 删除转会
"""
import logging
import os
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import Transfer, Player, Contract, Team
from extensions import db
from datetime import datetime
from utils.jwt_auth import login_required, admin_required, optional_login
from utils.base_crud import handle_api_errors, APIError
from utils.pagination import Pagination, PaginatedResult

logger = logging.getLogger(__name__)

bp = Blueprint('transfers', __name__)


@bp.route('/', methods=['GET'])
@handle_api_errors
@optional_login
def list_transfers():
    """获取转会列表"""
    # 使用 joinedload 预加载关联关系
    query = Transfer.query.options(
        joinedload(Transfer.player),
        joinedload(Transfer.from_team),
        joinedload(Transfer.to_team)
    )
    
    # 筛选参数
    player_id = request.args.get('player_id', type=int)
    from_team_id = request.args.get('from_team_id', type=int)
    to_team_id = request.args.get('to_team_id', type=int)
    
    if player_id:
        query = query.filter(Transfer.player_id == player_id)
    if from_team_id:
        query = query.filter(Transfer.from_team_id == from_team_id)
    if to_team_id:
        query = query.filter(Transfer.to_team_id == to_team_id)
    
    # 分页
    pagination = Pagination.from_request(default_per_page=20, max_per_page=100)
    paginated = pagination.paginate_query(query.order_by(Transfer.id.desc()))
    
    items = [t.to_dict() for t in paginated.items]
    result = PaginatedResult(items, paginated.total, paginated.page, paginated.per_page)
    
    return jsonify(result.to_dict())


@bp.route('/<int:transfer_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_transfer(transfer_id):
    """获取单个转会记录"""
    t = Transfer.query.get(transfer_id)
    if not t:
        raise APIError('转会记录不存在', 404)
    return jsonify(t.to_dict())


@bp.route('/', methods=['POST'])
@handle_api_errors
@login_required
def create_transfer():
    """创建转会记录"""
    data = request.json or {}
    
    # 验证必填字段
    player_id = data.get('player_id')
    from_team_id = data.get('from_team_id')
    to_team_id = data.get('to_team_id')
    fee = data.get('fee')
    transfer_date = data.get('transfer_date')
    
    if not player_id:
        raise APIError('player_id 是必填字段', 400)
    if not to_team_id:
        raise APIError('to_team_id 是必填字段', 400)
    
    # 验证球员是否存在
    player = Player.query.get(player_id)
    if not player:
        raise APIError('球员不存在', 404)
    
    # 验证球队是否存在
    if from_team_id:
        from_team = Team.query.get(from_team_id)
        if not from_team:
            raise APIError('转出球队不存在', 404)
    
    to_team = Team.query.get(to_team_id)
    if not to_team:
        raise APIError('转入球队不存在', 404)
    
    # 验证转会费
    if fee is not None and (not isinstance(fee, (int, float)) or fee < 0):
        raise APIError('转会费必须是非负数', 400)
    
    # 验证转会费是否满足释放条款（如果有）
    if from_team_id:
        active_contract = Contract.query.filter_by(
            player_id=player_id, 
            team_id=from_team_id
        ).first()
        
        if active_contract and active_contract.release_clause:
            if fee and fee < float(active_contract.release_clause):
                raise APIError(f'转会费未达到释放条款 ({active_contract.release_clause})', 400)

    # 创建转会记录
    t = Transfer(
        player_id=player_id, 
        from_team_id=from_team_id, 
        to_team_id=to_team_id, 
        fee=fee, 
        transfer_date=transfer_date
    )
    db.session.add(t)

    # 更新球员的team_id
    player.team_id = to_team_id

    # 结束旧合同（如果存在）
    if from_team_id:
        active_contract = Contract.query.filter_by(
            player_id=player_id, 
            team_id=from_team_id
        ).first()
        if active_contract:
            active_contract.end_date = transfer_date or datetime.utcnow().date()

    # 创建新合同（如果提供合同信息）
    new_contract_data = data.get('new_contract')
    if new_contract_data:
        new_contract = Contract(
            player_id=player_id,
            team_id=to_team_id,
            start_date=transfer_date or datetime.utcnow().date(),
            end_date=new_contract_data.get('end_date'),
            salary=new_contract_data.get('salary'),
            release_clause=new_contract_data.get('release_clause')
        )
        db.session.add(new_contract)

    db.session.commit()
    
    logger.info(f"转会记录创建成功: {player.name} -> {to_team.name}")
    
    return jsonify(t.to_dict()), 201


@bp.route('/<int:transfer_id>', methods=['PUT'])
@handle_api_errors
@login_required
def update_transfer(transfer_id):
    """更新转会记录"""
    t = Transfer.query.get(transfer_id)
    if not t:
        raise APIError('转会记录不存在', 404)
    
    data = request.json or {}
    
    # 验证转会费
    fee = data.get('fee')
    if fee is not None and (not isinstance(fee, (int, float)) or fee < 0):
        raise APIError('转会费必须是非负数', 400)
    
    # 更新字段
    if 'player_id' in data:
        t.player_id = data['player_id']
    if 'from_team_id' in data:
        t.from_team_id = data['from_team_id']
    if 'to_team_id' in data:
        t.to_team_id = data['to_team_id']
    if 'fee' in data:
        t.fee = data['fee']
    if 'transfer_date' in data:
        t.transfer_date = data['transfer_date']
    
    db.session.commit()
    
    logger.info(f"转会记录更新成功: ID={transfer_id}")
    
    return jsonify(t.to_dict())


@bp.route('/<int:transfer_id>', methods=['DELETE'])
@handle_api_errors
@login_required
def delete_transfer(transfer_id):
    """删除转会记录"""
    t = Transfer.query.get(transfer_id)
    if not t:
        raise APIError('转会记录不存在', 404)
    
    db.session.delete(t)
    db.session.commit()
    
    logger.info(f"转会记录删除成功: ID={transfer_id}")
    
    return jsonify({'status': 'deleted', 'id': transfer_id})


@bp.route('/batch-delete', methods=['POST'])
@handle_api_errors
@admin_required
def batch_delete_transfers():
    """批量删除转会记录（仅管理员）"""
    data = request.json or {}
    ids = data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        raise APIError('请提供要删除的ID列表', 400)
    
    deleted_count = 0
    for transfer_id in ids:
        t = Transfer.query.get(transfer_id)
        if t:
            db.session.delete(t)
            deleted_count += 1
    
    db.session.commit()
    
    logger.info(f"批量删除转会记录成功: 共删除 {deleted_count} 条")
    
    return jsonify({
        'status': 'deleted',
        'deleted_count': deleted_count
    })


@bp.route('/reset-ids', methods=['POST'])
@handle_api_errors
@admin_required
def reset_transfer_ids():
    """重置转会记录ID（仅管理员，仅开发环境）"""
    if os.getenv('FLASK_ENV', 'development') != 'development':
        raise APIError('仅允许在开发环境执行此操作', 403)
    
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
    db.session.execute(db.text("SET @new_id = 0"))
    db.session.execute(db.text("UPDATE transfers SET id = @new_id := @new_id + 1 ORDER BY id"))
    db.session.execute(db.text("ALTER TABLE transfers AUTO_INCREMENT = 1"))
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
    db.session.commit()
    
    logger.info("转会记录ID重置成功")
    
    return jsonify({'message': 'ID重置成功'})
