"""
俄罗斯方块游戏 - Tetris Game
A classic Tetris game with 10 levels and Chinese interface

Version: 1.1.0
Features:
  - 10 levels with increasing difficulty
  - Chinese interface
  - Sound effects
  - High score system
"""

import pygame
import random
import sys
import os
import json

# 初始化 pygame
pygame.init()
pygame.font.init()

# 游戏常量
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 12)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)

# 方块颜色 (鲜艳的渐变色)
COLORS = {
    'I': (0, 255, 255),      # 青色
    'O': (255, 255, 0),      # 黄色
    'T': (128, 0, 255),      # 紫色
    'S': (0, 255, 0),        # 绿色
    'Z': (255, 0, 0),        # 红色
    'J': (0, 0, 255),        # 蓝色
    'L': (255, 165, 0),      # 橙色
}

# 音效配置
SOUND_ENABLED = True
SOUND_VOLUME = 0.3

# 最高分记录文件
HIGH_SCORE_FILE = 'highscore.json'

# 方块形状定义
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]],
}

# 关卡配置 (速度，每关消除行数要求)
LEVELS = [
    {'level': 1, 'speed': 1000, 'lines': 10, 'name': '初学者'},
    {'level': 2, 'speed': 900, 'lines': 20, 'name': '新手'},
    {'level': 3, 'speed': 800, 'lines': 30, 'name': '入门'},
    {'level': 4, 'speed': 700, 'lines': 40, 'name': '熟练'},
    {'level': 5, 'speed': 600, 'lines': 50, 'name': '进阶'},
    {'level': 6, 'speed': 500, 'lines': 60, 'name': '高手'},
    {'level': 7, 'speed': 400, 'lines': 70, 'name': '专家'},
    {'level': 8, 'speed': 300, 'lines': 80, 'name': '大师'},
    {'level': 9, 'speed': 200, 'lines': 90, 'name': '传奇'},
    {'level': 10, 'speed': 100, 'lines': 100, 'name': '方块之王'},
]


class SoundManager:
    """音效管理器"""

    def __init__(self):
        self.enabled = SOUND_ENABLED
        self.sounds = {}
        self.music_loaded = False

        if self.enabled:
            pygame.mixer.init()
            self._init_sounds()

    def _init_sounds(self):
        """初始化音效（使用程序生成的声音）"""
        try:
            # 使用 pygame 生成简单的音效
            sample_rate = 22050

            # 硬降音效 - 高频短音
            self.sounds['drop'] = self._generate_sound(400, 0.1, 'square')

            # 消行音效 - 和弦效果
            self.sounds['clear'] = self._generate_sound(600, 0.2, 'sine')

            # 消多行音效 - 更长的音效
            self.sounds['clear_multi'] = self._generate_sound(800, 0.3, 'sine')

            # 旋转音效
            self.sounds['rotate'] = self._generate_sound(300, 0.05, 'sine')

            # 游戏结束音效
            self.sounds['gameover'] = self._generate_sound(200, 0.5, 'sawtooth')

            # 升级音效
            self.sounds['levelup'] = self._generate_sound(500, 0.4, 'sine')

            # 设置音量
            for sound in self.sounds.values():
                sound.set_volume(SOUND_VOLUME)

        except Exception as e:
            print(f"音效初始化失败：{e}")
            self.enabled = False

    def _generate_sound(self, freq, duration, wave_type='sine'):
        """生成简单音效"""
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            buf = bytes()

            for i in range(n_samples):
                t = i / sample_rate
                if wave_type == 'sine':
                    # 正弦波
                    value = int(127 * (0.5 * (1 + (2 * t / duration) ** 0.5)) *
                               (2 * t * freq * 3.14159) % 256)
                elif wave_type == 'square':
                    # 方波
                    value = 255 if (int(t * freq * 2) % 2) == 0 else 0
                elif wave_type == 'sawtooth':
                    # 锯齿波
                    value = int(255 * (t * freq % 1))
                else:
                    value = 128

                # 添加包络（淡入淡出）
                envelope = 1.0
                if i < n_samples * 0.1:
                    envelope = i / (n_samples * 0.1)
                elif i > n_samples * 0.8:
                    envelope = (n_samples - i) / (n_samples * 0.2)

                value = int(value * envelope)
                buf += bytes([value])

            # 创建单声道声音
            sound = pygame.mixer.Sound(buffer=buf)
            return sound
        except Exception:
            # 如果生成失败，返回一个空音效
            return pygame.mixer.Sound(buffer=bytes([128] * 100))

    def play(self, sound_name):
        """播放音效"""
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def play_clear(self, lines):
        """根据消除行数播放不同音效"""
        if lines >= 2:
            self.play('clear_multi')
        else:
            self.play('clear')

    def stop_music(self):
        """停止背景音乐"""
        if self.enabled:
            pygame.mixer.music.stop()


class HighScoreManager:
    """最高分记录管理器"""

    def __init__(self):
        self.high_scores = self._load_high_scores()

    def _get_file_path(self):
        """获取最高分文件路径"""
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            return os.path.join(os.path.dirname(sys.executable), HIGH_SCORE_FILE)
        else:
            # 开发环境路径
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), HIGH_SCORE_FILE)

    def _load_high_scores(self):
        """加载最高分记录"""
        try:
            file_path = self._get_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('high_scores', [])
            else:
                return []
        except Exception as e:
            print(f"加载最高分失败：{e}")
            return []

    def save_high_scores(self):
        """保存最高分记录"""
        try:
            file_path = self._get_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'high_scores': self.high_scores}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存最高分失败：{e}")
            return False

    def add_score(self, score, lines, level):
        """添加新的分数记录"""
        entry = {
            'score': score,
            'lines': lines,
            'level': level,
            'date': pygame.time.get_ticks() // 1000
        }

        self.high_scores.append(entry)

        # 按分数排序，保留前 10 名
        self.high_scores.sort(key=lambda x: x['score'], reverse=True)
        self.high_scores = self.high_scores[:10]

        self.save_high_scores()

        # 返回是否进入排行榜
        return len(self.high_scores) > 0 and self.high_scores[-1] == entry

    def get_high_scores(self):
        """获取最高分列表"""
        return self.high_scores

    def get_high_score(self):
        """获取最高分"""
        if self.high_scores:
            return self.high_scores[0]['score']
        return 0


class Block:
    """方块类"""

    def __init__(self, shape_type=None):
        if shape_type is None:
            shape_type = random.choice(list(SHAPES.keys()))
        self.shape_type = shape_type
        self.shape = [row[:] for row in SHAPES[shape_type]]
        self.color = COLORS[shape_type]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        """顺时针旋转方块"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[self.shape[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]
        return rotated


class GameBoard:
    """游戏棋盘类"""

    def __init__(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    def is_valid_position(self, block, offset_x=0, offset_y=0):
        """检查方块位置是否有效"""
        for y, row in enumerate(block.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = block.x + x + offset_x
                    new_y = block.y + y + offset_y
                    if new_x < 0 or new_x >= GRID_WIDTH:
                        return False
                    if new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x] is not None:
                        return False
        return True

    def lock_block(self, block):
        """锁定方块到棋盘"""
        for y, row in enumerate(block.shape):
            for x, cell in enumerate(row):
                if cell:
                    board_y = block.y + y
                    board_x = block.x + x
                    if 0 <= board_y < GRID_HEIGHT and 0 <= board_x < GRID_WIDTH:
                        self.grid[board_y][board_x] = block.color

    def clear_lines(self):
        """清除满行并返回消除的行数"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
                lines_cleared += 1
            else:
                y -= 1
        return lines_cleared

    def is_game_over(self):
        """检查游戏是否结束"""
        return not self.is_valid_position(Block())

    def get_ghost_y(self, block):
        """获取方块的影子位置"""
        ghost_y = block.y
        while self.is_valid_position(block, offset_x=0, offset_y=ghost_y - block.y + 1):
            ghost_y += 1
        return ghost_y


class TetrisGame:
    """游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('俄罗斯方块 - Tetris')

        # 加载中文字体
        self.font_large = self._load_font(36)
        self.font_medium = self._load_font(24)
        self.font_small = self._load_font(18)

        # 初始化管理器
        self.sound_manager = SoundManager()
        self.high_score_manager = HighScoreManager()

        self.clock = pygame.time.Clock()
        self.reset_game()

    def _load_font(self, size):
        """加载字体，优先使用支持中文的字体"""
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',  # Windows 宋体
            'C:/Windows/Fonts/msyh.ttc',     # Windows 微软雅黑
            '/System/Library/Fonts/PingFang.ttc',  # macOS 苹方
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Linux 文泉驿
        ]
        for path in font_paths:
            try:
                return pygame.font.Font(path, size)
            except:
                continue
        # 回退到默认字体
        return pygame.font.SysFont('arial', size)

    def reset_game(self):
        """重置游戏状态"""
        self.board = GameBoard()
        self.current_block = Block()
        self.next_block = Block()
        self.score = 0
        self.lines_cleared = 0
        self.level_index = 0
        self.level_lines = 0
        self.game_over = False
        self.paused = False
        self.last_fall_time = pygame.time.get_ticks()
        self.running = True
        self.new_high_score = False  # 标记是否创造新高分

    def spawn_block(self):
        """生成新方块"""
        self.current_block = self.next_block
        self.next_block = Block()
        self.current_block.x = GRID_WIDTH // 2 - len(self.current_block.shape[0]) // 2
        self.current_block.y = 0

        if not self.board.is_valid_position(self.current_block):
            self.game_over = True
            self.sound_manager.play('gameover')  # 播放游戏结束音效
            # 记录最高分
            self.high_score_manager.add_score(self.score, self.lines_cleared, self.level_index + 1)
            if self.score > self.high_score_manager.get_high_score():
                self.new_high_score = True

    def move_block(self, dx, dy):
        """移动方块"""
        if self.board.is_valid_position(self.current_block, offset_x=dx, offset_y=dy):
            self.current_block.x += dx
            self.current_block.y += dy
            return True
        return False

    def rotate_block(self):
        """旋转方块"""
        original_shape = self.current_block.shape
        self.current_block.shape = self.current_block.rotate()

        # 墙踢检测
        if not self.board.is_valid_position(self.current_block):
            if self.board.is_valid_position(self.current_block, offset_x=-1, offset_y=0):
                self.current_block.x -= 1
            elif self.board.is_valid_position(self.current_block, offset_x=1, offset_y=0):
                self.current_block.x += 1
            elif self.board.is_valid_position(self.current_block, offset_x=-2, offset_y=0):
                self.current_block.x -= 2
            elif self.board.is_valid_position(self.current_block, offset_x=2, offset_y=0):
                self.current_block.x += 2
            else:
                self.current_block.shape = original_shape
                return  # 旋转失败，不播放音效

        self.sound_manager.play('rotate')

    def hard_drop(self):
        """硬降方块"""
        while self.move_block(0, 1):
            self.score += 2
        self.sound_manager.play('drop')
        self.lock_current_block()

    def lock_current_block(self):
        """锁定当前方块"""
        self.board.lock_block(self.current_block)
        lines = self.board.clear_lines()

        if lines > 0:
            self.lines_cleared += lines
            self.level_lines += lines

            # 播放消行音效
            self.sound_manager.play_clear(lines)

            # 计分
            line_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += line_scores.get(lines, 0) * (self.level_index + 1)

            # 检查升级
            self._check_level_up()

        self.spawn_block()

    def _check_level_up(self):
        """检查是否升级"""
        current_level = LEVELS[self.level_index]
        if self.level_lines >= current_level['lines']:
            if self.level_index < len(LEVELS) - 1:
                self.level_index += 1
                self.level_lines = 0
                self.sound_manager.play('levelup')  # 播放升级音效

    def get_current_speed(self):
        """获取当前下落速度"""
        return LEVELS[self.level_index]['speed']

    def draw_block(self, block, offset_x=0, offset_y=0, ghost=False):
        """绘制方块"""
        for y, row in enumerate(block.shape):
            for x, cell in enumerate(row):
                if cell:
                    draw_x = (block.x + x + offset_x) * BLOCK_SIZE
                    draw_y = (block.y + y + offset_y) * BLOCK_SIZE

                    if ghost:
                        # 影子方块
                        pygame.draw.rect(self.screen, block.color,
                                       (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2), 2)
                    else:
                        # 实体方块 - 带渐变效果
                        color = block.color if not ghost else tuple(c // 4 for c in block.color)
                        pygame.draw.rect(self.screen, color,
                                       (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))
                        # 高光效果
                        highlight = tuple(min(255, c + 50) for c in color)
                        pygame.draw.line(self.screen, highlight,
                                       (draw_x + 2, draw_y + 2),
                                       (draw_x + BLOCK_SIZE - 3, draw_y + 2), 2)
                        pygame.draw.line(self.screen, highlight,
                                       (draw_x + 2, draw_y + 2),
                                       (draw_x + 2, draw_y + BLOCK_SIZE - 3), 2)

    def draw_grid(self):
        """绘制游戏网格"""
        # 绘制背景
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (0, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))

        # 绘制网格线
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, GRAY,
                           (x * BLOCK_SIZE, 0),
                           (x * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, GRAY,
                           (0, y * BLOCK_SIZE),
                           (GRID_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE))

        # 绘制已锁定的方块
        for y, row in enumerate(self.board.grid):
            for x, color in enumerate(row):
                if color:
                    draw_x = x * BLOCK_SIZE
                    draw_y = y * BLOCK_SIZE
                    pygame.draw.rect(self.screen, color,
                                   (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))
                    # 高光效果
                    highlight = tuple(min(255, c + 50) for c in color)
                    pygame.draw.line(self.screen, highlight,
                                   (draw_x + 2, draw_y + 2),
                                   (draw_x + BLOCK_SIZE - 3, draw_y + 2), 2)
                    pygame.draw.line(self.screen, highlight,
                                   (draw_x + 2, draw_y + 2),
                                   (draw_x + 2, draw_y + BLOCK_SIZE - 3), 2)

    def draw_ui(self):
        """绘制 UI 信息"""
        ui_x = GRID_WIDTH * BLOCK_SIZE + 20

        # 标题
        title = self.font_large.render('俄罗斯方块', True, WHITE)
        self.screen.blit(title, (ui_x, 20))

        # 最高分
        high_score = self.high_score_manager.get_high_score()
        high_score_text = self.font_small.render(f'最高分：{high_score}', True, (255, 215, 0))
        self.screen.blit(high_score_text, (ui_x, 55))

        # 下一个方块
        next_text = self.font_medium.render('下一个:', True, WHITE)
        self.screen.blit(next_text, (ui_x, 85))

        # 绘制下一个方块预览
        preview_x = ui_x
        preview_y = 100
        for y, row in enumerate(self.next_block.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_block.color,
                                   (preview_x + x * BLOCK_SIZE,
                                    preview_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 分数
        score_text = self.font_medium.render(f'分数：{self.score}', True, WHITE)
        self.screen.blit(score_text, (ui_x, 220))

        # 消除行数
        lines_text = self.font_medium.render(f'消除：{self.lines_cleared}', True, WHITE)
        self.screen.blit(lines_text, (ui_x, 260))

        # 关卡
        current_level = LEVELS[self.level_index]
        level_text = self.font_medium.render(f'关卡：{current_level["name"]}', True, WHITE)
        self.screen.blit(level_text, (ui_x, 300))

        # 升级进度
        progress = f'{self.level_lines}/{current_level["lines"]}'
        progress_text = self.font_small.render(f'升级：{progress}', True, WHITE)
        self.screen.blit(progress_text, (ui_x, 340))

        # 操作说明
        controls = [
            '操作说明:',
            '← → 移动',
            '↑ 旋转',
            '↓ 软降',
            '空格 硬降',
            'P 暂停',
            'R 重新开始',
        ]
        for i, text in enumerate(controls):
            rendered = self.font_small.render(text, True, GRAY)
            self.screen.blit(rendered, (ui_x, 380 + i * 25))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font_large.render('游戏结束', True, WHITE)
        score_text = self.font_medium.render(f'最终分数：{self.score}', True, WHITE)
        restart_text = self.font_medium.render('按 R 重新开始', True, WHITE)

        self.screen.blit(game_over_text,
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(score_text,
                        (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 30))

        # 显示最高分
        high_score = self.high_score_manager.get_high_score()
        high_score_text = self.font_small.render(f'最高分：{high_score}', True, WHITE)
        self.screen.blit(high_score_text,
                        (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 + 10))

        # 新高分提示
        if self.new_high_score:
            new_record_text = self.font_medium.render('新纪录!', True, (255, 215, 0))
            self.screen.blit(new_record_text,
                            (SCREEN_WIDTH // 2 - new_record_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 40))
            self.screen.blit(restart_text,
                            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 80))
        else:
            self.screen.blit(restart_text,
                            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 50))

    def draw_pause(self):
        """绘制暂停画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(120)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render('游戏暂停', True, WHITE)
        self.screen.blit(pause_text,
                        (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                         SCREEN_HEIGHT // 2))

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)

        # 绘制游戏区域
        self.draw_grid()

        # 绘制影子方块
        if not self.game_over:
            ghost_y = self.board.get_ghost_y(self.current_block)
            self.draw_block(self.current_block, offset_y=ghost_y - self.current_block.y, ghost=True)

            # 绘制当前方块
            self.draw_block(self.current_block)

        # 绘制 UI
        self.draw_ui()

        # 绘制游戏结束或暂停画面
        if self.game_over:
            self.draw_game_over()
        elif self.paused:
            self.draw_pause()

        pygame.display.flip()

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                    return

                if self.game_over or self.paused:
                    continue

                if event.key == pygame.K_p:
                    self.paused = True
                elif event.key == pygame.K_LEFT:
                    self.move_block(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_block(1, 0)
                elif event.key == pygame.K_DOWN:
                    if self.move_block(0, 1):
                        self.score += 1
                elif event.key == pygame.K_UP:
                    self.rotate_block()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = False

    def update(self):
        """更新游戏状态"""
        if self.game_over or self.paused:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_fall_time > self.get_current_speed():
            self.last_fall_time = current_time

            if not self.move_block(0, 1):
                self.lock_current_block()

    def run(self):
        """游戏主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    """主函数"""
    game = TetrisGame()
    game.run()


if __name__ == '__main__':
    main()
