#!/bin/bash
# Generate all required icon sizes from your PNG

echo "🎨 Generating icon sizes from semanticsurf.png..."

# Check if sips is available (built into macOS)
if ! command -v sips &> /dev/null; then
    echo "❌ sips not found (should be on macOS)"
    exit 1
fi

# Create iconset directory
mkdir -p SemanticSurfer.iconset

# Source image
SOURCE="SemanticSurfer.iconset/semanticsurf.png"

if [ ! -f "$SOURCE" ]; then
    echo "❌ Source image not found: $SOURCE"
    exit 1
fi

# Generate all required sizes
echo "Generating sizes..."
sips -z 16 16     "$SOURCE" --out "SemanticSurfer.iconset/icon_16x16.png"
sips -z 32 32     "$SOURCE" --out "SemanticSurfer.iconset/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE" --out "SemanticSurfer.iconset/icon_32x32.png"
sips -z 64 64     "$SOURCE" --out "SemanticSurfer.iconset/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE" --out "SemanticSurfer.iconset/icon_128x128.png"
sips -z 256 256   "$SOURCE" --out "SemanticSurfer.iconset/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE" --out "SemanticSurfer.iconset/icon_256x256.png"
sips -z 512 512   "$SOURCE" --out "SemanticSurfer.iconset/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE" --out "SemanticSurfer.iconset/icon_512x512.png"
sips -z 1024 1024 "$SOURCE" --out "SemanticSurfer.iconset/icon_512x512@2x.png"

# Convert to .icns
echo "Converting to .icns..."
iconutil -c icns SemanticSurfer.iconset -o app-icon.icns

echo "✅ Icon created: app-icon.icns"
ls -lh app-icon.icns
