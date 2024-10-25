import bcrypt
from .connsql import search_passwd

def encrypt(passwd: str) -> str:
    password = passwd.encode('utf-8')
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed_password.decode('utf-8')  # 返回字符串格式，便于存储



async def decrypt(passwd: str, identifier: str):
    """
    解密函数

    参数:
    passwd (str): 原始的密码字符串
    identifier (str): 用户名或邮箱

    返回:
    bool: 如果密码匹配则返回 True,否则返回 False
    """
    input_password = passwd.encode('utf-8')
    hashed_password = search_passwd(identifier)
    if hashed_password is None:
        return False
    
    hashed_password = hashed_password.encode('utf-8')
    # 直接返回检查结果
    return bcrypt.checkpw(input_password, hashed_password)
