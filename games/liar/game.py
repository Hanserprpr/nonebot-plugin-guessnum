from .redis_utils import *
from nonebot.adapters.onebot.v11 import Bot

class LiarsGame:
    def __init__(self, room_id, bot: Bot):
        self.room_id = room_id
        self.bot = bot

    async def start_game(self):
        players = list(await redis.smembers(f"game:room:{self.room_id}:players"))
        if len(players) != 3:
            return "游戏需要 3 名玩家，请等待其他玩家加入。"
        
        await redis.set(f"game:room:{self.room_id}:status", "active")
        await redis.set(f"game:room:{self.room_id}:turn", players[0])
        
        await initialize_deck(self.room_id)
        for player in players:
            cards = await deal_cards(player, self.room_id, 5)
            await self.bot.send_private_msg(user_id=player, message=f"你的手牌为：{', '.join(cards)}")
        
        return "游戏开始！请各位玩家查看私聊获得的手牌。"

    async def player_action(self, player_id, action, cards=None):
        if not await is_player_in_room(self.room_id, player_id):
            return "你不在游戏中，请先加入。"
        
        current_turn = await get_current_turn(self.room_id)
        if player_id != current_turn:
            return "现在还没轮到你，请等待其他玩家的操作。"
        
        if action == "出牌":
            player_hand = await get_player_hand(player_id)
            
            # 解析和验证出牌
            card_types = {}
            for card in cards:
                if card not in player_hand:
                    return "你的手牌中没有这些牌，请重新选择。"
                card_name = card[:-1]  # 获取卡牌类型（如 A, K, J）
                card_types[card_name] = card_types.get(card_name, 0) + 1
            
            # 从手牌中移除出牌
            await remove_cards_from_player_hand(player_id, cards)
            await save_last_action(self.room_id, player_id, cards)
            
            # 构建出牌信息
            card_descriptions = [f"{count} 张 {card}" for card, count in card_types.items()]
            result = f"玩家 {player_id} 出了 {', '.join(card_descriptions)}。"
        
        elif action == "质疑":
            last_action = await get_last_action(self.room_id)
            if not last_action:
                return "没有可质疑的出牌。"
            
            previous_player = last_action['player_id']
            previous_cards = last_action['cards'].split(",")
            result = await self.verify_bluff(player_id, previous_player, previous_cards)
        
        else:
            return "未知的操作。"
        
        await next_turn(self.room_id)
        return result

    async def verify_bluff(self, challenger, previous_player, previous_cards):
        player_hand = await get_player_hand(previous_player)
        is_lying = any(card not in player_hand for card in previous_cards)
        if is_lying:
            punishment = await self.russian_roulette(previous_player)
            return f"质疑成功！玩家 {previous_player} 被揭穿谎言。{punishment}"
        else:
            punishment = await self.russian_roulette(challenger)
            return f"质疑失败！玩家 {previous_player} 的出牌属实。{challenger} {punishment}"

    async def russian_roulette(self, player_id):
        import random
        
        # 获取当前未中弹的计数
        not_shot_count = await redis.get(f"game:room:{self.room_id}:not_shot_count") or 0
        not_shot_count = int(not_shot_count)
        
        # 基础中弹概率 1/6，随着未中弹次数增加，提高中弹概率
        base_chance = 1/6
        # 提高中弹的概率，最多增加到 100%
        chance = min(base_chance + (not_shot_count * 0.1), 1.0)

        # 判断是否中弹
        if random.random() < chance:
            await redis.srem(f"game:room:{self.room_id}:players", player_id)
            await redis.set(f"game:room:{self.room_id}:not_shot_count", 0)  # 重置计数器
            return "不幸中弹，被踢出游戏。"
        else:
            # 增加未中弹的计数
            await redis.set(f"game:room:{self.room_id}:not_shot_count", not_shot_count + 1)
            return "幸运地逃过一劫。"

