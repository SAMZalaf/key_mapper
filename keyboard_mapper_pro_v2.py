import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, Menu
import json
import os
import sys
import threading
import time
import random
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
    """زر قابل للسحب مع قائمة سياق بالزر الأيمن ومزايا متقدمة"""
    
    def __init__(self, parent, key_config, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.key_config = key_config
        self.is_pressed = False
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.animation_id = None
        
        # إعدادات الزر
        self.label_text = key_config.get('label', 'Button')
        self.bind_key = key_config.get('bind', '')
        self.sensitivity = key_config.get('sensitivity', 1.0)
        self.btn_color = key_config.get('color', '#4a9eff')
        self.width = key_config.get('width', 80)
        self.height = key_config.get('height', 80)
        self.border_width = key_config.get('border_width', 2)
        self.border_color = key_config.get('border_color', '#ffffff')
        self.font_size = key_config.get('font_size', 12)
        self.icon = key_config.get('icon', '')
        self.tooltip_text = key_config.get('tooltip', '')
        self.press_effect = key_config.get('press_effect', 'scale')
        self.glow_enabled = key_config.get('glow_enabled', False)
        self.glow_color = key_config.get('glow_color', '#00ff00')
        
        # تكوين الواجهة
        self.configure(bg=self.btn_color, width=self.width, height=self.height)
        self.configure(highlightbackground=self.border_color, highlightthickness=self.border_width)
        
        # إطار للتأثيرات
        self.glow_frame = None
        if self.glow_enabled:
            self.create_glow_effect()
        
        # تسمية الزر
        self.label = tk.Label(self, text=self.label_text, bg=self.btn_color, 
                             fg='white', font=('Arial', self.font_size, 'bold'))
        self.label.pack(expand=True)
        
        # ربط الأحداث
        self.bind("<Button-1>", self.on_left_click)
        self.bind("<ButtonRelease-1>", self.on_left_release)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.bind("<MouseWheel>", self.on_mouse_wheel)
        self.label.bind("<Button-1>", self.on_left_click)
        self.label.bind("<ButtonRelease-1>", self.on_left_release)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<Button-3>", self.show_context_menu)
        self.label.bind("<Enter>", self.on_hover_enter)
        self.label.bind("<Leave>", self.on_hover_leave)
        
        # حالة الضغط
        self.original_color = self.btn_color
        self.pressed_color = key_config.get('pressed_color', '#00aa00')
        self.hover_color = key_config.get('hover_color', self.lighten_color(self.btn_color, 20))
        
        # Tooltip
        self.tooltip = None
        
        # ربط المفتاح الفعلي بهذا الزر
        self.setup_key_binding()
    
    def create_glow_effect(self):
        """إنشاء تأثير التوهج"""
        self.glow_frame = tk.Frame(self, bg=self.glow_color)
        self.glow_frame.place(x=-2, y=-2, width=self.width+4, height=self.height+4)
        self.glow_frame.lower()
    
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
        
        # تأثير الضغط
        if self.press_effect == 'scale':
            self.scale_animation(0.9)
        elif self.press_effect == 'color':
            self.configure(bg=self.pressed_color)
            self.label.configure(bg=self.pressed_color)
        elif self.press_effect == 'both':
            self.scale_animation(0.9)
            self.configure(bg=self.pressed_color)
            self.label.configure(bg=self.pressed_color)
        
        # تفعيل الإجراء فوراً عند النقر
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=True)
    
    def on_left_release(self, event):
        """عند رفع الإصبع"""
        self.is_pressed = False
        self.dragging = False
        
        # إعادة الزر لحالته الأصلية
        if self.press_effect in ['scale', 'both']:
            self.scale_animation(1.0)
        if self.press_effect in ['color', 'both']:
            self.configure(bg=self.original_color)
            self.label.configure(bg=self.original_color)
        
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=False)
    
    def scale_animation(self, scale_factor):
        """تأثير التحجيم المتحرك"""
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        current_width = int(self.width * scale_factor)
        current_height = int(self.height * scale_factor)
        
        self.configure(width=current_width, height=current_height)
    
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
        context_menu = Menu(self, tearoff=0, bg='#2d2d2d', fg='white', font=('Arial', 10))
        
        # القائمة الرئيسية
        context_menu.add_command(label="✂️ قص", command=self.cut_button, font=('Arial', 10, 'bold'))
        context_menu.add_command(label="📋 نسخ", command=self.copy_button, font=('Arial', 10))
        context_menu.add_command(label="📌 لصق", command=self.paste_button, font=('Arial', 10))
        context_menu.add_separator()
        context_menu.add_command(label="⚙️ خصائص متقدمة", command=self.edit_properties, font=('Arial', 10, 'bold'))
        context_menu.add_command(label="🎨 تغيير اللون", command=self.change_color, font=('Arial', 10))
        context_menu.add_command(label="🖌️ لون الضغط", command=self.change_pressed_color, font=('Arial', 10))
        context_menu.add_command(label="🌟 لون التمرير", command=self.change_hover_color, font=('Arial', 10))
        context_menu.add_command(label="📏 تغيير الحجم", command=self.change_size, font=('Arial', 10))
        context_menu.add_command(label="🔲 حدود الزر", command=self.edit_border, font=('Arial', 10))
        context_menu.add_command(label="🎯 حساسية فردية", command=self.edit_sensitivity, font=('Arial', 10))
        context_menu.add_command(label="💡 تأثيرات", command=self.edit_effects, font=('Arial', 10))
        context_menu.add_command(label="📝_TOOLTIP", command=self.edit_tooltip, font=('Arial', 10))
        context_menu.add_separator()
        context_menu.add_command(label="🔄 تكرار", command=self.duplicate_button, font=('Arial', 10))
        context_menu.add_command(label="🗑️ حذف", command=self.delete_button, foreground='red', font=('Arial', 10, 'bold'))
        
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
    
    def duplicate_button(self):
        """تكرار الزر"""
        self.copy_button()
        self.paste_button()
    
    def edit_properties(self):
        """تحرير خصائص الزر المتقدمة"""
        dialog = tk.Toplevel(self)
        dialog.title("خصائص الزر المتقدمة")
        dialog.geometry("450x550")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self)
        dialog.grab_set()
        
        # إنشاء Notebook للتبويبات
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تبويب الإعدادات الأساسية
        tab_basic = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(tab_basic, text="أساسي")
        
        tk.Label(tab_basic, text="اسم الزر:", bg='#2d2d2d', fg='white').pack(pady=(20,5))
        ent_label = tk.Entry(tab_basic, bg='#444', fg='white', font=('Arial', 11))
        ent_label.insert(0, self.label_text)
        ent_label.pack(fill=tk.X, padx=20)
        
        tk.Label(tab_basic, text="المفتاح المرتبط:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        ent_bind = tk.Entry(tab_basic, bg='#444', fg='white', font=('Arial', 11))
        ent_bind.insert(0, self.bind_key)
        ent_bind.pack(fill=tk.X, padx=20)
        
        tk.Label(tab_basic, text="نوع الإجراء:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        action_type = tk.StringVar(value=self.key_config.get('action_type', 'key'))
        type_combo = ttk.Combobox(tab_basic, textvariable=action_type, 
                                  values=['key', 'mouse_click', 'macro', 'text', 'combo'],
                                  state='readonly', font=('Arial', 11))
        type_combo.pack(fill=tk.X, padx=20)
        
        tk.Label(tab_basic, text="القيمة/الإجراء:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        ent_action = tk.Entry(tab_basic, bg='#444', fg='white', font=('Arial', 11))
        ent_action.insert(0, self.key_config.get('action_value', ''))
        ent_action.pack(fill=tk.X, padx=20)
        
        # تبويب المظهر
        tab_appearance = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(tab_appearance, text="مظهر")
        
        tk.Label(tab_appearance, text="حجم الخط:", bg='#2d2d2d', fg='white').pack(pady=(20,5))
        scale_font = tk.Scale(tab_appearance, from_=8, to=30, orient=tk.HORIZONTAL, 
                             bg='#2d2d2d', fg='white', font=('Arial', 10))
        scale_font.set(self.font_size)
        scale_font.pack(fill=tk.X, padx=20)
        
        tk.Label(tab_appearance, text="سمك الحدود:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        scale_border = tk.Scale(tab_appearance, from_=0, to=10, orient=tk.HORIZONTAL,
                               bg='#2d2d2d', fg='white', font=('Arial', 10))
        scale_border.set(self.border_width)
        scale_border.pack(fill=tk.X, padx=20)
        
        tk.Label(tab_appearance, text="تأثير الضغط:", bg='#2d2d2d', fg='white').pack(pady=(15,5))
        press_effect = tk.StringVar(value=self.press_effect)
        effect_combo = ttk.Combobox(tab_appearance, textvariable=press_effect,
                                   values=['none', 'scale', 'color', 'both'],
                                   state='readonly', font=('Arial', 11))
        effect_combo.pack(fill=tk.X, padx=20)
        
        # تبويب التأثيرات
        tab_effects = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(tab_effects, text="تأثيرات")
        
        glow_var = tk.BooleanVar(value=self.glow_enabled)
        chk_glow = tk.Checkbutton(tab_effects, text="تفعيل التوهج", variable=glow_var,
                                 bg='#2d2d2d', fg='white', font=('Arial', 11), selectcolor='#444')
        chk_glow.pack(pady=(20,5))
        
        def save():
            self.key_config['label'] = ent_label.get()
            self.key_config['bind'] = ent_bind.get()
            self.key_config['action_type'] = action_type.get()
            self.key_config['action_value'] = ent_action.get()
            self.key_config['font_size'] = scale_font.get()
            self.key_config['border_width'] = scale_border.get()
            self.key_config['press_effect'] = press_effect.get()
            self.key_config['glow_enabled'] = glow_var.get()
            
            # تحديث العرض
            self.label_text = ent_label.get()
            self.bind_key = ent_bind.get()
            self.font_size = scale_font.get()
            self.border_width = scale_border.get()
            self.press_effect = press_effect.get()
            self.glow_enabled = glow_var.get()
            
            self.label.configure(text=self.label_text, font=('Arial', self.font_size, 'bold'))
            self.configure(highlightthickness=self.border_width)
            
            if self.glow_enabled and not self.glow_frame:
                self.create_glow_effect()
            elif not self.glow_enabled and self.glow_frame:
                self.glow_frame.destroy()
                self.glow_frame = None
            
            # إعادة ربط المفتاح
            if self.app:
                self.app.refresh_key_bindings()
            
            dialog.destroy()
        
        tk.Button(dialog, text="💾 حفظ", command=save, bg='#4a9eff', fg='white', 
                 font=('Arial', 12, 'bold')).pack(pady=20)
    
    def change_color(self):
        """تغيير لون الزر"""
        color = colorchooser.askcolor(initialcolor=self.btn_color, title="اختر لون الزر")
        if color[1]:
            self.btn_color = color[1]
            self.key_config['color'] = color[1]
            self.configure(bg=self.btn_color)
            self.label.configure(bg=self.btn_color)
            self.original_color = self.btn_color
            # تحديث لون التمرير الافتراضي
            self.hover_color = self.lighten_color(self.btn_color, 20)
            self.key_config['hover_color'] = self.hover_color
    
    def change_pressed_color(self):
        """تغيير لون الضغط"""
        color = colorchooser.askcolor(initialcolor=self.pressed_color, title="اختر لون الضغط")
        if color[1]:
            self.pressed_color = color[1]
            self.key_config['pressed_color'] = color[1]
    
    def change_hover_color(self):
        """تغيير لون التمرير"""
        color = colorchooser.askcolor(initialcolor=self.hover_color, title="اختر لون التمرير")
        if color[1]:
            self.hover_color = color[1]
            self.key_config['hover_color'] = color[1]
    
    def change_size(self):
        """تغيير حجم الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("حجم الزر")
        dialog.geometry("300x200")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="العرض:", bg='#2d2d2d', fg='white', font=('Arial', 12)).pack(pady=10)
        scale_w = tk.Scale(dialog, from_=30, to=400, orient=tk.HORIZONTAL, 
                          bg='#2d2d2d', fg='white', font=('Arial', 10))
        scale_w.set(self.width)
        scale_w.pack(fill=tk.X, padx=30)
        
        tk.Label(dialog, text="الارتفاع:", bg='#2d2d2d', fg='white', font=('Arial', 12)).pack(pady=10)
        scale_h = tk.Scale(dialog, from_=30, to=400, orient=tk.HORIZONTAL,
                          bg='#2d2d2d', fg='white', font=('Arial', 10))
        scale_h.set(self.height)
        scale_h.pack(fill=tk.X, padx=30)
        
        def apply_size():
            new_w = scale_w.get()
            new_h = scale_h.get()
            self.configure(width=new_w, height=new_h)
            self.key_config['width'] = new_w
            self.key_config['height'] = new_h
            self.width = new_w
            self.height = new_h
            if self.glow_frame:
                self.glow_frame.place(x=-2, y=-2, width=new_w+4, height=new_h+4)
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply_size, bg='#4a9eff', fg='white', 
                 font=('Arial', 11, 'bold')).pack(pady=15)
    
    def edit_border(self):
        """تحرير حدود الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("حدود الزر")
        dialog.geometry("300x200")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="سمك الحدود:", bg='#2d2d2d', fg='white').pack(pady=10)
        scale_width = tk.Scale(dialog, from_=0, to=10, orient=tk.HORIZONTAL,
                              bg='#2d2d2d', fg='white')
        scale_width.set(self.border_width)
        scale_width.pack(fill=tk.X, padx=20)
        
        tk.Label(dialog, text="لون الحدود:", bg='#2d2d2d', fg='white').pack(pady=10)
        btn_color = tk.Button(dialog, text="اختر اللون", bg=self.border_color, fg='black',
                             command=lambda: self.choose_border_color(dialog, scale_width))
        btn_color.pack(pady=5)
        
        def apply():
            self.border_width = scale_width.get()
            self.configure(highlightthickness=self.border_width)
            self.key_config['border_width'] = self.border_width
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply, bg='#4a9eff', fg='white').pack(pady=10)
    
    def choose_border_color(self, dialog, scale):
        """اختيار لون الحدود"""
        color = colorchooser.askcolor(initialcolor=self.border_color, title="لون الحدود")
        if color[1]:
            self.border_color = color[1]
            self.configure(highlightbackground=self.border_color)
            self.key_config['border_color'] = self.border_color
    
    def edit_sensitivity(self):
        """تحرير حساسية الزر الفردية"""
        dialog = tk.Toplevel(self)
        dialog.title(f"حساسية الزر: {self.label_text}")
        dialog.geometry("350x200")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text=f"الحساسية الحالية: {self.sensitivity}", 
                bg='#2d2d2d', fg='#4a9eff', font=('Arial', 16, 'bold')).pack(pady=15)
        
        scale_sens = tk.Scale(dialog, from_=0.1, to=10.0, resolution=0.1,
                             orient=tk.HORIZONTAL, bg='#2d2d2d', fg='white', font=('Arial', 11),
                             length=300,
                             command=lambda v: sensitivity_label.configure(text=f"الحساسية: {v}"))
        scale_sens.set(self.sensitivity)
        scale_sens.pack(pady=10)
        
        sensitivity_label = tk.Label(dialog, text=f"الحساسية: {self.sensitivity}",
                                    bg='#2d2d2d', fg='white', font=('Arial', 14))
        sensitivity_label.pack(pady=10)
        
        # شرح الحساسية
        tk.Label(dialog, text="💡 الحساسية العالية = تنفيذ أسرع للإجراءات",
                bg='#2d2d2d', fg='#888888', font=('Arial', 9)).pack(pady=5)
        
        def apply_sensitivity():
            self.sensitivity = float(scale_sens.get())
            self.key_config['sensitivity'] = self.sensitivity
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply_sensitivity, bg='#4a9eff', fg='white', 
                 font=('Arial', 11, 'bold')).pack(pady=15)
    
    def edit_effects(self):
        """تحرير تأثيرات الزر"""
        dialog = tk.Toplevel(self)
        dialog.title("تأثيرات الزر")
        dialog.geometry("350x300")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="تأثير الضغط:", bg='#2d2d2d', fg='white', font=('Arial', 12, 'bold')).pack(pady=15)
        press_effect = tk.StringVar(value=self.press_effect)
        effect_combo = ttk.Combobox(dialog, textvariable=press_effect,
                                   values=['none', 'scale', 'color', 'both'],
                                   state='readonly', font=('Arial', 11))
        effect_combo.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(dialog, text="التوهج:", bg='#2d2d2d', fg='white', font=('Arial', 12, 'bold')).pack(pady=15)
        glow_var = tk.BooleanVar(value=self.glow_enabled)
        chk_glow = tk.Checkbutton(dialog, text="تفعيل التوهج", variable=glow_var,
                                 bg='#2d2d2d', fg='white', font=('Arial', 11), selectcolor='#444')
        chk_glow.pack(pady=5)
        
        tk.Label(dialog, text="لون التوهج:", bg='#2d2d2d', fg='white').pack(pady=5)
        btn_glow_color = tk.Button(dialog, text=self.glow_color, bg=self.glow_color, fg='black',
                                  command=lambda: self.choose_glow_color(dialog))
        btn_glow_color.pack(pady=5)
        
        def apply():
            self.press_effect = press_effect.get()
            self.glow_enabled = glow_var.get()
            self.key_config['press_effect'] = self.press_effect
            self.key_config['glow_enabled'] = self.glow_enabled
            
            if self.glow_enabled and not self.glow_frame:
                self.create_glow_effect()
            elif not self.glow_enabled and self.glow_frame:
                self.glow_frame.destroy()
                self.glow_frame = None
            
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply, bg='#4a9eff', fg='white').pack(pady=20)
    
    def choose_glow_color(self, dialog):
        """اختيار لون التوهج"""
        color = colorchooser.askcolor(initialcolor=self.glow_color, title="لون التوهج")
        if color[1]:
            self.glow_color = color[1]
            self.key_config['glow_color'] = self.glow_color
            if self.glow_frame:
                self.glow_frame.configure(bg=self.glow_color)
    
    def edit_tooltip(self):
        """تحرير نص التلميح"""
        dialog = tk.Toplevel(self)
        dialog.title("تلميح الزر")
        dialog.geometry("350x150")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="نص التلميح (Tooltip):", bg='#2d2d2d', fg='white').pack(pady=10)
        ent_tooltip = tk.Entry(dialog, bg='#444', fg='white', font=('Arial', 11))
        ent_tooltip.insert(0, self.tooltip_text)
        ent_tooltip.pack(fill=tk.X, padx=20)
        
        def apply():
            self.tooltip_text = ent_tooltip.get()
            self.key_config['tooltip'] = self.tooltip_text
            dialog.destroy()
        
        tk.Button(dialog, text="حفظ", command=apply, bg='#4a9eff', fg='white').pack(pady=15)
    
    def delete_button(self):
        """حذف الزر"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الزر؟"):
            if self.app:
                if self in self.app.buttons:
                    self.app.buttons.remove(self)
                self.destroy()
                self.app.refresh_key_bindings()
    
    def on_hover_enter(self, event):
        """عند مرور الماوس"""
        if not self.is_pressed and self.app.edit_mode:
            self.configure(bg=self.hover_color)
            self.label.configure(bg=self.hover_color)
        
        # إظهار Tooltip
        if self.tooltip_text:
            self.show_tooltip()
    
    def on_hover_leave(self, event):
        """عند مغادرة الماوس"""
        if not self.is_pressed:
            self.configure(bg=self.original_color)
            self.label.configure(bg=self.original_color)
        
        # إخفاء Tooltip
        self.hide_tooltip()
    
    def show_tooltip(self):
        """إظهار التلميح"""
        x = self.winfo_rootx() + self.width // 2
        y = self.winfo_rooty() - 30
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.tooltip_text, bg='#ffffcc', fg='#000000',
                        relief=tk.SOLID, borderwidth=1, font=('Arial', 9))
        label.pack()
    
    def hide_tooltip(self):
        """إخفاء التلميح"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def on_mouse_wheel(self, event):
        """تغيير الحجم بالماوس"""
        if self.app.edit_mode and event.state & 0x4:  # Ctrl pressed
            delta = 1 if event.delta > 0 else -1
            new_size = self.width + delta * 5
            if 30 <= new_size <= 400:
                self.configure(width=new_size, height=new_size)
                self.key_config['width'] = new_size
                self.key_config['height'] = new_size
                self.width = new_size
                self.height = new_size
    
    @staticmethod
    def lighten_color(color, amount):
        """تفتيح اللون"""
        try:
            # تحويل hex إلى RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            # تفتيح
            r = min(255, r + amount)
            g = min(255, g + amount)
            b = min(255, b + amount)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color


class KeyboardMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Mapper Pro - النسخة الاحترافية")
        self.root.geometry("1400x900")
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
        self.selected_button = None
        
        # إعدادات متقدمة
        self.settings = {
            "global_sensitivity": 1.0,
            "grid_snap": 10,
            "show_grid": False,
            "default_width": 80,
            "default_height": 80,
            "default_color": "#4a9eff",
            "pressed_color": "#00aa00",
            "hover_color": "#6ab0ff",
            "theme": "dark",
            "animation_enabled": True,
            "sound_enabled": False
        }
        
        # تاريخ الإجراءات للـ Undo/Redo
        self.action_history = []
        self.redo_stack = []
        
        self.setup_ui()
        self.load_default_buttons()
        self.bind_global_keys()
        self.start_auto_save()
    
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
                Key.up: 'up',
                Key.down: 'down',
                Key.left: 'left',
                Key.right: 'right',
                Key.f1: 'f1',
                Key.f2: 'f2',
                Key.f3: 'f3',
                Key.f4: 'f4',
                Key.f5: 'f5',
                Key.f6: 'f6',
                Key.f7: 'f7',
                Key.f8: 'f8',
                Key.f9: 'f9',
                Key.f10: 'f10',
                Key.f11: 'f11',
                Key.f12: 'f12',
            }
            return key_map.get(key, str(key).replace('Key.', ''))
    
    def setup_ui(self):
        """إعداد واجهة المستخدم - سايدبار فقط"""
        # الشريط الجانبي للإعدادات
        self.sidebar = tk.Frame(self.root, width=320, bg="#2d2d2d")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # منطقة الأزرار القابلة للسحب
        self.canvas_area = tk.Frame(self.root, bg="#1e1e1e")
        self.canvas_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas مع شريط تمرير
        self.keyboard_canvas = tk.Canvas(self.canvas_area, bg="#1e1e1e", highlightthickness=0)
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(self.canvas_area, orient=tk.VERTICAL, command=self.keyboard_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keyboard_canvas.configure(yscrollcommand=scrollbar.set)
        
        # ربط العجلة
        self.keyboard_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        self.build_sidebar()
        self.build_status_bar()
    
    def on_mousewheel(self, event):
        """التمرير بالماوس"""
        self.keyboard_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def build_status_bar(self):
        """بناء شريط الحالة"""
        self.status_bar = tk.Frame(self.root, bg="#2d2d2d", height=30)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(self.status_bar, text="جاهز - وضع التعديل مفعل", 
                                    bg="#2d2d2d", fg="#aaaaaa", font=('Arial', 9))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.stats_label = tk.Label(self.status_bar, text="أزرار: 0", 
                                   bg="#2d2d2d", fg="#888888", font=('Arial', 9))
        self.stats_label.pack(side=tk.RIGHT, padx=10)
    
    def build_sidebar(self):
        """بناء الشريط الجانبي"""
        # عنوان
        lbl_title = tk.Label(self.sidebar, text="⚙️ لوحة التحكم", 
                            bg="#2d2d2d", fg="#ffffff", 
                            font=("Arial", 16, "bold"))
        lbl_title.pack(pady=15)
        
        # إنشاء Canvas للشريط الجانبي مع scrollbar
        sidebar_canvas = tk.Canvas(self.sidebar, bg="#2d2d2d", highlightthickness=0)
        sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sidebar_scrollbar = ttk.Scrollbar(self.sidebar, orient=tk.VERTICAL, command=sidebar_canvas.yview)
        sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
        
        # Frame داخلي للمحتوى
        self.sidebar_content = tk.Frame(sidebar_canvas, bg="#2d2d2d")
        sidebar_canvas.create_window((0, 0), window=self.sidebar_content, anchor='nw', width=290)
        
        self.sidebar_content.bind("<Configure>", lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))
        
        # زر إضافة زر جديد
        btn_add = tk.Button(self.sidebar_content, text="➕ إضافة زر جديد", 
                           command=self.add_new_button, 
                           bg="#4a9eff", fg="white", 
                           font=("Arial", 12, "bold"),
                           height=2)
        btn_add.pack(fill=tk.X, padx=15, pady=10)
    
    def add_new_button(self):
        """إضافة زر جديد"""
        import time
        config = {
            'id': f"btn_{int(time.time() * 1000)}",
            'label': 'زر جديد',
            'bind': '',
            'action_type': 'key',
            'action_value': '',
            'x': 50,
            'y': 50,
            'width': 80,
            'height': 80,
            'color': '#4a9eff',
            'sensitivity': 1.0,
            'press_effect': 'both',
            'glow_enabled': False
        }
        self.create_button_widget(config)
        
        # فاصل
        ttk.Separator(self.sidebar_content, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم وضع التعديل
        lbl_edit = tk.Label(self.sidebar_content, text="📝 وضع التعديل", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_edit.pack(anchor='w', padx=15, pady=(10,5))
        
        self.btn_edit = tk.Button(self.sidebar_content, text="✅ مفعل (Ctrl+E)", 
                                 command=self.toggle_edit_mode, 
                                 bg="#00aa00", fg="white",
                                 font=("Arial", 10))
        self.btn_edit.pack(fill=tk.X, padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar_content, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الحساسية العامة
        lbl_sens = tk.Label(self.sidebar_content, text="🎯 الحساسية العامة", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_sens.pack(anchor='w', padx=15, pady=(10,5))
        
        self.scale_sensitivity = tk.Scale(self.sidebar_content, from_=0.1, to=5.0, 
                                         resolution=0.1, orient=tk.HORIZONTAL,
                                         label="قيمة الحساسية",
                                         bg="#2d2d2d", fg="white",
                                         highlightthickness=0,
                                         font=("Arial", 9))
        self.scale_sensitivity.set(1.0)
        self.scale_sensitivity.pack(fill=tk.X, padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar_content, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الشبكة
        lbl_grid = tk.Label(self.sidebar_content, text="📐 ضبط الشبكة", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_grid.pack(anchor='w', padx=15, pady=(10,5))
        
        self.scale_grid = tk.Scale(self.sidebar_content, from_=5, to=50, 
                                  orient=tk.HORIZONTAL,
                                  label="حجم الشبكة",
                                  bg="#2d2d2d", fg="white",
                                  highlightthickness=0,
                                  font=("Arial", 9),
                                  command=self.update_grid)
        self.scale_grid.set(10)
        self.scale_grid.pack(fill=tk.X, padx=15, pady=5)
        
        show_grid_var = tk.BooleanVar(value=False)
        chk_show_grid = tk.Checkbutton(self.sidebar_content, text="إظهار الشبكة", 
                                      variable=show_grid_var, bg="#2d2d2d", fg="white",
                                      selectcolor="#444", command=self.toggle_grid_display)
        chk_show_grid.pack(padx=15, pady=5)
        
        # فاصل
        ttk.Separator(self.sidebar_content, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم الإجراءات السريعة
        lbl_actions = tk.Label(self.sidebar_content, text="⚡ إجراءات سريعة", 
                              bg="#2d2d2d", fg="#aaaaaa",
                              font=("Arial", 11, "bold"))
        lbl_actions.pack(anchor='w', padx=15, pady=(10,5))
        
        btn_select_all = tk.Button(self.sidebar_content, text="📋 تحديد الكل", 
                                  command=self.select_all_buttons, 
                                  bg="#555", fg="white")
        btn_select_all.pack(fill=tk.X, padx=15, pady=3)
        
        btn_align = tk.Button(self.sidebar_content, text="📐 محاذاة تلقائية", 
                             command=self.auto_align_buttons, 
                             bg="#555", fg="white")
        btn_align.pack(fill=tk.X, padx=15, pady=3)
        
        # فاصل
        ttk.Separator(self.sidebar_content, orient='horizontal').pack(fill=tk.X, padx=15, pady=10)
        
        # قسم حفظ وتحميل
        lbl_save = tk.Label(self.sidebar_content, text="💾 حفظ وتحميل", 
                           bg="#2d2d2d", fg="#aaaaaa",
                           font=("Arial", 11, "bold"))
        lbl_save.pack(anchor='w', padx=15, pady=(10,5))
        
        btn_save = tk.Button(self.sidebar_content, text="💾 حفظ التخطيط", 
                            command=self.save_layout, 
                            bg="#444", fg="white")
        btn_save.pack(fill=tk.X, padx=15, pady=3)
        
        btn_load = tk.Button(self.sidebar_content, text="📂 تحميل تخطيط", 
                            command=self.load_layout, 
                            bg="#444", fg="white")
        btn_load.pack(fill=tk.X, padx=15, pady=3)
        
        btn_export = tk.Button(self.sidebar_content, text="📤 تصدير كصورة", 
                              command=self.export_as_image, 
                              bg="#444", fg="white")
        btn_export.pack(fill=tk.X, padx=15, pady=3)
        
        btn_clear = tk.Button(self.sidebar_content, text="🗑️ مسح الكل", 
                             command=self.clear_all_buttons, 
                             bg="#aa0000", fg="white")
        btn_clear.pack(fill=tk.X, padx=15, pady=5)
        
        # معلومات
        lbl_info = tk.Label(self.sidebar_content, 
                           text="💡 انقر بالزر الأيمن على أي زر\nللحصول على قائمة الإجراءات الكاملة",
                           bg="#2d2d2d", fg="#888888",
                           font=("Arial", 9),
                           justify='center')
        lbl_info.pack(side=tk.BOTTOM, pady=20)
    
    def toggle_grid_display(self):
        """تبديل عرض الشبكة"""
        self.settings["show_grid"] = not self.settings["show_grid"]
        if self.settings["show_grid"]:
            self.draw_grid()
        else:
            self.keyboard_canvas.delete("grid")
    
    def draw_grid(self):
        """رسم الشبكة"""
        self.keyboard_canvas.delete("grid")
        grid_size = self.settings.get("grid_snap", 10)
        width = self.keyboard_canvas.winfo_width()
        height = self.keyboard_canvas.winfo_height()
        
        for x in range(0, width, grid_size):
            self.keyboard_canvas.create_line(x, 0, x, height, fill="#333333", tags="grid")
        for y in range(0, height, grid_size):
            self.keyboard_canvas.create_line(0, y, width, y, fill="#333333", tags="grid")
    
    def select_all_buttons(self):
        """تحديد جميع الأزرار"""
        for btn in self.buttons:
            btn.configure(highlightbackground="#ffff00", highlightthickness=3)
        self.update_status(f"تم تحديد {len(self.buttons)} زر")
    
    def auto_align_buttons(self):
        """محاذاة تلقائية للأزرار"""
        grid_size = self.settings.get("grid_snap", 10)
        x_pos = 50
        y_pos = 50
        max_per_row = 8
        
        for i, btn in enumerate(self.buttons):
            btn.place(x=x_pos, y=y_pos)
            btn.key_config['x'] = x_pos
            btn.key_config['y'] = y_pos
            
            x_pos += btn.width + 20
            
            if (i + 1) % max_per_row == 0:
                x_pos = 50
                y_pos += 100
        
        self.update_status("تمت المحاذاة التلقائية")
    
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
            {'label': 'Shift', 'bind': 'shift', 'x': 150, 'y': 500, 'width': 120, 'height': 60, 'color': '#9f4aff'},
            {'label': 'Ctrl', 'bind': 'control', 'x': 50, 'y': 500, 'width': 80, 'height': 60, 'color': '#ff4a9f'},
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
                'sensitivity': 1.0,
                'press_effect': 'both',
                'glow_enabled': False
            }
            self.create_button_widget(config)
    
    def create_button_widget(self, config):
        """إنشاء زر قابل للسحب"""
        btn = DraggableButton(self.keyboard_canvas, config, self)
        btn.place(x=config['x'], y=config['y'], width=config['width'], height=config['height'])
        self.buttons.append(btn)
        self.refresh_key_bindings()
        self.update_stats()
    
    def refresh_key_bindings(self):
        """تحديث ربط المفاتيح"""
        self.key_bindings.clear()
        for btn in self.buttons:
            btn.setup_key_binding()
    
    def trigger_button_action(self, config, is_press=True):
        """تفعيل إجراء الزر"""
        if not self.layout_active:
            return
        
        sensitivity = config.get('sensitivity', 1.0) * self.settings.get('global_sensitivity', 1.0)
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
        elif action_type == 'combo':
            if is_press:
                self.execute_combo_action(action_value)
    
    def execute_key_action(self, key, is_press, sensitivity):
        """تنفيذ إجراء مفتاح"""
        if not PYNPUT_AVAILABLE or not self.kb_controller:
            return
        
        try:
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
                'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
                'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
                'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            }
            
            key_obj = special_keys.get(key, key if len(key) == 1 else None)
            
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
        print(f"تشغيل الماكرو: {macro_name}")
    
    def execute_combo_action(self, combo_string):
        """تنفيذ مجموعة مفاتيح"""
        if not PYNPUT_AVAILABLE or not self.kb_controller:
            return
        
        keys = combo_string.split('+')
        # ضغط جميع المفاتيح
        for key in keys:
            key = key.strip().lower()
            special_keys = {
                'ctrl': Key.ctrl, 'shift': Key.shift, 'alt': Key.alt,
                'space': Key.space, 'enter': Key.enter, 'tab': Key.tab
            }
            key_obj = special_keys.get(key, key if len(key) == 1 else None)
            if key_obj:
                self.kb_controller.press(key_obj)
        
        # رفع جميع المفاتيح
        for key in reversed(keys):
            key = key.strip().lower()
            special_keys = {
                'ctrl': Key.ctrl, 'shift': Key.shift, 'alt': Key.alt,
                'space': Key.space, 'enter': Key.enter, 'tab': Key.tab
            }
            key_obj = special_keys.get(key, key if len(key) == 1 else None)
            if key_obj:
                self.kb_controller.release(key_obj)
    
    def clear_all_buttons(self):
        """مسح جميع الأزرار"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من مسح جميع الأزرار؟"):
            for btn in self.buttons[:]:
                btn.destroy()
            self.buttons.clear()
            self.key_bindings.clear()
            self.update_stats()
            self.update_status("تم مسح جميع الأزرار")
    
    def toggle_edit_mode(self):
        """تبديل وضع التعديل"""
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            self.btn_edit.configure(text="✅ مفعل (Ctrl+E)", bg="#00aa00")
            self.update_status("وضع التعديل: مفعل - يمكنك سحب وتحريك الأزرار")
        else:
            self.btn_edit.configure(text="❌ معطل (Ctrl+E)", bg="#aa0000")
            self.update_status("وضع التعديل: معطل - الوضع النشط مفعل")
        
        # إعادة تعيين ألوان الحدود
        for btn in self.buttons:
            btn.configure(highlightbackground=btn.border_color, highlightthickness=btn.border_width)
    
    def bind_global_keys(self):
        """ربط المفاتيح العامة"""
        self.root.bind("<Control-e>", lambda e: self.toggle_edit_mode())
        self.root.bind("<Control-s>", lambda e: self.save_layout())
        self.root.bind("<Control-o>", lambda e: self.load_layout())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
    
    def update_grid(self, val):
        """تحديث حجم الشبكة"""
        grid_size = int(val)
        self.settings["grid_snap"] = grid_size
        if self.settings.get("show_grid", False):
            self.draw_grid()
    
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
            self.update_status(f"تم الحفظ في: {filename}")
    
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
                self.update_status(f"تم التحميل من: {filename}")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
    
    def export_as_image(self):
        """تصدير التخطيط كصورة"""
        messagebox.showinfo("معلومة", "هذه الميزة تتطلب مكتبات إضافية مثل PIL/Pillow")
    
    def update_stats(self):
        """تحديث إحصائيات الأزرار"""
        count = len(self.buttons)
        self.stats_label.configure(text=f"أزرار: {count}")
    
    def update_status(self, message):
        """تحديث شريط الحالة"""
        self.status_label.configure(text=message)
    
    def start_auto_save(self):
        """بدء الحفظ التلقائي"""
        def auto_save():
            # يمكن تطوير هذه الوظيفة للحفظ التلقائي الدوري
            self.root.after(60000, auto_save)  # كل دقيقة
        
        self.root.after(60000, auto_save)
    
    def undo(self):
        """تراجع"""
        if self.action_history:
            last_action = self.action_history.pop()
            self.redo_stack.append(last_action)
            self.update_status("تم التراجع")
    
    def redo(self):
        """إعادة"""
        if self.redo_stack:
            last_redo = self.redo_stack.pop()
            self.action_history.append(last_redo)
            self.update_status("تمت الإعادة")
    
    def delete_selected(self):
        """حذف المحدد"""
        if self.edit_mode and self.selected_button:
            self.selected_button.delete_button()
            self.selected_button = None


if __name__ == "__main__":
    root = tk.Tk()
    
    # محاولة جعل النافذة فوق الجميع
    try:
        root.attributes('-topmost', True)
    except:
        pass
    
    app = KeyboardMapperApp(root)
    
    # بدء حلقة التحديث
    def update_loop():
        # تحديثات دورية إذا لزم الأمر
        root.after(100, update_loop)
    
    root.after(100, update_loop)
    root.mainloop()
