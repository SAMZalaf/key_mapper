mport tkinter as tk
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
    print("تنبيه: لم يتم العثور على pyautogui. محاكاة الماوس والكيبورد لن تعمل خارج النافذة.")

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
            self.command(self.key_config['action'])

    def on_release(self, event):
        self.is_pressed = False
        self.draw_key()
        if app.edit_mode:
            # إنهاء السحب
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
        
        btn_lock_mouse = tk.Button(tab_control, text="قفل الماوس (F2)", command=self.toggle_mouse_lock, bg="#444", fg="white")
        btn_lock_mouse.pack(fill=tk.X, pady=5)
        
        btn_toggle_layout = tk.Button(tab_control, text="تشغيل/إيقاف التخطيط (F1)", command=self.toggle_layout, bg="#444", fg="white")
        btn_toggle_layout.pack(fill=tk.X, pady=5)

        # تاب المظهر
        tab_appearance = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(tab_appearance, text="مظهر")
        
        themes = ["داكن", "فاتح", "أزرق", "أخضر", "برمجي"]
        for t in themes:
            btn = tk.Button(tab_appearance, text=t, command=lambda x=t: self.change_theme(x))
            btn.pack(fill=tk.X, pady=2)

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
                    'x': start_x + c * (size + gap),
                    'y': start_y + r * (size + gap),
                    'w': size,
                    'h': size,
                    'color': '#333333',
                    'is_special': False
                }
                self.create_key_widget(config)

    def create_key_widget(self, config):
        btn = KeyButton(self.keyboard_canvas, config, command=self.handle_action)
        btn.place(x=config['x'], y=config['y'], width=config['w'], height=config['h'])
        self.keys.append(btn)

    def handle_action(self, action_id):
        if not self.layout_active: return
        
        # تأثير بصري
        if self.settings["touch_feedback"]:
            self.flash_screen()
            
        # محاكاة الإجراء (هنا يتم ربطها بـ pyautogui في النسخة الكاملة)
        print(f"Action Triggered: {action_id}")
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
            "برمجي": ("#282c34", "#21252b", "#abb2bf")
        }
        if theme_name in colors:
            bg, side, txt = colors[theme_name]
            self.main_frame.config(bg=bg)
            self.canvas_area.config(bg=bg)
            self.keyboard_canvas.config(bg=bg)
            self.sidebar.config(bg=side)
            # تحديث الألوان داخل التبويبات يتطلب تكرار الحلقات، تم تبسيطه هنا

    def bind_hotkeys(self):
        self.root.bind("<F1>", lambda e: self.toggle_layout())
        self.root.bind("<F2>", lambda e: self.toggle_mouse_lock())
        self.root.bind("<F3>", lambda e: self.toggle_transparency())
        self.root.bind("<Control-e>", lambda e: self.toggle_edit_mode())
        self.root.bind("<Control-s>", lambda e: self.save_layout())
        self.root.bind("<Control-o>", lambda e: self.load_layout())

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
                for config in 
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