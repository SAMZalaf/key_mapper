using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Shapes;
using KeyMapperPro.Models;
using KeyMapperPro.Native;
using KeyMapperPro.Services;
using KeyMapperPro.Views;

namespace KeyMapperPro
{
    public partial class MainWindow : Window
    {
        private bool _isMappingMode = false;
        private List<MappingElement> _elements = new List<MappingElement>();
        private UIElement? _draggedElement = null;
        private System.Windows.Point _dragStart;

        private InputHookService _hookService;
        private InputSimulatorService _simulatorService;
        private MappingEngine _mappingEngine;
        private SettingsWindow _settingsWindow;

        public MainWindow()
        {
            InitializeComponent();

            _hookService = new InputHookService();
            _simulatorService = new InputSimulatorService();

            double width = SystemParameters.PrimaryScreenWidth;
            double height = SystemParameters.PrimaryScreenHeight;
            _mappingEngine = new MappingEngine(_simulatorService, _elements, width, height);

            _settingsWindow = new SettingsWindow();
            _settingsWindow.OnAddElement += SettingsWindow_OnAddElement;
            _settingsWindow.OnUpdateElement += SettingsWindow_OnUpdateElement;

            _hookService.KeyChanged += _hookService_KeyChanged;
            _hookService.MouseMoved += _hookService_MouseMoved;

            this.Loaded += MainWindow_Loaded;
            this.Closing += MainWindow_Closing;
        }

        private void SettingsWindow_OnAddElement(ControlType type)
        {
            var element = new MappingElement {
                Name = $"New {type}",
                Type = type,
                X = 50,
                Y = 50,
                BoundKey = "None"
            };
            AddMappingElement(element);
        }

        private void SettingsWindow_OnUpdateElement(MappingElement element)
        {
            foreach (FrameworkElement child in MappingCanvas.Children)
            {
                if (child.Tag == element)
                {
                    UpdateUIFromModel(child, element);
                    break;
                }
            }
        }

        private void UpdateUIFromModel(FrameworkElement uiElement, MappingElement element)
        {
            if (uiElement is Border border)
            {
                border.Opacity = element.Opacity;
                try {
                    border.Background = (SolidColorBrush)new BrushConverter().ConvertFrom(element.ColorHex)!;
                } catch {
                    border.Background = System.Windows.Media.Brushes.Red;
                }

                if (border.Child is TextBlock textBlock)
                {
                    textBlock.Text = element.BoundKey;
                }

                border.Width = element.Width;
                border.Height = element.Height;
                border.CornerRadius = new CornerRadius(element.Width / 2);

                double canvasWidth = MappingCanvas.ActualWidth > 0 ? MappingCanvas.ActualWidth : SystemParameters.PrimaryScreenWidth;
                double canvasHeight = MappingCanvas.ActualHeight > 0 ? MappingCanvas.ActualHeight : SystemParameters.PrimaryScreenHeight;

                Canvas.SetLeft(border, (element.X / 100) * canvasWidth - (element.Width / 2));
                Canvas.SetTop(border, (element.Y / 100) * canvasHeight - (element.Height / 2));
            }
        }

        private bool _hookService_KeyChanged(int vkCode, bool isDown)
        {
            var key = KeyInterop.KeyFromVirtualKey(vkCode);
            if (key == Key.F9 && isDown)
            {
                this.Dispatcher.Invoke(() => {
                    if (_settingsWindow.IsVisible)
                    {
                        _settingsWindow.Hide();
                        SetMappingMode(false);
                    }
                    else
                    {
                        _settingsWindow.Show();
                        SetMappingMode(true);
                    }
                });
                return true;
            }

            if (!_isMappingMode)
            {
                return _mappingEngine.HandleKeyPress(vkCode, isDown);
            }
            return false;
        }

        private void SetMappingMode(bool enabled)
        {
            _isMappingMode = enabled;
            if (_isMappingMode)
            {
                ToggleMappingBtn.Content = "Disable Mapping Mode";
                MappingCanvas.Visibility = Visibility.Visible;
                SaveBtn.Visibility = Visibility.Visible;
                this.Background = new SolidColorBrush(System.Windows.Media.Color.FromArgb(50, 0, 0, 0));
                SetClickThrough(false);
            }
            else
            {
                ToggleMappingBtn.Content = "Enable Mapping Mode";
                MappingCanvas.Visibility = Visibility.Collapsed;
                SaveBtn.Visibility = Visibility.Collapsed;
                this.Background = System.Windows.Media.Brushes.Transparent;
                SetClickThrough(true);
            }
        }

        private void _hookService_MouseMoved(int x, int y)
        {
            if (!_isMappingMode)
            {
                _mappingEngine.HandleMouseMove(x, y);
            }
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            SetClickThrough(true);
            _hookService.Start();
        }

        private void MainWindow_Closing(object? sender, CancelEventArgs e)
        {
            _hookService.Stop();
            _hookService.Dispose();
            _settingsWindow.Close();
        }

        private void SetClickThrough(bool clickThrough)
        {
            var hwnd = new WindowInteropHelper(this).Handle;
            int extendedStyle = NativeMethods.GetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE);
            if (clickThrough)
            {
                NativeMethods.SetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE, extendedStyle | NativeMethods.WS_EX_TRANSPARENT | NativeMethods.WS_EX_LAYERED);
            }
            else
            {
                NativeMethods.SetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE, extendedStyle & ~NativeMethods.WS_EX_TRANSPARENT);
            }
        }

        private void ToggleMappingBtn_Click(object sender, RoutedEventArgs e)
        {
            SetMappingMode(!_isMappingMode);
        }

        private void AddMappingElement(MappingElement element)
        {
            _elements.Add(element);

            Border border = new Border
            {
                Width = element.Width,
                Height = element.Height,
                Background = System.Windows.Media.Brushes.Red,
                CornerRadius = new CornerRadius(element.Width / 2),
                Opacity = element.Opacity,
                Child = new TextBlock
                {
                    Text = element.BoundKey,
                    HorizontalAlignment = System.Windows.HorizontalAlignment.Center,
                    VerticalAlignment = System.Windows.VerticalAlignment.Center,
                    Foreground = System.Windows.Media.Brushes.White
                },
                Tag = element
            };

            border.MouseLeftButtonDown += Element_MouseLeftButtonDown;
            border.MouseMove += Element_MouseMove;
            border.MouseLeftButtonUp += Element_MouseLeftButtonUp;
            border.MouseRightButtonDown += Element_MouseRightButtonDown;

            UpdateUIFromModel(border, element);

            MappingCanvas.Children.Add(border);
        }

        private void Element_MouseRightButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (!_isMappingMode) return;
            var uiElement = sender as FrameworkElement;
            if (uiElement == null) return;

            var element = (MappingElement)uiElement.Tag;

            System.Windows.Controls.ContextMenu menu = new System.Windows.Controls.ContextMenu();

            System.Windows.Controls.MenuItem copyItem = new System.Windows.Controls.MenuItem { Header = "Copy" };
            copyItem.Click += (s, ev) => {
                var clone = new MappingElement {
                    Type = element.Type,
                    X = element.X + 2,
                    Y = element.Y + 2,
                    BoundKey = element.BoundKey,
                    ColorHex = element.ColorHex,
                    Opacity = element.Opacity,
                    Width = element.Width,
                    Height = element.Height
                };
                AddMappingElement(clone);
            };

            System.Windows.Controls.MenuItem deleteItem = new System.Windows.Controls.MenuItem { Header = "Delete" };
            deleteItem.Click += (s, ev) => {
                _elements.Remove(element);
                MappingCanvas.Children.Remove(uiElement);
            };

            System.Windows.Controls.MenuItem propertiesItem = new System.Windows.Controls.MenuItem { Header = "Properties" };
            propertiesItem.Click += (s, ev) => {
                _settingsWindow.Show();
                _settingsWindow.EditElement(element);
            };

            menu.Items.Add(copyItem);
            menu.Items.Add(deleteItem);
            menu.Items.Add(new System.Windows.Controls.Separator());
            menu.Items.Add(propertiesItem);

            uiElement.ContextMenu = menu;
            menu.IsOpen = true;
            e.Handled = true;
        }

        private void Element_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (!_isMappingMode) return;
            _draggedElement = sender as UIElement;
            if (_draggedElement != null)
            {
                _dragStart = e.GetPosition(_draggedElement);
                _draggedElement.CaptureMouse();
            }
            e.Handled = true;
        }

        private void Element_MouseMove(object sender, System.Windows.Input.MouseEventArgs e)
        {
            if (_draggedElement == null) return;

            System.Windows.Point currentPos = e.GetPosition(MappingCanvas);
            double left = currentPos.X - _dragStart.X;
            double top = currentPos.Y - _dragStart.Y;

            Canvas.SetLeft(_draggedElement, left);
            Canvas.SetTop(_draggedElement, top);

            var element = (MappingElement)((FrameworkElement)_draggedElement).Tag;
            element.X = ((left + (element.Width / 2)) / MappingCanvas.ActualWidth) * 100;
            element.Y = ((top + (element.Height / 2)) / MappingCanvas.ActualHeight) * 100;
        }

        private void Element_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (_draggedElement == null) return;
            _draggedElement.ReleaseMouseCapture();
            _draggedElement = null;
        }

        private void SaveBtn_Click(object sender, RoutedEventArgs e)
        {
            System.Windows.MessageBox.Show("Profile saved (Simulated)");
        }
    }
}
