import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, Menu
import json
import os
import sys
import threading
import time
import random
import math
from datetime import datetime

# محاولة استيراد مكتبات المحاكاة
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

class DraggableButton(tk.Frame):
    """زر قابل للسحب مع قائمة سياق بالزر الأيمن"""
    
    def __init__(self, parent, key_config, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.key_config = key_config
        self.is_pressed = False
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # إعدادات الزر
        self.label_text = key_config.get('label', 'Button')
        self.bind_key = key_config.get('bind', '')
        self.sensitivity = key_config.get('sensitivity', 1.0)
        self.btn_color = key_config.get('color', '#4a9eff')
        self.width = key_config.get('width', 80)
        self.height = key_config.get('height', 80)
        
        # تكوين الواجهة
        self.configure(bg=self.btn_color, width=self.width, height=self.height)
        self.configure(highlightbackground=self.btn_color, highlightthickness=2)
        
        # تسمية الزر
        self.label = tk.Label(self, text=self.label_text, bg=self.btn_color, 
                             fg='white', font=('Arial', 10, 'bold'))
        self.label.pack(expand=True)
        
        # ربط الأحداث
        self.bind("<Button-1>", self.on_left_click)
        self.bind("<ButtonRelease-1>", self.on_left_release)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Button-3>", self.show_context_menu)
        self.label.bind("<Button-1>", self.on_left_click)
        self.label.bind("<ButtonRelease-1>", self.on_left_release)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<Button-3>", self.show_context_menu)
        
        # حالة الضغط
        self.original_color = self.btn_color
        self.pressed_color = key_config.get('pressed_color', '#00ff00')
        
        # ربط المفتاح الفعلي بهذا الزر
        self.setup_key_binding()
    
    def setup_key_binding(self):
        """ربط المفتاح الفعلي بتفعيل هذا الزر"""
        if self.bind_key and self.app:
            self.app.key_bindings[self.bind_key.lower()] = self
    
    def on_left_click(self, event):
        """عند النقر الأيسر - تفعيل فوري"""
        self.is_pressed = True
        self.dragging = False
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.configure(bg=self.pressed_color)
        self.label.configure(bg=self.pressed_color)
        
        # تفعيل الإجراء فوراً عند النقر
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=True)
    
    def on_left_release(self, event):
        """عند رفع الإصبع"""
        if not self.dragging:
            # إذا لم يكن سحباً، نعتبره نقرة كاملة
            pass
        
        self.is_pressed = False
        self.dragging = False
        self.configure(bg=self.original_color)
        self.label.configure(bg=self.original_color)
        
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=False)
    
    def on_drag(self, event):
        """السحب والتحريك"""
        if self.app.edit_mode:
            self.dragging = True
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # الحصول على الموقع الحالي
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            
            new_x = current_x + dx
            new_y = current_y + dy
            
            # Snap to grid
            snap = self.app.settings.get("grid_snap", 10)
            new_x = (new_x // snap) * snap
            new_y = (new_y // snap) * snap
            
            self.place(x=new_x, y=new_y)
            self.key_config['x'] = new_x
            self.key_config['y'] = new_y
    
    def show_context_menu(self, event):
        """إظهار قائمة السياق بالزر الأيمن"""
        context_menu = Menu(self, tearoff=0, bg='#2d2d2d', fg='white')
        
        context_menu.add_command(label="✂️ قص", command=self.cut_button)
        context_menu.add_command(label="📋 نسخ", command=self.copy_button)
        context_menu.add_command(label="📌 لصق", command=self.paste_button)
        context_menu.add_separator()
        context_menu.add_command(label="⚙️ خصائص", command=self.edit_properties)
        context_menu.add_command(label="🎨 تغيير اللون", command=self.change_color)
        context_menu.add_command(label="📏 تغيير الحجم", command=self.change_size)
        context_menu.add_command(label="🎯 حساسية", command=self.edit_sensitivity)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ حذف", command=self.delete_button, foreground='red')
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def cut_button(self):
        """قص الزر"""
        self.app.clipboard_data = self.key_config.copy()
        self.delete_button()
    
    def copy_button(self):
        """نسخ الزر"""
        self.app.clipboard_data = self.key_config.copy()
    
    def paste_button(self):
        """لصق زر جديد"""
        if self.app.clipboard_data:
            new_config = self.app.clipboard_data.copy()
            new_config['id'] = f"btn_{int(time.time() * 1000)}"
            new_config['x'] = self.key_config['x'] + 20
            new_config['y'] = self.key_config['y'] + 20
            new_config['label'] = f"{new_config.get('label', 'Copy')} (2)"
            self.app.create_button_widget(new_config)
    
    def edit_properties(self):
        """تحرير خصائص الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("خصائص الزر")
        dialog.geometry("350x400")
        dialog.configure(bg='#2d2d2d')
        
        # جعل النافذة منبثقة
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="اسم الزر:", bg='#2d2d2d', fg='white').pack(pady=(20,5))
        ent_label = tk.Entry(dialog, bg='#444', fg='white')
        ent_label.insert(0, self.label_text)
        ent_label.pack(fill=tk.X, padx=20)
        
        tk.Label(dialog, text="المفتاح المرتبط (مثلاً: w, a, space, button1):", 
                bg='#2d2d2d', fg='white').pack(pady=(15,5))
        ent_bind = tk.Entry(dialog, bg='#444', fg='white')
        ent_bind.insert(0, self.bind_key)
        ent_bind.pack(fill=tk.X, padx=20)
        
        tk.Label(dialog, text="نوع الإجراء:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        action_type = tk.StringVar(value=self.key_config.get('action_type', 'key'))
        type_combo = ttk.Combobox(dialog, textvariable=action_type, 
                                  values=['key', 'mouse_click', 'macro', 'text'],
                                  state='readonly')
        type_combo.pack(fill=tk.X, padx=20)
        
        tk.Label(dialog, text="القيمة/الإجراء:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        ent_action = tk.Entry(dialog, bg='#444', fg='white')
        ent_action.insert(0, self.key_config.get('action_value', ''))
        ent_action.pack(fill=tk.X, padx=20)
        
        def save():
            self.key_config['label'] = ent_label.get()
            self.key_config['bind'] = ent_bind.get()
            self.key_config['action_type'] = action_type.get()
            self.key_config['action_value'] = ent_action.get()
            
            # تحديث العرض
            self.label_text = ent_label.get()
            self.bind_key = ent_bind.get()
            self.label.configure(text=self.label_text)
            
            # إعادة ربط المفتاح
            if self.app:
                self.app.key_bindings.clear()
                for btn in self.app.buttons:
                    btn.setup_key_binding()
            
            dialog.destroy()
        
        tk.Button(dialog, text="💾 حفظ", command=save, bg='#4a9eff', fg='white').pack(pady=20)
    
    def change_color(self):
        """تغيير لون الزر"""
        color = colorchooser.askcolor(initialcolor=self.btn_color, title="اختر لون الزر")
        if color[1]:
            self.btn_color = color[1]
            self.key_config['color'] = color[1]
            self.configure(bg=self.btn_color)
            self.label.configure(bg=self.btn_color)
            self.original_color = self.btn_color
    
    def change_size(self):
        """تغيير حجم الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("حجم الزر")
        dialog.geometry("250x150")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="العرض:", bg='#2d2d2d', fg='white').pack(pady=5)
        scale_w = tk.Scale(dialog, from_=30, to=300, orient=tk.HORIZONTAL, 
                          bg='#2d2d2d', fg='white')
        scale_w.set(self.width)
        scale_w.pack()
        
        tk.Label(dialog, text="الارتفاع:", bg='#2d2d2d', fg='white').pack(pady=5)
        scale_h = tk.Scale(dialog, from_=30, to=300, orient=tk.HORIZONTAL,
                          bg='#2d2d2d', fg='white')
        scale_h.set(self.height)
        scale_h.pack()
        
        def apply_size():
            new_w = scale_w.get()
            new_h = scale_h.get()
            self.configure(width=new_w, height=new_h)
            self.key_config['width'] = new_w
            self.key_config['height'] = new_h
            self.width = new_w
            self.height = new_h
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply_size, bg='#4a9eff', fg='white').pack(pady=10)
    
    def edit_sensitivity(self):
        """تحرير حساسية الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("حساسية الزر")
        dialog.geometry("300x150")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text=f"حساسية: {self.sensitivity}", 
                bg='#2d2d2d', fg='white', font=('Arial', 14)).pack(pady=10)
        
        scale_sens = tk.Scale(dialog, from_=0.1, to=5.0, resolution=0.1,
                             orient=tk.HORIZONTAL, bg='#2d2d2d', fg='white',
                             command=lambda v: self.sensitivity_label.configure(text=f"حساسية: {v}"))
        scale_sens.set(self.sensitivity)
        scale_sens.pack(fill=tk.X, padx=20)
        
        self.sensitivity_label = tk.Label(dialog, text=f"حساسية: {self.sensitivity}",
                                         bg='#2d2d2d', fg='white', font=('Arial', 14))
        self.sensitivity_label.pack(pady=10)
        
        def apply_sensitivity():
            self.sensitivity = float(scale_sens.get())
            self.key_config['sensitivity'] = self.sensitivity
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply_sensitivity, bg='#4a9eff', fg='white').pack(pady=10)
    
    def delete_button(self):
        """حذف الزر"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الزر؟"):
            if self.app:
                self.app.buttons.remove(self)
                self.destroy()
                self.app.refresh_key_bindings()

class KeyboardMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Mapper Pro - النسخة المحترفة")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # الأجهزة المحاكية
        if PYNPUT_AVAILABLE:
            self.kb_controller = KeyboardController()
            self.mouse_controller = MouseController()
            self.kb_listener = keyboard.Listener(on_press=self.on_global_key_press, on_release=self.on_global_key_release)
            self.kb_listener.start()
            self.m_listener = mouse.Listener(on_click=self.on_global_mouse_click)
            self.m_listener.start()

        # المتغيرات العامة
        self.edit_mode = True  # البدء بوضع التعديل
        self.buttons = []
        self.key_bindings = {}
        self.clipboard_data = None
        self.recording = False
        self.recorded_actions = []
        self.layout_active = True
        
        # إعدادات
        self.settings = {
            "sensitivity": 1.0,
            "grid_snap": 10,
            "default_width": 80,
            "default_height": 80,
            "default_color": "#4a9eff",
            "pressed_color": "#00ff00"
        }
        
        self.setup_ui()
        self.load_default_buttons()
        self.bind_global_keys()

    def on_global_key_press(self, key):
        """عند ضغط مفتاح - تفعيل الزر المرتبط"""
        if not self.layout_active or self.edit_mode:
            return

        k = self.get_key_string(key).lower()
        
        # البحث عن الزر المرتبط بهذا المفتاح
        if k in self.key_bindings:
            btn = self.key_bindings[k]
            self.trigger_button_action(btn.key_config, is_press=True)

    def on_global_key_release(self, key):
        """عند رفع مفتاح"""
        if not self.layout_active or self.edit_mode:
            return

        k = self.get_key_string(key).lower()
        
        if k in self.key_bindings:
            btn = self.key_bindings[k]
            self.trigger_button_action(btn.key_config, is_press=False)

    def on_global_mouse_click(self, x, y, button, pressed):
        """عند نقر الماوس"""
        if not self.layout_active or self.edit_mode:
            return

        k = str(button).lower()
        
        if k in self.key_bindings:
            btn = self.key_bindings[k]
            self.trigger_button_action(btn.key_config, is_press=pressed)

    def get_key_string(self, key):
        """الحصول على نص المفتاح"""
        try:
            return key.char
        except AttributeError:
            key_map = {
                Key.space: 'space',
                Key.enter: 'return',
                Key.shift: 'shift',
                Key.ctrl: 'control',
                Key.alt: 'alt',
                Key.tab: 'tab',
                Key.esc: 'escape',
                Key.backspace: 'backspace',
                Key.caps_lock: 'caps_lock',
            }
            return key_map.get(key, str(key).replace('Key.', ''))

    def setup_ui(self):
        """إعداد واجهة المستخدم - سايدبار فقط"""
        # الشريط الجانبي للإعدادات
        self.sidebar = tk.Frame(self.root, width=300, bg="#2d2d2d")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # منطقة الأزرار القابلة للسحب
        self.canvas_area = tk.Frame(self.root, bg="#1e1e1e")
        self.canvas_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.keyboard_canvas = tk.Canvas(self.canvas_area, bg="#1e1e1e", highlightthickness=0)
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.build_sidebar()

    def add_new_button(self):
        """إضافة زر جديد"""
        config = {
            'id': f"btn_{int(time.time() * 1000)}",
            'label': 'زر جديد',
            'bind': '',
            'action_type': 'key',
            'action_value': '',
            'x': 100, 
            'y': 100, 
            'width': 80, 
            'height': 80,
            'color': '#4a9eff',
            'sensitivity': 1.0
        }
        self.create_button_widget(config)

    def build_sidebar(self):
        """بناء الشريط الجانبي"""
        # عنوان
        lbl_title = tk.Label(self.sidebar, text="⚙️ الإعدادات", 
                            bg="#2d2d2d", fg="#ffffff", 
                            font=("Arial", 16, "bold"))
        lbl_title.pack(pady=15)
        
        # زر إضافة زر جديد
        btn_add = tk.Button(self.sidebar, text="➕ إضافة زر", 
                           command=self.add_new_button, 
                           bg="#4a9eff", fg="white", 
                           font=("Arial", 12, "bold"),
                           height=2)
        btn_add.pack(fill=tk.X, padx=15, pady=10)
        
        # فاصل
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم وضع التعديل
        lbl_edit = tk.Label(self.sidebar, text="📝 وضع التعديل", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_edit.pack(anchor='w', padx=15, pady=(10,5))
        
        self.btn_edit = tk.Button(self.sidebar, text="✅ مفعل (Ctrl+E)", 
                                 command=self.toggle_edit_mode, 
                                 bg="#00aa00", fg="white")
        self.btn_edit.pack(fill=tk.X, padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الحساسية العامة
        lbl_sens = tk.Label(self.sidebar, text="🎯 الحساسية العامة", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_sens.pack(anchor='w', padx=15, pady=(10,5))
        
        self.scale_sensitivity = tk.Scale(self.sidebar, from_=0.1, to=5.0, 
                                         resolution=0.1, orient=tk.HORIZONTAL,
                                         label="قيمة الحساسية",
                                         bg="#2d2d2d", fg="white",
                                         highlightthickness=0)
        self.scale_sensitivity.set(1.0)
        self.scale_sensitivity.pack(fill=tk.X, padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الشبكة
        lbl_grid = tk.Label(self.sidebar, text="📐 ضبط الشبكة", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_grid.pack(anchor='w', padx=15, pady=(10,5))
        
        self.scale_grid = tk.Scale(self.sidebar, from_=5, to=50, 
                                  orient=tk.HORIZONTAL,
                                  label="حجم الشبكة",
                                  bg="#2d2d2d", fg="white",
                                  highlightthickness=0,
                                  command=self.update_grid)
        self.scale_grid.set(10)
        self.scale_grid.pack(fill=tk.X, padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الإجراءات
        lbl_actions = tk.Label(self.sidebar, text="💾 حفظ وتحميل", 
                              bg="#2d2d2d", fg="#aaaaaa",
                              font=("Arial", 11, "bold"))
        lbl_actions.pack(anchor='w', padx=15, pady=(10,5))
        
        btn_save = tk.Button(self.sidebar, text="💾 حفظ التخطيط", 
                            command=self.save_layout, 
                            bg="#444", fg="white")
        btn_save.pack(fill=tk.X, padx=15, pady=5)
        
        btn_load = tk.Button(self.sidebar, text="📂 تحميل تخطيط", 
                            command=self.load_layout, 
                            bg="#444", fg="white")
        btn_load.pack(fill=tk.X, padx=15, pady=5)
        
        btn_clear = tk.Button(self.sidebar, text="🗑️ مسح الكل", 
                             command=self.clear_all_buttons, 
                             bg="#aa0000", fg="white")
        btn_clear.pack(fill=tk.X, padx=15, pady=5)
        
        # معلومات
        lbl_info = tk.Label(self.sidebar, 
                           text="💡 انقر بالزر الأيمن على أي زر\nللحصول على قائمة الإجراءات",
                           bg="#2d2d2d", fg="#888888",
                           font=("Arial", 9),
                           justify='center')
        lbl_info.pack(side=tk.BOTTOM, pady=20)

    def load_default_buttons(self):
        """تحميل أزرار افتراضية"""
        default_buttons = [
            {'label': 'W', 'bind': 'w', 'x': 200, 'y': 300, 'width': 70, 'height': 70, 'color': '#4a9eff'},
            {'label': 'A', 'bind': 'a', 'x': 130, 'y': 370, 'width': 70, 'height': 70, 'color': '#4a9eff'},
            {'label': 'S', 'bind': 's', 'x': 200, 'y': 370, 'width': 70, 'height': 70, 'color': '#4a9eff'},
            {'label': 'D', 'bind': 'd', 'x': 270, 'y': 370, 'width': 70, 'height': 70, 'color': '#4a9eff'},
            {'label': 'Space', 'bind': 'space', 'x': 300, 'y': 500, 'width': 200, 'height': 60, 'color': '#ff9f4a'},
            {'label': 'R', 'bind': 'r', 'x': 400, 'y': 200, 'width': 70, 'height': 70, 'color': '#ff4a4a'},
            {'label': 'F', 'bind': 'f', 'x': 470, 'y': 200, 'width': 70, 'height': 70, 'color': '#4aff4a'},
        ]
        
        for btn_config in default_buttons:
            config = {
                'id': f"btn_{btn_config['label']}_{int(time.time() * 1000)}",
                'label': btn_config['label'],
                'bind': btn_config['bind'],
                'action_type': 'key',
                'action_value': btn_config['bind'],
                'x': btn_config['x'],
                'y': btn_config['y'],
                'width': btn_config['width'],
                'height': btn_config['height'],
                'color': btn_config['color'],
                'sensitivity': 1.0
            }
            self.create_button_widget(config)

    def create_button_widget(self, config):
        """إنشاء زر قابل للسحب"""
        btn = DraggableButton(self.keyboard_canvas, config, self)
        btn.place(x=config['x'], y=config['y'], width=config['width'], height=config['height'])
        self.buttons.append(btn)
        self.refresh_key_bindings()

    def refresh_key_bindings(self):
        """تحديث ربط المفاتيح"""
        self.key_bindings.clear()
        for btn in self.buttons:
            btn.setup_key_binding()

    def trigger_button_action(self, config, is_press=True):
        """تفعيل إجراء الزر"""
        if not self.layout_active:
            return
        
        sensitivity = config.get('sensitivity', 1.0)
        action_type = config.get('action_type', 'key')
        action_value = config.get('action_value', config.get('bind', ''))
        
        if is_press and self.recording:
            self.recorded_actions.append({
                "time": time.time(),
                "config": config,
                "type": "button_press"
            })
        
        # تنفيذ الإجراء بناءً على النوع
        if action_type == 'key':
            self.execute_key_action(action_value, is_press, sensitivity)
        elif action_type == 'mouse_click':
            self.execute_mouse_action(is_press)
        elif action_type == 'text':
            if is_press:
                self.execute_text_action(action_value)
        elif action_type == 'macro':
            if is_press:
                self.execute_macro_action(action_value)

    def execute_key_action(self, key, is_press, sensitivity):
        """تنفيذ إجراء مفتاح"""
        if not PYNPUT_AVAILABLE or not self.kb_controller:
            return
        
        try:
            # تحويل اسم المفتاح إلى كائن pynput
            key_obj = None
            
            special_keys = {
                'space': Key.space,
                'enter': Key.enter,
                'return': Key.enter,
                'shift': Key.shift,
                'ctrl': Key.ctrl,
                'control': Key.ctrl,
                'alt': Key.alt,
                'tab': Key.tab,
                'esc': Key.esc,
                'escape': Key.esc,
                'backspace': Key.backspace,
                'caps_lock': Key.caps_lock,
                'up': Key.up,
                'down': Key.down,
                'left': Key.left,
                'right': Key.right,
            }
            
            if key in special_keys:
                key_obj = special_keys[key]
            elif len(key) == 1:
                key_obj = key
            else:
                # محاولة استخدام المفتاح كما هو
                key_obj = key
            
            if key_obj:
                if is_press:
                    self.kb_controller.press(key_obj)
                else:
                    self.kb_controller.release(key_obj)
        except Exception as e:
            print(f"خطأ في تنفيذ المفتاح: {e}")

    def execute_mouse_action(self, is_press):
        """تنفيذ نقر الماوس"""
        if not PYNPUT_AVAILABLE or not self.mouse_controller:
            return
        
        if is_press:
            self.mouse_controller.press(Button.left)
        else:
            self.mouse_controller.release(Button.left)

    def execute_text_action(self, text):
        """كتابة نص"""
        if not PYNPUT_AVAILABLE or not self.kb_controller:
            return
        
        self.kb_controller.type(text)

    def execute_macro_action(self, macro_name):
        """تشغيل ماكرو"""
        # يمكن توسيع هذا لاحقاً لتشغيل تسجيلات محفوظة
        print(f"تشغيل الماكرو: {macro_name}")

    def clear_all_buttons(self):
        """مسح جميع الأزرار"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من مسح جميع الأزرار؟"):
            for btn in self.buttons[:]:
                btn.destroy()
            self.buttons.clear()
            self.key_bindings.clear()

    def toggle_edit_mode(self):
        """تبديل وضع التعديل"""
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            self.btn_edit.configure(text="✅ مفعل (Ctrl+E)", bg="#00aa00")
        else:
            self.btn_edit.configure(text="❌ معطل (Ctrl+E)", bg="#aa0000")
        
        print(f"وضع التعديل: {'مفعل' if self.edit_mode else 'معطل'}")

    def bind_global_keys(self):
        """ربط المفاتيح العامة"""
        self.root.bind("<Control-e>", lambda e: self.toggle_edit_mode())
        self.root.bind("<Control-s>", lambda e: self.save_layout())
        self.root.bind("<Control-o>", lambda e: self.load_layout())

    def update_grid(self, val):
        """تحديث حجم الشبكة"""
        grid_size = int(val)
        self.settings["grid_snap"] = grid_size

    def save_layout(self):
        """حفظ التخطيط"""
        filename = filedialog.asksaveasfilename(defaultextension=".json", 
                                                 filetypes=[("JSON Files", "*.json")])
        if filename:
            data = []
            for btn in self.buttons:
                data.append(btn.key_config)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("نجاح", "تم حفظ التخطيط بنجاح!")

    def load_layout(self):
        """تحميل تخطيط"""
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # مسح القديم
                for btn in self.buttons[:]:
                    btn.destroy()
                self.buttons.clear()
                
                # إنشاء الجديد
                for config in data:
                    self.create_button_widget(config)
                
                messagebox.showinfo("نجاح", "تم تحميل التخطيط!")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

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