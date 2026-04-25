using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Shapes;
using KeyMapperPro.Models;
using KeyMapperPro.Native;
using KeyMapperPro.Services;

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

        public MainWindow()
        {
            InitializeComponent();

            _hookService = new InputHookService();
            _simulatorService = new InputSimulatorService();

            double width = SystemParameters.PrimaryScreenWidth;
            double height = SystemParameters.PrimaryScreenHeight;
            _mappingEngine = new MappingEngine(_simulatorService, _elements, width, height);

            _hookService.KeyChanged += _hookService_KeyChanged;
            _hookService.MouseMoved += _hookService_MouseMoved;

            this.Loaded += MainWindow_Loaded;
            this.Closing += MainWindow_Closing;
        }

        private bool _hookService_KeyChanged(int vkCode, bool isDown)
        {
            if (!_isMappingMode)
            {
                return _mappingEngine.HandleKeyPress(vkCode, isDown);
            }
            return false;
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
            _isMappingMode = !_isMappingMode;
            if (_isMappingMode)
            {
                ToggleMappingBtn.Content = "Disable Mapping Mode";
                MappingCanvas.Visibility = Visibility.Visible;
                SaveBtn.Visibility = Visibility.Visible;
                this.Background = new SolidColorBrush(System.Windows.Media.Color.FromArgb(50, 0, 0, 0));
                SetClickThrough(false);

                if (_elements.Count == 0)
                {
                    AddMappingElement(new MappingElement { Name = "Fire", Type = ControlType.TapSpot, X = 50, Y = 50, BoundKey = "F" });
                }
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

        private void AddMappingElement(MappingElement element)
        {
            _elements.Add(element);

            Border border = new Border
            {
                Width = 50,
                Height = 50,
                Background = System.Windows.Media.Brushes.Red,
                CornerRadius = new CornerRadius(25),
                Opacity = 0.7,
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

            Canvas.SetLeft(border, (element.X / 100) * MappingCanvas.ActualWidth - 25);
            Canvas.SetTop(border, (element.Y / 100) * MappingCanvas.ActualHeight - 25);

            MappingCanvas.Children.Add(border);
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
            element.X = ((left + 25) / MappingCanvas.ActualWidth) * 100;
            element.Y = ((top + 25) / MappingCanvas.ActualHeight) * 100;
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
