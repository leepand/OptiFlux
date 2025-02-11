from .app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# 用户模型
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(
        db.String(20), nullable=False, default="viewer"
    )  # 新字段：用户角色

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """检查用户是否为管理员"""
        return self.role == "admin"

    def can_ops(self):
        """检查用户是否有权操作"""
        return self.role in ["admin", "operator"]


# 定义操作日志模型
class OperationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # 关联用户
    action = db.Column(db.String(100), nullable=False)  # 操作类型
    details = db.Column(db.String(255), nullable=True)  # 额外的描述信息
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<OperationLog {self.action} - {self.timestamp}>"
