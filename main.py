import pygame
import win32api
import win32con
import win32gui
import math
import random
import time
import sys
import ctypes
from pynput import mouse
from enum import Enum, auto

# ================= 1. 系统配置 =================
DEBUG_MODE = False 

def log_error(msg):
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

# 高DPI感知
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

try:
    SCREEN_WIDTH = win32api.GetSystemMetrics(0)
    SCREEN_HEIGHT = win32api.GetSystemMetrics(1)
except:
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

# ================= 2. 视觉参数 =================
PIXEL_SCALE = 4      # 像素放大倍数 (每个点4x4像素)
TASKBAR_HEIGHT = 80  
GROUND_Y = SCREEN_HEIGHT - TASKBAR_HEIGHT 
# 基于新的Grid高度(18)，计算基准Y坐标
FOX_BASE_HEIGHT = 18 * PIXEL_SCALE 
FOX_Y_BASE = GROUND_Y - FOX_BASE_HEIGHT + 8 # +8 稍微沉底一点，让影子不悬空

# 物理参数
GRAVITY = 0.8
BOUNCE_DAMPING = 0.5
FOX_RUN_SPEED = 7
INTERACT_DIST = 60

# --- 颜色映射字典 (Color Map) ---
# 0: 透明
# 1: 深褐 (Deep Brown)
# 2: 日落金 (Sunset Gold)
# 3: 奶油白 (Cream White)
# 4: 腮红粉 (Blush Pink)

COLOR_MAP = {
    0: None,              # 透明
    1: (70, 40, 10),      # 深褐
    2: (235, 150, 40),    # 日落金
    3: (255, 245, 225),   # 奶油白
    4: (255, 160, 160)    # 腮红粉
}

COLOR_TRANSPARENT_KEY = (255, 0, 128) # 用于窗口透明色键

# ================= 3. 像素数据 (Grids) =================

# 1. 待机状态 (Idle) - 坐姿
GRID_SIT = [
    [0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], 
    [0,0,1,2,1,0,0,0,0,0,0,1,2,1,0,0,0,0,0,0], 
    [0,0,1,3,2,1,0,0,0,0,1,3,2,1,0,0,0,0,0,0], 
    [0,0,1,3,3,2,1,1,1,1,2,3,3,1,0,0,0,0,0,0], 
    [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0,0,0,0,0], 
    [0,0,0,1,2,1,2,2,2,2,1,2,1,0,0,0,0,0,0,0], 
    [0,0,0,0,1,3,3,1,1,3,3,1,0,0,0,0,0,0,0,0], 
    [0,0,0,0,0,1,3,3,3,3,1,0,0,0,0,0,0,0,0,0], 
    [0,0,0,0,0,0,1,3,3,1,0,0,0,0,0,0,0,0,0,0], 
    [0,0,0,0,0,2,2,3,3,2,2,0,0,0,0,0,0,1,1,0], 
    [0,0,0,0,2,2,2,3,3,2,2,2,0,0,0,0,1,3,3,1], 
    [0,0,0,2,2,2,2,3,3,2,2,2,2,0,0,1,3,3,3,1], 
    [0,0,2,2,2,2,2,3,3,2,2,2,2,2,1,2,3,3,2,1], 
    [0,1,2,2,2,2,2,3,3,2,2,2,2,2,2,2,2,2,2,1], 
    [1,2,2,2,2,2,2,3,3,2,2,2,2,2,2,2,2,2,1,0], 
    [0,1,1,2,2,2,2,3,3,2,2,2,1,1,2,2,2,1,0,0], 
    [0,0,0,1,1,0,0,1,1,0,0,1,1,1,1,1,1,0,0,0], 
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# 2. 行走帧1 (迈左腿)
GRID_WALK_1 = [
    [0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,2,1,1,3,1,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,3,2,2,3,2,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,2,1,2,2,2,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,3,3,3,1,0,0,0,0,0,0,0,0,0,0,1],
    [0,0,0,0,0,1,3,1,2,2,2,2,2,2,0,0,0,0,1,3],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,0,0,1,3,3],
    [0,0,0,0,2,2,3,3,2,2,2,2,2,2,2,1,1,3,3,2],
    [0,0,0,0,2,3,3,3,2,2,2,2,2,2,2,2,2,2,2,1],
    [0,0,0,0,2,3,3,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,0,0,0,1,2,2,1,0,0,0,0,1,2,2,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# 3. 行走帧2 (迈右腿)
GRID_WALK_2 = [
    [0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,2,1,1,3,1,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,3,2,2,3,2,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,2,1,2,2,2,1,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,1,3,3,3,1,0,0,0,0,0,0,0,0,0,1,1],
    [0,0,0,0,0,1,3,1,2,2,2,2,2,2,0,0,0,1,3,3],
    [0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,0,1,3,3,2],
    [0,0,0,0,2,2,3,3,2,2,2,2,2,2,2,1,2,2,2,1],
    [0,0,0,0,2,3,3,3,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,0,0,0,2,3,3,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0,0],
    [0,0,0,0,1,2,2,2,1,0,0,1,2,2,2,1,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# 4. 仰望 (Looking Up)
GRID_LOOK_UP = [
    [0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,1,2,1,0,0,0,0,0,0,1,2,1,0,0,0,0],
    [0,0,0,1,2,3,2,1,0,0,0,0,1,2,3,2,1,0,0,0],
    [0,0,0,1,2,2,2,2,1,1,1,1,2,2,2,2,1,0,0,0],
    [0,0,0,1,2,1,2,2,2,2,2,2,2,1,2,2,1,0,0,0],
    [0,0,0,0,1,3,3,1,1,1,1,1,1,3,3,1,0,0,0,0],
    [0,0,0,0,0,1,3,3,3,3,3,3,3,3,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,2,3,3,3,3,2,1,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,3,3,3,3,3,3,2,2,0,0,0,1,1],
    [0,0,0,0,2,2,2,3,3,3,3,3,3,2,2,2,0,1,3,3],
    [0,0,0,2,2,2,2,3,3,3,3,3,3,2,2,2,1,3,3,3],
    [0,0,2,2,2,2,2,2,3,3,3,3,2,2,2,2,2,3,3,2],
    [0,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,0],
    [0,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,0,0],
    [0,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

# 5. 开心互动 (Happy)
GRID_HAPPY = [
    [0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], 
    [0,0,1,2,1,0,0,0,0,0,0,1,2,1,0,0,0,0,0,0],
    [0,0,1,3,2,1,0,0,0,0,1,3,2,1,0,0,0,0,0,0],
    [0,0,1,3,3,2,1,1,1,1,2,3,3,1,0,0,0,0,0,0],
    [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0,0,0,0,0],
    [0,0,0,1,2,1,1,2,2,2,1,1,2,1,0,0,0,0,0,0],
    [0,0,0,0,1,3,4,1,1,4,3,1,0,0,0,0,0,1,0,0],
    [0,0,0,0,0,1,3,3,3,3,1,0,0,0,0,0,1,3,1,0],
    [0,0,0,0,0,0,1,3,3,1,0,0,0,0,1,3,3,3,1,0],
    [0,0,0,0,0,2,2,3,3,2,2,0,0,1,3,3,3,2,1,0],
    [0,0,0,0,2,2,2,3,3,2,2,2,1,2,3,3,2,1,0,0],
    [0,0,0,2,2,2,2,3,3,2,2,2,2,1,2,2,1,0,0,0],
    [0,0,2,2,2,2,2,3,3,2,2,2,2,2,1,1,0,0,0,0],
    [0,1,2,2,2,2,2,3,3,2,2,2,2,2,2,1,0,0,0,0],
    [1,2,2,2,2,2,2,3,3,2,2,2,2,2,2,1,0,0,0,0],
    [0,1,1,2,2,2,2,3,3,2,2,2,1,1,2,1,0,0,0,0],
    [0,0,0,1,1,0,0,1,1,0,0,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

class FoxState(Enum):
    SIT_IDLE = auto()    # 坐着待机
    RUNNING = auto()     # 奔跑
    LOOKING_UP = auto()  # 看星星
    CIRCLING = auto()    # 围着星星转
    PETTING = auto()     # 被抚摸
    HIDDEN = auto()      # 躲避全屏
    ENTERING = auto()    # 回归

# ================= 4. 视觉绘制器 =================
class PixelDrawer:
    @staticmethod
    def draw_fox(surface, x, y, facing_right, state, tick):
        
        # --- 1. 选择 Grid 和 动画逻辑 ---
        grid = GRID_SIT
        offset_y = 0
        
        # A. 待机 (呼吸感)
        if state == FoxState.SIT_IDLE:
            grid = GRID_SIT
            if (tick // 30) % 2 == 0:
                offset_y = 1
            else:
                offset_y = 0

        # B. 奔跑/转圈 (行走动画 + 跳跃)
        elif state == FoxState.RUNNING or state == FoxState.CIRCLING or state == FoxState.ENTERING:
            if (tick // 6) % 2 == 0:
                grid = GRID_WALK_1
            else:
                grid = GRID_WALK_2
            
            # 奔跑跳跃
            jump_phase = math.sin(tick * 0.4) 
            offset_y = int(abs(jump_phase) * -5)

        # C. 仰望
        elif state == FoxState.LOOKING_UP:
            grid = GRID_LOOK_UP
        
        # D. 互动
        elif state == FoxState.PETTING:
            grid = GRID_HAPPY
            offset_y = 2

        # --- 2. 绘制像素 ---
        rows = len(grid)
        cols = len(grid[0])
        pixel_size = PIXEL_SCALE
        
        # 居中对齐计算
        draw_start_x = x - (cols * pixel_size) // 2
        draw_start_y = y + offset_y

        for r in range(rows):
            for c in range(cols):
                # ==========================================
                # [关键修改] 翻转逻辑修正
                # 原始素材是面朝左的。
                # 如果 facing_right 为 True，我们需要翻转它(镜像)。
                # 如果 facing_right 为 False，我们直接用原图。
                # ==========================================
                col_idx = c
                if facing_right: 
                    col_idx = cols - 1 - c
                # ==========================================
                
                color_code = grid[r][col_idx]
                if color_code == 0: continue
                
                color = COLOR_MAP.get(color_code)
                if not color: continue

                rect = (
                    draw_start_x + c * pixel_size,
                    draw_start_y + r * pixel_size,
                    pixel_size, 
                    pixel_size
                )
                pygame.draw.rect(surface, color, rect)

    @staticmethod
    def draw_star(surface, x, y, tick):
        # 纯五角星绘制，无外圈
        # 缩放呼吸
        scale = 1.0 + math.sin(tick * 0.1) * 0.15
        size = 12 * scale
        
        # 颜色: 金色带一点亮黄
        color = (255, 225, 50) 
        
        points = []
        rotation = tick * 0.05 # 旋转
        
        for i in range(5):
            # 外顶点
            angle = math.radians(i * 72 - 18) + rotation
            px = x + size * math.cos(angle)
            py = y + size * math.sin(angle)
            points.append((px, py))
            
            # 内顶点 (更加尖锐，内径系数设为0.4)
            angle2 = math.radians(i * 72 + 18) + rotation
            px2 = x + (size * 0.4) * math.cos(angle2)
            py2 = y + (size * 0.4) * math.sin(angle2)
            points.append((px2, py2))
            
        pygame.draw.polygon(surface, color, points)

# ================= 5. 主逻辑核心 =================
class DesktopPet:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
        self.clock = pygame.time.Clock()
        self.hwnd = pygame.display.get_wm_info()["window"]
        win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
        
        # 设置透明
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        if DEBUG_MODE:
             win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 100, win32con.LWA_ALPHA)
        else:
             win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*COLOR_TRANSPARENT_KEY), 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        # 状态
        self.fox_x = SCREEN_WIDTH // 2
        self.state = FoxState.SIT_IDLE
        self.facing_right = True
        self.tick = 0
        self.last_state_change = time.time()
        
        # 星星
        self.star = {'x':0, 'y':0, 'vx':0, 'vy':0, 'active':False, 'physic':False}
        self.particles = [] # 灰尘/爱心粒子
        
        # 鼠标监听
        self.mouse_pos = (0,0)
        self.click_queue = [] 
        self.running = True
        self.listener = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click)
        self.listener.start()

    def on_mouse_move(self, x, y):
        self.mouse_pos = (x, y)

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.click_queue.append((x, y))
        if pressed and button == mouse.Button.right:
            if abs(x - self.fox_x) < 50 and abs(y - FOX_Y_BASE) < 50:
                self.running = False

    def spawn_dust(self, x, y):
        """生成奔跑时的扬尘"""
        self.particles.append({
            'x': x, 'y': y + 15,
            'vx': random.uniform(-1, 1),
            'vy': random.uniform(-1, 0),
            'life': 10,
            'color': (200, 190, 180), # 灰色尘土
            'size': random.randint(3, 6)
        })

    def spawn_love(self, x, y):
        """生成抚摸时的爱心"""
        self.particles.append({
            'x': x, 'y': y,
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(-3, -1),
            'life': 30,
            'color': (255, 160, 160),
            'size': random.randint(4, 8)
        })

    def update(self):
        self.tick += 1
        current_time = time.time()
        
        # 0. 处理点击
        if self.click_queue:
            cx, cy = self.click_queue.pop(0)
            if abs(cx - self.fox_x) < 60 and abs(cy - FOX_Y_BASE) < 60:
                self.state = FoxState.PETTING
                self.last_state_change = current_time
                self.spawn_love(self.fox_x, FOX_Y_BASE - 40)
            else:
                if self.state != FoxState.PETTING and not self.star['physic']:
                    self.star['x'], self.star['y'] = cx, cy
                    self.star['vx'], self.star['vy'] = 0, 0
                    self.star['active'] = True
                    self.star['physic'] = True
                    self.state = FoxState.RUNNING

        # 1. 状态逻辑
        
        # A. 抚摸
        if self.state == FoxState.PETTING:
            if current_time - self.last_state_change > 2.0:
                self.state = FoxState.SIT_IDLE
            return

        # B. 星星物理
        if self.star['physic']:
            self.star['vy'] += GRAVITY
            self.star['x'] += self.star['vx']
            self.star['y'] += self.star['vy']
            
            if self.star['y'] >= GROUND_Y:
                self.star['y'] = GROUND_Y
                if abs(self.star['vy']) > 2:
                    self.star['vy'] = -self.star['vy'] * BOUNCE_DAMPING
                    self.star['vx'] = (1 if self.fox_x > self.star['x'] else -1) * random.uniform(2, 4)
                else:
                    self.star['vy'] = 0
                    self.star['vx'] = 0
            
            # 追逐逻辑
            dx = self.star['x'] - self.fox_x
            if abs(dx) > INTERACT_DIST:
                self.state = FoxState.RUNNING
                self.fox_x += FOX_RUN_SPEED * (1 if dx > 0 else -1)
                self.facing_right = (dx > 0)
                # 奔跑产生尘土
                if self.tick % 5 == 0:
                    offset_x = -20 if self.facing_right else 20
                    self.spawn_dust(self.fox_x + offset_x, FOX_Y_BASE + 30)
            else:
                if (GROUND_Y - self.star['y']) < 50:
                    self.star['physic'] = False
                    self.state = FoxState.CIRCLING
                    self.last_state_change = current_time
                else:
                    self.state = FoxState.LOOKING_UP
                    self.facing_right = (dx > 0)
        
        # C. 转圈互动
        elif self.state == FoxState.CIRCLING:
            if current_time - self.last_state_change > 4.0:
                self.state = FoxState.SIT_IDLE
                self.star['active'] = False
            else:
                patrol_radius = 40
                if self.facing_right:
                    target = self.star['x'] + patrol_radius
                    if self.fox_x >= target: self.facing_right = False
                    else: self.fox_x += FOX_RUN_SPEED
                else:
                    target = self.star['x'] - patrol_radius
                    if self.fox_x <= target: self.facing_right = True
                    else: self.fox_x -= FOX_RUN_SPEED
                
                # 转圈也产生尘土
                if self.tick % 6 == 0:
                    offset_x = -20 if self.facing_right else 20
                    self.spawn_dust(self.fox_x + offset_x, FOX_Y_BASE + 30)

        # D. 鼠标悬浮
        elif not self.star['active']:
             mx, my = self.mouse_pos
             if my < SCREEN_HEIGHT - 100:
                 self.state = FoxState.LOOKING_UP
                 dx = mx - self.fox_x
                 self.facing_right = (dx > 0)
             else:
                 self.state = FoxState.SIT_IDLE
    
    def draw(self):
        if DEBUG_MODE:
            self.screen.fill((0,0,0))
        else:
            self.screen.fill(COLOR_TRANSPARENT_KEY)
            
        PixelDrawer.draw_fox(self.screen, self.fox_x, FOX_Y_BASE, self.facing_right, self.state, self.tick)
        
        if self.star['active']:
            PixelDrawer.draw_star(self.screen, self.star['x'], self.star['y'], self.tick)
            
        # 粒子渲染 (简单的矩形块)
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] > 0:
                s = p['size']
                pygame.draw.rect(self.screen, p['color'], (int(p['x']), int(p['y']), s, s))
        self.particles = [p for p in self.particles if p['life'] > 0]

        pygame.display.update()
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    def run(self):
        while self.running:
            self.update()
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.clock.tick(60)
        self.listener.stop()
        pygame.quit()

if __name__ == "__main__":
    DesktopPet().run()