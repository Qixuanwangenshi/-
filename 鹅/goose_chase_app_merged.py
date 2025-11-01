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
import win32file
import win32event
import win32con
import subprocess
import requests
import cv2
import json
import re
# 添加pygame库用于音频播放
try:
    import pygame
    pygame.mixer.init()
except ImportError:
    print("警告: pygame库未安装，音乐播放功能将不可用")
    pygame = None

class GooseAnimation:
    def __init__(self, root, goose_app):
        self.root = root
        self.goose_app = goose_app
        self.running = True
        
        # 动画参数
        self.animation_speed = 100  # 动画更新速度（毫秒）
        self.wing_animation_frame = 0
        self.wing_animation_speed = 5  # 翅膀扇动速度
        
        # 动作序列帧参数
        self.action_state = "idle"  # idle, walking, dancing, stretching
        self.action_frame = 0
        self.action_duration = 0
        self.action_frames = {
            "dancing": 12,    # 跳舞帧数
            "stretching": 10  # 伸展帧数
        }
        self.is_dancing = False
        self.is_stretching = False
        
        # 音乐相关参数
        self.currently_playing = False
        self.current_song = None
        self.music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "周杰伦")
        self.show_lyrics = True  # 字幕开关，默认为开启
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
        self.affection = 50  # 初始好感度设置为50
        self.click_count = 0
        
        # 便签系统
        self.note_interval = 50  # 好感值达到50的倍数时显示便签
        self.notes = [
            "你好呀！",
            "今天天气真好！",
            "我喜欢你摸我的头！",
            "虫子真好吃！",
            "谢谢你的照顾！",
            "我想和你一起玩！",
            "做事情",
            "不要拖"
        ]
        # 对话框系统
        self.dialog_text = ""
        self.dialog_showing = False
        self.dialog_timer = 0
        self.dialog_duration = 3.0  # 对话框显示时长（秒）
        self.dialog_id = None  # 对话框在画布中的ID
        self.dialog_text_id = None  # 对话框文本ID
        self.conversation_history = []
        self.anim_window = tk.Toplevel(self.root)
        self.anim_window.overrideredirect(True)
        self.anim_window.attributes('-topmost', True)
        self.anim_window.attributes('-transparentcolor', '#ffffff')
        self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
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
        self.canvas.bind("<Button-3>", self.show_goose_menu)  # 右键菜单
        
        # 创建右键菜单
        self.create_goose_menu()
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
        if self.affection % self.note_interval == 0 and self.affection > 0:
            self.show_note()
        if random.random() < 0.3:
            self.make_goose_speak()
        
        # 好感度达到一定值时有几率触发特殊动作
        if random.random() < 0.5 and self.affection > 5:
            action_choice = random.choice(["dance", "stretch", "hum"])
            if action_choice == "dance" and self.affection > 20:
                self.start_dancing()
            elif action_choice == "stretch" and self.affection > 10:
                self.start_stretching()
            elif action_choice == "hum" and self.affection > 15:
                self.start_humming()
    
    def on_drag(self, event):
        if not self.is_dragging:
            self.is_dragging = True
            self.drag_offset_x = event.x_root - self.anim_window.winfo_x()
            self.drag_offset_y = event.y_root - self.anim_window.winfo_y()
        else:
            self.x = event.x_root - self.drag_offset_x + self.size
            self.y = event.y_root - self.drag_offset_y + self.size
            self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
            self.root.after(10, lambda: self.on_drag_complete())
    
    def on_drag_complete(self):
        self.is_dragging = False
    
    # 拖拽相关方法将在GooseChaseApp类中定义
    
    def create_goose_menu(self):
        # 创建大白鹅右键菜单
        self.goose_menu = tk.Menu(self.root, tearoff=0)
        self.goose_menu.add_command(label="与大白鹅聊天", command=self.open_chat_window)
        self.goose_menu.add_command(label="查看对话记录", command=self.show_conversation_history)
        self.goose_menu.add_command(label="让大白鹅说话", command=self.make_goose_speak)
        self.goose_menu.add_separator()
        self.goose_menu.add_command(label="显示在最底层", command=self.send_to_bottom)
        self.goose_menu.add_command(label="显示在最顶层", command=self.send_to_top)
    
    def show_goose_menu(self, event):
        # 显示右键菜单
        try:
            self.goose_menu.post(event.x_root, event.y_root)
        except:
            # 如果菜单显示失败，忽略错误
            pass
    
    def open_chat_window(self):
        # 打开与该大白鹅的聊天窗口
        x, y = win32gui.GetCursorPos()
        chat_window = ChatWindow(self.root, self.goose_app.ai_manager, (x, y))
        # 保存对当前鹅实例的引用，以便在聊天时添加消息到对话历史
        chat_window.goose_instance = self
        self.goose_app.chat_windows.append(chat_window)
        print("打开了大白鹅聊天窗口")
    
    def send_to_bottom(self):
        """将大白鹅窗口发送到最底层"""
        try:
            # 移除置顶属性
            self.anim_window.attributes('-topmost', False)
            # 降低窗口层级到最底层
            self.anim_window.lower()
            print("大白鹅已显示在最底层")
        except Exception as e:
            print(f"设置窗口层级时出错: {e}")
            
    def send_to_top(self):
        """将大白鹅窗口发送到最顶层"""
        try:
            # 设置置顶属性
            self.anim_window.attributes('-topmost', True)
            # 提升窗口层级到最顶层
            self.anim_window.lift()
            print("大白鹅已显示在最顶层")
        except Exception as e:
            print(f"设置窗口层级时出错: {e}")
            
    def _create_note_window(self, content, bg_color):
        """创建便签窗口的通用方法"""
        # 创建便签窗口
        note_window = tk.Toplevel(self.root)
        note_window.overrideredirect(True)
        note_window.attributes('-topmost', True)
        note_window.attributes('-alpha', 0.9)
        
        # 便签位置（鹅的上方）
        x = int(self.x - 100)
        y = int(self.y - self.size - 60)
        note_window.geometry(f"200x50+{x}+{y}")
        
        # 创建便签背景和文字
        note_frame = tk.Frame(note_window, bg=bg_color, bd=2, relief=tk.RAISED)
        note_frame.pack(fill=tk.BOTH, expand=True)
        
        note_label = tk.Label(note_frame, text=content, bg=bg_color, fg='black', font=('SimHei', 12))
        note_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 3秒后关闭便签
        self.root.after(3000, note_window.destroy)
        
        # 保存便签窗口引用，以便后续管理
        if not hasattr(self, 'note_windows'):
            self.note_windows = []
        self.note_windows.append(note_window)
        
        # 限制便签数量，避免过多
        if len(self.note_windows) > 3:
            old_note = self.note_windows.pop(0)
            try:
                old_note.destroy()
            except:
                pass
            
    def show_conversation_history(self):
        # 显示对话历史窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("大白鹅对话记录")
        history_window.geometry("400x400")
        history_window.attributes('-topmost', True)
        history_text = tk.Text(history_window, wrap=tk.WORD, font=('SimHei', 10))
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        history_text.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(history_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=history_text.yview)
        
        # 填充对话历史
        history_text.config(state=tk.NORMAL)
        if not self.conversation_history:
            history_text.insert(tk.END, "暂无对话记录\n", "empty_history")
        else:
            for message in self.conversation_history:
                sender = message['sender']
                content = message['content']
                time_str = message['time']
                
                if sender == "你":
                    history_text.insert(tk.END, f"[{time_str}] {sender}: {content}\n", "user_message")
                else:
                    history_text.insert(tk.END, f"[{time_str}] {sender}: {content}\n", "bot_message")
        
        # 配置标签样式
        history_text.tag_configure("empty_history", font=("SimHei", 10, "italic"), foreground="#888888", justify="center")
        history_text.tag_configure("user_message", font=("SimHei", 10), foreground="#2196F3", justify="right")
        history_text.tag_configure("bot_message", font=("SimHei", 10), foreground="#4CAF50", justify="left")
        
        # 滚动到底部
        history_text.see(tk.END)
        history_text.config(state=tk.DISABLED)
    
    def make_goose_speak(self):
        # 让大白鹅随机说一句话（使用便签显示）
        random_phrases = [
            "你好呀！",
            "今天天气真好！",
            "我喜欢你！",
            "要一起玩吗？",
            "虫子在哪里？",
            "我想游泳了！"
        ]
        phrase = random.choice(random_phrases)
        self._create_note_window(phrase, '#FFF9C4')  # 使用便签显示
        
        # 添加到对话历史
        current_time = time.strftime("%H:%M:%S")
        self.conversation_history.append({
            'sender': '大白鹅',
            'content': phrase,
            'time': current_time
        })
    
    def show_dialog(self, text):
        # 显示对话框
        self.dialog_text = text
        self.dialog_showing = True
        self.dialog_timer = time.time()
        
        # 设置固定的对话框宽度，让文本自动换行
        max_dialog_width = 250  # 最大对话框宽度
        dialog_width = min(250, len(text) * 8 + 20)  # 根据文本长度动态调整，但不超过最大值
        dialog_width = max(dialog_width, 120)  # 确保最小宽度
        
        # 估算行数，动态调整对话框高度
        # 平均每个字符宽度约为6像素（SimHei 10号字体）
        chars_per_line = (dialog_width - 20) // 6  # 每行字符数，减去边距
        lines = (len(text) + chars_per_line - 1) // chars_per_line  # 计算行数
        dialog_height = max(40, lines * 20 + 10)  # 基础高度40，每行增加20像素
        
        # 确保对话框不会超出画布范围
        dialog_x = self.size - dialog_width // 2
        dialog_y = - (dialog_height + 20)  # 确保对话框在鹅的上方，且有足够空间
        
        # 如果对话框ID存在，先删除
        if self.dialog_id:
            self.canvas.delete(self.dialog_id)
        if self.dialog_text_id:
            self.canvas.delete(self.dialog_text_id)
        radius = 10
        self.dialog_id = self.canvas.create_polygon(
            dialog_x + radius, dialog_y,
            dialog_x + dialog_width - radius, dialog_y,
            dialog_x + dialog_width, dialog_y + radius,
            dialog_x + dialog_width, dialog_y + dialog_height - 15,
            dialog_x + dialog_width // 2 + 10, dialog_y + dialog_height - 15,
            dialog_x + dialog_width // 2, dialog_y + dialog_height,
            dialog_x + dialog_width // 2 - 10, dialog_y + dialog_height - 15,
            dialog_x, dialog_y + dialog_height - 15,
            dialog_x, dialog_y + radius,
            fill="#F0F0F0", outline="#CCCCCC", width=2
        )
        
        # 绘制文本，使用justify参数确保文本对齐良好
        self.dialog_text_id = self.canvas.create_text(
            dialog_x + dialog_width // 2,
            dialog_y + dialog_height // 2 - 5,
            text=text,
            font=('SimHei', 10),
            fill="#333333",
            width=dialog_width - 20,
            justify='center'
        )
    
    def update_dialog(self):
        # 更新对话框状态
        if self.dialog_showing:
            current_time = time.time()
            if current_time - self.dialog_timer > self.dialog_duration:
                # 隐藏对话框
                self.dialog_showing = False
                if self.dialog_id:
                    self.canvas.delete(self.dialog_id)
                    self.dialog_id = None
                if self.dialog_text_id:
                    self.canvas.delete(self.dialog_text_id)
                    self.dialog_text_id = None
    
    def add_conversation_message(self, sender, content):
        # 添加对话消息到历史记录
        current_time = time.strftime("%H:%M:%S")
        self.conversation_history.append({
            'sender': sender,
            'content': content,
            'time': current_time
        })
        
        # 如果是大白鹅的消息，使用便签显示
        if sender == '大白鹅':
            self._create_note_window(content, '#FFE4B5')  # 特殊便签颜色用于AI回复
    
    def change_direction(self):
        # 随机改变移动方向
        angle = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
    
    def dance(self):
        # 开始跳舞动作
        self.start_dancing()
    
    def start_dancing(self):
        """开始跳舞动作"""
        self.action_state = "dancing"
        self.action_frame = 0
        self.action_duration = 30  # 跳舞持续30帧
        self.is_dancing = True
        print("大白鹅开始跳舞了！")
        
    def start_stretching(self):
        """开始伸展动作"""
        self.action_state = "stretching"
        self.action_frame = 0
        self.action_duration = 20  # 伸展持续20帧
        self.is_stretching = True
        print("大白鹅开始伸展身体了！")
        
    # 整理羽毛功能已移除
    
    def update_action_state(self, force_change=False):
        """更新动作状态"""
        # 如果正在进行特殊动作，不进行状态更新
        if self.is_dancing or self.is_stretching:
            return
        
        # 基于好感度随机触发特殊动作（包括哼唱周杰伦歌曲）
        if force_change or (random.random() < 0.005 and self.affection > 0):  # 增加触发概率
            print(f"\n触发特殊动作检测 - 好感度: {self.affection}")
            action_prob = random.random()
            if action_prob < 0.33 and self.affection > 20:
                print("触发跳舞动作")
                self.start_dancing()
            elif action_prob < 0.66 and self.affection > 10:
                print("触发伸展动作")
                self.start_stretching()
            elif self.affection > 15:  # 好感度大于15时可能哼唱歌曲
                print("触发哼唱周杰伦歌曲")
                self.start_humming()
    
    def update_action_frame(self):
        """更新动作帧"""
        if self.action_state != "idle":
            self.action_frame += 1
            
            # 检查动作是否结束
            if self.action_duration > 0 and self.action_frame >= self.action_duration:
                self.end_special_action()
    
    def end_special_action(self):
        """结束特殊动作"""
        self.is_dancing = False
        self.is_stretching = False
        self.action_state = "idle"
        self.action_frame = 0
        self.action_duration = 0
    
    def get_music_files(self):
        """获取周杰伦文件夹中的所有音乐文件"""
        music_files = []
        if not os.path.exists(self.music_folder):
            print(f"周杰伦文件夹不存在: {self.music_folder}")
            return music_files
        
        # 支持的音频格式
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        
        try:
            for file in os.listdir(self.music_folder):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    music_files.append(os.path.join(self.music_folder, file))
        except Exception as e:
            print(f"读取音乐文件夹时出错: {str(e)}")
        
        return music_files
    
    def play_random_song(self):
        """随机播放一首周杰伦的歌曲"""
        print("===== 开始音乐播放流程 =====")
        if pygame is None:
            print("pygame未初始化，无法播放音乐")
            return False
        
        # 检查pygame.mixer是否正常工作
        if not pygame.mixer.get_init():
            print("pygame.mixer未初始化，尝试重新初始化...")
            try:
                pygame.mixer.quit()
                pygame.mixer.init()
                print("pygame.mixer重新初始化成功")
            except Exception as e:
                print(f"pygame.mixer重新初始化失败: {str(e)}")
                return False
        
        # 检查当前是否正在播放音乐，如果正在播放则不中断
        if pygame.mixer.music.get_busy() or self.currently_playing:
            print("当前正在播放音乐，等待播放完毕后再切换")
            return False
        
        # 获取音乐文件列表
        music_files = self.get_music_files()
        print(f"找到音乐文件数量: {len(music_files)}")
        if not music_files:
            print("周杰伦文件夹中没有找到音乐文件")
            return False
        
        # 随机选择一首歌曲
        song_path = random.choice(music_files)
        song_name = os.path.basename(song_path)
        print(f"选择播放: {song_name}")
        
        try:
            print("正在加载音频文件...")
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(0.5)  # 设置音量为50%
            print("开始播放音乐...")
            pygame.mixer.music.play()
            self.currently_playing = True
            self.current_song = song_path
            print(f"音乐播放成功: {song_name}")
            
            # 使用便签显示正在播放的歌曲
            try:
                print("创建歌曲信息便签...")
                self._create_note_window(f"正在哼唱: {song_name}", '#E8F5E9')
                print("便签创建成功")
            except Exception as note_error:
                print(f"创建便签时出错: {str(note_error)}")
            
            # 获取并显示歌词（如果字幕开关开启）
            if self.show_lyrics:
                try:
                    lyrics = self.get_lyrics_for_song(song_name)
                    # 在主线程中显示歌词
                    self.root.after(500, self.show_lyrics, lyrics)
                except Exception as lyrics_error:
                    print(f"显示歌词时出错: {str(lyrics_error)}")
            else:
                print("字幕显示已关闭")
            
            return True
        except Exception as e:
            print(f"播放音乐时出错: {str(e)}")
            self.currently_playing = False
            self.current_song = None
            return False
        finally:
            print("===== 音乐播放流程结束 =====")
    
    def stop_music(self):
        """停止当前播放的音乐"""
        if pygame is not None and self.currently_playing:
            try:
                pygame.mixer.music.stop()
                self.currently_playing = False
                self.current_song = None
                print("音乐已停止")
                # 关闭字幕窗口
                if hasattr(self, 'lyrics_window') and self.lyrics_window:
                    try:
                        self.lyrics_window.destroy()
                        print("字幕窗口已关闭")
                    except:
                        pass
            except Exception as e:
                print(f"停止音乐时出错: {str(e)}")
    
    def toggle_lyrics(self):
        """切换字幕显示状态"""
        self.show_lyrics = not self.show_lyrics
        status = "开启" if self.show_lyrics else "关闭"
        print(f"字幕显示已{status}")
        
        # 如果关闭字幕且字幕窗口存在，立即关闭它
        if not self.show_lyrics and hasattr(self, 'lyrics_window') and self.lyrics_window:
            try:
                self.lyrics_window.destroy()
                print("字幕窗口已关闭")
            except:
                pass
        
        return self.show_lyrics  # 返回新的状态
    
    def get_lyrics_for_song(self, song_name):
        """获取歌曲的歌词
        
        Args:
            song_name: 歌曲名称
            
        Returns:
            list: 歌词列表
        """
        # 尝试从文件加载歌词
        lyrics = self._load_lyrics_from_file(song_name)
        if lyrics:
            return lyrics
        
        # 如果无法从文件加载，使用默认歌词映射
        lyrics_map = {
            "1-我怀念的，吕嘉铭.mp3": [
                (0, "我怀念的是无话不说"),
                (2, "我怀念的是一起做梦"),
                (4, "我怀念的是争吵以后"),
                (6, "还是想要爱你的冲动"),
                (8, "我记得那年生日"),
                (10, "也记得那一首歌"),
                (12, "记得那片星空"),
                (14, "最紧的右手"),
                (16, "最暖的胸口")
            ]
        }
        
        # 返回对应歌曲的歌词，如果没有则返回默认歌词
        return lyrics_map.get(song_name, [(0, "大白鹅正在欢快地哼唱..."), (2, "啦啦啦..."), (4, "多么美好的时光~"), (6, "继续哼唱中...")])
    
    def _load_lyrics_from_file(self, song_name):
        """从文件加载歌词
        
        Args:
            song_name: 歌曲名称
            
        Returns:
            list: 歌词列表，如果加载失败返回None
        """
        try:
            # 构建歌词文件路径（将.mp3替换为.txt）
            lyrics_filename = os.path.splitext(song_name)[0] + ".txt"
            lyrics_path = os.path.join("周杰伦", lyrics_filename)
            
            # 检查歌词文件是否存在
            if not os.path.exists(lyrics_path):
                print(f"歌词文件不存在: {lyrics_path}")
                return None
            
            print(f"开始加载歌词文件: {lyrics_path}")
            lyrics = []
            
            # 读取歌词文件
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue  # 跳过空行和注释行
                    
                    # 解析歌词行，格式支持：
                    # 1. 时间:歌词 (例如: "12.5:我怀念的是无话不说")
                    # 2. 时间,歌词 (例如: "12.5,我怀念的是无话不说")
                    try:
                        # 尝试多种分隔符
                        if ':' in line:
                            time_str, lyric_text = line.split(':', 1)
                        elif ',' in line:
                            time_str, lyric_text = line.split(',', 1)
                        else:
                            print(f"警告: 第{line_num+1}行格式不正确: {line}")
                            continue
                        
                        # 转换时间为浮点数
                        time_point = float(time_str.strip())
                        lyric_text = lyric_text.strip()
                        
                        if lyric_text:
                            lyrics.append((time_point, lyric_text))
                            print(f"加载歌词: {time_point}秒 - {lyric_text}")
                    except ValueError as e:
                        print(f"警告: 解析第{line_num+1}行时出错: {str(e)}, 行内容: {line}")
            
            # 按时间排序歌词
            lyrics.sort(key=lambda x: x[0])
            
            if lyrics:
                print(f"成功加载{len(lyrics)}句歌词")
                return lyrics
            else:
                print("歌词文件中没有找到有效的歌词")
                return None
                
        except Exception as e:
            print(f"加载歌词文件时出错: {str(e)}")
            return None
    
    def show_lyrics(self, lyrics):
        """显示歌词字幕
        
        Args:
            lyrics: 歌词列表，格式为 [(时间点(秒), 歌词), ...]
        """
        print("开始显示字幕...")
        
        # 记录当前显示的歌词窗口
        if hasattr(self, 'lyrics_window') and self.lyrics_window:
            try:
                self.lyrics_window.destroy()
                print("已关闭之前的字幕窗口")
            except:
                pass
        
        # 创建一个新的字幕窗口
        self.lyrics_window = tk.Toplevel(self.root)
        self.lyrics_window.overrideredirect(True)
        self.lyrics_window.attributes('-topmost', True)
        self.lyrics_window.attributes('-alpha', 0.95)  # 更透明一些
        
        # 字幕位置（鹅的下方）
        x = int(self.x - 120)
        y = int(self.y + self.size + 10)
        self.lyrics_window.geometry(f"240x60+{x}+{y}")
        
        # 创建字幕背景和文字
        lyrics_frame = tk.Frame(self.lyrics_window, bg='#4A148C', bd=2, relief=tk.RAISED)
        lyrics_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用较大且美观的字体
        self.lyrics_label = tk.Label(lyrics_frame, text="", bg='#4A148C', fg='white', 
                                   font=('SimHei', 14, 'bold'), wraplength=220, justify='center')
        self.lyrics_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 开始显示歌词
        def update_lyrics(index=0):
            # 检查音乐是否还在播放
            if not (pygame and pygame.mixer and pygame.mixer.music.get_busy() and self.currently_playing):
                try:
                    self.lyrics_window.destroy()
                    print("音乐停止，字幕窗口已关闭")
                except:
                    pass
                return
            
            if index < len(lyrics):
                time_delay, lyric_text = lyrics[index]
                # 设置当前歌词
                self.lyrics_label.config(text=lyric_text)
                print(f"显示歌词: {lyric_text}")
                
                # 计算下一行歌词的延迟时间
                next_delay = time_delay * 1000  # 转换为毫秒
                if index > 0:
                    next_delay = (lyrics[index][0] - lyrics[index-1][0]) * 1000
                elif index == 0:
                    next_delay = 1000  # 第一行立即显示
                
                # 安排下一次更新
                self.root.after(int(next_delay), update_lyrics, index + 1)
            else:
                # 歌词显示完毕，重新开始
                self.root.after(1000, update_lyrics, 0)
        
        # 启动歌词更新
        update_lyrics()
    
    def start_humming(self):
        """大白鹅开始哼唱周杰伦的歌曲"""
        print("大白鹅准备开始哼唱周杰伦的歌曲...")
        # 确保不会同时启动多个音乐线程
        if not hasattr(self, 'music_thread') or not self.music_thread.is_alive():
            self.music_thread = threading.Thread(target=self.play_random_song, daemon=True)
            self.music_thread.start()
            print("哼唱线程已启动")
        else:
            print("已有音乐线程在运行，跳过启动")
    
    def show_note(self):
        # 显示便签
        note_text = random.choice(self.notes)
        print(f"大白鹅带来了便签: {note_text}")
        
        note_window = tk.Toplevel(self.root)
        note_window.overrideredirect(True)
        note_window.attributes('-topmost', True)
        note_window.attributes('-alpha', 0.9)
        
        # 便签位置（鹅的上方）
        x = int(self.x - 120)
        y = int(self.y - self.size - 80)
        
        # 创建便签背景和文字
        note_frame = tk.Frame(note_window, bg='#FFF9C4', bd=2, relief=tk.RAISED)
        note_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加文字自动换行功能，设置最大宽度
        note_label = tk.Label(note_frame, text=note_text, bg='#FFF9C4', fg='black', 
                            font=('SimHei', 12), wraplength=220, justify='left')
        note_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 强制窗口布局更新，以便正确计算大小
        note_window.update_idletasks()
        
        # 获取标签的实际大小并调整窗口大小
        # 确保最小高度为60，宽度为240，根据内容自动扩展
        width = 240  # 固定宽度
        height = max(60, note_label.winfo_reqheight() + 20)  # 最小高度60，加上边距
        
        note_window.geometry(f"{width}x{height}+{x}+{y}")
        
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
    

    
    def draw_goose(self):
        # 绘制鹅
        self.canvas.delete('all')
        
        # 根据动作状态更新动作帧
        self.update_action_frame()
        
        # 计算基础翅膀动画的y轴偏移
        base_wing_offset = math.sin(self.wing_animation_frame * 0.1) * 5
        
        # 根据动作状态调整翅膀偏移
        wing_offset = base_wing_offset
        
        # 根据动作状态添加额外的动画效果
        if self.action_state == "dancing":
            # 跳舞动画效果
            dance_offset = math.sin(self.action_frame * 0.3) * 8
            size_variation = math.sin(self.action_frame * 0.2) * 5
            current_size = self.size + size_variation
        elif self.action_state == "stretching":
            # 伸展动画效果
            stretch_factor = min(1.0, self.action_frame / self.action_frames["stretching"])
            wing_offset = base_wing_offset + stretch_factor * 10
        elif self.action_state == "preening":
            # 整理羽毛动画效果
            preen_offset = math.cos(self.action_frame * 0.4) * 5
            wing_offset = base_wing_offset + preen_offset
        else:
            # 普通状态
            current_size = self.size
        
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
            
            # 根据动作状态调整颜色
            body_color = '#FFFFFF'  # 默认白色
            if self.action_state == "dancing":
                # 跳舞时颜色稍微变化
                if int(self.action_frame) % 2 == 0:
                    body_color = '#FFFFF0'  # 更亮的白色
            
            # 绘制鹅的身体
            self.canvas.create_oval(
                center_x - 30, center_y - 20,
                center_x + 30, center_y + 20,
                fill=body_color, outline='')
            
            # 绘制鹅的头部
            self.canvas.create_oval(
                center_x + 20, center_y - 15,
                center_x + 40, center_y + 15,
                fill=body_color, outline='')
            
            # 绘制鹅的嘴
            beak_length = 15
            if self.action_state == "preening":
                # 整理羽毛时嘴的位置变化
                beak_length = 10 + math.sin(self.action_frame * 0.2) * 5
            beak_x = center_x + 40 + beak_length * math.cos(math.radians(angle))
            beak_y = center_y + beak_length * math.sin(math.radians(angle))
            self.canvas.create_line(
                center_x + 40, center_y,
                beak_x, beak_y,
                width=5, fill='#FFCC00')
            
            # 绘制鹅的眼睛
            eye_offset_x = 10
            eye_offset_y = -5
            # 根据动作状态调整眼睛表情
            if self.action_state == "dancing":
                eye_offset_y -= 2  # 跳舞时眼睛看起来更开心
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
        # 检测是否到达桌面边缘并有一定概率触发拉视频行为
        edge_triggered = False
        if self.x - self.size < 50:  # 左侧边缘
            if random.random() < 0.01:  # 1%概率触发
                edge_triggered = True
                self.pull_video_from_edge("left")
            self.velocity_x = -self.velocity_x
            self.x = self.size
        elif self.x + self.size > self.screen_width - 50:  # 右侧边缘
            if random.random() < 0.01:  # 1%概率触发
                edge_triggered = True
                self.pull_video_from_edge("right")
            self.velocity_x = -self.velocity_x
            self.x = self.screen_width - self.size
        
        if self.y - self.size < 50:  # 上边缘
            if random.random() < 0.01 and not edge_triggered:  # 1%概率触发
                self.pull_video_from_edge("top")
            self.velocity_y = -self.velocity_y
            self.y = self.size
        elif self.y + self.size > self.screen_height - 50:  # 下边缘
            if random.random() < 0.01 and not edge_triggered:  # 1%概率触发
                self.pull_video_from_edge("bottom")
            self.velocity_y = -self.velocity_y
            self.y = self.screen_height - self.size
    
    def pull_video_from_edge(self, edge):
        """从指定边缘拉出视频"""
        # 检查是否在冷却时间内
        current_time = time.time()
        if hasattr(self, 'last_video_pull_time') and (current_time - self.last_video_pull_time) < 30:  # 30秒冷却时间
            print("大白鹅刚刚拉过视频，需要休息一下...")
            return
            
        print(f"大白鹅从{edge}边缘拉出了视频！")
        # 记录上次拉视频的时间
        self.last_video_pull_time = current_time
        # 在新线程中播放视频，避免阻塞主UI
        threading.Thread(target=self._play_video_from_edge, args=(edge,), daemon=True).start()
    
    def _play_video_from_edge(self, edge):
        """播放视频的实际实现 - 修改为大白鹅隐藏到边缘再出现，内部播放视频"""
        try:
            # 支持的视频格式
            video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
            video_files = []
            
            # 使用相对路径查找Video文件夹
            project_video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Video')
            print(f"使用相对路径查找项目Video文件夹: {project_video_path}")
            
            if os.path.exists(project_video_path):
                print(f"项目Video文件夹存在，开始搜索视频文件")
                for root, dirs, files in os.walk(project_video_path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in video_extensions:
                            video_path = os.path.join(root, file)
                            video_files.append(video_path)
                            print(f"找到视频文件: {video_path}")
            else:
                print(f"项目Video文件夹不存在: {project_video_path}")
            
            # 如果找不到视频，尝试用户视频文件夹作为最后备选
            if not video_files:
                print("前两个路径都未找到视频文件，尝试用户视频文件夹")
                user_videos_path = os.path.join(os.path.expanduser('~'), 'Videos')
                if os.path.exists(user_videos_path):
                    print(f"尝试在用户视频文件夹中搜索: {user_videos_path}")
                    for root, dirs, files in os.walk(user_videos_path):
                        for file in files:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in video_extensions:
                                video_path = os.path.join(root, file)
                                video_files.append(video_path)
                                print(f"找到视频文件: {video_path}")
            
            # 选择视频文件
            selected_video = None
            if video_files:
                selected_video = random.choice(video_files)
                print(f"选择播放视频: {selected_video}")
            else:
                print("未找到视频文件")
                return
            
            # 大白鹅隐藏到边缘的动画效果
            print(f"大白鹅开始隐藏到{edge}边缘...")
            
            # 记录当前位置
            original_x, original_y = self.x, self.y
            
            # 根据边缘确定隐藏位置
            hide_steps = 50  # 隐藏动画的步数，增加以延长时间
            for i in range(hide_steps):
                # 计算当前透明度
                alpha = 1.0 - (i / hide_steps)
                
                # 移动到边缘
                if edge == "left":
                    self.x = original_x - (original_x - self.size) * (i / hide_steps)
                elif edge == "right":
                    self.x = original_x + (self.screen_width - original_x - self.size) * (i / hide_steps)
                elif edge == "top":
                    self.y = original_y - (original_y - self.size) * (i / hide_steps)
                elif edge == "bottom":
                    self.y = original_y + (self.screen_height - original_y - self.size) * (i / hide_steps)
                
                # 更新窗口位置和透明度
                self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
                try:
                    self.anim_window.attributes('-alpha', alpha)
                except:
                    pass
                
                # 暂停一小段时间，增加动画持续时间
                time.sleep(0.05)  # 每步暂停50ms，总隐藏时间为hide_steps * 0.05秒
            
            # 完全隐藏
            try:
                self.anim_window.attributes('-alpha', 0.0)
            except:
                pass
            
            # 模拟拉视频的时间 - 延长时间
            print("大白鹅正在努力拉视频...")
            time.sleep(10.0)  # 拉视频的时间，设置为5秒
            
            # 在主UI线程中显示视频窗口
            if self.root:
                self.root.after(0, lambda: self.goose_app._show_folder_video_window_with_video(selected_video))
            
            # 大白鹅从边缘出现的动画效果
            print(f"大白鹅从{edge}边缘出现...")
            for i in range(hide_steps):
                # 计算当前透明度
                alpha = i / hide_steps
                
                # 从边缘移回原始位置
                if edge == "left":
                    self.x = self.size + (original_x - self.size) * (i / hide_steps)
                elif edge == "right":
                    self.x = self.screen_width - self.size - (self.screen_width - original_x - self.size) * (i / hide_steps)
                elif edge == "top":
                    self.y = self.size + (original_y - self.size) * (i / hide_steps)
                elif edge == "bottom":
                    self.y = self.screen_height - self.size - (self.screen_height - original_y - self.size) * (i / hide_steps)
                
                # 更新窗口位置和透明度
                self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
                try:
                    self.anim_window.attributes('-alpha', alpha)
                except:
                    pass
                
                # 暂停一小段时间
                time.sleep(0.05)  # 每步暂停50ms，总出现时间为hide_steps * 0.05秒
            
            # 恢复完全不透明
            try:
                self.anim_window.attributes('-alpha', 1.0)
            except:
                pass
            
            print("大白鹅成功拉取并播放视频！")
            
            # 确保动画循环继续运行，让大白鹅继续在桌面上闲逛
            if hasattr(self, 'running') and self.running and hasattr(self, 'animate'):
                print("大白鹅继续在桌面上闲逛...")
            
        except Exception as e:
            print(f"播放视频时出错: {e}")
            # 确保恢复透明度
            try:
                if hasattr(self, 'anim_window'):
                    self.anim_window.attributes('-alpha', 1.0)
            except:
                pass
    
    def _show_video_window(self, edge):
        """不再显示模拟视频窗口，仅使用系统播放器播放视频"""
        pass  # 移除了模拟视频窗口的显示，仅保留方法名以保持代码兼容性
    
    def _show_folder_video_window_with_video(self, video_path):
        """显示带指定视频的Tkinter视频播放窗口"""
        # 先调用基础方法创建窗口
        self._show_folder_video_window()
        
        # 保存视频路径
        self.current_video_path = video_path
        
        # 在新线程中播放视频
        threading.Thread(target=self._play_video_with_path, args=(video_path,), daemon=True).start()
    
    def _play_video_with_path(self, video_path):
        """在内部窗口中播放指定路径的视频"""
        try:
            # 导入必要的库
            import cv2
            from PIL import Image, ImageTk
            
            # 更新状态
            self.root.after(0, lambda: setattr(self.video_status_label, "text", f"正在播放: {os.path.basename(video_path)}"))
            
            # 创建视频捕获对象
            self.cap = cv2.VideoCapture(video_path)
            
            # 获取视频属性
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:  # 如果获取不到FPS，设置默认值
                fps = 30
            
            # 计算每帧的延迟
            delay = int(1000 / fps)
            
            # 设置初始播放状态
            self.video_playing = True
            self.video_paused = False
            
            # 播放视频的函数
            def show_frame():
                if not self.video_playing:
                    return
                    
                if not self.video_paused and hasattr(self, 'cap') and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # 将BGR转换为RGB
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # 获取Canvas的尺寸
                        canvas_width = self.video_canvas.winfo_width()
                        canvas_height = self.video_canvas.winfo_height()
                        
                        # 计算视频帧的缩放比例以保持宽高比
                        frame_height, frame_width = rgb_frame.shape[:2]
                        scale = min(canvas_width / frame_width, canvas_height / frame_height)
                        new_width = int(frame_width * scale)
                        new_height = int(frame_height * scale)
                        
                        # 调整视频帧大小
                        resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                        
                        # 转换为PIL图像
                        pil_image = Image.fromarray(resized_frame)
                        
                        # 转换为Tkinter可用的图像
                        tk_image = ImageTk.PhotoImage(image=pil_image)
                        
                        # 清空Canvas并显示图像
                        self.video_canvas.delete("all")
                        
                        # 计算居中位置
                        x_pos = (canvas_width - new_width) // 2
                        y_pos = (canvas_height - new_height) // 2
                        
                        # 显示图像
                        self.video_canvas.create_image(x_pos, y_pos, anchor=tk.NW, image=tk_image)
                        
                        # 保存图像引用以防止被垃圾回收
                        self.video_canvas.image = tk_image
                    else:
                        # 视频播放结束，重新开始
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                # 继续下一帧
                if self.video_playing:
                    self.root.after(delay, show_frame)
            
            # 开始播放
            self.root.after(0, show_frame)
            
        except ImportError:
            # 如果缺少必要的库
            self.root.after(0, lambda: setattr(self.video_status_label, "text", "错误: 缺少必要的视频处理库"))
        except Exception as e:
            # 捕获其他异常
            self.root.after(0, lambda: setattr(self.video_status_label, "text", f"错误: {str(e)}"))
            # 确保释放资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                except:
                    pass
    
    def animate(self):
        # 动画循环
        if not self.running:
            return
        
        # 更新行为模式
        self.update_behavior_mode()
        
        # 更新动作状态
        self.update_action_state()
        
        # 根据当前模式更新移动
        if self.current_mode == 'explore':
            # 探索模式：随机移动
            if random.random() < 0.02:
                self.change_direction()
            if not self.is_dancing and not self.is_stretching:
                self.action_state = "walking"
        elif self.current_mode == 'rest':
            # 休息模式：移动缓慢或停止
            self.velocity_x *= 0.9
            self.velocity_y *= 0.9
            if not self.is_dancing and not self.is_stretching:
                self.action_state = "idle"
                # 休息时有几率进行特殊动作
                if random.random() < 0.005 and self.affection > 20:
                    self.update_action_state(True)
        elif self.current_mode == 'play':
            # 玩耍模式：快速随机移动
            if random.random() < 0.05:
                self.change_direction()
            self.velocity_x = max(-self.speed*1.5, min(self.speed*1.5, self.velocity_x))
            self.velocity_y = max(-self.speed*1.5, min(self.speed*1.5, self.velocity_y))
            if not self.is_dancing and not self.is_stretching:
                self.action_state = "walking"
                # 玩耍时有几率跳舞
                if random.random() < 0.01 and self.affection > 10:
                    self.start_dancing()
        elif self.current_mode == 'follow_mouse':
            # 跟随鼠标模式
            self.follow_mouse()
            if not self.is_dancing and not self.is_stretching:
                self.action_state = "walking"
        
        # 更新位置
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 检查碰撞
        self.check_collision()
        
        # 更新窗口位置
        self.anim_window.geometry(f"{self.size * 2}x{self.size * 2}+{int(self.x - self.size)}+{int(self.y - self.size)}")
        
        # 更新翅膀动画
        self.wing_animation_frame += self.wing_animation_speed
        
        # 足迹相关代码已移除
        
        # 更新对话框
        self.update_dialog()
        
        # 绘制鹅
        self.draw_goose()
        
        # 如果对话框显示中，重新绘制对话框
        if self.dialog_showing and self.dialog_text:
            self.show_dialog(self.dialog_text)
        
        # 继续动画循环
        self.root.after(self.animation_speed, self.animate)
    
    def stop(self):
        # 停止动画
        self.running = False
        self.stop_music()  # 停止音乐播放
        self.anim_window.destroy()

class EnhancedChatManager:
    def __init__(self):
        # 在线AI配置
        self.use_online_ai = True  # 是否使用在线AI
        self.api_url = "https://api.openai.com/v1/chat/completions"  # OpenAI API URL
        self.api_key = "sk-"  # 用户需要设置的API密钥
        self.model = "gpt-3.5-turbo"  # 使用的模型
        self.max_retries = 3  # 最大重试次数
        # 预定义回复集合
        self.replies = {
            "greeting": [
                "你好呀！我是一只可爱的大白鹅～ 嘎嘎！",
                "嗨！很高兴见到你！要一起玩吗？～ 嘎嘎！",
                "你好你好！今天过得怎么样？～ 嘎嘎！",
                "早晨的阳光真美好，就像见到你一样开心！～ 嘎嘎！",
                "晚上好！今天有没有遇到有趣的事情呀？～ 嘎嘎！",
                "嗨喽！能和你聊天我感到特别荣幸！～ 嘎嘎！"
            ],
            "thanks": [
                "不客气，这是我应该做的！～ 嘎嘎！",
                "能帮到你我很开心！～ 嘎嘎！",
                "随时为你服务！～ 嘎嘎！",
                "举手之劳，不足挂齿！～ 嘎嘎！",
                "能成为你的朋友我就很满足了！～ 嘎嘎！",
                "你的感谢让我一整天都充满能量！～ 嘎嘎！"
            ],
            "goodbye": [
                "再见啦！记得常来找我玩哦～ 嘎嘎！",
                "下次见！我会想念你的～ 嘎嘎！",
                "拜拜！祝你有美好的一天！～ 嘎嘎！",
                "期待下次与你相遇！要好好照顾自己哦～ 嘎嘎！",
                "晚安！希望你做个甜甜的梦！～ 嘎嘎！",
                "后会有期！我会在这里等你回来的～ 嘎嘎！"
            ],
            "hobby": [
                "我喜欢在水里游泳，还有吃绿绿的青草！～ 嘎嘎！",
                "我最喜欢晒太阳和整理我的羽毛了！～ 嘎嘎！",
                "我喜欢追逐小虫子，那是最有趣的游戏！～ 嘎嘎！",
                "我还喜欢看日落，湖面被染成金黄色的时候真美！～ 嘎嘎！",
                "下雨天我喜欢听雨滴打在荷叶上的声音～ 嘎嘎！",
                "有时候我会练习飞行，虽然飞不高但很快乐！～ 嘎嘎！"
            ],
            "weather": [
                "今天天气真好，阳光明媚，适合游泳！～ 嘎嘎！",
                "下雨天我喜欢躲在屋檐下，听雨滴的声音～ 嘎嘎！",
                "晴朗的天空让我的心情也变得很好！～ 嘎嘎！",
                "微风拂面的日子最适合出去散步了！～ 嘎嘎！",
                "下雪的时候世界一片洁白，太美了！～ 嘎嘎！",
                "阴天也不错，适合躲在草丛里休息～ 嘎嘎！"
            ],
            "hungry": [
                "我现在有点饿了，想吃点青草或小虫子～ 嘎嘎！",
                "肚子咕咕叫，有什么好吃的吗？～ 嘎嘎！",
                "给我点吃的吧，我会很感激你的！～ 嘎嘎！",
                "新鲜的嫩草是我的最爱，嚼起来特别香！～ 嘎嘎！",
                "我也喜欢吃玉米粒，甜甜的很好吃！～ 嘎嘎！",
                "如果有面包屑的话，我也会很开心的！～ 嘎嘎！"
            ],
            "happy": [
                "我今天特别开心，感觉能飞起来！～ 嘎嘎！",
                "和你聊天让我心情好好！～ 嘎嘎！",
                "快乐就是这么简单！～ 嘎嘎！",
                "今天阳光好，心情也跟着明媚起来！～ 嘎嘎！",
                "扑棱翅膀就能带来好心情，你也试试！～ 嘎嘎！",
                "看到你我就忍不住想笑，你真是我的开心果！～ 嘎嘎！"
            ],
            "sad": [
                "别难过，一切都会好起来的！～ 嘎嘎！",
                "我会陪在你身边的，不要伤心～ 嘎嘎！",
                "给你一个大大的拥抱！～ 嘎嘎！",
                "每个人都有难过的时候，重要的是要学会坚强！～ 嘎嘎！",
                "想哭就哭吧，眼泪能带走不开心的情绪～ 嘎嘎！",
                "我会用我的翅膀为你遮风挡雨！～ 嘎嘎！"
            ],
            "unknown": [
                "抱歉，我不太明白你的意思～ 嘎嘎！",
                "能换个方式告诉我吗？～ 嘎嘎！",
                "这个问题有点难，我需要思考一下～ 嘎嘎！",
                "我的小脑袋瓜还在发育中，需要慢慢学习～ 嘎嘎！",
                "也许我们可以聊点简单的话题？～ 嘎嘎！",
                "这个问题太深奥了，我需要去请教其他的鹅朋友！～ 嘎嘎！"
            ],
            "praise": [
                "谢谢你的夸奖，我会继续努力的！～ 嘎嘎！",
                "能得到你的认可真是太开心了！～ 嘎嘎！",
                "你也很厉害呢！～ 嘎嘎！",
                "你的话让我脸红心跳，人家会不好意思的～ 嘎嘎！",
                "我会把你的夸奖珍藏在心里的！～ 嘎嘎！",
                "有你的鼓励，我感觉自己能做得更好！～ 嘎嘎！"
            ],
            "help": [
                "我可以陪你聊天，给你解闷！～ 嘎嘎！",
                "有什么我能帮到你的吗？～ 嘎嘎！",
                "告诉我你的需求，我会尽力帮助你！～ 嘎嘎！",
                "虽然我只是一只鹅，但我会全力以赴的！～ 嘎嘎！",
                "无论何时，我都愿意倾听你的烦恼！～ 嘎嘎！",
                "需要一个拥抱吗？我随时都在这里！～ 嘎嘎！"
            ],
            "video": [
                "我刚刚从桌面边缘拉了一个精彩视频，你看到了吗？～ 嘎嘎！",
                "视频里有好多美丽的风景，就像我家乡的湖泊一样！～ 嘎嘎！",
                "我喜欢分享有趣的视频，希望你也喜欢！～ 嘎嘎！",
                "如果视频不好看，我下次拉个更好的！～ 嘎嘎！",
                "看视频是我最喜欢的休闲活动之一！～ 嘎嘎！",
                "你想看什么类型的视频？我可以帮你找找！～ 嘎嘎！"
            ],
            "folder": [
                "我一直在帮你监控那个特殊的文件夹哦！～ 嘎嘎！",
                "要小心保护重要的文件呢！～ 嘎嘎！",
                "文件夹里是不是藏着什么秘密呀？～ 嘎嘎！",
                "我会帮你看好文件夹的，放心吧！～ 嘎嘎！",
                "有人靠近文件夹时我会提醒你的！～ 嘎嘎！",
                "保护文件是我的重要任务之一！～ 嘎嘎！"
            ],
            "funny": [
                "为什么鹅会游泳？因为它们有鹅泳裤！～ 嘎嘎！",
                "有一天，一只鹅走进了酒吧...酒保说：'你为什么在这里？'鹅说：'因为我会游泳但不会飞！'～ 嘎嘎！",
                "我刚学了一个新词：鹅毛大雪！是不是很有趣？～ 嘎嘎！",
                "你知道鹅最喜欢听什么音乐吗？当然是'鹅鹅鹅，曲项向天歌'啦！～ 嘎嘎！",
                "为什么鹅总是排成一队游泳？因为它们不想掉队！～ 嘎嘎！",
                "我今天学了个新技能：假装自己是一只鸭子！～ 嘎嘎！"
            ],
            "story": [
                "从前，有一只可爱的大白鹅，它有一个特别的能力...可以从桌面边缘拉视频！～ 嘎嘎！",
                "我想给你讲个故事：在一个美丽的湖边，住着一只快乐的小鹅，它每天都...～ 嘎嘎！",
                "有一天，大白鹅发现了一个神奇的文件夹，每当有人打开它...～ 嘎嘎！",
                "从前从前，有一只会魔法的鹅，它能用翅膀创造出美丽的画面...～ 嘎嘎！",
                "我给你讲个睡前故事吧：夜深了，一只小鹅蜷缩在温暖的羽毛里，做了一个甜甜的梦...～ 嘎嘎！",
                "在遥远的鹅王国里，有一只勇敢的鹅骑士，它的使命是...～ 嘎嘎！"
            ]
        }
        
        # 关键词分类
        self.keywords = {
            "greeting": ["你好", "嗨", "哈喽", "早上好", "晚上好", "中午好", "嗨喽", "您好", "喂"],
            "thanks": ["谢谢", "感谢", "多谢", "谢啦", "感激", "辛苦了", "感恩"],
            "goodbye": ["再见", "拜拜", "下次见", "回头见", "晚安", "bye", "拜"],
            "hobby": ["喜欢", "爱好", "爱做", "平时做什么", "兴趣", "特长", "擅长"],
            "weather": ["天气", "下雨", "晴天", "多云", "温度", "气温", "预报"],
            "hungry": ["饿", "想吃", "肚子", "吃饭", "食物", "美食", "大餐"],
            "happy": ["开心", "高兴", "快乐", "愉快", "兴奋", "喜悦", "欢乐"],
            "sad": ["难过", "伤心", "不开心", "郁闷", "烦恼", "沮丧", "悲伤"],
            "praise": ["可爱", "厉害", "棒", "聪明", "好看", "优秀", "棒极了"],
            "help": ["帮助", "帮我", "需要帮忙", "求助", "求救", "需要帮助"],
            "video": ["视频", "电影", "播放", "看视频", "看电视", "放映"],
            "folder": ["文件夹", "文件", "文档", "监控", "保护"],
            "funny": ["笑话", "搞笑", "好玩", "有趣", "幽默", "笑死了"],
            "story": ["故事", "讲个故事", "传说", "睡前故事", "童话", "神话"]
        }
        
        # 直接回答映射
        self.direct_answers = {
            "你是谁": "我是一只可爱的大白鹅！很高兴认识你！～ 嘎嘎！",
            "你叫什么名字": "我是大白鹅，你可以叫我鹅鹅！～ 嘎嘎！",
            "你多大了": "我还是一只小鹅呢！～ 嘎嘎！",
            "你从哪里来": "我从湖边来，那里有绿绿的青草和清澈的湖水！～ 嘎嘎！",
            "你会飞吗": "虽然我是鹅，但我现在还太小，飞不高呢！～ 嘎嘎！",
            "你喜欢什么颜色": "我喜欢白色，因为和我的羽毛很配！～ 嘎嘎！",
            "今天星期几": f"今天是{time.strftime('%A')}！～ 嘎嘎！",
            "现在几点了": f"现在是{time.strftime('%H:%M')}！～ 嘎嘎！",
            "你会说话": "当然啦！我可是一只会说话的神奇大白鹅！～ 嘎嘎！",
            "你喜欢我吗": "当然喜欢你啦！你是我最好的朋友！～ 嘎嘎！",
            "你吃什么": "我喜欢吃青草、玉米粒和小虫子！～ 嘎嘎！",
            "你住在哪里": "我住在你的电脑桌面上，随时陪伴着你！～ 嘎嘎！",
            "你会游泳吗": "那是当然！游泳可是我们鹅族的拿手好戏！～ 嘎嘎！",
            "你为什么会在我的电脑上": "因为我想和你做朋友呀！～ 嘎嘎！",
            "你有什么本领": "我会拉视频、聊天、监控文件夹，还会给你讲笑话！～ 嘎嘎！",
            "你喜欢做什么": "我喜欢和你聊天、在桌面上散步、从边缘拉视频！～ 嘎嘎！",
            "你害怕什么": "我最怕孤独了，所以谢谢你一直陪着我！～ 嘎嘎！",
            "你会想念我吗": "当然会！每一刻我都在想念你！～ 嘎嘎！",
            "你困了吗": "有一点点，但只要能和你聊天，我就精神百倍！～ 嘎嘎！",
            "你开心吗": "只要和你在一起，我每天都很开心！～ 嘎嘎！",
            "给我讲个笑话": "为什么鹅会游泳？因为它们有鹅泳裤！～ 嘎嘎！",
            "讲个故事": "从前，有一只可爱的大白鹅，它有一个特别的能力...可以从桌面边缘拉视频！～ 嘎嘎！",
            "你在做什么": "我在看着你，随时准备和你聊天！～ 嘎嘎！",
            "你喜欢听音乐吗": "喜欢！特别是'鹅鹅鹅，曲项向天歌'这首！～ 嘎嘎！",
            "你冷吗": "我有厚厚的羽毛，一点都不冷！～ 嘎嘎！",
            "你热吗": "热的时候我就想象自己在清凉的湖水里游泳！～ 嘎嘎！",
            "你会跳舞吗": "当然会！我可是鹅族的舞蹈高手！～ 嘎嘎！",
            "你会唱歌吗": "我会唱'嘎嘎嘎嘎'，要不要听？～ 嘎嘎！",
            "你会保护我吗": "是的！我会用我的生命保护你！～ 嘎嘎！",
            "你能帮我什么": "我可以陪你聊天解闷，还能帮你监控重要文件夹！～ 嘎嘎！"
        }
        
        # 对话历史管理
        self.conversation_history = []
        self.max_history_length = 5  # 最多保存5轮对话
    
    def classify_input(self, user_input):
        # 转换为小写进行匹配
        user_input = user_input.lower()
        
        # 先检查直接回答
        for question, answer in self.direct_answers.items():
            if question in user_input:
                return "direct", question
        
        # 检查关键词
        for category, words in self.keywords.items():
            for word in words:
                if word in user_input:
                    return "category", category
        
        # 未分类
        return "unknown", None
    
    def _get_online_ai_response(self, user_input):
        """调用在线AI获取回复"""
        if not self.use_online_ai or not self.api_key or self.api_key == "sk-":
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 准备对话历史
        messages = []
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": "你是一只可爱的大白鹅，喜欢用嘎嘎声结束句子。性格活泼友好，喜欢和人类聊天。请保持简短的回复风格，语气可爱。"
        })
        
        # 添加历史对话
        for role, content in self.conversation_history:
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })
        
        # 添加最新用户输入
        messages.append({"role": "user", "content": user_input})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    print(f"在线AI调用失败: HTTP {response.status_code}")
                    if attempt == self.max_retries - 1:
                        return None
            except Exception as e:
                print(f"在线AI调用异常: {e}")
                if attempt == self.max_retries - 1:
                    return None
            
            # 重试间隔
            time.sleep(1)
        
        return None
    
    def generate_response(self, user_input):
        # 添加到对话历史
        self.conversation_history.append(("user", user_input))
        
        # 首先尝试在线AI回复
        online_response = self._get_online_ai_response(user_input)
        if online_response:
            # 确保回复以"～ 嘎嘎！"结尾
            if not online_response.endswith("～ 嘎嘎！"):
                online_response += "～ 嘎嘎！"
            response = online_response
        else:
            # 在线AI失败时使用本地回复
            # 分类输入
            input_type, category = self.classify_input(user_input)
            
            # 生成回复
            if input_type == "direct":
                response = self.direct_answers[category]
            elif input_type == "category":
                response = random.choice(self.replies[category])
            else:
                response = random.choice(self.replies["unknown"])
        
        # 添加到对话历史
        self.conversation_history.append(("bot", response))
        
        # 保持历史记录长度
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length*2:]
        
        return response
    
    def send_prompt(self, user_input):
        # 获取基础回复
        base_response = self.generate_response(user_input)
        
        # 检查是否是在线AI回复（通常会包含'～ 嘎嘎！'结尾）
        is_online_response = "～ 嘎嘎！" in base_response
        
        if not is_online_response:
            # 如果是本地回复，添加时间问候等装饰
            # 根据时间调整回复
            hour = int(time.strftime('%H'))
            if 6 <= hour < 12:
                time_greeting = "早上好！"
            elif 12 <= hour < 18:
                time_greeting = "下午好！"
            else:
                time_greeting = "晚上好！"
            
            # 随机添加动作描述
            actions = ["扑棱着翅膀", "歪着脑袋", "甩了甩尾巴", "眨了眨眼睛", "抖了抖羽毛"]
            action = random.choice(actions)
            
            # 随机添加额外的叫声
            extra_quacks = ["嘎嘎！", "嘎嘎嘎！", "呱呱！"]
            extra_quack = random.choice(extra_quacks)
            
            # 组合最终回复
            final_response = f"🦢 {base_response} {action} {extra_quack}"
            
            # 避免重复回复
            if len(self.conversation_history) > 2:
                last_response = self.conversation_history[-3][1]
                if final_response == last_response:
                    # 重新生成
                    base_response = self.generate_response(user_input)
                    final_response = f"🦢 {base_response} {action} {extra_quack}"
        else:
            # 在线AI回复已经很好，只添加图标
            final_response = f"🦢 {base_response}"
        
        return final_response

class ChatWindow:
    def __init__(self, root, ai_manager, position=None):
        self.root = root
        self.ai_manager = ai_manager
        
        # 创建聊天窗口
        self.window = tk.Toplevel(root)
        self.window.title("大白鹅聊天室")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        
        # 设置窗口位置
        if position:
            x, y = position
            self.window.geometry(f"+{x}+{y}")
        
        # 设置窗口样式
        self.window.configure(bg='#E0F7FA')  # 浅蓝色背景，符合鹅的主题
        
        # 创建标题栏（可拖动）
        self.title_bar = tk.Frame(self.window, bg='#FFE082', height=30, bd=1, relief=tk.RAISED)
        self.title_bar.pack(fill=tk.X)
        
        # 标题文字
        self.title_label = tk.Label(self.title_bar, text="大白鹅聊天室", bg='#FFE082', font=('SimHei', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 窗口拖动相关
        self.is_dragging = False
        self.drag_x = 0
        self.drag_y = 0
        
        # 绑定标题栏事件
        self.title_bar.bind("<Button-1>", self.on_header_click)
        self.title_bar.bind("<B1-Motion>", self.on_header_drag)
        
        # 创建聊天区域
        self.chat_frame = tk.Frame(self.window, bg='#E0F7FA')
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建文本框显示聊天内容
        self.chat_text = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED, 
                               bg='#FFFFFF', font=('SimHei', 10))
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=self.scrollbar.set)
        
        # 创建输入区域
        self.input_frame = tk.Frame(self.window, bg='#E0F7FA')
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建输入框
        self.input_text = tk.Entry(self.input_frame, font=('SimHei', 10))
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.input_text.bind("<Return>", self.send_message)
        
        # 创建发送按钮
        self.send_button = tk.Button(self.input_frame, text="发送", command=self.send_message, 
                                   bg='#81C784', fg='white', font=('SimHei', 10, 'bold'))
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 添加装饰性水草边框
        self.create_water_grass_decoration()
        
        # 初始消息
        self.add_message("系统", "🦢 你好呀！我是可爱的大白鹅，很高兴认识你！～ 嘎嘎！")
    
    def create_water_grass_decoration(self):
        # 在窗口边缘添加装饰性水草
        pass  # 简化处理，实际项目中可以添加更复杂的装饰
    
    def on_header_click(self, event):
        # 处理标题栏点击事件
        self.is_dragging = True
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_header_drag(self, event):
        # 处理标题栏拖动事件
        if self.is_dragging:
            x = self.window.winfo_pointerx() - self.drag_x
            y = self.window.winfo_pointery() - self.drag_y
            self.window.geometry(f"+{x}+{y}")
    
    def add_message(self, sender, message):
        # 添加消息到聊天窗口
        self.chat_text.config(state=tk.NORMAL)
        
        # 插入发送者
        if sender == "你":
            self.chat_text.insert(tk.END, f"{sender}: ", "user_sender")
        else:
            self.chat_text.insert(tk.END, f"{sender}: ", "bot_sender")
        
        # 插入消息内容
        if sender == "你":
            self.chat_text.insert(tk.END, f"{message}\n", "user_message")
        else:
            self.chat_text.insert(tk.END, f"{message}\n", "bot_message")
        
        # 配置标签样式
        self.chat_text.tag_configure("user_sender", font=("SimHei", 10, "bold"), foreground="#2196F3")
        self.chat_text.tag_configure("bot_sender", font=("SimHei", 10, "bold"), foreground="#4CAF50")
        self.chat_text.tag_configure("user_message", font=("SimHei", 10), background="#E3F2FD", justify="right")
        self.chat_text.tag_configure("bot_message", font=("SimHei", 10), background="#E8F5E9", justify="left")
        
        # 滚动到底部
        self.chat_text.see(tk.END)
        
        # 禁用编辑
        self.chat_text.config(state=tk.DISABLED)
        
        # 如果有关联的鹅实例，将消息添加到对话历史
        if hasattr(self, 'goose_instance') and self.goose_instance:
            self.goose_instance.add_conversation_message(sender, message)
    
    def send_message(self, event=None):
        # 获取用户输入
        user_input = self.input_text.get().strip()
        
        if user_input:
            # 添加用户消息
            self.add_message("你", user_input)
            
            # 清空输入框
            self.input_text.delete(0, tk.END)
            
            # 添加思考中提示
            self.add_message("大白鹅", "正在整理羽毛思考中...")
            
            # 在新线程中获取AI回复，避免界面卡顿
            threading.Thread(target=self._get_ai_response, args=(user_input,)).start()
    
    def _get_ai_response(self, user_input):
        # 获取AI回复
        response = self.ai_manager.send_prompt(user_input)
        
        # 更新UI（必须在主线程中进行）
        self.root.after(0, self._update_chat, response)
    
    def _update_chat(self, response):
        # 更新聊天界面
        # 首先移除思考中的消息
        self.chat_text.config(state=tk.NORMAL)
        last_line_start = self.chat_text.index("end-2l")
        last_line_end = self.chat_text.index("end-1l")
        self.chat_text.delete(last_line_start, last_line_end)
        
        # 添加AI回复
        self.chat_text.insert(tk.END, f"大白鹅: {response}\n", "bot_message")
        
        # 滚动到底部
        self.chat_text.see(tk.END)
        
        # 禁用编辑
        self.chat_text.config(state=tk.DISABLED)
        
        # 如果有关联的鹅实例，将AI回复添加到对话历史
        if hasattr(self, 'goose_instance') and self.goose_instance:
            self.goose_instance.add_conversation_message("大白鹅", response)

class FolderMonitor:
    def __init__(self, folder_path, callback_func):
        self.folder_path = folder_path
        self.callback_func = callback_func
        self.running = True
        self.folder_was_opened = False  # 跟踪文件夹是否被打开过
        self.last_close_time = 0  # 上次关闭文件夹的时间
        self.cooldown_period = 60  # 冷却时间（秒），设置为60秒
        
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
        while self.running:
            try:
                # 检查文件夹是否存在
                if os.path.exists(self.folder_path):
                    try:
                        # 尝试打开文件夹中的一个临时文件，如果成功打开，说明文件夹未被独占
                        test_file = os.path.join(self.folder_path, "test_access.tmp")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        # 如果之前检测到文件夹被打开，现在可以正常访问，说明文件夹已关闭
                        if self.folder_was_opened:
                            print("张恩实文件夹已关闭")
                            self.folder_was_opened = False
                    except Exception as e:
                        # 如果无法创建或删除文件，可能是文件夹被打开了
                        # 只有在第一次检测到被打开时触发回调
                        if not self.folder_was_opened:
                            print(f"检测到张恩实文件夹被打开: {e}")
                            current_time = time.time()
                            # 检查是否在冷却期内
                            if current_time - self.last_close_time > self.cooldown_period:
                                print("冷却期已过，正在关闭文件夹...")
                                # 自动关闭文件夹窗口
                                self._close_folder_window()
                                self.last_close_time = current_time
                                print(f"文件夹已关闭，冷却期开始。将在{self.cooldown_period}秒后再次响应。")
                            else:
                                remaining = self.cooldown_period - (current_time - self.last_close_time)
                                print(f"冷却期内，{remaining:.1f}秒后再响应")
                            # 调用回调函数拉视频而不是退出程序
                            self.callback_func()
                            self.folder_was_opened = True
            except Exception as e:
                print(f"监控文件夹时出错: {e}")
            
            # 每2秒检查一次，减少资源占用
            time.sleep(2)

    def _close_folder_window(self):
        # 查找并关闭包含张恩实文件夹的资源管理器窗口
        def callback(hwnd, extra):
            # 检查窗口类是否为资源管理器
            if win32gui.GetClassName(hwnd) in ['CabinetWClass', 'ExploreWClass']:
                # 获取窗口标题
                title = win32gui.GetWindowText(hwnd)
                # 检查标题是否包含"张恩实"
                if '张恩实' in title:
                    print(f"找到张恩实文件夹窗口: {title}")
                    # 关闭窗口
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    extra.append(hwnd)
            return True
        
        closed_windows = []
        win32gui.EnumWindows(callback, closed_windows)
        
        if not closed_windows:
            print("未找到张恩实文件夹窗口，但尝试通过进程名关闭")
            # 备用方案：尝试关闭可能打开该文件夹的explorer进程
            try:
                # 使用taskkill关闭特定的explorer进程（但这会关闭所有explorer窗口，作为最后的备选）
                # 更安全的方式是使用PowerShell查找打开特定路径的explorer进程
                ps_command = f"powershell -Command \"Get-Process explorer | Where-Object {{ $_.MainWindowTitle -like '*张恩实*' }} | Stop-Process\""
                subprocess.run(ps_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("尝试通过PowerShell关闭特定的explorer进程")
            except Exception as e:
                print(f"关闭文件夹进程时出错: {e}")

class GooseChaseApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # 隐藏主窗口
        
        # 鹅动画管理
        self.active_geese = []
        
        # 聊天窗口管理
        self.chat_windows = []
        
        # AI管理器
        self.ai_manager = EnhancedChatManager()
        
        # 检查并设置API密钥
        self._check_api_key()
        
        # 创建系统托盘图标窗口
        self.tray_window = tk.Toplevel(self.root)
        # 设置窗口标题，使其在任务栏中显示
        self.tray_window.title("大白鹅菜单")
        
        # 设置窗口样式，使用工具窗口减少标题栏空间，同时保持在任务栏显示
        self.tray_window.attributes('-toolwindow', True)  # 使用工具窗口样式
        self.tray_window.resizable(False, False)  # 不可调整大小
        self.tray_window.geometry("40x40+0+0")  # 小窗口，放在左上角
        self.tray_window.attributes('-topmost', True)  # 窗口置顶
        
        # 拖拽相关变量
        self.drag_data = {"x": 0, "y": 0}
        # 绑定拖拽事件
        self.tray_window.bind("<Button-1>", self.on_tray_drag_start)
        self.tray_window.bind("<B1-Motion>", self.on_tray_drag_motion)
        
        # 创建托盘图标
        self.create_tray_icon()
        
        # 创建右键菜单
        self.create_tray_menu()
        
        # 绑定事件 - 右键显示菜单，左键松开时检查是否是点击
        self.tray_window.bind("<Button-3>", self.show_tray_menu)
        self.tray_window.bind("<ButtonRelease-1>", self.on_tray_click)
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self.cleanup_finished_geese, daemon=True)
        self.cleanup_thread.start()
        
        # 配置要监控的文件夹路径
        # 默认检查用户文档目录下的"张恩实"文件夹
        self.target_folder = os.path.join(os.path.expanduser('~'), "Documents", "张恩实")
        
        # 尝试查找张恩实文件夹的实际位置
        found_folder = find_target_folder("张恩实")
        if found_folder:
            self.target_folder = found_folder
            print(f"找到张恩实文件夹：{self.target_folder}")
        else:
            print(f"未找到张恩实文件夹，使用默认路径：{self.target_folder}")
        
        # 启动文件夹监控
        self.folder_monitor = FolderMonitor(self.target_folder, self.on_folder_opened)
        self.folder_monitor.start_monitoring()
    
    def on_tray_drag_start(self, event):
        """开始拖拽托盘窗口或处理左键点击"""
        # 记录鼠标相对窗口的位置
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
        # 如果点击的是label而不是窗口本身，也能正确处理
        if hasattr(self, 'tray_label') and event.widget == self.tray_label:
            self.tray_window.focus_force()
        
        # 记录点击时间，用于区分点击和拖拽
        self.click_time = time.time()
        self.click_pos = (event.x, event.y)
    
    def on_tray_drag_motion(self, event):
        """处理托盘窗口拖拽"""
        # 计算新位置
        x = self.tray_window.winfo_pointerx() - self.drag_data["x"]
        y = self.tray_window.winfo_pointery() - self.drag_data["y"]
        # 移动窗口
        self.tray_window.geometry(f"40x40+{x}+{y}")
    
    def on_tray_click(self, event):
        """处理托盘窗口左键点击（非拖拽）"""
        # 检查是否是简单点击而非拖拽
        current_time = time.time()
        time_diff = current_time - getattr(self, 'click_time', 0)
        pos_diff = (abs(event.x - getattr(self, 'click_pos', (0,0))[0]), 
                   abs(event.y - getattr(self, 'click_pos', (0,0))[1]))
        
        # 如果点击时间短且移动距离小，则认为是点击事件
        if time_diff < 0.2 and pos_diff[0] < 5 and pos_diff[1] < 5:
            # 确保summon_goose是可调用的
            if hasattr(self, 'summon_goose') and callable(self.summon_goose):
                self.summon_goose()
            else:
                print("警告: summon_goose方法不可用")
    
    def on_folder_opened(self):
        # 当检测到张恩实文件夹被打开时的处理函数
        print("检测到张恩实文件夹被打开，正在拉出视频！")
        self.pull_video_from_folder()
    
    def pull_video_from_folder(self):
        """从文件夹打开事件中拉视频"""
        # 在主线程中创建视频窗口
        self.root.after(0, self._show_folder_video_window)
    
    def _show_folder_video_window_with_video(self, video_path):
        """显示Tkinter视频播放窗口并播放指定的视频文件"""
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # 创建一个特殊的视频窗口
            video_window = tk.Toplevel(self.root)
            video_window.title("🦢 视频播放 🦢")
            video_window.geometry("800x600+{}+{}".format(
                (screen_width - 800) // 2, (screen_height - 600) // 2
            ))
            video_window.configure(bg="#212121")
            video_window.attributes('-topmost', True)
            
            # 添加标题信息
            title_frame = tk.Frame(video_window, bg="#4CAF50")
            title_frame.pack(fill=tk.X)
            
            title_label = tk.Label(
                title_frame, 
                text="🦢 视频播放 🦢", 
                font=("SimHei", 14, "bold"), 
                fg="white", 
                bg="#4CAF50"
            )
            title_label.pack(pady=10)
            
            # 添加状态显示区域
            status_frame = tk.Frame(video_window, bg="#212121")
            status_frame.pack(fill=tk.X, padx=20, pady=10)
            
            self.video_status_label = tk.Label(
                status_frame, 
                text="准备播放视频...", 
                font=("SimHei", 12), 
                fg="#E0E0E0", 
                bg="#212121",
                justify=tk.CENTER
            )
            self.video_status_label.pack(fill=tk.X)
            
            # 创建视频显示区域（Canvas）
            canvas_frame = tk.Frame(video_window, bg="#000000")
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            self.video_canvas = tk.Canvas(
                canvas_frame, 
                bg="#000000", 
                highlightthickness=0
            )
            self.video_canvas.pack(fill=tk.BOTH, expand=True)
            
            # 添加控制按钮区域
            control_frame = tk.Frame(video_window, bg="#212121")
            control_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # 播放/暂停按钮
            self.play_pause_button = tk.Button(
                control_frame, 
                text="⏸️ 暂停", 
                font=("SimHei", 12),
                bg="#4CAF50", 
                fg="white",
                padx=20, 
                pady=8,
                relief=tk.RAISED,
                command=lambda: self.toggle_play_pause(video_window)
            )
            self.play_pause_button.pack(side=tk.LEFT, padx=5)
            
            # 停止按钮
            stop_button = tk.Button(
                control_frame, 
                text="⏹️ 停止", 
                font=("SimHei", 12),
                bg="#F44336", 
                fg="white",
                padx=20, 
                pady=8,
                relief=tk.RAISED,
                command=lambda: self.stop_video(video_window)
            )
            stop_button.pack(side=tk.LEFT, padx=5)
            
            # 窗口关闭时的回调
            video_window.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_video_resources(video_window))
            
            # 设置播放状态
            self.is_playing = True
            
            # 更新状态标签
            try:
                video_info = "正在播放视频..."
                if video_path and hasattr(os, 'path') and hasattr(os.path, 'basename'):
                    try:
                        video_info = f"正在播放: {os.path.basename(video_path)}"
                    except Exception:
                        # 如果获取视频名称失败，使用默认信息
                        pass
                if hasattr(self, 'video_status_label') and self.video_status_label.winfo_exists():
                    self.video_status_label.config(text=video_info)
            except:
                pass
            
            # 保存视频路径作为实例属性
            self.video_path = video_path
            
            # 使用OpenCV播放视频
            threading.Thread(target=self._play_video_with_path, args=(video_window, video_path), daemon=True).start()
            
        except Exception as e:
            print(f"创建视频窗口时出错: {e}")
    
    def _play_video_with_path(self, video_window, video_path):
        """使用OpenCV播放指定路径的视频"""
        try:
            import cv2
            from PIL import Image, ImageTk
            
            # 更新状态标签
            def update_status_label(text="正在准备视频..."):
                try:
                    if hasattr(self, 'video_status_label') and self.video_status_label.winfo_exists():
                        self.video_status_label.config(text=text)
                except (tk.TclError, AttributeError):
                    pass
            
            self.root.after(0, lambda: update_status_label(f"正在播放: {os.path.basename(video_path)}"))
            
            # 创建视频捕获对象
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                self.root.after(0, lambda: update_status_label("无法打开视频文件"))
                print(f"无法打开视频文件: {video_path}")
                return
            
            # 获取视频信息
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # 默认帧率
            
            delay = int(1000 / fps)  # 帧延迟（毫秒）
            
            # 视频帧显示函数
            def show_frame():
                if not hasattr(self, 'cap') or not self.cap or not hasattr(self, 'is_playing'):
                    return
                
                if not self.is_playing:
                    return
                
                # 检查窗口是否存在
                if not video_window.winfo_exists():
                    # 窗口已关闭，释放资源
                    if hasattr(self, 'cap') and self.cap:
                        self.cap.release()
                        self.cap = None
                    return
                
                # 获取Canvas尺寸
                try:
                    canvas_width = self.video_canvas.winfo_width()
                    canvas_height = self.video_canvas.winfo_height()
                except:
                    return
                
                if canvas_width < 10 or canvas_height < 10:
                    # Canvas还没准备好，稍后重试
                    video_window.after(100, show_frame)
                    return
                
                # 读取一帧视频
                ret, frame = self.cap.read()
                
                if not ret:
                    # 视频播放完毕，重新开始
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        # 仍然无法读取，可能视频已损坏
                        self.root.after(0, lambda: update_status_label("视频播放出错"))
                        if hasattr(self, 'cap') and self.cap:
                            self.cap.release()
                            self.cap = None
                        return
                
                # 转换颜色格式（BGR -> RGB）
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 计算调整后的尺寸，保持宽高比
                video_height, video_width = rgb_frame.shape[:2]
                aspect_ratio = video_width / video_height
                
                if canvas_width / canvas_height > aspect_ratio:
                    # Canvas更宽，以高度为准
                    new_height = canvas_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    # Canvas更高，以宽度为准
                    new_width = canvas_width
                    new_height = int(new_width / aspect_ratio)
                
                # 调整图像大小
                resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                
                # 转换为PIL图像
                pil_image = Image.fromarray(resized_frame)
                
                # 转换为Tkinter可用的图像
                tk_image = ImageTk.PhotoImage(image=pil_image)
                
                # 清除Canvas并显示新帧
                try:
                    self.video_canvas.delete('all')
                    # 居中显示视频
                    x_offset = (canvas_width - new_width) // 2
                    y_offset = (canvas_height - new_height) // 2
                    self.video_frame_id = self.video_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=tk_image)
                    
                    # 保存引用，防止被垃圾回收
                    self.video_canvas.current_image = tk_image
                except:
                    return
                
                # 继续播放下一帧
                if video_window.winfo_exists() and self.is_playing:
                    video_window.after(delay, show_frame)
            
            # 开始播放视频
            video_window.after(100, show_frame)
            
        except ImportError:
            error_msg = "缺少必要的库。请安装opencv-python和pillow。"
            print(error_msg)
            self.root.after(0, lambda: update_status_label(error_msg))
        except Exception as e:
            error_msg = f"播放视频时出错: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: update_status_label(error_msg))
            # 确保释放资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                except:
                    pass
    def _show_folder_video_window(self):
        """显示Tkinter视频播放窗口"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 创建一个特殊的视频窗口
        video_window = tk.Toplevel(self.root)
        video_window.title("🦢 视频播放 🦢")
        video_window.geometry("800x600+{}+{}".format(
            (screen_width - 800) // 2, (screen_height - 600) // 2
        ))
        video_window.configure(bg="#212121")
        video_window.attributes('-topmost', True)
        
        # 添加标题信息
        title_frame = tk.Frame(video_window, bg="#4CAF50")
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame, 
            text="🦢 视频播放 🦢", 
            font=("SimHei", 14, "bold"), 
            fg="white", 
            bg="#4CAF50"
        )
        title_label.pack(pady=10)
        
        # 添加状态显示区域
        status_frame = tk.Frame(video_window, bg="#212121")
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.video_status_label = tk.Label(
            status_frame, 
            text="准备播放视频...", 
            font=("SimHei", 12), 
            fg="#E0E0E0", 
            bg="#212121",
            justify=tk.CENTER
        )
        self.video_status_label.pack(fill=tk.X)
        
        # 创建视频显示区域（Canvas）
        self.video_canvas = tk.Canvas(video_window, bg="#000000")
        self.video_canvas.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # 添加控制按钮
        control_frame = tk.Frame(video_window, bg="#333333")
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.play_pause_button = tk.Button(
            control_frame, 
            text="播放", 
            font=("SimHei", 12), 
            fg="white", 
            bg="#4CAF50",
            relief=tk.FLAT,
            command=self.toggle_play_pause
        )
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = tk.Button(
            control_frame, 
            text="停止", 
            font=("SimHei", 12), 
            fg="white", 
            bg="#F44336",
            relief=tk.FLAT,
            command=self.stop_video
        )
        stop_button.pack(side=tk.LEFT, padx=5)
        
        # 窗口关闭事件处理
        def on_close():
            self.stop_video()
            video_window.destroy()
        
        video_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 保存窗口引用
        self.video_window = video_window
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 创建播放/暂停按钮
        self.play_pause_button = tk.Button(
            control_frame,
            text="暂停",
            command=self.toggle_play_pause,
            font=("SimHei", 10),
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        
        # 创建停止按钮
        self.stop_button = tk.Button(
            control_frame,
            text="停止",
            command=self.stop_video,
            font=("SimHei", 10),
            bg="#F44336",
            fg="white",
            padx=10,
            pady=5
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 初始化视频状态变量
        self.current_video = None
        self.cap = None
        self.video_frame_id = None
        self.is_playing = True
        
        # 直接在Tkinter窗口中播放视频（使用模拟视频）
        self._play_video_in_window(video_window)
        
        # 30秒后自动关闭窗口
        self.root.after(30000, lambda: self._cleanup_video_resources(video_window))
        
    def _find_and_play_video(self, video_window):
        """已移除搜索视频功能，直接使用Tkinter窗口播放模拟视频"""
        pass  # 此方法已不再使用
    
    def _play_video_in_window(self, video_window):
        """在Tkinter窗口中使用OpenCV播放实际视频"""
        try:
            import cv2
            from PIL import Image, ImageTk
            import os
            import random
            
            # 更新状态标签
            def update_status_label(text="正在准备视频..."):
                try:
                    if hasattr(self, 'video_status_label') and self.video_status_label.winfo_exists():
                        self.video_status_label.config(text=text)
                except (tk.TclError, AttributeError):
                    pass
            
            self.root.after(0, lambda: update_status_label("正在准备视频..."))
            
            # 查找视频文件
            def find_video_file():
                # 支持的视频格式
                video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
                video_files = []
                
                # 1. 尝试项目中的Video文件夹
                project_video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Video')
                if os.path.exists(project_video_path):
                    print(f"在项目Video文件夹中搜索: {project_video_path}")
                    for root, dirs, files in os.walk(project_video_path):
                        for file in files:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in video_extensions:
                                video_path = os.path.join(root, file)
                                video_files.append(video_path)
                
                # 2. 如果找不到，尝试用户视频文件夹
                if not video_files:
                    user_videos_path = os.path.join(os.path.expanduser('~'), 'Videos')
                    if os.path.exists(user_videos_path):
                        print(f"在用户视频文件夹中搜索: {user_videos_path}")
                        for root, dirs, files in os.walk(user_videos_path):
                            for file in files:
                                ext = os.path.splitext(file)[1].lower()
                                if ext in video_extensions:
                                    video_path = os.path.join(root, file)
                                    video_files.append(video_path)
                                    # 限制搜索数量，避免查找太多文件
                                    if len(video_files) >= 10:
                                        break
                
                # 3. 如果找不到，尝试当前目录
                if not video_files:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    print(f"在当前目录中搜索: {current_dir}")
                    for file in os.listdir(current_dir):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in video_extensions:
                            video_path = os.path.join(current_dir, file)
                            video_files.append(video_path)
                
                # 随机选择一个视频文件
                if video_files:
                    selected_video = random.choice(video_files)
                    print(f"选择播放视频: {selected_video}")
                    return selected_video
                
                return None
            
            # 获取视频文件路径
            video_path = find_video_file()
            
            # 保存视频路径作为实例属性
            self.video_path = video_path
            
            if not video_path:
                self.root.after(0, lambda: update_status_label("未找到可用的视频文件"))
                print("未找到可用的视频文件")
                return
            
            # 更新状态
            self.root.after(0, lambda: update_status_label(f"正在播放: {os.path.basename(video_path)}"))
            
            # 创建视频捕获对象
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                self.root.after(0, lambda: update_status_label("无法打开视频文件"))
                print(f"无法打开视频文件: {video_path}")
                return
            
            # 获取视频信息
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # 默认帧率
            
            delay = int(1000 / fps)  # 帧延迟（毫秒）
            
            # 视频帧显示函数
            def show_frame():
                if not hasattr(self, 'cap') or not self.cap or not hasattr(self, 'is_playing'):
                    return
                
                if not self.is_playing:
                    return
                
                # 检查窗口是否存在
                if not video_window.winfo_exists():
                    # 窗口已关闭，释放资源
                    if hasattr(self, 'cap') and self.cap:
                        self.cap.release()
                        self.cap = None
                    return
                
                # 获取Canvas尺寸
                try:
                    canvas_width = self.video_canvas.winfo_width()
                    canvas_height = self.video_canvas.winfo_height()
                except:
                    return
                
                if canvas_width < 10 or canvas_height < 10:
                    # Canvas还没准备好，稍后重试
                    video_window.after(100, show_frame)
                    return
                
                # 读取一帧视频
                ret, frame = self.cap.read()
                
                if not ret:
                    # 视频播放完毕，重新开始
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        # 仍然无法读取，可能视频已损坏
                        self.root.after(0, lambda: update_status_label("视频播放出错"))
                        if hasattr(self, 'cap') and self.cap:
                            self.cap.release()
                            self.cap = None
                        return
                
                # 转换颜色格式（BGR -> RGB）
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 计算调整后的尺寸，保持宽高比
                video_height, video_width = rgb_frame.shape[:2]
                aspect_ratio = video_width / video_height
                
                if canvas_width / canvas_height > aspect_ratio:
                    # Canvas更宽，以高度为准
                    new_height = canvas_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    # Canvas更高，以宽度为准
                    new_width = canvas_width
                    new_height = int(new_width / aspect_ratio)
                
                # 调整图像大小
                resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                
                # 转换为PIL图像
                pil_image = Image.fromarray(resized_frame)
                
                # 转换为Tkinter可用的图像
                tk_image = ImageTk.PhotoImage(image=pil_image)
                
                # 清除Canvas并显示新帧
                try:
                    self.video_canvas.delete('all')
                    # 居中显示视频
                    x_offset = (canvas_width - new_width) // 2
                    y_offset = (canvas_height - new_height) // 2
                    self.video_frame_id = self.video_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=tk_image)
                    
                    # 保存引用，防止被垃圾回收
                    self.video_canvas.current_image = tk_image
                except:
                    return
                
                # 继续播放下一帧
                if video_window.winfo_exists() and self.is_playing:
                    video_window.after(delay, show_frame)
            
            # 开始播放视频
            show_frame()
            
        except ImportError:
            error_msg = "缺少必要的库。请安装opencv-python和pillow。"
            print(error_msg)
            self.root.after(0, lambda: update_status_label(error_msg))
        except Exception as e:
            error_msg = f"播放视频时出错: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: update_status_label(error_msg))
            # 确保释放资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                except:
                    pass
    
    def _fallback_play_video(self):
        """备用播放方法（已不再需要）"""
        print("备用播放方法已调用")
    
    def _get_dynamic_background_color(self, frame):
        """获取动态背景颜色"""
        # 创建一个渐变的背景色
        r = int(30 + 20 * math.sin(frame * 0.05))
        g = int(30 + 20 * math.sin(frame * 0.05 + 2))
        b = int(30 + 20 * math.sin(frame * 0.05 + 4))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _draw_dynamic_elements(self, width, height, frame):
        """绘制动态元素模拟视频内容"""
        # 绘制一些动态形状
        center_x = width // 2
        center_y = height // 2
        
        # 绘制旋转的圆形
        radius = 50 + 20 * math.sin(frame * 0.03)
        circle_x = center_x + 100 * math.cos(frame * 0.02)
        circle_y = center_y + 100 * math.sin(frame * 0.02)
        self.video_canvas.create_oval(
            circle_x - radius, circle_y - radius,
            circle_x + radius, circle_y + radius,
            fill="#FF5722", outline="", stipple="gray50"
        )
        
        # 绘制移动的矩形
        rect_size = 40 + 10 * math.cos(frame * 0.04)
        rect_x = center_x - 120 + 50 * math.sin(frame * 0.03)
        rect_y = center_y - 30 + 40 * math.cos(frame * 0.03)
        self.video_canvas.create_rectangle(
            rect_x, rect_y,
            rect_x + rect_size, rect_y + rect_size,
            fill="#2196F3", outline="", stipple="gray50"
        )
        
        # 绘制一些装饰性元素
        for i in range(10):
            x = int(50 + (width - 100) * i / 9)
            y = center_y + 50 * math.sin(frame * 0.05 + i)
            self.video_canvas.create_line(x, y - 10, x, y + 10, fill="white", width=2)
        
        # 添加文字说明
        self.video_canvas.create_text(
            width // 2, height - 30,
            text="Tkinter视频播放演示",
            fill="white",
            font=("SimHei", 12, "bold")
        )
    
    def toggle_play_pause(self):
        """切换视频的播放/暂停状态"""
        try:
            self.is_playing = not self.is_playing
            
            if hasattr(self, 'play_pause_button'):
                try:
                    if self.is_playing:
                        self.play_pause_button.config(text="暂停", bg="#4CAF50")
                        # 找到当前窗口并重新开始播放循环
                        for window in self.root.winfo_children():
                            if isinstance(window, tk.Toplevel) and "视频播放" in window.title():
                                self._play_video_in_window(window)
                                break
                    else:
                        self.play_pause_button.config(text="播放", bg="#2196F3")
                except (tk.TclError, AttributeError):
                    pass
            
            # 更新状态标签
            if hasattr(self, 'video_status_label'):
                try:
                    status = "播放中" if self.is_playing else "已暂停"
                    # 安全地构建状态文本，避免在属性不存在时出错
                    video_info = ""
                    if hasattr(self, 'video_path') and self.video_path:
                        try:
                            video_info = f" - {os.path.basename(self.video_path)}"
                        except:
                            video_info = " - 视频播放"
                    self.video_status_label.config(text=f"{status}{video_info}")
                except (tk.TclError, AttributeError):
                    pass
                    
        except Exception as e:
            print(f"切换播放状态出错: {e}")
    
    def stop_video(self):
        """停止视频播放并释放资源"""
        try:
            # 停止播放
            self.is_playing = False
            
            # 释放视频捕获资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                    print("OpenCV视频资源已成功释放")
                except Exception as release_error:
                    print(f"释放视频捕获资源时出错: {release_error}")
                finally:
                    # 确保删除属性
                    if hasattr(self, 'cap'):
                        delattr(self, 'cap')
            
            # 清除Canvas
            if hasattr(self, 'video_canvas'):
                try:
                    # 首先检查canvas是否仍然存在
                    if hasattr(self.video_canvas, 'winfo_exists') and self.video_canvas.winfo_exists():
                        if hasattr(self, 'video_frame_id'):
                            self.video_canvas.delete(self.video_frame_id)
                            self.video_frame_id = None
                        # 清除所有内容
                        self.video_canvas.delete('all')
                        # 移除当前图像引用
                        if hasattr(self.video_canvas, 'current_image'):
                            delattr(self.video_canvas, 'current_image')
                except Exception as canvas_error:
                    print(f"清除Canvas时出错: {canvas_error}")
            
            # 更新按钮状态
            if hasattr(self, 'play_pause_button'):
                try:
                    self.play_pause_button.config(text="播放", bg="#2196F3")
                except (tk.TclError, AttributeError):
                    pass
                    
            # 更新状态标签
            if hasattr(self, 'video_status_label'):
                try:
                    self.video_status_label.config(text="视频已停止")
                except (tk.TclError, AttributeError):
                    pass
                    
        except Exception as e:
            print(f"停止视频播放时出错: {e}")
            # 无论如何都尝试释放关键资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                if hasattr(self, 'cap'):
                    delattr(self, 'cap')
    
    def _cleanup_video_resources(self, video_window):
        """清理视频播放资源并关闭窗口"""
        try:
            # 停止视频播放
            self.stop_video()
            
            # 关闭窗口
            try:
                if video_window and video_window.winfo_exists():
                    video_window.destroy()
                    print("视频窗口已关闭")
            except Exception as window_error:
                print(f"关闭视频窗口时出错: {window_error}")
                
            # 清理相关属性
            cleanup_attrs = ['video_window', 'video_canvas', 'video_status_label', 
                           'play_pause_button', 'stop_button', 'video_frame_id', 'video_path']
            for attr in cleanup_attrs:
                if hasattr(self, attr):
                    try:
                        delattr(self, attr)
                    except:
                        pass
                        
        except Exception as e:
            print(f"清理视频资源时出错: {e}")
            # 无论如何都尝试释放关键资源
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                if hasattr(self, 'cap'):
                    delattr(self, 'cap')
        except:
            pass
    
    def _animate_warning_text(self, label):
        """给警告文字添加动画效果"""
        colors = ["#FFEB3B", "#FF5722", "#E91E63", "#9C27B0"]
        color_index = 0
        
        def update_color():
            nonlocal color_index
            label.config(fg=colors[color_index])
            color_index = (color_index + 1) % len(colors)
            self.root.after(300, update_color)
        
        # 启动动画
        update_color()
    
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
        self.tray_menu.add_command(label="与大白鹅聊天", command=self.open_chat_window)
        self.tray_menu.add_command(label="更新AI对话设置", command=self._show_api_key_dialog)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label="退出", command=self.quit_app)
    
    def open_chat_window(self):
        """打开与大白鹅的聊天窗口"""
        # 获取当前鼠标位置作为聊天窗口的位置
        x, y = win32gui.GetCursorPos()
        chat_window = ChatWindow(self.root, self.ai_manager, (x, y))
        self.chat_windows.append(chat_window)
        print("打开了大白鹅聊天窗口")
    
    def cleanup_chat_windows(self):
        """清理已关闭的聊天窗口"""
        # 这个函数会在清理线程中调用
    
    def summon_goose(self, event=None):
        # 召唤一只大白鹅
        goose = GooseAnimation(self.root, self)
        self.active_geese.append(goose)
        print("成功召唤一只大白鹅！")
    
    def cleanup_finished_geese(self):
        # 清理已停止的鹅动画和聊天窗口
        while True:
            time.sleep(5)
            # 清理已停止的鹅动画
            active_geese = []
            for goose in self.active_geese:
                if hasattr(goose, 'running') and goose.running:
                    active_geese.append(goose)
            self.active_geese = active_geese
            
            # 清理聊天窗口引用（简化处理）
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
    
    def _check_api_key(self):
        """检查并设置API密钥"""
        # 尝试从配置文件读取API密钥
        config_path = os.path.join(os.path.expanduser('~'), '.goose_ai_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'api_key' in config and config['api_key']:
                        self.ai_manager.api_key = config['api_key']
                        print("已加载保存的API密钥")
                        return
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        
        # 显示设置API密钥的对话框
        self._show_api_key_dialog()
        
    def _show_api_key_dialog(self):
        """显示设置API密钥的对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置在线AI对话")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 创建说明标签
        label = tk.Label(dialog, text="请输入OpenAI API密钥以启用在线AI对话功能：", font=('SimHei', 10))
        label.pack(pady=20)
        
        # 创建输入框
        api_key_var = tk.StringVar(value=self.ai_manager.api_key)
        api_key_entry = tk.Entry(dialog, textvariable=api_key_var, width=50, show="*")
        api_key_entry.pack(pady=10)
        api_key_entry.focus_set()
        
        # 创建按钮框架
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def save_api_key():
            key = api_key_var.get().strip()
            if key and key.startswith("sk-"):
                self.ai_manager.api_key = key
                # 保存到配置文件
                config_path = os.path.join(os.path.expanduser('~'), '.goose_ai_config.json')
                try:
                    with open(config_path, 'w') as f:
                        json.dump({'api_key': key}, f)
                    print("API密钥已保存")
                except Exception as e:
                    print(f"保存API密钥失败: {e}")
                dialog.destroy()
            else:
                messagebox.showerror("错误", "请输入有效的OpenAI API密钥（以sk-开头）")
        
        def skip_api_key():
            self.ai_manager.use_online_ai = False
            dialog.destroy()
        
        # 创建按钮
        save_button = tk.Button(button_frame, text="保存并启用", command=save_api_key, bg='#4CAF50', fg='white')
        save_button.pack(side=tk.LEFT, padx=10)
        
        skip_button = tk.Button(button_frame, text="跳过（使用本地回复）", command=skip_api_key, bg='#FF9800', fg='white')
        skip_button.pack(side=tk.LEFT, padx=10)
        
        # 绑定Enter键
        dialog.bind('<Return>', lambda event: save_api_key())
        dialog.bind('<Escape>', lambda event: skip_api_key())
        
        # 设置对话框模态
        dialog.grab_set()
        self.root.wait_window(dialog)

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
        
    def test_video_playback(self):
        """测试视频播放功能的方法，可以通过控制台调用"""
        print("手动触发视频播放测试...")
        self._show_folder_video_window()

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
    
    # 测试视频播放功能（添加这一行来测试Video文件夹的视频播放）
    root.after(2000, app.test_video_playback)
    
    # 启动主循环
    root.mainloop()