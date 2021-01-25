import sqlite3, os, random, asyncio
from . import runchara
import copy
import heapq

ROAD = '='
ROADLENGTH = 16
TOTAL_NUMBER = 7
NUMBER = 5
ONE_TURN_TIME = 3
SUPPORT_TIME = 30
DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
class RunningJudger:
    def __init__(self):
        self.on = {}
        self.support = {}
        self.stop = {}
    def set_support(self,gid):
        self.support[gid] = {}
    def get_support(self,gid):
        return self.support[gid] if self.support.get(gid) is not None else 0
    def add_support(self,gid,uid,id,score):
        self.support[gid][uid]=[id,score]
    def clean_support(self,gid):
        self.support[gid] = None
    def get_support_id(self,gid,uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][0]
        else :
            return 0
    def get_support_score(self,gid,uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][1]
        else :
            return 0
    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False
    def get_on_shut_down_status(self,gid):
        return self.stop[gid] if self.stop.get(gid) is not None else False
    def turn_on(self, gid):
        self.on[gid] = True
    def turn_off(self, gid):
        self.on[gid] = False
    def shut_down(self, gid):
        self.stop[gid] = True
    def un_shut_down(self, gid):
        self.stop[gid] = False
               
        
        


class ScoreCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._create_table()


    def _connect(self):
        return sqlite3.connect(DB_PATH)


    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           SCORE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')
    
    
    def _add_score(self, gid, uid ,score):
        try:
            current_score = self._get_score(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score+score))
            conn.commit()       
        except:
            raise Exception('更新表发生错误')

    def _reduce_score(self, gid, uid ,score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score-score))
                conn.commit()     
            else:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, 0))
                conn.commit()     
        except:
            raise Exception('更新表发生错误')

    def _get_score(self, gid, uid):
        try:
            r = self._connect().execute("SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?",(gid,uid)).fetchone()        
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')
            
#判断积分是否足够下注
    def _judge_score(self, gid, uid ,score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                return 1
            else:
                return 0
        except Exception as e:
            raise Exception(str(e))
    


#将角色以角色编号的形式分配到赛道上，返回一个赛道的列表。
def chara_select():
    l = range(1,TOTAL_NUMBER+1)
    select_list = random.sample(l,5)
    return select_list
#取得指定角色编号的赛道号,输入分配好的赛道和指定角色编号
def get_chara_id(list,id):
    raceid= list.index(id)+1
    return raceid
       
#输入赛道列表和自己的赛道，选出自己外最快的赛道
def select_fast(charalist,id):
    list1 = copy.deepcopy(charalist) 
    list1[id-1] = 999
    fast = list1.index(min(list1))
    return fast+1

#输入赛道列表和自己的赛道，选出自己外最慢的赛道。 
def select_last(charalist,id):
    list1 = copy.deepcopy(charalist)
    list1[id-1] = 0
    last = list1.index(max(list1))
    return last+1    
    
#输入赛道列表，自己的赛道和数字n，选出自己外第n快的赛道。     
def select_number(charalist,id,n):
    lis = copy.deepcopy(charalist)
    lis[id-1] = 999
    max_NUMBER = heapq.nsmallest(n, lis) 
    max_index = []
    for t in max_NUMBER:
        index = lis.index(t)
        max_index.append(index)
        lis[index] = 0
    nfast = max_index[n-1]
    return nfast+1

#输入自己的赛道号，选出自己外的随机1个赛道，返回一个赛道编号   
def select_random(id):
    l1 = range(1,NUMBER+1)
    list(l1).remove(id)
    select_id = random.choice(l1)
    return select_id

#输入自己的赛道号和数字n，选出自己外的随机n个赛道，返回一个赛道号的列表   
def nselect_random(id,n):
    l1 = range(1,NUMBER+1)
    list(l1).remove(id)
    select_list = random.sample(l1,n)
    return select_list
    
#选择除自己外的全部对象，返回赛道号的列表
def select_all(id):
    l1 = list(range(1,NUMBER+1))
    l1.remove(id)
    return l1

#对单一对象的基本技能：前进，后退，沉默，暂停，必放ub，交换位置
def forward(id,step,position):
    fid = int(id)
    position[fid-1] = position[fid-1] - step
    position[fid-1] = max (1,position[fid-1])
    return
    
def backward(id,step,position):

    position[id-1] = position[id-1] + step
    position[id-1] = min (ROADLENGTH,position[id-1])
    return  

def give_silence(id,num,silence):
    silence[id-1] += num
    return   

def give_pause(id,num,pause):
    pause[id-1] += num
    return

def give_ub(id,num,ub):
    ub[id-1] += num
    return

def change_position(id1,id2,position):
    position[id1-1],position[id2-1] = position[id2-1],position[id1-1]

#对列表多对象的基本技能

def n_forward(list,step,position):
    for id in list:
        position[id-1] = position[id-1] - step
        position[id-1] = max (1,position[id-1])
    return
    
def n_backward(list,step,position):
    for id in list:
        position[id-1] = position[id-1] + step
        position[id-1] = min (ROADLENGTH,position[id-1])
    return  

def n_give_silence(list,num,silence):
    for id in list:
        silence[id-1] += num
    return   

def n_give_pause(list,num,pause):
    for id in list:
        pause[id-1] += num
    return

def n_give_ub(list,num,ub):
    for id in list:
        ub[id-1] += num
    return

#概率触发的基本技能
def prob_forward(prob,id,step,position):
    r=random.random()
    if r < prob:
        forward(id,step,position)
        return 1
    else :
        return 0
      
        
def prob_backward(prob,id,step,position):
    r=random.random()
    if r < prob:
        backward(id,step,position)
        return 1
    else :
        return 0        
        
def prob_give_pause(prob,id,num,pause):
    r=random.random()
    if r < prob:
        give_pause(id,num,pause)
        return 1
    else :
        return 0

def prob_give_silence(prob,id,num,silence):
    r=random.random()
    if r < prob:
        give_silence(id,num,silence)
        return 1
    else :
        return 0

def prob_critical_forward(prob, id, step, position):
    r = random.random()
    if r < prob:
        forward(id,2*step,position)
        return 1
    else:
        forward(id,step,position)
        return 0
        
#根据概率触发技能的返回，判断是否增加文本，返回一段技能文本
def prob_text(is_prob,text1,text2=None):
    if is_prob == 1:
        addtion_text = text1
    elif text2:
        addtion_text = text2
    else:
        addtion_text = ''
    return addtion_text

#按概率表选择一个技能编号
def skill_select(cid):
    c = runchara.Run_chara(str(cid))
    skillnum_ = ['0','1', '2', '3', '4']
    #概率列表,读json里的概率，被注释掉的为老版本固定概率
    r_ = c.getskill_prob_list()
   #r_ = [0.7, 0.1, 0.1, 0.08, 0.02]
    sum_ = 0
    ran = random.random()
    for num, r in zip(skillnum_, r_):
        sum_ += r
        if ran < sum_ :break
    return int (num)

#加载指定角色的指定技能，返回角色名，技能文本和技能效果
def skill_load(cid,sid):
    c = runchara.Run_chara(str(cid))
    name = c.getname()
    if sid == 0:
        return name,"none","null"
    else :
        skill_text = c.getskill(sid)["skill_text"]
        skill_effect = c.getskill(sid)["skill_effect"]
        return name,skill_text,skill_effect
    
    
#指定赛道的角色释放技能，输入分配好的赛道和赛道编号
def skill_unit(Race_list,rid,position,silence,pause,ub):
    #检查是否被沉默，如果被沉默，即使必定ub也放不出来，并且消耗ub槽
    cid = Race_list[rid-1]
    sid = skill_select(cid)
    if ub[rid-1] == 1:
        sid = 3
        ub[rid-1] -=  1    
    skill = skill_load(cid,sid)
    skillmsg = skill[0]
    skillmsg += ":"
    if silence[rid-1] == 1:
        skillmsg += "本回合被沉默"
        silence[rid-1] -= 1
        return skillmsg

    skillmsg += skill[1]
    list = Race_list
    id = rid
    position = position
    silence = silence
    pause = pause
    ub = ub
    if skill[2]== "null":
        return skillmsg
    loc = locals()    
    addtion_text = ''
    exec(skill[2])
    if 'text'in loc.keys():
        addtion_text = loc['text']    
    skillmsg += addtion_text
    
    return skillmsg
    
#每个赛道的角色轮流释放技能    
def skill_race(Race_list,position,silence,pause,ub):
    skillmsg = ""
    for rid in range(1,6):
        skillmsg += skill_unit(Race_list,rid,position,silence,pause,ub)
        if rid !=5:
            skillmsg += "\n"
    return skillmsg    
        
   
    
#初始状态相关函数    
def position_init(position):
    for i in range (0,NUMBER):
        position[i] = ROADLENGTH
    return
    
def silence_init(silence):
    for i in range (0,NUMBER):
        silence[i] = 0
    return
    
def pause_init(pause):
    for i in range (0,NUMBER):
        pause[i] = 0
    return    
    
def ub_init(ub):
    for i in range (0,NUMBER):
        ub[i] = 0
    return       

#赛道初始化
def race_init(position,silence,pause,ub):
    position_init(position)
    silence_init(silence)
    pause_init(pause)
    ub_init(ub)
    return
    
#一个角色跑步 检查是否暂停
def one_unit_run(id,pause,position,Race_list):
    if  pause[id-1]  == 0:
        cid = Race_list[id-1]
        c = runchara.Run_chara(str(cid))
        speedlist = c.getspeed()
        step = random.choice(speedlist)
        forward(id,step,position)
        return
    else:
        pause[id-1]-=1
        return
           
#一轮跑步，每个角色跑一次    
def one_turn_run(pause,position,Race_list):
    for id in range(1,6):
        one_unit_run(id,pause,position,Race_list)

#打印当前跑步状态
def print_race(Race_list,position):
    racemsg = ""
    for id in range(1,6):
        cid = Race_list[id-1]
        c = runchara.Run_chara(str(cid))
        icon = c.geticon()
                
        for n in range (1,ROADLENGTH+1):
            if n != position[id-1]:
                racemsg = racemsg + ROAD
            else:
                racemsg = racemsg + str(icon)
        if id != 5:
            racemsg = racemsg + "\n"   
      
    return racemsg
#检查比赛结束用，要考虑到同时冲线
def check_game(position):
    winner = []
    is_win = 0
    for id in range(1,6):
        if position[id-1] == 1:
            winner.append(id)
            is_win = 1
    return is_win,winner  



def introduce_race(Race_list):
    msg = ''
    for id in range(1,6):
        msg += f'{id}号：'
        cid = Race_list[id-1]
        c = runchara.Run_chara(str(cid))
        icon = c.geticon()
        name = c.getname()
        msg += f'{name}，图标为{icon}'
        msg += "\n" 
    msg += "所有人请在30秒内选择支持的选手。格式如下：\n1/2/3/4/5号xx积分\n如果积分为0，可以发送：\n领赛跑积分"    
    return msg    
