import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import os
import sys
import threading
import time
import random
import math
import ctypes
from datetime import datetime

# استيراد pynput للمراقبة العالمية
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# محاولة استيراد مكتبات المحاكاة (قد تتطلب تثبيت إضافي أو تعمل فقط على ويندوز مع pyautogui)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # تقليل التأخير لتحسين الاستجابة
    pyautogui.PAUSE = 0.001
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("تنبيه: لم يتم العثور على pyautogui. محاكاة الماوس والكيبورد لن تعمل خارج النافذة.")

class GlobalInputHandler:
    def __init__(self, app):
        self.app = app
        self.key_map = {} # Maps physical key to KeyButton or action_id
        self.pressed_keys = set()
        self.keyboard_listener = None
        self.mouse_listener = None
        self.running = False

    def start(self):
        if not PYNPUT_AVAILABLE: return
        self.running = True
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.keyboard_listener.start()

        # Start mouse listener for Aim Mode
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move)
        self.mouse_listener.start()

    def on_mouse_move(self, x, y):
        if not self.app.layout_active or not self.app.mouse_locked: return

        # Capture deltas for Aim Mode
        # In a real app we'd compare with center and reset cursor
        # Here we simulate camera movement by clicking and dragging
        for aim in self.app.aim_controls:
            aim.trigger_aim(x, y)

    def stop(self):
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def on_press(self, key):
        if not self.app.layout_active: return
        try:
            k = self.get_key_str(key)
            if k in self.pressed_keys: return # Ignore repeated events
            self.pressed_keys.add(k)

            # Check D-Pad bindings
            for dpad in self.app.dpads:
                bindings = dpad.config_data.get('bindings', {})
                for direction, bound_key in bindings.items():
                    if bound_key.lower() == k:
                        dpad.on_key_press(direction)
                        return

            if k in self.key_map:
                # Trigger action
                self.app.handle_action(self.key_map[k])

            # Check Repeated Tap bindings
            for tap in self.app.repeated_taps:
                if tap.config_data.get('binding', '').lower() == k:
                    tap.start_tap()
        except Exception as e:
            print(f"Error in global on_press: {e}")

    def on_release(self, key):
        if not self.app.layout_active: return
        try:
            k = self.get_key_str(key)
            if k in self.pressed_keys:
                self.pressed_keys.remove(k)

            # Check D-Pad bindings
            for dpad in self.app.dpads:
                bindings = dpad.config_data.get('bindings', {})
                for direction, bound_key in bindings.items():
                    if bound_key.lower() == k:
                        dpad.on_key_release(direction)
                        return

            # Check Repeated Tap bindings
            for tap in self.app.repeated_taps:
                if tap.config_data.get('binding', '').lower() == k:
                    tap.stop_tap()
        except Exception as e:
            print(f"Error in global on_release: {e}")

    def get_key_str(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            return str(key).replace('Key.', '')
        except:
            return str(key)

class DPadControl(tk.Canvas):
    def __init__(self, parent, config, app, **kwargs):
        super().__init__(parent, highlightthickness=0, bg="#222222", **kwargs)
        self.config_data = config
        self.app = app
        self.center_x = config.get('w', 120) // 2
        self.center_y = config.get('h', 120) // 2
        self.active_directions = set()
        self.move_thread = None
        self.running = False
        self.draw_dpad()
        self.bind("<B1-Motion>", self.on_drag)

    def draw_dpad(self):
        self.delete("all")
        w = self.winfo_width() if self.winfo_width() > 1 else self.config_data.get('w', 120)
        h = self.winfo_height() if self.winfo_height() > 1 else self.config_data.get('h', 120)

        # Outer ring
        self.create_oval(5, 5, w-5, h-5, outline="#ffffff", width=2, fill="#333333")
        self.create_oval(w//4, h//4, 3*w//4, 3*h//4, outline="#666", width=1)

        # Directions
        binds = self.config_data.get('bindings', {})
        self.create_text(w//2, 20, text=binds.get('up', 'W').upper(), fill="white", font=("Segoe UI", 10, "bold"))
        self.create_text(w//2, h-20, text=binds.get('down', 'S').upper(), fill="white", font=("Segoe UI", 10, "bold"))
        self.create_text(20, h//2, text=binds.get('left', 'A').upper(), fill="white", font=("Segoe UI", 10, "bold"))
        self.create_text(w-20, h//2, text=binds.get('right', 'D').upper(), fill="white", font=("Segoe UI", 10, "bold"))

        self.create_text(w//2, h//2, text="MOVE", fill="#00ff00", font=("Segoe UI", 8, "bold"))

    def on_drag(self, event):
        if self.app.edit_mode:
            dx = event.x - self.config_data.get('w', 120)//2
            dy = event.y - self.config_data.get('h', 120)//2
            new_x = self.winfo_x() + dx
            new_y = self.winfo_y() + dy
            self.place(x=new_x, y=new_y)
            self.config_data['x'] = new_x
            self.config_data['y'] = new_y

    def on_key_press(self, direction):
        self.active_directions.add(direction)
        if not self.running:
            self.start_movement()

    def on_key_release(self, direction):
        if direction in self.active_directions:
            self.active_directions.remove(direction)
        if not self.active_directions:
            self.stop_movement()

    def start_movement(self):
        self.running = True
        # Get coordinates in main thread
        try:
            self.root_coords = {
                'root_x': self.app.root.winfo_rootx(),
                'root_y': self.app.root.winfo_rooty(),
                'rel_x': self.winfo_x(),
                'rel_y': self.winfo_y(),
                'w': self.winfo_width(),
                'h': self.winfo_height()
            }
        except:
            self.root_coords = None

        self.move_thread = threading.Thread(target=self.movement_loop, daemon=True)
        self.move_thread.start()

    def stop_movement(self):
        self.running = False
        if PYAUTOGUI_AVAILABLE:
            pyautogui.mouseUp()

    def movement_loop(self):
        if not PYAUTOGUI_AVAILABLE or not hasattr(self, 'root_coords') or not self.root_coords:
            return

        root_x = self.root_coords['root_x']
        root_y = self.root_coords['root_y']
        rel_x = self.root_coords['rel_x']
        rel_y = self.root_coords['rel_y']
        w = self.root_coords['w']
        h = self.root_coords['h']

        abs_center_x = root_x + rel_x + w // 2
        abs_center_y = root_y + rel_y + h // 2

        pyautogui.mouseDown(abs_center_x, abs_center_y)

        while self.running:
            target_x = abs_center_x
            target_y = abs_center_y
            offset = 40

            if 'up' in self.active_directions: target_y -= offset
            if 'down' in self.active_directions: target_y += offset
            if 'left' in self.active_directions: target_x -= offset
            if 'right' in self.active_directions: target_x += offset

            pyautogui.moveTo(target_x, target_y, duration=0.05)
            time.sleep(0.01)

        pyautogui.mouseUp()

class AimModeControl(tk.Canvas):
    def __init__(self, parent, config, app, **kwargs):
        super().__init__(parent, highlightthickness=0, bg="#1a1a1a", **kwargs)
        self.config_data = config
        self.app = app
        self.draw_aim()

    def draw_aim(self):
        self.delete("all")
        w = self.config_data.get('w', 100)
        h = self.config_data.get('h', 100)
        self.create_oval(5, 5, w-5, h-5, outline="cyan", width=2, dash=(5, 5))
        self.create_line(w//2, 10, w//2, h-10, fill="cyan", width=1)
        self.create_line(10, h//2, w-10, h//2, fill="cyan", width=1)
        self.create_text(w//2, h//2 + 20, text="AIM", fill="cyan", font=("Segoe UI", 10, "bold"))
        self.create_text(w//2, h//2 - 20, text="[F2]", fill="white", font=("Segoe UI", 8))

    def trigger_aim(self, x, y):
        if not PYAUTOGUI_AVAILABLE: return

        # Use cached coordinates if available
        if not hasattr(self, 'last_aim_center'):
            try:
                root_x = self.app.root.winfo_rootx()
                root_y = self.app.root.winfo_rooty()
                rel_x = self.winfo_x()
                rel_y = self.winfo_y()
                w = self.winfo_width()
                h = self.winfo_height()
                self.last_aim_center = (root_x + rel_x + w // 2, root_y + rel_y + h // 2)
            except:
                return

        center_x, center_y = self.last_aim_center

        dx = x - center_x
        dy = y - center_y

        # Sensitivity and threshold
        threshold = 2
        if abs(dx) > threshold or abs(dy) > threshold:
            # Reset mouse position immediately to prevent cursor escaping
            pyautogui.moveTo(center_x, center_y)

            # Rate limiting / Thread management: only one aim swipe at a time
            if not hasattr(self, 'aiming') or not self.aiming:
                self.aiming = True
                def do_aim_movement():
                    try:
                        # For smooth camera rotation in emulators, we simulate a drag
                        pyautogui.mouseDown(center_x, center_y)
                        pyautogui.moveRel(dx * self.app.settings["sensitivity"] * 2,
                                          dy * self.app.settings["sensitivity"] * 2,
                                          duration=0.01)
                        pyautogui.mouseUp()
                    finally:
                        self.aiming = False

                threading.Thread(target=do_aim_movement, daemon=True).start()

class RepeatedTapControl(tk.Canvas):
    def __init__(self, parent, config, app, **kwargs):
        super().__init__(parent, highlightthickness=0, bg="#4a148c", **kwargs)
        self.config_data = config
        self.app = app
        self.running = False
        self.draw_repeated()
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)

    def draw_repeated(self):
        self.delete("all")
        w = self.config_data.get('w', 60)
        h = self.config_data.get('h', 60)
        self.create_oval(5, 5, w-5, h-5, fill="#7b1fa2", outline="white")
        label = self.config_data.get('binding', 'Auto').upper()
        self.create_text(w//2, h//2, text=label, fill="white", font=("Arial", 10, "bold"))

    def on_press(self, event):
        if self.app.edit_mode:
            self.app.selected_control = self
            self.config(highlightbackground="red", highlightthickness=2)

    def on_drag(self, event):
        if self.app.edit_mode:
            self.place(x=self.winfo_x() + event.x - 30, y=self.winfo_y() + event.y - 30)

    def start_tap(self):
        self.running = True
        # Cache coords in main thread
        try:
            self.root_coords = {
                'root_x': self.app.root.winfo_rootx(),
                'root_y': self.app.root.winfo_rooty(),
                'rel_x': self.winfo_x(),
                'rel_y': self.winfo_y(),
                'w': self.winfo_width(),
                'h': self.winfo_height()
            }
        except:
            self.root_coords = None
        threading.Thread(target=self.tap_loop, daemon=True).start()

    def stop_tap(self):
        self.running = False

    def tap_loop(self):
        if not PYAUTOGUI_AVAILABLE or not hasattr(self, 'root_coords') or not self.root_coords:
            return

        root_x = self.root_coords['root_x']
        root_y = self.root_coords['root_y']
        rel_x = self.root_coords['rel_x']
        rel_y = self.root_coords['rel_y']
        w = self.root_coords['w']
        h = self.root_coords['h']

        abs_x = root_x + rel_x + w // 2
        abs_y = root_y + rel_y + h // 2

        delay = self.config_data.get('delay', 0.1)
        while self.running:
            pyautogui.click(abs_x, abs_y)
            time.sleep(delay)

class KeyButton(tk.Canvas):
    def __init__(self, parent, key_config, app, command=None, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.key_config = key_config
        self.app = app
        self.command = command
        self.is_pressed = False
        self.base_color = key_config.get('color', '#333333')
        self.active_color = key_config.get('active_color', '#00ff00')
        self.text_color = key_config.get('text_color', '#ffffff')
        
        self.draw_key()
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        # دعم السحب والإفلات في وضع التعديل
        self.bind("<B1-Motion>", self.on_drag)
        self.drag_start_x = 0
        self.drag_start_y = 0

    def draw_key(self):
        self.delete("all")
        w = self.winfo_width() if self.winfo_width() > 1 else self.key_config.get('w', 50)
        h = self.winfo_height() if self.winfo_height() > 1 else self.key_config.get('h', 50)
        if w < 2 or h < 2: return
        
        radius = 10
        # استخدام لون شفاف جزئياً في التخطيط
        color = self.active_color if self.is_pressed else self.base_color
        
        # خلفية الزر
        self.create_rounded_rect(2, 2, w-2, h-2, radius, fill=color, outline="#ffffff", width=1)
        
        # النص (الاختصار)
        binding = self.key_config.get('binding', '').upper()
        if binding:
            self.create_text(w//2, h//2, text=binding, fill=self.text_color, font=("Segoe UI", 12, "bold"))
        else:
            label = self.key_config.get('label', '?')
            self.create_text(w//2, h//2, text=label, fill=self.text_color, font=("Segoe UI", 9))
        
        # مؤشر الوضع
        if self.key_config.get('is_special'):
            self.create_oval(2, 2, 8, 8, fill="red")

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x2-r, y1, x2, y1+r, x2, y2-r, x2-r, y2, x1+r, y2, x1, y2-r, x1, y1+r]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_press(self, event):
        self.is_pressed = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.draw_key()

        if self.app.edit_mode:
            # Click-to-Bind logic
            self.app.selected_control = self
            self.config(highlightbackground="red", highlightthickness=2)
            print(f"Selected control for binding: {self.key_config['id']}")
        elif self.command:
            self.command(self.key_config['action'])

    def on_release(self, event):
        self.is_pressed = False
        self.draw_key()
        if app.edit_mode:
            # Check if we should keep it highlighted or not
            pass

    def on_drag(self, event):
        if app.edit_mode:
            # منطق تحريك الزر (مبسط)
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            # في تطبيق حقيقي نحتاج لتحديث إحداثيات الزر في الـ layout
            # هنا مجرد مثال بصري
            self.move(0, dx, dy) 
            self.drag_start_x = event.x
            self.drag_start_y = event.y

class KeyboardMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Mapper Pro - SAM Edition")
        self.root.geometry("1000x700")
        
        # المتغيرات العامة
        self.edit_mode = False
        self.transparency_enabled = False
        self.transparency_level = 1.0 # 0.01 to 1.0
        self.mouse_locked = False
        self.layout_active = True
        self.theme = "dark"
        self.keys = []
        self.dpads = []
        self.aim_controls = []
        self.repeated_taps = []
        self.selected_control = None
        self.input_handler = GlobalInputHandler(self)
        self.recording = False
        self.recorded_actions = []
        
        # إعدادات الافتراضية
        self.settings = {
            "sensitivity": 1.0,
            "touch_feedback": True,
            "grid_snap": 10,
            "key_size": 50
        }
        
        self.setup_ui()
        self.load_default_layout()
        self.bind_hotkeys()
        
        # حلقة التحديث للرسوم المتحركة
        self.animate_loop()

    def setup_ui(self):
        # الإطار الرئيسي
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # الشريط الجانبي للإعدادات
        self.sidebar = tk.Frame(self.main_frame, width=250, bg="#2d2d2d")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # منطقة الرسم (الكيبورد)
        self.canvas_area = tk.Frame(self.main_frame, bg="#121212")
        self.canvas_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.keyboard_canvas = tk.Canvas(self.canvas_area, bg="#121212", highlightthickness=0)
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.build_sidebar()

    def build_sidebar(self):
        # عنوان
        lbl_title = tk.Label(self.sidebar, text="الإعدادات المتقدمة", bg="#2d2d2d", fg="#ffffff", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=10)
        
        # تبويبات
        self.notebook = ttk.Notebook(self.sidebar)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # تاب التحكم
        tab_control = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_control, text="تحكم")
        
        btn_edit = tk.Button(tab_control, text="وضع التعديل (Ctrl+E)", command=self.toggle_edit_mode, bg="#444", fg="white")
        btn_edit.pack(fill=tk.X, pady=5)
        
        btn_trans = tk.Button(tab_control, text="تفعيل الشفافية (F3)", command=self.toggle_transparency, bg="#444", fg="white")
        btn_trans.pack(fill=tk.X, pady=5)
        
        self.scale_trans = tk.Scale(tab_control, from_=1, to=100, orient=tk.HORIZONTAL, label="الشفافية %", bg="#2d2d2d", fg="white", command=self.update_transparency)
        self.scale_trans.set(100)
        self.scale_trans.pack(fill=tk.X, pady=5)
        
        # تاب التسجيل
        tab_recording = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_recording, text="تسجيل")
        
        btn_start_record = tk.Button(tab_recording, text="بدء التسجيل", command=self.start_recording, 
                                      bg="#444", fg="#00ff00", font=("Arial", 10, "bold"))
        btn_start_record.pack(fill=tk.X, pady=5)
        
        btn_stop_record = tk.Button(tab_recording, text="إيقاف التسجيل", command=self.stop_recording,
                                     bg="#444", fg="#ff0000", font=("Arial", 10, "bold"))
        btn_stop_record.pack(fill=tk.X, pady=5)
        
        btn_save_record = tk.Button(tab_recording, text="حفظ التسجيل", command=self.save_recording, bg="#444", fg="white")
        btn_save_record.pack(fill=tk.X, pady=5)
        
        btn_play_record = tk.Button(tab_recording, text="تشغيل التسجيل", command=self.play_recording, bg="#444", fg="white")
        btn_play_record.pack(fill=tk.X, pady=5)
        
        self.lbl_record_status = tk.Label(tab_recording, text="الحالة: متوقف", bg="#2d2d2d", fg="white")
        self.lbl_record_status.pack(pady=10)
        
        # تاب الأداء
        tab_performance = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_performance, text="أداء")
        
        lbl_fps = tk.Label(tab_performance, text="معدل الإطارات (FPS):", bg="#2d2d2d", fg="white")
        lbl_fps.pack(pady=(10,5))
        self.scale_fps = tk.Scale(tab_performance, from_=15, to=144, orient=tk.HORIZONTAL,
                                   bg="#2d2d2d", fg="white")
        self.scale_fps.set(60)
        self.scale_fps.pack(fill=tk.X, pady=5)
        
        self.chk_vsync = tk.BooleanVar(value=False)
        chk_vsync = tk.Checkbutton(tab_performance, text="V-Sync", variable=self.chk_vsync,
                                    bg="#2d2d2d", fg="white", selectcolor="#2d2d2d")
        chk_vsync.pack(pady=5)
        
        self.chk_hw_accel = tk.BooleanVar(value=True)
        chk_hw_accel = tk.Checkbutton(tab_performance, text="التسريع العتادي", variable=self.chk_hw_accel,
                                       bg="#2d2d2d", fg="white", selectcolor="#2d2d2d")
        chk_hw_accel.pack(pady=5)
        
        lbl_quality = tk.Label(tab_performance, text="جودة الرسم:", bg="#2d2d2d", fg="white")
        lbl_quality.pack(pady=(10,5))
        quality_frame = tk.Frame(tab_performance, bg="#2d2d2d")
        quality_frame.pack(fill=tk.X, pady=5)
        
        for i, q in enumerate(["منخفضة", "متوسطة", "عالية"]):
            rb = tk.Radiobutton(quality_frame, text=q, value=i, bg="#2d2d2d", fg="white",
                               selectcolor="#2d2d2d", activebackground="#2d2d2d")
            rb.grid(row=0, column=i, padx=10)

        # تاب التخطيط
        tab_layout = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_layout, text="تخطيط")

        btn_add_key = tk.Button(tab_layout, text="إضافة زر لمس", command=self.add_touch_key, bg="#444", fg="white")
        btn_add_key.pack(fill=tk.X, pady=5)

        btn_add_dpad = tk.Button(tab_layout, text="إضافة D-Pad", command=self.add_dpad, bg="#444", fg="white")
        btn_add_dpad.pack(fill=tk.X, pady=5)

        btn_add_aim = tk.Button(tab_layout, text="إضافة منطقة تصويب", command=self.add_aim_area, bg="#444", fg="white")
        btn_add_aim.pack(fill=tk.X, pady=5)

        btn_add_tap = tk.Button(tab_layout, text="إضافة نقر متكرر", command=self.add_repeated_tap, bg="#444", fg="white")
        btn_add_tap.pack(fill=tk.X, pady=5)

        tk.Label(tab_layout, text="قوالب جاهزة", bg="#2d2d2d", fg="#aaa", font=("Arial", 10)).pack(pady=(15, 5))

        btn_fps = tk.Button(tab_layout, text="تخطيط ألعاب FPS", command=self.load_fps_preset, bg="#333", fg="#00ff00")
        btn_fps.pack(fill=tk.X, pady=2)

        btn_moba = tk.Button(tab_layout, text="تخطيط ألعاب MOBA", command=self.load_moba_preset, bg="#333", fg="#00ffff")
        btn_moba.pack(fill=tk.X, pady=2)

    def load_fps_preset(self):
        self.new_layout_silent()
        # D-Pad
        self.add_dpad_at(50, 450)
        # Aim Mode
        self.add_aim_area_at(600, 200)
        # Fire button
        self.add_touch_key_at(800, 500, "FIRE", "left", "L-Click")
        # Jump
        self.add_touch_key_at(900, 400, "JUMP", "space", "SPACE")
        print("FPS Preset Loaded")

    def load_moba_preset(self):
        self.new_layout_silent()
        # D-Pad
        self.add_dpad_at(50, 450)
        # Skills
        self.add_touch_key_at(750, 550, "S1", "q", "Q")
        self.add_touch_key_at(820, 480, "S2", "w", "W")
        self.add_touch_key_at(900, 450, "S3", "e", "E")
        # Attack
        self.add_touch_key_at(850, 580, "ATK", "space", "SPACE")
        print("MOBA Preset Loaded")

    def new_layout_silent(self):
        for widget in self.keyboard_canvas.winfo_children():
            widget.destroy()
        self.keys = []
        self.dpads = []
        self.aim_controls = []
        self.repeated_taps = []

    def add_dpad_at(self, x, y):
        config = {'id': f"dpad_{random.randint(100,999)}", 'bindings': {'up': 'w', 'down': 's', 'left': 'a', 'right': 'd'}, 'x': x, 'y': y, 'w': 120, 'h': 120}
        dpad = DPadControl(self.keyboard_canvas, config, self)
        dpad.place(x=x, y=y, width=120, height=120)
        self.dpads.append(dpad)

    def add_aim_area_at(self, x, y):
        config = {'id': f"aim_{random.randint(100,999)}", 'x': x, 'y': y, 'w': 200, 'h': 200}
        aim = AimModeControl(self.keyboard_canvas, config, self)
        aim.place(x=x, y=y, width=200, height=200)
        self.aim_controls.append(aim)

    def add_touch_key_at(self, x, y, label, binding, action):
        config = {'id': f"k_{random.randint(100,999)}", 'label': label, 'action': action, 'binding': binding, 'x': x, 'y': y, 'w': 60, 'h': 60, 'color': '#333333'}
        self.create_key_widget(config)

    def add_touch_key(self):
        config = {
            'id': f"key_{random.randint(1000, 9999)}",
            'label': "New",
            'action': f"action_{random.randint(1000, 9999)}",
            'binding': '',
            'x': 100, 'y': 100, 'w': 60, 'h': 60,
            'color': '#333333'
        }
        self.create_key_widget(config)

    def add_dpad(self):
        config = {
            'id': f"dpad_{random.randint(1000, 9999)}",
            'bindings': {'up': 'w', 'down': 's', 'left': 'a', 'right': 'd'},
            'x': 100, 'y': 300, 'w': 120, 'h': 120
        }
        dpad = DPadControl(self.keyboard_canvas, config, self)
        dpad.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.dpads.append(dpad)

    def add_aim_area(self):
        config = {
            'id': f"aim_{random.randint(1000, 9999)}",
            'x': 500, 'y': 200, 'w': 150, 'h': 150
        }
        aim = AimModeControl(self.keyboard_canvas, config, self)
        aim.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.aim_controls.append(aim)

    def add_repeated_tap(self):
        config = {
            'id': f"tap_{random.randint(1000, 9999)}",
            'binding': 'z',
            'delay': 0.05,
            'x': 300, 'y': 300, 'w': 60, 'h': 60
        }
        tap = RepeatedTapControl(self.keyboard_canvas, config, self)
        tap.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.repeated_taps.append(tap)

    def start_recording(self):
        """بدء تسجيل الإجراءات"""
        self.recording = True
        self.recorded_actions = []
        self.lbl_record_status.config(text="الحالة: جاري التسجيل...", fg="#00ff00")
        print("بدأ التسجيل")
    
    def stop_recording(self):
        """إيقاف تسجيل الإجراءات"""
        self.recording = False
        count = len(self.recorded_actions)
        self.lbl_record_status.config(text=f"الحالة: متوقف ({count} حدث)", fg="#ff0000")
        print(f"تم إيقاف التسجيل. عدد الأحداث: {count}")
    
    def save_recording(self):
        """حفظ التسجيل في ملف JSON"""
        if not self.recorded_actions:
            messagebox.showwarning("تحذير", "لا يوجد تسجيل لحفظه!")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".json", 
                                                 filetypes=[("JSON Files", "*.json")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.recorded_actions, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("نجاح", f"تم حفظ التسجيل في:\n{filename}")
    
    def play_recording(self):
        """تشغيل تسجيل محفوظ"""
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    actions = json.load(f)
                print(f"جاري تشغيل {len(actions)} حدث من {filename}")
                messagebox.showinfo("تشغيل", f"سيتم تشغيل {len(actions)} حدث")
                # هنا يمكن إضافة منطق التشغيل الفعلي
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
        tab_appearance = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_appearance, text="مظهر")
        
        themes = ["داكن", "فاتح", "أزرق", "أخضر", "برتقالي"]
        for t in themes:
            btn = tk.Button(tab_appearance, text=t, command=lambda x=t: self.change_theme(x))
            btn.pack(fill=tk.X, pady=2)
        
        # حجم المفاتيح
        lbl_size = tk.Label(tab_appearance, text="حجم المفاتيح:", bg="#2d2d2d", fg="white")
        lbl_size.pack(pady=(10,5))
        self.scale_key_size = tk.Scale(tab_appearance, from_=30, to=200, orient=tk.HORIZONTAL, 
                                        bg="#2d2d2d", fg="white", command=self.update_key_size)
        self.scale_key_size.set(50)
        self.scale_key_size.pack(fill=tk.X, pady=5)
        
        # الشبكة
        lbl_grid = tk.Label(tab_appearance, text="حجم الشبكة:", bg="#2d2d2d", fg="white")
        lbl_grid.pack(pady=(10,5))
        self.scale_grid = tk.Scale(tab_appearance, from_=5, to=50, orient=tk.HORIZONTAL,
                                    bg="#2d2d2d", fg="white", command=self.update_grid)
        self.scale_grid.set(10)
        self.scale_grid.pack(fill=tk.X, pady=5)

    def load_default_layout(self):
        # إنشاء مفاتيح افتراضية
        rows = 5
        cols = 10
        start_x, start_y = 50, 50
        gap = 10
        size = 60
        
        for r in range(rows):
            for c in range(cols):
                key_label = f"K{r}-{c}"
                config = {
                    'id': f"{r}_{c}",
                    'label': key_label,
                    'action': f"key_{r}_{c}",
                    'binding': '', # Physical key
                    'x': start_x + c * (size + gap),
                    'y': start_y + r * (size + gap),
                    'w': size,
                    'h': size,
                    'color': '#333333',
                    'is_special': False
                }
                self.create_key_widget(config)

    def create_key_widget(self, config):
        btn = KeyButton(self.keyboard_canvas, config, self, command=self.handle_action)
        btn.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.keys.append(btn)

    def handle_action(self, action_id):
        if not self.layout_active: return
        
        # تأثير بصري
        if self.settings["touch_feedback"]:
            self.flash_screen()
            
        # محاكاة الإجراء
        print(f"Action Triggered: {action_id}")

        # العثور على الزر أو الكنترول المرتبط بالـ action_id
        target_control = None
        for key in self.keys:
            if key.key_config.get('action') == action_id:
                target_control = key
                break

        if target_control and PYAUTOGUI_AVAILABLE:
            # حساب الإحداثيات المطلقة على الشاشة
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()

            # إحداثيات الزر بالنسبة للنافذة
            rel_x = target_control.winfo_x()
            rel_y = target_control.winfo_y()
            width = target_control.winfo_width()
            height = target_control.winfo_height()

            # النقطة المركزية للزر
            abs_x = root_x + rel_x + width // 2
            abs_y = root_y + rel_y + height // 2

            # تنفيذ النقرة (في ثريد منفصل لتجنب تجميد الواجهة)
            threading.Thread(target=lambda: pyautogui.click(abs_x, abs_y), daemon=True).start()

        if self.recording:
            self.recorded_actions.append({
                "time": time.time(),
                "action": action_id,
                "type": "key_press"
            })

    def flash_screen(self):
        # وميض سريع للخلفية
        original = self.canvas_area.cget('bg')
        self.canvas_area.config(bg='#333333')
        self.root.after(50, lambda: self.canvas_area.config(bg=original))

    # --- الوظائف الرئيسية (Hotkeys Logic) ---
    
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        status = "تفعيل" if self.edit_mode else "إيقاف"
        print(f"وضع التعديل: {status}")
        # تغيير لون الحدود للأزرار في وضع التعديل
        for key in self.keys:
            if self.edit_mode:
                key.config(highlightbackground="yellow", highlightthickness=2)
            else:
                key.config(highlightbackground="", highlightthickness=0)

    def toggle_transparency(self):
        self.transparency_enabled = not self.transparency_enabled
        self.apply_transparency()

    def update_transparency(self, val):
        level = int(val) / 100.0
        if level < 0.01: level = 0.01
        self.transparency_level = level
        if self.transparency_enabled:
            self.apply_transparency()

    def apply_transparency(self):
        if self.transparency_enabled:
            # ملاحظة: الشفافية الكاملة تتطلب نظام تشغيل يدعمها وقد تختلف في Tkinter
            self.root.attributes('-alpha', self.transparency_level)
        else:
            self.root.attributes('-alpha', 1.0)

    def apply_click_through(self, enabled):
        """تفعيل أو إيقاف خاصية النقر من خلال النافذة (ويندوز فقط)"""
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if not hwnd: hwnd = self.root.winfo_id()

                # WS_EX_TRANSPARENT = 0x00000020
                # WS_EX_LAYERED = 0x00080000
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
                if enabled:
                    style |= 0x00000020 | 0x00080000
                else:
                    style &= ~0x00000020

                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            except Exception as e:
                print(f"Error applying click-through: {e}")

    def toggle_mouse_lock(self):
        self.mouse_locked = not self.mouse_locked
        msg = "تم قفل الماوس (التحكم بالتطبيق فقط)" if self.mouse_locked else "تم تحرير الماوس"
        print(msg)

        if self.mouse_locked:
            # Clear aim cache when locking to get fresh coordinates
            for aim in self.aim_controls:
                if hasattr(aim, 'last_aim_center'):
                    del aim.last_aim_center
        # في تطبيق حقيقي نستخدم win32api لتقييد الماوس

    def toggle_layout(self):
        self.layout_active = not self.layout_active
        state = "نشط" if self.layout_active else "متوقف"
        print(f"حالة التخطيط: {state}")

        if self.layout_active:
            # تحديث خارطة المفاتيح قبل البدء
            self.input_handler.key_map = {}
            for key in self.keys:
                binding = key.key_config.get('binding')
                if binding:
                    self.input_handler.key_map[binding.lower()] = key.key_config['action']

            self.input_handler.start()
            self.apply_click_through(True)
            self.root.attributes('-topmost', True)
        else:
            self.input_handler.stop()
            self.apply_click_through(False)
            self.root.attributes('-topmost', False)

        color = "#00ff00" if self.layout_active else "#ff0000"
        self.sidebar.config(bg=color if not self.edit_mode else "#2d2d2d")

    def change_theme(self, theme_name):
        colors = {
            "داكن": ("#1e1e1e", "#2d2d2d", "#ffffff"),
            "فاتح": ("#f0f0f0", "#ffffff", "#000000"),
            "أزرق": ("#001f3f", "#003366", "#ffffff"),
            "أخضر": ("#001100", "#003300", "#00ff00"),
            "برتقالي": ("#331100", "#552200", "#ffaa00")
        }
        if theme_name in colors:
            bg, side, txt = colors[theme_name]
            self.main_frame.config(bg=bg)
            self.canvas_area.config(bg=bg)
            self.keyboard_canvas.config(bg=bg)
            self.sidebar.config(bg=side)
            # تحديث الألوان داخل التبويبات يتطلب تكرار الحلقات، تم تبسيطه هنا
    
    def update_key_size(self, val):
        """تحديث حجم المفاتيح"""
        size = int(val)
        self.settings["key_size"] = size
        print(f"تم تغيير حجم المفاتيح إلى: {size}")
    
    def update_grid(self, val):
        """تحديث حجم الشبكة"""
        grid_size = int(val)
        self.settings["grid_snap"] = grid_size
        print(f"تم تغيير حجم الشبكة إلى: {grid_size}")

    def bind_hotkeys(self):
        self.root.bind("<Key>", self.on_any_key)
        self.root.bind("<F1>", lambda e: self.toggle_layout())
        self.root.bind("<F2>", lambda e: self.toggle_mouse_lock())
        self.root.bind("<F3>", lambda e: self.toggle_transparency())
        self.root.bind("<Control-e>", lambda e: self.toggle_edit_mode())
        self.root.bind("<Control-s>", lambda e: self.save_layout())
        self.root.bind("<Control-o>", lambda e: self.load_layout())
        self.root.bind("<Control-n>", lambda e: self.new_layout())
        # دعم Ctrl+Scroll لتغيير الحجم
        self.root.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
    
    def new_layout(self):
        """إنشاء تخطيط جديد"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من إنشاء تخطيط جديد؟ سيتم فقدان التخطيط الحالي."):
            for widget in self.keyboard_canvas.winfo_children():
                widget.destroy()
            self.keys = []
            self.load_default_layout()
            print("تم إنشاء تخطيط جديد")
    
    def on_any_key(self, event):
        if self.edit_mode and self.selected_control:
            key_name = event.keysym
            if len(key_name) == 1:
                key_name = key_name.lower()

            if isinstance(self.selected_control, KeyButton):
                self.selected_control.key_config['binding'] = key_name
                self.selected_control.key_config['label'] = key_name.upper()
                self.selected_control.draw_key()
                print(f"Bound {self.selected_control.key_config['id']} to {key_name}")
            elif isinstance(self.selected_control, RepeatedTapControl):
                self.selected_control.config_data['binding'] = key_name
                self.selected_control.draw_repeated()
                print(f"Bound {self.selected_control.config_data['id']} to {key_name}")

            self.selected_control.config(highlightbackground="yellow", highlightthickness=2)
            self.selected_control = None

    def on_ctrl_scroll(self, event):
        """تغيير حجم المفتاح المحدد عند الضغط على Ctrl+Scroll"""
        if not self.edit_mode or len(self.keys) == 0:
            return
        
        # الحصول على آخر مفتاح تم النقر عليه (يمكن تحسينه)
        delta = 1 if event.delta > 0 else -1
        current_size = self.settings.get("key_size", 50)
        new_size = max(30, min(200, current_size + delta * 5))
        self.settings["key_size"] = new_size
        self.scale_key_size.set(new_size)
        print(f"حجم المفاتيح: {new_size}")

    def save_layout(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filename:
            data = []
            for key in self.keys:
                data.append(key.key_config)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("نجاح", "تم حفظ التخطيط بنجاح!")

    def load_layout(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                # مسح القديم وإنشاء الجديد
                for widget in self.keyboard_canvas.winfo_children():
                    widget.destroy()
                self.keys = []
                for config in data:
                    self.create_key_widget(config)
                messagebox.showinfo("نجاح", "تم تحميل التخطيط!")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

    def animate_loop(self):
        # حلقة بسيطة لأي رسوم متحركة مستقبلية
        self.root.after(16, self.animate_loop) # ~60 FPS

if __name__ == "__main__":
    root = tk.Tk()
    # محاولة جعل النافذة فوق الجميع
    try:
        root.attributes('-topmost', True)
    except:
        pass
    
    app = KeyboardMapperApp(root)
    root.mainloop()