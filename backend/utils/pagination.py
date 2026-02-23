"""
分页工具类

提供统一的分页功能
"""
from math import ceil
from flask import request

class Pagination:
    """分页工具类"""
    
    def __init__(self, page=1, per_page=20, max_per_page=100):
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), max_per_page)
        self.max_per_page = max_per_page
    
    @classmethod
    def from_request(cls, default_per_page=20, max_per_page=100):
        """从请求参数创建分页对象"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', default_per_page, type=int)
        return cls(page, per_page, max_per_page)
    
    def get_offset(self):
        """获取偏移量"""
        return (self.page - 1) * self.per_page
    
    def paginate_query(self, query):
        """对查询进行分页"""
        total = query.count()
        items = query.offset(self.get_offset()).limit(self.per_page).all()
        return PaginatedResult(items, total, self.page, self.per_page)

class PaginatedResult:
    """分页结果"""
    
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = ceil(total / per_page) if total > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.pages
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'items': self.items,
            'pagination': {
                'page': self.page,
                'per_page': self.per_page,
                'total': self.total,
                'pages': self.pages,
                'has_prev': self.has_prev,
                'has_next': self.has_next,
                'prev_num': self.page - 1 if self.has_prev else None,
                'next_num': self.page + 1 if self.has_next else None
            }
        }