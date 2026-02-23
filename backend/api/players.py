"""
球员管理API路由

提供球员的CRUD操作接口：
- GET /api/players/ - 获取所有球员
- POST /api/players/ - 创建球员
- GET /api/players/<id> - 获取单个球员
- PUT /api/players/<id> - 更新球员
- DELETE /api/players/<id> - 删除球员
"""
import logging
import os
import uuid
from flask import Blueprint, request, jsonify, g
from sqlalchemy.orm import joinedload
from models import Player, Team
from extensions import db
from utils.pagination import Pagination, PaginatedResult
from utils.jwt_auth import login_required, admin_required, optional_login
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

bp = Blueprint('players', __name__)

# 常量定义
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads/players'
MAX_AGE = 100
MIN_AGE = 0
MAX_HEIGHT = 250
MIN_HEIGHT = 100


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_path():
    """获取上传文件路径"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), UPLOAD_FOLDER)


def validate_player_data(data, is_update=False):
    """
    验证球员数据
    
    Args:
        data: 请求数据
        is_update: 是否为更新操作
    
    Returns:
        (is_valid, error_message, cleaned_data)
    """
    cleaned = {}
    
    # 验证名称
    name = data.get('name')
    if not is_update:
        if not name or not isinstance(name, str) or len(name.strip()) == 0:
            return False, 'name is required and must be a non-empty string', None
    if name is not None:
        if not isinstance(name, str) or len(name.strip()) == 0:
            return False, 'name must be a non-empty string', None
        cleaned['name'] = name.strip()
    
    # 验证年龄
    age = data.get('age')
    if age is not None:
        if not isinstance(age, int) or age < MIN_AGE or age > MAX_AGE:
            return False, f'age must be an integer between {MIN_AGE} and {MAX_AGE}', None
        cleaned['age'] = age
    
    # 验证身高
    height_cm = data.get('height_cm')
    if height_cm is not None:
        if not isinstance(height_cm, int) or height_cm < MIN_HEIGHT or height_cm > MAX_HEIGHT:
            return False, f'height_cm must be an integer between {MIN_HEIGHT} and {MAX_HEIGHT}', None
        cleaned['height_cm'] = height_cm
    
    # 验证球队ID
    team_id = data.get('team_id')
    if team_id is not None:
        team = Team.query.get(team_id)
        if not team:
            return False, 'invalid team_id', None
        cleaned['team_id'] = team_id
    
    # 其他字段
    if 'nationality' in data:
        cleaned['nationality'] = data.get('nationality')
    if 'position' in data:
        cleaned['position'] = data.get('position')
    if 'avatar' in data:
        cleaned['avatar'] = data.get('avatar')
    
    return True, None, cleaned


@bp.route('/', methods=['GET'])
@optional_login
def list_players():
    """获取球员列表（支持筛选和分页）"""
    try:
        # 使用 joinedload 预加载关联关系
        query = Player.query.options(joinedload(Player.team))

        # 高级筛选参数（使用参数化查询防止SQL注入）
        team_id = request.args.get('team_id', type=int)
        position = request.args.get('position')
        nationality = request.args.get('nationality')
        min_age = request.args.get('min_age', type=int)
        max_age = request.args.get('max_age', type=int)
        name_search = request.args.get('name')

        if team_id:
            query = query.filter(Player.team_id == team_id)
        if position:
            query = query.filter(Player.position == position)
        if nationality:
            query = query.filter(Player.nationality == nationality)
        if min_age is not None:
            query = query.filter(Player.age >= min_age)
        if max_age is not None:
            query = query.filter(Player.age <= max_age)
        if name_search:
            # 使用参数化查询防止SQL注入
            search_pattern = f'%{name_search}%'
            query = query.filter(Player.name.ilike(search_pattern))

        # 分页处理
        pagination = Pagination.from_request(default_per_page=20, max_per_page=100)
        paginated_result = pagination.paginate_query(query.order_by(Player.id))
        
        # 转换为字典格式
        items = [p.to_dict() for p in paginated_result.items]
        result = PaginatedResult(items, paginated_result.total, paginated_result.page, paginated_result.per_page)
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"获取球员列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/<int:player_id>', methods=['GET'])
@optional_login
def get_player(player_id):
    """获取单个球员详情"""
    try:
        # 使用 db.session.get() 替代已弃用的 query.get()
        player = db.session.get(Player, player_id)
        if not player:
            return jsonify({'error': '球员不存在'}), 404
        
        return jsonify(player.to_dict())
        
    except Exception as e:
        logger.error(f"获取球员详情错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/', methods=['POST'])
@login_required
def create_player():
    """创建球员"""
    try:
        data = request.json or {}
        
        # 验证数据
        is_valid, error, cleaned_data = validate_player_data(data)
        if not is_valid:
            return jsonify({'error': error}), 400

        player = Player(
            name=cleaned_data.get('name'),
            age=cleaned_data.get('age'),
            nationality=cleaned_data.get('nationality'),
            position=cleaned_data.get('position'),
            height_cm=cleaned_data.get('height_cm'),
            avatar=cleaned_data.get('avatar'),
            team_id=cleaned_data.get('team_id')
        )
        db.session.add(player)
        db.session.commit()
        
        logger.info(f"球员创建成功: {player.name} (ID: {player.id})")
        
        return jsonify(player.to_dict()), 201
        
    except Exception as e:
        logger.error(f"创建球员错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/<int:player_id>', methods=['PUT'])
@login_required
def update_player(player_id):
    """更新球员信息"""
    try:
        player = db.session.get(Player, player_id)
        if not player:
            return jsonify({'error': '球员不存在'}), 404
        
        data = request.json or {}
        
        # 验证数据
        is_valid, error, cleaned_data = validate_player_data(data, is_update=True)
        if not is_valid:
            return jsonify({'error': error}), 400

        # 更新字段
        if 'name' in cleaned_data:
            player.name = cleaned_data['name']
        if 'age' in cleaned_data:
            player.age = cleaned_data['age']
        if 'nationality' in cleaned_data:
            player.nationality = cleaned_data['nationality']
        if 'position' in cleaned_data:
            player.position = cleaned_data['position']
        if 'height_cm' in cleaned_data:
            player.height_cm = cleaned_data['height_cm']
        if 'avatar' in cleaned_data:
            player.avatar = cleaned_data['avatar']
        if 'team_id' in cleaned_data:
            player.team_id = cleaned_data['team_id']
        
        db.session.commit()
        
        logger.info(f"球员更新成功: {player.name} (ID: {player.id})")
        
        return jsonify(player.to_dict())
        
    except Exception as e:
        logger.error(f"更新球员错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/<int:player_id>', methods=['DELETE'])
@login_required
def delete_player(player_id):
    """删除球员"""
    try:
        player = db.session.get(Player, player_id)
        if not player:
            return jsonify({'error': '球员不存在'}), 404
        
        # 删除头像文件
        if player.avatar:
            avatar_path = os.path.join(get_upload_path(), os.path.basename(player.avatar))
            if os.path.exists(avatar_path):
                try:
                    os.remove(avatar_path)
                except OSError as e:
                    logger.warning(f"删除头像文件失败: {e}")
        
        player_name = player.name
        db.session.delete(player)
        db.session.commit()
        
        logger.info(f"球员删除成功: {player_name} (ID: {player_id})")
        
        return jsonify({'status': 'deleted', 'message': f'球员 {player_name} 已删除'})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"删除球员错误: {str(e)}\n{error_detail}")
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500


@bp.route('/batch-delete', methods=['POST'])
@admin_required
def batch_delete_players():
    """批量删除球员（仅管理员）"""
    try:
        data = request.json or {}
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return jsonify({'error': '请提供要删除的球员ID列表'}), 400
        
        deleted_count = 0
        for player_id in ids:
            player = db.session.get(Player, player_id)
            if player:
                # 删除头像文件
                if player.avatar:
                    avatar_path = os.path.join(get_upload_path(), os.path.basename(player.avatar))
                    if os.path.exists(avatar_path):
                        try:
                            os.remove(avatar_path)
                        except OSError:
                            pass
                db.session.delete(player)
                deleted_count += 1
        
        db.session.commit()
        
        logger.info(f"批量删除球员成功: 共删除 {deleted_count} 人")
        
        return jsonify({
            'status': 'deleted',
            'message': f'成功删除 {deleted_count} 名球员',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"批量删除球员错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500


@bp.route('/reset-ids', methods=['POST'])
@admin_required
def reset_player_ids():
    """重置球员ID（仅管理员，仅开发环境）"""
    # 仅允许在开发环境执行此危险操作
    if os.getenv('FLASK_ENV', 'development') != 'development':
        return jsonify({'error': 'Not allowed in non-development environments'}), 403

    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE players SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE players AUTO_INCREMENT = 1"))
        
        related_tables = ['contracts', 'transfers', 'match_lineups', 'match_events', 'player_stats']
        for table in related_tables:
            try:
                db.session.execute(db.text("SET @new_id = 0"))
                db.session.execute(db.text(f"UPDATE {table} SET player_id = @new_id := @new_id + 1 ORDER BY player_id"))
            except Exception as table_error:
                logger.warning(f"重置表 {table} 失败: {table_error}")
        
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        
        logger.info("球员ID重置成功")
        
        return jsonify({'message': 'ID重置成功'})
        
    except Exception as e:
        logger.error(f"重置ID错误: {str(e)}")
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/upload-avatar', methods=['POST'])
@login_required
def upload_player_avatar():
    """上传球员头像"""
    try:
        if 'avatar' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['avatar']
        player_id = request.form.get('id')
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type or extension'}), 400

        # 验证图片
        try:
            from PIL import Image
            file.stream.seek(0)
            img = Image.open(file.stream)
            img.verify()
            img_format = (img.format or '').lower()
        except Exception:
            return jsonify({'error': 'Uploaded file is not a valid image'}), 400

        detected_ext = 'jpg' if img_format == 'jpeg' else img_format
        if detected_ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': 'Invalid image format'}), 400

        # 保存前重置流位置
        file.stream.seek(0)

        filename = secure_filename(f"player_{player_id or 'new'}_{uuid.uuid4().hex[:8]}.{detected_ext}")
        upload_path = get_upload_path()
        os.makedirs(upload_path, exist_ok=True)
        save_path = os.path.join(upload_path, filename)
        file.save(save_path)
        avatar_url = f"/{UPLOAD_FOLDER}/{filename}"

        if player_id:
            try:
                pid = int(player_id)
                player = Player.query.get(pid)
                if player:
                    # 删除旧头像
                    if player.avatar:
                        old_path = os.path.join(upload_path, os.path.basename(player.avatar))
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass
                    player.avatar = avatar_url
                    db.session.commit()
                    
                    logger.info(f"球员头像上传成功: {player.name} (ID: {pid})")
            except (ValueError, TypeError):
                pass

        return jsonify({'avatar': avatar_url, 'player_id': player_id})
        
    except Exception as e:
        logger.error(f"上传头像错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '服务器内部错误'}), 500
