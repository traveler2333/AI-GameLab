from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import threading
import uuid
import math
import random

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'a_very_secret_key_for_all_games!'
socketio = SocketIO(app)

# --- Tank Game Constants & State ---
TANK_GAME_CANVAS_WIDTH = 800; TANK_GAME_CANVAS_HEIGHT = 600; TANK_SPEED = 3; TANK_ROTATION_SPEED = 0.1; TANK_BULLET_SPEED = 7; TANK_GAME_LOOP_INTERVAL = 0.05; TANK_TARGET_HIT_SCORE = 10; TANK_AI_DESTROYED_SCORE_BASE = 50; TANK_MAX_GAME_EVENTS = 4; TANK_COLLISION_RADIUS = 15; TANK_BODY_WIDTH = 20; TANK_BODY_HEIGHT = 30; TANK_TURRET_LENGTH = 20; TANK_BULLET_RADIUS = 3; TANK_BASE_NUM_AI = 1; TANK_MAX_AI_TANKS = 5; TANK_BASE_AI_SPEED = 1.0; TANK_MAX_AI_SPEED = 2.5; TANK_BASE_AI_MAX_SHOOT_COOLDOWN = 200; TANK_MIN_AI_MAX_SHOOT_COOLDOWN = 70; TANK_BASE_AI_MOVE_TIMER = 120; TANK_MIN_AI_MOVE_TIMER = 50; TANK_NUM_DUMMY_TARGETS = 3;
SERVER_HIGH_SCORE = 0
tank_game_state_lock = threading.Lock()
tank_game_state = {}
tank_game_loop_thread = None

# --- Snake Game Constants & State ---
SNAKE_CANVAS_WIDTH = 400; SNAKE_CANVAS_HEIGHT = 400; SNAKE_GRID_SIZE = 20; SNAKE_GAME_SPEED = 0.15; SNAKE_GRID_WIDTH = SNAKE_CANVAS_WIDTH // SNAKE_GRID_SIZE; SNAKE_GRID_HEIGHT = SNAKE_CANVAS_HEIGHT // SNAKE_GRID_SIZE;
snake_game_state_lock = threading.Lock()
snake_game_state = {}
snake_game_loop_thread = None

# --- Memory Game Constants & State ---
MEMORY_GAME_SYMBOLS = ['🐱', '🐶', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🦁', '🐯', '🐨', '🐷']
MEMORY_BOARD_PAIRS = 8
MEMORY_BOARD_SIZE = MEMORY_BOARD_PAIRS * 2
memory_game_lock = threading.Lock()
memory_game_state = {'board':[],'flipped_indices':[],'moves':0,'matches_found':0,'is_over':False,'lock_board':False}

# --- Hangman Game Constants & State ---
HANGMAN_WORD_LIST = ["PYTHON", "FLASK", "JAVASCRIPT", "HTML", "SOCKETIO", "DEVELOPER", "ENGINEER", "JULES", "TERMINAL", "KEYBOARD", "MONITOR", "SOFTWARE"]
HANGMAN_MAX_WRONG_GUESSES = 6
hangman_game_state_lock = threading.Lock()
hangman_game_state = {'secret_word': "", 'guessed_letters': set(), 'display_word': [], 'wrong_guesses_count': 0, 'game_status': 'playing'}

# --- Gobang Game Constants & State ---
GOBANG_BOARD_SIZE = 15
gobang_game_state_lock = threading.Lock()
gobang_game_state = {
    'board': [], 'current_player': 1, 'game_status_message': "Initializing...",
    'is_game_over': False, 'is_player_turn': True
}

# --- Tank Game Logic (condensed for brevity) ---
def tank_get_initial_player_state(): return {'x': TANK_GAME_CANVAS_WIDTH/2, 'y': TANK_GAME_CANVAS_HEIGHT - TANK_BODY_HEIGHT*2, 'angle': -math.pi/2, 'color':'green', 'status':'active'}
def tank_add_game_event(message):
    if 'game_events' not in tank_game_state: tank_game_state['game_events'] = []
    tank_game_state['game_events'].insert(0, message)
    if len(tank_game_state['game_events']) > TANK_MAX_GAME_EVENTS: tank_game_state['game_events'] = tank_game_state['game_events'][:TANK_MAX_GAME_EVENTS]
def tank_generate_map(num_obstacles_base=5):
    if 'map' not in tank_game_state: tank_game_state['map'] = {}
    tank_game_state['map']['obstacles'] = []
    player_data=tank_game_state.get('player_tank',tank_get_initial_player_state()); player_spawn={'x':player_data['x']-50,'y':player_data['y']-50,'width':100,'height':100}
    num_obs=min(num_obstacles_base+tank_game_state['current_level']//2,10)
    for _ in range(num_obs):
        for _ in range(10):
            w=min(random.randint(30+tank_game_state['current_level']*2,70+tank_game_state['current_level']*5),120);h=min(random.randint(30+tank_game_state['current_level']*2,70+tank_game_state['current_level']*5),120)
            x,y=random.uniform(0,TANK_GAME_CANVAS_WIDTH-w),random.uniform(0,TANK_GAME_CANVAS_HEIGHT-h)
            new_obs={'id':str(uuid.uuid4()),'x':x,'y':y,'width':w,'height':h}
            if tank_check_aabb_collision(new_obs,player_spawn):continue
            if any(tank_check_aabb_collision(new_obs,obs) for obs in tank_game_state['map']['obstacles']):continue
            tank_game_state['map']['obstacles'].append(new_obs);break
def tank_initialize_targets():
    tank_game_state['targets']=[]
    for _ in range(TANK_NUM_DUMMY_TARGETS):
        for _ in range(20):
            w,h=30,30;x,y=random.uniform(0,TANK_GAME_CANVAS_WIDTH-w),random.uniform(0,TANK_GAME_CANVAS_HEIGHT-h)
            new_target={'id':str(uuid.uuid4()),'x':x,'y':y,'width':w,'height':h,'status':'active'}
            player_data=tank_game_state.get('player_tank',tank_get_initial_player_state());player_spawn={'x':player_data['x']-50,'y':player_data['y']-50,'width':100,'height':100}
            if any(tank_check_aabb_collision(new_target,obs) for obs in tank_game_state['map']['obstacles']):continue
            if tank_check_aabb_collision(new_target,player_spawn):continue
            tank_game_state['targets'].append(new_target);break
def tank_initialize_ai(level):
    num=min(TANK_MAX_AI_TANKS,TANK_BASE_NUM_AI+(level-1));speed=min(TANK_MAX_AI_SPEED,TANK_BASE_AI_SPEED+(level-1)*0.2);cooldown=int(max(TANK_MIN_AI_MAX_SHOOT_COOLDOWN,TANK_BASE_AI_MAX_SHOOT_COOLDOWN-(level-1)*10));move_timer=int(max(TANK_MIN_AI_MOVE_TIMER,TANK_BASE_AI_MOVE_TIMER-(level-1)*7));ai_tanks=[]
    for _ in range(num):
        for _ in range(20):
            x,y=random.uniform(TANK_BODY_WIDTH,TANK_GAME_CANVAS_WIDTH-TANK_BODY_WIDTH),random.uniform(TANK_BODY_HEIGHT,TANK_GAME_CANVAS_HEIGHT*0.6)
            ai_bbox={'x':x-TANK_COLLISION_RADIUS,'y':y-TANK_COLLISION_RADIUS,'width':TANK_COLLISION_RADIUS*2,'height':TANK_COLLISION_RADIUS*2}
            player_data=tank_game_state.get('player_tank',tank_get_initial_player_state());player_bbox={'x':player_data['x']-TANK_COLLISION_RADIUS*2,'y':player_data['y']-TANK_COLLISION_RADIUS*2,'width':TANK_COLLISION_RADIUS*4,'height':TANK_COLLISION_RADIUS*4}
            if tank_check_aabb_collision(ai_bbox,player_bbox):continue
            if any(tank_check_aabb_collision(ai_bbox,obs) for obs in tank_game_state['map'].get('obstacles',[])):continue
            if any(tank_check_aabb_collision(ai_bbox,{'x':o['x']-TANK_COLLISION_RADIUS,'y':o['y']-TANK_COLLISION_RADIUS,'width':TANK_COLLISION_RADIUS*2,'height':TANK_COLLISION_RADIUS*2}) for o in ai_tanks):continue
            ai_tank={'id':str(uuid.uuid4()),'x':x,'y':y,'angle':random.uniform(0,2*math.pi),'color':random.choice(['#B22222','#8B4513','#A0522D']),'speed':speed,'rotation_speed':0.05+(level-1)*0.005,'shoot_cooldown':random.randint(cooldown//2,cooldown),'max_shoot_cooldown':cooldown,'move_timer':random.randint(move_timer//2,move_timer),'max_move_timer':move_timer,'status':'active'}
            ai_tanks.append(ai_tank);break
    tank_game_state['ai_tanks']=ai_tanks
def tank_reset_game_state():
    global tank_game_state,SERVER_HIGH_SCORE,tank_game_loop_thread
    with tank_game_state_lock:
        if tank_game_loop_thread and tank_game_loop_thread.is_alive():
            if 'game_active' in tank_game_state:tank_game_state['game_active']=False
        tank_game_state={'player_tank':tank_get_initial_player_state(),'ai_tanks':[],'bullets':[],'targets':[],'map':{'obstacles':[]},'game_events':[],'score':0,'current_level':1,'is_over':False,'high_score':SERVER_HIGH_SCORE,'game_active':True}
        tank_generate_map();tank_initialize_targets();tank_initialize_ai(tank_game_state['current_level'])
        tank_add_game_event(f"Tank Game Started! Level {tank_game_state['current_level']}")
def tank_check_aabb_collision(r1,r2): return r1['x']<r2['x']+r2['width'] and r1['x']+r1['width']>r2['x'] and r1['y']<r2['y']+r2['height'] and r1['y']+r1['height']>r2['y']
def tank_game_loop():
    global tank_game_state,SERVER_HIGH_SCORE
    while True:
        with tank_game_state_lock:
            if not tank_game_state.get('game_active',False):break
            if not tank_game_state.get('is_over',False):
                all_tanks=[tank_game_state['player_tank']]+tank_game_state['ai_tanks']
                for tank in all_tanks:
                    if tank.get('status','active')!='active':continue
                    px,py=tank['x'],tank['y']
                    if 'move_timer' in tank:
                        tank['move_timer']-=1
                        if tank['move_timer']<=0:tank['angle']=(tank['angle']+random.uniform(-math.pi/1.5,math.pi/1.5))%(2*math.pi);tank['move_timer']=tank['max_move_timer']
                        tank['x']+=tank['speed']*math.cos(tank['angle']);tank['y']+=tank['speed']*math.sin(tank['angle'])
                    if not(TANK_COLLISION_RADIUS<=tank['x']<=TANK_GAME_CANVAS_WIDTH-TANK_COLLISION_RADIUS):tank['x']=px;
                    if'move_timer'in tank:tank['angle']=(tank['angle']+math.pi+random.uniform(-0.1,0.1))%(2*math.pi)
                    if not(TANK_COLLISION_RADIUS<=tank['y']<=TANK_GAME_CANVAS_HEIGHT-TANK_COLLISION_RADIUS):tank['y']=py;
                    if'move_timer'in tank:tank['angle']=(tank['angle']+math.pi+random.uniform(-0.1,0.1))%(2*math.pi)
                    tank_bbox={'x':tank['x']-TANK_COLLISION_RADIUS,'y':tank['y']-TANK_COLLISION_RADIUS,'width':TANK_COLLISION_RADIUS*2,'height':TANK_COLLISION_RADIUS*2}
                    for obs in tank_game_state['map']['obstacles']:
                        if tank_check_aabb_collision(tank_bbox,obs):
                            tank['x'],tank['y']=px,py
                            if'move_timer'in tank:tank['angle']=(tank['angle']+math.pi/2+random.uniform(-0.3,0.3))%(2*math.pi);tank['move_timer']=tank['max_move_timer']//2
                            break
                    if'move_timer'in tank and tank.get('status')=='active':
                        tank['shoot_cooldown']-=1
                        if tank['shoot_cooldown']<=0:
                            b_x,b_y=tank['x']+TANK_TURRET_LENGTH*math.cos(tank['angle']),tank['y']+TANK_TURRET_LENGTH*math.sin(tank['angle'])
                            tank_game_state['bullets'].append({'id':str(uuid.uuid4()),'x':b_x,'y':b_y,'angle':tank['angle'],'speed':TANK_BULLET_SPEED+tank_game_state['current_level']*0.15,'owner':'ai','color':tank['color']})
                            tank['shoot_cooldown']=tank['max_shoot_cooldown']
                active_bullets=[]
                for b in tank_game_state['bullets']:
                    b['x']+=b['speed']*math.cos(b['angle']);b['y']+=b['speed']*math.sin(b['angle']);collided=False
                    if not(0<b['x']<TANK_GAME_CANVAS_WIDTH and 0<b['y']<TANK_GAME_CANVAS_HEIGHT):collided=True
                    b_bbox={'x':b['x']-TANK_BULLET_RADIUS,'y':b['y']-TANK_BULLET_RADIUS,'width':TANK_BULLET_RADIUS*2,'height':TANK_BULLET_RADIUS*2}
                    if not collided:
                        for obs in tank_game_state['map']['obstacles']:
                            if tank_check_aabb_collision(b_bbox,obs):b['hit_obstacle']=True;collided=True;break
                    if not collided:
                        for t in tank_game_state['targets']:
                            if t.get('status','inactive')=='active' and tank_check_aabb_collision(b_bbox,t):
                                t['status']='hit';
                                if b.get('owner')=='player':tank_game_state['score']+=TANK_TARGET_HIT_SCORE;tank_add_game_event(f"Target Hit! +{TANK_TARGET_HIT_SCORE}")
                                collided=True;break
                    if not collided and b.get('owner')=='player':
                        for ai in tank_game_state['ai_tanks']:
                            if ai.get('status')=='active':
                                ai_bbox={'x':ai['x']-TANK_COLLISION_RADIUS,'y':ai['y']-TANK_COLLISION_RADIUS,'width':TANK_COLLISION_RADIUS*2,'height':TANK_COLLISION_RADIUS*2}
                                if tank_check_aabb_collision(b_bbox,ai_bbox):
                                    ai['status']='destroyed';points=TANK_AI_DESTROYED_SCORE_BASE+(tank_game_state['current_level']-1)*10
                                    tank_game_state['score']+=points;tank_add_game_event(f"Enemy Down! +{points}")
                                    collided=True;break
                    if not collided and b.get('owner')=='ai' and tank_game_state['player_tank']['status']=='active':
                        pt=tank_game_state['player_tank'];p_bbox={'x':pt['x']-TANK_COLLISION_RADIUS,'y':pt['y']-TANK_COLLISION_RADIUS,'width':TANK_COLLISION_RADIUS*2,'height':TANK_COLLISION_RADIUS*2}
                        if tank_check_aabb_collision(b_bbox,p_bbox):
                            pt['status']='destroyed';tank_game_state['is_over']=True;tank_add_game_event("Tank Destroyed!")
                            if tank_game_state['score']>SERVER_HIGH_SCORE:SERVER_HIGH_SCORE=tank_game_state['score'];tank_game_state['high_score']=SERVER_HIGH_SCORE;tank_add_game_event(f"New Tank High Score: {SERVER_HIGH_SCORE}!")
                            collided=True
                    if not collided:active_bullets.append(b)
                tank_game_state['bullets']=active_bullets
                tank_game_state['ai_tanks']=[t for t in tank_game_state['ai_tanks'] if t.get('status')=='active']
                if not tank_game_state['is_over'] and not tank_game_state['ai_tanks']:
                    tank_game_state['current_level']+=1;tank_add_game_event(f"Reached Level {tank_game_state['current_level']}!")
                    tank_generate_map();tank_initialize_ai(tank_game_state['current_level']);tank_initialize_targets()
            if tank_game_state.get('score',0)>tank_game_state.get('high_score',0):
                tank_game_state['high_score']=tank_game_state['score']
                if tank_game_state['high_score']>SERVER_HIGH_SCORE:SERVER_HIGH_SCORE=tank_game_state['high_score']
            socketio.emit('tank_update_state',tank_game_state)
        time.sleep(TANK_GAME_LOOP_INTERVAL)
    print("Exited Tank game loop")

# --- Snake Game Logic (condensed) ---
def snake_initialize_game():
    global snake_game_state
    with snake_game_lock:
        snake_game_state={'snake_body':[(SNAKE_GRID_WIDTH//2,SNAKE_GRID_HEIGHT//2)],'food_pos':(0,0),'score':0,'direction':'RIGHT','is_game_over':False,'game_active':True,'grid_width':SNAKE_GRID_WIDTH,'grid_height':SNAKE_GRID_HEIGHT,'grid_size':SNAKE_GRID_SIZE}
        snake_place_food_unsafe();print("Snake game initialized/restarted")
def snake_place_food_unsafe():
    while True:
        food_x,food_y=random.randint(0,SNAKE_GRID_WIDTH-1),random.randint(0,SNAKE_GRID_HEIGHT-1)
        if(food_x,food_y)not in snake_game_state['snake_body']:snake_game_state['food_pos']=(food_x,food_y);break
def snake_game_loop_function():
    global snake_game_state
    while True:
        with snake_game_lock:
            if not snake_game_state.get('game_active',False):break
            if snake_game_state.get('is_game_over',False):socketio.emit('snake_update_state',dict(snake_game_state));time.sleep(SNAKE_GAME_SPEED);continue
            head_x,head_y=snake_game_state['snake_body'][0]
            if snake_game_state['direction']=='UP':new_head=(head_x,head_y-1)
            elif snake_game_state['direction']=='DOWN':new_head=(head_x,head_y+1)
            elif snake_game_state['direction']=='LEFT':new_head=(head_x-1,head_y)
            else:new_head=(head_x+1,head_y)
            if not(0<=new_head[0]<SNAKE_GRID_WIDTH and 0<=new_head[1]<SNAKE_GRID_HEIGHT)or new_head in snake_game_state['snake_body']:
                snake_game_state['is_game_over']=True;snake_game_state['game_active']=False;print(f"Snake Game Over! Score: {snake_game_state['score']}")
            if not snake_game_state['is_game_over']:
                snake_game_state['snake_body'].insert(0,new_head)
                if new_head==snake_game_state['food_pos']:snake_game_state['score']+=1;snake_place_food_unsafe()
                else:snake_game_state['snake_body'].pop()
            current_snapshot=dict(snake_game_state)
        socketio.emit('snake_update_state',current_snapshot);time.sleep(SNAKE_GAME_SPEED)
    print("Exited Snake game loop")
def snake_start_new_game_instance():
    global snake_game_loop_thread
    with snake_game_lock:
        if snake_game_loop_thread and snake_game_loop_thread.is_alive():
            if'game_active'in snake_game_state:snake_game_state['game_active']=False
            snake_game_loop_thread.join(timeout=SNAKE_GAME_SPEED*2)
        snake_initialize_game()
        snake_game_loop_thread=threading.Thread(target=snake_game_loop_function,daemon=True);snake_game_loop_thread.start()
        print("New Snake game instance started.")

# --- Memory Game Logic (condensed) ---
def memory_initialize_game():
    global memory_game_state
    with memory_game_lock:
        symbols_for_board=(MEMORY_GAME_SYMBOLS[:MEMORY_BOARD_PAIRS]*2);random.shuffle(symbols_for_board)
        memory_game_state['board']=[{'id':i,'symbol':symbols_for_board[i],'is_flipped':False,'is_matched':False} for i in range(MEMORY_BOARD_SIZE)]
        memory_game_state['flipped_indices']=[];memory_game_state['moves']=0;memory_game_state['matches_found']=0;memory_game_state['is_over']=False;memory_game_state['lock_board']=False;print("Memory game initialized.")
def memory_get_client_state(): return {'board':memory_game_state['board'],'moves':memory_game_state['moves'],'is_over':memory_game_state['is_over'],'lock_board':memory_game_state['lock_board']}

# --- Hangman Game Logic ---
def hangman_initialize_game():
    global hangman_game_state
    with hangman_game_state_lock:
        hangman_game_state['secret_word'] = random.choice(HANGMAN_WORD_LIST)
        hangman_game_state['guessed_letters'] = set()
        hangman_game_state['display_word'] = ['_'] * len(hangman_game_state['secret_word'])
        hangman_game_state['wrong_guesses_count'] = 0
        hangman_game_state['game_status'] = 'playing'
        print(f"Hangman game initialized. Word: {hangman_game_state['secret_word']}")

def get_hangman_public_state():
    with hangman_game_state_lock:
        return {
            'display_word': hangman_game_state['display_word'],
            'guessed_letters': list(hangman_game_state['guessed_letters']),
            'wrong_guesses_count': hangman_game_state['wrong_guesses_count'],
            'max_wrong_guesses': HANGMAN_MAX_WRONG_GUESSES,
            'game_status': hangman_game_state['game_status'],
            'secret_word': hangman_game_state['secret_word'] if hangman_game_state['game_status'] == 'lost' else None
        }

# --- Gobang Game Logic ---
def gobang_initialize_game():
    global gobang_game_state
    with gobang_game_state_lock:
        gobang_game_state['board'] = [[0 for _ in range(GOBANG_BOARD_SIZE)] for _ in range(GOBANG_BOARD_SIZE)]
        gobang_game_state['current_player'] = 1 # Player (black) starts
        gobang_game_state['is_game_over'] = False
        gobang_game_state['is_player_turn'] = True
        gobang_game_state['game_status_message'] = "游戏开始! 请玩家走棋 (黑棋)."
        print("Gobang game initialized.")

def gobang_check_win(board, player_stone):
    for r in range(GOBANG_BOARD_SIZE):
        for c in range(GOBANG_BOARD_SIZE):
            if board[r][c] == player_stone:
                if c + 4 < GOBANG_BOARD_SIZE and all(board[r][c+i] == player_stone for i in range(5)): return True
                if r + 4 < GOBANG_BOARD_SIZE and all(board[r+i][c] == player_stone for i in range(5)): return True
                if r + 4 < GOBANG_BOARD_SIZE and c + 4 < GOBANG_BOARD_SIZE and all(board[r+i][c+i] == player_stone for i in range(5)): return True
                if r - 4 >= 0 and c + 4 < GOBANG_BOARD_SIZE and all(board[r-i][c+i] == player_stone for i in range(5)): return True
    return False

def gobang_ai_find_best_move(board):
    empty_cells = []
    for r_idx, row_val in enumerate(board):
        for c_idx, cell_val in enumerate(row_val):
            if cell_val == 0: empty_cells.append((r_idx, c_idx))
    if empty_cells:
        for r, c in empty_cells: # Simple heuristic: play near existing stones
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GOBANG_BOARD_SIZE and 0 <= nc < GOBANG_BOARD_SIZE and board[nr][nc] != 0: return (r,c)
        return random.choice(empty_cells)
    return None

def get_gobang_public_state():
    with gobang_game_state_lock:
        return {
            'board': gobang_game_state['board'],
            'status_message': gobang_game_state['game_status_message'],
            'is_game_over': gobang_game_state['is_game_over'],
            'is_player_turn': gobang_game_state['is_player_turn']
        }


# --- Flask Routes ---
@app.route('/')
def lobby(): return render_template('lobby.html')
@app.route('/tank_game_page')
def tank_game_page_route(): return render_template('index.html')
@app.route('/snake_game_page')
def snake_game_page_route(): return render_template('snake_game.html')
@app.route('/memory_game_page')
def memory_game_page_route(): return render_template('memory_game.html')
@app.route('/hangman_game_page')
def hangman_game_page_route(): return render_template('hangman_game.html')
@app.route('/gobang_game_page')
def gobang_game_page_route(): return render_template('gobang_game.html')

# --- SocketIO Event Handlers ---
@socketio.on('tank_connect') # Tank Game
def handle_tank_connect():
    global tank_game_loop_thread;print('Client connected to Tank game.')
    with tank_game_state_lock:
        is_first_or_stale=not tank_game_state or tank_game_state.get('current_level',0)==0 or not tank_game_loop_thread or not tank_game_loop_thread.is_alive()
        if is_first_or_stale:
            tank_reset_game_state()
            if not tank_game_loop_thread or not tank_game_loop_thread.is_alive():
                tank_game_loop_thread=threading.Thread(target=tank_game_loop,daemon=True);tank_game_loop_thread.start()
        socketio.emit('tank_update_state',tank_game_state)
@socketio.on('tank_player_input') # Tank Game
def handle_tank_player_input(data):
    with tank_game_state_lock:
        if tank_game_state.get('is_over',False)or tank_game_state.get('player_tank',{}).get('status')=='destroyed':return
        player_tank=tank_game_state['player_tank'];action=data.get('action')
        if action=='move':direction=data.get('direction');speed=TANK_SPEED if direction=='forward'else -TANK_SPEED;player_tank['x']+=speed*math.cos(player_tank['angle']);player_tank['y']+=speed*math.sin(player_tank['angle'])
        elif action=='rotate':direction=data.get('direction');player_tank['angle']-=(TANK_ROTATION_SPEED if direction=='left'else -TANK_ROTATION_SPEED);player_tank['angle']%= (2*math.pi)
        elif action=='shoot':bx,by=player_tank['x']+TANK_TURRET_LENGTH*math.cos(player_tank['angle']),player_tank['y']+TANK_TURRET_LENGTH*math.sin(player_tank['angle']);tank_game_state['bullets'].append({'id':str(uuid.uuid4()),'x':bx,'y':by,'angle':player_tank['angle'],'speed':TANK_BULLET_SPEED,'owner':'player','color':'#00FFFF'})
@socketio.on('tank_restart_game') # Tank Game
def handle_tank_restart_game():
    global tank_game_loop_thread;print("Tank game restart request received.");tank_reset_game_state()
    if not tank_game_loop_thread or not tank_game_loop_thread.is_alive():print("Tank game loop was not running. Starting it now.");tank_game_loop_thread=threading.Thread(target=tank_game_loop,daemon=True);tank_game_loop_thread.start()
    socketio.emit('tank_update_state',tank_game_state)

@socketio.on('snake_start_game') # Snake Game
def handle_snake_start_game():
    print("Snake game started/restarted by client");snake_start_new_game_instance()
    with snake_game_lock:socketio.emit('snake_update_state',dict(snake_game_state))
@socketio.on('snake_change_direction') # Snake Game
def handle_snake_change_direction(data):
    new_dir=data.get('direction')
    if not new_dir:return
    with snake_game_lock:
        if snake_game_state.get('is_game_over',True)or not snake_game_state.get('game_active',False):return
        current_dir=snake_game_state['direction']
        if(new_dir=='UP'and current_dir!='DOWN')or(new_dir=='DOWN'and current_dir!='UP')or(new_dir=='LEFT'and current_dir!='RIGHT')or(new_dir=='RIGHT'and current_dir!='LEFT'):snake_game_state['direction']=new_dir

@socketio.on('memory_start_game') # Memory Game
def handle_memory_start_game():
    with memory_game_lock:memory_initialize_game();socketio.emit('memory_update_state',memory_get_client_state())
@socketio.on('memory_flip_card') # Memory Game
def handle_memory_flip_card(data):
    with memory_game_lock:
        if memory_game_state['lock_board']or memory_game_state['is_over']:return
        card_id=data.get('card_id')
        if card_id is None or not(0<=card_id<MEMORY_BOARD_SIZE):return
        card=memory_game_state['board'][card_id]
        if card['is_flipped']or card['is_matched']:return
        card['is_flipped']=True;memory_game_state['flipped_indices'].append(card_id)
        socketio.emit('memory_update_state',memory_get_client_state())
        if len(memory_game_state['flipped_indices'])==2:
            memory_game_state['moves']+=1;memory_game_state['lock_board']=True
            idx1,idx2=memory_game_state['flipped_indices']
            card1,card2=memory_game_state['board'][idx1],memory_game_state['board'][idx2]
            if card1['symbol']==card2['symbol']:
                card1['is_matched'],card2['is_matched']=True,True
                memory_game_state['matches_found']+=1;memory_game_state['flipped_indices']=[];memory_game_state['lock_board']=False
                if memory_game_state['matches_found']*2==MEMORY_BOARD_SIZE:memory_game_state['is_over']=True
                socketio.emit('memory_update_state',memory_get_client_state())
            else:
                def unflip_task():
                    socketio.sleep(1.0)
                    with memory_game_lock:
                        if memory_game_state['board'] and idx1<len(memory_game_state['board']) and memory_game_state['board'][idx1]['is_flipped']and not memory_game_state['board'][idx1]['is_matched'] and idx2<len(memory_game_state['board']) and memory_game_state['board'][idx2]['is_flipped']and not memory_game_state['board'][idx2]['is_matched']:
                            memory_game_state['board'][idx1]['is_flipped']=False;memory_game_state['board'][idx2]['is_flipped']=False
                        memory_game_state['flipped_indices']=[];memory_game_state['lock_board']=False
                        socketio.emit('memory_update_state',memory_get_client_state())
                socketio.start_background_task(target=unflip_task)

@socketio.on('hangman_start_game') # Hangman Game
def handle_hangman_start_game():
    with hangman_game_state_lock: hangman_initialize_game()
    socketio.emit('hangman_update_state', get_hangman_public_state())
@socketio.on('hangman_guess_letter') # Hangman Game
def handle_hangman_guess_letter(data):
    with hangman_game_state_lock:
        if hangman_game_state['game_status']!='playing':return
        letter=data.get('letter','').upper()
        if not letter or len(letter)!=1 or not letter.isalpha() or letter in hangman_game_state['guessed_letters']:return
        hangman_game_state['guessed_letters'].add(letter)
        if letter in hangman_game_state['secret_word']:
            for i,char_in_word in enumerate(hangman_game_state['secret_word']):
                if char_in_word==letter:hangman_game_state['display_word'][i]=letter
            if "_" not in hangman_game_state['display_word']:hangman_game_state['game_status']='won'
        else:
            hangman_game_state['wrong_guesses_count']+=1
            if hangman_game_state['wrong_guesses_count']>=HANGMAN_MAX_WRONG_GUESSES:hangman_game_state['game_status']='lost'
    socketio.emit('hangman_update_state',get_hangman_public_state())

# Gobang Game SocketIO Handlers
@socketio.on('gobang_start_game')
def handle_gobang_start_game():
    with gobang_game_state_lock:
        gobang_initialize_game()
    socketio.emit('gobang_update_state', get_gobang_public_state())

@socketio.on('gobang_player_move')
def handle_gobang_player_move(data):
    with gobang_game_state_lock:
        if gobang_game_state['is_game_over'] or not gobang_game_state['is_player_turn']:
            return

        row, col = data.get('row'), data.get('col')
        if not (0 <= row < GOBANG_BOARD_SIZE and 0 <= col < GOBANG_BOARD_SIZE and gobang_game_state['board'][row][col] == 0):
            return # Invalid move

        gobang_game_state['board'][row][col] = 1 # Player's stone (black)
        if gobang_check_win(gobang_game_state['board'], 1):
            gobang_game_state['is_game_over'] = True
            gobang_game_state['game_status_message'] = "恭喜! 玩家获胜!"
            gobang_game_state['is_player_turn'] = False
            socketio.emit('gobang_update_state', get_gobang_public_state())
            return

        if not any(0 in r for r in gobang_game_state['board']): # Check for draw
            gobang_game_state['is_game_over'] = True
            gobang_game_state['game_status_message'] = "平局!"
            gobang_game_state['is_player_turn'] = False
            socketio.emit('gobang_update_state', get_gobang_public_state())
            return

        gobang_game_state['is_player_turn'] = False
        gobang_game_state['game_status_message'] = "AI思考中..."
        socketio.emit('gobang_update_state', get_gobang_public_state())

    # AI's turn - run as background task to allow emit before AI "thinks"
    def ai_turn_task():
        socketio.sleep(0.5) # Simulate AI thinking time
        with gobang_game_state_lock:
            if gobang_game_state['is_game_over']: return # Game might have been reset

            ai_move = gobang_ai_find_best_move(gobang_game_state['board'])
            if ai_move:
                r_ai, c_ai = ai_move
                gobang_game_state['board'][r_ai][c_ai] = 2 # AI's stone (white)
                if gobang_check_win(gobang_game_state['board'], 2):
                    gobang_game_state['is_game_over'] = True
                    gobang_game_state['game_status_message'] = "AI 获胜!"
                elif not any(0 in r for r in gobang_game_state['board']): # Check draw again
                    gobang_game_state['is_game_over'] = True
                    gobang_game_state['game_status_message'] = "平局!"
                else:
                    gobang_game_state['game_status_message'] = "请玩家走棋"
                    gobang_game_state['is_player_turn'] = True
            else:
                 if not gobang_game_state['is_game_over']:
                    gobang_game_state['is_game_over'] = True
                    gobang_game_state['game_status_message'] = "平局! (AI无法移动)"
            socketio.emit('gobang_update_state', get_gobang_public_state())

    socketio.start_background_task(target=ai_turn_task)


@socketio.on('connect')
def general_connect():print("A client connected (general connection). Game-specific start event expected from client.")
@socketio.on('disconnect')
def general_disconnect():print("A client disconnected.")

if __name__ == '__main__':
    print("Initializing server and preparing game states...")
    with tank_game_state_lock: tank_game_state = {'game_active': False, 'current_level':0}
    with snake_game_lock: snake_game_state = {'game_active': False}
    with memory_game_lock: memory_initialize_game()
    with hangman_game_state_lock: hangman_initialize_game()
    with gobang_game_state_lock: gobang_initialize_game() # Initialize Gobang state at start

    print("Starting Flask-SocketIO server on http://localhost:5000 ...")
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=5000)

[end of games/tank_game/main.py]
