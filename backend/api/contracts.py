"""
合同管理API路由

提供合同的CRUD操作接口：
- GET /api/contracts/ - 获取所有合同
- POST /api/contracts/ - 创建合同
- GET /api/contracts/<id> - 获取单个合同
- PUT /api/contracts/<id> - 更新合同
- DELETE /api/contracts/<id> - 删除合同
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import Contract
from extensions import db

bp = Blueprint('contracts', __name__)


@bp.route('/', methods=['GET'])
def list_contracts():
    contracts = Contract.query.options(
        joinedload(Contract.player),
        joinedload(Contract.team)
    ).order_by(Contract.id).limit(200).all()
    return jsonify([c.to_dict() for c in contracts])


@bp.route('/<int:contract_id>', methods=['GET'])
def get_contract(contract_id):
    c = Contract.query.get_or_404(contract_id)
    return jsonify(c.to_dict())


@bp.route('/', methods=['POST'])
def create_contract():
    data = request.json or {}
    if not data.get('player_id') or not data.get('team_id'):
        return jsonify({'error': 'player_id and team_id required'}), 400
    contract = Contract(
        player_id=data.get('player_id'),
        team_id=data.get('team_id'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        salary=data.get('salary') or 0.0,
        release_clause=data.get('release_clause')
    )
    db.session.add(contract)
    db.session.commit()
    return jsonify(contract.to_dict()), 201


@bp.route('/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    c = Contract.query.get_or_404(contract_id)
    data = request.json or {}
    c.player_id = data.get('player_id', c.player_id)
    c.team_id = data.get('team_id', c.team_id)
    c.start_date = data.get('start_date', c.start_date)
    c.end_date = data.get('end_date', c.end_date)
    c.salary = data.get('salary', c.salary)
    c.release_clause = data.get('release_clause', c.release_clause)
    db.session.commit()
    return jsonify(c.to_dict())


@bp.route('/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    c = Contract.query.get_or_404(contract_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_contract_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE contracts SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE contracts AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/player/<int:player_id>', methods=['GET'])
def get_contracts_by_player(player_id):
    contracts = Contract.query.filter_by(player_id=player_id).order_by(Contract.end_date).all()
    return jsonify([c.to_dict() for c in contracts])


@bp.route('/team/<int:team_id>', methods=['GET'])
def get_contracts_by_team(team_id):
    contracts = Contract.query.filter_by(team_id=team_id).order_by(Contract.end_date).all()
    return jsonify([c.to_dict() for c in contracts])


@bp.route('/expiring', methods=['GET'])
def get_expiring_contracts():
    from datetime import date
    from datetime import timedelta
    thirty_days_later = date.today() + timedelta(days=30)
    contracts = Contract.query.filter(Contract.end_date <= thirty_days_later).order_by(Contract.end_date).all()
    return jsonify([c.to_dict() for c in contracts])
