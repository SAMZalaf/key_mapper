using Xunit;
using KeyMapperPro.Services;
using KeyMapperPro.Models;
using System.Collections.Generic;
using System.IO;

namespace KeyMapperPro.Tests
{
    public class ProfileServiceTests
    {
        [Fact]
        public void SaveAndLoadProfile_ShouldBeEqual()
        {
            var service = new ProfileService();
            var elements = new List<MappingElement>
            {
                new MappingElement { Name = "Test", Type = ControlType.TapSpot, X = 10, Y = 20, BoundKey = "X" }
            };
            string filePath = "test_profile.json";

            service.SaveProfile(filePath, elements);
            var loadedElements = service.LoadProfile(filePath);

            Assert.Single(loadedElements);
            Assert.Equal(elements[0].Name, loadedElements[0].Name);
            Assert.Equal(elements[0].X, loadedElements[0].X);
            Assert.Equal(elements[0].Y, loadedElements[0].Y);
            Assert.Equal(elements[0].BoundKey, loadedElements[0].BoundKey);

            if (File.Exists(filePath)) File.Delete(filePath);
        }
    }
}
