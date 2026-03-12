"""
俄罗斯方块游戏 - Tetris Game
A classic Tetris game with 10 levels and Chinese interface

Version: 2.6.0
Features:
  - 10 levels with increasing difficulty
  - Chinese interface
  - Sound effects
  - High score system
  - Line clear animations
  - Level up effects
  - Multiple game themes
  - Hold block feature
  - Combo system
  - Local 2-player versus mode
  - Endless mode, Sprint mode, Ultra mode
  - Block skin system
  - Particle effects system
  - Music playlist system
  - Statistics and achievements
  - Enhanced line clear animations with explosions
  - Background particle effects
  - Unlockable block skins
  - Online leaderboard and cloud save (v2.4.0)
  - More game modes: Master, Zen, Challenge, Custom (v2.5.0)
"""

import pygame
import random
import sys
import os
import json
import math

# 初始化 pygame
pygame.init()
pygame.font.init()

# 游戏常量
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 12)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# 双人模式常量
DUAL_BLOCK_SIZE = 25
DUAL_GRID_WIDTH = 10
DUAL_GRID_HEIGHT = 20
DUAL_SCREEN_WIDTH = DUAL_BLOCK_SIZE * (DUAL_GRID_WIDTH * 2 + 8)
DUAL_SCREEN_HEIGHT = DUAL_BLOCK_SIZE * DUAL_GRID_HEIGHT

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
MUSIC_VOLUME = 0.5

# 音量设置文件
VOLUME_SETTINGS_FILE = 'volume_settings.json'

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


class Particle:
    """粒子类 - 用于华丽的视觉效果"""

    def __init__(self, x, y, color, vx=None, vy=None, life=60, size=3, gravity=0.5):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-5, -1)
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.alpha = 255

    def update(self):
        """更新粒子状态"""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.alpha = int(255 * (self.life / self.max_life))
        return self.life > 0

    def draw(self, screen):
        """绘制粒子"""
        if self.life > 0:
            # 创建半透明表面
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, self.alpha)
            pygame.draw.circle(s, color_with_alpha, (self.size, self.size), self.size)
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class Explosion:
    """爆炸效果类 - 用于消行时的华丽效果"""

    def __init__(self, x, y, color, particle_count=15):
        self.particles = []
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(2, 5)
            life = random.randint(30, 50)
            self.particles.append(Particle(x, y, color, vx, vy, life, size))

    def update(self):
        """更新爆炸效果"""
        self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0

    def draw(self, screen):
        """绘制爆炸效果"""
        for particle in self.particles:
            particle.draw(screen)

# 游戏模式
GAME_MODES = {
    'classic': {'name': '经典模式', 'desc': '10 个关卡挑战'},
    'endless': {'name': '无尽模式', 'desc': '无限挑战，速度越来越快'},
    'sprint': {'name': '竞速模式', 'desc': '尽快消除 40 行'},
    'ultra': {'name': '限时模式', 'desc': '2 分钟内获得最高分'},
    'master': {'name': '大师模式', 'desc': '20 层关卡，极限挑战'},
    'zen': {'name': '禅模式', 'desc': '无压力，放松体验'},
    'challenge': {'name': '挑战模式', 'desc': '特殊规则挑战'},
    'custom': {'name': '自定义模式', 'desc': '自定义游戏规则'},
}

# 无尽模式配置
ENDLESS_SPEEDS = [800, 700, 600, 500, 400, 300, 200, 150, 100, 80, 60, 50, 40, 30, 20]

# 方块皮肤配置
BLOCK_SKINS = {
    'default': {
        'name': '经典',
        'colors': COLORS,
        'unlock_condition': None,  # 默认解锁
    },
    'neon': {
        'name': '霓虹',
        'colors': {
            'I': (0, 255, 255),
            'O': (255, 255, 0),
            'T': (180, 0, 255),
            'S': (0, 255, 100),
            'Z': (255, 50, 50),
            'J': (50, 100, 255),
            'L': (255, 120, 0),
        },
        'unlock_condition': {'type': 'score', 'value': 5000},
    },
    'pastel': {
        'name': '粉色',
        'colors': {
            'I': (173, 216, 230),
            'O': (255, 218, 185),
            'T': (221, 160, 221),
            'S': (144, 238, 144),
            'Z': (255, 182, 193),
            'J': (176, 196, 222),
            'L': (255, 228, 181),
        },
        'unlock_condition': {'type': 'lines', 'value': 50},
    },
    'gold': {
        'name': '黄金',
        'colors': {
            'I': (255, 215, 0),
            'O': (255, 223, 100),
            'T': (255, 200, 50),
            'S': (255, 230, 150),
            'Z': (255, 180, 0),
            'J': (255, 210, 80),
            'L': (255, 190, 30),
        },
        'unlock_condition': {'type': 'level', 'value': 5},
    },
    'ice': {
        'name': '冰雪',
        'colors': {
            'I': (135, 206, 250),
            'O': (173, 216, 230),
            'T': (100, 149, 237),
            'S': (64, 224, 208),
            'Z': (70, 130, 180),
            'J': (30, 144, 255),
            'L': (0, 191, 255),
        },
        'unlock_condition': {'type': 'score', 'value': 10000},
    },
    'fire': {
        'name': '火焰',
        'colors': {
            'I': (255, 69, 0),
            'O': (255, 140, 0),
            'T': (255, 99, 71),
            'S': (255, 165, 0),
            'Z': (255, 50, 50),
            'J': (220, 20, 60),
            'L': (255, 80, 0),
        },
        'unlock_condition': {'type': 'lines', 'value': 100},
    },
    'forest': {
        'name': '森林',
        'colors': {
            'I': (34, 139, 34),
            'O': (154, 205, 50),
            'T': (107, 142, 35),
            'S': (50, 205, 50),
            'Z': (0, 100, 0),
            'J': (46, 139, 87),
            'L': (60, 179, 113),
        },
        'unlock_condition': {'type': 'level', 'value': 10},
    },
    'rainbow': {
        'name': '彩虹',
        'colors': {
            'I': (255, 0, 0),
            'O': (255, 127, 0),
            'T': (255, 255, 0),
            'S': (0, 255, 0),
            'Z': (0, 0, 255),
            'J': (75, 0, 130),
            'L': (148, 0, 211),
        },
        'unlock_condition': {'type': 'combo', 'value': 15},
    },
    'crystal': {
        'name': '水晶',
        'colors': {
            'I': (224, 176, 255),
            'O': (255, 224, 176),
            'T': (176, 224, 255),
            'S': (176, 255, 224),
            'Z': (255, 176, 224),
            'J': (224, 255, 176),
            'L': (255, 176, 176),
        },
        'unlock_condition': {'type': 'tetris', 'value': 10},
    },
}

# 支持的皮肤列表
SUPPORTED_SKINS = list(BLOCK_SKINS.keys())

# 游戏主题配置
THEMES = {
    'classic': {
        'name': '经典',
        'bg_color': (0, 0, 0),
        'grid_color': (64, 64, 64),
        'grid_line_color': (40, 40, 40),
        'ui_bg': (0, 0, 0),
        'text_color': (255, 255, 255),
        'accent_color': (255, 215, 0),
        'block_style': 'gradient',
    },
    'dark': {
        'name': '暗黑',
        'bg_color': (20, 20, 30),
        'grid_color': (30, 30, 45),
        'grid_line_color': (40, 40, 60),
        'ui_bg': (20, 20, 30),
        'text_color': (200, 200, 220),
        'accent_color': (255, 100, 100),
        'block_style': 'flat',
    },
    'light': {
        'name': '明亮',
        'bg_color': (240, 240, 250),
        'grid_color': (200, 200, 220),
        'grid_line_color': (180, 180, 200),
        'ui_bg': (240, 240, 250),
        'text_color': (40, 40, 60),
        'accent_color': (255, 140, 0),
        'block_style': 'outline',
    },
    'neon': {
        'name': '霓虹',
        'bg_color': (10, 10, 30),
        'grid_color': (20, 20, 50),
        'grid_line_color': (50, 50, 100),
        'ui_bg': (10, 10, 30),
        'text_color': (0, 255, 255),
        'accent_color': (255, 0, 255),
        'block_style': 'neon',
    },
}

# 消行动画帧数
CLEAR_ANIMATION_FRAMES = 20

# 升级动画帧数
LEVELUP_ANIMATION_FRAMES = 60

# 粒子效果最大数量
MAX_PARTICLES = 200

# 背景动画帧率
BG_ANIMATION_FPS = 60

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

# 大师模式关卡配置 (20 层，速度更快)
MASTER_LEVELS = [
    {'level': 1, 'speed': 800, 'lines': 5, 'name': '新手'},
    {'level': 2, 'speed': 700, 'lines': 10, 'name': '入门'},
    {'level': 3, 'speed': 600, 'lines': 15, 'name': '熟练'},
    {'level': 4, 'speed': 500, 'lines': 20, 'name': '进阶'},
    {'level': 5, 'speed': 400, 'lines': 25, 'name': '高手'},
    {'level': 6, 'speed': 300, 'lines': 30, 'name': '专家'},
    {'level': 7, 'speed': 250, 'lines': 35, 'name': '大师'},
    {'level': 8, 'speed': 200, 'lines': 40, 'name': '宗师'},
    {'level': 9, 'speed': 150, 'lines': 45, 'name': '传奇'},
    {'level': 10, 'speed': 100, 'lines': 50, 'name': '方块大师'},
    {'level': 11, 'speed': 80, 'lines': 55, 'name': '方块宗师'},
    {'level': 12, 'speed': 70, 'lines': 60, 'name': '方块传奇'},
    {'level': 13, 'speed': 60, 'lines': 65, 'name': '方块之神'},
    {'level': 14, 'speed': 50, 'lines': 70, 'name': '方块圣者'},
    {'level': 15, 'speed': 45, 'lines': 75, 'name': '方块尊者'},
    {'level': 16, 'speed': 40, 'lines': 80, 'name': '方块王者'},
    {'level': 17, 'speed': 35, 'lines': 85, 'name': '方块帝王'},
    {'level': 18, 'speed': 30, 'lines': 90, 'name': '方块至尊'},
    {'level': 19, 'speed': 25, 'lines': 95, 'name': '方块圣人'},
    {'level': 20, 'speed': 20, 'lines': 100, 'name': '方块之神王'},
]

# 挑战模式配置
CHALLENGE_CONFIGS = {
    'no_hold': {'name': '无暂存', 'desc': '禁止使用暂存方块', 'hold_enabled': False},
    'no_shadow': {'name': '无影子', 'desc': '不显示影子方块', 'shadow_enabled': False},
    'blind': {'name': '盲目', 'desc': '不显示下一个方块', 'next_enabled': False},
    'gravity_up': {'name': '反向重力', 'desc': '方块从下往上出现', 'gravity_up': True},
    'fast_drop': {'name': '快速下落', 'desc': '方块自动快速下落', 'auto_drop': True},
    'random_spin': {'name': '随机旋转', 'desc': '旋转方向随机', 'random_spin': True},
}

# 自定义规则配置
CUSTOM_RULES_FILE = 'custom_rules.json'

DEFAULT_CUSTOM_RULES = {
    'hold_enabled': True,        # 是否启用暂存
    'shadow_enabled': True,      # 是否显示影子方块
    'next_enabled': True,        # 是否显示下一个方块
    'next_count': 3,             # 预显示方块数量
    'initial_level': 1,          # 初始关卡
    'max_level': 10,             # 最大关卡
    'gravity_type': 'normal',    # 重力类型：normal/fast/random
    'rotation_system': 'SRS',    # 旋转系统：SRS/ARS
    'bag_system': True,          # 是否使用 7-bag 随机系统
    'ghost_block': True,         # 是否显示影子方块
    'hard_drop_enabled': True,   # 是否允许硬降
    'soft_drop_enabled': True,   # 是否允许软降
    'wall_kick': True,           # 是否启用墙踢
    'infinite_spin': False,      # 是否允许无限旋转
    'combo_enabled': True,       # 是否启用连击系统
    'scoring_classic': False,    # 是否使用经典计分
    'target_lines': 100,         # 目标消除行数
    'time_limit': None,          # 时间限制（秒），None 表示无限制
    'garbage_enabled': False,    # 是否启用垃圾行（双人模式）
}


class CustomRulesManager:
    """自定义规则管理器"""

    def __init__(self):
        self.rules = DEFAULT_CUSTOM_RULES.copy()
        self._load_rules()

    def _load_rules(self):
        """加载自定义规则"""
        try:
            if os.path.exists(CUSTOM_RULES_FILE):
                with open(CUSTOM_RULES_FILE, 'r', encoding='utf-8') as f:
                    saved_rules = json.load(f)
                    self.rules.update(saved_rules)
        except Exception as e:
            print(f"加载自定义规则失败：{e}")

    def save_rules(self):
        """保存自定义规则"""
        try:
            with open(CUSTOM_RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存自定义规则失败：{e}")

    def reset_to_default(self):
        """重置为默认规则"""
        self.rules = DEFAULT_CUSTOM_RULES.copy()
        self.save_rules()

    def get_rule(self, key):
        """获取规则值"""
        return self.rules.get(key, DEFAULT_CUSTOM_RULES.get(key))

    def set_rule(self, key, value):
        """设置规则值"""
        if key in self.rules:
            self.rules[key] = value
            self.save_rules()

    def get_all_rules(self):
        """获取所有规则"""
        return self.rules.copy()


class SoundManager:
    """音效管理器 - 支持音效和背景音乐独立控制"""

    def __init__(self):
        self.enabled = SOUND_ENABLED
        self.sounds = {}
        self.music_loaded = False
        self.music_playing = False
        self.current_music_index = 0
        self.music_playlist = []

        # 独立音量控制
        self.sound_volume = SOUND_VOLUME
        self.music_volume = MUSIC_VOLUME

        # 加载音量设置
        self._load_volume_settings()

        if self.enabled:
            pygame.mixer.init()
            self._init_sounds()
            self._init_music_playlist()

    def _load_volume_settings(self):
        """加载音量设置"""
        try:
            if os.path.exists(VOLUME_SETTINGS_FILE):
                with open(VOLUME_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.sound_volume = settings.get('sound_volume', SOUND_VOLUME)
                    self.music_volume = settings.get('music_volume', MUSIC_VOLUME)
        except Exception as e:
            print(f"加载音量设置失败：{e}")

    def _save_volume_settings(self):
        """保存音量设置"""
        try:
            with open(VOLUME_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'sound_volume': self.sound_volume,
                    'music_volume': self.music_volume
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存音量设置失败：{e}")

    def set_sound_volume(self, volume):
        """设置音效音量 (0.0 - 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
        self._save_volume_settings()

    def set_music_volume(self, volume):
        """设置音乐音量 (0.0 - 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_playing:
            pygame.mixer.music.set_volume(self.music_volume)
        self._save_volume_settings()

    def toggle_music(self):
        """切换背景音乐播放"""
        if self.music_playing:
            self.stop_music()
        else:
            self.play_music()

    def _generate_music_track(self, track_id, duration=60):
        """生成背景音乐曲目（程序生成的电子音乐）"""
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            buf = bytes()

            # 不同曲目的音调和节奏
            track_scales = [
                [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],  # C 大调
                [293.66, 329.63, 369.99, 392.00, 440.00, 493.88, 587.33],  # D 大调
                [329.63, 369.99, 415.30, 440.00, 493.88, 554.37, 659.25],  # E 大调
                [277.18, 311.13, 349.23, 369.99, 415.30, 466.16, 554.37],  # 升 C 小调
            ]
            scale = track_scales[track_id % len(track_scales)]
            tempo = 90 + (track_id * 10)  # BPM

            for i in range(n_samples):
                t = i / sample_rate
                beat = (t * tempo / 60) % 1

                # 低音节奏（每拍）
                bass_freq = scale[0] / 2
                bass = 0.3 * (1 if (int(t * tempo / 60 * 4) % 2) == 0 else -1)

                # 和弦进行中音
                chord_idx = int(t * tempo / 60 / 4) % len(scale)
                chord_freq = scale[chord_idx]
                chord = 0.2 * (0.5 if beat < 0.5 else -0.5)

                # 高音旋律（随机但和谐）
                melody_freq = scale[(track_id + int(t * 2)) % len(scale)]
                melody = 0.15 * (0.3 if int(t * 8) % 2 == 0 else -0.3)

                # 组合所有音轨
                value = int(127 + 60 * (bass + chord + melody))
                value = max(0, min(255, value))

                # 包络（淡入淡出）
                if i < n_samples * 0.01:
                    value = int(127 + (value - 127) * (i / (n_samples * 0.01)))
                elif i > n_samples * 0.99:
                    value = int(127 + (value - 127) * ((n_samples - i) / (n_samples * 0.01)))

                buf += bytes([value])

            return buf
        except Exception as e:
            print(f"生成音乐失败：{e}")
            return bytes([128] * sample_rate)

    def _init_music_playlist(self):
        """初始化背景音乐播放列表"""
        try:
            # 生成多首背景音乐
            self.music_playlist = []
            for i in range(4):
                track_data = self._generate_music_track(i, duration=30)
                self.music_playlist.append(track_data)
            self.music_loaded = len(self.music_playlist) > 0
        except Exception as e:
            print(f"初始化音乐播放列表失败：{e}")
            self.music_loaded = False

    def _init_sounds(self):
        """初始化音效（使用程序生成的声音）"""
        try:
            # 使用 pygame 生成简单的音效
            sample_rate = 22050

            # 硬降音效 - 高频短音
            self.sounds['drop'] = self._generate_sound(400, 0.1, 'square')

            # 软降/放置音效
            self.sounds['place'] = self._generate_sound(350, 0.05, 'sine')

            # 消行音效 - 和弦效果
            self.sounds['clear'] = self._generate_sound(600, 0.2, 'sine')

            # 消多行音效 - 更长的音效
            self.sounds['clear_multi'] = self._generate_sound(800, 0.3, 'sine')

            # Tetris 消除（4 行）特殊音效
            self.sounds['tetris'] = self._generate_sound(1000, 0.5, 'sine')

            # 旋转音效
            self.sounds['rotate'] = self._generate_sound(300, 0.05, 'sine')

            # 旋转失败音效
            self.sounds['rotate_fail'] = self._generate_sound(200, 0.1, 'sawtooth')

            # 游戏结束音效
            self.sounds['gameover'] = self._generate_sound(200, 0.5, 'sawtooth')

            # 升级音效
            self.sounds['levelup'] = self._generate_sound(500, 0.4, 'sine')

            # 暂停音效
            self.sounds['pause'] = self._generate_sound(600, 0.15, 'sine')

            # 选择/确认音效
            self.sounds['select'] = self._generate_sound(700, 0.1, 'sine')

            # 连击音效
            self.sounds['combo'] = self._generate_sound(800, 0.2, 'sine')

            # 攻击音效（双人对战）
            self.sounds['attack'] = self._generate_sound(250, 0.3, 'sawtooth')

            # 垃圾行警告音效
            self.sounds['warning'] = self._generate_sound(180, 0.4, 'sawtooth')

            # 设置音量
            for sound in self.sounds.values():
                sound.set_volume(self.sound_volume)

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
        if lines >= 4:
            self.play('tetris')
        elif lines >= 2:
            self.play('clear_multi')
        else:
            self.play('clear')

    def play_music(self):
        """播放背景音乐"""
        if self.enabled and self.music_loaded and self.music_playlist:
            try:
                # 加载当前音乐轨道
                track_data = self.music_playlist[self.current_music_index]
                import io
                music_io = io.BytesIO(track_data)
                pygame.mixer.music.load(music_io)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play()
                self.music_playing = True
            except Exception as e:
                print(f"播放音乐失败：{e}")
                self.music_playing = False

    def stop_music(self):
        """停止背景音乐"""
        if self.enabled:
            pygame.mixer.music.stop()
            self.music_playing = False

    def next_music(self):
        """播放下一首音乐"""
        if self.music_playlist:
            self.current_music_index = (self.current_music_index + 1) % len(self.music_playlist)
            self.play_music()


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
                    # 支持旧格式
                    if isinstance(data, list):
                        return {'classic': data}
                    return data.get('modes', {'classic': []})
            else:
                return {'classic': []}
        except Exception as e:
            print(f"加载最高分失败：{e}")
            return {'classic': []}

    def save_high_scores(self):
        """保存最高分记录"""
        try:
            file_path = self._get_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'modes': self.high_scores}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存最高分失败：{e}")
            return False

    def add_score(self, score, lines, level, mode='classic', extra_data=None):
        """添加新的分数记录"""
        if mode not in self.high_scores:
            self.high_scores[mode] = []

        entry = {
            'score': score,
            'lines': lines,
            'level': level,
            'date': pygame.time.get_ticks() // 1000,
        }

        if extra_data:
            entry.update(extra_data)

        self.high_scores[mode].append(entry)

        # 按分数排序，保留前 10 名
        self.high_scores[mode].sort(key=lambda x: x['score'], reverse=True)
        self.high_scores[mode] = self.high_scores[mode][:10]

        self.save_high_scores()

        # 返回是否进入排行榜
        return len(self.high_scores[mode]) > 0 and self.high_scores[mode][-1] == entry

    def get_high_scores(self, mode='classic'):
        """获取最高分列表"""
        return self.high_scores.get(mode, [])

    def get_high_score(self, mode='classic'):
        """获取最高分"""
        scores = self.high_scores.get(mode, [])
        if scores:
            return scores[0]['score']
        return 0


# 成就定义
ACHIEVEMENTS = {
    'first_game': {'name': '初次尝试', 'desc': '完成第一局游戏', 'icon': '🎮'},
    'first_line': {'name': '首行消除', 'desc': '消除第一行', 'icon': '📏'},
    'tetris': {'name': '俄罗斯方块!', 'desc': '一次性消除 4 行', 'icon': '🎉'},
    'combo_5': {'name': '连击高手', 'desc': '达成 5 连击', 'icon': '🔥'},
    'combo_10': {'name': '连击大师', 'desc': '达成 10 连击', 'icon': '⚡'},
    'score_10000': {'name': '万分俱乐部', 'desc': '单局获得 10000 分', 'icon': '💎'},
    'level_5': {'name': '进阶玩家', 'desc': '达到第 5 关', 'icon': '🏆'},
    'level_10': {'name': '传奇玩家', 'desc': '达到第 10 关', 'icon': '👑'},
    'sprint_fast': {'name': '速度之星', 'desc': '竞速模式 60 秒内完成', 'icon': '🚀'},
    'endless_10': {'name': '持久战', 'desc': '无尽模式达到等级 10', 'icon': '∞'},
}

# 在线功能常量
ONLINE_CONFIG_FILE = 'online_config.json'
CLOUD_SAVE_FILE = 'cloud_save.json'
PLAYER_ID_FILE = 'player_id.json'

# 模拟在线排行榜数据（离线模式使用本地数据）
# 在实际在线模式中，这些数据会从服务器获取
ONLINE_LEADERBOARD_URL = 'https://example.com/api/leaderboard'  # 示例 URL


class OnlineLeaderboardManager:
    """在线排行榜管理器 - v2.4.0 新增"""

    def __init__(self):
        self.is_online = False
        self.player_id = None
        self.leaderboard_data = {}
        self._load_player_id()
        self._check_online_status()

    def _load_player_id(self):
        """加载或生成玩家 ID"""
        try:
            if os.path.exists(PLAYER_ID_FILE):
                with open(PLAYER_ID_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.player_id = data.get('player_id')
                    if not self.player_id:
                        self.player_id = self._generate_player_id()
                        self._save_player_id()
            else:
                self.player_id = self._generate_player_id()
                self._save_player_id()
        except Exception as e:
            print(f"加载玩家 ID 失败：{e}")
            self.player_id = self._generate_player_id()

    def _generate_player_id(self):
        """生成唯一玩家 ID"""
        import hashlib
        import time
        # 使用时间戳和随机数生成唯一 ID
        raw = f"{time.time()}_{random.randint(100000, 999999)}"
        return hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    def _save_player_id(self):
        """保存玩家 ID"""
        try:
            with open(PLAYER_ID_FILE, 'w', encoding='utf-8') as f:
                json.dump({'player_id': self.player_id}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存玩家 ID 失败：{e}")

    def _check_online_status(self):
        """检查网络状态"""
        try:
            import urllib.request
            urllib.request.urlopen('https://www.google.com', timeout=3)
            self.is_online = True
        except Exception:
            self.is_online = False

    def get_player_id(self):
        """获取玩家 ID"""
        return self.player_id

    def get_player_id_display(self):
        """获取用于显示的玩家 ID（脱敏）"""
        if self.player_id:
            return f"玩家#{self.player_id[:4]}****"
        return "未知玩家"

    def refresh_online_status(self):
        """刷新在线状态"""
        self._check_online_status()
        return self.is_online

    def upload_score(self, score, lines, level, mode='classic', extra_data=None):
        """上传分数到在线排行榜"""
        if not self.is_online:
            return False

        try:
            import urllib.request
            data = {
                'player_id': self.player_id,
                'score': score,
                'lines': lines,
                'level': level,
                'mode': mode,
                'timestamp': pygame.time.get_ticks() // 1000,
            }
            if extra_data:
                data.update(extra_data)

            req = urllib.request.Request(
                ONLINE_LEADERBOARD_URL + '/submit',
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"上传分数失败：{e}")
            self.is_online = False
            return False

    def download_leaderboard(self, mode='classic', limit=10):
        """下载排行榜数据"""
        if not self.is_online:
            return self._get_local_leaderboard(mode, limit)

        try:
            import urllib.request
            url = f"{ONLINE_LEADERBOARD_URL}?mode={mode}&limit={limit}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.leaderboard_data[mode] = data
                return data
        except Exception as e:
            print(f"下载排行榜失败：{e}")
            self.is_online = False
            return self._get_local_leaderboard(mode, limit)

    def _get_local_leaderboard(self, mode='classic', limit=10):
        """获取本地排行榜（离线模式）"""
        # 从本地最高分记录生成排行榜
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    modes_data = data.get('modes', {}) if isinstance(data, dict) else {'classic': data}
                    scores = modes_data.get(mode, [])
                    # 添加玩家 ID 信息
                    leaderboard = []
                    for i, entry in enumerate(scores[:limit]):
                        leaderboard.append({
                            'rank': i + 1,
                            'player_id': self.player_id,
                            'player_name': f'本地玩家{i+1}',
                            'score': entry.get('score', 0),
                            'lines': entry.get('lines', 0),
                            'level': entry.get('level', 1),
                            'date': entry.get('date', 0),
                            'is_local': True,
                        })
                    return leaderboard
        except Exception as e:
            print(f"获取本地排行榜失败：{e}")
        return []

    def get_online_status(self):
        """获取在线状态"""
        return self.is_online


class CloudSaveManager:
    """云端存档管理器 - v2.4.0 新增"""

    def __init__(self, online_manager):
        self.online_manager = online_manager
        self.local_save_data = {}
        self._load_local_save()

    def _get_file_path(self):
        """获取云端存档文件路径"""
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), CLOUD_SAVE_FILE)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), CLOUD_SAVE_FILE)

    def _load_local_save(self):
        """加载本地存档"""
        try:
            file_path = self._get_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.local_save_data = json.load(f)
        except Exception as e:
            print(f"加载本地存档失败：{e}")
            self.local_save_data = {}

    def _save_local_save(self):
        """保存本地存档"""
        try:
            file_path = self._get_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.local_save_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存本地存档失败：{e}")
            return False

    def save_game(self, game_data):
        """保存游戏存档"""
        save_data = {
            'player_id': self.online_manager.get_player_id(),
            'timestamp': pygame.time.get_ticks() // 1000,
            'version': '2.4.0',
            'game_data': game_data,
        }
        self.local_save_data = save_data
        self._save_local_save()

        # 如果在线，尝试上传到云端
        if self.online_manager.get_online_status():
            self._upload_cloud_save(save_data)

        return True

    def load_game(self):
        """加载游戏存档"""
        if not self.local_save_data:
            return None

        # 验证存档归属
        saved_player_id = self.local_save_data.get('player_id')
        if saved_player_id != self.online_manager.get_player_id():
            print("存档不属于当前玩家")
            return None

        return self.local_save_data.get('game_data')

    def has_save(self):
        """检查是否有存档"""
        return bool(self.local_save_data)

    def delete_save(self):
        """删除存档"""
        self.local_save_data = {}
        file_path = self._get_file_path()
        if os.path.exists(file_path):
            os.remove(file_path)
        return True

    def _upload_cloud_save(self, save_data):
        """上传云端存档"""
        if not self.online_manager.get_online_status():
            return False

        try:
            import urllib.request
            req = urllib.request.Request(
                ONLINE_LEADERBOARD_URL + '/cloudsave',
                data=json.dumps(save_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"上传云端存档失败：{e}")
            return False

    def _download_cloud_save(self):
        """下载云端存档"""
        if not self.online_manager.get_online_status():
            return None

        try:
            import urllib.request
            url = f"{ONLINE_LEADERBOARD_URL}/cloudsave?player_id={self.online_manager.get_player_id()}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data:
                    self.local_save_data = data
                    self._save_local_save()
                return data
        except Exception as e:
            print(f"下载云端存档失败：{e}")
            return None

    def get_save_info(self):
        """获取存档信息"""
        if not self.local_save_data:
            return None

        game_data = self.local_save_data.get('game_data', {})
        return {
            'timestamp': self.local_save_data.get('timestamp', 0),
            'version': self.local_save_data.get('version', 'unknown'),
            'score': game_data.get('score', 0),
            'lines': game_data.get('lines_cleared', 0),
            'level': game_data.get('level_index', 0) + 1,
            'mode': game_data.get('game_mode', 'classic'),
        }


class StatisticsManager:
    """游戏统计管理器"""

    def __init__(self):
        self.stats = self._load_stats()
        self.achievements = self._load_achievements()
        self.unlocked_skins = self._load_unlocked_skins()
        self.current_game_stats = {
            'lines_cleared': 0,
            'blocks_placed': 0,
            'combos': 0,
            'max_combo': 0,
            'score': 0,
        }

    def _get_file_path(self):
        """获取统计文件路径"""
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), 'stats.json')
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats.json')

    def _load_stats(self):
        """加载统计数据"""
        try:
            file_path = self._get_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('stats', {})
            return self._get_default_stats()
        except Exception as e:
            print(f"加载统计失败：{e}")
            return self._get_default_stats()

    def _get_default_stats(self):
        """获取默认统计数据"""
        return {
            'total_games': 0,
            'total_lines': 0,
            'total_score': 0,
            'total_combos': 0,
            'max_combo': 0,
            'total_tetrises': 0,
            'games_finished': 0,
            'time_played': 0,
        }

    def _load_achievements(self):
        """加载成就"""
        try:
            file_path = self._get_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('achievements', [])
            return []
        except Exception:
            return []

    def _load_unlocked_skins(self):
        """加载已解锁皮肤"""
        try:
            file_path = self._get_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('unlocked_skins', ['default'])
            return ['default']
        except Exception:
            return ['default']

    def save_stats(self):
        """保存统计数据"""
        try:
            file_path = self._get_file_path()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'stats': self.stats,
                    'achievements': self.achievements,
                    'unlocked_skins': self.unlocked_skins
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存统计失败：{e}")
            return False

    def reset_game_stats(self):
        """重置当前游戏统计"""
        self.current_game_stats = {
            'lines_cleared': 0,
            'blocks_placed': 0,
            'combos': 0,
            'max_combo': 0,
            'score': 0,
        }

    def add_line(self, count=1):
        """添加消除行数"""
        self.current_game_stats['lines_cleared'] += count
        self.stats['total_lines'] += count

    def add_block_placed(self):
        """添加放置方块数"""
        self.current_game_stats['blocks_placed'] += 1

    def add_combo(self, combo_count):
        """添加连击"""
        if combo_count > 0:
            self.current_game_stats['combos'] += 1
            self.stats['total_combos'] += 1
            if combo_count > self.current_game_stats['max_combo']:
                self.current_game_stats['max_combo'] = combo_count
            if combo_count > self.stats.get('max_combo', 0):
                self.stats['max_combo'] = combo_count

    def add_score(self, score):
        """添加分数"""
        self.current_game_stats['score'] += score
        self.stats['total_score'] += score

    def add_tetris(self):
        """添加四行消除计数"""
        self.stats['total_tetrises'] += 1

    def finish_game(self, game_over=True):
        """完成游戏统计"""
        if game_over:
            self.stats['total_games'] += 1
        self.stats['games_finished'] += 1
        self.save_stats()

    def get_stats(self):
        """获取统计数据"""
        return self.stats

    def unlock_achievement(self, achievement_id):
        """解锁成就"""
        if achievement_id not in self.achievements and achievement_id in ACHIEVEMENTS:
            self.achievements.append(achievement_id)
            self.save_stats()
            return True
        return False

    def get_achievements(self):
        """获取已解锁成就"""
        return [(aid, ACHIEVEMENTS[aid]) for aid in self.achievements if aid in ACHIEVEMENTS]

    def get_all_achievements(self):
        """获取所有成就"""
        return ACHIEVEMENTS

    def check_skin_unlocks(self):
        """检查并解锁新的皮肤"""
        unlocked = []
        for skin_id, skin_data in BLOCK_SKINS.items():
            condition = skin_data.get('unlock_condition')
            if condition is None:
                continue  # 默认解锁的皮肤

            # 检查解锁条件
            unlocked_skin = False
            if condition['type'] == 'score' and self.stats.get('total_score', 0) >= condition['value']:
                unlocked_skin = True
            elif condition['type'] == 'lines' and self.stats.get('total_lines', 0) >= condition['value']:
                unlocked_skin = True
            elif condition['type'] == 'level' and self.stats.get('max_level', 0) >= condition['value']:
                unlocked_skin = True
            elif condition['type'] == 'combo' and self.stats.get('max_combo', 0) >= condition['value']:
                unlocked_skin = True
            elif condition['type'] == 'tetris' and self.stats.get('total_tetrises', 0) >= condition['value']:
                unlocked_skin = True

            if unlocked_skin and skin_id not in self.unlocked_skins:
                self.unlocked_skins.append(skin_id)
                unlocked.append(skin_id)

        return unlocked

    def update_max_level(self, level):
        """更新最高关卡"""
        if level > self.stats.get('max_level', 0):
            self.stats['max_level'] = level


class Block:
    """方块类"""

    def __init__(self, shape_type=None, skin='default'):
        if shape_type is None:
            shape_type = random.choice(list(SHAPES.keys()))
        self.shape_type = shape_type
        self.shape = [row[:] for row in SHAPES[shape_type]]
        self.skin = skin
        self.color = self._get_color(skin)
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def _get_color(self, skin):
        """根据皮肤获取颜色"""
        if skin in BLOCK_SKINS and self.shape_type in BLOCK_SKINS[skin]['colors']:
            return BLOCK_SKINS[skin]['colors'][self.shape_type]
        return COLORS[self.shape_type]

    def set_skin(self, skin):
        """设置皮肤"""
        self.skin = skin
        self.color = self._get_color(skin)

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
        """清除满行并返回消除的行数（保留用于兼容）"""
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

    def __init__(self, mode='classic', custom_rules=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('俄罗斯方块 - Tetris')

        # 加载中文字体
        self.font_large = self._load_font(36)
        self.font_medium = self._load_font(24)
        self.font_small = self._load_font(18)

        # 初始化管理器
        self.sound_manager = SoundManager()
        self.high_score_manager = HighScoreManager()
        self.statistics_manager = StatisticsManager()
        self.online_manager = OnlineLeaderboardManager()
        self.cloud_save_manager = CloudSaveManager(self.online_manager)
        self.custom_rules_manager = CustomRulesManager()

        # 游戏模式
        self.game_mode = mode
        self.mode_config = GAME_MODES.get(mode, GAME_MODES['classic'])

        # 自定义规则（仅自定义模式使用）
        self.custom_rules = custom_rules if custom_rules else DEFAULT_CUSTOM_RULES.copy()

        # 当前主题
        self.current_theme_name = 'classic'
        self.current_theme = THEMES['classic']

        # 当前皮肤
        self.current_skin = 'default'

        # 音量设置
        self.music_volume = MUSIC_VOLUME
        self.sound_volume = SOUND_VOLUME

        # 竞速/限时模式特定变量
        self.sprint_target = 40  # 竞速模式目标行数
        self.ultra_time = 120  # 限时模式时间（秒）
        self.ultra_start_time = 0

        # 大师模式特定变量
        self.master_max_level = 20

        # 成就解锁状态
        self.new_achievements = []

        self.clock = pygame.time.Clock()
        self.reset_game()

        # 动画状态
        self.clearing_lines = []  # 正在消除的行
        self.clear_animation_frame = 0
        self.levelup_animation_frame = 0
        self.levelup_animation_text = ""

        # 粒子效果
        self.particles = []
        self.explosions = []  # 爆炸效果列表

        # 背景动画
        self.bg_animation_frame = 0
        self.bg_particles = []  # 背景粒子
        self._init_bg_particles()

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

    def _init_bg_particles(self):
        """初始化背景粒子"""
        self.bg_particles = []
        for _ in range(30):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(0.2, 1)
            size = random.randint(1, 3)
            # 使用主题的强调色或白色
            color = (*self.current_theme.get('accent_color', (255, 215, 0)), 100)
            self.bg_particles.append(Particle(x, y, color, vx, vy, life=9999, size=size, gravity=0))

    def _update_bg_particles(self):
        """更新背景粒子"""
        self.bg_animation_frame += 1

        # 更新现有粒子
        for particle in self.bg_particles:
            particle.y += particle.vy
            particle.x += particle.vx

            # 超出屏幕重置到顶部
            if particle.y > SCREEN_HEIGHT:
                particle.y = -10
                particle.x = random.randint(0, SCREEN_WIDTH)

        # 限制粒子数量
        if len(self.bg_particles) < 30 and random.random() < 0.05:
            x = random.randint(0, SCREEN_WIDTH)
            y = -10
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(0.2, 1)
            size = random.randint(1, 3)
            color = (*self.current_theme.get('accent_color', (255, 215, 0)), 100)
            self.bg_particles.append(Particle(x, y, color, vx, vy, life=9999, size=size, gravity=0))

    def _draw_bg_particles(self):
        """绘制背景粒子"""
        for particle in self.bg_particles:
            s = pygame.Surface((particle.size * 2, particle.size * 2), pygame.SRCALPHA)
            color = (*self.current_theme.get('accent_color', (255, 215, 0)), 50)
            pygame.draw.circle(s, color, (particle.size, particle.size), particle.size)
            self.screen.blit(s, (int(particle.x - particle.size), int(particle.y - particle.size)))

    def reset_game(self):
        """重置游戏状态"""
        self.board = GameBoard()
        self.current_block = Block(skin=self.current_skin)
        self.next_block = Block(skin=self.current_skin)
        self.hold_block = None  # 暂存的方块
        self.can_hold = True  # 每回合只能暂存一次
        self.score = 0
        self.lines_cleared = 0
        self.level_index = 0
        self.level_lines = 0
        self.combo = 0  # 连击计数器
        self.game_over = False
        self.paused = False
        self.last_fall_time = pygame.time.get_ticks()
        self.running = True
        self.new_high_score = False  # 标记是否创造新高分
        self.clearing_lines = []
        self.clear_animation_frame = 0
        self.levelup_animation_frame = 0
        self.levelup_animation_text = ""
        self.combo_animation_frame = 0  # 连击动画帧
        self.particles = []
        self.explosions = []  # 爆炸效果列表
        self.new_achievements = []

        # 重置背景动画
        self.bg_animation_frame = 0
        self.bg_particles = []
        self._init_bg_particles()

        # 重置统计
        self.statistics_manager.reset_game_stats()

        # 模式特定重置
        if self.game_mode == 'sprint':
            self.sprint_start_time = pygame.time.get_ticks()
            self.sprint_finished = False
        elif self.game_mode == 'ultra':
            self.ultra_start_time = pygame.time.get_ticks()
            self.ultra_game_over = False
        elif self.game_mode == 'endless':
            self.endless_level = 0
        elif self.game_mode == 'master':
            self.master_level = 0
            self.master_start_time = pygame.time.get_ticks()
        elif self.game_mode == 'zen':
            self.zen_level = 1
            self.zen_speed = 1000  # 禅模式固定速度，无压力
        elif self.game_mode == 'challenge':
            self.challenge_type = random.choice(list(CHALLENGE_CONFIGS.keys()))
            self.challenge_config = CHALLENGE_CONFIGS[self.challenge_type]
        elif self.game_mode == 'custom':
            # 使用自定义规则
            self.custom_rules = self.custom_rules_manager.get_all_rules()
            self.level_index = self.custom_rules.get('initial_level', 1) - 1

        # 更新标题
        pygame.display.set_caption(f'俄罗斯方块 - Tetris - {self.mode_config["name"]}')

    def spawn_block(self):
        """生成新方块"""
        self.current_block = self.next_block
        self.next_block = Block(skin=self.current_skin)
        self.current_block.x = GRID_WIDTH // 2 - len(self.current_block.shape[0]) // 2
        self.current_block.y = 0
        self.can_hold = True  # 新方块生成后可以暂存

        if not self.board.is_valid_position(self.current_block):
            self.game_over = True
            self.sound_manager.play('gameover')  # 播放游戏结束音效

            # 根据模式记录分数
            if self.game_mode == 'sprint':
                # 竞速模式记录完成时间
                elapsed_time = (pygame.time.get_ticks() - self.sprint_start_time) / 1000
                self.high_score_manager.add_score(
                    self.score, self.lines_cleared, self.level_index + 1,
                    mode='sprint', extra_data={'time': elapsed_time}
                )
            elif self.game_mode == 'ultra':
                # 限时模式记录最终分数
                self.high_score_manager.add_score(
                    self.score, self.lines_cleared, self.level_index + 1,
                    mode='ultra'
                )
            elif self.game_mode == 'endless':
                # 无尽模式记录等级和分数
                self.high_score_manager.add_score(
                    self.score, self.lines_cleared, self.endless_level + 1,
                    mode='endless'
                )
            else:
                # 经典模式
                self.high_score_manager.add_score(
                    self.score, self.lines_cleared, self.level_index + 1,
                    mode='classic'
                )

            if self.score > self.high_score_manager.get_high_score(mode=self.game_mode):
                self.new_high_score = True

            # 统计游戏结束
            self.statistics_manager.finish_game(game_over=True)

            # 成就检测
            self.statistics_manager.unlock_achievement('first_game')
            if self.score >= 10000:
                self.statistics_manager.unlock_achievement('score_10000')

            # 上传分数到在线排行榜（如果在线）
            extra_data = {}
            if self.game_mode == 'sprint':
                extra_data = {'time': (pygame.time.get_ticks() - self.sprint_start_time) / 1000}
            self.online_manager.upload_score(
                self.score, self.lines_cleared, self.level_index + 1,
                mode=self.game_mode, extra_data=extra_data
            )

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

    def hold_block(self):
        """暂存方块"""
        if not self.can_hold:
            return

        if self.hold_block is None:
            self.hold_block = Block(self.current_block.shape_type)
            self.spawn_block()
        else:
            # 交换当前方块和暂存方块
            current_type = self.current_block.shape_type
            self.current_block = Block(self.hold_block.shape_type)
            self.hold_block = Block(current_type)
            self.current_block.x = GRID_WIDTH // 2 - len(self.current_block.shape[0]) // 2
            self.current_block.y = 0

        self.can_hold = False
        self.sound_manager.play('rotate')

    def lock_current_block(self):
        """锁定当前方块"""
        self.board.lock_block(self.current_block)
        lines = self._get_full_lines()

        if lines:
            self.clearing_lines = lines
            self.clear_animation_frame = 0
            # 不立即消除，等待动画完成
        else:
            # 没有消行，重置连击
            self.combo = 0
            self.spawn_block()

    def _get_full_lines(self):
        """获取所有满行的索引"""
        full_lines = []
        for y in range(GRID_HEIGHT):
            if all(self.board.grid[y]):
                full_lines.append(y)
        return full_lines

    def _clear_lines_with_animation(self):
        """执行消行动画并消除行"""
        if self.clear_animation_frame == 1:
            # 动画开始时创建爆炸效果
            for y in self.clearing_lines:
                # 为每个单元格创建爆炸效果
                for x in range(GRID_WIDTH):
                    cell_color = self.board.grid[y][x]
                    if cell_color:
                        cx = x * BLOCK_SIZE + BLOCK_SIZE // 2
                        cy = y * BLOCK_SIZE + BLOCK_SIZE // 2
                        self.explosions.append(Explosion(cx, cy, cell_color, particle_count=8))

        if self.clear_animation_frame >= CLEAR_ANIMATION_FRAMES:
            # 动画完成，实际消除行
            for y in sorted(self.clearing_lines, reverse=True):
                del self.board.grid[y]
                self.board.grid.insert(0, [None for _ in range(GRID_WIDTH)])

            lines = len(self.clearing_lines)
            self.lines_cleared += lines
            self.level_lines += lines

            # 更新统计
            self.statistics_manager.add_line(lines)

            # 连击系统
            self.combo += 1
            combo_bonus = self.combo * 50 * (self.level_index + 1)

            # 计分
            line_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            base_score = line_scores.get(lines, 0) * (self.level_index + 1)
            self.score += base_score + combo_bonus

            # 更新统计
            self.statistics_manager.add_score(base_score + combo_bonus)
            self.statistics_manager.add_combo(self.combo - 1)

            # 播放消行音效
            self.sound_manager.play_clear(lines)

            # 成就检测
            if self.lines_cleared >= 1:
                self.statistics_manager.unlock_achievement('first_line')
            if lines == 4:
                self.statistics_manager.add_tetris()
                self.statistics_manager.unlock_achievement('tetris')
            if self.combo >= 10:
                self.statistics_manager.unlock_achievement('combo_10')
            elif self.combo >= 5:
                self.statistics_manager.unlock_achievement('combo_5')

            # 检查升级
            self._check_level_up()

            # 检查竞速模式完成
            if self.game_mode == 'sprint' and self.lines_cleared >= self.sprint_target:
                self.sprint_finished = True
                self.game_over = True
                self.sound_manager.play('levelup')  # 播放完成音效

            self.clearing_lines = []
            self.clear_animation_frame = 0

            # 连击动画
            if self.combo > 1:
                self.combo_animation_frame = 30

            if not self.game_over:
                self.spawn_block()
        else:
            self.clear_animation_frame += 1

    def _check_level_up(self):
        """检查是否升级"""
        if self.game_mode == 'endless':
            # 无尽模式：每消除 10 行升一级
            new_level = self.lines_cleared // 10
            if new_level > self.endless_level:
                self.endless_level = new_level
                self.levelup_animation_frame = 0
                self.levelup_animation_text = f"无尽模式 - 等级 {self.endless_level + 1}"
                self.sound_manager.play('levelup')

                # 成就检测
                if self.endless_level >= 9:
                    self.statistics_manager.unlock_achievement('endless_10')
            return

        if self.game_mode == 'sprint':
            # 竞速模式不升级
            return

        if self.game_mode == 'ultra':
            # 限时模式：每消除 10 行升一级
            new_level = self.lines_cleared // 10
            if new_level > self.level_index:
                self.level_index = new_level
                self.levelup_animation_frame = 0
                self.levelup_animation_text = f"关卡 {self.level_index + 1}"
                self.sound_manager.play('levelup')
            return

        if self.game_mode == 'master':
            # 大师模式：20 层关卡
            current_level = MASTER_LEVELS[self.level_index] if self.level_index < len(MASTER_LEVELS) else MASTER_LEVELS[-1]
            if self.level_lines >= current_level['lines']:
                if self.level_index < len(MASTER_LEVELS) - 1:
                    self.level_index += 1
                    self.level_lines = 0
                    self.levelup_animation_frame = 0
                    self.levelup_animation_text = f"大师模式 - 关卡 {self.level_index + 1} - {MASTER_LEVELS[self.level_index]['name']}"
                    self.sound_manager.play('levelup')
            return

        if self.game_mode == 'zen':
            # 禅模式：不升级，无压力
            return

        if self.game_mode == 'challenge':
            # 挑战模式：根据挑战类型决定是否升级
            if self.level_index < len(LEVELS) - 1:
                current_level = LEVELS[self.level_index]
                if self.level_lines >= current_level['lines']:
                    self.level_index += 1
                    self.level_lines = 0
                    self.levelup_animation_frame = 0
                    self.levelup_animation_text = f"挑战模式 - 关卡 {self.level_index + 1}"
                    self.sound_manager.play('levelup')
            return

        if self.game_mode == 'custom':
            # 自定义模式：根据自定义规则
            max_level = self.custom_rules.get('max_level', 10)
            target_lines = self.custom_rules.get('target_lines', 100)
            lines_per_level = target_lines // max_level if max_level > 0 else 10

            if self.level_lines >= lines_per_level:
                if self.level_index < max_level - 1:
                    self.level_index += 1
                    self.level_lines = 0
                    self.levelup_animation_frame = 0
                    self.levelup_animation_text = f"自定义模式 - 关卡 {self.level_index + 1}"
                    self.sound_manager.play('levelup')
            return

        # 经典模式
        current_level = LEVELS[self.level_index]
        if self.level_lines >= current_level['lines']:
            if self.level_index < len(LEVELS) - 1:
                self.level_index += 1
                self.level_lines = 0
                self.levelup_animation_frame = 0
                self.levelup_animation_text = f"关卡 {self.level_index} - {LEVELS[self.level_index]['name']}"
                self.sound_manager.play('levelup')

                # 成就检测
                if self.level_index >= 4:
                    self.statistics_manager.unlock_achievement('level_5')
                if self.level_index >= 9:
                    self.statistics_manager.unlock_achievement('level_10')

    def get_current_speed(self):
        """获取当前下落速度"""
        if self.game_mode == 'endless':
            # 无尽模式：速度越来越快
            level = min(self.endless_level, len(ENDLESS_SPEEDS) - 1)
            return ENDLESS_SPEEDS[level]
        elif self.game_mode == 'sprint':
            # 竞速模式：固定速度，随消除行数加速
            base_speed = 500
            speed_decrease = self.lines_cleared * 10
            return max(50, base_speed - speed_decrease)
        elif self.game_mode == 'ultra':
            # 限时模式：根据关卡
            level = min(self.level_index, len(LEVELS) - 1)
            return LEVELS[level]['speed']
        elif self.game_mode == 'master':
            # 大师模式：使用大师关卡配置
            level = min(self.level_index, len(MASTER_LEVELS) - 1)
            return MASTER_LEVELS[level]['speed']
        elif self.game_mode == 'zen':
            # 禅模式：固定慢速，无压力
            return self.zen_speed
        elif self.game_mode == 'challenge':
            # 挑战模式：根据挑战类型调整速度
            base_speed = LEVELS[min(self.level_index, len(LEVELS) - 1)]['speed']
            if self.challenge_config.get('fast_drop'):
                return max(50, base_speed // 2)
            return base_speed
        elif self.game_mode == 'custom':
            # 自定义模式：根据自定义规则
            gravity = self.custom_rules.get('gravity_type', 'normal')
            if gravity == 'fast':
                return 100
            elif gravity == 'random':
                return random.randint(100, 500)
            # normal - 使用经典速度
            level = min(self.level_index, len(LEVELS) - 1)
            return LEVELS[level]['speed']
        else:
            # 经典模式
            return LEVELS[self.level_index]['speed']

    def _draw_block_cell(self, draw_x, draw_y, color):
        """绘制单个方块单元格，根据主题使用不同风格"""
        theme = self.current_theme
        style = theme.get('block_style', 'gradient')

        if style == 'flat':
            # 扁平风格
            pygame.draw.rect(self.screen, color,
                           (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))
        elif style == 'outline':
            # 轮廓风格
            pygame.draw.rect(self.screen, color,
                           (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2), 2)
            pygame.draw.rect(self.screen, color,
                           (draw_x + 4, draw_y + 4, BLOCK_SIZE - 8, BLOCK_SIZE - 8))
        elif style == 'neon':
            # 霓虹风格 - 带发光效果
            pygame.draw.rect(self.screen, color,
                           (draw_x + 2, draw_y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4))
            # 外发光
            glow_color = tuple(int(c * 0.5) for c in color)
            pygame.draw.rect(self.screen, glow_color,
                           (draw_x + 1, draw_y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2), 1)
            pygame.draw.rect(self.screen, glow_color,
                           (draw_x, draw_y, BLOCK_SIZE, BLOCK_SIZE), 1)
        else:
            # gradient 风格（默认）
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

    def _draw_clear_animation(self):
        """绘制消行动画 - 华丽的爆炸效果"""
        progress = self.clear_animation_frame / CLEAR_ANIMATION_FRAMES

        # 绘制爆炸效果
        for explosion in self.explosions:
            explosion.draw(self.screen)

        # 绘制闪电效果连接相邻的消除行
        if len(self.clearing_lines) > 1 and progress < 0.6:
            for i in range(len(self.clearing_lines) - 1):
                y1 = self.clearing_lines[i] * BLOCK_SIZE + BLOCK_SIZE // 2
                y2 = (self.clearing_lines[i + 1]) * BLOCK_SIZE
                lightning_color = (255, 255, 255) if int(progress * 15) % 2 == 0 else (100, 200, 255)
                for _ in range(3):
                    start_x = random.randint(0, GRID_WIDTH * BLOCK_SIZE)
                    points = [(start_x, y1)]
                    for j in range(5):
                        px = start_x + random.randint(-20, 20)
                        py = y1 + (y2 - y1) * (j / 5)
                        points.append((px, py))
                    points.append((start_x + random.randint(-20, 20), y2))
                    pygame.draw.lines(self.screen, lightning_color, False, points, 2)

        # 绘制冲击波效果
        if progress < 0.4:
            for y in self.clearing_lines:
                wave_y = y * BLOCK_SIZE + BLOCK_SIZE // 2
                wave_alpha = int(255 * (1 - progress / 0.4))
                wave_width = int(BLOCK_SIZE * GRID_WIDTH * (progress / 0.4))
                wave_height = int(BLOCK_SIZE * (1 + progress * 2))
                wave_surface = pygame.Surface((wave_width, wave_height), pygame.SRCALPHA)
                wave_color = (255, 255, 255, wave_alpha)
                pygame.draw.ellipse(wave_surface, wave_color, (0, 0, wave_width, wave_height))
                self.screen.blit(wave_surface, (0, wave_y - wave_height // 2))

    def _draw_levelup_animation(self):
        """绘制升级动画"""
        progress = self.levelup_animation_frame / LEVELUP_ANIMATION_FRAMES

        # 创建半透明覆盖层
        overlay = pygame.Surface((GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
        overlay.fill(self.current_theme['bg_color'])
        overlay.set_alpha(int(100 * (1 - abs(progress - 0.5) * 2)))
        self.screen.blit(overlay, (0, 0))

        # 绘制升级文字
        text = self.font_large.render(self.levelup_animation_text, True, self.current_theme['accent_color'])
        text_rect = text.get_rect(center=(GRID_WIDTH * BLOCK_SIZE // 2, GRID_HEIGHT * BLOCK_SIZE // 2))

        # 缩放效果
        scale = 1 + 0.3 * (1 - abs(progress - 0.5) * 2)
        scaled_text = pygame.transform.scale(text,
            (int(text.get_width() * scale), int(text.get_height() * scale)))
        scaled_rect = scaled_text.get_rect(center=(GRID_WIDTH * BLOCK_SIZE // 2, GRID_HEIGHT * BLOCK_SIZE // 2))

        self.screen.blit(scaled_text, scaled_rect)

        # 粒子效果
        for _ in range(5):
            px = random.randint(0, GRID_WIDTH * BLOCK_SIZE)
            py = random.randint(0, GRID_HEIGHT * BLOCK_SIZE)
            color = random.choice([(255, 215, 0), (255, 100, 100), (100, 255, 100)])
            pygame.draw.circle(self.screen, color, (px, py), random.randint(2, 4))

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
                        # 实体方块 - 使用主题风格
                        self._draw_block_cell(draw_x, draw_y, block.color)

    def draw_grid(self):
        """绘制游戏网格"""
        theme = self.current_theme
        # 绘制背景
        pygame.draw.rect(self.screen, theme['grid_color'],
                        (0, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))

        # 绘制网格线
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, theme['grid_line_color'],
                           (x * BLOCK_SIZE, 0),
                           (x * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, theme['grid_line_color'],
                           (0, y * BLOCK_SIZE),
                           (GRID_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE))

        # 绘制已锁定的方块
        for y, row in enumerate(self.board.grid):
            for x, color in enumerate(row):
                if color:
                    draw_x = x * BLOCK_SIZE
                    draw_y = y * BLOCK_SIZE
                    self._draw_block_cell(draw_x, draw_y, color)

    def draw_ui(self):
        """绘制 UI 信息"""
        theme = self.current_theme
        ui_x = GRID_WIDTH * BLOCK_SIZE + 20

        # 标题
        title = self.font_large.render('俄罗斯方块', True, theme['text_color'])
        self.screen.blit(title, (ui_x, 20))

        # 最高分
        high_score = self.high_score_manager.get_high_score()
        high_score_text = self.font_small.render(f'最高分：{high_score}', True, theme['accent_color'])
        self.screen.blit(high_score_text, (ui_x, 55))

        # 暂存方块
        hold_text = self.font_medium.render('暂存:', True, theme['text_color'])
        self.screen.blit(hold_text, (ui_x, 85))

        # 绘制暂存方块
        if self.hold_block:
            preview_x = ui_x
            preview_y = 100
            for y, row in enumerate(self.hold_block.shape):
                for x, cell in enumerate(row):
                    if cell:
                        color = self.hold_block.color if self.can_hold else tuple(c // 2 for c in self.hold_block.color)
                        pygame.draw.rect(self.screen, color,
                                       (preview_x + x * BLOCK_SIZE,
                                        preview_y + y * BLOCK_SIZE,
                                        BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 下一个方块
        next_text = self.font_medium.render('下一个:', True, theme['text_color'])
        self.screen.blit(next_text, (ui_x, 165))

        # 绘制下一个方块预览
        preview_x = ui_x
        preview_y = 180
        for y, row in enumerate(self.next_block.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_block.color,
                                   (preview_x + x * BLOCK_SIZE,
                                    preview_y + y * BLOCK_SIZE,
                                    BLOCK_SIZE - 2, BLOCK_SIZE - 2))

        # 分数
        score_text = self.font_medium.render(f'分数：{self.score}', True, theme['text_color'])
        self.screen.blit(score_text, (ui_x, 300))

        # 消除行数
        lines_text = self.font_medium.render(f'消除：{self.lines_cleared}', True, theme['text_color'])
        self.screen.blit(lines_text, (ui_x, 340))

        # 连击
        if self.combo > 0:
            combo_text = self.font_medium.render(f'连击：{self.combo}', True, theme['accent_color'])
            self.screen.blit(combo_text, (ui_x, 380))
            ui_y_offset = 40
        else:
            ui_y_offset = 0

        # 根据模式显示不同信息
        if self.game_mode == 'classic':
            # 经典模式：显示关卡
            current_level = LEVELS[self.level_index]
            level_text = self.font_medium.render(f'关卡：{current_level["name"]}', True, theme['text_color'])
            self.screen.blit(level_text, (ui_x, 420 - ui_y_offset))

            # 升级进度
            progress = f'{self.level_lines}/{current_level["lines"]}'
            progress_text = self.font_small.render(f'升级：{progress}', True, theme['text_color'])
            self.screen.blit(progress_text, (ui_x, 460 - ui_y_offset))
        elif self.game_mode == 'endless':
            # 无尽模式：显示等级
            level_text = self.font_medium.render(f'等级：{self.endless_level + 1}', True, theme['text_color'])
            self.screen.blit(level_text, (ui_x, 420 - ui_y_offset))

            # 升级进度
            progress_to_next = self.lines_cleared % 10
            progress_text = self.font_small.render(f'升级：{progress_to_next}/10', True, theme['text_color'])
            self.screen.blit(progress_text, (ui_x, 460 - ui_y_offset))
        elif self.game_mode == 'sprint':
            # 竞速模式：显示剩余行数和用时
            remaining = max(0, self.sprint_target - self.lines_cleared)
            elapsed = (pygame.time.get_ticks() - self.sprint_start_time) / 1000
            level_text = self.font_medium.render(f'剩余：{remaining} 行', True, theme['text_color'])
            self.screen.blit(level_text, (ui_x, 420 - ui_y_offset))

            time_text = self.font_small.render(f'用时：{elapsed:.1f}秒', True, theme['text_color'])
            self.screen.blit(time_text, (ui_x, 460 - ui_y_offset))
        elif self.game_mode == 'ultra':
            # 限时模式：显示剩余时间
            elapsed = (pygame.time.get_ticks() - self.ultra_start_time) / 1000
            remaining = max(0, self.ultra_time - elapsed)
            level_text = self.font_medium.render(f'剩余：{remaining:.1f}秒', True, theme['text_color'])
            self.screen.blit(level_text, (ui_x, 420 - ui_y_offset))

            # 目标
            target_text = self.font_small.render(f'目标：最高分', True, theme['text_color'])
            self.screen.blit(target_text, (ui_x, 460 - ui_y_offset))

        # 操作说明
        controls = [
            '操作说明:',
            '← → 移动',
            '↑ 旋转',
            '↓ 软降',
            '空格 硬降',
            'C 暂存',
            'P 暂停',
            'R 重新开始',
            'T 切换主题',
            '1/2 音效音量',
            '3/4 音乐音量',
            'M 切换音乐',
            'F5 刷新在线',
            'S 保存 (暂停)',
            'L 读取存档',
            'DEL 删除存档 (暂停)',
        ]
        for i, text in enumerate(controls):
            rendered = self.font_small.render(text, True, theme['text_color'])
            self.screen.blit(rendered, (ui_x, 500 - ui_y_offset + i * 25))

        # 音量显示
        volume_y = 720 - ui_y_offset
        sound_volume_bar = self._draw_volume_bar(ui_x, volume_y, '音效', self.sound_manager.sound_volume, theme)
        music_volume_bar = self._draw_volume_bar(ui_x, volume_y + 30, '音乐', self.sound_manager.music_volume, theme)

        # 音乐播放状态
        if self.sound_manager.music_playing:
            music_status = self.font_small.render('音乐：播放中', True, theme['accent_color'])
        else:
            music_status = self.font_small.render('音乐：已暂停', True, theme['text_color'])
        self.screen.blit(music_status, (ui_x, volume_y + 60))

        # 在线状态显示 - v2.4.0 新增
        online_status_y = volume_y + 100
        if self.online_manager.get_online_status():
            online_text = self.font_small.render('在线：已连接', True, (100, 255, 100))
        else:
            online_text = self.font_small.render('在线：离线模式', True, (255, 200, 100))
        self.screen.blit(online_text, (ui_x, online_status_y))

        # 玩家 ID 显示
        player_id_text = self.font_small.render(f'ID: {self.online_manager.get_player_id_display()}', True, theme['text_color'])
        self.screen.blit(player_id_text, (ui_x, online_status_y + 20))

        # 存档状态
        if self.cloud_save_manager.has_save():
            save_info = self.cloud_save_manager.get_save_info()
            save_text = self.font_small.render(f'存档：{save_info["score"]}分 L{save_info["level"]}', True, theme['accent_color'])
        else:
            save_text = self.font_small.render('存档：无', True, theme['text_color'])
        self.screen.blit(save_text, (ui_x, online_status_y + 40))

    def _draw_volume_bar(self, x, y, label, volume, theme):
        """绘制音量条"""
        # 标签
        label_text = self.font_small.render(f'{label}:', True, theme['text_color'])
        self.screen.blit(label_text, (x, y))

        # 音量条背景
        bar_x = x + 50
        bar_width = 100
        bar_height = 15
        pygame.draw.rect(self.screen, theme['grid_color'], (bar_x, y + 2, bar_width, bar_height))

        # 音量条填充
        fill_width = int(bar_width * volume)
        if volume > 0.5:
            bar_color = theme['accent_color']
        elif volume > 0.2:
            bar_color = (255, 200, 0)
        else:
            bar_color = (100, 200, 100)
        pygame.draw.rect(self.screen, bar_color, (bar_x, y + 2, fill_width, bar_height))

        # 边框
        pygame.draw.rect(self.screen, theme['text_color'], (bar_x, y + 2, bar_width, bar_height), 1)

        return (bar_x, y + 2, bar_width, bar_height)

    def draw_game_over(self):
        """绘制游戏结束画面"""
        theme = self.current_theme
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(theme['bg_color'])
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # 根据模式显示不同文字
        if self.game_mode == 'sprint':
            elapsed = (pygame.time.get_ticks() - self.sprint_start_time) / 1000
            game_over_text = self.font_large.render('挑战完成!', True, theme['accent_color'])
            score_text = self.font_medium.render(f'分数：{self.score}', True, theme['text_color'])
            time_text = self.font_medium.render(f'用时：{elapsed:.2f}秒', True, theme['text_color'])
        elif self.game_mode == 'ultra':
            game_over_text = self.font_large.render('时间到!', True, theme['accent_color'])
            score_text = self.font_medium.render(f'最终分数：{self.score}', True, theme['text_color'])
            time_text = None
        else:
            game_over_text = self.font_large.render('游戏结束', True, theme['text_color'])
            score_text = self.font_medium.render(f'最终分数：{self.score}', True, theme['text_color'])
            time_text = None

        self.screen.blit(game_over_text,
                        (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(score_text,
                        (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 30))

        if time_text:
            self.screen.blit(time_text,
                            (SCREEN_WIDTH // 2 - time_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 10))

        # 显示最高分
        high_score = self.high_score_manager.get_high_score(mode=self.game_mode)
        high_score_text = self.font_small.render(f'最高分：{high_score}', True, theme['text_color'])
        self.screen.blit(high_score_text,
                        (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 + 40))

        # 新高分提示
        if self.new_high_score:
            new_record_text = self.font_medium.render('新纪录!', True, (255, 215, 0))
            self.screen.blit(new_record_text,
                            (SCREEN_WIDTH // 2 - new_record_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + 70))

        restart_text = self.font_medium.render('按 R 重新开始', True, theme['text_color'])
        self.screen.blit(restart_text,
                        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                         SCREEN_HEIGHT // 2 + 110))

    def draw_pause(self):
        """绘制暂停画面"""
        theme = self.current_theme
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(theme['bg_color'])
        overlay.set_alpha(120)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render('游戏暂停', True, theme['text_color'])
        self.screen.blit(pause_text,
                        (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                         SCREEN_HEIGHT // 2))

    def _draw_combo_animation(self):
        """绘制连击动画"""
        if self.combo_animation_frame <= 0:
            return

        progress = self.combo_animation_frame / 30

        # 在游戏区域中央绘制连击文字
        combo_text = self.font_large.render(f'{self.combo} COMBO!', True, (255, 215, 0))
        scale = 1 + 0.3 * (1 - progress)
        scaled_text = pygame.transform.scale(combo_text,
            (int(combo_text.get_width() * scale), int(combo_text.get_height() * scale)))
        scaled_rect = scaled_text.get_rect(center=(GRID_WIDTH * BLOCK_SIZE // 2, GRID_HEIGHT * BLOCK_SIZE // 2))

        # 绘制发光效果
        glow = self.font_large.render(f'{self.combo} COMBO!', True, (255, 100, 100))
        glow_rect = glow.get_rect(center=(GRID_WIDTH * BLOCK_SIZE // 2 + 2, GRID_HEIGHT * BLOCK_SIZE // 2 + 2))
        self.screen.blit(glow, glow_rect)
        self.screen.blit(scaled_text, scaled_rect)

        # 粒子效果
        for _ in range(5):
            px = random.randint(0, GRID_WIDTH * BLOCK_SIZE)
            py = random.randint(0, GRID_HEIGHT * BLOCK_SIZE)
            color = random.choice([(255, 215, 0), (255, 100, 100), (100, 255, 100)])
            pygame.draw.circle(self.screen, color, (px, py), random.randint(2, 4))

        self.combo_animation_frame -= 1

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(self.current_theme['bg_color'])

        # 绘制背景粒子
        self._draw_bg_particles()

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

        # 绘制消行动画
        if self.clearing_lines:
            self._draw_clear_animation()

        # 绘制连击动画
        if self.combo_animation_frame > 0:
            self._draw_combo_animation()

        # 绘制升级动画
        if self.levelup_animation_frame > 0 and self.levelup_animation_frame < LEVELUP_ANIMATION_FRAMES:
            self._draw_levelup_animation()

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

                # 主题切换
                if event.key == pygame.K_t:
                    self._switch_theme()
                    continue

                # 音量控制
                if event.key == pygame.K_1:
                    # 降低音效音量
                    new_volume = max(0.0, self.sound_manager.sound_volume - 0.1)
                    self.sound_manager.set_sound_volume(new_volume)
                    continue
                if event.key == pygame.K_2:
                    # 增加音效音量
                    new_volume = min(1.0, self.sound_manager.sound_volume + 0.1)
                    self.sound_manager.set_sound_volume(new_volume)
                    continue
                if event.key == pygame.K_3:
                    # 降低音乐音量
                    new_volume = max(0.0, self.sound_manager.music_volume - 0.1)
                    self.sound_manager.set_music_volume(new_volume)
                    continue
                if event.key == pygame.K_4:
                    # 增加音乐音量
                    new_volume = min(1.0, self.sound_manager.music_volume + 0.1)
                    self.sound_manager.set_music_volume(new_volume)
                    continue
                if event.key == pygame.K_m:
                    # 切换背景音乐
                    self.sound_manager.toggle_music()
                    continue

                # 云存档控制 - v2.4.0 新增
                if event.key == pygame.K_F5:
                    # 刷新在线状态
                    self.online_manager.refresh_online_status()
                    continue
                if event.key == pygame.K_s and self.paused:
                    # 保存游戏（暂停时）
                    game_data = {
                        'score': self.score,
                        'lines_cleared': self.lines_cleared,
                        'level_index': self.level_index,
                        'game_mode': self.game_mode,
                    }
                    self.cloud_save_manager.save_game(game_data)
                    continue
                if event.key == pygame.K_l:
                    # 加载游戏
                    if self.cloud_save_manager.has_save():
                        game_data = self.cloud_save_manager.load_game()
                        if game_data:
                            self.score = game_data.get('score', 0)
                            self.lines_cleared = game_data.get('lines_cleared', 0)
                            self.level_index = game_data.get('level_index', 0)
                    continue
                if event.key == pygame.K_DELETE and self.paused:
                    # 删除存档（暂停时）
                    self.cloud_save_manager.delete_save()
                    continue

                if self.game_over or self.paused:
                    continue

                if event.key == pygame.K_p:
                    self.paused = True
                    self.sound_manager.play('pause')
                elif event.key == pygame.K_LEFT:
                    self.move_block(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_block(1, 0)
                elif event.key == pygame.K_DOWN:
                    if self.move_block(0, 1):
                        self.score += 1
                        self.sound_manager.play('place')
                elif event.key == pygame.K_UP:
                    self.rotate_block()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key == pygame.K_c:
                    self.hold_block()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = False

    def _switch_theme(self):
        """切换游戏主题"""
        theme_names = list(THEMES.keys())
        current_index = theme_names.index(self.current_theme_name)
        next_index = (current_index + 1) % len(theme_names)
        self.current_theme_name = theme_names[next_index]
        self.current_theme = THEMES[self.current_theme_name]

    def update(self):
        """更新游戏状态"""
        # 更新背景动画（即使在暂停或游戏结束时也更新）
        self._update_bg_particles()

        # 更新爆炸效果
        self.explosions = [e for e in self.explosions if e.update()]

        if self.game_over or self.paused:
            return

        # 限时模式：检查时间
        if self.game_mode == 'ultra':
            current_time = pygame.time.get_ticks()
            elapsed_time = (current_time - self.ultra_start_time) / 1000
            if elapsed_time >= self.ultra_time:
                self.game_over = True
                self.ultra_game_over = True
                self.sound_manager.play('gameover')
                # 记录分数
                self.high_score_manager.add_score(
                    self.score, self.lines_cleared, self.level_index + 1,
                    mode='ultra', extra_data={'time': elapsed_time}
                )
                return

        # 更新消行动画
        if self.clearing_lines:
            self._clear_lines_with_animation()
            return  # 动画期间不更新其他状态

        # 更新升级动画
        if self.levelup_animation_frame < LEVELUP_ANIMATION_FRAMES:
            self.levelup_animation_frame += 1

        current_time = pygame.time.get_ticks()
        if current_time - self.last_fall_time > self.get_current_speed():
            self.last_fall_time = current_time

            if not self.move_block(0, 1):
                self.lock_current_block()

    def run(self):
        """游戏主循环"""
        # 播放背景音乐
        self.sound_manager.play_music()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


class GameMenu:
    """游戏主菜单"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('俄罗斯方块 - 主菜单')

        self.font_large = self._load_font(48)
        self.font_medium = self._load_font(32)
        self.font_small = self._load_font(20)

        self.current_theme = THEMES['classic']
        self.running = True
        self.menu_state = 'main'  # main, single, dual
        self.selected_mode = 0
        self.clock = pygame.time.Clock()

    def _load_font(self, size):
        """加载字体"""
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        for path in font_paths:
            try:
                return pygame.font.Font(path, size)
            except:
                continue
        return pygame.font.SysFont('arial', size)

    def draw_main_menu(self):
        """绘制主菜单"""
        self.screen.fill(self.current_theme['bg_color'])

        # 标题
        title = self.font_large.render('俄罗斯方块', True, self.current_theme['accent_color'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        # 版本信息
        version = self.font_small.render('Version 2.5.0 - 更多游戏模式', True, GRAY)
        version_rect = version.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(version, version_rect)

        # 菜单选项
        menu_items = [
            ('单人游戏', '选择单人游戏模式'),
            ('双人对战', '本地双人对战，互相攻击'),
            ('退出游戏', ''),
        ]

        for i, (name, desc) in enumerate(menu_items):
            y = 200 + i * 80
            is_selected = (i == self.selected_mode)

            # 选项背景
            if is_selected:
                pygame.draw.rect(self.screen, (50, 50, 80), (SCREEN_WIDTH // 2 - 200, y - 30, 400, 60))

            # 选项文字
            color = self.current_theme['accent_color'] if is_selected else WHITE
            text = self.font_medium.render(name, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)

            # 描述文字
            if desc:
                desc_text = self.font_small.render(desc, True, GRAY)
                desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, y + 35))
                self.screen.blit(desc_text, desc_rect)

        # 操作说明
        controls = [
            '使用 ↑ ↓ 键选择，按 空格键 或 Enter 确认',
        ]
        for i, text in enumerate(controls):
            rendered = self.font_small.render(text, True, (150, 150, 150))
            self.screen.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, 450 + i * 25))

        pygame.display.flip()

    def draw_single_player_menu(self):
        """绘制单人游戏模式选择菜单"""
        self.screen.fill(self.current_theme['bg_color'])

        # 标题
        title = self.font_large.render('单人游戏', True, self.current_theme['accent_color'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)

        # 模式选项
        mode_items = [
            ('classic', '经典模式', '10 个关卡挑战'),
            ('endless', '无尽模式', '无限挑战，速度越来越快'),
            ('sprint', '竞速模式', '尽快消除 40 行'),
            ('ultra', '限时模式', '2 分钟内获得最高分'),
            ('master', '大师模式', '20 层关卡，极限挑战'),
            ('zen', '禅模式', '无压力，放松体验'),
            ('challenge', '挑战模式', '特殊规则挑战'),
            ('custom', '自定义模式', '自定义游戏规则'),
        ]

        for i, (mode_key, name, desc) in enumerate(mode_items):
            y = 140 + i * 90
            is_selected = (i == self.selected_mode)

            # 选项背景
            if is_selected:
                pygame.draw.rect(self.screen, (50, 50, 80), (SCREEN_WIDTH // 2 - 220, y - 40, 440, 70))

            # 选项文字
            color = self.current_theme['accent_color'] if is_selected else WHITE
            text = self.font_medium.render(name, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)

            # 描述文字
            desc_text = self.font_small.render(desc, True, GRAY)
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, y + 35))
            self.screen.blit(desc_text, desc_rect)

        # 返回提示
        back_text = self.font_small.render('按 ESC 返回主菜单', True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, 520))
        self.screen.blit(back_text, back_rect)

        pygame.display.flip()

    def handle_main_menu_events(self):
        """处理主菜单事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_mode = (self.selected_mode - 1) % 3
                elif event.key == pygame.K_DOWN:
                    self.selected_mode = (self.selected_mode + 1) % 3
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.selected_mode == 0:
                        self.menu_state = 'single'
                        self.selected_mode = 0
                        return 'single_menu'
                    elif self.selected_mode == 1:
                        return 'dual'
                    else:
                        self.running = False
                        return None

        return 'menu'

    def handle_single_menu_events(self):
        """处理单人游戏菜单事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.menu_state = 'main'
                    self.selected_mode = 0
                    return 'main_menu'
                elif event.key == pygame.K_UP:
                    self.selected_mode = (self.selected_mode - 1) % 8
                elif event.key == pygame.K_DOWN:
                    self.selected_mode = (self.selected_mode + 1) % 8
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    modes = ['classic', 'endless', 'sprint', 'ultra', 'master', 'zen', 'challenge', 'custom']
                    return modes[self.selected_mode]

        return 'single_menu'

    def run(self):
        """运行菜单循环"""
        while self.running:
            if self.menu_state == 'main':
                self.draw_main_menu()
                result = self.handle_main_menu_events()
            elif self.menu_state == 'single':
                self.draw_single_player_menu()
                result = self.handle_single_menu_events()
            else:
                result = 'menu'

            if result and result not in ('menu', 'main_menu', 'single_menu'):
                return result

        pygame.quit()
        return None


def main():
    """主函数"""
    # 显示主菜单
    menu = GameMenu()
    mode = menu.run()

    if mode in ('classic', 'endless', 'sprint', 'ultra', 'master', 'zen', 'challenge', 'custom'):
        # 单人游戏模式
        game = TetrisGame(mode=mode)
        game.run()
    elif mode == 'dual':
        # 双人对战模式
        dual_game = TetrisDualGame()
        dual_game.run()
    else:
        # 退出
        pygame.quit()
        sys.exit()


class TetrisDualGame:
    """双人对战游戏类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((DUAL_SCREEN_WIDTH, DUAL_SCREEN_HEIGHT))
        pygame.display.set_caption('俄罗斯方块 - 双人对战')

        # 加载中文字体
        self.font_large = self._load_font(32)
        self.font_medium = self._load_font(20)
        self.font_small = self._load_font(14)

        # 初始化管理器
        self.sound_manager = SoundManager()

        # 当前主题
        self.current_theme_name = 'classic'
        self.current_theme = THEMES['classic']

        self.clock = pygame.time.Clock()
        self.reset_game()

        # 动画状态
        self.clearing_lines_p1 = []
        self.clearing_lines_p2 = []
        self.clear_animation_frame_p1 = 0
        self.clear_animation_frame_p2 = 0

    def _load_font(self, size):
        """加载字体，优先使用支持中文的字体"""
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        for path in font_paths:
            try:
                return pygame.font.Font(path, size)
            except:
                continue
        return pygame.font.SysFont('arial', size)

    def reset_game(self):
        """重置双人对战状态"""
        # 玩家 1（左侧）
        self.board_p1 = GameBoard()
        self.current_block_p1 = Block()
        self.next_block_p1 = Block()
        self.hold_block_p1 = None
        self.can_hold_p1 = True
        self.score_p1 = 0
        self.lines_cleared_p1 = 0
        self.combo_p1 = 0
        self.game_over_p1 = False

        # 玩家 2（右侧）
        self.board_p2 = GameBoard()
        self.current_block_p2 = Block()
        self.next_block_p2 = Block()
        self.hold_block_p2 = None
        self.can_hold_p2 = True
        self.score_p2 = 0
        self.lines_cleared_p2 = 0
        self.combo_p2 = 0
        self.game_over_p2 = False

        # 游戏状态
        self.paused = False
        self.winner = None  # 'p1' 或 'p2'
        self.running = True
        self.last_fall_time_p1 = pygame.time.get_ticks()
        self.last_fall_time_p2 = pygame.time.get_ticks()
        self.speed_p1 = 1000  # 玩家 1 速度
        self.speed_p2 = 1000  # 玩家 2 速度

        # 攻击/垃圾行系统
        self.pending_garbage_p1 = 0  # 玩家 1 待接收的垃圾行
        self.pending_garbage_p2 = 0  # 玩家 2 待接收的垃圾行

        # 动画状态
        self.clearing_lines_p1 = []
        self.clearing_lines_p2 = []
        self.clear_animation_frame_p1 = 0
        self.clear_animation_frame_p2 = 0
        self.attack_animation_p1 = 0
        self.attack_animation_p2 = 0

    def spawn_block_p1(self):
        """生成玩家 1 新方块"""
        self.current_block_p1 = self.next_block_p1
        self.next_block_p1 = Block()
        self.current_block_p1.x = DUAL_GRID_WIDTH // 2 - len(self.current_block_p1.shape[0]) // 2
        self.current_block_p1.y = 0
        self.can_hold_p1 = True

        if not self.board_p1.is_valid_position(self.current_block_p1):
            self.game_over_p1 = True
            self.winner = 'p2'
            self.sound_manager.play('gameover')

    def spawn_block_p2(self):
        """生成玩家 2 新方块"""
        self.current_block_p2 = self.next_block_p2
        self.next_block_p2 = Block()
        self.current_block_p2.x = DUAL_GRID_WIDTH // 2 - len(self.current_block_p2.shape[0]) // 2
        self.current_block_p2.y = 0
        self.can_hold_p2 = True

        if not self.board_p2.is_valid_position(self.current_block_p2):
            self.game_over_p2 = True
            self.winner = 'p1'
            self.sound_manager.play('gameover')

    def move_block_p1(self, dx, dy):
        """移动玩家 1 方块"""
        if self.board_p1.is_valid_position(self.current_block_p1, offset_x=dx, offset_y=dy):
            self.current_block_p1.x += dx
            self.current_block_p1.y += dy
            return True
        return False

    def move_block_p2(self, dx, dy):
        """移动玩家 2 方块"""
        if self.board_p2.is_valid_position(self.current_block_p2, offset_x=dx, offset_y=dy):
            self.current_block_p2.x += dx
            self.current_block_p2.y += dy
            return True
        return False

    def rotate_block_p1(self):
        """旋转玩家 1 方块"""
        original_shape = self.current_block_p1.shape
        self.current_block_p1.shape = self.current_block_p1.rotate()

        if not self.board_p1.is_valid_position(self.current_block_p1):
            if self.board_p1.is_valid_position(self.current_block_p1, offset_x=-1, offset_y=0):
                self.current_block_p1.x -= 1
            elif self.board_p1.is_valid_position(self.current_block_p1, offset_x=1, offset_y=0):
                self.current_block_p1.x += 1
            elif self.board_p1.is_valid_position(self.current_block_p1, offset_x=-2, offset_y=0):
                self.current_block_p1.x -= 2
            elif self.board_p1.is_valid_position(self.current_block_p1, offset_x=2, offset_y=0):
                self.current_block_p1.x += 2
            else:
                self.current_block_p1.shape = original_shape
                return

        self.sound_manager.play('rotate')

    def rotate_block_p2(self):
        """旋转玩家 2 方块"""
        original_shape = self.current_block_p2.shape
        self.current_block_p2.shape = self.current_block_p2.rotate()

        if not self.board_p2.is_valid_position(self.current_block_p2):
            if self.board_p2.is_valid_position(self.current_block_p2, offset_x=-1, offset_y=0):
                self.current_block_p2.x -= 1
            elif self.board_p2.is_valid_position(self.current_block_p2, offset_x=1, offset_y=0):
                self.current_block_p2.x += 1
            elif self.board_p2.is_valid_position(self.current_block_p2, offset_x=-2, offset_y=0):
                self.current_block_p2.x -= 2
            elif self.board_p2.is_valid_position(self.current_block_p2, offset_x=2, offset_y=0):
                self.current_block_p2.x += 2
            else:
                self.current_block_p2.shape = original_shape
                return

        self.sound_manager.play('rotate')

    def hard_drop_p1(self):
        """玩家 1 硬降方块"""
        drop_distance = 0
        while self.move_block_p1(0, 1):
            drop_distance += 1
        self.score_p1 += drop_distance * 2
        self.sound_manager.play('drop')
        self.lock_current_block_p1()

    def hard_drop_p2(self):
        """玩家 2 硬降方块"""
        drop_distance = 0
        while self.move_block_p2(0, 1):
            drop_distance += 1
        self.score_p2 += drop_distance * 2
        self.sound_manager.play('drop')
        self.lock_current_block_p2()

    def hold_block_p1(self):
        """玩家 1 暂存方块"""
        if not self.can_hold_p1:
            return

        if self.hold_block_p1 is None:
            self.hold_block_p1 = Block(self.current_block_p1.shape_type)
            self.spawn_block_p1()
        else:
            current_type = self.current_block_p1.shape_type
            self.current_block_p1 = Block(self.hold_block_p1.shape_type)
            self.hold_block_p1 = Block(current_type)
            self.current_block_p1.x = DUAL_GRID_WIDTH // 2 - len(self.current_block_p1.shape[0]) // 2
            self.current_block_p1.y = 0

        self.can_hold_p1 = False
        self.sound_manager.play('rotate')

    def hold_block_p2(self):
        """玩家 2 暂存方块"""
        if not self.can_hold_p2:
            return

        if self.hold_block_p2 is None:
            self.hold_block_p2 = Block(self.current_block_p2.shape_type)
            self.spawn_block_p2()
        else:
            current_type = self.current_block_p2.shape_type
            self.current_block_p2 = Block(self.hold_block_p2.shape_type)
            self.hold_block_p2 = Block(current_type)
            self.current_block_p2.x = DUAL_GRID_WIDTH // 2 - len(self.current_block_p2.shape[0]) // 2
            self.current_block_p2.y = 0

        self.can_hold_p2 = False
        self.sound_manager.play('rotate')

    def calculate_attack_lines(self, lines, combo):
        """计算攻击行数（基于消除行数和连击）"""
        attack = 0
        if lines == 1:
            attack = 0
        elif lines == 2:
            attack = 1
        elif lines == 3:
            attack = 2
        elif lines == 4:
            attack = 4
        # 连击 bonus
        if combo > 0:
            attack += min(combo, 5)  # 最多额外 5 行
        return attack

    def lock_current_block_p1(self):
        """锁定玩家 1 当前方块"""
        self.board_p1.lock_block(self.current_block_p1)
        lines = self._get_full_lines_p1()

        if lines:
            self.clearing_lines_p1 = lines
            self.clear_animation_frame_p1 = 0
            # 计算攻击
            attack = self.calculate_attack_lines(len(lines), self.combo_p1 + 1)
            if attack > 0:
                self.pending_garbage_p2 += attack
                self.attack_animation_p1 = 20
        else:
            self.combo_p1 = 0
            self.spawn_block_p1()

    def lock_current_block_p2(self):
        """锁定玩家 2 当前方块"""
        self.board_p2.lock_block(self.current_block_p2)
        lines = self._get_full_lines_p2()

        if lines:
            self.clearing_lines_p2 = lines
            self.clear_animation_frame_p2 = 0
            # 计算攻击
            attack = self.calculate_attack_lines(len(lines), self.combo_p2 + 1)
            if attack > 0:
                self.pending_garbage_p1 += attack
                self.attack_animation_p2 = 20
        else:
            self.combo_p2 = 0
            self.spawn_block_p2()

    def _get_full_lines_p1(self):
        """获取玩家 1 所有满行的索引"""
        full_lines = []
        for y in range(DUAL_GRID_HEIGHT):
            if all(self.board_p1.grid[y]):
                full_lines.append(y)
        return full_lines

    def _get_full_lines_p2(self):
        """获取玩家 2 所有满行的索引"""
        full_lines = []
        for y in range(DUAL_GRID_HEIGHT):
            if all(self.board_p2.grid[y]):
                full_lines.append(y)
        return full_lines

    def add_garbage_lines(self, player, count):
        """添加垃圾行到指定玩家"""
        board = self.board_p1 if player == 'p1' else self.board_p2
        for _ in range(min(count, 10)):  # 最多一次加 10 行
            # 删除最上面一行
            del board.grid[0]
            # 在底部添加一行带随机缺口的垃圾行
            gap = random.randint(0, DUAL_GRID_WIDTH - 1)
            garbage_row = [GRAY for _ in range(DUAL_GRID_WIDTH)]
            garbage_row[gap] = None
            board.grid.append(garbage_row)

    def _clear_lines_with_animation_p1(self):
        """执行玩家 1 消行动画并消除行"""
        if self.clear_animation_frame_p1 >= CLEAR_ANIMATION_FRAMES:
            # 动画完成，实际消除行
            for y in sorted(self.clearing_lines_p1, reverse=True):
                del self.board_p1.grid[y]
                self.board_p1.grid.insert(0, [None for _ in range(DUAL_GRID_WIDTH)])

            lines = len(self.clearing_lines_p1)
            self.lines_cleared_p1 += lines
            self.combo_p1 += 1

            # 计分
            line_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            base_score = line_scores.get(lines, 0)
            combo_bonus = self.combo_p1 * 50
            self.score_p1 += base_score + combo_bonus

            # 处理垃圾行
            if self.pending_garbage_p1 > 0:
                self.add_garbage_lines('p1', self.pending_garbage_p1)
                self.pending_garbage_p1 = 0

            self.sound_manager.play_clear(lines)
            self.clearing_lines_p1 = []
            self.clear_animation_frame_p1 = 0
            self.spawn_block_p1()
        else:
            self.clear_animation_frame_p1 += 1

    def _clear_lines_with_animation_p2(self):
        """执行玩家 2 消行动画并消除行"""
        if self.clear_animation_frame_p2 >= CLEAR_ANIMATION_FRAMES:
            for y in sorted(self.clearing_lines_p2, reverse=True):
                del self.board_p2.grid[y]
                self.board_p2.grid.insert(0, [None for _ in range(DUAL_GRID_WIDTH)])

            lines = len(self.clearing_lines_p2)
            self.lines_cleared_p2 += lines
            self.combo_p2 += 1

            line_scores = {1: 100, 2: 300, 3: 500, 4: 800}
            base_score = line_scores.get(lines, 0)
            combo_bonus = self.combo_p2 * 50
            self.score_p2 += base_score + combo_bonus

            if self.pending_garbage_p2 > 0:
                self.add_garbage_lines('p2', self.pending_garbage_p2)
                self.pending_garbage_p2 = 0

            self.sound_manager.play_clear(lines)
            self.clearing_lines_p2 = []
            self.clear_animation_frame_p2 = 0
            self.spawn_block_p2()
        else:
            self.clear_animation_frame_p2 += 1

    def _draw_block_cell(self, draw_x, draw_y, color, block_size):
        """绘制单个方块单元格"""
        pygame.draw.rect(self.screen, color,
                        (draw_x + 1, draw_y + 1, block_size - 2, block_size - 2))
        highlight = tuple(min(255, c + 50) for c in color)
        pygame.draw.line(self.screen, highlight,
                        (draw_x + 2, draw_y + 2),
                        (draw_x + block_size - 3, draw_y + 2), 2)
        pygame.draw.line(self.screen, highlight,
                        (draw_x + 2, draw_y + 2),
                        (draw_x + 2, draw_y + block_size - 3), 2)

    def _draw_grid(self, x_offset, board, current_block, ghost_y=None, clearing_lines=None, clear_frame=0, block_size=DUAL_BLOCK_SIZE):
        """绘制游戏网格"""
        grid_width = DUAL_GRID_WIDTH
        grid_height = DUAL_GRID_HEIGHT

        # 绘制背景
        pygame.draw.rect(self.screen, (30, 30, 50),
                        (x_offset, 0, grid_width * block_size, grid_height * block_size))

        # 绘制网格线
        for x in range(grid_width + 1):
            pygame.draw.line(self.screen, (50, 50, 70),
                           (x_offset + x * block_size, 0),
                           (x_offset + x * block_size, grid_height * block_size))
        for y in range(grid_height + 1):
            pygame.draw.line(self.screen, (50, 50, 70),
                           (x_offset, y * block_size),
                           (x_offset + grid_width * block_size, y * block_size))

        # 绘制已锁定的方块
        for y, row in enumerate(board.grid):
            for x, color in enumerate(row):
                if color:
                    draw_x = x_offset + x * block_size
                    draw_y = y * block_size
                    self._draw_block_cell(draw_x, draw_y, color, block_size)

        # 绘制消行动画
        if clearing_lines and clear_frame > 0:
            progress = clear_frame / CLEAR_ANIMATION_FRAMES
            flash_color = (255, 255, 255) if int(progress * 10) % 2 == 0 else (255, 200, 100)
            for y in clearing_lines:
                for x in range(grid_width):
                    draw_x = x_offset + x * block_size
                    draw_y = y * block_size
                    pygame.draw.rect(self.screen, flash_color,
                                   (draw_x + 1, draw_y + 1, block_size - 2, block_size - 2))

        # 绘制影子方块
        if current_block and ghost_y is not None:
            for y, row in enumerate(current_block.shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_x = x_offset + (current_block.x + x) * block_size
                        draw_y = (ghost_y + y) * block_size
                        pygame.draw.rect(self.screen, current_block.color,
                                       (draw_x + 1, draw_y + 1, block_size - 2, block_size - 2), 2)

        # 绘制当前方块
        if current_block:
            for y, row in enumerate(current_block.shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_x = x_offset + (current_block.x + x) * block_size
                        draw_y = (current_block.y + y) * block_size
                        self._draw_block_cell(draw_x, draw_y, current_block.color, block_size)

    def _draw_player_board(self, player_num, x_offset):
        """绘制玩家游戏区域"""
        is_p1 = player_num == 1
        board = self.board_p1 if is_p1 else self.board_p2
        current_block = self.current_block_p1 if is_p1 else self.current_block_p2
        ghost_y = None
        clearing_lines = self.clearing_lines_p1 if is_p1 else self.clearing_lines_p2
        clear_frame = self.clear_animation_frame_p1 if is_p1 else self.clearing_lines_p2

        if current_block and not (self.game_over_p1 if is_p1 else self.game_over_p2):
            # 获取影子位置
            ghost_y = board.get_ghost_y(current_block)

        self._draw_grid(x_offset, board, current_block, ghost_y, clearing_lines, clear_frame)

    def _draw_mini_board(self, board, x, y, title, block_size=20):
        """绘制小型预览板（下一个/暂存）"""
        # 标题
        text = self.font_small.render(title, True, self.current_theme['text_color'])
        self.screen.blit(text, (x, y))

        # 棋盘背景
        pygame.draw.rect(self.screen, (30, 30, 50),
                        (x, y + 15, GRID_WIDTH * block_size, GRID_HEIGHT * block_size))

        # 绘制方块
        for board_y, row in enumerate(board.grid):
            for board_x, color in enumerate(row):
                if color:
                    draw_x = x + board_x * block_size
                    draw_y = y + 15 + board_y * block_size
                    pygame.draw.rect(self.screen, color,
                                   (draw_x, draw_y, block_size, block_size))

    def _draw_next_block(self, block, x, y, title, block_size=20):
        """绘制下一个方块预览"""
        text = self.font_small.render(title, True, self.current_theme['text_color'])
        self.screen.blit(text, (x, y))

        for row_idx, row in enumerate(block.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    draw_x = x + col_idx * block_size
                    draw_y = y + 15 + row_idx * block_size
                    pygame.draw.rect(self.screen, block.color,
                                   (draw_x, draw_y, block_size, block_size))

    def _draw_hold_block(self, block, x, y, title, can_use=True, block_size=20):
        """绘制暂存方块"""
        text = self.font_small.render(title, True, self.current_theme['text_color'])
        self.screen.blit(text, (x, y))

        if block:
            color = block.color if can_use else tuple(c // 2 for c in block.color)
            for row_idx, row in enumerate(block.shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        draw_x = x + col_idx * block_size
                        draw_y = y + 15 + row_idx * block_size
                        pygame.draw.rect(self.screen, color,
                                       (draw_x, draw_y, block_size, block_size))

    def draw_ui(self):
        """绘制 UI 信息"""
        bs = DUAL_BLOCK_SIZE
        gw = DUAL_GRID_WIDTH

        # 玩家 1 信息（左侧）
        p1_color = self.current_theme['accent_color']
        p1_name = self.font_medium.render('玩家 1', True, p1_color)
        self.screen.blit(p1_name, (10, 5))

        p1_score = self.font_small.render(f'分数：{self.score_p1}', True, WHITE)
        self.screen.blit(p1_score, (10, 25))

        p1_lines = self.font_small.render(f'消行：{self.lines_cleared_p1}', True, WHITE)
        self.screen.blit(p1_lines, (10, 45))

        p1_combo = self.font_small.render(f'连击：{self.combo_p1}', True, (255, 215, 0) if self.combo_p1 > 0 else GRAY)
        self.screen.blit(p1_combo, (10, 65))

        # 垃圾行指示
        if self.pending_garbage_p1 > 0:
            garbage_text = self.font_small.render(f'垃圾行：{self.pending_garbage_p1}', True, (255, 100, 100))
            self.screen.blit(garbage_text, (10, 85))

        # 玩家 1 暂存和下一个
        self._draw_hold_block(self.hold_block_p1, 10, 110, '暂存 (Q)', self.can_hold_p1)
        self._draw_next_block(self.next_block_p1, 10, 180, '下一个', bs)

        # 玩家 2 信息（右侧）
        p2_color = (100, 255, 100)
        p2_name = self.font_medium.render('玩家 2', True, p2_color)
        p2_name_rect = p2_name.get_rect(topright=(DUAL_SCREEN_WIDTH - 10, 5))
        self.screen.blit(p2_name, p2_name_rect)

        p2_score = self.font_small.render(f'分数：{self.score_p2}', True, WHITE)
        p2_score_rect = p2_score.get_rect(topright=(DUAL_SCREEN_WIDTH - 10, 25))
        self.screen.blit(p2_score, p2_score_rect)

        p2_lines = self.font_small.render(f'消行：{self.lines_cleared_p2}', True, WHITE)
        p2_lines_rect = p2_lines.get_rect(topright=(DUAL_SCREEN_WIDTH - 10, 45))
        self.screen.blit(p2_lines, p2_lines_rect)

        p2_combo = self.font_small.render(f'连击：{self.combo_p2}', True, (255, 215, 0) if self.combo_p2 > 0 else GRAY)
        p2_combo_rect = p2_combo.get_rect(topright=(DUAL_SCREEN_WIDTH - 10, 65))
        self.screen.blit(p2_combo, p2_combo_rect)

        if self.pending_garbage_p2 > 0:
            garbage_text = self.font_small.render(f'垃圾行：{self.pending_garbage_p2}', True, (255, 100, 100))
            garbage_rect = garbage_text.get_rect(topright=(DUAL_SCREEN_WIDTH - 10, 85))
            self.screen.blit(garbage_text, garbage_rect)

        # 玩家 2 暂存和下一个
        self._draw_hold_block(self.hold_block_p2, DUAL_SCREEN_WIDTH - 110, 110, '暂存 (M)', self.can_hold_p2, bs)
        self._draw_next_block(self.next_block_p2, DUAL_SCREEN_WIDTH - 110, 180, '下一个', bs)

        # 中央标题
        title = self.font_large.render('双人对战', True, self.current_theme['accent_color'])
        title_rect = title.get_rect(centerx=DUAL_SCREEN_WIDTH // 2, top=10)
        self.screen.blit(title, title_rect)

        # 操作说明
        controls_p1 = [
            '玩家 1 操作:',
            'WASD - 移动',
            'E - 旋转',
            'F - 硬降',
            'Q - 暂存',
        ]
        for i, text in enumerate(controls_p1):
            rendered = self.font_small.render(text, True, WHITE)
            self.screen.blit(rendered, (10, 280 + i * 20))

        controls_p2 = [
            '玩家 2 操作:',
            '箭头键 - 移动',
            '0 - 旋转',
            'Enter- 硬降',
            'M - 暂存',
        ]
        for i, text in enumerate(controls_p2):
            rendered = self.font_small.render(text, True, WHITE)
            self.screen.blit(rendered, (DUAL_SCREEN_WIDTH - 100, 280 + i * 20))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((DUAL_SCREEN_WIDTH, DUAL_SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        if self.winner == 'p1':
            result_text = self.font_large.render('玩家 1 获胜!', True, (100, 150, 255))
        elif self.winner == 'p2':
            result_text = self.font_large.render('玩家 2 获胜!', True, (100, 255, 150))
        else:
            result_text = self.font_large.render('游戏结束', True, WHITE)

        score_text = self.font_medium.render(f'P1: {self.score_p1}  |  P2: {self.score_p2}', True, WHITE)
        restart_text = self.font_medium.render('按 R 重新开始', True, WHITE)

        result_rect = result_text.get_rect(center=(DUAL_SCREEN_WIDTH // 2, DUAL_SCREEN_HEIGHT // 2 - 50))
        score_rect = score_text.get_rect(center=(DUAL_SCREEN_WIDTH // 2, DUAL_SCREEN_HEIGHT // 2))
        restart_rect = restart_text.get_rect(center=(DUAL_SCREEN_WIDTH // 2, DUAL_SCREEN_HEIGHT // 2 + 50))

        self.screen.blit(result_text, result_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_rect)

    def draw_pause(self):
        """绘制暂停画面"""
        overlay = pygame.Surface((DUAL_SCREEN_WIDTH, DUAL_SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render('游戏暂停', True, WHITE)
        pause_rect = pause_text.get_rect(center=(DUAL_SCREEN_WIDTH // 2, DUAL_SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(self.current_theme['bg_color'])

        # 绘制玩家 1 区域（左侧）
        p1_x = 80
        self._draw_player_board(1, p1_x)

        # 绘制玩家 2 区域（右侧）
        p2_x = DUAL_SCREEN_WIDTH - 80 - DUAL_GRID_WIDTH * DUAL_BLOCK_SIZE
        self._draw_player_board(2, p2_x)

        # 绘制 UI
        self.draw_ui()

        # 绘制游戏结束或暂停画面
        if self.game_over_p1 or self.game_over_p2:
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

                if self.game_over_p1 or self.game_over_p2 or self.paused:
                    continue

                # 玩家 1 控制 (WASD + QEF)
                if event.key == pygame.K_a:
                    self.move_block_p1(-1, 0)
                elif event.key == pygame.K_d:
                    self.move_block_p1(1, 0)
                elif event.key == pygame.K_s:
                    if self.move_block_p1(0, 1):
                        self.score_p1 += 1
                elif event.key == pygame.K_w:
                    self.rotate_block_p1()
                elif event.key == pygame.K_f:
                    self.hard_drop_p1()
                elif event.key == pygame.K_q:
                    self.hold_block_p1()

                # 玩家 2 控制 (箭头键 + M/0/Enter)
                if event.key == pygame.K_LEFT:
                    self.move_block_p2(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_block_p2(1, 0)
                elif event.key == pygame.K_DOWN:
                    if self.move_block_p2(0, 1):
                        self.score_p2 += 1
                elif event.key == pygame.K_UP:
                    self.rotate_block_p2()
                elif event.key == pygame.K_RETURN:
                    self.hard_drop_p2()
                elif event.key == pygame.K_m:
                    self.hold_block_p2()
                elif event.key == pygame.K_0:
                    self.hard_drop_p2()

                # 公共控制
                if event.key == pygame.K_p:
                    self.paused = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_p and not self.game_over_p1 and not self.game_over_p2:
                    self.paused = False

    def update(self):
        """更新游戏状态"""
        if self.paused or self.game_over_p1 or self.game_over_p2:
            return

        # 更新玩家 1
        if not self.clearing_lines_p1:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_fall_time_p1 > self.speed_p1:
                self.last_fall_time_p1 = current_time
                if not self.move_block_p1(0, 1):
                    self.lock_current_block_p1()
        else:
            self._clear_lines_with_animation_p1()

        # 更新玩家 2
        if not self.clearing_lines_p2:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_fall_time_p2 > self.speed_p2:
                self.last_fall_time_p2 = current_time
                if not self.move_block_p2(0, 1):
                    self.lock_current_block_p2()
        else:
            self._clear_lines_with_animation_p2()

    def run(self):
        """双人对战主循环"""
        # 播放背景音乐
        self.sound_manager.play_music()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    main()
