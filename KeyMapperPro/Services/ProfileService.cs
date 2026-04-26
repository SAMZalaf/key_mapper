using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using KeyMapperPro.Models;

namespace KeyMapperPro.Services
{
    public class ProfileService
    {
        private static readonly JsonSerializerOptions _options = new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNameCaseInsensitive = true
        };

        public void SaveProfile(string filePath, List<MappingElement> elements)
        {
            var json = JsonSerializer.Serialize(elements, _options);
            File.WriteAllText(filePath, json);
        }

        public List<MappingElement> LoadProfile(string filePath)
        {
            if (!File.Exists(filePath))
                return new List<MappingElement>();

            var json = File.ReadAllText(filePath);
            return JsonSerializer.Deserialize<List<MappingElement>>(json, _options) ?? new List<MappingElement>();
        }
    }
}
