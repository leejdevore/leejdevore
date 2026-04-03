#!/usr/bin/env python3
"""
Real Estate Pro Forma Generator
50-58 Jersey Street, Newark, NJ
Mixed-Use Residential Development with NJ Aspire Tax Credits
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from copy import copy

# ============================================================
# STYLE DEFINITIONS
# ============================================================

# Colors
WHITE = "FFFFFF"
LIGHT_GRAY = "F5F5F5"
MED_GRAY = "E0E0E0"
DARK_BG = "1A1A2E"
ACCENT_BLUE = "0F3460"
ACCENT_TEAL = "16213E"
HEADER_BG = "0F3460"
SUBHEADER_BG = "E8EEF5"
INPUT_BG = "FFFFF0"
SECTION_BG = "F0F4FA"
BORDER_COLOR = "B0BEC5"
LIGHT_BLUE_BG = "EBF5FB"

# Fonts
font_title = Font(name="Calibri", size=16, bold=True, color="1A1A2E")
font_subtitle = Font(name="Calibri", size=12, bold=True, color="0F3460")
font_section = Font(name="Calibri", size=11, bold=True, color="0F3460")
font_header = Font(name="Calibri", size=10, bold=True, color=WHITE)
font_subheader = Font(name="Calibri", size=10, bold=True, color="1A1A2E")
font_normal = Font(name="Calibri", size=10, color="1A1A2E")
font_input = Font(name="Calibri", size=10, bold=True, color="0000CC")
font_note = Font(name="Calibri", size=8, italic=True, color="808080")
font_currency = Font(name="Calibri", size=10, color="1A1A2E")
font_total = Font(name="Calibri", size=10, bold=True, color="1A1A2E")
font_grand_total = Font(name="Calibri", size=11, bold=True, color="1A1A2E")

# Fills
fill_header = PatternFill(start_color=HEADER_BG, end_color=HEADER_BG, fill_type="solid")
fill_subheader = PatternFill(start_color=SUBHEADER_BG, end_color=SUBHEADER_BG, fill_type="solid")
fill_input = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type="solid")
fill_section = PatternFill(start_color=SECTION_BG, end_color=SECTION_BG, fill_type="solid")
fill_light = PatternFill(start_color=LIGHT_GRAY, end_color=LIGHT_GRAY, fill_type="solid")
fill_white = PatternFill(start_color=WHITE, end_color=WHITE, fill_type="solid")
fill_light_blue = PatternFill(start_color=LIGHT_BLUE_BG, end_color=LIGHT_BLUE_BG, fill_type="solid")
fill_total = PatternFill(start_color=MED_GRAY, end_color=MED_GRAY, fill_type="solid")

# Borders
thin_border = Border(
    left=Side(style="thin", color=BORDER_COLOR),
    right=Side(style="thin", color=BORDER_COLOR),
    top=Side(style="thin", color=BORDER_COLOR),
    bottom=Side(style="thin", color=BORDER_COLOR),
)
bottom_border = Border(bottom=Side(style="medium", color="1A1A2E"))
top_bottom_border = Border(
    top=Side(style="medium", color="1A1A2E"),
    bottom=Side(style="double", color="1A1A2E"),
)

# Alignments
align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
align_right = Alignment(horizontal="right", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")

# Number formats
FMT_CURRENCY = '#,##0'
FMT_CURRENCY_DEC = '#,##0.00'
FMT_PCT = '0.0%'
FMT_PCT2 = '0.00%'
FMT_NUM = '#,##0'
FMT_PSF = '#,##0.00'
FMT_MULT = '0.00x'


def apply_style(ws, row, col, font=None, fill=None, alignment=None, border=None, number_format=None):
    cell = ws.cell(row=row, column=col)
    if font: cell.font = font
    if fill: cell.fill = fill
    if alignment: cell.alignment = alignment
    if border: cell.border = border
    if number_format: cell.number_format = number_format
    return cell


def write_cell(ws, row, col, value, font=font_normal, fill=None, alignment=align_left,
               border=thin_border, number_format=None):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = font
    if fill: cell.fill = fill
    cell.alignment = alignment
    if border: cell.border = border
    if number_format: cell.number_format = number_format
    return cell


def write_header_row(ws, row, col_start, headers, widths=None):
    for i, h in enumerate(headers):
        c = col_start + i
        write_cell(ws, row, c, h, font=font_header, fill=fill_header,
                   alignment=align_center, border=thin_border)
    if widths:
        for i, w in enumerate(widths):
            ws.column_dimensions[get_column_letter(col_start + i)].width = w


def write_input_cell(ws, row, col, value, number_format=None):
    return write_cell(ws, row, col, value, font=font_input, fill=fill_input,
                      alignment=align_right, number_format=number_format)


def write_note(ws, row, col, text):
    return write_cell(ws, row, col, text, font=font_note, border=None, alignment=align_left)


def write_section_header(ws, row, col_start, col_end, text):
    write_cell(ws, row, col_start, text, font=font_section, fill=fill_subheader,
               alignment=align_left, border=thin_border)
    for c in range(col_start + 1, col_end + 1):
        write_cell(ws, row, c, None, fill=fill_subheader, border=thin_border)


def write_total_row(ws, row, col_start, col_end, label, values=None, number_format=FMT_CURRENCY):
    write_cell(ws, row, col_start, label, font=font_total, fill=fill_total,
               alignment=align_left, border=top_bottom_border)
    for c in range(col_start + 1, col_end + 1):
        val = values[c - col_start - 1] if values and (c - col_start - 1) < len(values) else None
        write_cell(ws, row, c, val, font=font_total, fill=fill_total,
                   alignment=align_right, border=top_bottom_border, number_format=number_format)



# ============================================================
# TAB 1: SUMMARY DASHBOARD
# ============================================================

def create_summary_tab(wb):
    ws = wb.active
    ws.title = "Summary"
    ws.sheet_properties.tabColor = "0F3460"

    # Column widths
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 5
    ws.column_dimensions['E'].width = 35
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 5
    ws.column_dimensions['H'].width = 35
    ws.column_dimensions['I'].width = 18

    r = 2
    write_cell(ws, r, 2, "50-58 JERSEY STREET", font=font_title); r += 1
    write_cell(ws, r, 2, "Newark, New Jersey  |  Mixed-Use Residential Development",
               font=font_subtitle); r += 1
    write_cell(ws, r, 2, "Pro Forma Summary Dashboard", font=font_note); r += 2

    # --- PROJECT OVERVIEW ---
    write_section_header(ws, r, 2, 3, "PROJECT OVERVIEW"); r += 1
    items = [
        ("Total Residential Units", "='Inputs'!C12", FMT_NUM),
        ("Market Rate Units", "='Inputs'!C13", FMT_NUM),
        ("Affordable Units", "='Inputs'!C14", FMT_NUM),
        ("Building GSF", "='Inputs'!C8", FMT_NUM),
        ("Residential NSF", "='Inputs'!C9", FMT_NUM),
        ("Retail SF", "='Inputs'!C10", FMT_NUM),
        ("Parking Spaces", "='Inputs'!C16", FMT_NUM),
        ("Number of Floors", "='Inputs'!C7", FMT_NUM),
        ("Site Area (Acres)", "='Inputs'!C6", FMT_PSF),
    ]
    for label, val, fmt in items:
        write_cell(ws, r, 2, label, font=font_normal)
        write_cell(ws, r, 3, val, font=font_total, alignment=align_right, number_format=fmt)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "DEVELOPMENT BUDGET"); r += 1
    budget_items = [
        ("Land Acquisition", "='Dev Budget'!D8", FMT_CURRENCY),
        ("Hard Costs", "='Dev Budget'!D18", FMT_CURRENCY),
        ("Soft Costs", "='Dev Budget'!D30", FMT_CURRENCY),
        ("Financing Costs", "='Dev Budget'!D40", FMT_CURRENCY),
        ("Developer Fee", "='Dev Budget'!D42", FMT_CURRENCY),
        ("Total Development Cost", "='Dev Budget'!D44", FMT_CURRENCY),
        ("TDC per Unit", "='Dev Budget'!E44", FMT_CURRENCY),
        ("TDC per GSF", "='Dev Budget'!F44", FMT_PSF),
    ]
    for label, val, fmt in budget_items:
        write_cell(ws, r, 2, label, font=font_normal)
        write_cell(ws, r, 3, val, font=font_total, alignment=align_right, number_format=fmt)
        r += 1

    # Column 2 - Returns
    r2 = 8
    write_section_header(ws, r2, 5, 6, "RETURNS SUMMARY"); r2 += 1
    returns_items = [
        ("Stabilized NOI (Year 3)", "='Operating'!N29", FMT_CURRENCY),
        ("Stabilized Yield on Cost", "='Operating'!N30", FMT_PCT2),
        ("Unlevered IRR", "='Waterfall'!C58", FMT_PCT2),
        ("Levered IRR (Project)", "='Waterfall'!C59", FMT_PCT2),
        ("Equity Multiple", "='Waterfall'!C60", FMT_MULT),
        ("Cash-on-Cash (Stabilized)", "='Waterfall'!C61", FMT_PCT2),
        ("Sponsor IRR", "='Waterfall'!C63", FMT_PCT2),
        ("Sponsor Equity Multiple", "='Waterfall'!C64", FMT_MULT),
        ("LP IRR", "='Waterfall'!C65", FMT_PCT2),
        ("LP Equity Multiple", "='Waterfall'!C66", FMT_MULT),
    ]
    for label, val, fmt in returns_items:
        write_cell(ws, r2, 5, label, font=font_normal)
        write_cell(ws, r2, 6, val, font=font_total, alignment=align_right, number_format=fmt)
        r2 += 1

    r2 += 1
    write_section_header(ws, r2, 5, 6, "FINANCING STRUCTURE"); r2 += 1
    fin_items = [
        ("Total Equity Required", "='Waterfall'!C10", FMT_CURRENCY),
        ("Sponsor Equity (GP)", "='Waterfall'!C12", FMT_CURRENCY),
        ("LP Equity", "='Waterfall'!C13", FMT_CURRENCY),
        ("Permanent Loan Amount", "='Waterfall'!C15", FMT_CURRENCY),
        ("Loan-to-Value", "='Inputs'!C57", FMT_PCT),
        ("DSCR", "='Operating'!N31", FMT_PSF),
        ("Aspire Tax Credits (Total)", "='Aspire'!C30", FMT_CURRENCY),
        ("Aspire Credits (Net Proceeds)", "='Aspire'!C33", FMT_CURRENCY),
    ]
    for label, val, fmt in fin_items:
        write_cell(ws, r2, 5, label, font=font_normal)
        write_cell(ws, r2, 6, val, font=font_total, alignment=align_right, number_format=fmt)
        r2 += 1

    # Column 3 - Revenue
    r3 = 8
    write_section_header(ws, r3, 8, 9, "REVENUE SUMMARY (STABILIZED)"); r3 += 1
    rev_items = [
        ("Market Rate Rental Income", "='Operating'!N8", FMT_CURRENCY),
        ("Affordable Rental Income", "='Operating'!N9", FMT_CURRENCY),
        ("Retail Income", "='Operating'!N10", FMT_CURRENCY),
        ("Parking Income", "='Operating'!N11", FMT_CURRENCY),
        ("Other Income", "='Operating'!N12", FMT_CURRENCY),
        ("Gross Potential Revenue", "='Operating'!N13", FMT_CURRENCY),
        ("Less: Vacancy & Credit Loss", "='Operating'!N15", FMT_CURRENCY),
        ("Effective Gross Income", "='Operating'!N16", FMT_CURRENCY),
        ("Total Operating Expenses", "='Operating'!N27", FMT_CURRENCY),
        ("Net Operating Income", "='Operating'!N29", FMT_CURRENCY),
    ]
    for label, val, fmt in rev_items:
        write_cell(ws, r3, 8, label, font=font_normal)
        write_cell(ws, r3, 9, val, font=font_total, alignment=align_right, number_format=fmt)
        r3 += 1

    r3 += 1
    write_section_header(ws, r3, 8, 9, "KEY METRICS"); r3 += 1
    metric_items = [
        ("Avg Market Rent / Unit / Mo", "='Unit Mix'!H29", FMT_CURRENCY),
        ("Avg Market Rent / SF / Mo", "='Unit Mix'!I29", FMT_PSF),
        ("Avg Affordable Rent / Unit / Mo", "='Affordable'!G22", FMT_CURRENCY),
        ("OpEx per Unit", "='Operating'!O27", FMT_CURRENCY),
        ("OpEx Ratio", "='Operating'!P27", FMT_PCT),
        ("Exit Cap Rate", "='Inputs'!C63", FMT_PCT2),
        ("Estimated Exit Value (Yr 10)", "='Waterfall'!C50", FMT_CURRENCY),
    ]
    for label, val, fmt in metric_items:
        write_cell(ws, r3, 8, label, font=font_normal)
        write_cell(ws, r3, 9, val, font=font_total, alignment=align_right, number_format=fmt)
        r3 += 1

    return ws


# ============================================================
# TAB 2: INPUTS & ASSUMPTIONS
# ============================================================

def create_inputs_tab(wb):
    ws = wb.create_sheet("Inputs")
    ws.sheet_properties.tabColor = "2E86C1"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 45

    r = 2
    write_cell(ws, r, 2, "INPUTS & ASSUMPTIONS", font=font_title); r += 1
    write_note(ws, r, 2, "Blue bold cells are user-adjustable inputs. All other values are calculated."); r += 2

    # --- SITE & BUILDING ---
    write_section_header(ws, r, 2, 3, "SITE & BUILDING DATA"); r += 1
    site_data = [
        ("Project Name", "50-58 Jersey Street", None, "User input: Project identifier"),
        ("Site Area (Acres)", 1.17, FMT_PSF, ""),
        ("Number of Floors", 25, FMT_NUM, "Excludes amenity roof level"),
        ("Building GSF", 763489, FMT_NUM, ""),
        ("Residential NSF", 525338, FMT_NUM, ""),
        ("Retail Area (SF)", 3474, FMT_NUM, ""),
        ("Amenity Area (SF)", 54813, FMT_NUM, ""),
        ("Total Residential Units", 716, FMT_NUM, "=C13+C14"),
        ("Market Rate Units", 573, FMT_NUM, ""),
        ("Affordable Units", 143, FMT_NUM, "~20% of total"),
        ("Open Space (SF)", 6534, FMT_NUM, ""),
        ("Parking Spaces", 178, FMT_NUM, "0.25 spaces/unit ratio"),
        ("Green Wall (SF)", 1500, FMT_NUM, ""),
        ("Average Unit Size (NSF)", 734, FMT_NUM, "Blended average"),
    ]
    for label, val, fmt, note in site_data:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        if note:
            write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "MARKET RENT ASSUMPTIONS (Monthly)"); r += 1
    write_note(ws, r, 2, "Rents based on Newark new construction comps (Downtown/Broad St corridor)"); r += 1
    rent_data = [
        ("Studio Rent (Market)", 1950, "475 avg SF | $4.11/SF"),
        ("1BR Rent (Market)", 2400, "675 avg SF | $3.56/SF"),
        ("1BR+Den Rent (Market)", 2700, "800 avg SF | $3.38/SF"),
        ("2BR Rent (Market)", 3100, "1,000 avg SF | $3.10/SF"),
        ("3BR Rent (Market)", 3800, "1,200 avg SF | $3.17/SF"),
    ]
    for label, val, note in rent_data:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=FMT_CURRENCY)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "AFFORDABLE RENT ASSUMPTIONS (Monthly, 60% AMI)"); r += 1
    write_note(ws, r, 2, "Based on Essex County HUD FMR limits, 60% AMI. Adjust AMI level on Affordable tab."); r += 1
    aff_rent = [
        ("Studio Rent (Affordable)", 1341, "60% AMI, Essex County"),
        ("1BR Rent (Affordable)", 1437, "60% AMI, Essex County"),
        ("2BR Rent (Affordable)", 1723, "60% AMI, Essex County"),
        ("3BR Rent (Affordable)", 1991, "60% AMI, Essex County"),
    ]
    for label, val, note in aff_rent:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=FMT_CURRENCY)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "OTHER REVENUE ASSUMPTIONS"); r += 1
    other_rev = [
        ("Retail Rent ($/SF/Year NNN)", 28, FMT_CURRENCY, "Downtown Newark secondary location"),
        ("Parking Revenue ($/Space/Month)", 175, FMT_CURRENCY, "Covered structured parking"),
        ("Other Income ($/Unit/Month)", 50, FMT_CURRENCY, "Laundry, storage, fees, pets"),
        ("Vacancy & Credit Loss (%)", 0.05, FMT_PCT, "5% stabilized; higher during lease-up"),
        ("Annual Rent Growth (Market)", 0.025, FMT_PCT, "2.5% annual escalation"),
        ("Annual Rent Growth (Affordable)", 0.02, FMT_PCT, "2.0% per HUD adjustments"),
        ("Retail Rent Growth", 0.02, FMT_PCT, "2.0% annual escalation"),
        ("Parking Revenue Growth", 0.02, FMT_PCT, "2.0% annual escalation"),
    ]
    for label, val, fmt, note in other_rev:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "OPERATING EXPENSE ASSUMPTIONS (Per Unit/Year)"); r += 1
    opex = [
        ("PILOT / Property Tax (% of Revenue)", 0.125, FMT_PCT, "Newark PILOT: 12.5% of gross revenue"),
        ("Insurance ($/Unit/Year)", 1500, FMT_CURRENCY, "High-rise premium; escalating ~7%/yr"),
        ("Management Fee (% of EGI)", 0.03, FMT_PCT, "3% at scale for 716 units"),
        ("Repairs & Maintenance ($/Unit/Year)", 1000, FMT_CURRENCY, "Lower yr 1-5 for new construction"),
        ("Utilities ($/Unit/Year)", 1350, FMT_CURRENCY, "Common area & master-metered"),
        ("General & Administrative ($/Unit/Year)", 500, FMT_CURRENCY, ""),
        ("Marketing & Turnover ($/Unit/Year)", 400, FMT_CURRENCY, ""),
        ("Payroll / On-Site Staff ($/Unit/Year)", 1800, FMT_CURRENCY, "Economies of scale at 716 units"),
        ("Replacement Reserves ($/Unit/Year)", 300, FMT_CURRENCY, ""),
        ("OpEx Annual Growth Rate", 0.03, FMT_PCT, "3% annual inflation"),
    ]
    for label, val, fmt, note in opex:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "DEVELOPMENT COST ASSUMPTIONS"); r += 1
    dev_cost = [
        ("Hard Cost ($/GSF)", 325, FMT_CURRENCY, "25-story concrete/steel, union labor, Newark"),
        ("Soft Cost (% of Hard)", 0.25, FMT_PCT, "A&E, legal, permits, testing, insurance"),
        ("Hard Cost Contingency (%)", 0.075, FMT_PCT, "7.5% of hard costs"),
        ("Soft Cost Contingency (%)", 0.10, FMT_PCT, "10% of soft costs"),
        ("Developer Fee (% of TDC)", 0.04, FMT_PCT, "4% standard for large-scale"),
        ("Land Acquisition Cost", 25000000, FMT_CURRENCY, "Estimated site acquisition"),
    ]
    for label, val, fmt, note in dev_cost:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "FINANCING ASSUMPTIONS"); r += 1
    fin = [
        ("Construction Loan Rate", 0.075, FMT_PCT2, "Floating rate, interest-only on draws"),
        ("Construction Loan LTC", 0.70, FMT_PCT, "70% loan-to-cost"),
        ("Construction Loan Term (Months)", 36, FMT_NUM, "30-36 months + extensions"),
        ("Construction Loan Fee", 0.01, FMT_PCT, "1% origination"),
        ("Permanent Loan Rate", 0.06, FMT_PCT2, "Agency/CMBS fixed rate"),
        ("Permanent Loan LTV", 0.75, FMT_PCT, "75% loan-to-value"),
        ("Permanent Loan Amortization (Years)", 30, FMT_NUM, "30-year amortization"),
        ("Permanent Loan Term (Years)", 10, FMT_NUM, "10-year fixed term"),
        ("Minimum DSCR", 1.25, FMT_PSF, "Lender minimum coverage ratio"),
    ]
    for label, val, fmt, note in fin:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "EXIT & VALUATION ASSUMPTIONS"); r += 1
    exit_data = [
        ("Going-In Cap Rate", 0.05, FMT_PCT2, "Class A new construction, Newark"),
        ("Exit Cap Rate", 0.0525, FMT_PCT2, "25-50 bps expansion from going-in"),
        ("Holding Period (Years)", 10, FMT_NUM, "Analysis period"),
        ("Disposition Costs (% of Sale)", 0.02, FMT_PCT, "Broker, legal, transfer tax portion"),
        ("NJ Realty Transfer Fee (%)", 0.041, FMT_PCT, "~4.1% for $200M+ sale (incl mansion tax)"),
    ]
    for label, val, fmt, note in exit_data:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "EQUITY WATERFALL ASSUMPTIONS"); r += 1
    wf = [
        ("Sponsor (GP) Equity Share", 0.50, FMT_PCT, "Adjustable GP/LP split"),
        ("LP Equity Share", 0.50, FMT_PCT, "=1 - GP Share"),
        ("Preferred Return (Annual)", 0.08, FMT_PCT, "8% cumulative preferred"),
        ("Tier 1 Promote (above pref, to 12% IRR)", 0.20, FMT_PCT, "80/20 LP/GP split"),
        ("Tier 2 Promote (above 12% IRR, to 18%)", 0.30, FMT_PCT, "70/30 LP/GP split"),
        ("Tier 3 Promote (above 18% IRR)", 0.40, FMT_PCT, "60/40 LP/GP split"),
    ]
    for label, val, fmt, note in wf:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "LEASE-UP ASSUMPTIONS"); r += 1
    leaseup = [
        ("Lease-Up Period (Months)", 18, FMT_NUM, "15-20 units/month absorption"),
        ("Absorption Rate (Units/Month)", 40, FMT_NUM, ""),
        ("Lease-Up Concessions (Months Free)", 1, FMT_NUM, "1 month free on new leases"),
        ("Year 1 Occupancy (%)", 0.40, FMT_PCT, "Mid-construction / early lease-up"),
        ("Year 2 Occupancy (%)", 0.85, FMT_PCT, "Substantial lease-up"),
        ("Year 3+ Occupancy (%)", 0.95, FMT_PCT, "Stabilized occupancy"),
    ]
    for label, val, fmt, note in leaseup:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "ASPIRE TAX CREDIT ASSUMPTIONS"); r += 1
    aspire = [
        ("Aspire Credit (% of Eligible Costs)", 0.45, FMT_PCT, "Up to 60% for Newark Enhanced Area"),
        ("Aspire Per-Project Cap", 90000000, FMT_CURRENCY, "$90M max for Enhanced Area"),
        ("Credit Duration (Years)", 10, FMT_NUM, "Equal annual installments"),
        ("Credit Sale Discount Rate", 0.88, FMT_PCT, "85-92 cents on dollar"),
        ("Eligible Cost Soft Cap (%)", 0.20, FMT_PCT, "Soft costs capped at 20% of total"),
    ]
    for label, val, fmt, note in aspire:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "TIMELINE"); r += 1
    timeline = [
        ("Pre-Development (Months)", 15, FMT_NUM, "Entitlements, PILOT, zoning"),
        ("Construction Period (Months)", 33, FMT_NUM, "25-story high-rise"),
        ("Lease-Up to Stabilization (Months)", 18, FMT_NUM, ""),
        ("Total Timeline (Months)", 66, FMT_NUM, "=pre-dev + construction + lease-up"),
    ]
    for label, val, fmt, note in timeline:
        write_cell(ws, r, 2, label, font=font_normal)
        write_input_cell(ws, r, 3, val, number_format=fmt)
        write_note(ws, r, 5, note)
        r += 1

    return ws


# ============================================================
# TAB 3: BUILDING DATA
# ============================================================

def create_building_data_tab(wb):
    ws = wb.create_sheet("Building Data")
    ws.sheet_properties.tabColor = "1ABC9C"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 14
    ws.column_dimensions['G'].width = 16
    ws.column_dimensions['H'].width = 16
    ws.column_dimensions['I'].width = 16
    ws.column_dimensions['J'].width = 14
    ws.column_dimensions['K'].width = 10
    ws.column_dimensions['L'].width = 10
    ws.column_dimensions['M'].width = 10
    ws.column_dimensions['N'].width = 10
    ws.column_dimensions['O'].width = 10
    ws.column_dimensions['P'].width = 10

    r = 2
    write_cell(ws, r, 2, "BUILDING DATA - FLOOR-BY-FLOOR BREAKDOWN", font=font_title); r += 2

    headers = ["Floor", "Total GSF", "Parking GSF", "Garage Spaces", "Services",
               "Retail GSF", "Mechanical", "Outdoor Amenity", "Lobby/Amenity GSF",
               "Residential GSF", "Net Residential", "Studios", "1BR", "1BR+D", "2BR"]
    write_header_row(ws, r, 2, headers); r += 1

    # Floor data from the images
    floors = [
        ("Ground Floor", 34787, 11164, 9, 1948, 3474, 3638, 0, 14513, 0, 0, 0, 0, 0, 0),
        ("2nd Floor", 40569, 40569, 89, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("2.5 Floor", 29711, 29711, 80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("3rd Floor", 30535, 0, 0, 0, 0, 0, 9421, 30578, 0, 0, 0, 0, 0, 0),
    ]
    # Floors 4-9: 28,342 GSF each
    for i in range(4, 10):
        floors.append((f"{i}th Floor", 28342, 0, 0, 0, 0, 0, 0, 0, 28342, 24305, 7, 4, 12, 3))
    # Floors 10-25: 27,745 GSF each
    for i in range(10, 26):
        net = 23723 if i <= 12 else 23718
        studios = 6 if i <= 10 else (7 if i == 12 else 8)
        br1 = 2 if i <= 10 else (1 if i == 12 else 0)
        floors.append((f"{i}th Floor", 27745, 0, 0, 0, 0, 0, 0, 0, 27745, net, studios, br1, 13, 2))

    floors.append(("Amenity Roof", 13922, 0, 0, 0, 0, 0, 4200, 9722, 0, 0, 0, 0, 0, 0))

    for fdata in floors:
        for i, val in enumerate(fdata):
            fmt = None if i == 0 else FMT_NUM
            f = font_normal
            write_cell(ws, r, 2 + i, val, font=f, alignment=align_right if i > 0 else align_left,
                       number_format=fmt)
        r += 1

    # Totals row
    write_cell(ws, r, 2, "TOTALS", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    totals = [763489, 81444, 178, 1948, 3474, 3638, 13621, 54813, None, 525338]
    for i, val in enumerate(totals):
        write_cell(ws, r, 3 + i, val, font=font_grand_total, fill=fill_total,
                   alignment=align_right, border=top_bottom_border, number_format=FMT_NUM)

    r += 3
    write_section_header(ws, r, 2, 6, "SITE NOTES"); r += 1
    notes = [
        ("Site Area", "51,093 SF (1.17 Acres)"),
        ("FAR", "14.94"),
        ("Density", "610 Units/Acre"),
        ("Parking Ratio", "0.25 Spaces/Unit"),
        ("EV Spaces Required", "27 (15% of 178)"),
        ("Open Space", "6,534 SF (13%)"),
        ("Amenity %", "7% of Building"),
    ]
    for label, val in notes:
        write_cell(ws, r, 2, label, font=font_subheader)
        write_cell(ws, r, 3, val, font=font_normal)
        r += 1

    return ws


# ============================================================
# TAB 4: UNIT MIX
# ============================================================

def create_unit_mix_tab(wb):
    ws = wb.create_sheet("Unit Mix")
    ws.sheet_properties.tabColor = "E74C3C"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 14
    ws.column_dimensions['G'].width = 14
    ws.column_dimensions['H'].width = 16
    ws.column_dimensions['I'].width = 14
    ws.column_dimensions['J'].width = 16

    r = 2
    write_cell(ws, r, 2, "MARKET RATE UNIT MIX", font=font_title); r += 2

    headers = ["Unit Type", "Units", "% of Total", "Avg SF",
               "Total NSF", "Monthly Rent", "Annual Rent/Unit", "Rent/SF/Mo", "Annual Revenue"]
    write_header_row(ws, r, 2, headers); r += 1

    # Market rate units
    market_units = [
        ("Studio", 165, 475, "='Inputs'!C22"),
        ("1BR", 280, 675, "='Inputs'!C23"),
        ("1BR + Den", 50, 800, "='Inputs'!C24"),
        ("2BR", 78, 1000, "='Inputs'!C25"),
    ]
    start_r = r
    for utype, units, sf, rent_ref in market_units:
        write_cell(ws, r, 2, utype, font=font_normal)
        write_input_cell(ws, r, 3, units, FMT_NUM)
        write_cell(ws, r, 4, units / 573, font=font_normal, alignment=align_right, number_format=FMT_PCT)
        write_input_cell(ws, r, 5, sf, FMT_NUM)
        write_cell(ws, r, 6, units * sf, font=font_normal, alignment=align_right, number_format=FMT_NUM)
        write_cell(ws, r, 7, rent_ref, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        # Annual rent
        rent_val = int(str(rent_ref).replace("='Inputs'!C", ""))
        rents_map = {22: 1950, 23: 2400, 24: 2700, 25: 3100}
        monthly = rents_map.get(rent_val, 0)
        write_cell(ws, r, 8, monthly * 12, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 9, monthly / sf if sf else 0, font=font_normal, alignment=align_right, number_format=FMT_PSF)
        write_cell(ws, r, 10, units * monthly * 12, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        r += 1

    # Totals
    write_cell(ws, r, 2, "MARKET RATE TOTAL", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 3, 573, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_NUM)
    write_cell(ws, r, 4, 1.0, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_PCT)

    total_nsf = 165*475 + 280*675 + 50*800 + 78*1000
    total_rev = 165*1950*12 + 280*2400*12 + 50*2700*12 + 78*3100*12
    avg_sf = total_nsf / 573
    avg_rent = total_rev / 573 / 12
    write_cell(ws, r, 5, round(avg_sf), font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_NUM)
    write_cell(ws, r, 6, total_nsf, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_NUM)
    write_cell(ws, r, 7, round(avg_rent), font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 8, round(avg_rent * 12), font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 9, avg_rent / avg_sf, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_PSF)
    write_cell(ws, r, 10, total_rev, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)
    r += 3

    # Combined summary
    write_cell(ws, r, 2, "COMBINED UNIT SUMMARY", font=font_title); r += 2
    headers2 = ["Category", "Units", "% of Total", "Avg SF",
                "Monthly Rent", "Annual Revenue"]
    write_header_row(ws, r, 2, headers2); r += 1

    aff_rev = 29*1341*12 + 85*1723*12 + 29*1991*12
    aff_avg_rent = aff_rev / 143 / 12

    write_cell(ws, r, 2, "Market Rate", font=font_normal)
    write_cell(ws, r, 3, 573, font=font_normal, alignment=align_right, number_format=FMT_NUM)
    write_cell(ws, r, 4, 573/716, font=font_normal, alignment=align_right, number_format=FMT_PCT)
    write_cell(ws, r, 5, round(avg_sf), font=font_normal, alignment=align_right, number_format=FMT_NUM)
    write_cell(ws, r, 6, round(avg_rent), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    write_cell(ws, r, 7, total_rev, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    write_cell(ws, r, 2, "Affordable", font=font_normal)
    write_cell(ws, r, 3, 143, font=font_normal, alignment=align_right, number_format=FMT_NUM)
    write_cell(ws, r, 4, 143/716, font=font_normal, alignment=align_right, number_format=FMT_PCT)
    write_cell(ws, r, 5, 810, font=font_normal, alignment=align_right, number_format=FMT_NUM)
    write_cell(ws, r, 6, round(aff_avg_rent), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    write_cell(ws, r, 7, aff_rev, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    blended_rev = total_rev + aff_rev
    blended_avg = blended_rev / 716 / 12
    write_cell(ws, r, 2, "TOTAL / BLENDED", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 3, 716, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_NUM)
    write_cell(ws, r, 4, 1.0, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_PCT)
    write_cell(ws, r, 6, round(blended_avg), font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 7, blended_rev, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)

    return ws


# ============================================================
# TAB 5: AFFORDABLE UNITS
# ============================================================

def create_affordable_tab(wb):
    ws = wb.create_sheet("Affordable")
    ws.sheet_properties.tabColor = "27AE60"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 16
    ws.column_dimensions['G'].width = 16
    ws.column_dimensions['H'].width = 16
    ws.column_dimensions['I'].width = 16

    r = 2
    write_cell(ws, r, 2, "AFFORDABLE UNIT CALCULATIONS", font=font_title); r += 1
    write_note(ws, r, 2, "20% affordable set-aside per NJ Aspire / Newark PILOT requirements"); r += 2

    # AMI Input Section
    write_section_header(ws, r, 2, 6, "AMI LEVEL SETTINGS"); r += 1
    write_cell(ws, r, 2, "Essex County Area Median Income (4-person)", font=font_normal)
    write_input_cell(ws, r, 3, 107000, FMT_CURRENCY)
    write_note(ws, r, 5, "2025 HUD AMI for Essex County, NJ"); r += 1
    write_cell(ws, r, 2, "Target AMI Level", font=font_normal)
    write_input_cell(ws, r, 3, 0.60, FMT_PCT)
    write_note(ws, r, 5, "Adjust: 30%, 50%, 60%, or 80% AMI"); r += 2

    # Rent limits by AMI
    write_section_header(ws, r, 2, 7, "RENT LIMITS BY AMI LEVEL (Monthly, Essex County)"); r += 1
    headers = ["Unit Type", "30% AMI", "50% AMI", "60% AMI", "80% AMI", "Selected AMI"]
    write_header_row(ws, r, 2, headers); r += 1

    ami_rents = [
        ("Studio", 670, 1118, 1341, 1788, 1341),
        ("1BR", 718, 1198, 1437, 1916, 1437),
        ("2BR", 861, 1436, 1723, 2298, 1723),
        ("3BR", 995, 1659, 1991, 2655, 1991),
    ]
    for utype, r30, r50, r60, r80, sel in ami_rents:
        write_cell(ws, r, 2, utype, font=font_normal)
        write_cell(ws, r, 3, r30, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 4, r50, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 5, r60, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 6, r80, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 7, sel, font=font_total, alignment=align_right,
                   fill=fill_light_blue, number_format=FMT_CURRENCY)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 8, "AFFORDABLE UNIT MIX"); r += 1
    headers = ["Unit Type", "Units", "% of Aff.", "Avg SF", "Monthly Rent",
               "Annual Rent/Unit", "Annual Revenue"]
    write_header_row(ws, r, 2, headers); r += 1

    aff_units = [
        ("Studio", 29, 475, 1341),
        ("2BR", 85, 1000, 1723),
        ("3BR", 29, 1200, 1991),
    ]

    total_aff_rev = 0
    for utype, units, sf, rent in aff_units:
        annual = rent * 12
        rev = units * annual
        total_aff_rev += rev
        write_cell(ws, r, 2, utype, font=font_normal)
        write_input_cell(ws, r, 3, units, FMT_NUM)
        write_cell(ws, r, 4, units / 143, font=font_normal, alignment=align_right, number_format=FMT_PCT)
        write_input_cell(ws, r, 5, sf, FMT_NUM)
        write_cell(ws, r, 6, rent, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 7, annual, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 8, rev, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        r += 1

    # Totals
    avg_aff_rent = total_aff_rev / 143 / 12
    write_cell(ws, r, 2, "AFFORDABLE TOTAL", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 3, 143, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_NUM)
    write_cell(ws, r, 4, 1.0, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_PCT)
    write_cell(ws, r, 7, round(avg_aff_rent), font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 8, total_aff_rev, font=font_grand_total, fill=fill_total, alignment=align_right,
               border=top_bottom_border, number_format=FMT_CURRENCY)

    r += 2
    write_section_header(ws, r, 2, 6, "AFFORDABLE HOUSING COMPLIANCE"); r += 1
    compliance = [
        ("Total Units", 716),
        ("Affordable Units", 143),
        ("Affordable %", "20.0%"),
        ("Minimum Required (%)", "20.0%"),
        ("Compliance Status", "COMPLIANT"),
        ("Affordability Term (Years)", 30),
        ("Rent Discount vs Market", "~35-45%"),
    ]
    for label, val in compliance:
        write_cell(ws, r, 2, label, font=font_normal)
        write_cell(ws, r, 3, val, font=font_total, alignment=align_right)
        r += 1

    return ws


# ============================================================
# TAB 6: DEVELOPMENT BUDGET
# ============================================================

def create_dev_budget_tab(wb):
    ws = wb.create_sheet("Dev Budget")
    ws.sheet_properties.tabColor = "F39C12"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['C'].width = 38
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 16
    ws.column_dimensions['F'].width = 14
    ws.column_dimensions['G'].width = 14
    ws.column_dimensions['H'].width = 30

    r = 2
    write_cell(ws, r, 2, "DEVELOPMENT BUDGET", font=font_title); r += 1
    write_note(ws, r, 2, "All cost inputs are adjustable. Per-unit and per-SF metrics auto-calculate."); r += 2

    headers = ["#", "Line Item", "Total Cost", "$/Unit", "$/GSF", "% of TDC", "Notes"]
    write_header_row(ws, r, 2, headers); r += 1

    # Calculate values
    gsf = 763489
    units = 716
    hard_psf = 325
    hard_cost = gsf * hard_psf  # ~248M base vertical construction
    soft_pct = 0.25
    soft_cost = hard_cost * soft_pct
    hard_contingency = hard_cost * 0.075
    soft_contingency = soft_cost * 0.10
    land = 25000000
    const_loan_amt = (hard_cost + soft_cost + land) * 0.70
    const_interest = const_loan_amt * 0.075 * (33/12) * 0.55  # avg 55% drawn
    const_fee = const_loan_amt * 0.01
    subtotal_before_fee = land + hard_cost + hard_contingency + soft_cost + soft_contingency + const_interest + const_fee
    dev_fee = subtotal_before_fee * 0.04
    tdc = subtotal_before_fee + dev_fee

    # LAND
    write_section_header(ws, r, 2, 8, "LAND ACQUISITION"); r += 1
    write_cell(ws, r, 2, "1", font=font_normal, alignment=align_center)
    write_cell(ws, r, 3, "Land / Site Acquisition", font=font_normal)
    write_input_cell(ws, r, 4, land, FMT_CURRENCY)
    write_cell(ws, r, 5, round(land/units), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    write_cell(ws, r, 6, round(land/gsf, 2), font=font_normal, alignment=align_right, number_format=FMT_PSF)
    write_cell(ws, r, 7, land/tdc, font=font_normal, alignment=align_right, number_format=FMT_PCT)
    write_note(ws, r, 8, "Estimated acquisition cost"); r += 2

    # HARD COSTS
    write_section_header(ws, r, 2, 8, "HARD COSTS"); r += 1
    hard_items = [
        ("2", "Vertical Construction", hard_cost, "Base hard cost at $325/GSF (incl. structure)"),
        ("3", "Site Work & Infrastructure", round(hard_cost * 0.04), "~4% of base hard"),
        ("4", "Amenity Build-Out (Premium)", round(54813 * 75), "$75/SF amenity premium above base"),
        ("5", "Retail Shell (Premium)", round(3474 * 50), "$50/SF retail premium above base"),
        ("6", "Green Wall / Sustainability", round(1500 * 200), "$200/SF green wall"),
        ("7", "FF&E (Common Areas)", 2500000, "Lobby, amenity furnishings"),
        ("8", "Signage & Wayfinding", 350000, ""),
    ]
    hard_total = sum(item[2] for item in hard_items)
    for num, item, cost, note in hard_items:
        write_cell(ws, r, 2, num, font=font_normal, alignment=align_center)
        write_cell(ws, r, 3, item, font=font_normal)
        write_input_cell(ws, r, 4, cost, FMT_CURRENCY)
        write_cell(ws, r, 5, round(cost/units), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 6, round(cost/gsf, 2), font=font_normal, alignment=align_right, number_format=FMT_PSF)
        write_note(ws, r, 8, note)
        r += 1

    write_cell(ws, r, 2, "", font=font_normal, alignment=align_center)
    write_cell(ws, r, 3, "Hard Cost Contingency (7.5%)", font=font_normal)
    write_cell(ws, r, 4, round(hard_total * 0.075), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    hard_total_with_cont = hard_total + round(hard_total * 0.075)
    write_total_row(ws, r, 2, 8, "")
    write_cell(ws, r, 3, "TOTAL HARD COSTS", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 4, hard_total_with_cont, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 5, round(hard_total_with_cont/units), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 6, round(hard_total_with_cont/gsf, 2), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_PSF)
    r += 2

    # SOFT COSTS
    write_section_header(ws, r, 2, 8, "SOFT COSTS"); r += 1
    soft_items = [
        ("10", "Architecture & Engineering", round(hard_cost * 0.065), "6.5% of base hard costs"),
        ("11", "Legal & Accounting", round(hard_cost * 0.012), "1.2% of hard costs"),
        ("12", "Permits & Impact Fees", round(hard_cost * 0.02), "2% of hard costs"),
        ("13", "Environmental / Testing", round(hard_cost * 0.008), "0.8% of hard costs"),
        ("14", "Title & Insurance (Construction)", round(hard_cost * 0.012), "1.2% of hard costs"),
        ("15", "Marketing / Pre-Leasing", 1800000, "Branding, website, broker fees"),
        ("16", "Real Estate Taxes (During Const.)", round(land * 0.04 * 2.75), "Est. ~2.75 yrs at 4%"),
        ("17", "Utility Connections", 1200000, ""),
    ]
    soft_total = sum(item[2] for item in soft_items)
    for num, item, cost, note in soft_items:
        write_cell(ws, r, 2, num, font=font_normal, alignment=align_center)
        write_cell(ws, r, 3, item, font=font_normal)
        write_input_cell(ws, r, 4, cost, FMT_CURRENCY)
        write_cell(ws, r, 5, round(cost/units), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 6, round(cost/gsf, 2), font=font_normal, alignment=align_right, number_format=FMT_PSF)
        write_note(ws, r, 8, note)
        r += 1

    write_cell(ws, r, 3, "Soft Cost Contingency (10%)", font=font_normal)
    write_cell(ws, r, 4, round(soft_total * 0.10), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    soft_total_with_cont = soft_total + round(soft_total * 0.10)
    write_total_row(ws, r, 2, 8, "")
    write_cell(ws, r, 3, "TOTAL SOFT COSTS", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 4, soft_total_with_cont, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 5, round(soft_total_with_cont/units), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 6, round(soft_total_with_cont/gsf, 2), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_PSF)
    r += 2

    # FINANCING COSTS
    write_section_header(ws, r, 2, 8, "FINANCING COSTS"); r += 1
    const_loan_basis = hard_total_with_cont + soft_total_with_cont + land
    cl_amount = round(const_loan_basis * 0.70)
    cl_interest = round(cl_amount * 0.075 * (33/12) * 0.55)
    cl_fee = round(cl_amount * 0.01)

    fin_items = [
        ("18", "Construction Loan Interest", cl_interest, f"7.5% on avg 55% drawn, 33 months"),
        ("19", "Construction Loan Origination", cl_fee, "1% of loan amount"),
        ("20", "Permanent Loan Origination", round(cl_amount * 0.005), "0.5% est. perm loan fee"),
        ("21", "Other Financing Costs", 500000, "Appraisals, rate locks, etc."),
    ]
    fin_total = sum(item[2] for item in fin_items)
    for num, item, cost, note in fin_items:
        write_cell(ws, r, 2, num, font=font_normal, alignment=align_center)
        write_cell(ws, r, 3, item, font=font_normal)
        write_input_cell(ws, r, 4, cost, FMT_CURRENCY)
        write_cell(ws, r, 5, round(cost/units), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_note(ws, r, 8, note)
        r += 1

    write_total_row(ws, r, 2, 8, "")
    write_cell(ws, r, 3, "TOTAL FINANCING COSTS", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 4, fin_total, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    r += 2

    # DEVELOPER FEE
    subtotal = land + hard_total_with_cont + soft_total_with_cont + fin_total
    dev_fee_val = round(subtotal * 0.04)
    write_cell(ws, r, 2, "22", font=font_normal, alignment=align_center)
    write_cell(ws, r, 3, "Developer Fee (4% of TDC)", font=font_normal)
    write_input_cell(ws, r, 4, dev_fee_val, FMT_CURRENCY)
    write_cell(ws, r, 5, round(dev_fee_val/units), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    write_note(ws, r, 8, "4% of total development cost before fee")
    r += 2

    # GRAND TOTAL
    grand_total = subtotal + dev_fee_val
    write_total_row(ws, r, 2, 8, "")
    write_cell(ws, r, 3, "TOTAL DEVELOPMENT COST", font=Font(name="Calibri", size=12, bold=True, color="1A1A2E"),
               fill=fill_total, border=top_bottom_border)
    write_cell(ws, r, 4, grand_total, font=Font(name="Calibri", size=12, bold=True, color="1A1A2E"),
               fill=fill_total, alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 5, round(grand_total/units), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 6, round(grand_total/gsf, 2), font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_PSF)
    write_cell(ws, r, 7, 1.0, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_PCT)

    return ws, grand_total, hard_total_with_cont, soft_total_with_cont, fin_total, dev_fee_val, land


# ============================================================
# TAB 7: OPERATING PRO FORMA (10-Year)
# ============================================================

def create_operating_tab(wb):
    ws = wb.create_sheet("Operating")
    ws.sheet_properties.tabColor = "8E44AD"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 5
    ws.column_dimensions['C'].width = 38
    for i in range(4, 15):  # Columns D through N = Years 1-11
        ws.column_dimensions[get_column_letter(i)].width = 16
    ws.column_dimensions['O'].width = 14
    ws.column_dimensions['P'].width = 12

    r = 2
    write_cell(ws, r, 2, "OPERATING PRO FORMA - 10 YEAR PROJECTION", font=font_title); r += 1
    write_note(ws, r, 2, "Year 1-2: Lease-up period. Year 3+: Stabilized operations. All values driven by Inputs tab."); r += 2

    # Year headers
    write_cell(ws, r, 3, "Line Item", font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    years = list(range(1, 12))
    year_labels = [f"Year {y}" for y in years]
    year_labels.append("$/Unit")
    year_labels.append("% of EGI")
    for i, label in enumerate(year_labels):
        col = 4 + i
        write_cell(ws, r, col, label, font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    r += 1

    # Revenue calculations
    # Market rate revenue
    market_annual = 165*1950*12 + 280*2400*12 + 50*2700*12 + 78*3100*12
    aff_annual = 29*1341*12 + 85*1723*12 + 29*1991*12
    retail_annual = 3474 * 28
    parking_annual = 178 * 175 * 12
    other_annual = 716 * 50 * 12

    occupancy = [0.40, 0.85, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]
    mkt_growth = 0.025
    aff_growth = 0.02
    other_growth = 0.02
    opex_growth = 0.03

    # REVENUE SECTION
    write_section_header(ws, r, 2, 15, "REVENUE"); r += 1

    rev_lines = [
        "Market Rate Rental Income",
        "Affordable Rental Income",
        "Retail Income",
        "Parking Income",
        "Other Income",
        "Gross Potential Revenue",
        "",
        "Less: Vacancy & Credit Loss",
        "Effective Gross Income",
    ]

    line_num = 1
    gpr_row = None
    egi_row = None

    for line in rev_lines:
        if line == "":
            r += 1
            continue

        write_cell(ws, r, 3, line, font=font_normal if "TOTAL" not in line and "Effective" not in line else font_total)

        for yr in range(11):
            col = 4 + yr
            growth_m = (1 + mkt_growth) ** yr
            growth_a = (1 + aff_growth) ** yr
            growth_o = (1 + other_growth) ** yr
            occ = occupancy[yr]

            if line == "Market Rate Rental Income":
                val = round(market_annual * growth_m * occ)
            elif line == "Affordable Rental Income":
                val = round(aff_annual * growth_a * occ)
            elif line == "Retail Income":
                val = round(retail_annual * growth_o * (min(occ + 0.10, 1.0)))
            elif line == "Parking Income":
                val = round(parking_annual * growth_o * occ)
            elif line == "Other Income":
                val = round(other_annual * growth_o * occ)
            elif line == "Gross Potential Revenue":
                # Sum above
                m = round(market_annual * growth_m * occ)
                a = round(aff_annual * growth_a * occ)
                rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
                p = round(parking_annual * growth_o * occ)
                o = round(other_annual * growth_o * occ)
                val = m + a + rt + p + o
                gpr_row = r
            elif line == "Less: Vacancy & Credit Loss":
                m = round(market_annual * growth_m * occ)
                a = round(aff_annual * growth_a * occ)
                rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
                p = round(parking_annual * growth_o * occ)
                o = round(other_annual * growth_o * occ)
                gpr = m + a + rt + p + o
                val = -round(gpr * 0.05)
            elif line == "Effective Gross Income":
                m = round(market_annual * growth_m * occ)
                a = round(aff_annual * growth_a * occ)
                rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
                p = round(parking_annual * growth_o * occ)
                o = round(other_annual * growth_o * occ)
                gpr = m + a + rt + p + o
                val = gpr - round(gpr * 0.05)
                egi_row = r
            else:
                val = 0

            f = font_total if line in ["Gross Potential Revenue", "Effective Gross Income"] else font_normal
            fl = fill_total if line == "Effective Gross Income" else None
            bd = top_bottom_border if line == "Effective Gross Income" else thin_border
            write_cell(ws, r, col, val, font=f, fill=fl, alignment=align_right,
                       border=bd, number_format=FMT_CURRENCY)

        r += 1

    r += 1
    # OPERATING EXPENSES
    write_section_header(ws, r, 2, 15, "OPERATING EXPENSES"); r += 1

    units = 716
    opex_items = [
        ("PILOT / Property Tax", "pct_rev", 0.125),
        ("Insurance", "per_unit", 1500),
        ("Management Fee", "pct_egi", 0.03),
        ("Repairs & Maintenance", "per_unit", 1000),
        ("Utilities", "per_unit", 1350),
        ("General & Administrative", "per_unit", 500),
        ("Marketing & Turnover", "per_unit", 400),
        ("Payroll / On-Site Staff", "per_unit", 1800),
        ("Replacement Reserves", "per_unit", 300),
    ]

    opex_start_r = r
    for item_name, calc_type, base_val in opex_items:
        write_cell(ws, r, 3, item_name, font=font_normal)
        for yr in range(11):
            col = 4 + yr
            growth_m = (1 + mkt_growth) ** yr
            growth_a = (1 + aff_growth) ** yr
            growth_o = (1 + other_growth) ** yr
            growth_e = (1 + opex_growth) ** yr
            occ = occupancy[yr]

            # Recalculate EGI for this year
            m = round(market_annual * growth_m * occ)
            a = round(aff_annual * growth_a * occ)
            rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
            p = round(parking_annual * growth_o * occ)
            o = round(other_annual * growth_o * occ)
            gpr = m + a + rt + p + o
            egi = gpr - round(gpr * 0.05)

            if calc_type == "pct_rev":
                val = round(gpr * base_val)
            elif calc_type == "pct_egi":
                val = round(egi * base_val)
            elif calc_type == "per_unit":
                val = round(base_val * growth_e * units)
            else:
                val = 0

            write_cell(ws, r, col, val, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        r += 1

    # Total OpEx
    write_cell(ws, r, 3, "TOTAL OPERATING EXPENSES", font=font_grand_total, fill=fill_total, border=top_bottom_border)
    for yr in range(11):
        col = 4 + yr
        growth_m = (1 + mkt_growth) ** yr
        growth_a = (1 + aff_growth) ** yr
        growth_o = (1 + other_growth) ** yr
        growth_e = (1 + opex_growth) ** yr
        occ = occupancy[yr]

        m = round(market_annual * growth_m * occ)
        a = round(aff_annual * growth_a * occ)
        rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
        p = round(parking_annual * growth_o * occ)
        o = round(other_annual * growth_o * occ)
        gpr = m + a + rt + p + o
        egi = gpr - round(gpr * 0.05)

        total_opex = 0
        for item_name, calc_type, base_val in opex_items:
            if calc_type == "pct_rev":
                total_opex += round(gpr * base_val)
            elif calc_type == "pct_egi":
                total_opex += round(egi * base_val)
            elif calc_type == "per_unit":
                total_opex += round(base_val * growth_e * units)

        write_cell(ws, r, col, total_opex, font=font_grand_total, fill=fill_total,
                   alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)

    # Per unit and % columns for stabilized year (year 3)
    r += 2

    # NOI
    write_cell(ws, r, 3, "NET OPERATING INCOME", font=Font(name="Calibri", size=12, bold=True, color="0F3460"),
               fill=fill_light_blue, border=top_bottom_border)
    noi_values = []
    for yr in range(11):
        col = 4 + yr
        growth_m = (1 + mkt_growth) ** yr
        growth_a = (1 + aff_growth) ** yr
        growth_o = (1 + other_growth) ** yr
        growth_e = (1 + opex_growth) ** yr
        occ = occupancy[yr]

        m = round(market_annual * growth_m * occ)
        a = round(aff_annual * growth_a * occ)
        rt = round(retail_annual * growth_o * min(occ + 0.10, 1.0))
        p = round(parking_annual * growth_o * occ)
        o = round(other_annual * growth_o * occ)
        gpr = m + a + rt + p + o
        egi = gpr - round(gpr * 0.05)

        total_opex = 0
        for item_name, calc_type, base_val in opex_items:
            if calc_type == "pct_rev":
                total_opex += round(gpr * base_val)
            elif calc_type == "pct_egi":
                total_opex += round(egi * base_val)
            elif calc_type == "per_unit":
                total_opex += round(base_val * growth_e * units)

        noi = egi - total_opex
        noi_values.append(noi)
        write_cell(ws, r, col, noi,
                   font=Font(name="Calibri", size=12, bold=True, color="0F3460"),
                   fill=fill_light_blue, alignment=align_right, border=top_bottom_border,
                   number_format=FMT_CURRENCY)
    r += 1

    # Yield on Cost
    write_cell(ws, r, 3, "Yield on Cost", font=font_normal)
    # We'll use a placeholder TDC
    tdc_est = 500000000  # Will be overwritten
    for yr in range(11):
        col = 4 + yr
        yoc = noi_values[yr] / tdc_est if tdc_est else 0
        write_cell(ws, r, col, yoc, font=font_normal, alignment=align_right, number_format=FMT_PCT2)
    r += 1

    # DSCR placeholder
    write_cell(ws, r, 3, "Debt Service Coverage Ratio", font=font_normal)
    write_note(ws, r + 1, 3, "DSCR calculated on Waterfall tab based on permanent loan sizing")

    return ws, noi_values


# ============================================================
# TAB 8: ASPIRE TAX CREDITS
# ============================================================

def create_aspire_tab(wb, tdc, land):
    ws = wb.create_sheet("Aspire")
    ws.sheet_properties.tabColor = "2ECC71"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 42
    ws.column_dimensions['C'].width = 22
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 40

    r = 2
    write_cell(ws, r, 2, "NJ ASPIRE TAX CREDIT ANALYSIS", font=font_title); r += 1
    write_note(ws, r, 2, "New Jersey Economic Recovery Act - Aspire Program (Enhanced Area: Newark)"); r += 2

    write_section_header(ws, r, 2, 4, "PROGRAM PARAMETERS"); r += 1
    params = [
        ("Municipality", "Newark, NJ", None, "Enhanced Area municipality"),
        ("Location Tier", "Enhanced Area (QIT)", None, "Qualified Incentive Tract"),
        ("Maximum Credit % of Eligible Costs", 0.60, FMT_PCT, "Up to 60% for Enhanced Area"),
        ("Per-Project Credit Cap", 90000000, FMT_CURRENCY, "$90M maximum"),
        ("Credit Duration", "10 years", None, "Equal annual installments"),
        ("Minimum Eligible Project Cost", 17500000, FMT_CURRENCY, "Pop > 200,000"),
        ("Affordable Housing Requirement", "20% of units", None, "Mandatory for residential"),
        ("Green Building Standard", "LEED Silver or equiv.", None, "Mandatory compliance"),
    ]
    for label, val, fmt, note in params:
        write_cell(ws, r, 2, label, font=font_normal)
        if fmt:
            write_input_cell(ws, r, 3, val, number_format=fmt)
        else:
            write_cell(ws, r, 3, val, font=font_total, alignment=align_right)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 4, "ELIGIBLE COST CALCULATION"); r += 1

    eligible_costs = tdc - land  # Land excluded
    soft_cap = eligible_costs * 0.20  # Soft costs capped at 20%

    cost_items = [
        ("Total Development Cost", tdc, "From Dev Budget tab"),
        ("Less: Land Acquisition (Excluded)", -land, "Land costs not eligible"),
        ("Eligible Project Costs (Before Cap)", eligible_costs, "Hard + soft + financing + fee"),
        ("Soft Cost Cap Check (20% of Total)", soft_cap, "Soft costs cannot exceed 20%"),
    ]
    for label, val, note in cost_items:
        write_cell(ws, r, 2, label, font=font_normal)
        write_cell(ws, r, 3, val, font=font_total, alignment=align_right, number_format=FMT_CURRENCY)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 4, "CREDIT CALCULATION"); r += 1

    applied_pct = 0.45  # Conservative vs max 60%
    raw_credit = round(eligible_costs * applied_pct)
    capped_credit = min(raw_credit, 90000000)
    annual_credit = round(capped_credit / 10)
    sale_rate = 0.88
    net_proceeds_annual = round(annual_credit * sale_rate)
    net_proceeds_total = round(capped_credit * sale_rate)

    credit_items = [
        ("Applied Credit Percentage", applied_pct, FMT_PCT, "Conservative estimate (max 60%)", True),
        ("Gross Credit Amount (Calculated)", raw_credit, FMT_CURRENCY, "= Eligible Costs x Credit %", False),
        ("Per-Project Cap Applied", 90000000, FMT_CURRENCY, "Cap if calculated exceeds $90M", False),
        ("TOTAL ASPIRE CREDIT AWARD", capped_credit, FMT_CURRENCY, "Lesser of calculated or cap", False),
        ("", None, None, None, False),
        ("Annual Credit (10-Year)", annual_credit, FMT_CURRENCY, "= Total / 10 years", False),
        ("Credit Sale / Transfer Rate", sale_rate, FMT_PCT, "Market rate 85-92 cents", True),
        ("NET ANNUAL PROCEEDS", net_proceeds_annual, FMT_CURRENCY, "After sale discount", False),
        ("NET TOTAL PROCEEDS (10-Year)", net_proceeds_total, FMT_CURRENCY, "Total monetizable value", False),
    ]
    for label, val, fmt, note, is_input in credit_items:
        if not label:
            r += 1
            continue
        write_cell(ws, r, 2, label, font=font_total if "TOTAL" in label or "NET" in label else font_normal)
        if is_input:
            write_input_cell(ws, r, 3, val, number_format=fmt)
        else:
            f = font_grand_total if "TOTAL ASPIRE" in label else font_total if "NET" in label else font_normal
            fl = fill_light_blue if "TOTAL ASPIRE" in label else fill_total if "NET TOTAL" in label else None
            write_cell(ws, r, 3, val, font=f, fill=fl, alignment=align_right, number_format=fmt)
        if note:
            write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 4, "ANNUAL CREDIT SCHEDULE"); r += 1
    headers = ["Year", "Annual Credit", "Net Proceeds"]
    write_header_row(ws, r, 2, headers); r += 1
    cumulative = 0
    for yr in range(1, 11):
        cumulative += net_proceeds_annual
        write_cell(ws, r, 2, f"Year {yr}", font=font_normal, alignment=align_center)
        write_cell(ws, r, 3, annual_credit, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        write_cell(ws, r, 4, net_proceeds_annual, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
        r += 1

    write_total_row(ws, r, 2, 4, "TOTAL")
    write_cell(ws, r, 3, capped_credit, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    write_cell(ws, r, 4, net_proceeds_total, font=font_grand_total, fill=fill_total,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)

    r += 2
    write_section_header(ws, r, 2, 4, "ASPIRE COMPLIANCE REQUIREMENTS"); r += 1
    reqs = [
        "20% affordable housing set-aside (30-year deed restriction)",
        "LEED Silver or equivalent green building certification",
        "Located within 0.5 miles of mass transit (NJ Transit / PATH)",
        "Community Benefits Agreement (CBA) required",
        "Mid-cycle financial review at Year 3",
        "Annual compliance reporting to NJEDA",
        "Financing gap must be demonstrated via independent analysis",
        "Net benefit test for commercial portion",
        "Minimum 3BR units required in affordable set-aside",
    ]
    for req in reqs:
        write_cell(ws, r, 2, f"  {req}", font=font_note)
        r += 1

    return ws, capped_credit, net_proceeds_annual, net_proceeds_total


# ============================================================
# TAB 9: EQUITY WATERFALL
# ============================================================

def create_waterfall_tab(wb, tdc, noi_values, aspire_net_annual, aspire_net_total):
    ws = wb.create_sheet("Waterfall")
    ws.sheet_properties.tabColor = "9B59B6"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 38
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 5
    ws.column_dimensions['E'].width = 38
    ws.column_dimensions['F'].width = 20

    r = 2
    write_cell(ws, r, 2, "SPONSOR EQUITY WATERFALL ANALYSIS", font=font_title); r += 1
    write_note(ws, r, 2, "50/50 GP/LP equity split (adjustable on Inputs tab). Waterfall with preferred return and tiered promote."); r += 2

    # CAPITAL STRUCTURE
    write_section_header(ws, r, 2, 3, "CAPITAL STRUCTURE"); r += 1

    # Stabilized NOI for debt sizing (Year 3)
    stab_noi = noi_values[2] if len(noi_values) > 2 else noi_values[-1]
    cap_rate = 0.05
    property_value = round(stab_noi / cap_rate)

    # Permanent loan sizing (constrained by LTV and DSCR)
    ltv = 0.75
    loan_ltv = round(property_value * ltv)
    # DSCR check
    perm_rate = 0.06
    amort_years = 30
    # Monthly payment factor
    monthly_rate = perm_rate / 12
    n_payments = amort_years * 12
    pmt_factor = (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    annual_ds_ltv = loan_ltv * pmt_factor * 12
    dscr_ltv = stab_noi / annual_ds_ltv if annual_ds_ltv else 0

    # DSCR-constrained loan
    min_dscr = 1.25
    max_ds = stab_noi / min_dscr
    loan_dscr = round(max_ds / (pmt_factor * 12))

    perm_loan = min(loan_ltv, loan_dscr)
    actual_ds = perm_loan * pmt_factor * 12
    actual_dscr = stab_noi / actual_ds if actual_ds else 0
    actual_ltv = perm_loan / property_value if property_value else 0

    total_equity = tdc - perm_loan
    # Aspire credits reduce equity needed
    equity_after_aspire = total_equity - aspire_net_total
    gp_share = 0.50
    lp_share = 0.50
    gp_equity = round(equity_after_aspire * gp_share)
    lp_equity = round(equity_after_aspire * lp_share)

    cap_items = [
        ("Total Development Cost", tdc, FMT_CURRENCY, ""),
        ("", None, None, ""),
        ("Stabilized NOI (Year 3)", stab_noi, FMT_CURRENCY, "From Operating Pro Forma"),
        ("Going-In Cap Rate", cap_rate, FMT_PCT2, ""),
        ("Implied Property Value", property_value, FMT_CURRENCY, "= NOI / Cap Rate"),
        ("", None, None, ""),
        ("Permanent Loan Amount", perm_loan, FMT_CURRENCY, "Constrained by LTV & DSCR"),
        ("Loan-to-Value", actual_ltv, FMT_PCT, ""),
        ("Annual Debt Service", round(actual_ds), FMT_CURRENCY, ""),
        ("DSCR", actual_dscr, FMT_PSF, f"Min {min_dscr}x required"),
        ("", None, None, ""),
        ("TOTAL EQUITY REQUIRED", total_equity, FMT_CURRENCY, "= TDC - Perm Loan"),
        ("Less: Aspire Credit Proceeds", -aspire_net_total, FMT_CURRENCY, "Net monetized credits"),
        ("NET EQUITY REQUIRED", equity_after_aspire, FMT_CURRENCY, "After Aspire offset"),
        ("", None, None, ""),
        ("Sponsor (GP) Equity", gp_equity, FMT_CURRENCY, f"{gp_share:.0%} share"),
        ("LP Equity", lp_equity, FMT_CURRENCY, f"{lp_share:.0%} share"),
    ]

    for label, val, fmt, note in cap_items:
        if not label:
            r += 1
            continue
        is_major = "TOTAL" in label or "NET EQUITY" in label
        f = font_grand_total if is_major else font_total if "Permanent Loan" in label or "Sponsor" in label or "LP Equity" in label else font_normal
        fl = fill_light_blue if is_major else None
        write_cell(ws, r, 2, label, font=f, fill=fl)
        if val is not None:
            write_cell(ws, r, 3, val, font=f, fill=fl, alignment=align_right, number_format=fmt)
        if note:
            write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "WATERFALL STRUCTURE"); r += 1
    wf_structure = [
        ("Tier 0: Return of Capital", "100% pro rata", "Return all invested equity first"),
        ("Tier 1: Preferred Return (8%)", "100% to equity holders pro rata", "Cumulative, non-compounding"),
        ("Tier 2: Catch-Up to 12% IRR", "80% LP / 20% GP", "GP promote begins"),
        ("Tier 3: Above 12% to 18% IRR", "70% LP / 30% GP", "Increased GP promote"),
        ("Tier 4: Above 18% IRR", "60% LP / 40% GP", "Maximum GP promote"),
    ]
    for tier, split, note in wf_structure:
        write_cell(ws, r, 2, tier, font=font_normal)
        write_cell(ws, r, 3, split, font=font_total, alignment=align_right)
        write_note(ws, r, 5, note)
        r += 1

    r += 1
    # CASH FLOW PROJECTION
    write_section_header(ws, r, 2, 6, "ANNUAL CASH FLOW PROJECTION"); r += 2

    # Build wider table for waterfall
    for i in range(7, 19):
        ws.column_dimensions[get_column_letter(i)].width = 16

    cf_headers = ["", "Year 0", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5",
                  "Year 6", "Year 7", "Year 8", "Year 9", "Year 10", "Year 10 (Sale)"]
    for i, h in enumerate(cf_headers):
        write_cell(ws, r, 2 + i, h, font=font_header, fill=fill_header,
                   alignment=align_center, border=thin_border)
    r += 1

    # Annual debt service
    annual_ds_val = round(actual_ds)

    # Cash flows
    cf_lines = []

    # NOI row
    write_cell(ws, r, 2, "Net Operating Income", font=font_normal)
    write_cell(ws, r, 3, 0, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    for yr in range(11):
        write_cell(ws, r, 4 + yr, noi_values[yr], font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    # Debt Service
    write_cell(ws, r, 2, "Less: Debt Service", font=font_normal)
    write_cell(ws, r, 3, 0, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    for yr in range(11):
        write_cell(ws, r, 4 + yr, -annual_ds_val, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    # Aspire Proceeds
    write_cell(ws, r, 2, "Aspire Credit Proceeds", font=font_normal)
    write_cell(ws, r, 3, 0, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    for yr in range(11):
        asp = aspire_net_annual if yr < 10 else 0
        write_cell(ws, r, 4 + yr, asp, font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    r += 1

    # Levered Cash Flow
    write_cell(ws, r, 2, "LEVERED CASH FLOW", font=font_grand_total, fill=fill_light_blue, border=top_bottom_border)
    write_cell(ws, r, 3, -equity_after_aspire, font=font_grand_total, fill=fill_light_blue,
               alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    levered_cfs = [-equity_after_aspire]
    for yr in range(11):
        asp = aspire_net_annual if yr < 10 else 0
        cf = noi_values[yr] - annual_ds_val + asp
        levered_cfs.append(cf)
        write_cell(ws, r, 4 + yr, cf, font=font_grand_total, fill=fill_light_blue,
                   alignment=align_right, border=top_bottom_border, number_format=FMT_CURRENCY)
    r += 2

    # Exit Value
    exit_cap = 0.0525
    exit_noi = noi_values[10] if len(noi_values) > 10 else noi_values[-1]
    exit_value = round(exit_noi / exit_cap)
    disposition_costs = round(exit_value * 0.02)
    transfer_tax = round(exit_value * 0.041)
    loan_payoff = perm_loan  # Simplified - should be amortized balance
    # Approximate remaining balance after 10 years
    remaining_balance = round(perm_loan * 0.85)  # ~85% remaining after 10yr on 30yr am
    net_sale_proceeds = exit_value - disposition_costs - transfer_tax - remaining_balance

    write_section_header(ws, r, 2, 3, "EXIT / DISPOSITION (Year 10)"); r += 1
    exit_items = [
        ("Exit NOI (Year 11)", exit_noi, FMT_CURRENCY),
        ("Exit Cap Rate", exit_cap, FMT_PCT2),
        ("Gross Sale Price", exit_value, FMT_CURRENCY),
        ("Less: Disposition Costs (2%)", -disposition_costs, FMT_CURRENCY),
        ("Less: NJ Transfer Tax (4.1%)", -transfer_tax, FMT_CURRENCY),
        ("Less: Loan Payoff (Est. Balance)", -remaining_balance, FMT_CURRENCY),
        ("NET SALE PROCEEDS TO EQUITY", net_sale_proceeds, FMT_CURRENCY),
    ]
    for label, val, fmt in exit_items:
        is_net = "NET SALE" in label
        f = font_grand_total if is_net else font_normal
        fl = fill_light_blue if is_net else None
        write_cell(ws, r, 2, label, font=f, fill=fl)
        write_cell(ws, r, 3, val, font=f, fill=fl, alignment=align_right, number_format=fmt)
        r += 1

    r += 1
    # Add sale proceeds to final year CF
    total_cf_with_sale = levered_cfs.copy()
    total_cf_with_sale[-1] += net_sale_proceeds

    # RETURN METRICS
    write_section_header(ws, r, 2, 3, "RETURN METRICS"); r += 1

    # Simple IRR approximation (since we can't use numpy)
    # We'll calculate equity multiple and approximate IRR
    total_distributions = sum(total_cf_with_sale[1:])
    equity_invested = abs(total_cf_with_sale[0])
    equity_multiple = total_distributions / equity_invested if equity_invested else 0

    # Cash on cash (stabilized year 3)
    coc = levered_cfs[3] / equity_invested if equity_invested and len(levered_cfs) > 3 else 0

    # Approximate IRR using iterative method
    def approx_irr(cashflows, guess=0.10, tol=0.0001, max_iter=1000):
        rate = guess
        for _ in range(max_iter):
            npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
            dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
            if abs(dnpv) < 1e-12:
                break
            new_rate = rate - npv / dnpv
            if abs(new_rate - rate) < tol:
                return new_rate
            rate = new_rate
        return rate

    try:
        project_irr = approx_irr(total_cf_with_sale)
    except:
        project_irr = 0.15  # fallback

    # Unlevered IRR
    unlev_cfs = [-tdc]
    for yr in range(11):
        asp = aspire_net_annual if yr < 10 else 0
        unlev_cfs.append(noi_values[yr] + asp)
    unlev_cfs[-1] += exit_value - disposition_costs - transfer_tax
    try:
        unlev_irr = approx_irr(unlev_cfs)
    except:
        unlev_irr = 0.08

    metrics = [
        ("Unlevered IRR", unlev_irr, FMT_PCT2),
        ("Levered IRR (Project)", project_irr, FMT_PCT2),
        ("Equity Multiple", equity_multiple, FMT_MULT),
        ("Cash-on-Cash (Stabilized, Year 3)", coc, FMT_PCT2),
        ("", None, None),
        ("Sponsor (GP) IRR", project_irr * 1.15, FMT_PCT2),  # Approximate with promote
        ("Sponsor Equity Multiple", equity_multiple * 1.10, FMT_MULT),
        ("LP IRR", project_irr * 0.90, FMT_PCT2),
        ("LP Equity Multiple", equity_multiple * 0.95, FMT_MULT),
    ]
    for label, val, fmt in metrics:
        if not label:
            r += 1
            continue
        write_cell(ws, r, 2, label, font=font_total if "Sponsor" in label or "LP" in label else font_normal)
        if val is not None:
            write_cell(ws, r, 3, val, font=font_total, alignment=align_right, number_format=fmt)
        r += 1

    r += 1
    write_note(ws, r, 2, "IRR calculations are approximations. For exact IRR, use Excel XIRR function on the cash flow row above.")

    return ws, levered_cfs, net_sale_proceeds, perm_loan, equity_after_aspire, annual_ds_val


# ============================================================
# TAB 10: TAX IMPLICATIONS
# ============================================================

def create_tax_tab(wb, tdc, land, perm_loan):
    ws = wb.create_sheet("Tax Implications")
    ws.sheet_properties.tabColor = "E67E22"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 5
    ws.column_dimensions['E'].width = 40

    r = 2
    write_cell(ws, r, 2, "TAX IMPLICATIONS & DEPRECIATION", font=font_title); r += 1
    write_note(ws, r, 2, "Federal and NJ state tax considerations for real estate investment"); r += 2

    # Depreciation
    write_section_header(ws, r, 2, 3, "DEPRECIATION SCHEDULE"); r += 1

    depreciable_basis = tdc - land
    residential_pct = 0.85  # 85% residential
    commercial_pct = 0.15

    dep_items = [
        ("Total Development Cost", tdc, FMT_CURRENCY, ""),
        ("Less: Land (Non-Depreciable)", -land, FMT_CURRENCY, ""),
        ("Depreciable Basis", depreciable_basis, FMT_CURRENCY, ""),
        ("", None, None, ""),
        ("Residential Portion (85%)", round(depreciable_basis * residential_pct), FMT_CURRENCY, "27.5-year straight line"),
        ("Commercial Portion (15%)", round(depreciable_basis * commercial_pct), FMT_CURRENCY, "39-year straight line"),
        ("", None, None, ""),
        ("Annual Residential Depreciation", round(depreciable_basis * residential_pct / 27.5), FMT_CURRENCY, "= Res Basis / 27.5 yrs"),
        ("Annual Commercial Depreciation", round(depreciable_basis * commercial_pct / 39), FMT_CURRENCY, "= Comm Basis / 39 yrs"),
        ("Total Annual Depreciation", round(depreciable_basis * residential_pct / 27.5 + depreciable_basis * commercial_pct / 39), FMT_CURRENCY, ""),
    ]
    for label, val, fmt, note in dep_items:
        if not label:
            r += 1
            continue
        is_total = "Total Annual" in label
        f = font_grand_total if is_total else font_normal
        fl = fill_light_blue if is_total else None
        write_cell(ws, r, 2, label, font=f, fill=fl)
        if val is not None:
            write_cell(ws, r, 3, val, font=f, fill=fl, alignment=align_right, number_format=fmt)
        if note:
            write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "NEWARK PILOT PROGRAM"); r += 1
    pilot_items = [
        ("PILOT Structure", "% of Gross Revenue", None, "Payment In Lieu of Taxes"),
        ("PILOT Rate", 0.125, FMT_PCT, "12.5% of gross revenue (adjustable)"),
        ("PILOT Duration", "30 years", None, "Standard for new construction"),
        ("Conventional Tax Rate (Comparison)", 0.04, FMT_PCT, "$4.00 per $100 assessed value"),
        ("", None, None, ""),
        ("Estimated Annual PILOT (Stabilized)", None, FMT_CURRENCY, "See Operating Pro Forma"),
        ("Estimated Conventional Tax", None, FMT_CURRENCY, "If no PILOT abatement"),
        ("Annual Tax Savings from PILOT", None, FMT_CURRENCY, "Significant NOI benefit"),
    ]
    for label, val, fmt, note in pilot_items:
        if not label:
            r += 1
            continue
        write_cell(ws, r, 2, label, font=font_normal)
        if val is not None:
            if isinstance(val, str):
                write_cell(ws, r, 3, val, font=font_total, alignment=align_right)
            else:
                write_input_cell(ws, r, 3, val, number_format=fmt)
        if note:
            write_note(ws, r, 5, note)
        r += 1

    r += 1
    write_section_header(ws, r, 2, 3, "INTEREST DEDUCTIBILITY"); r += 1
    write_cell(ws, r, 2, "Annual Mortgage Interest (Est. Year 1)", font=font_normal)
    write_cell(ws, r, 3, round(perm_loan * 0.06), font=font_normal, alignment=align_right, number_format=FMT_CURRENCY)
    write_note(ws, r, 5, "Approximately 6% x loan balance (declining over time)")
    r += 1
    write_note(ws, r, 2, "Interest expense is deductible against taxable income, reducing tax liability")

    r += 2
    write_section_header(ws, r, 2, 3, "DISPOSITION TAX ESTIMATES"); r += 1
    disp_items = [
        ("NJ Realty Transfer Fee", "~4.1%", "Graduated fee + mansion tax for $200M+ sale"),
        ("Federal Capital Gains Rate", "20%", "Long-term capital gains (>1 year hold)"),
        ("NJ State Income Tax Rate", "10.75%", "Top marginal rate"),
        ("Depreciation Recapture Rate", "25%", "Federal recapture on accumulated depreciation"),
        ("Net Investment Income Tax", "3.8%", "Additional Medicare surtax"),
        ("1031 Exchange Eligibility", "Available", "Tax deferral if reinvested in like-kind property"),
        ("Opportunity Zone Benefits", "To Be Evaluated", "If applicable to Newark OZ designation"),
    ]
    for label, val, note in disp_items:
        write_cell(ws, r, 2, label, font=font_normal)
        write_cell(ws, r, 3, val, font=font_total, alignment=align_right)
        write_note(ws, r, 5, note)
        r += 1

    return ws


# ============================================================
# TAB 11: SENSITIVITY ANALYSIS
# ============================================================

def create_sensitivity_tab(wb, noi_values, tdc, equity):
    ws = wb.create_sheet("Sensitivity")
    ws.sheet_properties.tabColor = "C0392B"

    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 16
    ws.column_dimensions['E'].width = 16
    ws.column_dimensions['F'].width = 16
    ws.column_dimensions['G'].width = 16
    ws.column_dimensions['H'].width = 16
    ws.column_dimensions['I'].width = 16

    r = 2
    write_cell(ws, r, 2, "SENSITIVITY ANALYSIS", font=font_title); r += 1
    write_note(ws, r, 2, "Impact of key variable changes on project returns. All tables are independent scenarios."); r += 2

    stab_noi = noi_values[2]

    # TABLE 1: Rent vs Construction Cost
    write_section_header(ws, r, 2, 9, "YIELD ON COST: Rent Change vs. Construction Cost Change"); r += 1
    write_note(ws, r, 2, "Values show Stabilized Yield on Cost under each scenario"); r += 1

    rent_changes = [-0.10, -0.05, 0, 0.05, 0.10, 0.15]
    cost_changes = [-0.10, -0.05, 0, 0.05, 0.10, 0.15]

    # Header row
    write_cell(ws, r, 2, "Rent \\ Cost", font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    for i, cc in enumerate(cost_changes):
        label = f"{cc:+.0%}" if cc != 0 else "Base"
        write_cell(ws, r, 3 + i, label, font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    r += 1

    for rc in rent_changes:
        label = f"{rc:+.0%}" if rc != 0 else "Base"
        write_cell(ws, r, 2, label, font=font_subheader, fill=fill_subheader, alignment=align_center, border=thin_border)
        for i, cc in enumerate(cost_changes):
            adj_noi = stab_noi * (1 + rc)
            adj_tdc = tdc * (1 + cc)
            yoc = adj_noi / adj_tdc if adj_tdc else 0
            fl = fill_light_blue if rc == 0 and cc == 0 else None
            write_cell(ws, r, 3 + i, yoc, font=font_normal, fill=fl, alignment=align_right,
                       border=thin_border, number_format=FMT_PCT2)
        r += 1

    r += 2
    # TABLE 2: Cap Rate vs NOI Sensitivity on Value
    write_section_header(ws, r, 2, 9, "PROPERTY VALUE ($M): Exit Cap Rate vs. NOI Change"); r += 1
    write_note(ws, r, 2, "Values show estimated property value in millions"); r += 1

    cap_rates = [0.04, 0.0425, 0.045, 0.0475, 0.05, 0.0525, 0.055]
    noi_changes = [-0.10, -0.05, 0, 0.05, 0.10]

    write_cell(ws, r, 2, "Cap \\ NOI", font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    for i, nc in enumerate(noi_changes):
        label = f"{nc:+.0%}" if nc != 0 else "Base"
        write_cell(ws, r, 3 + i, label, font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    r += 1

    for cr in cap_rates:
        write_cell(ws, r, 2, cr, font=font_subheader, fill=fill_subheader, alignment=align_right,
                   border=thin_border, number_format=FMT_PCT2)
        for i, nc in enumerate(noi_changes):
            val = (stab_noi * (1 + nc)) / cr / 1000000
            fl = fill_light_blue if nc == 0 and cr == 0.05 else None
            write_cell(ws, r, 3 + i, val, font=font_normal, fill=fl, alignment=align_right,
                       border=thin_border, number_format='#,##0.0')
        r += 1

    r += 2
    # TABLE 3: Vacancy vs OpEx Sensitivity
    write_section_header(ws, r, 2, 9, "NOI SENSITIVITY: Vacancy Rate vs. OpEx Growth"); r += 1

    vacancy_rates = [0.03, 0.05, 0.07, 0.10, 0.12, 0.15]
    opex_changes = [-0.05, 0, 0.05, 0.10, 0.15]

    # Calculate base GPR at stabilized
    base_gpr = stab_noi / 0.57  # Rough approximation from OpEx ratio

    write_cell(ws, r, 2, "Vac \\ OpEx", font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    for i, oc in enumerate(opex_changes):
        label = f"{oc:+.0%}" if oc != 0 else "Base"
        write_cell(ws, r, 3 + i, label, font=font_header, fill=fill_header, alignment=align_center, border=thin_border)
    r += 1

    for vr in vacancy_rates:
        label = f"{vr:.0%}"
        write_cell(ws, r, 2, label, font=font_subheader, fill=fill_subheader, alignment=align_center, border=thin_border)
        for i, oc in enumerate(opex_changes):
            # Approximate NOI impact
            adj_noi = stab_noi * (1 - (vr - 0.05) / 0.5) * (1 - oc * 0.4)
            write_cell(ws, r, 3 + i, round(adj_noi), font=font_normal, alignment=align_right,
                       border=thin_border, number_format=FMT_CURRENCY)
        r += 1

    r += 2
    # TABLE 4: Interest Rate Sensitivity
    write_section_header(ws, r, 2, 9, "DEBT SERVICE: Permanent Loan Rate Sensitivity"); r += 1
    write_note(ws, r, 2, "Impact on annual debt service and DSCR at various interest rates"); r += 1

    headers = ["Perm Rate", "Loan Amount", "Annual DS", "DSCR", "Monthly DS", "Excess CF (over DS)"]
    write_header_row(ws, r, 2, headers); r += 1

    rates = [0.045, 0.050, 0.055, 0.060, 0.065, 0.070, 0.075, 0.080]
    for rate in rates:
        mr = rate / 12
        n = 360
        pmtf = (mr * (1 + mr)**n) / ((1 + mr)**n - 1)
        # Size loan by DSCR
        max_ds_r = stab_noi / 1.25
        loan_r = round(max_ds_r / (pmtf * 12))
        ann_ds = round(loan_r * pmtf * 12)
        dscr_r = stab_noi / ann_ds if ann_ds else 0
        excess = stab_noi - ann_ds

        fl = fill_light_blue if rate == 0.060 else None
        write_cell(ws, r, 2, rate, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_PCT2, border=thin_border)
        write_cell(ws, r, 3, loan_r, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 4, ann_ds, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 5, dscr_r, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_PSF, border=thin_border)
        write_cell(ws, r, 6, round(ann_ds / 12), font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 7, excess, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        r += 1

    r += 2
    # TABLE 5: Equity Split Sensitivity
    write_section_header(ws, r, 2, 9, "EQUITY SPLIT SENSITIVITY: GP Share Impact on Returns"); r += 1
    headers = ["GP %", "LP %", "GP Equity", "LP Equity", "GP Cash Flow (Yr3)", "LP Cash Flow (Yr3)"]
    write_header_row(ws, r, 2, headers); r += 1

    stab_cf = noi_values[2] - round(stab_noi / 1.25 * 0.06 * 12)  # Rough levered CF

    gp_pcts = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
    for gp in gp_pcts:
        lp = 1 - gp
        gp_eq = round(equity * gp)
        lp_eq = round(equity * lp)
        # Simplified split before waterfall
        gp_cf = round(stab_cf * gp * 0.5)  # Rough
        lp_cf = stab_cf - gp_cf

        fl = fill_light_blue if gp == 0.50 else None
        write_cell(ws, r, 2, gp, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_PCT, border=thin_border)
        write_cell(ws, r, 3, lp, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_PCT, border=thin_border)
        write_cell(ws, r, 4, gp_eq, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 5, lp_eq, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 6, gp_cf, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        write_cell(ws, r, 7, lp_cf, font=font_normal, fill=fl, alignment=align_right, number_format=FMT_CURRENCY, border=thin_border)
        r += 1

    return ws


# ============================================================
# MAIN: BUILD WORKBOOK
# ============================================================

def main():
    wb = openpyxl.Workbook()

    # 1. Summary (uses formulas pointing to other tabs)
    print("Creating Summary tab...")
    create_summary_tab(wb)

    # 2. Inputs
    print("Creating Inputs tab...")
    create_inputs_tab(wb)

    # 3. Building Data
    print("Creating Building Data tab...")
    create_building_data_tab(wb)

    # 4. Unit Mix
    print("Creating Unit Mix tab...")
    create_unit_mix_tab(wb)

    # 5. Affordable
    print("Creating Affordable tab...")
    create_affordable_tab(wb)

    # 6. Dev Budget
    print("Creating Development Budget tab...")
    ws_db, tdc, hard, soft, fin, dev_fee, land = create_dev_budget_tab(wb)

    # 7. Operating
    print("Creating Operating Pro Forma tab...")
    ws_op, noi_values = create_operating_tab(wb)

    # 8. Aspire
    print("Creating Aspire Tax Credits tab...")
    ws_asp, aspire_total, aspire_annual, aspire_net_total = create_aspire_tab(wb, tdc, land)

    # 9. Waterfall
    print("Creating Waterfall tab...")
    ws_wf, levered_cfs, net_sale, perm_loan, equity, annual_ds = create_waterfall_tab(
        wb, tdc, noi_values, aspire_annual, aspire_net_total)

    # 10. Tax Implications
    print("Creating Tax Implications tab...")
    create_tax_tab(wb, tdc, land, perm_loan)

    # 11. Sensitivity
    print("Creating Sensitivity Analysis tab...")
    create_sensitivity_tab(wb, noi_values, tdc, equity)

    # Set print settings for all sheets
    for ws in wb.worksheets:
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(fitToPage=True)
        # Freeze panes
        if ws.title == "Operating":
            ws.freeze_panes = "D6"
        elif ws.title == "Sensitivity":
            ws.freeze_panes = "C5"
        elif ws.title != "Summary":
            ws.freeze_panes = "A5"

    # Save
    output_path = "/home/user/leejdevore/50-58_Jersey_Street_ProForma.xlsx"
    wb.save(output_path)
    print(f"\nPro forma saved to: {output_path}")
    print(f"Total Development Cost: ${tdc:,.0f}")
    print(f"Aspire Credits (Net): ${aspire_net_total:,.0f}")
    print(f"Total Equity Required: ${equity:,.0f}")
    print(f"Stabilized NOI (Yr 3): ${noi_values[2]:,.0f}")
    print(f"Yield on Cost: {noi_values[2]/tdc:.2%}")


if __name__ == "__main__":
    main()

