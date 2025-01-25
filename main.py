import tkinter as tk
from tkinter import ttk, messagebox
import math

# 游戏配置
BOARD_SIZE = 15
CELL_SIZE = 40
AI_DEPTH = 4
COLORS = {
    'board': '#E6C9A8',
    'player1': '#2C2C2C',
    'player2': '#F5F5F5',
    'hover': '#FFD700',
    'last_move': '#FF4136',
    'bg': '#4A766E',
    'highlight': '#DDDDDD'
}

SCORE = {
    'five': 10000000,
    'live_four': 500000,
    'rush_four': 100000,
    'live_three': 80000,
    'rush_three': 30000,
    'live_two': 5000,
    'rush_two': 1000
}

class GobangGame:
    def __init__(self, master, mode='ai', first_player=1):
        self.master = master
        self.master.configure(bg=COLORS['bg'])
        
        # 游戏设置
        self.mode = mode
        self.ai_first = (first_player == 2)
        self.board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.human_turn = (first_player == 1)
        self.last_ai_move = None  # 新增：记录AI最后一步
        self.last_move_marker = None  # 新增：标记图形对象
        
        # 创建界面
        self.create_widgets()
        if self.mode == 'ai' and self.ai_first:
            self.master.after(500, self.ai_move)

    def create_widgets(self):
        """创建游戏界面组件"""
        # 棋盘（增加边框效果）
        self.canvas = tk.Canvas(self.master, 
                              width=CELL_SIZE*BOARD_SIZE,
                              height=CELL_SIZE*BOARD_SIZE,
                              bg=COLORS['board'], 
                              highlightthickness=2,
                              highlightbackground="#8B4513")
        self.canvas.pack(pady=20, padx=20)
        
        # 控制面板（优化样式）
        control_frame = ttk.Frame(self.master, style='Dark.TFrame')
        control_frame.pack(fill='x', padx=20)
        
        # 状态标签（增加图标）
        self.status_var = tk.StringVar()
        status_style = ttk.Style()
        status_style.configure('Status.TLabel', 
                              font=('微软雅黑', 12),
                              foreground='white',
                              background=COLORS['bg'])
        self.status_label = ttk.Label(control_frame, 
                                    textvariable=self.status_var,
                                    style='Status.TLabel')
        self.status_label.pack(side='left', padx=10)
        
        # 按钮样式
        btn_style = ttk.Style()
        btn_style.configure('Gold.TButton', 
                          font=('微软雅黑', 10),
                          foreground='black',
                          background='#FFD700')
        
        ttk.Button(control_frame, text="新游戏", 
                  style='Gold.TButton', 
                  command=self.restart).pack(side='right')
        
        ttk.Button(control_frame, text="退出", 
                  style='Gold.TButton', 
                  command=self.master.quit).pack(side='right', padx=10)
        
        # 绘制棋盘
        self.draw_board()
        self.update_status()
        
        # 事件绑定
        self.canvas.bind("<Motion>", self.mouse_hover)
        self.canvas.bind("<Button-1>", self.click_handler)

    def draw_board(self):
        """绘制棋盘（带最后一步标记）"""
        self.canvas.delete("all")  # 清空画布
        
        # 棋盘线（优化线条颜色）
        for i in range(BOARD_SIZE):
            self.canvas.create_line(
                CELL_SIZE//2, i*CELL_SIZE + CELL_SIZE//2,
                CELL_SIZE*(BOARD_SIZE-0.5), i*CELL_SIZE + CELL_SIZE//2,
                width=1.5, fill='#5A4D41'
            )
            self.canvas.create_line(
                i*CELL_SIZE + CELL_SIZE//2, CELL_SIZE//2,
                i*CELL_SIZE + CELL_SIZE//2, CELL_SIZE*(BOARD_SIZE-0.5),
                width=1.5, fill='#5A4D41'
            )
        
        # 星位标记（增大尺寸）
        star_points = [(3,3), (3,11), (11,3), (11,11), (7,7)]
        for x, y in star_points:
            self.canvas.create_oval(
                (x*CELL_SIZE + CELL_SIZE//2 - 5,
                 y*CELL_SIZE + CELL_SIZE//2 - 5,
                 x*CELL_SIZE + CELL_SIZE//2 + 5,
                 y*CELL_SIZE + CELL_SIZE//2 + 5),
                fill='#5A4D41', outline=''
            )
        
        # 绘制已有棋子（包括最后一步标记）
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] != 0:
                    self.draw_piece(i, j, self.board[i][j])
        
        # 单独绘制最后一步标记（确保在最上层）
        if self.last_ai_move:
            row, col = self.last_ai_move
            x = col * CELL_SIZE + CELL_SIZE//2
            y = row * CELL_SIZE + CELL_SIZE//2
            self.last_move_marker = self.canvas.create_oval(
                x-8, y-8, x+8, y+8,
                outline=COLORS['last_move'], width=3,
                tags="last_move"
            )

    def draw_piece(self, row, col, player):
        """绘制棋子（不再包含标记逻辑）"""
        x = col * CELL_SIZE + CELL_SIZE//2
        y = row * CELL_SIZE + CELL_SIZE//2
        color = COLORS['player1'] if player == 1 else COLORS['player2']
        
        # 立体阴影效果
        self.canvas.create_oval(x-16, y-16, x+16, y+16,
                               fill=color, outline='#222222', width=2)
        self.canvas.create_oval(x-14, y-14, x+14, y+14,
                           outline=COLORS['highlight'], width=1)

    def ai_move(self):
        """AI移动（增加标记管理）"""
        if not self.game_over and not self.human_turn:
            # 删除旧标记
            if self.last_move_marker:
                self.canvas.delete(self.last_move_marker)
            
            move = self.find_best_move()
            if move:
                row, col = move
                self.last_ai_move = (row, col)
                self.place_piece(row, col, 2)
                
                # 绘制新标记
                x = col * CELL_SIZE + CELL_SIZE//2
                y = row * CELL_SIZE + CELL_SIZE//2
                self.last_move_marker = self.canvas.create_oval(
                    x-8, y-8, x+8, y+8,
                    outline=COLORS['last_move'], width=3,
                    tags="last_move"
                )
                
                if self.check_win(row, col, 2):
                    self.game_end("ai_win")
                else:
                    self.human_turn = True
                    self.update_status()

    def place_piece(self, row, col, player):
        """放置棋子（优化边界检查）"""
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.board[row][col] == 0 and not self.game_over:
                self.board[row][col] = player
                self.draw_piece(row, col, player)
                return True
        return False

##########################################

    def get_grid_pos(self, event):
        """将鼠标坐标转换为棋盘网格位置（列，行）"""
        board_x = event.x - CELL_SIZE//2
        board_y = event.y - CELL_SIZE//2
        
        # 计算网格位置（四舍五入）
        col = round(board_x / CELL_SIZE)
        row = round(board_y / CELL_SIZE)
        
        # 边界约束
        col = max(0, min(col, BOARD_SIZE-1))
        row = max(0, min(row, BOARD_SIZE-1))
        
        return col, row

    def mouse_hover(self, event):
        """处理鼠标移动事件"""
        if not self.human_turn or self.game_over:
            return
        
        try:
            col, row = self.get_grid_pos(event)
            self.show_hover(row, col)
        except (AttributeError, TypeError):
            # 处理初始化未完成时的异常
            pass

    def click_handler(self, event):
        """修复后的点击处理"""
        if not self.human_turn or self.game_over:
            return
        
        try:
            col, row = self.get_grid_pos(event)
            if self.board[row][col] == 0:
                self.place_piece(row, col, 1)
                
                # 检查胜利
                if self.check_win(row, col, 1):
                    self.game_end("player_win")
                    return  # 确保胜利后立即返回
                
                # 模式判断
                if self.mode == 'ai':
                    self.human_turn = False  # 必须显式设置
                    self.update_status()
                    self.master.after(200, self.ai_move)  # 确保调用AI
                else:
                    self.human_turn = not self.human_turn
                    self.update_status()
                    
        except Exception as e:
            print(f"操作异常: {e}")


    def show_hover(self, row, col):
        """显示悬停效果"""
        x = col * CELL_SIZE + CELL_SIZE//2
        y = row * CELL_SIZE + CELL_SIZE//2
        if hasattr(self, 'hover_item'):
            self.canvas.delete(self.hover_item)
        self.hover_item = self.canvas.create_oval(
            x-18, y-18, x+18, y+18,
            outline=COLORS['hover'], width=3, dash=(4,4)
        )



    def game_end(self, result):
        """结束游戏"""
        self.game_over = True
        messages = {
            'player_win': ("胜利！", "恭喜你战胜了AI！\n🎉🎉🎉"),
            'ai_win': ("挑战失败", "AI取得了胜利，再接再厉！\n💪"),
            'pvp_win': ("游戏结束", "玩家{}获胜！".format(1 if self.human_turn else 2)),
            'draw': ("平局", "旗鼓相当的对手！")
        }
        
        if result == 'player_win':
            title, msg = messages['player_win']
            icon = 'info'
        elif result == 'ai_win':
            title, msg = messages['ai_win']
            icon = 'warning'
        else:
            title, msg = messages.get(result, ("游戏结束", ""))
            icon = 'info'
            
        messagebox.showinfo(title, msg, icon=icon)
        self.status_var.set("游戏结束 - " + title)

    def restart(self):
        """重新开始游戏"""
        self.master.destroy()
        show_setup_window()

    def update_status(self):
        """更新状态栏"""
        if self.mode == 'pvp':
            text = "玩家{}回合".format(1 if self.human_turn else 2)
        else:
            text = "你的回合" if self.human_turn else "AI思考中..."
        self.status_var.set(text)

    # ------------ 核心AI算法（保持不变）------------
    def find_best_move(self):
        if win_move := self.find_winning_move(2):
            return win_move
        if defense_move := self.find_winning_move(1):
            return defense_move
        
        best_score = -math.inf
        best_move = (7,7)
        candidates = self.get_priority_candidates()
        
        for move in candidates[:12]:
            x, y = move
            self.board[x][y] = 2
            score = self.minimax(AI_DEPTH-1, -math.inf, math.inf, False)
            self.board[x][y] = 0
            if score > best_score:
                best_score = score
                best_move = (x, y)
            if score > 100000:
                break
        return best_move

    def minimax(self, depth, alpha, beta, maximizing):
        """优化后的搜索算法"""
        if depth == 0 or self.game_over:
            return self.evaluate_board()
        
        candidates = self.get_priority_candidates()
        if maximizing:
            max_score = -math.inf
            for (x,y) in candidates:
                self.board[x][y] = 2
                score = self.minimax(depth-1, alpha, beta, False)
                self.board[x][y] = 0
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = math.inf
            for (x,y) in candidates:
                self.board[x][y] = 1
                score = self.minimax(depth-1, alpha, beta, True)
                self.board[x][y] = 0
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score

    def get_priority_candidates(self):
        """生成优先候选列表"""
        candidates = set()
        # 获取所有邻近棋子两格内的空位
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] != 0:
                    for dx in range(-2,3):
                        for dy in range(-2,3):
                            if 0<=i+dx<BOARD_SIZE and 0<=j+dy<BOARD_SIZE:
                                if self.board[i+dx][j+dy] == 0:
                                    candidates.add((i+dx,j+dy))
        # 按威胁程度排序
        return sorted(candidates, key=lambda pos: self.position_value(pos), reverse=True)

    def position_value(self, pos):
        """位置价值评估"""
        x, y = pos
        value = 0
        for dx, dy in [(1,0),(0,1),(1,1),(1,-1)]:
            value += self.evaluate_line(x, y, dx, dy, 2)*2  # 进攻价值
            value += self.evaluate_line(x, y, dx, dy, 1)*1  # 防守价值
        return value

    def evaluate_line(self, x, y, dx, dy, player):
        """评估单方向棋型"""
        score = 0
        count = 1       # 当前假设落子后的连续数
        blocks = 0      # 阻挡数
        empty = 0       # 空位计数
        
        # 正向检测
        i, j = x+dx, y+dy
        while 0<=i<BOARD_SIZE and 0<=j<BOARD_SIZE:
            if self.board[i][j] == player:
                count +=1
            elif self.board[i][j] == 0:
                empty +=1
                break
            else:
                blocks +=1
                break
            i += dx
            j += dy
        
        # 反向检测
        i, j = x-dx, y-dy
        while 0<=i<BOARD_SIZE and 0<=j<BOARD_SIZE:
            if self.board[i][j] == player:
                count +=1
            elif self.board[i][j] == 0:
                empty +=1
                break
            else:
                blocks +=1
                break
            i -= dx
            j -= dy
        
        # 棋型判定
        if count >=5:
            return SCORE['five']
        if count ==4:
            if blocks ==0:
                return SCORE['live_four']
            if blocks ==1 and empty ==1:
                return SCORE['rush_four']
        if count ==3:
            if blocks ==0 and empty ==2:
                return SCORE['live_three']
            if blocks ==1 and empty ==1:
                return SCORE['rush_three']
        if count ==2:
            if blocks ==0 and empty ==2:
                return SCORE['live_two']
            if blocks ==1 and empty ==1:
                return SCORE['rush_two']
        return 0

    def find_winning_move(self, player):
        """立即获胜/防御检测"""
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.board[x][y] == 0:
                    self.board[x][y] = player
                    if self.check_win(x, y, player):
                        self.board[x][y] = 0
                        return (x, y)
                    self.board[x][y] = 0
        return None

    def evaluate_board(self):
        """综合评估棋盘（修复错误调用）"""
        score = 0
        # 优先检查特殊棋型
        score += self.find_special_pattern(2)*10  # 进攻
        score -= self.find_special_pattern(1)*8   # 防守
        return score

    def find_special_pattern(self, player):
        """检测双活三、冲四等特殊棋型（修复缺失方法问题）"""
        score = 0
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.board[x][y] == player:
                    # 简单版双活三检测（实际项目需要更复杂实现）
                    three_count = 0
                    for dx, dy in [(1,0),(0,1),(1,1),(1,-1)]:
                        line_score = self.evaluate_line(x, y, dx, dy, player)
                        if line_score == SCORE['live_three']:
                            three_count += 1
                    if three_count >= 2:
                        score += 50000
        return score

    def check_win(self, x, y, player):
        """增强胜利检查"""
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in directions:
            count = 1
            # 正向检测
            i, j = x+dx, y+dy
            while 0<=i<BOARD_SIZE and 0<=j<BOARD_SIZE and self.board[i][j]==player:
                count +=1
                i += dx
                j += dy
            # 反向检测
            i, j = x-dx, y-dy
            while 0<=i<BOARD_SIZE and 0<=j<BOARD_SIZE and self.board[i][j]==player:
                count +=1
                i -= dx
                j -= dy
            if count >=5:
                return True
        return False

def show_setup_window():
    """显示增强的设置窗口"""
    setup_win = tk.Tk()
    setup_win.title("游戏设置")
    setup_win.configure(bg=COLORS['bg'])
    
    # 标题（增加图标）
    ttk.Label(setup_win, text="⚫ 五子棋 ⚪", 
             font=('微软雅黑', 18), 
             background=COLORS['bg'], 
             foreground='white').pack(pady=15)
    
    # 模式选择卡片
    card_frame = ttk.Frame(setup_win, style='Dark.TFrame')
    card_frame.pack(pady=10, padx=20, fill='x')
    
    ttk.Label(card_frame, text="游戏模式:").pack(side='left')
    mode_var = tk.StringVar(value='ai')
    ttk.Radiobutton(card_frame, text="人机对战", 
                   variable=mode_var, value='ai').pack(side='left', padx=10)
    ttk.Radiobutton(card_frame, text="双人对战", 
                   variable=mode_var, value='pvp').pack(side='left')
    
    # 先手选择卡片
    card_frame2 = ttk.Frame(setup_win, style='Dark.TFrame')
    card_frame2.pack(pady=10, padx=20, fill='x')
    
    ttk.Label(card_frame2, text="先手方:").pack(side='left')
    first_var = tk.IntVar(value=1)
    ttk.Radiobutton(card_frame2, text="玩家", 
                   variable=first_var, value=1).pack(side='left', padx=10)
    ttk.Radiobutton(card_frame2, text="AI", 
                   variable=first_var, value=2).pack(side='left')
    
    # 开始按钮（美化）
    start_btn = ttk.Button(setup_win, text="开始游戏", 
                          style='Gold.TButton', 
                          command=lambda: start_game())
    start_btn.pack(pady=20, ipadx=20, ipady=8)
    
    def start_game():
        setup_win.destroy()
        root = tk.Tk()
        GobangGame(root, mode=mode_var.get(), first_player=first_var.get())
        root.mainloop()
    
    # 样式配置
    style = ttk.Style()
    style.configure('Dark.TFrame', background=COLORS['bg'])
    style.configure('TRadiobutton', background=COLORS['bg'], foreground='white')
    style.configure('Gold.TButton', 
                   font=('微软雅黑', 12),
                   foreground='black',
                   background='#FFD700')
    
    setup_win.mainloop()

if __name__ == "__main__":
    show_setup_window()