"""
新闻公告API路由

提供新闻公告的CRUD操作接口：
- GET /api/news/ - 获取所有新闻
- POST /api/news/ - 创建新闻
- GET /api/news/<id> - 获取单个新闻
- PUT /api/news/<id> - 更新新闻
- DELETE /api/news/<id> - 删除新闻
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import News
from extensions import db

bp = Blueprint('news', __name__)


@bp.route('/', methods=['GET'])
def list_news():
    news = News.query.order_by(News.id).limit(200).all()
    return jsonify([n.to_dict() for n in news])


@bp.route('/<int:news_id>', methods=['GET'])
def get_news(news_id):
    n = News.query.get_or_404(news_id)
    return jsonify(n.to_dict())


@bp.route('/', methods=['POST'])
def create_news():
    data = request.json or {}
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title required'}), 400
    news = News(
        title=title,
        content=data.get('content'),
        author_id=data.get('author_id'),
        published_at=data.get('published_at') or datetime.utcnow(),
        category=data.get('category') or '新闻'
    )
    db.session.add(news)
    db.session.commit()
    return jsonify(news.to_dict()), 201


@bp.route('/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    n = News.query.get_or_404(news_id)
    data = request.json or {}
    n.title = data.get('title', n.title)
    n.content = data.get('content', n.content)
    n.author_id = data.get('author_id', n.author_id)
    n.category = data.get('category', n.category)
    db.session.commit()
    return jsonify(n.to_dict())


@bp.route('/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    n = News.query.get_or_404(news_id)
    db.session.delete(n)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@bp.route('/reset-ids', methods=['POST'])
def reset_news_ids():
    try:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.execute(db.text("SET @new_id = 0"))
        db.session.execute(db.text("UPDATE news SET id = @new_id := @new_id + 1 ORDER BY id"))
        db.session.execute(db.text("ALTER TABLE news AUTO_INCREMENT = 1"))
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        return jsonify({'message': 'ID重置成功'})
    except Exception as e:
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/category/<category>', methods=['GET'])
def get_news_by_category(category):
    news = News.query.filter_by(category=category).order_by(News.published_at.desc()).all()
    return jsonify([n.to_dict() for n in news])
