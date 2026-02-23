"""
训练计划API路由

提供训练计划的CRUD操作接口：
- GET /api/training-plans/ - 获取所有训练计划
- POST /api/training-plans/ - 创建训练计划
- GET /api/training-plans/<id> - 获取单个训练计划
- PUT /api/training-plans/<id> - 更新训练计划
- DELETE /api/training-plans/<id> - 删除训练计划
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import TrainingPlan
from extensions import db

bp = Blueprint('training_plans', __name__)


@bp.route('/', methods=['GET'])
def list_training_plans():
    training_plans = TrainingPlan.query.options(joinedload(TrainingPlan.team)).order_by(TrainingPlan.id).limit(200).all()
    return jsonify([t.to_dict() for t in training_plans])


@bp.route('/<int:training_plan_id>', methods=['GET'])
def get_training_plan(training_plan_id):
    t = TrainingPlan.query.get_or_404(training_plan_id)
    return jsonify(t.to_dict())


@bp.route('/', methods=['POST'])
def create_training_plan():
    data = request.json or {}
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title required'}), 400
    training_plan = TrainingPlan(
        team_id=data.get('team_id'),
        title=title,
        content=data.get('content'),
        training_date=data.get('training_date'),
        duration_minutes=data.get('duration_minutes') or 90,
        location=data.get('location')
    )
    db.session.add(training_plan)
    db.session.commit()
    return jsonify(training_plan.to_dict()), 201


@bp.route('/<int:training_plan_id>', methods=['PUT'])
def update_training_plan(training_plan_id):
    t = TrainingPlan.query.get_or_404(training_plan_id)
    data = request.json or {}
    t.team_id = data.get('team_id', t.team_id)
    t.title = data.get('title', t.title)
    t.content = data.get('content', t.content)
    t.training_date = data.get('training_date', t.training_date)
    t.duration_minutes = data.get('duration_minutes', t.duration_minutes)
    t.location = data.get('location', t.location)
    db.session.commit()
    return jsonify(t.to_dict())


@bp.route('/<int:training_plan_id>', methods=['DELETE'])
def delete_training_plan(training_plan_id):
    t = TrainingPlan.query.get_or_404(training_plan_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_training_plan_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE training_plans SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE training_plans AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/team/<int:team_id>', methods=['GET'])
def get_training_plans_by_team(team_id):
    training_plans = TrainingPlan.query.filter_by(team_id=team_id).order_by(TrainingPlan.training_date.desc()).all()
    return jsonify([t.to_dict() for t in training_plans])


@bp.route('/upcoming', methods=['GET'])
def get_upcoming_training_plans():
    from datetime import date
    training_plans = TrainingPlan.query.filter(TrainingPlan.training_date >= date.today()).order_by(TrainingPlan.training_date).limit(20).all()
    return jsonify([t.to_dict() for t in training_plans])
