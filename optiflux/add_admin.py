import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# 确保传入数据库路径
if len(sys.argv) != 2:
    print("Usage: python add_admin.py <db_path>")
    sys.exit(1)

db_path = sys.argv[1]
Base = declarative_base()

# 定义 User 模型
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20), nullable=False, default='viewer')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# 创建数据库连接
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def add_admin_user(username, password):
    # 检查用户名是否已存在
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        return

    # 创建新用户
    admin_user = User(username=username, role='admin')
    admin_user.set_password(password)
    session.add(admin_user)

    try:
        session.commit()
        print(f"Admin user '{username}' added successfully!")
    except IntegrityError:
        session.rollback()
        print("Error: Failed to add user due to integrity error.")
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # 添加管理员用户
    admin_username = input("Enter admin username: ")
    admin_password = input("Enter admin password: ")
    add_admin_user(admin_username, admin_password)
