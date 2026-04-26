using System;
using System.Windows;
using KeyMapperPro.Models;

namespace KeyMapperPro.Views
{
    public partial class SettingsWindow : Window
    {
        public event Action<ControlType>? OnAddElement;
        public event Action<MappingElement>? OnUpdateElement;

        private MappingElement? _editingElement;

        public SettingsWindow()
        {
            InitializeComponent();
        }

        private void AddTapSpotBtn_Click(object sender, RoutedEventArgs e)
        {
            OnAddElement?.Invoke(ControlType.TapSpot);
        }

        private void AddDPadBtn_Click(object sender, RoutedEventArgs e)
        {
            OnAddElement?.Invoke(ControlType.DPad);
        }

        private void AddAimModeBtn_Click(object sender, RoutedEventArgs e)
        {
            OnAddElement?.Invoke(ControlType.AimMode);
        }

        public void EditElement(MappingElement element)
        {
            _editingElement = element;
            PropertiesPanel.Visibility = Visibility.Visible;
            PropName.Text = element.Name;
            PropKey.Text = element.BoundKey;
            PropOpacity.Value = element.Opacity;
            PropColor.Text = element.ColorHex;
            PropWidth.Text = element.Width.ToString();
            PropHeight.Text = element.Height.ToString();
        }

        private void ApplyBtn_Click(object sender, RoutedEventArgs e)
        {
            if (_editingElement == null) return;

            _editingElement.Name = PropName.Text;
            _editingElement.BoundKey = PropKey.Text;
            _editingElement.Opacity = PropOpacity.Value;
            _editingElement.ColorHex = PropColor.Text;

            if (double.TryParse(PropWidth.Text, out double w)) _editingElement.Width = w;
            if (double.TryParse(PropHeight.Text, out double h)) _editingElement.Height = h;

            OnUpdateElement?.Invoke(_editingElement);
            // We keep the panel open for further adjustments if needed, or hide it.
            // PropertiesPanel.Visibility = Visibility.Collapsed;
        }

        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            e.Cancel = true;
            this.Hide();
        }
    }
}
