from openpyxl.styles import Alignment, Font, Border, Side, PatternFill


# Alignment
CENTER = Alignment(horizontal='center', vertical='center')
CENTER_WRAP = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT = Alignment(horizontal='left', vertical='center')

# Fonts
BOLD = Font(bold=True)
TITLE_FONT = Font(bold=True, size=12)
RED_BOLD = Font(color="FF0000", bold=True)

# Borders
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Fills
YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
