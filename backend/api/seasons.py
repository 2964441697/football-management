"""
赛季管理API路由

提供赛季的CRUD操作接口：
- GET /api/seasons/ - 获取所有赛季
- POST /api/seasons/ - 创建赛季
- GET /api/seasons/<id> - 获取单个赛季
- PUT /api/seasons/<id> - 更新赛季
- DELETE /api/seasons/<id> - 删除赛季
"""
from flask import Blueprint, request, jsonify
from models import Season
from extensions import db

bp = Blueprint('seasons', __name__)


@bp.route('/', methods=['GET'])
def list_seasons():
    seasons = Season.query.order_by(Season.id).all()
    return jsonify([s.to_dict() for s in seasons])


@bp.route('/<int:season_id>', methods=['GET'])
def get_season(season_id):
    s = Season.query.get_or_404(season_id)
    return jsonify(s.to_dict())


@bp.route('/', methods=['POST'])
def create_season():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    s = Season(name=name, start_date=data.get('start_date'), end_date=data.get('end_date'))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@bp.route('/<int:season_id>', methods=['PUT'])
def update_season(season_id):
    s = Season.query.get_or_404(season_id)
    data = request.json or {}
    s.name = data.get('name', s.name)
    s.start_date = data.get('start_date', s.start_date)
    s.end_date = data.get('end_date', s.end_date)
    db.session.commit()
    return jsonify(s.to_dict())


@bp.route('/<int:season_id>', methods=['DELETE'])
def delete_season(season_id):
    s = Season.query.get_or_404(season_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_season_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE seasons SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE seasons AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
