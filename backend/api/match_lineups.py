"""
比赛阵容API路由

提供比赛阵容的CRUD操作接口：
- GET /api/match-lineups/ - 获取所有比赛阵容
- POST /api/match-lineups/ - 创建比赛阵容
- GET /api/match-lineups/<id> - 获取单个比赛阵容
- PUT /api/match-lineups/<id> - 更新比赛阵容
- DELETE /api/match-lineups/<id> - 删除比赛阵容
"""
from flask import Blueprint, request, jsonify
from models import MatchLineup
from extensions import db

bp = Blueprint('match_lineups', __name__)


@bp.route('/', methods=['GET'])
def list_match_lineups():
    match_id = request.args.get('match_id')
    if match_id:
        lineups = MatchLineup.query.filter_by(match_id=match_id).all()
    else:
        lineups = MatchLineup.query.limit(500).all()
    return jsonify([l.to_dict() for l in lineups])


@bp.route('/<int:lineup_id>', methods=['GET'])
def get_match_lineup(lineup_id):
    l = MatchLineup.query.get_or_404(lineup_id)
    return jsonify(l.to_dict())


@bp.route('/', methods=['POST'])
def create_match_lineup():
    data = request.json or {}
    if not data.get('match_id') or not data.get('player_id'):
        return jsonify({'error': 'match_id and player_id required'}), 400
    lineup = MatchLineup(
        match_id=data.get('match_id'),
        team_id=data.get('team_id'),
        player_id=data.get('player_id'),
        is_starting=data.get('is_starting') or False,
        shirt_number=data.get('shirt_number')
    )
    db.session.add(lineup)
    db.session.commit()
    return jsonify(lineup.to_dict()), 201


@bp.route('/<int:lineup_id>', methods=['PUT'])
def update_match_lineup(lineup_id):
    l = MatchLineup.query.get_or_404(lineup_id)
    data = request.json or {}
    l.team_id = data.get('team_id', l.team_id)
    l.player_id = data.get('player_id', l.player_id)
    l.is_starting = data.get('is_starting', l.is_starting)
    l.shirt_number = data.get('shirt_number', l.shirt_number)
    db.session.commit()
    return jsonify(l.to_dict())


@bp.route('/<int:lineup_id>', methods=['DELETE'])
def delete_match_lineup(lineup_id):
    l = MatchLineup.query.get_or_404(lineup_id)
    db.session.delete(l)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/match/<int:match_id>', methods=['GET'])
def get_lineups_by_match(match_id):
    lineups = MatchLineup.query.filter_by(match_id=match_id).order_by(MatchLineup.is_starting.desc(), MatchLineup.shirt_number).all()
    return jsonify([l.to_dict() for l in lineups])
