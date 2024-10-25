from nonebot import get_driver, on_command, logger, on_message, require
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
from nonebot.message import event_preprocessor
from .config import Config
from .connsql import search_name, get_me, signup, update_last_login, update_user_info, search_passwd, get_id
from .passwd import decrypt, encrypt
from .status import set_user_logged_in, is_user_logged_in, init_redis, set_user_logged_out
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot_plugin_apscheduler import scheduler
from nonebot.matcher import Matcher
from .games.guess_number import guess_game, history_command, leaderboard_command, rank_command #猜数字相关指令
from .console import handle_signup, handle_login, handle_edit, handle_getme, handle_log_out #个人中心相关指令

from .games.liar.game import LiarsGame
from .games.liar.redis_utils import *

from nonebot.adapters.onebot.v11.exception import ActionFailed

import uuid
import time

__plugin_meta__ = PluginMetadata(
    name="games",
    description="",
    usage="",
    config=Config,
)

get_driver().on_startup(init_redis)
global_config = get_driver().config
config = Config(**global_config.dict())


from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.matcher import Matcher
from nonebot.typing import T_State

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.matcher import Matcher
from nonebot.typing import T_State

""" EXEMPT_COMMANDS = {"注册", "login", "help", "登录"}
COMMANDS = {'猜数字','菜单','help','排行榜','生涯','个人中心','我的排名'}

check_login_status = on_message(block=False)
@check_login_status.handle()
async def check_login_status_1(bot: Bot, event: Event):
        qq_id = event.get_user_id()
        user_id = get_id(qq_id) if not await is_user_logged_in(qq_id) else qq_id
        message_text = event.get_plaintext().strip()

        if not message_text:
            return

        command = message_text.split()[0]

        # 检查是否属于豁免指令，不属于则进行登录检查
        if command not in EXEMPT_COMMANDS and not await is_user_logged_in(user_id):
            if command in COMMANDS:
                check_login_status.block = True
                await check_login_status.finish('用户还未登录，请先登录')
        return """
        

#菜单
handle_menu = on_command("菜单", aliases={'menu','帮助'}, priority=5)

@handle_menu.handle()
async def menu(bot: Bot, event: Event, state: T_State):
    user_id = event.get_user_id()
    user_id = get_id(user_id)
    if not await is_user_logged_in(user_id):
        await handle_menu.send('你还没有登录哦！请先"登录"')
        return
    else:
        await handle_menu.finish(f'个人中心 游戏列表\n修改资料 退出')





handle_games = on_command('游戏列表',priority=5)
@handle_games.handle()
async def games():
    await handle_games.send('猜数字\n请输入游戏名进行游玩')




# 后面都是半成品
# 创建游戏
start_cmd = on_command("start", aliases={"liar", "liar's bar"}, priority=5)

@start_cmd.handle()
async def start_game_command(bot: Bot, event: Event):
    user_id = event.get_user_id()

    # 检查用户是否已经在其他房间中
    current_room = await find_player_room(user_id)
    if current_room:
       await start_cmd.finish(f"你已经在房间 {current_room} 中，请先退出当前房间再创建新的房间。") 
        
    
    # 自动生成唯一的房间 ID
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    
    # 将房间 ID 添加到 `game:rooms` 集合中，确保房间记录
    await redis.sadd("game:rooms", room_id)

    # 添加玩家到房间，并设置房主
    await add_player_to_room(room_id, user_id)
    await set_room_creator(room_id, user_id)    

    # 设置超时时间（10分钟后超时）
    timeout_timestamp = time.time() + 600
    await redis.set(f"game:room:{room_id}:timeout", timeout_timestamp)

    # 提示玩家房间创建成功，等待其他玩家加入
    await bot.send(event, f"房间 {room_id} 已创建，等待其他玩家加入。使用 join {room_id} 加入游戏")


#进入房间
join_cmd = on_command("join", aliases={'加入房间'})

@join_cmd.handle()
async def join_game_command(bot: Bot, event: Event):
    user_id = event.get_user_id()
    args = str(event.get_message()).strip().split()
    
    # 检查用户是否提供了房间号
    if len(args) == 1:
        await join_cmd.finish("请使用 join 房间号 来加入游戏")
    
    room_id = args[1]
    
    # 检查房间是否存在
    room_exists = await redis.sismember("game:rooms", room_id)
    if not room_exists:
        await join_cmd.finish(f"房间 {room_id} 不存在，请确认房间号。")
    
    # 检查是否已经在房间中
    if await is_player_in_room(room_id, user_id):
        await join_cmd.finish("你已经在该房间中。")
    
    # 检查用户是否已经在其他房间中
    current_room = await redis.get(f"user:{user_id}:room")
    if current_room:
        await join_cmd.finish(f"你已经在房间 {current_room} 中，请先退出当前房间再加入新的房间。")

    # 加入房间
    await add_player_to_room(room_id, user_id)
    players = list(await redis.smembers(f"game:room:{room_id}:players"))
    
    # 通知玩家加入成功
    await bot.send(event, f"你已加入房间 {room_id}，当前玩家数量：{len(players)}/3")
    
    # 如果房间内有 3 个玩家，启动游戏
    if len(players) == 3:
        game = LiarsGame(room_id, bot)
        message = await game.start_game()
        await bot.send_group_msg(group_id=event.group_id, message=message)

#退出房间
leave_cmd = on_command("leave", aliases={'退出游戏','退出房间'},priority=5)

@leave_cmd.handle()
async def leave_game_command(bot: Bot, event: Event):
    user_id = event.get_user_id()
    
    # 查找用户所在的房间
    room_id = await find_player_room(user_id)
    if not room_id:
        await bot.send(event, "你目前不在任何房间中。")
        return
    
    # 从房间中移除玩家
    await remove_player_from_room(room_id, user_id)
    
    # 检查房间内是否还有其他玩家
    players = list(await redis.smembers(f"game:room:{room_id}:players"))
    if not players:
        # 如果没有玩家了，移除房间记录
        await redis.srem("game:rooms", room_id)
        await redis.delete(f"game:room:{room_id}:players")
        await redis.delete(f"game:room:{room_id}:status")
        await bot.send(event, f"你已退出房间 {room_id}，房间已解散。")
    else:
        await bot.send(event, f"你已退出房间 {room_id}。")




scheduler = require("nonebot_plugin_apscheduler").scheduler

@scheduler.scheduled_job("interval", minutes=1)
async def clean_expired_rooms():
    room_ids = await redis.smembers("game:rooms")
    current_time = time.time()
    
    for room_id in room_ids:
        # 检查每个房间的超时时间
        timeout = await redis.get(f"game:room:{room_id}:timeout")
        if timeout and float(timeout) < current_time:
            # 如果超时，移除房间
            print(f"房间 {room_id} 已超时，正在删除...")
            await remove_room(room_id)

async def remove_room(room_id):
    # 删除 Redis 中与房间相关的所有数据
    await redis.srem("game:rooms", room_id)
    await redis.delete(f"game:room:{room_id}:players")
    await redis.delete(f"game:room:{room_id}:timeout")
    await redis.delete(f"game:room:{room_id}:status")
    print(f"房间 {room_id} 已成功清理。")