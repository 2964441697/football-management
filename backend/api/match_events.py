"""
比赛事件API路由

提供比赛事件（进球、红黄牌等）的CRUD操作接口：
- GET /api/match-events/ - 获取所有比赛事件
- POST /api/match-events/ - 创建比赛事件
- GET /api/match-events/<id> - 获取单个比赛事件
- PUT /api/match-events/<id> - 更新比赛事件
- DELETE /api/match-events/<id> - 删除比赛事件
"""
from flask import Blueprint, request, jsonify
from models import MatchEvent
from extensions import db

bp = Blueprint('match_events', __name__)


@bp.route('/', methods=['GET'])
def list_match_events():
    match_id = request.args.get('match_id')
    if match_id:
        events = MatchEvent.query.filter_by(match_id=match_id).order_by(MatchEvent.minute).all()
    else:
        events = MatchEvent.query.limit(500).all()
    return jsonify([e.to_dict() for e in events])


@bp.route('/<int:event_id>', methods=['GET'])
def get_match_event(event_id):
    e = MatchEvent.query.get_or_404(event_id)
    return jsonify(e.to_dict())


@bp.route('/', methods=['POST'])
def create_match_event():
    data = request.json or {}
    if not data.get('match_id') or not data.get('event_type'):
        return jsonify({'error': 'match_id and event_type required'}), 400
    event = MatchEvent(
        match_id=data.get('match_id'),
        minute=data.get('minute') or 0,
        event_type=data.get('event_type'),
        player_id=data.get('player_id'),
        related_player_id=data.get('related_player_id'),
        description=data.get('description')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@bp.route('/<int:event_id>', methods=['PUT'])
def update_match_event(event_id):
    e = MatchEvent.query.get_or_404(event_id)
    data = request.json or {}
    e.minute = data.get('minute', e.minute)
    e.event_type = data.get('event_type', e.event_type)
    e.player_id = data.get('player_id', e.player_id)
    e.related_player_id = data.get('related_player_id', e.related_player_id)
    e.description = data.get('description', e.description)
    db.session.commit()
    return jsonify(e.to_dict())


@bp.route('/<int:event_id>', methods=['DELETE'])
def delete_match_event(event_id):
    e = MatchEvent.query.get_or_404(event_id)
    db.session.delete(e)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/match/<int:match_id>', methods=['GET'])
def get_events_by_match(match_id):
    events = MatchEvent.query.filter_by(match_id=match_id).order_by(MatchEvent.minute).all()
    return jsonify([e.to_dict() for e in events])


@bp.route('/player/<int:player_id>', methods=['GET'])
def get_events_by_player(player_id):
    events = MatchEvent.query.filter_by(player_id=player_id).order_by(MatchEvent.minute).all()
    return jsonify([e.to_dict() for e in events])


@bp.route('/type/<event_type>', methods=['GET'])
def get_events_by_type(event_type):
    events = MatchEvent.query.filter_by(event_type=event_type).limit(200).all()
    return jsonify([e.to_dict() for e in events])


@bp.route('/match/<int:match_id>/timeline', methods=['GET'])
def get_match_timeline(match_id):
    events = MatchEvent.query.filter_by(match_id=match_id).order_by(MatchEvent.minute).all()
    timeline = []
    for event in events:
        timeline.append({
            'minute': event.minute,
            'type': event.event_type,
            'description': event.description
        })
    return jsonify(timeline)
