import sqlite3
import json
import time
import os
from pathlib import Path

class DatabaseManager:
    """数据库管理类，用于处理对话记录和用户偏好"""
    
    def __init__(self, db_path=None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认数据库路径
            self.db_path = Path("backend/static/data/voice_chat.db")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = Path(db_path)
        
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库连接和表结构"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            
            # 创建对话历史表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_input TEXT,
                    ai_response TEXT,
                    role_id TEXT,
                    timestamp TEXT,
                    additional_data TEXT
                )
            ''')
            
            # 创建用户偏好表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    preferred_role TEXT,
                    voice_settings TEXT,
                    last_login TEXT,
                    settings_json TEXT
                )
            ''')
            
            # 创建角色配置表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id TEXT UNIQUE,
                    role_name TEXT,
                    voice_id TEXT,
                    character_id TEXT,
                    config_json TEXT
                )
            ''')
            
            self.conn.commit()
            print(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def save_conversation(self, user_input, ai_response, role_id, session_id=None, additional_data=None):
        """保存对话记录到数据库
        
        Args:
            user_input: 用户输入
            ai_response: AI回复
            role_id: 角色ID
            session_id: 会话ID，如果为None则使用当前时间戳
            additional_data: 额外数据，将被存储为JSON
        
        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.conn:
                self._init_db()
                
            if not session_id:
                session_id = f"session_{int(time.time())}"
                
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            additional_json = None
            if additional_data:
                additional_json = json.dumps(additional_data, ensure_ascii=False)
            
            self.cursor.execute(
                "INSERT INTO conversations (session_id, user_input, ai_response, role_id, timestamp, additional_data) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, user_input, ai_response, role_id, timestamp, additional_json)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存对话记录失败: {e}")
            return False
    
    def get_conversations(self, session_id=None, limit=10, role_id=None):
        """获取对话历史
        
        Args:
            session_id: 会话ID，如果为None则获取所有会话
            limit: 限制返回结果数量
            role_id: 角色ID过滤
            
        Returns:
            list: 对话记录列表
        """
        try:
            if not self.conn:
                self._init_db()
                
            query = "SELECT session_id, user_input, ai_response, role_id, timestamp FROM conversations"
            params = []
            
            if session_id or role_id:
                query += " WHERE"
                
                if session_id:
                    query += " session_id = ?"
                    params.append(session_id)
                    
                if role_id:
                    if session_id:
                        query += " AND"
                    query += " role_id = ?"
                    params.append(role_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, tuple(params))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取对话历史失败: {e}")
            return []
    
    def save_role_config(self, role_id, role_name, voice_id, character_id, config=None):
        """保存角色配置
        
        Args:
            role_id: 角色ID
            role_name: 角色名称
            voice_id: 语音ID
            character_id: 角色性格ID
            config: 其他配置，将被存储为JSON
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.conn:
                self._init_db()
                
            config_json = None
            if config:
                config_json = json.dumps(config, ensure_ascii=False)
                
            # 使用REPLACE语法，如果role_id已存在则更新
            self.cursor.execute(
                "REPLACE INTO role_configs (role_id, role_name, voice_id, character_id, config_json) VALUES (?, ?, ?, ?, ?)",
                (role_id, role_name, voice_id, character_id, config_json)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存角色配置失败: {e}")
            return False
    
    def get_role_configs(self, role_id=None):
        """获取角色配置
        
        Args:
            role_id: 角色ID，如果为None则获取所有角色
            
        Returns:
            list: 角色配置列表
        """
        try:
            if not self.conn:
                self._init_db()
                
            if role_id:
                self.cursor.execute(
                    "SELECT role_id, role_name, voice_id, character_id, config_json FROM role_configs WHERE role_id = ?",
                    (role_id,)
                )
                return self.cursor.fetchone()
            else:
                self.cursor.execute(
                    "SELECT role_id, role_name, voice_id, character_id, config_json FROM role_configs"
                )
                return self.cursor.fetchall()
        except Exception as e:
            print(f"获取角色配置失败: {e}")
            return [] if role_id is None else None
    
    def save_user_preference(self, user_id, preferred_role=None, voice_settings=None, settings=None):
        """保存用户偏好设置
        
        Args:
            user_id: 用户ID
            preferred_role: 偏好角色ID
            voice_settings: 语音设置
            settings: 其他设置，将被存储为JSON
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.conn:
                self._init_db()
                
            last_login = time.strftime("%Y-%m-%d %H:%M:%S")
            settings_json = None
            
            if settings:
                settings_json = json.dumps(settings, ensure_ascii=False)
                
            # 检查用户是否已存在
            self.cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user_id,))
            if self.cursor.fetchone():
                # 更新现有用户
                self.cursor.execute(
                    "UPDATE user_preferences SET preferred_role = ?, voice_settings = ?, last_login = ?, settings_json = ? WHERE user_id = ?",
                    (preferred_role, voice_settings, last_login, settings_json, user_id)
                )
            else:
                # 插入新用户
                self.cursor.execute(
                    "INSERT INTO user_preferences (user_id, preferred_role, voice_settings, last_login, settings_json) VALUES (?, ?, ?, ?, ?)",
                    (user_id, preferred_role, voice_settings, last_login, settings_json)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存用户偏好失败: {e}")
            return False
    
    def get_user_preference(self, user_id):
        """获取用户偏好设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户偏好设置
        """
        try:
            if not self.conn:
                self._init_db()
                
            self.cursor.execute(
                "SELECT preferred_role, voice_settings, last_login, settings_json FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                preferred_role, voice_settings, last_login, settings_json = result
                preference = {
                    "user_id": user_id,
                    "preferred_role": preferred_role,
                    "voice_settings": voice_settings,
                    "last_login": last_login
                }
                
                if settings_json:
                    try:
                        settings = json.loads(settings_json)
                        preference.update(settings)
                    except:
                        pass
                        
                return preference
            return None
        except Exception as e:
            print(f"获取用户偏好失败: {e}")
            return None


# 单例模式
_db_instance = None

def get_db_manager(db_path=None):
    """获取数据库管理器单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
