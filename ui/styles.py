NEON_GREEN = "#39FF14"
NEON_BLUE = "#00BFFF"
DARK_BG = "#000000"  # Changed from #121212 to #000000 for pure black

GLOBAL_STYLE = f"""
QWidget {{
    background-color: {DARK_BG};
    color: {NEON_GREEN};
    border-radius: 4px;
}}

QPushButton {{
    background-color: {DARK_BG};
    color: {NEON_GREEN};
    border: 2px solid {NEON_GREEN};
    padding: 5px 15px;
    border-radius: 4px;
}}

QPushButton:hover {{
    background-color: {NEON_GREEN};
    color: {DARK_BG};
}}

QComboBox {{
    background-color: {DARK_BG};
    color: {NEON_GREEN};
    border: 2px solid {NEON_GREEN};
    padding: 5px;
    border-radius: 4px;
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 2px solid {NEON_GREEN};
    border-bottom: 2px solid {NEON_GREEN};
    width: 8px;
    height: 8px;
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {DARK_BG};
    color: {NEON_GREEN};
    selection-background-color: {NEON_GREEN};
    selection-color: {DARK_BG};
    border: 2px solid {NEON_GREEN};
}}

QLabel {{
    color: {NEON_GREEN};
}}

QTextEdit, QLineEdit {{
    background-color: {DARK_BG};
    color: {NEON_GREEN};
    border: 2px solid {NEON_GREEN};
    border-radius: 4px;
    padding: 5px;
}}
"""
