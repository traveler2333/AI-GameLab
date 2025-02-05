# 🎮 AI-GameLab [![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

<div align="center">
  <img src="https://64.media.tumblr.com/85e28b2c1364a2084bd7a6727add810a/bf7dea713bb52297-ac/s1280x1920/0f03a27d7d10f150b8abba46376358eb72e1bd89.gif" width="400">
</div>

下一代智能小游戏集合库，融合：
- 🤖 **强化学习AI对手**
- 🎨 **现代化交互界面**
- 📊 **实时对战数据可视化**
- 🚀 **模块化游戏架构**

## 🌟 特色项目展示
### 🎮智能五子棋 Gobang AI [![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)


#### 🌟 功能特性
- 🧠 基于Alpha-Beta剪枝的AI引擎 
- 🎨 现代化棋盘界面
- ⚡ 实时落子反馈
- 🎯 AI最后落子标记

#### 🚀 快速开始
```bash
git clone https://github.com/yourname/AI-GameLab
cd AI-GameLab
python main.py
```

#### 🛠️ 技术实现
**核心算法**
```python
def minimax(self, depth, alpha, beta, maximizing):
    # Alpha-Beta剪枝实现
    if maximizing:
        max_eval = -math.inf
        for (x,y) in candidates:
            self.board[x][y] = 2
            eval = self.minimax(depth-1, alpha, beta, False)
            self.board[x][y] = 0
            if eval > max_eval:
                max_eval = eval
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # 剪枝
        return max_eval
```

**棋型评估**
| 棋型       | 权重     | 说明               |
|------------|----------|--------------------|
| 连五       | 10,000,000 | 直接获胜           |
| 活四       | 500,000  | 无阻挡四连         |
| 冲四       | 100,000  | 单边阻挡四连       |


#### 📜 依赖环境
```requirements.txt
tkinter
math
```

## 🤝 参与贡献
欢迎提交Issue或PR，遵循MIT开源协议