#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import random
import math
import os
import sys
import time
import threading
import win32gui
import win32con
from pynput import mouse
import pyttsx3
import win32file
import win32event
import win32con

class GooseAnimation:
    def __init__(self, root, goose_app):
        self.root = root
        self.goose_app = goose_app
        self.running = True
        
        # 动画参数
        self.animation_speed = 100  # 动画更新速度（毫秒）
        self.wing_animation_frame = 0
        self.wing_animation_speed = 5  # 翅膀扇动速度
        
        # 移动参数
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.speed = 3.0  # 移动速度
        self.velocity_x = random.uniform(-self.speed, self.speed)
        self.velocity_y = random.uniform(-self.speed, self.speed)
        self.size = 80  # 鹅的大小
        
        # 随机初始位置
        self.x = random.randint(self.size, self.screen_width - self.size)
        self.y = random.randint(self.size, self.screen_height - self.size)
        
        # 行为模式相关
        self.behavior_modes = ['explore', 'rest', 'play', 'follow_mouse']
        self.current_mode = random.choice(self.behavior_modes)
        self.mode_timer = time.time()
        self.mode_duration = random.randint(15, 30)  # 延长冷却时间：模式持续时间从5-15秒改为15-30秒
        
        # 好感值系统
        self.affection = 0
        self.click_count = 0
        
        # 便签系统
        self.note_interval = 100  # 好感值达到100的倍数时显示便签
        self.notes = [
            "你好呀！",
            "今天天气真好！",
            "我喜欢你摸我的头！",
            "虫子真好吃！",
            "谢谢你的照顾！",
            "我想和你一起玩！"
        ]
        
        # 足迹系统
        self.footprints = []
        self.footprint_timer = time.time()
        self.footprint_interval = 2.0  # 延长足迹生成间隔：从1秒改为2秒
        
        # 创建动画窗口
        self.anim_window = tk.Toplevel(self.root)
        self.anim_window.overrideredirect(True)
        self.anim_window.attributes('-topmost', True)
        self.anim_window.attributes('-transparentcolor', '#ffffff')
        self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
        
        # 创建画布
        self.canvas = tk.Canvas(self.anim_window, width=self.size * 2, height=self.size * 2, bg='white', highlightthickness=0)
        self.canvas.pack()
        
        # 尝试加载鹅图片
        self.goose_image = None
        try:
            # 获取当前脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建鹅图片的完整路径
            goose_image_path = os.path.join(script_dir, "鹅.png")
            self.goose_image = Image.open(goose_image_path)
            self.goose_image = self.goose_image.resize((self.size * 2, self.size * 2), Image.Resampling.LANCZOS)
            self.goose_photo = ImageTk.PhotoImage(self.goose_image)
            print(f"成功加载鹅图片: {goose_image_path}")
        except Exception as e:
            print(f"无法加载鹅图片，使用备用绘制方法: {e}")
            self.goose_photo = None
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        # 开始动画循环
        self.animate()
        
    def on_click(self, event):
        # 处理鼠标点击事件
        self.click_count += 1
        self.affection += 10
        print(f"大白鹅被点击了 {self.click_count} 次，当前好感值: {self.affection}")
        
        # 随机改变方向
        if random.random() < 0.3:
            self.change_direction()
            print("大白鹅改变了方向")
        
        # 特殊行为触发
        if self.affection % 100 == 0:
            print("大白鹅开始跳舞")
            self.dance()
        elif self.affection % 50 == 0:
            action = random.choice(["伸展身体", "整理羽毛"])
            print(f"大白鹅在{action}")
        
        # 显示便签
        if self.affection % self.note_interval == 0 and self.affection > 0:
            self.show_note()
    
    def on_drag(self, event):
        # 处理鼠标拖拽事件
        if not self.is_dragging:
            self.is_dragging = True
            self.drag_offset_x = event.x_root - self.anim_window.winfo_x()
            self.drag_offset_y = event.y_root - self.anim_window.winfo_y()
        else:
            self.x = event.x_root - self.drag_offset_x + self.size
            self.y = event.y_root - self.drag_offset_y + self.size
            self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
            
            # 拖拽时更新位置
            self.root.after(10, lambda: self.on_drag_complete())
    
    def on_drag_complete(self):
        self.is_dragging = False
    
    def change_direction(self):
        # 随机改变移动方向
        angle = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
    
    def dance(self):
        # 跳舞动画
        for _ in range(5):
            self.size = 80 + random.randint(-5, 5)
            self.root.after(100)
            self.size = 80
            self.root.after(100)
    
    def show_note(self):
        # 显示便签
        note_text = random.choice(self.notes)
        print(f"大白鹅带来了便签: {note_text}")
        
        note_window = tk.Toplevel(self.root)
        note_window.overrideredirect(True)
        note_window.attributes('-topmost', True)
        note_window.attributes('-alpha', 0.9)
        
        # 便签位置（鹅的上方）
        x = int(self.x - 100)
        y = int(self.y - self.size - 60)
        note_window.geometry(f"200x50+{x}+{y}")
        
        # 创建便签背景和文字
        note_frame = tk.Frame(note_window, bg='#FFF9C4', bd=2, relief=tk.RAISED)
        note_frame.pack(fill=tk.BOTH, expand=True)
        
        note_label = tk.Label(note_frame, text=note_text, bg='#FFF9C4', fg='black', font=('SimHei', 12))
        note_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 3秒后关闭便签
        self.root.after(3000, note_window.destroy)
    
    def update_behavior_mode(self):
        # 更新行为模式
        current_time = time.time()
        if current_time - self.mode_timer > self.mode_duration:
            self.current_mode = random.choice(self.behavior_modes)
            self.mode_timer = current_time
            self.mode_duration = random.randint(15, 30)  # 延长冷却时间：模式持续时间从5-15秒改为15-30秒
    
    def follow_mouse(self):
        # 跟随鼠标模式
        mouse_x, mouse_y = win32gui.GetCursorPos()
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 如果距离大于阈值，向鼠标移动
        if distance > 50:
            self.velocity_x = (dx / distance) * self.speed * 0.7
            self.velocity_y = (dy / distance) * self.speed * 0.7
    
    def create_footprint(self):
        # 创建足迹
        current_time = time.time()
        if current_time - self.footprint_timer > self.footprint_interval:
            # 计算足迹位置（鹅的后方）
            angle = math.atan2(self.velocity_y, self.velocity_x)
            footprint_x = self.x - self.size * math.cos(angle)
            footprint_y = self.y - self.size * math.sin(angle)
            
            # 添加足迹到列表
            self.footprints.append({
                'x': footprint_x,
                'y': footprint_y,
                'opacity': 1.0,
                'size': 10
            })
            
            self.footprint_timer = current_time
    
    def update_footprints(self):
        # 更新足迹（淡出效果）
        new_footprints = []
        for footprint in self.footprints:
            footprint['opacity'] -= 0.01  # 延长足迹消失时间：从0.02改为0.01
            if footprint['opacity'] > 0:
                new_footprints.append(footprint)
        self.footprints = new_footprints
    
    def draw_footprints(self):
        # 绘制足迹
        for footprint in self.footprints:
            # 使用不透明的灰色，根据透明度调整灰度
            gray_value = int(footprint['opacity'] * 150 + 50)  # 50-200的灰度范围
            color = f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'  # 灰度颜色
            
            # 绘制足迹
            self.canvas.create_oval(
                footprint['x'] - footprint['size'], footprint['y'] - footprint['size'],
                footprint['x'] + footprint['size'], footprint['y'] + footprint['size'],
                fill=color, outline='')
    
    def draw_goose(self):
        # 绘制鹅
        self.canvas.delete('all')
        
        # 绘制足迹
        self.draw_footprints()
        
        # 计算翅膀动画的y轴偏移
        wing_offset = math.sin(self.wing_animation_frame * 0.1) * 5
        
        # 根据移动方向计算旋转角度
        if abs(self.velocity_x) > 0.1 or abs(self.velocity_y) > 0.1:
            angle = math.atan2(self.velocity_y, self.velocity_x) * 180 / math.pi
        else:
            angle = 0
        
        # 使用图片绘制鹅
        if self.goose_photo:
            # 计算图像中心点
            center_x = self.size
            center_y = self.size + wing_offset
            
            # 在画布上显示鹅图片
            self.goose_id = self.canvas.create_image(center_x, center_y, image=self.goose_photo)
        else:
            # 备用绘制方法（不使用图片）
            center_x = self.size
            center_y = self.size + wing_offset
            
            # 绘制鹅的身体
            self.canvas.create_oval(
                center_x - 30, center_y - 20,
                center_x + 30, center_y + 20,
                fill='#888888', outline='')#白色
            
            # 绘制鹅的头部
            self.canvas.create_oval(
                center_x + 20, center_y - 15,
                center_x + 40, center_y + 15,
                fill='#888888', outline='')
            
            # 绘制鹅的嘴
            beak_length = 15
            beak_x = center_x + 40 + beak_length * math.cos(math.radians(angle))
            beak_y = center_y + beak_length * math.sin(math.radians(angle))
            self.canvas.create_line(
                center_x + 40, center_y,
                beak_x, beak_y,
                width=5, fill='#FFCC00')
            
            # 绘制鹅的眼睛
            eye_offset_x = 10
            eye_offset_y = -5
            self.canvas.create_oval(
                center_x + 30 + eye_offset_x, center_y + eye_offset_y - 3,
                center_x + 30 + eye_offset_x + 6, center_y + eye_offset_y + 3,
                fill='white', outline='')
            self.canvas.create_oval(
                center_x + 30 + eye_offset_x + 2, center_y + eye_offset_y - 1,
                center_x + 30 + eye_offset_x + 4, center_y + eye_offset_y + 1,
                fill='black', outline='')
    
    def check_collision(self):
        # 检查窗口边界碰撞
        if self.x - self.size < 0 or self.x + self.size > self.screen_width:
            self.velocity_x = -self.velocity_x
            # 确保鹅不会卡在边界
            if self.x - self.size < 0:
                self.x = self.size
            else:
                self.x = self.screen_width - self.size
        
        if self.y - self.size < 0 or self.y + self.size > self.screen_height:
            self.velocity_y = -self.velocity_y
            # 确保鹅不会卡在边界
            if self.y - self.size < 0:
                self.y = self.size
            else:
                self.y = self.screen_height - self.size
    
    def animate(self):
        # 动画循环
        if not self.running:
            return
        
        # 更新行为模式
        self.update_behavior_mode()
        
        # 根据当前模式更新移动
        if self.current_mode == 'explore':
            # 探索模式：随机移动
            if random.random() < 0.02:
                self.change_direction()
        elif self.current_mode == 'rest':
            # 休息模式：移动缓慢或停止
            self.velocity_x *= 0.9
            self.velocity_y *= 0.9
        elif self.current_mode == 'play':
            # 玩耍模式：快速随机移动
            if random.random() < 0.05:
                self.change_direction()
            self.velocity_x = max(-self.speed*1.5, min(self.speed*1.5, self.velocity_x))
            self.velocity_y = max(-self.speed*1.5, min(self.speed*1.5, self.velocity_y))
        elif self.current_mode == 'follow_mouse':
            # 跟随鼠标模式
            self.follow_mouse()
        
        # 更新位置
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 检查碰撞
        self.check_collision()
        
        # 更新窗口位置
        self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
        
        # 更新翅膀动画
        self.wing_animation_frame += self.wing_animation_speed
        
        # 更新足迹
        self.update_footprints()
        if random.random() < 0.3:  # 不是每次都创建足迹
            self.create_footprint()
        
        # 绘制鹅
        self.draw_goose()
        
        # 继续动画循环
        self.root.after(self.animation_speed, self.animate)
    
    def stop(self):
        # 停止动画
        self.running = False
        self.anim_window.destroy()

class FolderMonitor:
    def __init__(self, folder_path, callback_func):
        self.folder_path = folder_path
        self.callback_func = callback_func
        self.running = True
        
    def start_monitoring(self):
        # 启动文件夹监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_folder, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        # 停止文件夹监控
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_folder(self):
        # 监控文件夹是否被打开
        # 注意：这个方法会定期检查文件夹是否存在，以及是否有进程访问该文件夹
        while self.running:
            try:
                # 检查文件夹是否存在
                if os.path.exists(self.folder_path):
                    try:
                        # 尝试打开文件夹中的一个临时文件，如果成功打开，说明文件夹未被独占
                        # 但如果无法打开，可能是被其他程序（如资源管理器）打开了
                        test_file = os.path.join(self.folder_path, "test_access.tmp")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                    except Exception as e:
                        # 如果无法创建或删除文件，可能是文件夹被打开了
                        print(f"检测到张恩实文件夹可能被打开: {e}")
                        # 调用回调函数关闭程序
                        self.callback_func()
                        break
            except Exception as e:
                print(f"监控文件夹时出错: {e}")
            
            # 每1秒检查一次
            time.sleep(1)

class GooseChaseApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # 隐藏主窗口
        
        # 鹅动画管理
        self.active_geese = []
        
        # 创建系统托盘图标
        self.tray_window = tk.Toplevel(self.root)
        self.tray_window.overrideredirect(True)
        self.tray_window.geometry("40x40+0+0")  # 小窗口，放在左上角
        self.tray_window.attributes('-topmost', True)
        
        # 创建托盘图标
        self.create_tray_icon()
        
        # 创建右键菜单
        self.create_tray_menu()
        
        # 绑定事件
        self.tray_window.bind("<Button-1>", self.summon_goose)
        self.tray_window.bind("<Button-3>", self.show_tray_menu)
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self.cleanup_finished_geese, daemon=True)
        self.cleanup_thread.start()
        
        # 配置要监控的文件夹路径
        # 默认检查用户文档目录下的"张恩实"文件夹
        self.target_folder = os.path.join(os.path.expanduser('~'), "Documents", "张恩实")
        
        # 启动文件夹监控
        self.folder_monitor = FolderMonitor(self.target_folder, self.on_folder_opened)
        self.folder_monitor.start_monitoring()
    
    def on_folder_opened(self):
        # 当检测到张恩实文件夹被打开时的处理函数
        print("检测到张恩实文件夹被打开，正在关闭程序...")
        self.quit_app()
    
    def create_tray_icon(self):
        # 创建托盘图标
        icon_size = 40
        icon = Image.new('RGBA', (icon_size, icon_size), color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(icon)
        
        # 尝试加载鹅图片作为图标
        try:
            # 获取当前脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建鹅图片的完整路径
            goose_image_path = os.path.join(script_dir, "鹅.png")
            goose_icon = Image.open(goose_image_path)
            goose_icon = goose_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            icon.paste(goose_icon, (0, 0), goose_icon)
            print(f"成功加载鹅图标图片: {goose_image_path}")
        except Exception as e:
            print(f"无法加载鹅图标图片，使用备用绘制方法: {e}")
            # 备用绘制：简单的鹅形图标
            draw.ellipse((5, 5, 35, 35), fill='#888888')
            draw.ellipse((25, 10, 35, 30), fill='#888888')
            draw.line((35, 20, 45, 20), width=3, fill='#FFCC00')
        
        # 转换为Tkinter可用的图像
        self.tray_photo = ImageTk.PhotoImage(icon)
        
        # 创建标签显示图标
        self.tray_label = tk.Label(self.tray_window, image=self.tray_photo, bd=0)
        self.tray_label.pack(fill=tk.BOTH, expand=True)
    
    def create_tray_menu(self):
        # 创建右键菜单
        self.tray_menu = tk.Menu(self.root, tearoff=0)
        self.tray_menu.add_command(label="召唤大白鹅", command=self.summon_goose)
        self.tray_menu.add_command(label="清理所有鹅", command=self.cleanup_all_geese)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="退出", command=self.quit_app)
    
    def summon_goose(self, event=None):
        # 召唤一只大白鹅
        goose = GooseAnimation(self.root, self)
        self.active_geese.append(goose)
        print("成功召唤一只大白鹅！")
    
    def cleanup_finished_geese(self):
        # 清理已停止的鹅动画
        while True:
            time.sleep(5)
            # 注意：这里简化处理，实际项目中可能需要更好的方式来检测已停止的动画
            pass
    
    def cleanup_all_geese(self):
        # 清理所有鹅动画
        for goose in self.active_geese:
            goose.stop()
        self.active_geese.clear()
        print("已清理所有大白鹅")
    
    def show_tray_menu(self, event):
        # 显示右键菜单
        try:
            self.tray_menu.post(event.x_root, event.y_root)
        except:
            # 如果菜单显示失败，忽略错误
            pass
    
    def quit_app(self):
        # 退出应用
        print("正在退出应用...")
        
        # 停止文件夹监控
        if hasattr(self, 'folder_monitor'):
            self.folder_monitor.stop_monitoring()
        
        # 清理所有鹅
        self.cleanup_all_geese()
        
        # 销毁窗口并退出
        self.root.after(100, lambda: self._delayed_quit())
    
    def _delayed_quit(self):
        # 延迟退出，确保所有资源都被正确释放
        self.root.destroy()
        sys.exit(0)

# 查找张恩实文件夹的函数
def find_target_folder(folder_name="张恩实"):
    # 在常见位置搜索目标文件夹
    common_paths = [
        os.path.join(os.path.expanduser('~'), "Documents"),
        os.path.join(os.path.expanduser('~'), "Desktop"),
        os.path.join(os.path.expanduser('~')),
        
    ]
    
    for path in common_paths:
        try:
            for root, dirs, files in os.walk(path):
                if folder_name in dirs:
                    return os.path.join(root, folder_name)
        except Exception as e:
            print(f"搜索文件夹时出错: {e}")
    
    return None

def create_auto_run_file():
    # 创建自动运行批处理文件
    try:
        app_path = os.path.abspath(__file__)
        bat_path = os.path.join(os.path.dirname(app_path), "启动大白鹅捉虫.bat")
        
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f"@echo off\n")
            f.write(f"chcp 65001 >nul\n")  # 设置UTF-8编码
            f.write(f"python \"{app_path}\"\n")
            f.write(f"exit\n")
        
        print(f"已创建自动运行文件: {bat_path}")
    except Exception as e:
        print(f"创建自动运行文件失败: {e}")

if __name__ == "__main__":
    # 创建自动运行文件
    create_auto_run_file()
    
    # 创建主窗口
    root = tk.Tk()
    
    # 设置中文字体支持
    root.option_add("*Font", "SimHei 10")
    
    # 初始化应用
    app = GooseChaseApp(root)
    
    # 启动主循环
    root.mainloop()