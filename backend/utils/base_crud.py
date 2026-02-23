"""
基础CRUD操作类

提供通用的CRUD操作，减少重复代码
包含认证装饰器支持和统一的错误处理
"""
import logging
from functools import wraps
from flask import request, jsonify, g
from extensions import db
from utils.pagination import Pagination, PaginatedResult

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API 异常类"""
    def __init__(self, message, status_code=400, code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or 'ERROR'
    
    def to_response(self):
        return jsonify({
            'error': self.message,
            'code': self.code
        }), self.status_code


def handle_api_errors(f):
    """API 错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {e.message}")
            return e.to_response()
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({
                'error': '服务器内部错误',
                'code': 'INTERNAL_ERROR'
            }), 500
    return decorated_function


class BaseCRUD:
    """基础CRUD操作类"""
    
    def __init__(self, model, resource_name=None):
        """
        初始化 CRUD 操作类
        
        Args:
            model: SQLAlchemy 模型类
            resource_name: 资源名称（用于日志）
        """
        self.model = model
        self.resource_name = resource_name or model.__tablename__
    
    def get_list(self, query=None, search_fields=None, default_order=None, filters=None):
        """
        获取列表数据（带分页和搜索）
        
        Args:
            query: 初始查询对象
            search_fields: 可搜索的字段列表
            default_order: 默认排序字段
            filters: 额外的过滤条件函数列表
        """
        if query is None:
            query = self.model.query
        
        # 搜索功能（使用参数化查询防止SQL注入）
        if search_fields:
            search_term = request.args.get('search', '').strip()
            if search_term:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        # 使用参数化查询
                        search_pattern = f'%{search_term}%'
                        search_conditions.append(
                            getattr(self.model, field).ilike(search_pattern)
                        )
                if search_conditions:
                    from sqlalchemy import or_
                    query = query.filter(or_(*search_conditions))
        
        # 应用额外过滤条件
        if filters:
            for filter_func in filters:
                query = filter_func(query, request.args)
        
        # 默认排序
        if default_order:
            if isinstance(default_order, str) and hasattr(self.model, default_order):
                query = query.order_by(getattr(self.model, default_order))
            elif hasattr(default_order, '__call__'):
                query = default_order(query)
        
        # 分页
        pagination = Pagination.from_request(default_per_page=20, max_per_page=100)
        paginated_result = pagination.paginate_query(query)
        
        # 转换为字典格式
        items = [item.to_dict() for item in paginated_result.items]
        result = PaginatedResult(items, paginated_result.total, paginated_result.page, paginated_result.per_page)
        
        return jsonify(result.to_dict())
    
    def get_by_id(self, item_id):
        """根据ID获取单个项目"""
        item = db.session.get(self.model, item_id)
        if not item:
            raise APIError(f'{self.resource_name} 不存在', 404, 'NOT_FOUND')
        return jsonify(item.to_dict())
    
    def create(self, required_fields=None, optional_fields=None, validation_rules=None, 
               before_create=None, after_create=None):
        """
        创建新项目
        
        Args:
            required_fields: 必填字段列表
            optional_fields: 可选字段列表
            validation_rules: 验证规则字典 {field: (validator, error_message)}
            before_create: 创建前的回调函数 (data) -> data
            after_create: 创建后的回调函数 (item) -> None
        """
        data = request.json or {}
        
        # 验证必填字段
        if required_fields:
            for field in required_fields:
                value = data.get(field)
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    raise APIError(f'{field} 是必填字段', 400, 'FIELD_REQUIRED')
        
        # 自定义验证
        if validation_rules:
            for field, rule in validation_rules.items():
                if field in data and data[field] is not None:
                    validator, error_msg = rule
                    if not validator(data[field]):
                        raise APIError(error_msg, 400, 'VALIDATION_ERROR')
        
        # 创建前回调
        if before_create:
            data = before_create(data)
        
        # 创建新实例
        allowed_fields = (required_fields or []) + (optional_fields or [])
        item_data = {k: v for k, v in data.items() if k in allowed_fields}
        item = self.model(**item_data)
        
        db.session.add(item)
        db.session.commit()
        
        # 创建后回调
        if after_create:
            after_create(item)
        
        logger.info(f"{self.resource_name} 创建成功: ID={item.id}")
        
        return jsonify(item.to_dict()), 201
    
    def update(self, item_id, updatable_fields=None, validation_rules=None,
               before_update=None, after_update=None):
        """
        更新项目
        
        Args:
            item_id: 项目ID
            updatable_fields: 可更新字段列表
            validation_rules: 验证规则字典
            before_update: 更新前的回调函数 (item, data) -> data
            after_update: 更新后的回调函数 (item) -> None
        """
        item = db.session.get(self.model, item_id)
        if not item:
            raise APIError(f'{self.resource_name} 不存在', 404, 'NOT_FOUND')
        
        data = request.json or {}
        
        # 自定义验证
        if validation_rules:
            for field, rule in validation_rules.items():
                if field in data and data[field] is not None:
                    validator, error_msg = rule
                    if not validator(data[field]):
                        raise APIError(error_msg, 400, 'VALIDATION_ERROR')
        
        # 更新前回调
        if before_update:
            data = before_update(item, data)
        
        # 更新字段
        if updatable_fields:
            for field in updatable_fields:
                if field in data:
                    setattr(item, field, data[field])
        
        db.session.commit()
        
        # 更新后回调
        if after_update:
            after_update(item)
        
        logger.info(f"{self.resource_name} 更新成功: ID={item_id}")
        
        return jsonify(item.to_dict())
    
    def delete(self, item_id, before_delete=None, after_delete=None):
        """
        删除项目
        
        Args:
            item_id: 项目ID
            before_delete: 删除前的回调函数 (item) -> None
            after_delete: 删除后的回调函数 (item_id) -> None
        """
        item = db.session.get(self.model, item_id)
        if not item:
            raise APIError(f'{self.resource_name} 不存在', 404, 'NOT_FOUND')
        
        # 删除前回调
        if before_delete:
            before_delete(item)
        
        db.session.delete(item)
        db.session.commit()
        
        # 删除后回调
        if after_delete:
            after_delete(item_id)
        
        logger.info(f"{self.resource_name} 删除成功: ID={item_id}")
        
        return jsonify({
            'message': '删除成功',
            'id': item_id
        })
    
    def batch_delete(self, ids, before_delete=None):
        """
        批量删除
        
        Args:
            ids: ID 列表
            before_delete: 每个项目删除前的回调函数 (item) -> None
        """
        if not ids or not isinstance(ids, list):
            raise APIError('请提供要删除的ID列表', 400, 'INVALID_IDS')
        
        deleted_count = 0
        for item_id in ids:
            item = db.session.get(self.model, item_id)
            if item:
                if before_delete:
                    before_delete(item)
                db.session.delete(item)
                deleted_count += 1
        
        db.session.commit()
        
        logger.info(f"{self.resource_name} 批量删除成功: 共删除 {deleted_count} 条")
        
        return jsonify({
            'message': f'成功删除 {deleted_count} 条记录',
            'deleted_count': deleted_count
        })


class BaseModelAPI:
    """模型API基类，集成BaseCRUD功能"""
    
    def __init__(self, model, blueprint, search_fields=None, default_order='id',
                 resource_name=None, auth_required=False):
        """
        初始化 API
        
        Args:
            model: SQLAlchemy 模型类
            blueprint: Flask Blueprint
            search_fields: 可搜索字段列表
            default_order: 默认排序字段
            resource_name: 资源名称
            auth_required: 是否需要认证（影响写操作）
        """
        self.crud = BaseCRUD(model, resource_name)
        self.blueprint = blueprint
        self.search_fields = search_fields
        self.default_order = default_order
        self.auth_required = auth_required
    
    @handle_api_errors
    def list(self):
        """获取列表"""
        return self.crud.get_list(
            search_fields=self.search_fields, 
            default_order=self.default_order
        )
    
    @handle_api_errors
    def get(self, item_id):
        """获取单个项目"""
        return self.crud.get_by_id(item_id)
    
    @handle_api_errors
    def create(self):
        """创建项目 - 子类需要重写"""
        return self.crud.create()
    
    @handle_api_errors
    def update(self, item_id):
        """更新项目 - 子类需要重写"""
        return self.crud.update(item_id)
    
    @handle_api_errors
    def delete(self, item_id):
        """删除项目"""
        return self.crud.delete(item_id)


def validate_required(value):
    """验证必填值"""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == '':
        return False
    return True


def validate_range(min_val=None, max_val=None):
    """创建范围验证器"""
    def validator(value):
        if not isinstance(value, (int, float)):
            return False
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True
    return validator


def validate_length(min_len=None, max_len=None):
    """创建长度验证器"""
    def validator(value):
        if not isinstance(value, str):
            return False
        if min_len is not None and len(value) < min_len:
            return False
        if max_len is not None and len(value) > max_len:
            return False
        return True
    return validator


def validate_in_list(allowed_values):
    """创建枚举验证器"""
    def validator(value):
        return value in allowed_values
    return validator
