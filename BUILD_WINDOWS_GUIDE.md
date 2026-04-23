--- BUILD_WINDOWS_GUIDE.md (原始)


+++ BUILD_WINDOWS_GUIDE.md (修改后)
# 🎹 KeyboardMapper Pro - دليل البناء لنظام ويندوز

## ⚠️ ملاحظة هامة جداً

**أنت حالياً على نظام Linux**، لذا لا يمكن بناء ملف `.exe` لويندوز مباشرة.
PyInstaller يبني فقط للنظام الذي يعمل عليه.

---

## ✅ الحل: طريقتان للحصول على ملف EXE

### الطريقة 1: البناء على ويندوز (موصى به)

#### الخطوات:
1. **انقل الملفات التالية إلى جهاز ويندوز**:
   - `keyboard_mapper_pro.py`
   - `build_windows.bat`
   - `README_PRO_AR.md`

2. **على ويندوز، شغل الأمر**:
   ```cmd
   build_windows.bat
   ```

3. **أو يدوياً**:
   ```cmd
   pip install pyinstaller
   pyinstaller --onefile --windowed --name KeyboardMapperPro keyboard_mapper_pro.py
   ```

4. **الملف الناتج** سيكون في:
   ```
   dist\KeyboardMapperPro.exe
   ```

---

### الطريقة 2: استخدام بيئة ويندوز عن بعد

#### خيار أ: GitHub Actions (مجاني)
أنشئ ملف `.github/workflows/build.yml` في مشروعك:

```yaml
name: Build Windows EXE

on: [push]

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        pip install pyinstaller

    - name: Build EXE
      run: |
        pyinstaller --onefile --windowed --name KeyboardMapperPro keyboard_mapper_pro.py

    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: KeyboardMapperPro
        path: dist/KeyboardMapperPro.exe
```

#### خيار ب: Azure DevOps / GitLab CI
استخدم نفس المبدأ مع runners لويندوز.

---

## 📦 الملفات الجاهزة

تم إنشاء الملفات التالية في `/workspace`:

| الملف | الحجم | الوصف |
|-------|-------|-------|
| `keyboard_mapper_pro.py` | 39 KB | كود التطبيق الكامل |
| `build_windows.bat` | 938 B | سكريبت البناء لويندوز |
| `README_PRO_AR.md` | 8.0 KB | دليل التوثيق بالعربية |
| `README_PRO.md` | 7.9 KB | دليل التوثيق بالإنجليزية |

---

## 🚀 تعليمات سريعة للمستخدم النهائي

### على ويندوز:

```cmd
# 1. تثبيت Python (إذا لم يكن مثبتاً)
# حمّل من: https://python.org

# 2. فتح موجه الأوامر في مجلد المشروع
cd path\to\project

# 3. تشغيل السكريبت
build_windows.bat

# 4. الانتظار حتى ينتهي البناء
# ستجد الملف في: dist\KeyboardMapperPro.exe

# 5. تشغيل التطبيق
dist\KeyboardMapperPro.exe
```

---

## 🔧 متطلبات النظام

### للبناء:
- ويندوز 7/8/10/11 (64-bit)
- Python 3.7 أو أحدث
- PyInstaller
- مساحة تخزين: 500 ميجابايت (مؤقتاً)

### للتشغيل:
- ويندوز 7/8/10/11
- لا حاجة لـ Python مثبت
- رام: 50-100 ميجابايت
- معالج: أي معالج حديث

---

## 📊 حجم الملف النهائي

| النوع | الحجم التقريبي |
|-------|----------------|
| EXE غير مضغوط | 20-30 ميجابايت |
| EXE مضغوط (UPX) | 10-15 ميجابايت |
| مع حزمة Python كاملة | 30-40 ميجابايت |

---

## ⚡ نصائح للضغط

لتقليل حجم الملف التنفيذي:

```cmd
# 1. حمّل UPX من: https://upx.github.io/

# 2. ضغط الملف
upx --best dist\KeyboardMapperPro.exe

# 3. التحقق من الحجم الجديد
dir dist\KeyboardMapperPro.exe
```

**توفير متوقع**: 40-60% من الحجم الأصلي

---

## 🛠️ حل المشاكل الشائعة

### المشكلة: "tkinter not found"
```cmd
# تأكد من تثبيت Python بشكل كامل
# عند التثبيت، فعّل خيار "tcl/tk and IDLE"
```

### المشكلة: "MSVCP140.dll missing"
```cmd
# حمّل Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### المشكلة: "Build takes too long"
```cmd
# امسح المجلدات المؤقتة
rmdir /s /q build
rmdir /s /q dist

# أعد البناء
build_windows.bat
```

---

## 📞 الدعم

للمزيد من المساعدة:
- راجع `README_PRO_AR.md` للتوثيق الكامل
- تفقد قسم "حل المشاكل" في الدليل
- تواصل عبر: support@keyboardmapper.pro

---

**ملاحظة أخيرة**:
هذا المشروع مصمم للعمل على ويندوز. البناء الحالي على Linux أنتج ملفاً لنظام Linux فقط. للحصول على `.exe`، يجب اتباع إحدى الطريقتين المذكورتين أعلاه.

🎉 شكراً لاستخدامكم KeyboardMapper Pro!