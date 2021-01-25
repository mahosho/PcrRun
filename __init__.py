from hoshino import Service, R
from hoshino.typing import *
from hoshino import Service, priv, util
from hoshino.util import DailyNumberLimiter, pic2b64, concat_pic, silence
#import sqlite3, os, random, asyncio
from nonebot import MessageSegment
from hoshino import Service
from hoshino.typing import CQEvent
from .util import *
#import random
#import heapq
#from . import runchara
#import copy
running_judger = RunningJudger()

sv = Service('pcr-run', enable_on_default=True)
    
@sv.on_prefix(('测试赛跑', '赛跑开始'))
async def Racetest(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能开启赛跑', at_sender=True)
    if running_judger.get_on_off_status(ev.group_id):
            await bot.send(ev, "此轮赛跑还没结束，请勿重复使用指令。")
            return
    running_judger.turn_on(ev.group_id)
   
    #用于记录各赛道上角色位置，第i号角色记录在position[i-1]上
    position = [ROADLENGTH for x in range(0,NUMBER)]
    #同理，记录沉默，暂停，以及必放ub标记情况
    silence = [0 for x in range(0,NUMBER)]
    pause = [0 for x in range(0,NUMBER)]
    ub = [0 for x in range(0,NUMBER)]
           
    Race_list = chara_select()
    msg = '兰德索尔赛跑即将开始！\n下面为您介绍参赛选手：'
    await bot.send(ev, msg)
    await asyncio.sleep(ONE_TURN_TIME)
    #介绍选手，开始支持环节
    
    
    msg = introduce_race(Race_list)
    await bot.send(ev, msg)
    await asyncio.sleep(SUPPORT_TIME)
    running_judger.turn_off(ev.group_id)
    #支持环节结束
    msg = '支持环节结束，下面赛跑正式开始。'
    await bot.send(ev, msg)    
    await asyncio.sleep(ONE_TURN_TIME)    
    
 
    race_init(position,silence,pause,ub)
    msg = '运动员们已经就绪！\n'
    msg += print_race(Race_list,position)
    await bot.send(ev, msg)
   
    gameend = 0
    i = 1
    while gameend == 0:
        await asyncio.sleep(ONE_TURN_TIME)
        msg = f'第{i}轮跑步:\n'
        one_turn_run(pause,position,Race_list)
        msg += print_race(Race_list,position)
        await bot.send(ev, msg)
        check = check_game(position)
        if check[0]!=0:
            break
        if running_judger.get_on_shut_down_status(ev.group_id):
            running_judger.un_shut_down(ev.group_id)
            running_judger.clean_support(ev.group_id)
            await bot.finish(ev,'已停止赛跑')            
        await asyncio.sleep(ONE_TURN_TIME)
        skillmsg = "技能发动阶段:\n"
        skillmsg += skill_race(Race_list,position,silence,pause,ub)
        await bot.send(ev, skillmsg)
        await asyncio.sleep(ONE_TURN_TIME)
        msg = f'技能发动结果:\n'
        msg += print_race(Race_list,position)
        await bot.send(ev, msg)

        i+=1
        check = check_game(position)
        gameend = check[0]
    winner = check[1]
    winmsg = ""
    for id in winner:
        winmsg += str(id)
        winmsg += "\n"
    msg = f'胜利者为:\n{winmsg}'
    score_counter = ScoreCounter()
    await bot.send(ev, msg)
    gid = ev.group_id
    support = running_judger.get_support(gid)
    winuid = []
    supportmsg = '积分结算:\n'
    if support!=0:
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            if support_id in winner:
                winuid.append(uid)
                winscore = support_score*2
                score_counter._add_score(gid, uid ,winscore)
                supportmsg += f'[CQ:at,qq={uid}]+{winscore}积分\n'     
            else:
                score_counter._reduce_score(gid, uid ,support_score)
                supportmsg += f'[CQ:at,qq={uid}]-{support_score}积分\n'
    await bot.send(ev, supportmsg)  
    running_judger.set_support(ev.group_id) 
    running_judger.turn_off(ev.group_id) 
        
@sv.on_rex(r'^(\d+)号(\d+)(积分|分)$') 
async def on_input_score(bot, ev: CQEvent):
    try:
        if running_judger.get_on_off_status(ev.group_id):
            gid = ev.group_id
            uid = ev.user_id
            
            match = ev['match']
            select_id = int(match.group(1))
            input_score = int(match.group(2))
            print(select_id,input_score)
            score_counter = ScoreCounter()
            #若下注该群下注字典不存在则创建
            if running_judger.get_support(gid) == 0:
                running_judger.set_support(gid)
            support = running_judger.get_support(gid)
            #检查是否重复下注
            if uid in support:
                msg = '您已经支持过了。'
                await bot.send(ev, msg, at_sender=True)
                return
            #检查积分是否足够下注
            if score_counter._judge_score(gid, uid ,input_score) == 0:
                msg = '您的积分不足。'
                await bot.send(ev, msg, at_sender=True)
                return
            else :
                running_judger.add_support(gid,uid,select_id,input_score)
                msg = f'支持{select_id}号成功。'
                await bot.send(ev, msg, at_sender=True)                
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))            
            
                
                
@sv.on_prefix(('领赛跑积分','签到'))
async def add_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter()
        gid = ev.group_id
        uid = ev.user_id
        
        current_score = score_counter._get_score(gid, uid)
        if current_score == 0:
            score_counter._add_score(gid, uid ,50)
            msg = '您已领取50积分'
            await bot.send(ev, msg, at_sender=True)
            return
        else:     
            msg = '积分为0才能领取哦。'
            await bot.send(ev, msg, at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))         
@sv.on_prefix(('查询积分','查赛跑积分','积分查询'))
async def get_score(bot, ev: CQEvent):
    try:
        score_counter = ScoreCounter()
        gid = ev.group_id
        uid = ev.user_id
        
        current_score = score_counter._get_score(gid, uid)
        msg = f'您的积分为{current_score}'
        await bot.send(ev, msg, at_sender=True)
        return
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e)) 
        
@sv.on_prefix(('充值'))
async def _add_score(bot,  ev:CQEvent):
    if ev.user_id not in bot.config.SUPERUSERS:
        await bot.finish(ev,'只有维护组才能充值')
    score_counter = ScoreCounter()
    gid = ev.group_id
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            score_counter._add_score(gid, uid ,50)
            count += 1
    await bot.send(ev, f"已为{count}位用户充值完毕！谢谢惠顾～")
    
@sv.on_prefix(('停止赛跑'))
async def stop_run(bot, ev:CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能停止赛跑', at_sender=True)
    running_judger.shut_down(ev.group_id)
        
    

    
        
        
        
        
   
    
    
    
    
    
    
    
    
    





    