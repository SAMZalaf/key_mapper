import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import os
import sys
import threading
import time
import random
import math
from datetime import datetime

# محاولة استيراد مكتبات المحاكاة (قد تتطلب تثبيت إضافي أو تعمل فقط على ويندوز مع pyautogui)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Button, Controller as MouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

if not PYAUTOGUI_AVAILABLE or not PYNPUT_AVAILABLE:
    print("تنبيه: بعض المكتبات (pyautogui, pynput) غير متوفرة. المحاكاة قد تكون محدودة.")

class KeyButton(tk.Canvas):
    def __init__(self, parent, key_config, command=None, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.key_config = key_config
        self.command = command
        self.is_pressed = False
        self.base_color = key_config.get('color', '#333333')
        self.active_color = key_config.get('active_color', '#00ff00')
        self.text_color = key_config.get('text_color', '#ffffff')
        
        self.draw_key()
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Double-Button-1>", self.on_double_click)
        
        # دعم السحب والإفلات في وضع التعديل
        self.bind("<B1-Motion>", self.on_drag)
        self.drag_start_x = 0
        self.drag_start_y = 0

    def draw_key(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2: return
        
        radius = 5
        color = self.active_color if self.is_pressed else self.base_color
        
        # رسم مستطيل بحواف دائرية
        self.create_rounded_rect(0, 0, w, h, radius, fill=color, outline="#555555", width=2)
        
        # النص
        label = self.key_config.get('label', '?')
        self.create_text(w//2, h//2, text=label, fill=self.text_color, font=("Arial", 10, "bold"))
        
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
        if self.command and not app.edit_mode:
            self.command(self.key_config, is_press=True)

    def on_release(self, event):
        self.is_pressed = False
        self.draw_key()
        if self.command and not app.edit_mode:
            self.command(self.key_config, is_press=False)

    def on_drag(self, event):
        if app.edit_mode:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            new_x = self.winfo_x() + dx
            new_y = self.winfo_y() + dy

            # Snap to grid
            snap = app.settings.get("grid_snap", 1)
            new_x = (new_x // snap) * snap
            new_y = (new_y // snap) * snap

            self.place(x=new_x, y=new_y)
            self.key_config['x'] = new_x
            self.key_config['y'] = new_y

    def on_double_click(self, event):
        if app.edit_mode:
            self.edit_settings()

    def edit_settings(self):
        # نافذة تعديل إعدادات المفتاح
        dialog = tk.Toplevel(self)
        dialog.title("تعديل المفتاح")
        dialog.geometry("300x400")

        tk.Label(dialog, text="الاسم المعروض:").pack()
        ent_label = tk.Entry(dialog)
        ent_label.insert(0, self.key_config.get('label', ''))
        ent_label.pack()

        tk.Label(dialog, text="المفتاح المربوط (مثلاً w أو Key.space):").pack()
        ent_bind = tk.Entry(dialog)
        ent_bind.insert(0, self.key_config.get('bind', ''))
        ent_bind.pack()

        tk.Label(dialog, text="النوع (button, dpad, aim):").pack()
        ent_type = tk.Entry(dialog)
        ent_type.insert(0, self.key_config.get('type', 'button'))
        ent_type.pack()

        def save():
            self.key_config['label'] = ent_label.get()
            self.key_config['bind'] = ent_bind.get()
            self.key_config['type'] = ent_type.get()
            self.draw_key()
            app.refresh_key_map()
            dialog.destroy()

        tk.Button(dialog, text="حفظ", command=save).pack(pady=10)
        tk.Button(dialog, text="حذف", command=lambda: self.delete_key(dialog), fg="red").pack()

    def delete_key(self, dialog):
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا المفتاح؟"):
            app.keys.remove(self)
            self.destroy()
            app.refresh_key_map()
            dialog.destroy()

class KeyboardMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Mapper Pro - Advanced Edition")
        self.root.geometry("1100x800")
        
        # الأجهزة المحاكية
        if PYNPUT_AVAILABLE:
            self.kb_controller = KeyboardController()
            self.mouse_controller = MouseController()
            self.kb_listener = keyboard.Listener(on_press=self.on_global_key_press, on_release=self.on_global_key_release)
            self.kb_listener.start()
            self.m_listener = mouse.Listener(on_move=self.on_global_mouse_move, on_click=self.on_global_mouse_click)
            self.m_listener.start()

        # المتغيرات العامة
        self.edit_mode = False
        self.transparency_enabled = False
        self.transparency_level = 1.0
        self.mouse_locked = False
        self.layout_active = True
        self.theme = "dark"
        self.keys = []
        self.recording = False
        self.recorded_actions = []
        
        # تخطيط المفاتيح الفعلي (المفتاح الفعلي -> الإجراء)
        self.key_map = {}
        self.pressed_keys = set()

        # إعدادات الافتراضية
        self.settings = {
            "sensitivity": 1.0,
            "touch_feedback": True,
            "grid_snap": 10,
            "key_size": 50,
            "fps": 60
        }
        
        self.setup_ui()
        self.load_default_layout()
        self.bind_hotkeys()
        
        self.animate_loop()

    def on_global_key_press(self, key):
        if not self.layout_active or self.edit_mode:
            return

        k = self.get_key_string(key)
        self.pressed_keys.add(k)

        if k in self.key_map:
            config = self.key_map[k]
            self.handle_action(config, is_press=True)

    def on_global_key_release(self, key):
        if not self.layout_active or self.edit_mode:
            return

        k = self.get_key_string(key)
        if k in self.pressed_keys:
            self.pressed_keys.remove(k)

        if k in self.key_map:
            config = self.key_map[k]
            self.handle_action(config, is_press=False)

    def on_global_mouse_move(self, x, y):
        if self.mouse_locked and self.layout_active and not self.edit_mode:
            # Shooting Mode (Aim Mode) logic
            # Calculate relative movement from center
            screen_w, screen_h = pyautogui.size()
            center_x, center_y = screen_w // 2, screen_h // 2

            # Avoid infinite loop if we are already at center
            if x == center_x and y == center_y:
                return

            dx = x - center_x
            dy = y - center_y

            if dx != 0 or dy != 0:
                # In a real scenario, we might use Win32 API to send raw input
                # For now, we simulate the 'camera look' by returning mouse to center
                # and potentially triggering a secondary action or macro if defined
                pyautogui.moveTo(center_x, center_y)

                # Apply sensitivity
                sens = self.settings.get("sensitivity", 1.0)
                # print(f"Aim Move: DX={dx*sens}, DY={dy*sens}")

    def on_global_mouse_click(self, x, y, button, pressed):
        if not self.layout_active or self.edit_mode:
            return

        k = str(button)
        if k in self.key_map:
            config = self.key_map[k]
            self.handle_action(config, is_press=pressed)

    def get_key_string(self, key):
        try:
            return key.char
        except AttributeError:
            return str(key)

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

    def add_new_button(self):
        config = {
            'id': f"btn_{int(time.time())}",
            'label': 'New',
            'type': 'button',
            'bind': 'k',
            'action': 'new_action',
            'x': 100, 'y': 100, 'w': 60, 'h': 60,
            'color': '#333333',
            'is_special': False
        }
        self.create_key_widget(config)
        messagebox.showinfo("تنبيه", "تم إضافة زر جديد. انقر مزدوجاً لتعديله.")

    def add_new_dpad(self):
        config = {
            'id': f"dpad_{int(time.time())}",
            'label': 'DPad',
            'type': 'dpad',
            'bind': 'w',
            'action': 'dpad',
            'x': 100, 'y': 100, 'w': 150, 'h': 150,
            'color': '#1a1a1a',
            'is_special': True
        }
        self.create_key_widget(config)
        messagebox.showinfo("تنبيه", "تم إضافة D-Pad جديد.")

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

        # تاب الإضافة (جديد)
        tab_add = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_add, text="إضافة")

        lbl_add = tk.Label(tab_add, text="إضافة عنصر جديد:", bg="#2d2d2d", fg="white")
        lbl_add.pack(pady=10)

        btn_add_btn = tk.Button(tab_add, text="إضافة زر عادي", command=self.add_new_button, bg="#444", fg="white")
        btn_add_btn.pack(fill=tk.X, pady=5)

        btn_add_dpad = tk.Button(tab_add, text="إضافة D-Pad", command=self.add_new_dpad, bg="#444", fg="white")
        btn_add_dpad.pack(fill=tk.X, pady=5)
        
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
        """تشغيل تسجيل محفوظ (ماكرو)"""
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    actions = json.load(f)

                def run_macro():
                    if not actions: return
                    start_time = actions[0]['time']
                    for action in actions:
                        delay = action['time'] - start_time
                        time.sleep(max(0, delay))
                        start_time = action['time']
                        self.handle_action(action['config'], is_press=(action['type'] == 'key_press'))
                        # نحتاج لـ key_release أيضاً في التسجيل ليكون الماكرو دقيقاً
                    messagebox.showinfo("ماكرو", "اكتمل تشغيل الماكرو")

                threading.Thread(target=run_macro, daemon=True).start()
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
        # إنشاء مفاتيح افتراضية مع ربط حقيقي وأنواع متقدمة
        default_keys = [
            # D-Pad
            {'label': 'DPad', 'type': 'dpad', 'bind': 'w', 'x': 100, 'y': 500, 'w': 150, 'h': 150, 'color': '#1a1a1a'},

            # Buttons
            {'label': 'Space', 'bind': 'Key.space', 'x': 500, 'y': 600, 'w': 200, 'h': 50},
            {'label': 'F', 'bind': 'f', 'x': 750, 'y': 500, 'w': 60, 'h': 60},
            {'label': 'R', 'bind': 'r', 'x': 750, 'y': 420, 'w': 60, 'h': 60},
            {'label': 'Left Click (Fire)', 'bind': 'Button.left', 'x': 850, 'y': 500, 'w': 80, 'h': 80, 'color': '#550000'},

            # Aim Mode
            {'label': 'Aim Mode (F1)', 'type': 'aim', 'bind': 'Key.f1', 'x': 900, 'y': 50, 'w': 100, 'h': 40, 'color': '#004400'},
        ]
        
        # إضافة WASD للـ key_map يدوياً للـ DPad إذا لزم الأمر
        self.key_map['w'] = default_keys[0]
        self.key_map['a'] = default_keys[0]
        self.key_map['s'] = default_keys[0]
        self.key_map['d'] = default_keys[0]

        for k in default_keys:
            config = {
                'id': k['label'],
                'label': k['label'],
                'type': k.get('type', 'button'),
                'bind': k['bind'],
                'action': k['label'],
                'x': k['x'],
                'y': k['y'],
                'w': k.get('w', 60),
                'h': k.get('h', 60),
                'color': k.get('color', '#333333'),
                'is_special': k.get('type', 'button') != 'button'
            }
            self.create_key_widget(config)

    def create_key_widget(self, config):
        btn = KeyButton(self.keyboard_canvas, config, command=self.handle_action)
        btn.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.keys.append(btn)
        self.refresh_key_map()

    def refresh_key_map(self):
        self.key_map = {}
        for key in self.keys:
            cfg = key.key_config
            if 'bind' in cfg:
                # دعم مفاتيح الـ D-Pad (WASD)
                if cfg.get('type') == 'dpad':
                    for k in ['w', 'a', 's', 'd']:
                        self.key_map[k] = cfg
                else:
                    self.key_map[cfg['bind']] = cfg

    def handle_action(self, config, is_press=True):
        if not self.layout_active: return
        
        action_type = config.get('type', 'button')

        if action_type == 'button':
            self.handle_button_action(config, is_press)
        elif action_type == 'dpad':
            self.handle_dpad_action(config, is_press)
        elif action_type == 'aim':
            if is_press: self.toggle_aim_mode()

    def handle_button_action(self, config, is_press):
        if is_press:
            if self.settings["touch_feedback"]:
                self.flash_screen()

            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            click_x = root_x + config['x'] + config['w']//2
            click_y = root_y + config['y'] + config['h']//2

            if PYAUTOGUI_AVAILABLE:
                threading.Thread(target=lambda: pyautogui.mouseDown(click_x, click_y), daemon=True).start()
            
            if self.recording:
                self.recorded_actions.append({
                    "time": time.time(),
                    "config": config,
                    "type": "key_press"
                })
        else:
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            click_x = root_x + config['x'] + config['w']//2
            click_y = root_y + config['y'] + config['h']//2
            if PYAUTOGUI_AVAILABLE:
                threading.Thread(target=lambda: pyautogui.mouseUp(click_x, click_y), daemon=True).start()

            if self.recording:
                self.recorded_actions.append({
                    "time": time.time(),
                    "config": config,
                    "type": "key_release"
                })

    def handle_dpad_action(self, config, is_press):
        # يتم التعامل مع الـ D-Pad الآن في animate_loop للحصول على استجابة أسلس
        pass

    def update_dpad_state(self):
        if not self.layout_active or self.edit_mode: return

        # البحث عن إعداد الـ D-Pad
        dpad_config = None
        for key in self.keys:
            if key.key_config.get('type') == 'dpad':
                dpad_config = key.key_config
                break

        if not dpad_config or not PYAUTOGUI_AVAILABLE: return

        cx = self.root.winfo_rootx() + dpad_config['x'] + dpad_config['w']//2
        cy = self.root.winfo_rooty() + dpad_config['y'] + dpad_config['h']//2
        offset = dpad_config.get('offset', 50)

        dx, dy = 0, 0
        if 'w' in self.pressed_keys: dy -= offset
        if 's' in self.pressed_keys: dy += offset
        if 'a' in self.pressed_keys: dx -= offset
        if 'd' in self.pressed_keys: dx += offset

        if dx != 0 or dy != 0:
            if not getattr(self, 'dpad_active', False):
                pyautogui.mouseDown(cx, cy)
                self.dpad_active = True
            pyautogui.moveTo(cx + dx, cy + dy)
        else:
            if getattr(self, 'dpad_active', False):
                pyautogui.mouseUp()
                self.dpad_active = False

    def toggle_aim_mode(self):
        self.mouse_locked = not self.mouse_locked
        status = 'ON' if self.mouse_locked else 'OFF'
        print(f"Shooting Mode: {status}")

        if self.mouse_locked:
            self.root.config(cursor="none")
            # Move mouse to center initially
            screen_w, screen_h = pyautogui.size()
            pyautogui.moveTo(screen_w // 2, screen_h // 2)
            # Optional: Lock mouse within window or use ClipCursor (requires Win32)
        else:
            self.root.config(cursor="")

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

    def toggle_mouse_lock(self):
        self.mouse_locked = not self.mouse_locked
        msg = "تم قفل الماوس (التحكم بالتطبيق فقط)" if self.mouse_locked else "تم تحرير الماوس"
        print(msg)
        # في تطبيق حقيقي نستخدم win32api لتقييد الماوس

    def toggle_layout(self):
        self.layout_active = not self.layout_active
        state = "نشط" if self.layout_active else "متوقف"
        print(f"حالة التخطيط: {state}")
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
        # تحديث الحالات المستمرة
        self.update_dpad_state()

        # حلقة بسيطة لأي رسوم متحركة مستقبلية
        fps = self.scale_fps.get() if hasattr(self, 'scale_fps') else 60
        ms = int(1000 / fps)
        self.root.after(ms, self.animate_loop)

if __name__ == "__main__":
    root = tk.Tk()
    # محاولة جعل النافذة فوق الجميع
    try:
        root.attributes('-topmost', True)
    except:
        pass
    
    app = KeyboardMapperApp(root)
    root.mainloop()