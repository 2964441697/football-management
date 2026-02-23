"""
球员统计API路由

提供球员统计的查询和聚合接口：
- GET /api/player-stats/ - 获取所有球员统计
- GET /api/player-stats/<player_id> - 获取单个球员统计
- POST /api/player-stats/aggregate - 聚合球员统计
"""
from flask import Blueprint, request, jsonify
from models import PlayerStat, MatchEvent, MatchLineup, Match
from extensions import db
from sqlalchemy import func

bp = Blueprint('player_stats', __name__)


@bp.route('/', methods=['GET'])
def list_player_stats():
    stats = PlayerStat.query.order_by(PlayerStat.id).all()
    return jsonify([s.to_dict() for s in stats])


@bp.route('/<int:player_id>', methods=['GET'])
def get_player_stats(player_id):
    stats = PlayerStat.query.filter_by(player_id=player_id).all()
    return jsonify([s.to_dict() for s in stats])


@bp.route('/aggregate', methods=['POST'])
def aggregate_player_stats():
    """
    聚合球员统计数据
    从match_events和match_lineups中计算统计
    """
    data = request.json or {}
    season_id = data.get('season_id')

    # 获取所有球员
    players = db.session.query(MatchEvent.player_id.distinct()).filter(
        MatchEvent.player_id.isnot(None)
    ).all()
    player_ids = [p[0] for p in players]

    aggregated_stats = []

    for player_id in player_ids:
        # 计算比赛场次
        matches_played = db.session.query(func.count(func.distinct(MatchLineup.match_id))).filter(
            MatchLineup.player_id == player_id
        ).scalar() or 0

        # 计算进球
        goals = MatchEvent.query.filter(
            MatchEvent.player_id == player_id,
            MatchEvent.event_type == 'goal'
        ).count()

        # 计算助攻
        assists = MatchEvent.query.filter(
            MatchEvent.player_id == player_id,
            MatchEvent.event_type == 'assist'
        ).count()

        # 计算黄牌
        yellow_cards = MatchEvent.query.filter(
            MatchEvent.player_id == player_id,
            MatchEvent.event_type == 'yellow_card'
        ).count()

        # 计算红牌
        red_cards = MatchEvent.query.filter(
            MatchEvent.player_id == player_id,
            MatchEvent.event_type == 'red_card'
        ).count()

        # 计算出场分钟（简化：假设90分钟每场）
        minutes_played = matches_played * 90

        # 检查是否已有统计记录
        existing_stat = PlayerStat.query.filter_by(
            player_id=player_id,
            season_id=season_id
        ).first()

        if existing_stat:
            existing_stat.matches_played = matches_played
            existing_stat.goals = goals
            existing_stat.assists = assists
            existing_stat.yellow_cards = yellow_cards
            existing_stat.red_cards = red_cards
            existing_stat.minutes_played = minutes_played
        else:
            new_stat = PlayerStat(
                player_id=player_id,
                season_id=season_id,
                matches_played=matches_played,
                goals=goals,
                assists=assists,
                yellow_cards=yellow_cards,
                red_cards=red_cards,
                minutes_played=minutes_played
            )
            db.session.add(new_stat)

        aggregated_stats.append({
            'player_id': player_id,
            'season_id': season_id,
            'matches_played': matches_played,
            'goals': goals,
            'assists': assists,
            'yellow_cards': yellow_cards,
            'red_cards': red_cards,
            'minutes_played': minutes_played
        })

    db.session.commit()
    return jsonify({'message': 'Player stats aggregated successfully', 'stats': aggregated_stats})