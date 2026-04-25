using System;

namespace KeyMapperPro.Models
{
    public enum ControlType
    {
        TapSpot,
        DPad,
        AimMode
    }

    public class MappingElement
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = "New Button";
        public ControlType Type { get; set; }
        public double X { get; set; } // Percentage 0-100
        public double Y { get; set; } // Percentage 0-100
        public string BoundKey { get; set; } = "None";

        // Visual Properties
        public string ColorHex { get; set; } = "#FF0000"; // Red
        public double Opacity { get; set; } = 0.7;
        public bool IsEnabled { get; set; } = true;
        public double Width { get; set; } = 50;
        public double Height { get; set; } = 50;

        // For DPad
        public double Radius { get; set; } = 10; // Percentage of window width

        // For AimMode
        public double Sensitivity { get; set; } = 1.0;
    }
}
