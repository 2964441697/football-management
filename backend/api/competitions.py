"""
赛事管理API路由

提供赛事的CRUD操作接口：
- GET /api/competitions/ - 获取所有赛事
- POST /api/competitions/ - 创建赛事
- GET /api/competitions/<id> - 获取单个赛事
- PUT /api/competitions/<id> - 更新赛事
- DELETE /api/competitions/<id> - 删除赛事
"""
from flask import Blueprint, request, jsonify
from models import Competition
from extensions import db

bp = Blueprint('competitions', __name__)


@bp.route('/', methods=['GET'])
def list_competitions():
    competitions = Competition.query.order_by(Competition.id).limit(200).all()
    return jsonify([c.to_dict() for c in competitions])


@bp.route('/<int:competition_id>', methods=['GET'])
def get_competition(competition_id):
    c = Competition.query.get_or_404(competition_id)
    return jsonify(c.to_dict())


@bp.route('/', methods=['POST'])
def create_competition():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    competition = Competition(
        name=name,
        type=data.get('type') or '联赛',
        season_id=data.get('season_id')
    )
    db.session.add(competition)
    db.session.commit()
    return jsonify(competition.to_dict()), 201


@bp.route('/<int:competition_id>', methods=['PUT'])
def update_competition(competition_id):
    c = Competition.query.get_or_404(competition_id)
    data = request.json or {}
    c.name = data.get('name', c.name)
    c.type = data.get('type', c.type)
    c.season_id = data.get('season_id', c.season_id)
    db.session.commit()
    return jsonify(c.to_dict())


@bp.route('/<int:competition_id>', methods=['DELETE'])
def delete_competition(competition_id):
    c = Competition.query.get_or_404(competition_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_competition_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE competitions SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE competitions AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/season/<int:season_id>', methods=['GET'])
def get_competitions_by_season(season_id):
    competitions = Competition.query.filter_by(season_id=season_id).order_by(Competition.name).all()
    return jsonify([c.to_dict() for c in competitions])
