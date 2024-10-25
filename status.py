import redis.asyncio as aioredis
from .connsql import get_id
# 创建 Redis 连接池
redis = None

async def init_redis():
    global redis
    redis = await aioredis.Redis.from_url("redis://localhost")

async def set_user_logged_in(qq_id: str, user_id: str):
    """
    设置用户为已登录状态，并存储 QQ 号与用户 ID 的对应关系，同时启用续期机制。
    
    参数:
    qq_id (str): 用户的 QQ 号
    user_id (str): 用户的唯一标识符
    """
    # 设置登录状态，并设置 1 小时的有效期
    await redis.set(f"user_session:{user_id}", "logged_in", ex=3600)
    await redis.set(f"qq_to_user:{qq_id}", user_id, ex=3600)
    await redis.set(f"user_to_qq:{user_id}", qq_id, ex=3600)

async def extend_user_session(user_id: str):
    """
    续期用户的登录状态，每次调用都会延长 Redis 中存储的过期时间。
    
    参数:
    user_id (str): 用户的唯一标识符
    """
    await redis.expire(f"user_session:{user_id}", 3600)

async def set_user_logged_out(user_id: str):
    """
    将用户登出状态从 Redis 中移除，并移除 QQ 号与用户 ID 的对应关系。
    
    参数:
    user_id (str): 用户的唯一标识符
    """
    qq_id = await redis.get(f"user_to_qq:{user_id}")
    await redis.delete(f"user_session:{user_id}")
    await redis.delete(f"qq_to_user:{qq_id}")
    await redis.delete(f"user_to_qq:{user_id}")

async def is_user_logged_in(user_id: str) -> bool:
    """
    检查用户是否已登录，并在登录时续期。
    
    参数:
    user_id (str): 用户的唯一标识符
    
    返回:
    bool: 如果用户已登录则返回 True, 否则返回 False
    """
    try:
        status = await redis.get(f"user_session:{user_id}")
        if status and status.decode() == "logged_in":
            # 自动续期
            await extend_user_session(user_id)
            return True
        return False
    except Exception as e:
        # 处理可能的异常，避免程序中断
        print(f"检查用户登录状态时发生错误: {e}")
        return False



async def get_user_id_from_qq(qq_id: str) -> str:
    """
    根据 QQ 号获取用户 ID。
    
    参数:
    qq_id (str): 用户的 QQ 号
    
    返回:
    str: 对应的用户 ID，如果不存在则返回 None
    """
    return await redis.get(f"qq_to_user:{qq_id}")

async def get_qq_from_user_id(user_id: str) -> str:
    """
    根据用户 ID 获取 QQ 号。
    
    参数:
    user_id (str): 用户的唯一标识符
    
    返回:
    str: 对应的 QQ 号，如果不存在则返回 None
    """
    return await redis.get(f"user_to_qq:{user_id}")
