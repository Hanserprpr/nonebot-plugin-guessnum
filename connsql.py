import mysql.connector
import re
from datetime import datetime



# 数据库配置
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "****",
    "database": "games"
}

# 注册用户
def signup(name: str, email: str, sex: str, passwd: str, QQ: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (name, email, sex, passwd, QQ)
        VALUES (%s, %s, %s, %s, %s)
        ''', (name, email, sex, passwd, QQ))
        conn.commit()
    except mysql.connector.IntegrityError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

# 查找密码
def search_passwd(identifier: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 判断 identifier 是否是邮箱
    if re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
        cursor.execute('''
        SELECT passwd
        FROM users
        WHERE email = %s
        ''', (identifier,))
    else:
        cursor.execute('''
        SELECT passwd
        FROM users
        WHERE name = %s
        ''', (identifier,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None

#查找用户id
def search_id(name: str = None, QQ: str = None, email: str = None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    if name:
        cursor.execute('''
            SELECT id
            FROM users
            WHERE name = %s
            ''', (name,))
    elif QQ:
        cursor.execute('''
            SELECT id
            FROM users
            WHERE QQ = %s
            ''', (QQ,))
    elif email:
        cursor.execute('''
            SELECT id
            FROM users
            WHERE email = %s
            ''', (email,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


#查找用户名
def search_name(QQ: str = None, user_id: int = None):
    if not QQ and not user_id:
        raise ValueError("必须提供QQ号或用户ID之一进行查询。")

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 优先根据 QQ 进行查询，如果没有则使用 user_id
    if QQ:
        cursor.execute('''
            SELECT name
            FROM users
            WHERE QQ = %s
        ''', (QQ,))
    elif user_id:
        cursor.execute('''
            SELECT name
            FROM users
            WHERE id = %s
        ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return None

#查找用户个人信息
def get_me(QQ:str = None, user_id:str = None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    if not QQ and not user_id:
        raise ValueError("必须提供QQ号或用户ID之一进行查询。")
    if QQ:
        cursor.execute('''
            SELECT *
            FROM users
            WHERE QQ = %s
            ''', (QQ,))
    elif user_id:
        cursor.execute('''
            SELECT *
            FROM users
            WHERE id = %s
        ''', (user_id,))

    result = cursor.fetchone()
    conn.close()
    user_id, name, email, sex, _, qq, status, created_at, updated_at, last_login = result
    
    # 格式化个人中心信息
    return (
        f"用户 ID: {user_id}\n"
        f"用户名: {name}\n"
        f"邮箱: {email}\n"
        f"性别: {'男' if sex == 'M' else '女' if sex == 'F' else '其他'}\n"
        f"QQ: {qq}\n"
        f"账号状态: {'活跃' if status == 1 else '禁用'}\n"
        f"注册时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"最后更新时间: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"最后登录时间:{last_login.strftime('%Y-%m-%d %H:%M:%S')}"
    )




# 更新用户最后登录时间
def update_last_login(QQ: str = None, user_id : str = None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if QQ:
            cursor.execute('''
                UPDATE users
                SET last_login = %s
                WHERE QQ = %s
            ''', (current_time, QQ))
            conn.commit()
        elif user_id:
            cursor.execute('''
                UPDATE users
                SET last_login = %s
                WHERE id = %s
            ''', (current_time, user_id))
            conn.commit()
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

#更新用户信息
def update_user_info(qq: str, name: str = None, passwd: str = None, sex: str = None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if name:
            cursor.execute('''
                UPDATE users
                SET name = %s, updated_at = %s
                WHERE QQ = %s
            ''', (name, current_time, qq))
        if passwd:
            cursor.execute('''
                UPDATE users
                SET passwd = %s, updated_at = %s
                WHERE QQ = %s
            ''', (passwd, current_time, qq))
        if sex:
            cursor.execute('''
                UPDATE users
                SET sex = %s, updated_at = %s
                WHERE QQ = %s
            ''', (sex, current_time, qq))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def get_id(qq:str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id
    FROM users
    where QQ = %s
    ''', (qq,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None



def save_game_attempt(user_id, game_name, score, attempts):
    if not get_id(user_id):
        user_id = user_id
    else:
        user_id = get_id(user_id)
    # 保存每局游戏结果
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO game_attempts (user_id, game_name, score, attempts, result)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, game_name, score, attempts, 'win'))
    conn.commit()
    cursor.close()
    conn.close()

def update_user_stats(user_id, game_name, score, attempts):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    if not get_id(user_id):
        user_id = user_id
    else:
        user_id = get_id(user_id)
    # 检查 `game_stats` 中是否已有记录
    cursor.execute("""
        SELECT * FROM game_stats WHERE user_id = %s AND game_name = %s
    """, (user_id, game_name))
    result = cursor.fetchone()

    if result:
        # 更新现有记录
        cursor.execute("""
            UPDATE game_stats
            SET total_score = total_score + %s,
                games_played = games_played + 1,
                average_score = (total_score + %s) / (games_played + 1),
                min_attempts = LEAST(min_attempts, %s),
                max_attempts = GREATEST(max_attempts, %s),
                play_count = play_count + 1,
                last_played = NOW()
            WHERE user_id = %s AND game_name = %s
        """, (score, score, attempts, attempts, user_id, game_name))
    else:
        # 插入新的记录
        cursor.execute("""
            INSERT INTO game_stats (user_id, game_name, total_score, games_played, average_score, 
                                    wins, play_count, min_attempts, max_attempts, last_played)
            VALUES (%s, %s, %s, 1, %s, 1, 1, %s, %s, NOW())
        """, (user_id, game_name, score, score, attempts, attempts))

    conn.commit()
    cursor.close()
    conn.close()



def fetch_game_history(user_id, game_name):
    if not get_id(user_id):
        user_id = user_id
    else:
        user_id = get_id(user_id)
    # 获取用户的游戏历史记录
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # 查询游戏历史记录
    cursor.execute("""
        SELECT attempts, score, played_at
        FROM game_attempts
        WHERE user_id = %s AND game_name = %s
        ORDER BY played_at DESC
        LIMIT 10;
    """, (user_id, game_name))
    
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return history

def fetch_leaderboard(game_name):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # 获取按平均分数排行的前 10 名
    cursor.execute("""
        SELECT user_id, average_score
        FROM game_stats
        WHERE game_name = %s
        ORDER BY average_score DESC
        LIMIT 10;
    """, (game_name,))
    
    leaderboard = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return leaderboard

import mysql.connector

def get_user_rank(user_id, game_name):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # 确保获取单一的 user_id 值
    if not get_id(user_id):
        user_id = user_id
    else:
        user_id = get_id(user_id)
    
    # 查询用户的当前排名
    cursor.execute("""
        SELECT ranking, user_id, average_score
        FROM (
            SELECT user_id, average_score,
                   RANK() OVER (ORDER BY average_score DESC) AS ranking
            FROM game_stats
            WHERE game_name = %s
        ) AS ranked_stats
        WHERE user_id = %s;
    """, (game_name, user_id))
    
    user_rank = cursor.fetchone()
    if cursor.with_rows:
        cursor.fetchall() 

    cursor.close()
    conn.close()
    
    return user_rank
