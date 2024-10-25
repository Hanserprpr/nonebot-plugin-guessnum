import random
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.typing import T_State
from ..connsql import save_game_attempt, update_user_stats, fetch_game_history, fetch_leaderboard, search_name, get_user_rank
from ..status import extend_user_session, get_user_id_from_qq

# 猜数字
guess_game = on_command("猜数字", aliases={"开始猜数字", "猜数"}, priority=5)

@guess_game.handle()
async def start_game(bot: Bot, event: Event, state: T_State):
    qq_id = event.get_user_id()
    user_id = await get_user_id_from_qq(qq_id)
    if not user_id:
        await guess_game.finish('你还没有登录哦！请先"登录"')
        return

    # 自动续期
    await extend_user_session(user_id)


    random_number = random.randint(1, 100)
    state["target_number"] = random_number
    state["attempts"] = 0
    state["user_id"] = user_id  # 使用从 Redis 获取到的 user ID. tnnd user_id 和qq_id怎么混在一起了
    await guess_game.send("欢迎来到猜数字游戏！我已经想好了 1 到 100 之间的一个数字，请开始猜吧！")

# 处理用户的猜测
@guess_game.got("guess")
async def handle_guess(bot: Bot, event: Event, state: T_State):
    user_guess = str(event.get_message()).strip()
    
    try:
        # 将用户的输入转换为整数
        guess_number = int(user_guess)
    except ValueError:
        # 如果输入无法转换为整数
        await guess_game.reject("请输入一个有效的数字！")

    # 读取随机生成的目标数字
    target_number = state["target_number"]
    state["attempts"] += 1

    if guess_number < target_number:
        await guess_game.reject("太小了，请再试一次！")
    elif guess_number > target_number:
        await guess_game.reject("太大了，请再试一次！")
    else:
        attempts = state["attempts"]
        user_id = state["user_id"]
    
        score = max(100 - (attempts * 10), 0)

        # 保存游戏结果
        save_game_attempt(user_id=user_id, game_name="guess_number", score=score, attempts=attempts)

        # 更新统计数据
        update_user_stats(user_id=user_id, game_name="guess_number", score=score, attempts=attempts)

        await guess_game.finish(f"恭喜你猜对了！答案是 {target_number}。你总共猜了 {attempts} 次。")

# 创建查询历史记录的命令
history_command = on_command("生涯", aliases={"历史记录", "查看游戏历史"}, priority=5)

@history_command.handle()
async def show_history(bot: Bot, event: Event):
    qq_id = event.get_user_id()
    user_id = await get_user_id_from_qq(qq_id)
    if not user_id:
        await history_command.finish('你还没有登录哦！请先"登录"')
        return

    # 自动续期
    await extend_user_session(user_id)

    # 从数据库获取用户的游戏历史记录
    history = fetch_game_history(user_id, game_name="guess_number")

    if not history:
        await history_command.finish("你还没有任何游戏记录！")
    
    # 构建显示历史记录的消息
    history_message = "你的历史游戏记录：\n"
    for record in history:
        attempts = record["attempts"]
        score = record["score"]
        played_at = record["played_at"].strftime("%Y-%m-%d %H:%M:%S")
        history_message += f"日期: {played_at}, 分数: {score}, 猜测次数: {attempts}\n"
    
    await history_command.finish(history_message)

leaderboard_command = on_command("排行榜", aliases={"查看排行榜", "游戏排行"}, priority=5)

@leaderboard_command.handle()
async def show_leaderboard(bot: Bot, event: Event):
    # 从数据库获取排行榜
    leaderboard = fetch_leaderboard(game_name="guess_number")
    qq_id = event.get_user_id()
    user_id = await get_user_id_from_qq(qq_id)
    if not leaderboard:
        await leaderboard_command.finish("当前没有任何游戏数据。")
    
    # 自动续期
    await extend_user_session(user_id)

    # 构建显示排行榜的消息
    leaderboard_message = "猜数字游戏排行榜：\n"
    rank = 1
    for entry in leaderboard:
        uid = entry["user_id"]
        score = entry["average_score"]
        name = search_name(user_id=uid)  # 根据 user_id 获取用户名
        leaderboard_message += f"{rank}. 用户 {name} (ID: {uid}) - 平均分: {score}\n"
        rank += 1

    # 获取当前用户的排名
    current_user_rank = get_user_rank(user_id, game_name="guess_number")
    if current_user_rank:
        user_rank = current_user_rank["ranking"]
        user_score = current_user_rank["average_score"]
        leaderboard_message += f"\n你的当前排名:第 {user_rank} 名，平均分: {user_score}"

    await leaderboard_command.finish(leaderboard_message)

rank_command = on_command("我的排名", aliases={"查看排名", "查询排名"}, priority=5)

#用户当前排名
@rank_command.handle()
async def show_user_rank(bot: Bot, event: Event):
    qq_id = event.get_user_id()
    user_id = await get_user_id_from_qq(qq_id)
    if not user_id:
        await rank_command.finish("你还没有参与任何游戏，无法显示排名。")

    # 自动续期
    await extend_user_session(user_id)
    
    user_rank = get_user_rank(user_id, game_name="guess_number")
    
    if not user_rank:
        await rank_command.finish("你还没有参与任何游戏，无法显示排名。")
    
    rank = user_rank["ranking"]
    score = user_rank["average_score"]
    await rank_command.finish(f"你的当前排名是第 {rank} 名，平均分数为 {score}。")
