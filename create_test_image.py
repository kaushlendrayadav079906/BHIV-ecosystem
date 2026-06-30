from PIL import Image, ImageDraw

# Create a synthetic plant-like test image (green leaf)
img = Image.new('RGB', (224, 224), color=(255, 255, 255))
draw = ImageDraw.Draw(img)

# Draw a green leaf shape
leaf_color = (34, 139, 34)  # Forest green
draw.ellipse([50, 50, 200, 200], fill=leaf_color, outline=(0, 100, 0), width=2)
draw.polygon([(100, 50), (150, 80), (140, 120), (160, 150), (120, 160), (80, 140), (90, 100), (70, 80)], 
             fill=leaf_color, outline=(0, 100, 0))

# Add some texture
for i in range(0, 224, 20):
    draw.line([(i, 0), (i, 224)], fill=(200, 220, 200), width=1)

img.save('test_leaf.jpg')
print("✅ Test image created: test_leaf.jpg")
