import os
from app import create_app, db, User
import json
from werkzeug.security import generate_password_hash

print("--- Running run_init_db.py ---")

# 创建一个应用实例
app = create_app()

# 在应用上下文中执行数据库操作
with app.app_context():
    print("App context created. Initializing database...")
    try:
        # 删除所有现有的表
        db.drop_all()
        print("Existing tables dropped.")
        
        # 创建所有新的表
        db.create_all()
        print("Database tables created successfully.")
        
        # 迁移用户数据
        print("Attempting to migrate user data from users.json...")
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
                for username, data in users_data.items():
                    user = User(
                        id=username, 
                        role=data['role'], 
                        allowed_units=data.get('allowed_units', [])
                    )
                    user.set_password(data['password'])
                    db.session.add(user)
                db.session.commit()
                print("User data migrated successfully.")
        except FileNotFoundError:
            print("users.json not found, skipping user migration.")
        except Exception as e:
            print(f"An error occurred during user migration: {e}")
            db.session.rollback()

    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
        # 即使失败也退出，让 start.sh 知道
        exit(1)

print("--- Database initialization script finished ---")
