"""
数据库扩展模块

解决Flask-SQLAlchemy循环导入问题
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
