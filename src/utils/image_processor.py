"""
Image processing utilities for grid overlay and annotations
"""
from pathlib import Path
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
from src.config import GRID_SIZE


class ImageProcessor:
    """Process screenshots with grid overlays and annotations"""

    def __init__(self, grid_size: int = GRID_SIZE):
        self.grid_size = grid_size

    def add_grid_overlay(
        self,
        image_path: Path,
        output_path: Path,
        grid_color: Tuple[int, int, int, int] = (255, 0, 0, 128),
        label_color: Tuple[int, int, int] = (255, 0, 0)
    ) -> Path:
        """
        Add coordinate grid overlay to screenshot

        Args:
            image_path: Path to original screenshot
            output_path: Path to save annotated screenshot
            grid_color: RGBA color for grid lines
            label_color: RGB color for grid labels

        Returns:
            Path to annotated screenshot
        """
        # Open image
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        # Create transparent overlay
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        # Draw vertical grid lines and column labels (A, B, C...)
        col = 0
        for x in range(0, width, self.grid_size):
            # Draw vertical line
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)

            # Draw column label
            label = self._get_column_label(col)
            draw.text((x + 5, 5), label, fill=label_color, font=font)
            col += 1

        # Draw horizontal grid lines and row labels (1, 2, 3...)
        row = 1
        for y in range(0, height, self.grid_size):
            # Draw horizontal line
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)

            # Draw row label
            draw.text((5, y + 5), str(row), fill=label_color, font=font)
            row += 1

        # Composite images
        result = Image.alpha_composite(img, overlay)

        # Convert back to RGB for saving as PNG
        result_rgb = result.convert("RGB")
        result_rgb.save(output_path)

        return output_path

    def _get_column_label(self, col_index: int) -> str:
        """
        Convert column index to Excel-style label (A, B, C ... Z, AA, AB...)

        Args:
            col_index: Zero-based column index

        Returns:
            Column label string
        """
        label = ""
        col_index += 1  # Convert to 1-based

        while col_index > 0:
            col_index -= 1
            label = chr(65 + (col_index % 26)) + label
            col_index //= 26

        return label

    def get_grid_coordinates(self, x: int, y: int) -> str:
        """
        Convert pixel coordinates to grid cell identifier

        Args:
            x: X pixel coordinate
            y: Y pixel coordinate

        Returns:
            Grid cell identifier (e.g., "C4")
        """
        col = x // self.grid_size
        row = (y // self.grid_size) + 1

        return f"{self._get_column_label(col)}{row}"

    def highlight_region(
        self,
        image_path: Path,
        output_path: Path,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (255, 0, 0),
        border_width: int = 3
    ) -> Path:
        """
        Highlight a specific region on the screenshot

        Args:
            image_path: Path to original screenshot
            output_path: Path to save highlighted screenshot
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Width of highlight region
            height: Height of highlight region
            color: RGB color for highlight border
            border_width: Width of highlight border

        Returns:
            Path to highlighted screenshot
        """
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Draw rectangle
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            outline=color,
            width=border_width
        )

        img.save(output_path)
        return output_path


def demo_usage():
    """Demo usage of ImageProcessor"""
    from src.config import SCREENSHOTS_DIR

    processor = ImageProcessor(grid_size=100)

    # Example: Add grid to a screenshot
    input_path = SCREENSHOTS_DIR / "demo_screenshot.png"
    output_path = SCREENSHOTS_DIR / "demo_screenshot_grid.png"

    if input_path.exists():
        print(f"Adding grid overlay to {input_path}...")
        result_path = processor.add_grid_overlay(input_path, output_path)
        print(f"Grid overlay saved to: {result_path}")

        # Test coordinate conversion
        test_coords = [(150, 250), (500, 800), (1000, 1500)]
        print("\nCoordinate conversions:")
        for x, y in test_coords:
            grid_cell = processor.get_grid_coordinates(x, y)
            print(f"  Pixel ({x}, {y}) -> Grid cell {grid_cell}")
    else:
        print(f"Screenshot not found at {input_path}")
        print("Run the PlaywrightHelper demo first to create a screenshot.")


if __name__ == "__main__":
    demo_usage()
