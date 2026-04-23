#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard Mapper Pro V3 - النسخة الاحترافية المتقدمة
مع تتبع شامل للضغطات والحركات والنقرات
نافذة واحدة فقط مع سايدبار، أزرار قابلة للسحب، قائمة سياق متقدمة
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, Menu, scrolledtext
import json
import os
import sys
import threading
import time
import random
from datetime import datetime
from collections import deque
import hashlib

# محاولة استيراد مكتبات المحاكاة والتتبع
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, Controller as KeyboardController, Listener as KeyboardListener
    from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

if not PYAUTOGUI_AVAILABLE or not PYNPUT_AVAILABLE:
    print("تنبيه: بعض المكتبات (pyautogui, pynput) غير متوفرة.")


class InputMonitor:
    """مراقب متقدم لجميع مدخلات المستخدم"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.events_log = deque(maxlen=1000)
        self.key_states = {}
        self.mouse_position = (0, 0)
        self.click_count = {'left': 0, 'right': 0, 'middle': 0}
        self.key_press_count = {}
        self.monitoring = False
        self.keyboard_listener = None
        self.mouse_listener = None
        
    def start(self):
        """بدء المراقبة"""
        if PYNPUT_AVAILABLE and not self.monitoring:
            self.monitoring = True
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.mouse_listener = mouse.Listener(
                on_move=self.on_mouse_move,
                on_click=self.on_mouse_click,
                on_scroll=self.on_mouse_scroll
            )
            self.keyboard_listener.start()
            self.mouse_listener.start()
            print("✓ بدء مراقبة المدخلات")
    
    def stop(self):
        """إيقاف المراقبة"""
        if self.monitoring:
            self.monitoring = False
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()
            print("✓ إيقاف مراقبة المدخلات")
    
    def on_key_press(self, key):
        """عند ضغط مفتاح"""
        try:
            key_name = self.get_key_name(key)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            event_data = {
                'type': 'key_press',
                'key': key_name,
                'timestamp': timestamp,
                'action': 'press'
            }
            
            self.events_log.append(event_data)
            self.key_states[key_name] = True
            self.key_press_count[key_name] = self.key_press_count.get(key_name, 0) + 1
            
            if self.callback:
                self.callback(event_data)
                
        except Exception as e:
            pass
    
    def on_key_release(self, key):
        """عند رفع مفتاح"""
        try:
            key_name = self.get_key_name(key)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            event_data = {
                'type': 'key_release',
                'key': key_name,
                'timestamp': timestamp,
                'action': 'release'
            }
            
            self.events_log.append(event_data)
            self.key_states[key_name] = False
            
            if self.callback:
                self.callback(event_data)
                
        except Exception as e:
            pass
    
    def on_mouse_move(self, x, y):
        """عند تحريك الماوس"""
        self.mouse_position = (x, y)
        
        event_data = {
            'type': 'mouse_move',
            'x': x,
            'y': y,
            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
        }
        
        # إضافة حدث الحركة كل 100ms فقط لتجنب الإغراق
        if len(self.events_log) == 0 or self.events_log[-1].get('type') != 'mouse_move' or \
           time.time() - float(self.events_log[-1].get('timestamp', '0').split(':')[2]) > 0.1:
            self.events_log.append(event_data)
            
        if self.callback:
            self.callback(event_data)
    
    def on_mouse_click(self, x, y, button, pressed):
        """عند النقر بالماوس"""
        try:
            button_name = str(button).replace('Button.', '').lower()
            action = 'press' if pressed else 'release'
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if pressed:
                self.click_count[button_name] = self.click_count.get(button_name, 0) + 1
            
            event_data = {
                'type': 'mouse_click',
                'button': button_name,
                'x': x,
                'y': y,
                'action': action,
                'timestamp': timestamp
            }
            
            self.events_log.append(event_data)
            
            if self.callback:
                self.callback(event_data)
                
        except Exception as e:
            pass
    
    def on_mouse_scroll(self, x, y, dx, dy):
        """عند التمرير"""
        event_data = {
            'type': 'mouse_scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
        }
        
        self.events_log.append(event_data)
        
        if self.callback:
            self.callback(event_data)
    
    def get_key_name(self, key):
        """الحصول على اسم المفتاح"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key).replace('Key.', '')
        except:
            return str(key)
    
    def get_statistics(self):
        """الحصول على إحصائيات المدخلات"""
        return {
            'total_events': len(self.events_log),
            'key_presses': sum(self.key_press_count.values()),
            'mouse_clicks': sum(self.click_count.values()),
            'active_keys': [k for k, v in self.key_states.items() if v],
            'mouse_position': self.mouse_position,
            'top_keys': sorted(self.key_press_count.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def export_log(self, filename):
        """تصدير سجل الأحداث"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(list(self.events_log), f, indent=2, ensure_ascii=False)


class DraggableButton(tk.Frame):
    """زر قابل للسحب مع قائمة سياق متقدمة وتتبع كامل"""
    
    def __init__(self, parent, key_config, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.key_config = key_config
        self.is_pressed = False
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.animation_id = None
        self.press_time = None
        self.press_count = 0
        
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
        self.press_effect = key_config.get('press_effect', 'scale')
        self.glow_enabled = key_config.get('glow_enabled', False)
        self.glow_color = key_config.get('glow_color', '#00ff00')
        
        # تكوين الواجهة
        self.configure(bg=self.btn_color, width=self.width, height=self.height)
        self.configure(highlightbackground=self.border_color, highlightthickness=self.border_width)
        
        # تأثير التوهج
        self.glow_frame = None
        if self.glow_enabled:
            self.create_glow_effect()
        
        # تسمية الزر
        self.label = tk.Label(self, text=self.label_text, bg=self.btn_color, 
                             fg='white', font=('Arial', self.font_size, 'bold'))
        self.label.pack(expand=True)
        
        # عداد الضغطات
        self.count_label = tk.Label(self, text='', bg=self.btn_color, fg='yellow', 
                                   font=('Arial', 8))
        self.count_label.place(x=5, y=5)
        
        # ربط الأحداث
        self.bind_events()
        
        # حالة الضغط
        self.original_color = self.btn_color
        self.pressed_color = key_config.get('pressed_color', '#00aa00')
        self.hover_color = key_config.get('hover_color', self.lighten_color(self.btn_color, 20))
        
        # Tooltip
        self.tooltip = None
        self.tooltip_window = None
        
        # ربط المفتاح
        self.setup_key_binding()
        self.update_press_count_display()
    
    def bind_events(self):
        """ربط جميع الأحداث"""
        events = [
            "<Button-1>", "<ButtonRelease-1>", "<B1-Motion>",
            "<Button-3>", "<Enter>", "<Leave>", "<MouseWheel>"
        ]
        for event in events:
            self.bind(event, self.handle_event)
            self.label.bind(event, self.handle_event)
    
    def handle_event(self, event):
        """معالجة موحدة للأحداث"""
        if event.type == '2':  # Button-1
            self.on_left_click(event)
        elif event.type == '5':  # ButtonRelease-1
            self.on_left_release(event)
        elif event.type == '6':  # B1-Motion
            self.on_drag(event)
        elif event.type == '4':  # Button-3
            self.show_context_menu(event)
        elif event.type == '7':  # Enter
            self.on_hover_enter(event)
        elif event.type == '8':  # Leave
            self.on_hover_leave(event)
        elif event.type == '31':  # MouseWheel
            self.on_mouse_wheel(event)
    
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
        """عند النقر الأيسر - تفعيل فوري مع تتبع"""
        self.is_pressed = True
        self.dragging = False
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.press_time = time.time()
        self.press_count += 1
        
        # تحديث عداد الضغطات
        self.update_press_count_display()
        
        # تأثير الضغط
        self.apply_press_effect()
        
        # تسجيل الحدث
        if self.app and self.app.input_monitor:
            self.app.input_monitor.events_log.append({
                'type': 'button_press',
                'button_id': self.key_config.get('id'),
                'button_label': self.label_text,
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'x': event.x_root,
                'y': event.y_root
            })
        
        # تفعيل الإجراء فوراً
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=True)
    
    def on_left_release(self, event):
        """عند رفع الإصبع"""
        self.is_pressed = False
        self.dragging = False
        
        # حساب مدة الضغط
        if self.press_time:
            duration = time.time() - self.press_time
            if self.app and self.app.input_monitor:
                self.app.input_monitor.events_log.append({
                    'type': 'button_release',
                    'button_id': self.key_config.get('id'),
                    'button_label': self.label_text,
                    'duration': round(duration, 3),
                    'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
                })
            self.press_time = None
        
        # إعادة الزر لحالته الأصلية
        self.release_effect()
        
        if self.app and not self.app.edit_mode:
            self.app.trigger_button_action(self.key_config, is_press=False)
    
    def apply_press_effect(self):
        """تطبيق تأثير الضغط"""
        if self.press_effect == 'scale':
            self.scale_animation(0.9)
        elif self.press_effect == 'color':
            self.configure(bg=self.pressed_color)
            self.label.configure(bg=self.pressed_color)
        elif self.press_effect == 'both':
            self.scale_animation(0.9)
            self.configure(bg=self.pressed_color)
            self.label.configure(bg=self.pressed_color)
    
    def release_effect(self):
        """إعادة التأثير للحالة الأصلية"""
        if self.press_effect in ['scale', 'both']:
            self.scale_animation(1.0)
        if self.press_effect in ['color', 'both']:
            self.configure(bg=self.original_color)
            self.label.configure(bg=self.original_color)
    
    def scale_animation(self, scale_factor):
        """تأثير التحجيم المتحرك"""
        current_width = int(self.width * scale_factor)
        current_height = int(self.height * scale_factor)
        self.configure(width=current_width, height=current_height)
    
    def on_drag(self, event):
        """السحب والتحريك مع تتبع الحركة"""
        if self.app.edit_mode:
            self.dragging = True
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
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
            
            # تسجيل حركة السحب
            if self.app and self.app.input_monitor:
                self.app.input_monitor.events_log.append({
                    'type': 'button_drag',
                    'button_id': self.key_config.get('id'),
                    'from_x': current_x,
                    'from_y': current_y,
                    'to_x': new_x,
                    'to_y': new_y,
                    'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
                })
    
    def show_context_menu(self, event):
        """إظهار قائمة السياق بالزر الأيمن"""
        context_menu = Menu(self, tearoff=0, bg='#2d2d2d', fg='white', font=('Arial', 10))
        
        context_menu.add_command(label="✂️ قص", command=self.cut_button, font=('Arial', 10, 'bold'))
        context_menu.add_command(label="📋 نسخ", command=self.copy_button, font=('Arial', 10))
        context_menu.add_command(label="📌 لصق", command=self.paste_button, font=('Arial', 10))
        context_menu.add_separator()
        context_menu.add_command(label="⚙️ خصائص متقدمة", command=self.edit_properties, font=('Arial', 10, 'bold'))
        context_menu.add_command(label="🎨 تغيير اللون", command=self.change_color, font=('Arial', 10))
        context_menu.add_command(label="🖌️ لون الضغط", command=self.change_pressed_color, font=('Arial', 10))
        context_menu.add_command(label="📏 تغيير الحجم", command=self.change_size, font=('Arial', 10))
        context_menu.add_command(label="🎯 حساسية فردية", command=self.edit_sensitivity, font=('Arial', 10))
        context_menu.add_command(label="💡 تأثيرات", command=self.edit_effects, font=('Arial', 10))
        context_menu.add_command(label="📊 إحصائيات الزر", command=self.show_button_stats, font=('Arial', 10))
        context_menu.add_separator()
        context_menu.add_command(label="🔄 تكرار", command=self.duplicate_button, font=('Arial', 10))
        context_menu.add_command(label="🗑️ حذف", command=self.delete_button, foreground='red', font=('Arial', 10, 'bold'))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def update_press_count_display(self):
        """تحديث عرض عداد الضغطات"""
        if self.press_count > 0:
            self.count_label.configure(text=f"#{self.press_count}")
        else:
            self.count_label.configure(text='')
    
    def show_button_stats(self):
        """عرض إحصائيات الزر"""
        stats_window = tk.Toplevel(self)
        stats_window.title(f"إحصائيات: {self.label_text}")
        stats_window.geometry("350x250")
        stats_window.configure(bg='#2d2d2d')
        
        tk.Label(stats_window, text=f"📊 إحصائيات الزر: {self.label_text}", 
                bg='#2d2d2d', fg='white', font=('Arial', 14, 'bold')).pack(pady=15)
        
        stats_frame = tk.Frame(stats_window, bg='#3d3d3d')
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        stats = [
            ("عدد الضغطات:", str(self.press_count)),
            ("المفتاح المرتبط:", self.bind_key or "لا يوجد"),
            ("الحساسية:", str(self.sensitivity)),
            ("اللون:", self.btn_color),
            ("الحجم:", f"{self.width}x{self.height}"),
        ]
        
        for i, (label, value) in enumerate(stats):
            tk.Label(stats_frame, text=label, bg='#3d3d3d', fg='#aaa', 
                    font=('Arial', 11)).grid(row=i, column=0, sticky='w', pady=5)
            tk.Label(stats_frame, text=value, bg='#3d3d3d', fg='white', 
                    font=('Arial', 11, 'bold')).grid(row=i, column=1, sticky='w', padx=10, pady=5)
        
        tk.Button(stats_window, text="إغلاق", command=stats_window.destroy, 
                 bg='#4a9eff', fg='white').pack(pady=10)
    
    # ... باقي الدوال (cut_button, copy_button, paste_button, edit_properties, إلخ)
    # للاختصار، سأضيفها في النسخة الكاملة
    
    def cut_button(self):
        self.app.clipboard_data = self.key_config.copy()
        self.delete_button()
    
    def copy_button(self):
        self.app.clipboard_data = self.key_config.copy()
    
    def paste_button(self):
        if self.app.clipboard_data:
            new_config = self.app.clipboard_data.copy()
            new_config['id'] = f"btn_{int(time.time() * 1000)}"
            new_config['x'] = self.key_config['x'] + 20
            new_config['y'] = self.key_config['y'] + 20
            new_config['label'] = f"{new_config.get('label', 'Copy')} (2)"
            self.app.create_button_widget(new_config)
    
    def duplicate_button(self):
        self.copy_button()
        self.paste_button()
    
    def delete_button(self):
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الزر؟"):
            if self.bind_key and self.app:
                self.app.key_bindings.pop(self.bind_key.lower(), None)
            self.app.buttons.remove(self.key_config)
            self.destroy()
    
    def change_color(self):
        color = colorchooser.askcolor(initialcolor=self.btn_color, title="اختر لون الزر")
        if color[1]:
            self.btn_color = color[1]
            self.key_config['color'] = color[1]
            self.configure(bg=self.btn_color)
            self.label.configure(bg=self.btn_color)
            self.original_color = self.btn_color
    
    def change_pressed_color(self):
        color = colorchooser.askcolor(initialcolor=self.pressed_color, title="اختر لون الضغط")
        if color[1]:
            self.pressed_color = color[1]
            self.key_config['pressed_color'] = color[1]
    
    def change_size(self):
        dialog = tk.Toplevel(self)
        dialog.title("حجم الزر")
        dialog.geometry("300x200")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="العرض:", bg='#2d2d2d', fg='white').pack(pady=10)
        scale_w = tk.Scale(dialog, from_=50, to=300, orient=tk.HORIZONTAL, 
                          bg='#2d2d2d', fg='white')
        scale_w.set(self.width)
        scale_w.pack()
        
        tk.Label(dialog, text="الارتفاع:", bg='#2d2d2d', fg='white').pack(pady=10)
        scale_h = tk.Scale(dialog, from_=50, to=300, orient=tk.HORIZONTAL,
                          bg='#2d2d2d', fg='white')
        scale_h.set(self.height)
        scale_h.pack()
        
        def apply_size():
            self.width = scale_w.get()
            self.height = scale_h.get()
            self.key_config['width'] = self.width
            self.key_config['height'] = self.height
            self.configure(width=self.width, height=self.height)
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply_size, bg='#4a9eff', 
                 fg='white').pack(pady=10)
    
    def edit_sensitivity(self):
        dialog = tk.Toplevel(self)
        dialog.title("حساسية الزر")
        dialog.geometry("350x150")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="الحساسية (0.1 - 5.0):", 
                bg='#2d2d2d', fg='white', font=('Arial', 12)).pack(pady=10)
        
        scale = tk.Scale(dialog, from_=0.1, to=5.0, resolution=0.1, 
                        orient=tk.HORIZONTAL, bg='#2d2d2d', fg='white',
                        length=300)
        scale.set(self.sensitivity)
        scale.pack()
        
        def apply():
            self.sensitivity = scale.get()
            self.key_config['sensitivity'] = self.sensitivity
            messagebox.showinfo("تم", f"تم تعيين الحساسية إلى: {self.sensitivity}")
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply, bg='#4a9eff', 
                 fg='white').pack(pady=10)
    
    def edit_effects(self):
        dialog = tk.Toplevel(self)
        dialog.title("التأثيرات")
        dialog.geometry("350x250")
        dialog.configure(bg='#2d2d2d')
        
        tk.Label(dialog, text="نوع تأثير الضغط:", 
                bg='#2d2d2d', fg='white', font=('Arial', 12)).pack(pady=10)
        
        effect_var = tk.StringVar(value=self.press_effect)
        for effect in ['none', 'scale', 'color', 'both']:
            tk.Radiobutton(dialog, text=effect.upper(), variable=effect_var, 
                          value=effect, bg='#2d2d2d', fg='white',
                          selectcolor='#444').pack(anchor='w', padx=20)
        
        glow_var = tk.BooleanVar(value=self.glow_enabled)
        tk.Checkbutton(dialog, text="تفعيل التوهج", variable=glow_var,
                      bg='#2d2d2d', fg='white', selectcolor='#444').pack(pady=10)
        
        def apply():
            self.press_effect = effect_var.get()
            self.glow_enabled = glow_var.get()
            self.key_config['press_effect'] = self.press_effect
            self.key_config['glow_enabled'] = self.glow_enabled
            
            if self.glow_enabled and not self.glow_frame:
                self.create_glow_effect()
            elif not self.glow_enabled and self.glow_frame:
                self.glow_frame.destroy()
                self.glow_frame = None
            
            dialog.destroy()
        
        tk.Button(dialog, text="تطبيق", command=apply, bg='#4a9eff', 
                 fg='white').pack(pady=10)
    
    def edit_properties(self):
        """تحرير الخصائص المتقدمة"""
        dialog = tk.Toplevel(self)
        dialog.title("خصائص متقدمة")
        dialog.geometry("450x500")
        dialog.configure(bg='#2d2d2d')
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تبويب أساسي
        tab_basic = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(tab_basic, text="أساسي")
        
        fields = [
            ("اسم الزر:", 'label', self.label_text),
            ("المفتاح:", 'bind', self.bind_key),
            ("الإجراء:", 'action_value', self.key_config.get('action_value', '')),
        ]
        
        entries = {}
        for i, (label_text, key, default) in enumerate(fields):
            tk.Label(tab_basic, text=label_text, bg='#2d2d2d', fg='white').pack(pady=(20 if i==0 else 10, 5))
            ent = tk.Entry(tab_basic, bg='#444', fg='white', font=('Arial', 11))
            ent.insert(0, default)
            ent.pack(fill=tk.X, padx=20)
            entries[key] = ent
        
        # تبويب مظهر
        tab_appearance = tk.Frame(notebook, bg='#2d2d2d')
        notebook.add(tab_appearance, text="مظهر")
        
        tk.Label(tab_appearance, text="حجم الخط:", bg='#2d2d2d', fg='white').pack(pady=20)
        font_scale = tk.Scale(tab_appearance, from_=8, to=30, orient=tk.HORIZONTAL,
                             bg='#2d2d2d', fg='white')
        font_scale.set(self.font_size)
        font_scale.pack()
        
        def save():
            self.key_config['label'] = entries['label'].get()
            self.key_config['bind'] = entries['bind'].get()
            self.key_config['action_value'] = entries['action_value'].get()
            self.key_config['font_size'] = font_scale.get()
            
            self.label_text = entries['label'].get()
            self.bind_key = entries['bind'].get()
            self.font_size = font_scale.get()
            
            self.label.configure(text=self.label_text, font=('Arial', self.font_size, 'bold'))
            
            if self.app:
                self.app.refresh_key_bindings()
            
            dialog.destroy()
        
        tk.Button(dialog, text="💾 حفظ", command=save, bg='#4a9eff', 
                 fg='white', font=('Arial', 12, 'bold')).pack(pady=20)
    
    def lighten_color(self, color, amount=20):
        """تفتيح اللون"""
        try:
            import colorsys
            hex_color = color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            l = min(1, l + amount/100.0)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
        except:
            return color
    
    def on_hover_enter(self, event):
        """عند دخول الماوس"""
        if not self.is_pressed:
            self.configure(bg=self.hover_color)
            self.label.configure(bg=self.hover_color)
        
        # إظهار Tooltip
        tooltip_text = self.key_config.get('tooltip', f"المفتاح: {self.bind_key}\nضغطات: {self.press_count}")
        if tooltip_text:
            self.show_tooltip(tooltip_text)
    
    def on_hover_leave(self, event):
        """عند خروج الماوس"""
        if not self.is_pressed:
            self.configure(bg=self.original_color)
            self.label.configure(bg=self.original_color)
        
        # إخفاء Tooltip
        self.hide_tooltip()
    
    def show_tooltip(self, text):
        """إظهار Tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
        
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.overrideredirect(True)
        self.tooltip_window.attributes('-topmost', True)
        
        label = tk.Label(self.tooltip_window, text=text, bg='#ffffcc', fg='black',
                        font=('Arial', 10), relief='solid', borderwidth=1)
        label.pack()
        
        x = self.winfo_rootx() + self.width + 5
        y = self.winfo_rooty()
        self.tooltip_window.geometry(f"+{x}+{y}")
    
    def hide_tooltip(self):
        """إخفاء Tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def on_mouse_wheel(self, event):
        """عند تدوير عجلة الماوس فوق الزر"""
        if event.delta > 0:
            self.sensitivity = min(5.0, self.sensitivity + 0.1)
        else:
            self.sensitivity = max(0.1, self.sensitivity - 0.1)
        
        self.key_config['sensitivity'] = round(self.sensitivity, 1)
        
        # إظهار الحساسية الحالية
        if hasattr(self, 'sens_label'):
            self.sens_label.destroy()
        self.sens_label = tk.Label(self, text=f"⚡{self.sensitivity}", 
                                  bg='yellow', fg='black', font=('Arial', 8, 'bold'))
        self.sens_label.place(x=self.width-40, y=5)
        self.after(1000, lambda: hasattr(self, 'sens_label') and self.sens_label.destroy())


class KeyboardMapperProV3:
    """التطبيق الرئيسي - النسخة الثالثة المتقدمة"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Mapper Pro V3 - تتبع شامل")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1a1a1a')
        
        # متغيرات التطبيق
        self.buttons = []
        self.key_bindings = {}
        self.clipboard_data = None
        self.edit_mode = True
        self.settings = {
            'grid_snap': 10,
            'show_grid': True,
            'auto_save': True,
            'theme': 'dark'
        }
        
        # مراقب المدخلات
        self.input_monitor = InputMonitor(callback=self.on_input_event)
        
        # إنشاء الواجهة
        self.create_main_layout()
        self.create_sidebar()
        self.create_status_bar()
        
        # تحميل التخطيط المحفوظ
        self.load_layout()
        
        # بدء المراقبة
        self.input_monitor.start()
        
        # تحديث دوري للإحصائيات
        self.update_stats_periodically()
    
    def create_main_layout(self):
        """إنشاء التخطيط الرئيسي"""
        # الإطار الرئيسي للأزرار
        self.canvas_frame = tk.Frame(self.root, bg='#1a1a1a')
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas مع Scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='#2a2a2a', highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # إطار المحتوى
        self.content_frame = tk.Frame(self.canvas, bg='#2a2a2a')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        
        # ربط تغيير حجم canvas
        self.content_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # رسم الشبكة
        if self.settings.get('show_grid'):
            self.draw_grid()
    
    def create_sidebar(self):
        """إنشاء الشريط الجانبي للإعدادات"""
        self.sidebar = tk.Frame(self.root, bg='#2d2d2d', width=350)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # عنوان الشريط الجانبي
        title_frame = tk.Frame(self.sidebar, bg='#1a1a1a', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="⚙️ الإعدادات", bg='#1a1a1a', fg='white',
                font=('Arial', 16, 'bold')).pack(pady=15)
        
        # أدوات التحكم
        tools_frame = tk.Frame(self.sidebar, bg='#2d2d2d')
        tools_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Button(tools_frame, text="➕ إضافة زر جديد", command=self.add_new_button,
                 bg='#4a9eff', fg='white', font=('Arial', 11, 'bold')).pack(fill=tk.X, pady=5)
        
        tk.Button(tools_frame, text="💾 حفظ التخطيط", command=self.save_layout,
                 bg='#28a745', fg='white', font=('Arial', 11)).pack(fill=tk.X, pady=5)
        
        tk.Button(tools_frame, text="📂 تحميل تخطيط", command=self.load_layout_dialog,
                 bg='#ffc107', fg='black', font=('Arial', 11)).pack(fill=tk.X, pady=5)
        
        tk.Button(tools_frame, text="🗑️ مسح الكل", command=self.clear_all_buttons,
                 bg='#dc3545', fg='white', font=('Arial', 11)).pack(fill=tk.X, pady=5)
        
        # قسم تتبع المدخلات
        track_frame = tk.LabelFrame(self.sidebar, text="📊 تتبع المدخلات", 
                                   bg='#2d2d2d', fg='white', font=('Arial', 12, 'bold'))
        track_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # إحصائيات سريعة
        self.stats_label = tk.Label(track_frame, text="", bg='#3d3d3d', fg='white',
                                   font=('Arial', 10), justify='left', anchor='w')
        self.stats_label.pack(fill=tk.X, padx=10, pady=10)
        
        # سجل الأحداث
        tk.Label(track_frame, text="آخر الأحداث:", bg='#2d2d2d', fg='#aaa',
                font=('Arial', 10)).pack(padx=10, pady=(10,5))
        
        self.events_text = scrolledtext.ScrolledText(track_frame, height=15, 
                                                     bg='#1a1a1a', fg='#00ff00',
                                                     font=('Consolas', 9))
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # أزرار التحكم بالتتبع
        btn_frame = tk.Frame(track_frame, bg='#2d2d2d')
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame, text="▶️ بدء", command=self.start_monitoring,
                 bg='#28a745', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="⏸️ إيقاف", command=self.stop_monitoring,
                 bg='#dc3545', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="📥 تصدير", command=self.export_events,
                 bg='#17a2b8', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="🗑️ مسح", command=self.clear_events,
                 bg='#6c757d', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self):
        """إنشاء شريط الحالة"""
        self.status_bar = tk.Frame(self.root, bg='#1a1a1a', height=30)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_bar, text="جاهز | وضع التحرير: مفعل",
                                    bg='#1a1a1a', fg='#aaa', font=('Arial', 9))
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def draw_grid(self):
        """رسم شبكة الخلفية"""
        grid_size = 20
        canvas_width = 2000
        canvas_height = 2000
        
        for x in range(0, canvas_width, grid_size):
            self.canvas.create_line(x, 0, x, canvas_height, fill='#333333', width=1)
        
        for y in range(0, canvas_height, grid_size):
            self.canvas.create_line(0, y, canvas_width, y, fill='#333333', width=1)
    
    def add_new_button(self):
        """إضافة زر جديد"""
        config = {
            'id': f"btn_{int(time.time() * 1000)}",
            'label': f'زر {len(self.buttons) + 1}',
            'bind': '',
            'action_type': 'key',
            'action_value': '',
            'x': 50 + (len(self.buttons) * 100) % 500,
            'y': 50 + (len(self.buttons) // 5) * 100,
            'width': 80,
            'height': 80,
            'color': '#4a9eff',
            'sensitivity': 1.0,
            'press_effect': 'scale',
            'glow_enabled': False
        }
        
        self.buttons.append(config)
        self.create_button_widget(config)
        self.update_status(f"تم إضافة زر جديد: {config['label']}")
    
    def create_button_widget(self, config):
        """إنشاء عنصر زر على canvas"""
        btn = DraggableButton(self.content_frame, config, self)
        self.canvas.create_window(config['x'], config['y'], window=btn, anchor='nw')
    
    def on_input_event(self, event):
        """معالجة أحداث المدخلات"""
        # إضافة الحدث للسجل
        event_str = f"[{event.get('timestamp', 'N/A')}] {event.get('type', 'unknown')}"
        
        if event.get('type') == 'key_press':
            event_str += f" - {event.get('key', '')}"
        elif event.get('type') == 'mouse_click':
            event_str += f" - {event.get('button', '')} ({event.get('action', '')})"
        elif event.get('type') == 'mouse_move':
            event_str += f" - ({event.get('x', 0)}, {event.get('y', 0)})"
        
        # إضافة للنص
        self.events_text.insert(tk.END, event_str + "\n")
        self.events_text.see(tk.END)
        
        # الاحتفاظ بآخر 100 حدث فقط في العرض
        lines = self.events_text.get('1.0', tk.END).split('\n')
        if len(lines) > 100:
            self.events_text.delete('1.0', '2.0')
    
    def update_stats_periodically(self):
        """تحديث الإحصائيات بشكل دوري"""
        if self.input_monitor:
            stats = self.input_monitor.get_statistics()
            
            stats_text = (
                f"📊 إجمالي الأحداث: {stats['total_events']}\n"
                f"⌨️ ضغطات المفاتيح: {stats['key_presses']}\n"
                f"🖱️ نقرات الماوس: {stats['mouse_clicks']}\n"
                f"📍 موقع الماوس: {stats['mouse_position']}\n"
                f"🔑 مفاتيح نشطة: {', '.join(stats['active_keys']) if stats['active_keys'] else 'لا يوجد'}"
            )
            
            self.stats_label.configure(text=stats_text)
        
        self.root.after(500, self.update_stats_periodically)
    
    def start_monitoring(self):
        """بدء المراقبة"""
        self.input_monitor.start()
        self.update_status("تم بدء مراقبة المدخلات")
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self.input_monitor.stop()
        self.update_status("تم إيقاف مراقبة المدخلات")
    
    def clear_events(self):
        """مسح سجل الأحداث"""
        self.events_text.delete('1.0', tk.END)
        self.input_monitor.events_log.clear()
    
    def export_events(self):
        """تصدير الأحداث"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="تصدير سجل الأحداث"
        )
        
        if filename:
            self.input_monitor.export_log(filename)
            messagebox.showinfo("تم", f"تم تصدير الأحداث إلى:\n{filename}")
    
    def save_layout(self):
        """حفظ التخطيط"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="layout.json",
            filetypes=[("JSON files", "*.json")],
            title="حفظ التخطيط"
        )
        
        if filename:
            data = {
                'buttons': self.buttons,
                'settings': self.settings
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.update_status(f"تم الحفظ: {filename}")
    
    def load_layout_dialog(self):
        """تحميل تخطيط من ملف"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="تحميل تخطيط"
        )
        
        if filename:
            self.load_layout(filename)
    
    def load_layout(self, filename=None):
        """تحميل التخطيط"""
        try:
            if not filename:
                default_file = "keyboard_layout.json"
                if os.path.exists(default_file):
                    filename = default_file
            
            if filename and os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.buttons = data.get('buttons', [])
                self.settings.update(data.get('settings', {}))
                
                # مسح الأزرار الحالية
                for widget in self.content_frame.winfo_children():
                    widget.destroy()
                
                # إعادة إنشاء الأزرار
                for config in self.buttons:
                    self.create_button_widget(config)
                
                self.update_status(f"تم التحميل: {filename}")
            else:
                # تخطيط افتراضي
                self.add_new_button()
                self.add_new_button()
                self.add_new_button()
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل التخطيط: {str(e)}")
    
    def clear_all_buttons(self):
        """مسح جميع الأزرار"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من مسح جميع الأزرار؟"):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            self.buttons.clear()
            self.key_bindings.clear()
            self.update_status("تم مسح جميع الأزرار")
    
    def refresh_key_bindings(self):
        """تحديث روابط المفاتيح"""
        self.key_bindings.clear()
        for config in self.buttons:
            if config.get('bind'):
                # البحث عن الزر وتحديث الربط
                for widget in self.content_frame.winfo_children():
                    if isinstance(widget, DraggableButton) and widget.key_config == config:
                        widget.setup_key_binding()
    
    def trigger_button_action(self, config, is_press):
        """تفعيل إجراء الزر"""
        action_type = config.get('action_type', 'key')
        action_value = config.get('action_value', '')
        sensitivity = config.get('sensitivity', 1.0)
        
        if not PYNPUT_AVAILABLE:
            return
        
        keyboard_ctrl = KeyboardController()
        mouse_ctrl = MouseController()
        
        try:
            if action_type == 'key':
                key = self.parse_key(action_value)
                if key:
                    if is_press:
                        keyboard_ctrl.press(key)
                    else:
                        keyboard_ctrl.release(key)
            
            elif action_type == 'mouse_click':
                if is_press:
                    button = Button.left
                    if 'right' in action_value.lower():
                        button = Button.right
                    elif 'middle' in action_value.lower():
                        button = Button.middle
                    mouse_ctrl.press(button)
                else:
                    mouse_ctrl.release(Button.left)
            
            elif action_type == 'macro':
                if is_press:
                    # تنفيذ الماكرو
                    keys = action_value.split('+')
                    for k in keys:
                        key = self.parse_key(k.strip())
                        if key:
                            keyboard_ctrl.press(key)
                    for k in reversed(keys):
                        key = self.parse_key(k.strip())
                        if key:
                            keyboard_ctrl.release(key)
            
            elif action_type == 'text':
                if is_press:
                    keyboard_ctrl.type(action_value)
            
            elif action_type == 'combo':
                if is_press:
                    keys = action_value.split(',')
                    for k in keys:
                        key = self.parse_key(k.strip())
                        if key:
                            keyboard_ctrl.press(key)
                            time.sleep(0.05 * sensitivity)
                    for k in reversed(keys):
                        key = self.parse_key(k.strip())
                        if key:
                            keyboard_ctrl.release(key)
                            time.sleep(0.05 * sensitivity)
        
        except Exception as e:
            print(f"Error triggering action: {e}")
    
    def parse_key(self, key_str):
        """تحليل نص المفتاح"""
        if not key_str:
            return None
        
        key_str = key_str.strip().lower()
        
        # مفاتيح خاصة
        special_keys = {
            'enter': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'esc': Key.esc,
            'escape': Key.esc,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r,
            'shift_l': Key.shift_l, 'shift_r': Key.shift_r,
            'alt_l': Key.alt_l, 'alt_r': Key.alt_r,
            'cmd_l': Key.cmd_l, 'cmd_r': Key.cmd_r,
        }
        
        if key_str in special_keys:
            return special_keys[key_str]
        
        # أحرف عادية
        if len(key_str) == 1:
            return key_str
        
        return None
    
    def on_frame_configure(self, event):
        """عند تغيير حجم الإطار"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def on_canvas_configure(self, event):
        """عند تغيير حجم canvas"""
        self.canvas.itemconfig(self.canvas_window, width=max(event.width, 2000))
    
    def update_status(self, message):
        """تحديث شريط الحالة"""
        self.status_label.configure(text=message)
        self.root.after(5000, lambda: self.status_label.configure(
            text="جاهز | وضع التحرير: مفعل" if self.edit_mode else "جاهز"))


def main():
    root = tk.Tk()
    app = KeyboardMapperProV3(root)
    root.mainloop()


if __name__ == "__main__":
    main()
