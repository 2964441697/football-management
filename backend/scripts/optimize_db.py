"""
数据库索引优化脚本

运行此脚本来为现有数据库添加性能优化索引
"""
from extensions import db
from models import *
from sqlalchemy import text

def add_indexes():
    """添加性能优化索引"""
    indexes = [
        # 用户表索引
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        
        # 球队表索引
        "CREATE INDEX IF NOT EXISTS idx_teams_founded_year ON teams(founded_year);",
        
        # 球员表复合索引
        "CREATE INDEX IF NOT EXISTS idx_players_team_position ON players(team_id, position);",
        "CREATE INDEX IF NOT EXISTS idx_players_age ON players(age);",
        
        # 合同表复合索引
        "CREATE INDEX IF NOT EXISTS idx_contracts_player_team ON contracts(player_id, team_id);",
        "CREATE INDEX IF NOT EXISTS idx_contracts_dates ON contracts(start_date, end_date);",
        
        # 转会表复合索引
        "CREATE INDEX IF NOT EXISTS idx_transfers_player_date ON transfers(player_id, transfer_date);",
        "CREATE INDEX IF NOT EXISTS idx_transfers_teams ON transfers(from_team_id, to_team_id);",
        
        # 比赛表复合索引
        "CREATE INDEX IF NOT EXISTS idx_matches_season_teams ON matches(season_id, home_team_id, away_team_id);",
        "CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(start_time);",
        
        # 比赛阵容索引
        "CREATE INDEX IF NOT EXISTS idx_match_lineups_match_team ON match_lineups(match_id, team_id);",
        "CREATE INDEX IF NOT EXISTS idx_match_lineups_player ON match_lineups(player_id);",
        
        # 比赛事件索引
        "CREATE INDEX IF NOT EXISTS idx_match_events_match ON match_events(match_id);",
        "CREATE INDEX IF NOT EXISTS idx_match_events_player ON match_events(player_id);",
        
        # 球员统计复合索引
        "CREATE INDEX IF NOT EXISTS idx_player_stats_season_player ON player_stats(season_id, player_id);",
        
        # 财务表索引
        "CREATE INDEX IF NOT EXISTS idx_finances_team_date ON finances(team_id, record_date);",
        "CREATE INDEX IF NOT EXISTS idx_finances_category ON finances(category);",
    ]
    
    try:
        for index_sql in indexes:
            db.session.execute(text(index_sql))
        
        db.session.commit()
        print("✅ 数据库索引添加成功！")
        
        # 显示索引信息
        show_indexes()
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 添加索引时出错: {e}")

def show_indexes():
    """显示当前索引状态"""
    tables = ['users', 'teams', 'players', 'contracts', 'transfers', 'matches', 
              'match_lineups', 'match_events', 'player_stats', 'finances']
    
    print("\n📊 当前数据库索引状态:")
    for table in tables:
        try:
            result = db.session.execute(text(f"SHOW INDEX FROM {table}"))
            indexes = result.fetchall()
            if indexes:
                print(f"\n🔹 {table}:")
                for idx in indexes:
                    print(f"   - {idx[2]} (列: {idx[4]})")
        except Exception as e:
            print(f"   ⚠️  无法获取 {table} 的索引信息: {e}")

if __name__ == '__main__':
    from app import create_app
    app = create_app(with_db_init=False)
    
    with app.app_context():
        add_indexes()