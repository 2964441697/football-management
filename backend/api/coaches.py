"""
教练管理API路由

提供教练的CRUD操作接口：
- GET /api/coaches/ - 获取所有教练
- POST /api/coaches/ - 创建教练
- GET /api/coaches/<id> - 获取单个教练
- PUT /api/coaches/<id> - 更新教练
- DELETE /api/coaches/<id> - 删除教练
"""
from flask import Blueprint, request, jsonify
from models import Coach
from extensions import db
import os
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint('coaches', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads/coaches'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), UPLOAD_FOLDER)


@bp.route('/', methods=['GET'])
def list_coaches():
    # 支持分页参数
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size', type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    team_id = request.args.get('team_id', type=int)
    
    query = Coach.query
    
    # 搜索过滤
    if search:
        query = query.filter(Coach.name.ilike(f'%{search}%'))
    
    # 角色过滤
    if role:
        query = query.filter(Coach.role == role)
    
    # 球队过滤
    if team_id:
        query = query.filter(Coach.team_id == team_id)
    
    query = query.order_by(Coach.id)
    
    # 如果有分页参数，返回分页数据
    if page and page_size:
        total = query.count()
        coaches = query.offset((page - 1) * page_size).limit(page_size).all()
        return jsonify({
            'items': [c.to_dict() for c in coaches],
            'total': total,
            'page': page,
            'page_size': page_size
        })
    
    # 兼容旧接口，不分页时返回全部
    coaches = query.limit(200).all()
    return jsonify([c.to_dict() for c in coaches])


@bp.route('/<int:coach_id>', methods=['GET'])
def get_coach(coach_id):
    c = Coach.query.get_or_404(coach_id)
    return jsonify(c.to_dict())


@bp.route('/', methods=['POST'])
def create_coach():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    coach = Coach(
        name=name,
        nationality=data.get('nationality'),
        date_of_birth=data.get('date_of_birth'),
        role=data.get('role') or '主教练',
        avatar=data.get('avatar'),
        team_id=data.get('team_id'),
        hire_date=data.get('hire_date'),
        salary=data.get('salary')
    )
    db.session.add(coach)
    db.session.commit()
    return jsonify(coach.to_dict()), 201


@bp.route('/<int:coach_id>', methods=['PUT'])
def update_coach(coach_id):
    c = Coach.query.get_or_404(coach_id)
    data = request.json or {}
    c.name = data.get('name', c.name)
    c.nationality = data.get('nationality', c.nationality)
    c.date_of_birth = data.get('date_of_birth', c.date_of_birth)
    c.role = data.get('role', c.role)
    c.avatar = data.get('avatar', c.avatar)
    c.team_id = data.get('team_id', c.team_id)
    c.hire_date = data.get('hire_date', c.hire_date)
    c.salary = data.get('salary', c.salary)
    db.session.commit()
    return jsonify(c.to_dict())


@bp.route('/<int:coach_id>', methods=['DELETE'])
def delete_coach(coach_id):
    c = Coach.query.get_or_404(coach_id)
    if c.avatar and os.path.exists(os.path.join(get_upload_path(), os.path.basename(c.avatar))):
        try:
            os.remove(os.path.join(get_upload_path(), os.path.basename(c.avatar)))
        except:
            pass
    db.session.delete(c)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_coach_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE coaches SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE coaches AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/team/<int:team_id>', methods=['GET'])
def get_coaches_by_team(team_id):
    coaches = Coach.query.filter_by(team_id=team_id).order_by(Coach.role).all()
    return jsonify([c.to_dict() for c in coaches])


@bp.route('/upload-avatar', methods=['POST'])
def upload_coach_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['avatar']
    coach_id = request.form.get('id')
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(f"coach_{coach_id}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.', 1)[1].lower()}")
        upload_path = get_upload_path()
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))
        avatar_url = f"/{UPLOAD_FOLDER}/{filename}"
        if coach_id:
            coach = db.session.get(Coach, coach_id)
            if coach:
                if coach.avatar:
                    old_path = os.path.join(upload_path, os.path.basename(coach.avatar))
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                coach.avatar = avatar_url
                db.session.commit()
        return jsonify({'avatar': avatar_url})
    return jsonify({'error': 'Invalid file type'}), 400
