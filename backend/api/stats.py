"""
统计、批量操作和导出API

提供系统数据统计、批量删除和导出功能
"""
from flask import Blueprint, request, jsonify, Response
from models import Player, Team, Finance, News, Match, Contract, Coach, Competition, Transfer, Season, TrainingPlan
from extensions import db
import csv
import io
from datetime import datetime

bp = Blueprint('stats', __name__)


@bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    try:
        stats = {
            'players': Player.query.count(),
            'teams': Team.query.count(),
            'matches': Match.query.count(),
            'news': News.query.count(),
            'finances': Finance.query.count(),
            'contracts': Contract.query.count(),
            'coaches': Coach.query.count(),
            'competitions': Competition.query.count(),
            'transfers': Transfer.query.count(),
            'seasons': Season.query.count(),
            'training_plans': TrainingPlan.query.count()
        }

        finances = Finance.query.all()
        total_income = sum(f.amount for f in finances if f.amount > 0)
        total_expense = sum(abs(f.amount) for f in finances if f.amount < 0)
        stats['total_income'] = total_income
        stats['total_expense'] = total_expense
        stats['balance'] = total_income - total_expense

        stats['players_by_position'] = {}
        players = Player.query.all()
        for p in players:
            pos = p.position or '未知'
            stats['players_by_position'][pos] = stats['players_by_position'].get(pos, 0) + 1

        stats['finances_by_category'] = {}
        for f in finances:
            cat = f.category or '未分类'
            if f.amount > 0:
                stats['finances_by_category'][f'{cat}_income'] = stats['finances_by_category'].get(f'{cat}_income', 0) + f.amount
            else:
                stats['finances_by_category'][f'{cat}_expense'] = stats['finances_by_category'].get(f'{cat}_expense', 0) + abs(f.amount)

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/export/<resource>', methods=['GET'])
def export_resource(resource):
    try:
        model_map = {
            'players': Player,
            'teams': Team,
            'finances': Finance,
            'news': News,
            'matches': Match,
            'contracts': Contract,
            'coaches': Coach,
            'competitions': Competition,
            'transfers': Transfer,
            'seasons': Season,
            'training-plans': TrainingPlan
        }

        if resource not in model_map:
            return jsonify({'error': 'Invalid resource type'}), 400

        model = model_map[resource]
        items = model.query.all()
        data = [item.to_dict() for item in items]

        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        output.seek(0)
        filename = f'{resource}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    try:
        data = request.json or {}
        resource = data.get('resource')
        ids = data.get('ids', [])

        if not resource or not ids:
            return jsonify({'error': 'resource and ids are required'}), 400

        model_map = {
            'players': Player,
            'teams': Team,
            'finances': Finance,
            'news': News,
            'matches': Match,
            'contracts': Contract,
            'coaches': Coach,
            'competitions': Competition,
            'transfers': Transfer,
            'seasons': Season,
            'training-plans': TrainingPlan
        }

        if resource not in model_map:
            return jsonify({'error': 'Invalid resource type'}), 400

        model = model_map[resource]
        deleted_count = model.query.filter(model.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()

        return jsonify({'status': 'deleted', 'count': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/search', methods=['GET'])
def global_search():
    try:
        query = request.args.get('q', '').lower()
        if not query or len(query) < 1:
            return jsonify({'results': []})

        results = {}

        players = Player.query.filter(Player.name.ilike(f'%{query}%')).limit(10).all()
        results['players'] = [{'id': p.id, 'name': p.name, 'position': p.position} for p in players]

        teams = Team.query.filter(Team.name.ilike(f'%{query}%')).limit(10).all()
        results['teams'] = [{'id': t.id, 'name': t.name} for t in teams]

        news = News.query.filter(News.title.ilike(f'%{query}%')).limit(10).all()
        results['news'] = [{'id': n.id, 'title': n.title, 'category': n.category} for n in news]

        competitions = Competition.query.filter(Competition.name.ilike(f'%{query}%')).limit(10).all()
        results['competitions'] = [{'id': c.id, 'name': c.name, 'type': c.type} for c in competitions]

        return jsonify({'query': query, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
