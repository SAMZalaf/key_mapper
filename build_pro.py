#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KeyboardMapper Pro - Build Script
سكريبت بناء متقدم لتطبيق KeyboardMapper Pro
يدعم البناء لأنظمة مختلفة مع خيارات متعددة
"""

import os
import sys
import subprocess
import shutil
import argparse

# الألوان للطباعة
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def check_dependencies():
    """التحقق من تثبيت المتطلبات"""
    print_info("جاري التحقق من المتطلبات...")
    
    try:
        import pyinstaller
        print_success("PyInstaller مثبت")
    except ImportError:
        print_info("جاري تثبيت PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"])
        print_success("تم تثبيت PyInstaller")
    
    return True

def clean_build():
    """تنظيف الملفات القديمة"""
    print_info("جاري تنظيف الملفات القديمة...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['KeyboardMapperPro.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_success(f"تم حذف {dir_name}/")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print_success(f"تم حذف {file_name}")

def build_exe(name="KeyboardMapperPro", onefile=True, windowed=True, icon=None, debug=False):
    """بناء الملف التنفيذي"""
    print_header("بناء التطبيق")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", name,
    ]
    
    if onefile:
        cmd.append("--onefile")
        print_info("وضع الملف الواحد مفعل")
    
    if windowed:
        cmd.append("--windowed")
        print_info("وضع النافذة مفعل (بدون console)")
    
    if icon and os.path.exists(icon):
        cmd.extend(["--icon", icon])
        print_success(f"تم تعيين الأيقونة: {icon}")
    
    if debug:
        cmd.append("--debug=all")
        print_info("وضع التصحيح مفعل")
    
    # إضافة الكود المصدري
    cmd.append("keyboard_mapper_pro.py")
    
    print_info(f"جاري التنفيذ: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print_success("تم البناء بنجاح!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"فشل البناء: {e}")
        return False

def compress_exe(exe_path):
    """ضغط الملف التنفيذي باستخدام UPX"""
    if not os.path.exists(exe_path):
        print_error(f"الملف غير موجود: {exe_path}")
        return
    
    print_info("جاري البحث عن UPX للضغط...")
    
    # التحقق من وجود UPX
    upx_found = shutil.which("upx")
    
    if upx_found:
        print_success("تم العثور على UPX، جاري الضغط...")
        try:
            original_size = os.path.getsize(exe_path)
            subprocess.check_call(["upx", "--best", exe_path])
            compressed_size = os.path.getsize(exe_path)
            reduction = ((original_size - compressed_size) / original_size) * 100
            print_success(f"تم الضغط! التوفير: {reduction:.1f}%")
        except subprocess.CalledProcessError:
            print_info("فشل الضغط بـ UPX")
    else:
        print_info("UPX غير مثبت. لتثبيت الضغط:")
        print_info("  Windows: حمّل من https://github.com/upx/upx/releases")
        print_info("  Linux: sudo apt install upx-ucl")

def show_build_info(exe_path):
    """عرض معلومات عن البناء"""
    if not os.path.exists(exe_path):
        return
    
    size = os.path.getsize(exe_path)
    size_mb = size / (1024 * 1024)
    
    print_header("معلومات البناء")
    print_info(f"المسار: {exe_path}")
    print_info(f"الحجم: {size_mb:.2f} MB")
    
    if size_mb < 30:
        print_success("الحجم ممتاز!")
    elif size_mb < 50:
        print_info("الحجم جيد")
    else:
        print_info("الحجم كبير نسبياً")

def main():
    parser = argparse.ArgumentParser(description="KeyboardMapper Pro Build Script")
    parser.add_argument("--clean", action="store_true", help="تنظيف الملفات القديمة قبل البناء")
    parser.add_argument("--no-clean", action="store_true", help="عدم تنظيف الملفات القديمة")
    parser.add_argument("--debug", action="store_true", help="بناء مع وضع التصحيح")
    parser.add_argument("--no-compress", action="store_true", help="عدم ضغط الملف التنفيذي")
    parser.add_argument("--output", default="KeyboardMapperPro", help="اسم الملف التنفيذي الناتج")
    
    args = parser.parse_args()
    
    print_header("KeyboardMapper Pro - أداة البناء")
    
    # التحقق من المتطلبات
    if not check_dependencies():
        print_error("توقف بسبب عدم توفر المتطلبات")
        sys.exit(1)
    
    # التنظيف
    if args.clean or not args.no_clean:
        clean_build()
    
    # البناء
    success = build_exe(
        name=args.output,
        onefile=True,
        windowed=True,
        debug=args.debug
    )
    
    if not success:
        sys.exit(1)
    
    # تحديد مسار الملف التنفيذي
    if sys.platform == "win32":
        exe_path = f"dist/{args.output}.exe"
    else:
        exe_path = f"dist/{args.output}"
    
    # عرض المعلومات
    show_build_info(exe_path)
    
    # الضغط
    if not args.no_compress:
        compress_exe(exe_path)
    
    print_header("اكتمل البناء")
    print_success(f"الملف التنفيذي جاهز: {exe_path}")
    print_info("شكراً لاستخدام KeyboardMapper Pro!")

if __name__ == "__main__":
    main()
