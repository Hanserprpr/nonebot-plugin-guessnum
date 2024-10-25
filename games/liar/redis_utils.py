import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379"
redis = aioredis.from_url(REDIS_URL)

# 存储玩家状态
async def add_player_to_room(room_id, player_id):
    await redis.sadd(f"game:room:{room_id}:players", player_id)

async def is_player_in_room(room_id, player_id):
    return await redis.sismember(f"game:room:{room_id}:players", player_id)

async def set_room_creator(room_id, creator_id):
    await redis.set(f"game:room:{room_id}:creator", creator_id)

async def get_room_creator(room_id):
    return await redis.get(f"game:room:{room_id}:creator")

# 管理手牌
async def add_cards_to_player_hand(player_id, cards):
    await redis.sadd(f"player:{player_id}:hand", *cards)

async def remove_cards_from_player_hand(player_id, cards):
    for card in cards:
        await redis.srem(f"player:{player_id}:hand", card)

async def get_player_hand(player_id):
    return await redis.smembers(f"player:{player_id}:hand")

# 初始化牌堆
async def initialize_deck(room_id):
    cards = ["Joker"] * 6 + ["Queen"] * 6 + ["King"] * 2 + ["Ace"] * 6
    await redis.delete(f"game:room:{room_id}:deck")
    await redis.sadd(f"game:room:{room_id}:deck", *cards)

async def deal_cards(player_id, room_id, num_cards=5):
    player_hand = []
    for _ in range(num_cards):
        card = await redis.spop(f"game:room:{room_id}:deck")
        if card:
            player_hand.append(card)
            await add_cards_to_player_hand(player_id, [card])
    return player_hand

# 记录出牌
async def save_last_action(room_id, player_id, cards):
    await redis.hset(f"game:room:{room_id}:last_action", mapping={"player_id": player_id, "cards": ",".join(cards)})

async def get_last_action(room_id):
    return await redis.hgetall(f"game:room:{room_id}:last_action")

async def get_current_turn(room_id):
    return await redis.get(f"game:room:{room_id}:turn")

async def next_turn(room_id):
    players = list(await redis.smembers(f"game:room:{room_id}:players"))
    current_player = await get_current_turn(room_id)
    if current_player in players:
        current_index = players.index(current_player)
        next_index = (current_index + 1) % len(players)
        await redis.set(f"game:room:{room_id}:turn", players[next_index])

# 增加玩家到房间
async def add_player_to_room(room_id, player_id):
    await redis.sadd(f"game:room:{room_id}:players", player_id)

# 检查玩家是否在房间中
async def is_player_in_room(room_id, player_id):
    return await redis.sismember(f"game:room:{room_id}:players", player_id)

# 获取当前轮次玩家
async def get_current_turn(room_id):
    return await redis.get(f"game:room:{room_id}:turn")

# 切换到下一个玩家
async def next_turn(room_id):
    players = list(await redis.smembers(f"game:room:{room_id}:players"))
    current_player = await get_current_turn(room_id)
    if current_player in players:
        current_index = players.index(current_player)
        next_index = (current_index + 1) % len(players)
        await redis.set(f"game:room:{room_id}:turn", players[next_index])


# 从房间中移除玩家
async def remove_player_from_room(room_id, player_id):
    await redis.srem(f"game:room:{room_id}:players", player_id)

# 查找玩家所在的房间
async def find_player_room(player_id):
    room_ids = await redis.smembers("game:rooms")
    room_ids = [room_id.decode('utf-8') if isinstance(room_id, bytes) else room_id for room_id in room_ids]
    for room_id in room_ids:
        if await is_player_in_room(room_id, player_id):
            return room_id
    return None
