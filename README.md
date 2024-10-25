# StudentsOnline

## 项目概述
StudentsOnline 是一个后端项目，作为学生在线培训的最终考核作业。项目实现了用户登录、个人信息管理和简单的小游戏功能，旨在提供基本的用户交互和数据管理。未来计划迁移到 FastAPI 以支持更丰富的 HTTP API 响应。

## 技术栈
- **语言**: Python
- **框架**: NoneBot2
- **协议**: OneBot V11
- **数据库**: MySQL
- **缓存**: Redis (用于管理用户状态)

## 功能说明
1. **用户系统**
   - 用户可以注册、登录、查阅和修改个人信息。
   - 密码加密存储，确保用户信息安全。

2. **小游戏**
   - 提供多个简单的小游戏，例如：
     - **猜数字**：在 1-100 范围内随机生成一个数字，玩家需在一定次数内猜中。
     - 用户通过选择游戏并进行操作来游玩。

3. **待办功能**
   - [x] 实现用户系统和基础小游戏功能
   - [x] 完成数据统计和排行榜
   - [ ] 实现liar's bar搭建
   - [ ] 迁移到 FastAPI，实现 HTTP API 响应

## 目录结构
```
studentsonline/
│
├── src/                # 主应用目录
│   └── plugins/        # NoneBot2 插件目录
│       └── games/      # 小游戏插件
│           ├── __init__.py       # 插件初始化
│           ├── config.py         # 插件配置文件
│           ├── connsql.py        # 数据库连接和操作
│           ├── games/            # 游戏逻辑目录
│           │   └── guess_number.py # 猜数字游戏实现
│           ├── passwd.py         # 用户密码管理
│           └── status.py         # 用户状态管理
│
├── pyproject.toml      # 项目配置文件
├── README.md           # 项目说明文件
```

- 当前仓库存放的是```src/plugins/games/```的内容 并且```liar's bar```尚未完工故暂不添加入目录

## 安装与运行
请参考 [NoneBot2 官方文档](https://v2.nonebot.dev/) 进行安装和运行配置。

## 贡献
欢迎提出 Issue 或 Pull Request 以帮助改进项目。
