using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using KeyMapperPro.Native;

namespace KeyMapperPro.Services
{
    public class InputHookService : IDisposable
    {
        private NativeMethods.LowLevelProc _keyboardProc;
        private NativeMethods.LowLevelProc _mouseProc;
        private IntPtr _keyboardHookId = IntPtr.Zero;
        private IntPtr _mouseHookId = IntPtr.Zero;

        public delegate bool KeyChangedDelegate(int vkCode, bool isDown);
        public event KeyChangedDelegate? KeyChanged;
        public event Action<int, int>? MouseMoved;

        public InputHookService()
        {
            _keyboardProc = KeyboardHookCallback;
            _mouseProc = MouseHookCallback;
        }

        public void Start()
        {
            _keyboardHookId = SetHook(_keyboardProc, NativeMethods.WH_KEYBOARD_LL);
            _mouseHookId = SetHook(_mouseProc, NativeMethods.WH_MOUSE_LL);
        }

        public void Stop()
        {
            if (_keyboardHookId != IntPtr.Zero)
            {
                NativeMethods.UnhookWindowsHookEx(_keyboardHookId);
                _keyboardHookId = IntPtr.Zero;
            }
            if (_mouseHookId != IntPtr.Zero)
            {
                NativeMethods.UnhookWindowsHookEx(_mouseHookId);
                _mouseHookId = IntPtr.Zero;
            }
        }

        private IntPtr SetHook(NativeMethods.LowLevelProc proc, int hookId)
        {
            using (Process curProcess = Process.GetCurrentProcess())
            using (ProcessModule? curModule = curProcess.MainModule)
            {
                if (curModule == null) return IntPtr.Zero;
                return NativeMethods.SetWindowsHookEx(hookId, proc, NativeMethods.GetModuleHandle(curModule.ModuleName), 0);
            }
        }

        private IntPtr KeyboardHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int vkCode = Marshal.ReadInt32(lParam);
                bool isKeyDown = wParam == (IntPtr)NativeMethods.WM_KEYDOWN || wParam == (IntPtr)NativeMethods.WM_SYSKEYDOWN;
                bool isKeyUp = wParam == (IntPtr)NativeMethods.WM_KEYUP || wParam == (IntPtr)NativeMethods.WM_SYSKEYUP;

                if (isKeyDown || isKeyUp)
                {
                    bool handled = KeyChanged?.Invoke(vkCode, isKeyDown) ?? false;
                    if (handled) return (IntPtr)1; // Block input
                }
            }
            return NativeMethods.CallNextHookEx(_keyboardHookId, nCode, wParam, lParam);
        }

        private IntPtr MouseHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && wParam == (IntPtr)NativeMethods.WM_MOUSEMOVE)
            {
                var hookStruct = Marshal.PtrToStructure<NativeMethods.MSLLHOOKSTRUCT>(lParam);
                MouseMoved?.Invoke(hookStruct.pt.x, hookStruct.pt.y);
            }
            return NativeMethods.CallNextHookEx(_mouseHookId, nCode, wParam, lParam);
        }

        public void Dispose()
        {
            Stop();
        }
    }
}
