"""
数据模型定义文件

定义所有数据库表的ORM模型类：
- User: 用户表
- Team: 球队表
- Player: 球员表
- Season: 赛季表
- Match: 比赛表
- Transfer: 转会记录表
- 其他辅助模型
"""
from datetime import datetime
from decimal import Decimal
from extensions import db


class BaseModel(db.Model):
    """基础模型类，提供通用字段"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(BaseModel):
    """用户表"""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.Text)
    role = db.Column(db.String(30), nullable=False, default='viewer', index=True)

    # 角色常量
    ROLE_ADMIN = 'admin'
    ROLE_COACH = 'coach'
    ROLE_VIEWER = 'viewer'

    ROLE_CHOICES = [
        (ROLE_ADMIN, '管理员'),
        (ROLE_COACH, '教练'),
        (ROLE_VIEWER, '观察者')
    ]

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'role': self.role,
            'role_label': self.get_role_label(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_role_label(self):
        for value, label in self.ROLE_CHOICES:
            if value == self.role:
                return label
        return self.role


class Team(BaseModel):
    """球队表"""
    __tablename__ = 'teams'
    
    name = db.Column(db.String(120), nullable=False, index=True)
    logo = db.Column(db.String(255))
    home_stadium = db.Column(db.String(120))
    founded_year = db.Column(db.Integer)
    budget = db.Column(db.Numeric(18, 2), default=0.00)

    # 关联
    players = db.relationship('Player', back_populates='team', lazy='dynamic')
    coaches = db.relationship('Coach', backref='team_coaches', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
            'home_stadium': self.home_stadium,
            'founded_year': self.founded_year,
            'budget': float(self.budget) if self.budget else 0.0
        }


class Player(BaseModel):
    """球员表"""
    __tablename__ = 'players'
    
    name = db.Column(db.String(120), nullable=False, index=True)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(80), index=True)
    position = db.Column(db.String(30), index=True)
    height_cm = db.Column(db.Integer)
    avatar = db.Column(db.Text)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)

    # 关联 - 使用 lazy='joined' 预加载避免 N+1
    team = db.relationship('Team', back_populates='players', lazy='joined')
    contracts = db.relationship('Contract', back_populates='player', lazy='dynamic', passive_deletes=True)
    stats = db.relationship('PlayerStat', back_populates='player', lazy='dynamic', passive_deletes=True)
    transfers = db.relationship('Transfer', back_populates='player', lazy='dynamic', passive_deletes=True)

    # 复合索引
    __table_args__ = (
        db.Index('idx_player_team_position', 'team_id', 'position'),
        db.Index('idx_player_nationality_position', 'nationality', 'position'),
    )

    def to_dict(self):
        # 使用 sqlalchemy.orm.strategies.LazyLoader 检查是否已加载
        team_name = None
        if 'team' in self.__dict__ or hasattr(self, '_sa_instance_state'):
            try:
                team_name = self.team.name if self.team else None
            except:
                team_name = None
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'nationality': self.nationality,
            'position': self.position,
            'height_cm': self.height_cm,
            'avatar': self.avatar,
            'team_id': self.team_id,
            'team_name': team_name
        }


class Season(BaseModel):
    """赛季表"""
    __tablename__ = 'seasons'
    
    name = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }


class Contract(BaseModel):
    """合同表"""
    __tablename__ = 'contracts'
    
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    start_date = db.Column(db.Date, index=True)
    end_date = db.Column(db.Date, index=True)
    salary = db.Column(db.Numeric(18, 2))
    release_clause = db.Column(db.Numeric(18, 2))

    # 关联 - 使用 lazy='joined' 预加载
    player = db.relationship('Player', back_populates='contracts', lazy='joined')
    team = db.relationship('Team', backref='contracts', lazy='joined')

    def _safe_getattr(self, attr, default=None):
        try:
            return getattr(self, attr, default)
        except:
            return default

    def to_dict(self):
        player_obj = self._safe_getattr('player')
        team_obj = self._safe_getattr('team')
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': player_obj.name if player_obj else None,
            'team_id': self.team_id,
            'team_name': team_obj.name if team_obj else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'salary': float(self.salary) if self.salary else None,
            'release_clause': float(self.release_clause) if self.release_clause else None
        }


class Transfer(BaseModel):
    """转会表"""
    __tablename__ = 'transfers'
    
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), index=True)
    from_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    to_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    fee = db.Column(db.Numeric(18, 2))
    transfer_date = db.Column(db.Date, index=True)

    # 关联 - 使用 lazy='joined' 预加载
    player = db.relationship('Player', back_populates='transfers', passive_deletes=True, lazy='joined')
    from_team = db.relationship('Team', foreign_keys=[from_team_id], backref='transfers_out', lazy='joined')
    to_team = db.relationship('Team', foreign_keys=[to_team_id], backref='transfers_in', lazy='joined')

    def _safe_getattr(self, attr, default=None):
        try:
            return getattr(self, attr, default)
        except:
            return default

    def to_dict(self):
        player_obj = self._safe_getattr('player')
        from_team_obj = self._safe_getattr('from_team')
        to_team_obj = self._safe_getattr('to_team')
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': player_obj.name if player_obj else None,
            'from_team_id': self.from_team_id,
            'from_team_name': from_team_obj.name if from_team_obj else None,
            'to_team_id': self.to_team_id,
            'to_team_name': to_team_obj.name if to_team_obj else None,
            'fee': float(self.fee) if self.fee else None,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None
        }


class Match(BaseModel):
    """比赛表"""
    __tablename__ = 'matches'
    
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), index=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    start_time = db.Column(db.DateTime, index=True)
    venue = db.Column(db.String(120), index=True)

    # 关联 - 使用 lazy='joined' 预加载
    season = db.relationship('Season', backref='matches', lazy='joined')
    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_matches', lazy='joined')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_matches', lazy='joined')

    # 复合索引
    __table_args__ = (
        db.Index('idx_match_teams', 'home_team_id', 'away_team_id'),
    )

    def _safe_getattr(self, attr, default=None):
        try:
            return getattr(self, attr, default)
        except:
            return default

    def to_dict(self):
        return {
            'id': self.id,
            'season_id': self.season_id,
            'season_name': self._safe_getattr('season', {}).name if self._safe_getattr('season') else None,
            'home_team_id': self.home_team_id,
            'home_team_name': self._safe_getattr('home_team', {}).name if self._safe_getattr('home_team') else None,
            'away_team_id': self.away_team_id,
            'away_team_name': self._safe_getattr('away_team', {}).name if self._safe_getattr('away_team') else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'venue': self.venue
        }


class MatchLineup(BaseModel):
    """比赛阵容表"""
    __tablename__ = 'match_lineups'
    
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id', ondelete='CASCADE'), index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), index=True)
    is_starting = db.Column(db.Boolean, default=False)
    shirt_number = db.Column(db.Integer)

    # 关联
    match = db.relationship('Match', backref='lineups')
    team = db.relationship('Team')
    player = db.relationship('Player')

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'team_id': self.team_id,
            'player_id': self.player_id,
            'is_starting': self.is_starting,
            'shirt_number': self.shirt_number
        }


class MatchEvent(BaseModel):
    """比赛事件表"""
    __tablename__ = 'match_events'
    
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id', ondelete='CASCADE'), index=True)
    minute = db.Column(db.Integer)
    event_type = db.Column(db.String(50), index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='SET NULL'), index=True)
    related_player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='SET NULL'))
    description = db.Column(db.Text)

    # 关联
    match = db.relationship('Match', backref='events')
    player = db.relationship('Player', foreign_keys=[player_id])
    related_player = db.relationship('Player', foreign_keys=[related_player_id])

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'minute': self.minute,
            'event_type': self.event_type,
            'player_id': self.player_id,
            'related_player_id': self.related_player_id,
            'description': self.description
        }


class MatchStat(BaseModel):
    """比赛统计表"""
    __tablename__ = 'match_stats'
    
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    possession = db.Column(db.Numeric(5, 2))
    shots = db.Column(db.Integer)
    shots_on_target = db.Column(db.Integer)
    passes = db.Column(db.Integer)

    # 关联
    match = db.relationship('Match', backref='stats')
    team = db.relationship('Team')

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'team_id': self.team_id,
            'possession': float(self.possession) if self.possession else None,
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,
            'passes': self.passes
        }


class PlayerStat(BaseModel):
    """球员统计表"""
    __tablename__ = 'player_stats'
    
    player_id = db.Column(db.Integer, db.ForeignKey('players.id', ondelete='CASCADE'), index=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), index=True)
    matches_played = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)

    # 关联
    player = db.relationship('Player', back_populates='stats')
    season = db.relationship('Season', backref='player_stats')

    # 复合索引
    __table_args__ = (
        db.Index('idx_player_season_stats', 'player_id', 'season_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'season_id': self.season_id,
            'matches_played': self.matches_played,
            'goals': self.goals,
            'assists': self.assists,
            'yellow_cards': self.yellow_cards,
            'red_cards': self.red_cards,
            'minutes_played': self.minutes_played
        }


class Finance(BaseModel):
    """财务表"""
    __tablename__ = 'finances'
    
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    category = db.Column(db.String(100), index=True)
    amount = db.Column(db.Numeric(18, 2))
    note = db.Column(db.Text)
    record_date = db.Column(db.Date, index=True)

    # 关联 - 使用 lazy='joined' 预加载
    team = db.relationship('Team', backref='finances', lazy='joined')

    # 复合索引
    __table_args__ = (
        db.Index('idx_finance_team_category', 'team_id', 'category'),
    )

    def _safe_getattr(self, attr, default=None):
        try:
            return getattr(self, attr, default)
        except:
            return default

    def to_dict(self):
        team_obj = self._safe_getattr('team')
        return {
            'id': self.id,
            'team_id': self.team_id,
            'team_name': team_obj.name if team_obj else None,
            'category': self.category,
            'amount': float(self.amount) if self.amount else None,
            'note': self.note,
            'record_date': self.record_date.isoformat() if self.record_date else None
        }


class Competition(BaseModel):
    """赛事表"""
    __tablename__ = 'competitions'
    
    name = db.Column(db.String(120), nullable=False, index=True)
    type = db.Column(db.String(50), index=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), index=True)

    # 关联
    season = db.relationship('Season', backref='competitions')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'season_id': self.season_id
        }


class Coach(BaseModel):
    """教练表"""
    __tablename__ = 'coaches'
    
    name = db.Column(db.String(120), nullable=False, index=True)
    nationality = db.Column(db.String(80))
    date_of_birth = db.Column(db.Date)
    role = db.Column(db.String(50), default='主教练')
    avatar = db.Column(db.Text)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    hire_date = db.Column(db.Date)
    salary = db.Column(db.Numeric(18, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'nationality': self.nationality,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'role': self.role,
            'avatar': self.avatar,
            'team_id': self.team_id,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'salary': float(self.salary) if self.salary else None
        }


class TrainingPlan(BaseModel):
    """训练计划表"""
    __tablename__ = 'training_plans'
    
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    training_date = db.Column(db.Date, index=True)
    duration_minutes = db.Column(db.Integer)
    location = db.Column(db.String(120))

    # 关联 - 使用 lazy='joined' 预加载
    team = db.relationship('Team', backref='training_plans', lazy='joined')

    def _safe_getattr(self, attr, default=None):
        try:
            return getattr(self, attr, default)
        except:
            return default

    def to_dict(self):
        team_obj = self._safe_getattr('team')
        return {
            'id': self.id,
            'team_id': self.team_id,
            'team_name': team_obj.name if team_obj else None,
            'title': self.title,
            'content': self.content,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'duration_minutes': self.duration_minutes,
            'location': self.location
        }


class News(BaseModel):
    """新闻表"""
    __tablename__ = 'news'
    
    title = db.Column(db.String(255), nullable=False, index=True)
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    published_at = db.Column(db.DateTime, index=True)
    category = db.Column(db.String(50), index=True)

    # 关联
    author = db.relationship('User', backref='news')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'category': self.category
        }


class OperationLog(db.Model):
    """操作日志表"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    username = db.Column(db.String(100))
    action = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(100), index=True)
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    user = db.relationship('User', backref='operation_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
