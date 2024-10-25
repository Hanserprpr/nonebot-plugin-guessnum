from nonebot import get_driver, on_command, logger, get_bot,on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
from .config import Config
from .connsql import search_name, get_me, signup, update_last_login, update_user_info, search_passwd, search_id, get_id
from .passwd import decrypt, encrypt
from .status import set_user_logged_in, is_user_logged_in, init_redis, set_user_logged_out
from nonebot.adapters.onebot.v11 import MessageEvent
import re
import asyncio


# 保存待确认的 QQ 列表
pending_confirmations = {}

# 定义消息监听器，用于确认 QQ
confirm_listener = on_message(priority=5)

@confirm_listener.handle()
async def handle_confirmation(event: MessageEvent):
    qq = event.get_user_id()
    message = str(event.get_message()).strip()
    
    # 检查待确认的 QQ 并且消息为 "1"
    if qq in pending_confirmations and message == "1":
        # 完成 QQ 验证，获取并移除记录
        session_info = pending_confirmations.pop(qq)
        state = session_info["state"]
        
        # 获取 bot 实例并发送私聊消息
        bot = get_bot()
        await bot.send_private_msg(user_id=qq, message=f"QQ 号 {qq} 验证成功")
        
        # 完成注册
        await complete_signup(state)

# 主注册命令
handle_signup = on_command("注册", aliases={"signup"}, priority=5)
@handle_signup.handle()
async def if_logged_in(bot: Bot, event: Event, state: T_State):
    qq_id = event.get_user_id()
    user_id = get_id(qq_id) if not await is_user_logged_in(qq_id) else qq_id
    print(user_id)
    if await is_user_logged_in(user_id):
        print(await is_user_logged_in(user_id))
        await handle_signup.finish('别急,你还没退出登录')
@handle_signup.got('name', prompt='请输入你的用户名.要使用当前QQ昵称,请输入"1"')
async def ask_for_email(bot: Bot, event: Event, state: T_State):

    name = str(event.get_message()).strip()
    if name == "1":
        name = event.sender.nickname
    if not search_id(name=name):
        state['name'] = name
    else:
        await handle_signup.reject('该用户名已被使用,请输入新用户名')

@handle_signup.got('email', prompt='请输入你的邮箱.要使用当前账号QQ邮箱,请输入"1"')
async def ask_for_sex(bot: Bot, event: Event, state: T_State):
    email = str(event.get_message()).strip()
    if email == "1":
        email = str(event.get_user_id()) + "@qq.com"

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await handle_signup.reject('邮箱格式不正确，请重新输入有效的邮箱:')

    if not search_id(email=email):
        state['email'] = email
    else:
        await handle_signup.reject('该邮箱已被使用,请输入新邮箱')

@handle_signup.got('sex', prompt='请输入你的性别 (男/女):')
async def ask_for_passwd(bot: Bot, event: Event, state: T_State):
    sex = str(event.get_message()).strip()
    if sex == '男':
        sex = 'M'
    elif sex == '女':
        sex = 'F'
    else:
        sex = 'Other'
    state['sex'] = sex

@handle_signup.got('passwd', prompt='请输入你的密码:')
async def ask_for_qq(bot: Bot, event: Event, state: T_State):
    passwd = str(event.get_message()).strip()
    passwd = encrypt(passwd)
    state['passwd'] = passwd

@handle_signup.got('QQ', prompt='请输入你的QQ:\n使用当前QQ,请输入"1"')
async def finalize_signup(bot: Bot, event: Event, state: T_State):
    qq = str(event.get_message()).strip()
    recent_qq = event.get_user_id()

    if qq == "1":
        qq = recent_qq

    if not search_id(QQ=qq):
        state['QQ'] = qq
    else:
        await handle_signup.reject('该QQ已经注册过,请更换QQ号。')

    if qq != recent_qq:
        state['expected_qq'] = qq
        # 将状态存储到 pending_confirmations 中
        pending_confirmations[qq] = {"session_id": event.get_session_id(), "state": state}
        await handle_signup.send(f'你输入的 QQ 号 {qq} 与当前会话的 QQ {recent_qq} 不匹配，请使用 {qq} 向 bot 发送 "1" 来验证身份。')
        return  # 等待确认完成后再继续

    await complete_signup(state)

async def complete_signup(state: T_State):
    name = state.get('name')
    email = state.get('email')
    sex = state.get('sex')
    passwd = state.get('passwd')
    qq = str(state.get('QQ'))

    await handle_signup.send(f'注册信息:\n用户名: {name}\n邮箱: {email}\n性别: {sex}\n密码: 为保护用户隐私暂不显示\nQQ: {qq}\n你可以在稍后修改这些信息')
    await handle_signup.send(f'欢迎使用 请发送“菜单”来获取帮助')

    signup(name, email, sex, passwd, qq)


# 定义 "登录" 命令处理
handle_login = on_command("登录", aliases={'login', '登入'}, priority=5)

@handle_login.handle()
async def login(bot: Bot, event: MessageEvent, state: T_State):
    QQ_id = event.get_user_id()
    if await is_user_logged_in(QQ_id):
        await handle_login.finish('你已经登陆过了,请勿重复登录')
    await handle_login.send('请输入你的用户名或邮箱进行登录（输入 "退出" 以取消）,输入"1"使用当前QQ自动登录')

@handle_login.got("identifier")
async def get_user(bot: Bot, event: MessageEvent, state: T_State):
    try:
        identifier = await asyncio.wait_for(
            wait_for_user_input(event), LOGIN_TIMEOUT)

        # 检查用户是否输入了 "退出" 指令
        if identifier.strip().lower() in ["退出", "exit"]:
            await handle_login.finish("已取消登录。")
        if identifier == "1":
            QQ_id = event.get_user_id()
            user_id = search_id(QQ=QQ_id)  # 根据 QQ_id 获取 user_id
            name = search_name(QQ=QQ_id)  # 获取用户名
            if not name or not user_id:
                await handle_login.finish("未找到与当前 QQ 关联的用户，请先注册。")
            else:
                await set_user_logged_in(QQ_id, user_id)  # 设置用户登录状态并续期
                update_last_login(user_id = user_id)  # 更新登录时间
                await handle_login.finish(f'{name}登录成功')


        state["identifier"] = identifier.strip()
        await handle_login.send('请输入密码（输入 "退出" 以取消）')
    except asyncio.TimeoutError:
        await handle_login.finish("登录超时，已自动退出。")


# 超时时间设置（单位：秒）
LOGIN_TIMEOUT = 60

@handle_login.got("passwd")
async def get_passwd(bot: Bot, event: MessageEvent, state: T_State):
    try:
        # 设置超时等待
        passwd = await asyncio.wait_for(async_input(event), LOGIN_TIMEOUT)

        # 主动退出
        if passwd.strip().lower() == 'exit':
            await handle_login.finish('已退出登录流程')


        identifier = state.get("identifier")

        # 密码验证
        result = await decrypt(passwd, identifier) 
        if result:
            QQ_id = event.get_user_id()
            user_id = search_id(QQ=QQ_id)  # 获取对应的 user_id
            await set_user_logged_in(QQ_id, user_id)  # 设置用户登录状态
            name = search_name(user_id)  # 获取用户名
            update_last_login(user_id=user_id)  # 更新登录时间
            await handle_login.send(f'{name}登录成功')
        else:
            await handle_login.reject('账号或密码错误, 请重新输入密码,输入exit退出')
    except asyncio.TimeoutError:
        # 处理超时情况
        await handle_login.finish("登录超时，已自动退出。")

async def async_input(event: MessageEvent):
    return str(event.get_message()).strip()

async def wait_for_user_input(event: MessageEvent):
    """等待用户输入信息，提供给 asyncio.wait_for 使用"""
    return str(event.get_message())


#退出登录
handle_log_out = on_command('退出', aliases={'登出',"log out"}, priority=5)
@handle_log_out.handle()
async def log_out(bot: Bot, event: Event, state: T_State):
    QQ_id = event.get_user_id()
    user_id = get_id(QQ_id)
    if await is_user_logged_in(user_id):
        await set_user_logged_out(user_id)
        name = search_name(QQ=QQ_id)
        await handle_log_out.finish(f'{name}已登出')
    else:
        await handle_log_out.finish('你还没有登录哦！请先"登录"')


#个人中心
handle_getme = on_command('个人中心', priority=5)
@handle_getme.handle()
async def me(bot: Bot, event: Event, state: T_State):
    qq_id = event.get_user_id()
    user_id = get_id(qq_id)
    if not await is_user_logged_in(user_id):
        await handle_getme.send('你还没有登录哦！请先"登录"')
        return
    else:
        result = get_me(user_id=user_id)
        await handle_getme.finish(str(result))


# 编辑用户资料
handle_edit = on_command('编辑', aliases={'修改资料', '修改个人资料'}, priority=5)

@handle_edit.handle()
async def edit(bot: Bot, event: Event, state: T_State):
    user_id = event.get_user_id()
    if not await is_user_logged_in(user_id):
        await handle_edit.finish('你还没有登录哦！请先"登录"')
        return
    await handle_edit.send('请输入编辑条目：用户名、密码、性别\n一次仅能更改一项.示例:密码')
    title = str(event.get_message()).strip()
    
@handle_edit.got("title")
async def editing(bot: Bot, event: Event, state: T_State):
    title = str(event.get_message()).strip()
    if title == '用户名':
        state['edit_field'] = 'name'
        await handle_edit.send('请输入新的用户名：')
    elif title == '密码':
        state['edit_field'] = 'passwd'
        await handle_edit.send('请输入旧的密码进行验证：')
    elif title == '性别':
        state['edit_field'] = 'sex'
        await handle_edit.send('请输入新的性别（男/女/其他）：')
    else:
        await handle_edit.finish('无效的编辑项，请重新输入有效的编辑条目。当前可编辑条目:用户名、密码、性别\n用户名')


@handle_edit.got('new_value')
async def edit_value(bot: Bot, event: Event, state: T_State):
    new_value = str(event.get_message()).strip()
    edit_field = state['edit_field']
    qq = str(event.user_id) 

    # 处理不同的编辑项
    if edit_field == 'name':
        # 检查用户名是否有效
        if not search_id(name=new_value):
            if len(new_value) < 3:
                await handle_edit.reject('用户名长度过短，请重新输入一个有效的用户名：')
            update_user_info(qq=qq, name=new_value)
            await handle_edit.finish(f'用户名已更新为：{new_value}')
        else:
            await handle_edit.reject('该用户名已被使用,请输入新用户名')
        
    
    elif edit_field == 'passwd':
        # 第一次进入密码修改流程验证旧密码
        id = search_name(qq)
        if 'old_passwd' not in state:
            if decrypt(new_value, id):
                state['old_passwd'] = "verified"
                await handle_edit.reject('旧密码验证成功，请输入新密码：')

            else:
                await handle_edit.reject('旧密码验证失败，请重新输入正确的旧密码：')
        else:
            new_encrypted_passwd = encrypt(new_value)
            update_user_info(passwd=new_encrypted_passwd, qq=qq)
            await handle_edit.finish('密码已成功更新。')

    elif edit_field == 'sex':
        if new_value not in ['男', '女', '其他']:
            await handle_edit.reject('性别无效，请重新输入（男/女/其他）：')
        sex_code = 'M' if new_value == '男' else 'F' if new_value == '女' else 'O'
        update_user_info(qq=qq, sex=sex_code)
        await handle_edit.finish(f'性别已更新为：{new_value}')