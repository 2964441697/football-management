"""
Flask应用主入口文件

负责创建应用实例、配置CORS跨域、注册API蓝图和错误处理
"""
import logging
import os
from flask import Flask, jsonify
from config import Config, config, DevelopmentConfig
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(with_db_init=True):
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # 根据环境选择配置
    env = os.getenv('FLASK_ENV', 'development')
    config_class = config.get(env, DevelopmentConfig)
    app.config.from_object(config_class)
    # 限制上传最大大小（字节），默认 2MB，可在配置中覆盖
    app.config.setdefault('MAX_CONTENT_LENGTH', 2 * 1024 * 1024)
    
    # 速率限制配置
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv('REDIS_URL', 'memory://')
    )
    
    # CORS 配置 - 更宽松的配置
    CORS(app,
          resources={r"/*": {"origins": app.config['CORS_ORIGINS'], "supports_credentials": True}},
          methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
          allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
          expose_headers=['Content-Type', 'Authorization'],
          max_age=600)
    db.init_app(app)

    # 仅在开发环境下自动创建表（避免在生产环境误用）
    if with_db_init and env == 'development':
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created successfully (development only)")
            except Exception as e:
                logger.error(f"Failed to create database tables: {e}")

    @app.route('/api/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ok', 'message': 'Backend is running', 'database': 'connected'})
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return jsonify({'status': 'ok', 'message': 'Backend is running', 'database': 'disconnected'}), 200

    # register blueprints
    from api.teams import bp as teams_bp
    from api.players import bp as players_bp
    from api.matches import bp as matches_bp
    from api.seasons import bp as seasons_bp
    from api.transfers import bp as transfers_bp
    from api.auth import bp as auth_bp
    from api.coaches import bp as coaches_bp
    from api.competitions import bp as competitions_bp
    from api.news import bp as news_bp
    from api.finances import bp as finances_bp
    from api.training_plans import bp as training_plans_bp
    from api.contracts import bp as contracts_bp
    from api.match_lineups import bp as match_lineups_bp
    from api.match_events import bp as match_events_bp
    from api.stats import bp as stats_bp
    from api.player_stats import bp as player_stats_bp
    app.register_blueprint(teams_bp, url_prefix='/api/teams')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(seasons_bp, url_prefix='/api/seasons')
    app.register_blueprint(transfers_bp, url_prefix='/api/transfers')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(coaches_bp, url_prefix='/api/coaches')
    app.register_blueprint(competitions_bp, url_prefix='/api/competitions')
    app.register_blueprint(news_bp, url_prefix='/api/news')
    app.register_blueprint(finances_bp, url_prefix='/api/finances')
    app.register_blueprint(training_plans_bp, url_prefix='/api/training-plans')
    app.register_blueprint(contracts_bp, url_prefix='/api/contracts')
    app.register_blueprint(match_lineups_bp, url_prefix='/api/match-lineups')
    app.register_blueprint(match_events_bp, url_prefix='/api/match-events')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(player_stats_bp, url_prefix='/api/player-stats')

    # error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'status': 404, 'message': str(e)}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"500 Internal Server Error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'status': 500, 'message': '服务器内部错误，请检查数据库连接'}), 500

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'status': 400, 'message': str(e)}), 400

    @app.route('/static/backgrounds/<path:filename>')
    def serve_background(filename):
        from flask import send_from_directory
        backgrounds_dir = os.path.join(os.path.dirname(__file__), 'static', 'backgrounds')
        return send_from_directory(backgrounds_dir, filename)

    @app.route('/static/uploads/players/<path:filename>')
    def serve_player_avatar(filename):
        from flask import send_from_directory
        avatars_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'players')
        return send_from_directory(avatars_dir, filename)

    @app.route('/static/uploads/coaches/<path:filename>')
    def serve_coach_avatar(filename):
        from flask import send_from_directory
        avatars_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'coaches')
        return send_from_directory(avatars_dir, filename)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
