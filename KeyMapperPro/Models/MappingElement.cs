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
        public string Name { get; set; }
        public ControlType Type { get; set; }
        public double X { get; set; } // Percentage 0-100
        public double Y { get; set; } // Percentage 0-100
        public string BoundKey { get; set; }

        // For DPad
        public double Radius { get; set; } = 10; // Percentage of window width

        // For AimMode
        public double Sensitivity { get; set; } = 1.0;
    }
}
