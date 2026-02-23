"""
比赛管理API路由

提供比赛的CRUD操作接口：
- GET /api/matches/ - 获取所有比赛
- POST /api/matches/ - 创建比赛
- GET /api/matches/<id> - 获取单个比赛
- PUT /api/matches/<id> - 更新比赛
- DELETE /api/matches/<id> - 删除比赛
"""
import logging
import os
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import Match, Team, Season
from extensions import db
from utils.jwt_auth import login_required, admin_required, optional_login
from utils.base_crud import handle_api_errors, APIError
from utils.pagination import Pagination, PaginatedResult

logger = logging.getLogger(__name__)

bp = Blueprint('matches', __name__)


@bp.route('/', methods=['GET'])
@handle_api_errors
@optional_login
def list_matches():
    """获取比赛列表"""
    # 使用 joinedload 预加载关联关系，解决 N+1 查询问题
    query = Match.query.options(
        joinedload(Match.season),
        joinedload(Match.home_team),
        joinedload(Match.away_team)
    )
    
    # 筛选参数
    season_id = request.args.get('season_id', type=int)
    home_team_id = request.args.get('home_team_id', type=int)
    away_team_id = request.args.get('away_team_id', type=int)
    team_id = request.args.get('team_id', type=int)  # 主队或客队包含此球队
    
    if season_id:
        query = query.filter(Match.season_id == season_id)
    if home_team_id:
        query = query.filter(Match.home_team_id == home_team_id)
    if away_team_id:
        query = query.filter(Match.away_team_id == away_team_id)
    if team_id:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    # 分页
    pagination = Pagination.from_request(default_per_page=20, max_per_page=100)
    paginated = pagination.paginate_query(query.order_by(Match.start_time.desc()))
    
    items = [m.to_dict() for m in paginated.items]
    result = PaginatedResult(items, paginated.total, paginated.page, paginated.per_page)
    
    return jsonify(result.to_dict())


@bp.route('/<int:match_id>', methods=['GET'])
@handle_api_errors
@optional_login
def get_match(match_id):
    """获取单个比赛"""
    m = db.session.get(Match, match_id)
    if not m:
        raise APIError('比赛不存在', 404)
    return jsonify(m.to_dict())


@bp.route('/', methods=['POST'])
@handle_api_errors
@login_required
def create_match():
    """创建比赛"""
    data = request.json or {}
    
    # 验证必填字段
    home_team_id = data.get('home_team_id')
    away_team_id = data.get('away_team_id')
    
    if not home_team_id:
        raise APIError('home_team_id 是必填字段', 400)
    if not away_team_id:
        raise APIError('away_team_id 是必填字段', 400)
    
    # 验证主客队不能相同
    if home_team_id == away_team_id:
        raise APIError('主队和客队不能是同一支球队', 400)
    
    # 验证球队是否存在
    home_team = db.session.get(Team, home_team_id)
    if not home_team:
        raise APIError('主队不存在', 404)
    
    away_team = db.session.get(Team, away_team_id)
    if not away_team:
        raise APIError('客队不存在', 404)
    
    # 验证赛季
    season_id = data.get('season_id')
    if season_id:
        season = db.session.get(Season, season_id)
        if not season:
            raise APIError('赛季不存在', 404)
    
    m = Match(
        season_id=season_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        start_time=data.get('start_time'),
        venue=data.get('venue')
    )
    db.session.add(m)
    db.session.commit()
    
    logger.info(f"比赛创建成功: {home_team.name} vs {away_team.name}")
    
    return jsonify(m.to_dict()), 201


@bp.route('/<int:match_id>', methods=['PUT'])
@handle_api_errors
@login_required
def update_match(match_id):
    """更新比赛"""
    m = db.session.get(Match, match_id)
    if not m:
        raise APIError('比赛不存在', 404)
    
    data = request.json or {}
    
    # 获取新的主客队ID
    home_team_id = data.get('home_team_id', m.home_team_id)
    away_team_id = data.get('away_team_id', m.away_team_id)
    
    # 验证主客队不能相同
    if home_team_id == away_team_id:
        raise APIError('主队和客队不能是同一支球队', 400)
    
    # 验证球队是否存在
    if 'home_team_id' in data:
        home_team = db.session.get(Team, home_team_id)
        if not home_team:
            raise APIError('主队不存在', 404)
        m.home_team_id = home_team_id
    
    if 'away_team_id' in data:
        away_team = db.session.get(Team, away_team_id)
        if not away_team:
            raise APIError('客队不存在', 404)
        m.away_team_id = away_team_id
    
    # 验证赛季
    if 'season_id' in data:
        season_id = data['season_id']
        if season_id:
            season = db.session.get(Season, season_id)
            if not season:
                raise APIError('赛季不存在', 404)
        m.season_id = season_id
    
    if 'start_time' in data:
        m.start_time = data['start_time']
    if 'venue' in data:
        m.venue = data['venue']
    
    db.session.commit()
    
    logger.info(f"比赛更新成功: ID={match_id}")
    
    return jsonify(m.to_dict())


@bp.route('/<int:match_id>', methods=['DELETE'])
@handle_api_errors
@login_required
def delete_match(match_id):
    """删除比赛"""
    m = db.session.get(Match, match_id)
    if not m:
        raise APIError('比赛不存在', 404)
    
    db.session.delete(m)
    db.session.commit()
    
    logger.info(f"比赛删除成功: ID={match_id}")
    
    return jsonify({'status': 'deleted', 'id': match_id})


@bp.route('/batch-delete', methods=['POST'])
@handle_api_errors
@admin_required
def batch_delete_matches():
    """批量删除比赛（仅管理员）"""
    data = request.json or {}
    ids = data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        raise APIError('请提供要删除的ID列表', 400)
    
    deleted_count = 0
    for match_id in ids:
        m = db.session.get(Match, match_id)
        if m:
            db.session.delete(m)
            deleted_count += 1
    
    db.session.commit()
    
    logger.info(f"批量删除比赛成功: 共删除 {deleted_count} 场")
    
    return jsonify({
        'status': 'deleted',
        'deleted_count': deleted_count
    })


@bp.route('/reset-ids', methods=['POST'])
@handle_api_errors
@admin_required
def reset_match_ids():
    """重置比赛ID（仅管理员，仅开发环境）"""
    if os.getenv('FLASK_ENV', 'development') != 'development':
        raise APIError('仅允许在开发环境执行此操作', 403)
    
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
    db.session.execute(db.text("SET @new_id = 0"))
    db.session.execute(db.text("UPDATE matches SET id = @new_id := @new_id + 1 ORDER BY id"))
    db.session.execute(db.text("ALTER TABLE matches AUTO_INCREMENT = 1"))
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
    db.session.commit()
    
    logger.info("比赛ID重置成功")
    
    return jsonify({'message': 'ID重置成功'})
