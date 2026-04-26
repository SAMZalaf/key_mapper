using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Input;
using KeyMapperPro.Models;

namespace KeyMapperPro.Services
{
    public class MappingEngine
    {
        private readonly InputSimulatorService _simulator;
        private readonly List<MappingElement> _elements;
        private readonly double _screenWidth;
        private readonly double _screenHeight;

        private readonly HashSet<string> _pressedKeys = new HashSet<string>();
        private bool _isDPadActive = false;
        private bool _isAimModeEnabled = false;
        private MappingElement? _activeAimElement = null;

        public MappingEngine(InputSimulatorService simulator, List<MappingElement> elements, double screenWidth, double screenHeight)
        {
            _simulator = simulator;
            _elements = elements;
            _screenWidth = screenWidth;
            _screenHeight = screenHeight;
        }

        public bool HandleKeyPress(int vkCode, bool isDown)
        {
            var keyStr = ((Key)KeyInterop.KeyFromVirtualKey(vkCode)).ToString();

            if (isDown) _pressedKeys.Add(keyStr);
            else _pressedKeys.Remove(keyStr);

            var elementsToTrigger = _elements.Where(e => e.BoundKey != null && (e.BoundKey.Equals(keyStr, StringComparison.OrdinalIgnoreCase) ||
                                                        (e.Type == ControlType.DPad && IsDPadKey(keyStr)))).ToList();

            bool handled = false;
            foreach (var element in elementsToTrigger)
            {
                handled = true;
                switch (element.Type)
                {
                    case ControlType.TapSpot:
                        if (element.BoundKey != null && element.BoundKey.Equals(keyStr, StringComparison.OrdinalIgnoreCase))
                            HandleTapSpot(element, isDown);
                        break;
                    case ControlType.DPad:
                        HandleDPad(element);
                        break;
                    case ControlType.AimMode:
                        if (element.BoundKey != null && element.BoundKey.Equals(keyStr, StringComparison.OrdinalIgnoreCase))
                            HandleAimModeToggle(element, isDown);
                        break;
                }
            }
            return handled;
        }

        public void HandleMouseMove(int x, int y)
        {
            if (!_isAimModeEnabled || _activeAimElement == null) return;

            int centerX = (int)(_screenWidth / 2);
            int centerY = (int)(_screenHeight / 2);

            int dx = x - centerX;
            int dy = y - centerY;

            if (dx == 0 && dy == 0) return;

            _simulator.SendMouseMove((int)(dx * _activeAimElement.Sensitivity), (int)(dy * _activeAimElement.Sensitivity));

            global::System.Windows.Forms.Cursor.Position = new global::System.Drawing.Point(centerX, centerY);
        }

        private bool IsDPadKey(string key)
        {
            return key == "W" || key == "A" || key == "S" || key == "D";
        }

        private void HandleTapSpot(MappingElement element, bool isDown)
        {
            int screenX = (int)((element.X / 100) * _screenWidth);
            int screenY = (int)((element.Y / 100) * _screenHeight);
            _simulator.SendMouseClick(screenX, screenY, isDown, _screenWidth, _screenHeight);
        }

        private void HandleDPad(MappingElement element)
        {
            bool w = _pressedKeys.Contains("W");
            bool a = _pressedKeys.Contains("A");
            bool s = _pressedKeys.Contains("S");
            bool d = _pressedKeys.Contains("D");

            if (!w && !a && !s && !d)
            {
                if (_isDPadActive)
                {
                    _simulator.SendMouseClick(0, 0, false, _screenWidth, _screenHeight);
                    _isDPadActive = false;
                }
                return;
            }

            double offsetX = 0;
            double offsetY = 0;

            if (w) offsetY -= 1;
            if (s) offsetY += 1;
            if (a) offsetX -= 1;
            if (d) offsetX += 1;

            double length = Math.Sqrt(offsetX * offsetX + offsetY * offsetY);
            if (length > 0)
            {
                offsetX /= length;
                offsetY /= length;
            }

            int centerX = (int)((element.X / 100) * _screenWidth);
            int centerY = (int)((element.Y / 100) * _screenHeight);
            int radiusPx = (int)((element.Radius / 100) * _screenWidth);

            int targetX = centerX + (int)(offsetX * radiusPx);
            int targetY = centerY + (int)(offsetY * radiusPx);

            if (!_isDPadActive)
            {
                _simulator.SendMouseClick(centerX, centerY, true, _screenWidth, _screenHeight);
                _isDPadActive = true;
            }

            _simulator.SendMouseClick(targetX, targetY, true, _screenWidth, _screenHeight);
        }

        private void HandleAimModeToggle(MappingElement element, bool isDown)
        {
            if (isDown)
            {
                _isAimModeEnabled = !_isAimModeEnabled;
                if (_isAimModeEnabled)
                {
                    _activeAimElement = element;
                    global::System.Windows.Forms.Cursor.Hide();
                    global::System.Windows.Forms.Cursor.Position = new global::System.Drawing.Point((int)(_screenWidth / 2), (int)(_screenHeight / 2));
                }
                else
                {
                    global::System.Windows.Forms.Cursor.Show();
                    _activeAimElement = null;
                }
            }
        }
    }
}
