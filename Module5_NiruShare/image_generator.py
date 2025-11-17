"""
Image generation service for creating shareable social media images
"""
import os
from typing import Optional, Dict, List, Tuple
from io import BytesIO
import base64

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageGenerator:
    """Generate styled images from text content"""
    
    # Default image dimensions (Instagram post size)
    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1080
    
    # Color schemes
    COLOR_SCHEMES = {
        "default": {
            "background": (255, 255, 255),
            "text": (0, 0, 0),
            "accent": (0, 102, 204),
        },
        "dark": {
            "background": (26, 26, 46),
            "text": (255, 255, 255),
            "accent": (100, 200, 255),
        },
        "professional": {
            "background": (245, 245, 250),
            "text": (30, 30, 30),
            "accent": (0, 120, 212),
        },
        "vibrant": {
            "background": (255, 255, 255),
            "text": (20, 20, 20),
            "accent": (255, 87, 34),
        },
    }
    
    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        """
        Initialize image generator
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow (PIL) is required for image generation. "
                "Install with: pip install Pillow"
            )
        
        self.width = width
        self.height = height
        self._fonts = {}
    
    def _get_font(self, size: int, bold: bool = False) -> Optional[ImageFont.FreeTypeFont]:
        """Get font with caching"""
        key = (size, bold)
        if key in self._fonts:
            return self._fonts[key]
        
        try:
            # Try to use system fonts
            if bold:
                font_paths = [
                    "/System/Library/Fonts/Helvetica.ttc",  # macOS
                    "C:/Windows/Fonts/arialbd.ttf",  # Windows
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                ]
            else:
                font_paths = [
                    "/System/Library/Fonts/Helvetica.ttc",  # macOS
                    "C:/Windows/Fonts/arial.ttf",  # Windows
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    self._fonts[key] = font
                    return font
            
            # Fallback to default font
            font = ImageFont.load_default()
            self._fonts[key] = font
            return font
        
        except Exception:
            # Ultimate fallback
            return ImageFont.load_default()
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            # Get word width
            bbox = font.getbbox(word)
            word_width = bbox[2] - bbox[0]
            
            # Check if adding this word would exceed max width
            if current_width + word_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width + font.getbbox(" ")[2]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def generate_image(
        self,
        text: str,
        title: Optional[str] = None,
        color_scheme: str = "default",
        width: Optional[int] = None,
        height: Optional[int] = None,
        padding: int = 60,
    ) -> Image.Image:
        """
        Generate image from text content
        
        Args:
            text: Main text content
            title: Optional title text
            color_scheme: Color scheme name
            width: Image width (uses default if not provided)
            height: Image height (uses default if not provided)
            padding: Padding in pixels
        
        Returns:
            PIL Image object
        """
        width = width or self.width
        height = height or self.height
        
        # Get color scheme
        colors = self.COLOR_SCHEMES.get(color_scheme, self.COLOR_SCHEMES["default"])
        
        # Create image
        img = Image.new("RGB", (width, height), colors["background"])
        draw = ImageDraw.Draw(img)
        
        # Calculate available text area
        text_area_width = width - (padding * 2)
        text_area_height = height - (padding * 2)
        
        # Draw title if provided
        y_offset = padding
        if title:
            title_font = self._get_font(48, bold=True)
            title_lines = self._wrap_text(title, title_font, text_area_width)
            
            for line in title_lines:
                bbox = title_font.getbbox(line)
                line_height = bbox[3] - bbox[1] + 10
                
                # Center title
                x = (width - bbox[2]) // 2
                draw.text((x, y_offset), line, fill=colors["accent"], font=title_font)
                y_offset += line_height
            
            y_offset += 30  # Space after title
        
        # Draw main text
        body_font = self._get_font(36, bold=False)
        text_lines = self._wrap_text(text, body_font, text_area_width)
        
        available_height = height - y_offset - padding
        line_height = body_font.getbbox("A")[3] - body_font.getbbox("A")[1] + 15
        
        # Calculate how many lines fit
        max_lines = available_height // line_height
        text_lines = text_lines[:max_lines]
        
        for line in text_lines:
            if y_offset + line_height > height - padding:
                break
            
            bbox = body_font.getbbox(line)
            x = (width - bbox[2]) // 2  # Center text
            draw.text((x, y_offset), line, fill=colors["text"], font=body_font)
            y_offset += line_height
        
        # Add branding at bottom
        branding_font = self._get_font(24, bold=False)
        branding_text = "AmaniQuery"
        bbox = branding_font.getbbox(branding_text)
        x = (width - bbox[2]) // 2
        y = height - padding - 30
        draw.text((x, y), branding_text, fill=colors["accent"], font=branding_font)
        
        return img
    
    def generate_image_bytes(
        self,
        text: str,
        title: Optional[str] = None,
        color_scheme: str = "default",
        format: str = "PNG",
        **kwargs
    ) -> bytes:
        """
        Generate image as bytes
        
        Args:
            text: Main text content
            title: Optional title text
            color_scheme: Color scheme name
            format: Image format (PNG, JPEG)
            **kwargs: Additional arguments for generate_image
        
        Returns:
            Image bytes
        """
        img = self.generate_image(text, title, color_scheme, **kwargs)
        
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_image_base64(
        self,
        text: str,
        title: Optional[str] = None,
        color_scheme: str = "default",
        format: str = "PNG",
        **kwargs
    ) -> str:
        """
        Generate image as base64 string
        
        Args:
            text: Main text content
            title: Optional title text
            color_scheme: Color scheme name
            format: Image format (PNG, JPEG)
            **kwargs: Additional arguments for generate_image
        
        Returns:
            Base64 encoded image string
        """
        img_bytes = self.generate_image_bytes(text, title, color_scheme, format, **kwargs)
        return base64.b64encode(img_bytes).decode("utf-8")
    
    def generate_from_post(
        self,
        post_content: str,
        query: Optional[str] = None,
        color_scheme: str = "default",
        **kwargs
    ) -> Image.Image:
        """
        Generate image from formatted post content
        
        Args:
            post_content: Formatted post content
            query: Original query (used as title)
            color_scheme: Color scheme name
            **kwargs: Additional arguments for generate_image
        
        Returns:
            PIL Image object
        """
        # Use query as title if available, otherwise use first line
        title = None
        text = post_content
        
        if query:
            title = query
        else:
            # Extract first sentence or line as title
            lines = post_content.split("\n")
            if lines:
                first_line = lines[0].strip()
                if len(first_line) < 100:
                    title = first_line
                    text = "\n".join(lines[1:]).strip()
        
        return self.generate_image(text, title, color_scheme, **kwargs)

