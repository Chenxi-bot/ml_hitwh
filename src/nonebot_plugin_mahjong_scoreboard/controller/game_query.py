from datetime import datetime, date, timedelta, time

from nonebot import on_command, Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher

from .interceptor import handle_error
from .mapper.game_mapper import map_game
from .utils.dep import GroupDep, UnaryArg, UserDep
from .utils.general_handlers import require_store_command_args, require_platform_group_id, require_platform_user_id
from .utils.parse import parse_int_or_error
from ..errors import BadRequestError
from ..model import Group, User
from ..platform.get_user_nickname import get_user_nickname
from ..platform.send_messages import send_msgs
from ..service import game_service
from ..service.game_service import get_games

# =============== 查询对局 ===============
query_by_code_matcher = on_command("查询对局", aliases={"对局"}, priority=5)

require_store_command_args(query_by_code_matcher)
require_platform_group_id(query_by_code_matcher)


@query_by_code_matcher.handle()
@handle_error()
async def query_by_code(matcher: Matcher, group: Group = GroupDep(),
                        game_code=UnaryArg(lookup_matcher_state=True, parser=lambda x: parse_int_or_error(x, '对局编号'))):
    if game_code is None:
        raise BadRequestError("请指定对局编号")

    game = await game_service.get_game(game_code, group.id)
    if game is None:
        raise BadRequestError("未找到指定对局")

    msg = await map_game(game, detailed=True)
    await matcher.send(msg)


# ========== 个人最近对局 ==========
query_user_recent_games_matcher = on_command("个人最近对局", priority=5)

require_store_command_args(query_user_recent_games_matcher)
require_platform_group_id(query_user_recent_games_matcher)
require_platform_user_id(query_user_recent_games_matcher)


@query_user_recent_games_matcher.handle()
@handle_error()
async def query_user_recent_games(bot: Bot, event: Event, matcher: Matcher,
                                  group: Group = GroupDep(),
                                  user: User = UserDep(lookup_matcher_state=True)):
    end_time = datetime.combine(date.today() + timedelta(days=1), time())
    start_time = datetime.combine(end_time - timedelta(days=7), time())

    games = await get_games(group.id, user.id, limit=5, reverse_order=True, time_span=(start_time, end_time))
    if len(games) != 0:
        msgs = []
        msgs.append(f"以下是[{await get_user_nickname(bot, platform_user_id, group.platform_group_id)}]"
                    f"的最近对局：")

        for g in games:
            msgs.append(await map_game(g, detailed=True))

        await send_msgs(bot, event, msgs)
    else:
        await matcher.send("你还没有进行过对局")


# ========== 群最近对局 ==========
query_group_recent_games_matcher = on_command("群最近对局", aliases={"最近对局"}, priority=5)

require_store_command_args(query_group_recent_games_matcher)
require_platform_group_id(query_group_recent_games_matcher)


@query_group_recent_games_matcher.handle()
@handle_error()
async def query_group_recent_games(bot: Bot, event: Event, matcher: Matcher, group=GroupDep()):
    end_time = datetime.combine(date.today() + timedelta(days=1), time())
    start_time = datetime.combine(end_time - timedelta(days=7), time())

    games = await get_games(group.id, limit=5, reverse_order=True, time_span=(start_time, end_time))
    if len(games) != 0:
        msgs = []
        msgs.append(f"以下是本群的最近对局：")

        for g in games:
            msgs.append(await map_game(g, detailed=True))

        await send_msgs(bot, event, msgs)
    else:
        await matcher.send("本群还没有进行过对局")


# ========== 个人未完成对局 ==========
query_user_uncompleted_games_matcher = on_command("个人未完成对局", priority=5)

require_store_command_args(query_user_uncompleted_games_matcher)
require_platform_group_id(query_user_uncompleted_games_matcher)
require_platform_user_id(query_user_uncompleted_games_matcher)


@query_user_uncompleted_games_matcher.handle()
@handle_error()
async def query_user_uncompleted_games(bot: Bot, event: Event, matcher: Matcher,
                                       group=GroupDep(),
                                       user: User = UserDep(lookup_matcher_state=True)):
    games = await get_games(group.id, user.id, uncompleted_only=True, limit=10, reverse_order=True)
    if len(games) != 0:
        msgs = []
        msgs.append(f"以下是[{await get_user_nickname(bot, user.platform_user_id, group.platform_group_id)}]"
                    f"的未完成对局：")

        for g in games:
            msgs.append(await map_game(g, detailed=True))

        await send_msgs(bot, event, msgs)
    else:
        await matcher.send("你还没有未完成的对局")


# ========== 群未完成对局 ==========
query_group_uncompleted_games_matcher = on_command("群未完成对局", aliases={"未完成对局"}, priority=5)

require_store_command_args(query_group_uncompleted_games_matcher)
require_platform_group_id(query_group_uncompleted_games_matcher)


@query_group_uncompleted_games_matcher.handle()
@handle_error()
async def query_group_uncompleted_games(bot: Bot, event: Event, matcher: Matcher, group=GroupDep()):
    games = await get_games(group.id, uncompleted_only=True, limit=10, reverse_order=True)
    if len(games) != 0:
        msgs = []
        msgs.append(f"以下是本群的未完成对局：")

        for g in games:
            msgs.append(await map_game(g, detailed=True))

        await send_msgs(bot, event, msgs)
    else:
        await matcher.send("本群还没有未完成的对局")
