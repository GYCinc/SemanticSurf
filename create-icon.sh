#!/bin/bash
# Create app icon for Semantic Server

echo "Creating Semantic Server icon..."

# Create iconset directory
mkdir -p SemanticSurfer.iconset

# Create a simple SVG icon (surfboard wave theme)
cat > temp-icon.svg << 'SVGEOF'
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4ade80;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#22c55e;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="180" fill="#1a1a2e"/>
  <path d="M 200 512 Q 512 300 824 512 Q 512 724 200 512" fill="url(#grad)" opacity="0.9"/>
  <circle cx="512" cy="512" r="80" fill="#4ade80"/>
  <text x="512" y="750" font-family="SF Pro Display, sans-serif" font-size="120" font-weight="bold" fill="#4ade80" text-anchor="middle">SS</text>
</svg>
SVGEOF

# Convert SVG to PNG at different sizes (requires ImageMagick or use online converter)
# For now, create placeholder instructions
echo "Icon SVG created: temp-icon.svg"
echo ""
echo "To complete icon creation:"
echo "1. Open temp-icon.svg in Preview or any image editor"
echo "2. Export as PNG at these sizes and save to SemanticSurfer.iconset/:"
echo "   - icon_16x16.png (16x16)"
echo "   - icon_16x16@2x.png (32x32)"
echo "   - icon_32x32.png (32x32)"
echo "   - icon_32x32@2x.png (64x64)"
echo "   - icon_128x128.png (128x128)"
echo "   - icon_128x128@2x.png (256x256)"
echo "   - icon_256x256.png (256x256)"
echo "   - icon_256x256@2x.png (512x512)"
echo "   - icon_512x512.png (512x512)"
echo "   - icon_512x512@2x.png (1024x1024)"
echo ""
echo "3. Then run: iconutil -c icns SemanticSurfer.iconset"
echo "4. Move SemanticSurfer.icns to your app bundle"
