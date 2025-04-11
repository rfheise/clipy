from enum import Enum

class Color(Enum):
    #crayon colors
    RED             = (255, 0, 0)
    SCARLET         = (255, 36, 0)      # Approximate
    ORANGE          = (255, 165, 0)
    YELLOW          = (255, 255, 0)
    LIME            = (191, 255, 0)     # Approximate
    GREEN           = (0, 128, 0)
    BLUE_GREEN      = (13, 152, 186)    # Approximate
    BLUE            = (0, 0, 255)
    VIOLET_BLUE     = (50, 74, 178)     # Approximate
    VIOLET          = (238, 130, 238)
    MAGENTA         = (255, 0, 255)
    BROWN           = (165, 42, 42)
    BLACK           = (0, 0, 0)
    WHITE           = (255, 255, 255)
    GRAY            = (128, 128, 128)
    BLUE_VIOLET     = (138, 43, 226)    # Approximate
    GOLDENROD       = (218, 165, 32)
    SKY_BLUE        = (135, 206, 235)
    BURNT_ORANGE    = (204, 85, 0)
    BRICK_RED       = (156, 102, 31)    # Approximate
    MAHOGANY        = (192, 64, 0)      # Approximate
    CERULEAN        = (29, 172, 214)
    PERIWINKLE      = (204, 204, 255)   # Approximate light periwinkle
    YELLOW_ORANGE   = (255, 174, 66)

bright_colors = [
    Color.RED.value,
    Color.ORANGE.value,
    Color.YELLOW.value,
    Color.LIME.value,
    Color.GREEN.value,
    Color.BLUE_GREEN.value,
    Color.BLUE.value,
    Color.VIOLET_BLUE.value,
    Color.VIOLET.value,
    Color.MAGENTA.value,
]
all_colors = [color.value for color in Color]