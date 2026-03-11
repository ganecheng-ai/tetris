# 俄罗斯方块 - Tetris

经典的俄罗斯方块游戏，使用 Python 和 Pygame 开发。

## 游戏特性

- 精美的游戏界面和方块设计
- 10 个关卡，难度递增
- 简体中文界面
- 经典操作方式
- 影子方块提示
- 下一个方块预览

## 关卡系统

| 关卡 | 名称 | 速度 (ms) | 消除行数 |
|------|------|-----------|----------|
| 1 | 初学者 | 1000 | 10 |
| 2 | 新手 | 900 | 20 |
| 3 | 入门 | 800 | 30 |
| 4 | 熟练 | 700 | 40 |
| 5 | 进阶 | 600 | 50 |
| 6 | 高手 | 500 | 60 |
| 7 | 专家 | 400 | 70 |
| 8 | 大师 | 300 | 80 |
| 9 | 传奇 | 200 | 90 |
| 10 | 方块之王 | 100 | 100 |

## 操作说明

- **← →** - 左右移动
- **↑** - 旋转方块
- **↓** - 软降（加速下落）
- **空格** - 硬降（直接落底）
- **P** - 暂停/继续
- **R** - 重新开始

## 安装和运行

### 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行游戏
python tetris.py
```

### 使用可执行文件

从 [Releases](https://github.com/ganecheng-ai/tetris/releases) 页面下载对应平台的可执行文件：
- Windows: `Tetris.exe`
- macOS: `Tetris`
- Linux: `Tetris`

## 开发

### 构建可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Tetris tetris.py
```

## 技术栈

- Python 3.11+
- Pygame 2.5+
- PyInstaller（用于打包）

## 许可证

MIT License
