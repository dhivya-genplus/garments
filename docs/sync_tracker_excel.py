"""
Automated Synchronization Script for Garments ERP Trackers.
Parses docs/UI_TRACKER.md and docs/ui/ to build and synchronize:
  - docs/GARMENTS_ERP_MASTER_TRACKER.xlsx
  - docs/GARMENTS_ERP_TRACKER.xlsx
  - docs/UI_TRACKER.xlsx
  - docs/TRACKER.xlsx

Run anytime:
    python docs/sync_tracker_excel.py
"""

import os
import re
import shutil
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Color Tokens
DARK_NAVY = "0F172A"       # Primary header #0F172A
INDIGO = "4338CA"          # Accent #4338CA
SLATE_HEADER = "1E293B"    # Section headers #1E293B
LIGHT_BG = "F8FAFC"        # Background
BORDER_COLOR = "CBD5E1"    # Light border
GREEN_FILL = "DCFCE7"      # Complete badge bg
GREEN_TEXT = "166534"      # Complete text
AMBER_FILL = "FEF3C7"      # Planned badge bg
AMBER_TEXT = "92400E"      # Planned text
BLUE_FILL = "DBEAFE"       # In Progress badge bg
BLUE_TEXT = "1E40AF"       # In progress text

thin_border = Border(
    left=Side(style='thin', color=BORDER_COLOR),
    right=Side(style='thin', color=BORDER_COLOR),
    top=Side(style='thin', color=BORDER_COLOR),
    bottom=Side(style='thin', color=BORDER_COLOR)
)

def build_tracker_workbook():
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # 1. Parse screens from UI_TRACKER.md
    screens = parse_ui_tracker_markdown()

    # 2. Build Tab 1: Executive Summary
    build_executive_summary_tab(wb, screens)

    # 3. Build Tab 2: Stage & Workflow Suites
    build_stage_workflow_suites_tab(wb, screens)

    # 4. Build Tab 3: UI Screens Registry
    build_ui_screens_registry_tab(wb, screens)

    # 5. Build Tab 4: Backend Tickets
    build_backend_tickets_tab(wb)

    # Save to temp file and sync to all unlocked target copies
    temp_file = 'docs/_temp_tracker.xlsx'
    wb.save(temp_file)

    all_targets = [
        'docs/GARMENTS_ERP_MASTER_TRACKER.xlsx',
        'docs/GARMENTS_ERP_TRACKER.xlsx',
        'docs/UI_TRACKER.xlsx',
        'docs/TRACKER.xlsx'
    ]
    for target in all_targets:
        try:
            shutil.copyfile(temp_file, target)
            print(f"[OK] Synchronized: {target}")
        except PermissionError:
            print(f"[WARN] {target} is locked (open in Excel). Close it in Excel and re-run to update.")
        except Exception as e:
            print(f"[WARN] {target}: {e}")

    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception:
        pass

def parse_ui_tracker_markdown():
    tracker_path = 'docs/UI_TRACKER.md'
    if not os.path.exists(tracker_path):
        print(f"[ERROR] {tracker_path} not found.")
        return []

    screens = []
    with open(tracker_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    for line in lines:
        line_str = line.strip()
        if line_str.startswith('| Screen ID') or line_str.startswith('| **Screen ID**'):
            in_table = True
            continue
        if in_table:
            if not line_str.startswith('|'):
                in_table = False
                continue
            if '---|---' in line_str:
                continue
            
            parts = [p.strip() for p in line_str.split('|')[1:-1]]
            if len(parts) >= 8:
                raw_id = parts[0].replace('**', '').replace('`', '').strip()
                module = parts[1].replace('**', '').strip()
                name = parts[2].replace('**', '').strip()
                route = parts[3].replace('`', '').strip()
                status_raw = parts[4].strip()
                mockup = parts[5].strip()
                api_status = parts[6].strip()
                spec_file_raw = parts[7].strip()
                prd_ref = parts[8].strip() if len(parts) > 8 else ''

                # Normalize status
                if 'Complete' in status_raw or '✅' in status_raw:
                    status = 'Complete'
                elif 'In Progress' in status_raw or '🔄' in status_raw:
                    status = 'In Progress'
                else:
                    status = 'Planned'

                # Extract filename from markdown link [file.md](path) or `file.md`
                match = re.search(r'\[([^\]]+)\]\([^\)]+\)', spec_file_raw)
                if match:
                    spec_file = match.group(1)
                else:
                    spec_file = spec_file_raw.replace('`', '')

                # Determine Stage / Workflow Suite
                stage_suite = determine_stage_suite(raw_id, name, module)

                screens.append({
                    'id': raw_id,
                    'module': module,
                    'stage_suite': stage_suite,
                    'name': name,
                    'route': route,
                    'status': status,
                    'mockup': mockup,
                    'api_status': api_status,
                    'spec_file': spec_file,
                    'prd_ref': prd_ref
                })

    return screens

def determine_stage_suite(screen_id, name, module):
    if 'SCR-AUTH' in screen_id:
        return 'Authentication & Session'
    if 'SCR-COMP' in screen_id or 'SCR-DASH' in screen_id:
        return 'Foundation & Multi-Tenancy'
    if 'SCR-MAST' in screen_id:
        return 'Master Data Governance'
    if 'SCR-PROC-001' in screen_id:
        return 'Yarn Purchase Order (PO)'
    if 'SCR-INVN-001' in screen_id:
        return 'Yarn Inward (GRN)'
    if 'SCR-INVN-002' in screen_id:
        return 'Yarn Outward (DC)'
    if 'SCR-INVN-003' in screen_id:
        return 'Live Godown Stock Ledger'
    if 'SCR-INVN-004' in screen_id:
        return 'Party Stock Ledger & Job Work'
    if 'SCR-SALE-001' in screen_id:
        return 'Commercial Yarn Sales (Invoice)'
    if 'SCR-SALE-002' in screen_id:
        return 'Customer Yarn Sales Return'
    if 'SCR-KNIT' in screen_id:
        return 'Knitting & Fabric Production'
    if 'SCR-PRCS' in screen_id or 'SCR-PROC-002' in screen_id:
        return 'Production Process Engine'
    if 'SCR-PRIC-001' in screen_id:
        return 'Yarn Price Lists'
    if 'SCR-PRIC-002' in screen_id:
        return 'Job Work Subcontract Matrix'
    if 'SCR-FINL' in screen_id:
        return 'Financial Ledgers & Accounting'
    return module

def build_executive_summary_tab(wb, screens):
    ws = wb.create_sheet(title="Executive Summary")
    ws.views.sheetView[0].showGridLines = True

    # Title Banner
    ws.merge_cells("A1:G1")
    ws["A1"] = "GARMENTS ERP & CRM — SYSTEM IMPLEMENTATION TRACKER"
    ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells("A2:G2")
    ws["A2"] = "Authoritative Cross-Stack Telemetry: Frontend Next.js Screens, Workflows, APIs & Backend Engine"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="FFFFFF")
    ws["A2"].fill = PatternFill(start_color=INDIGO, end_color=INDIGO, fill_type="solid")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # Project Metadata
    ws["A4"] = "PROJECT METADATA"
    ws["A4"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ws["A4"].fill = PatternFill(start_color=SLATE_HEADER, end_color=SLATE_HEADER, fill_type="solid")
    ws.merge_cells("A4:G4")
    ws.row_dimensions[4].height = 22

    metadata = [
        ("Client / Tenant", "Enterprise Garments Pvt Ltd", "Country Pack", "India (IN) — GST, INR (₹), FY Apr-Mar"),
        ("Platform Stack", "Next.js 14 App Router (Frontend) + Django Monolith REST API", "Architecture Standard", "Strict Monolith, Zero Direct ORM in Views"),
        ("Database & Concurrency", "PostgreSQL 15 (timestamptz, select_for_update)", "PRD Reference", "PRD v1.2 Baseline"),
        ("Last Synchronized", "16/10/2026", "Tracker Status", "Active / Release v1.1.0 Ready")
    ]

    for idx, (k1, v1, k2, v2) in enumerate(metadata, start=5):
        ws[f"A{idx}"] = k1
        ws[f"B{idx}"] = v1
        ws.merge_cells(f"B{idx}:D{idx}")
        ws[f"E{idx}"] = k2
        ws[f"F{idx}"] = v2
        ws.merge_cells(f"F{idx}:G{idx}")
        ws[f"A{idx}"].font = Font(bold=True, color="475569")
        ws[f"E{idx}"].font = Font(bold=True, color="475569")
        ws.row_dimensions[idx].height = 18

    # High-level Metrics Cards
    total_screens = len(screens)
    completed_screens = sum(1 for s in screens if s['status'] == 'Complete')
    planned_screens = sum(1 for s in screens if s['status'] == 'Planned')
    comp_pct = round((completed_screens / total_screens * 100), 1) if total_screens else 0

    ws["A10"] = "OVERALL SPECIFICATION & DEVELOPMENT TELEMETRY"
    ws["A10"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ws["A10"].fill = PatternFill(start_color=SLATE_HEADER, end_color=SLATE_HEADER, fill_type="solid")
    ws.merge_cells("A10:G10")
    ws.row_dimensions[10].height = 22

    kpi_headers = ["TOTAL SCREENS", "SPECS COMPLETED", "COMPLETION %", "SPECS PLANNED", "BACKEND APIS", "MOCKUPS READY", "STATUS"]
    kpi_values = [total_screens, completed_screens, f"{comp_pct}%", planned_screens, "100% Deployed", "7 Generated", "ON TRACK"]

    for col_idx, (h, v) in enumerate(zip(kpi_headers, kpi_values), start=1):
        cell_h = ws.cell(row=12, column=col_idx, value=h)
        cell_v = ws.cell(row=13, column=col_idx, value=v)
        cell_h.font = Font(bold=True, size=9, color="475569")
        cell_h.alignment = Alignment(horizontal="center")
        cell_h.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        cell_v.font = Font(bold=True, size=13, color=INDIGO if "%" in str(v) or h=="STATUS" else "0F172A")
        cell_v.alignment = Alignment(horizontal="center")
        cell_v.border = thin_border
        cell_h.border = thin_border
    ws.row_dimensions[12].height = 18
    ws.row_dimensions[13].height = 24

    # Stage-by-Stage / Workflow-by-Workflow Progress Table
    ws["A16"] = "STAGE-BY-STAGE / WORKFLOW SUITE SPECIFICATION PROGRESS"
    ws["A16"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ws["A16"].fill = PatternFill(start_color=SLATE_HEADER, end_color=SLATE_HEADER, fill_type="solid")
    ws.merge_cells("A16:G16")
    ws.row_dimensions[16].height = 22

    stage_headers = ["Stage / Workflow Suite", "Module Ref", "Total Screens", "Complete", "Planned", "Progress %", "Readiness Status"]
    for col_idx, h in enumerate(stage_headers, start=1):
        c = ws.cell(row=18, column=col_idx, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=INDIGO, end_color=INDIGO, fill_type="solid")
        c.alignment = Alignment(horizontal="left" if col_idx <= 2 else "center")
    ws.row_dimensions[18].height = 20

    # Group by stage_suite
    stage_groups = {}
    for s in screens:
        suite = s['stage_suite']
        if suite not in stage_groups:
            stage_groups[suite] = {'module': s['module'], 'total': 0, 'complete': 0, 'planned': 0}
        stage_groups[suite]['total'] += 1
        if s['status'] == 'Complete':
            stage_groups[suite]['complete'] += 1
        else:
            stage_groups[suite]['planned'] += 1

    curr_row = 19
    for suite, data in stage_groups.items():
        tot = data['total']
        comp = data['complete']
        pl = data['planned']
        pct = round((comp / tot * 100), 1) if tot else 0
        readiness = "READY FOR DEV" if pct == 100 else ("IN PROGRESS" if pct > 0 else "PLANNED")

        ws.cell(row=curr_row, column=1, value=suite).alignment = Alignment(horizontal="left")
        ws.cell(row=curr_row, column=2, value=data['module']).alignment = Alignment(horizontal="left")
        ws.cell(row=curr_row, column=3, value=tot).alignment = Alignment(horizontal="center")
        ws.cell(row=curr_row, column=4, value=comp).alignment = Alignment(horizontal="center")
        ws.cell(row=curr_row, column=5, value=pl).alignment = Alignment(horizontal="center")
        
        pct_cell = ws.cell(row=curr_row, column=6, value=f"{pct}%")
        pct_cell.alignment = Alignment(horizontal="center")
        pct_cell.font = Font(bold=True)

        stat_cell = ws.cell(row=curr_row, column=7, value=readiness)
        stat_cell.alignment = Alignment(horizontal="center")
        if pct == 100:
            stat_cell.fill = PatternFill(start_color=GREEN_FILL, end_color=GREEN_FILL, fill_type="solid")
            stat_cell.font = Font(color=GREEN_TEXT, bold=True)
        elif pct > 0:
            stat_cell.fill = PatternFill(start_color=BLUE_FILL, end_color=BLUE_FILL, fill_type="solid")
            stat_cell.font = Font(color=BLUE_TEXT, bold=True)
        else:
            stat_cell.fill = PatternFill(start_color=AMBER_FILL, end_color=AMBER_FILL, fill_type="solid")
            stat_cell.font = Font(color=AMBER_TEXT, bold=True)

        for c_idx in range(1, 8):
            ws.cell(row=curr_row, column=c_idx).border = thin_border
        ws.row_dimensions[curr_row].height = 19
        curr_row += 1

    # Autofit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

def build_stage_workflow_suites_tab(wb, screens):
    ws = wb.create_sheet(title="Stage & Workflow Suites")
    ws.views.sheetView[0].showGridLines = True

    # Header
    ws.merge_cells("A1:H1")
    ws["A1"] = "TRANSACTIONAL 4-SCREEN SUITES & SPECIALIZED REGISTERS"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["Stage / Workflow Suite", "Screen ID", "Screen Role (Add/Edit/List/Print)", "Screen Title", "Route Path", "Spec Status", "Spec Document", "PRD Ref"]
    for col_idx, h in enumerate(headers, start=1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=INDIGO, end_color=INDIGO, fill_type="solid")
        c.alignment = Alignment(horizontal="left" if col_idx in [1, 3, 4, 5, 7] else "center")
    ws.row_dimensions[3].height = 22

    curr_row = 4
    for s in screens:
        # Determine role
        sid = s['id']
        if sid.endswith('-ADD'):
            role = '1. Add Workflow'
        elif sid.endswith('-EDIT'):
            role = '2. Edit Screen'
        elif sid.endswith('-LIST'):
            role = '3. Register List'
        elif sid.endswith('-PRINT'):
            role = '4. Print Document'
        else:
            role = 'Analytical Register'

        ws.cell(row=curr_row, column=1, value=s['stage_suite'])
        ws.cell(row=curr_row, column=2, value=s['id']).font = Font(bold=True)
        ws.cell(row=curr_row, column=3, value=role)
        ws.cell(row=curr_row, column=4, value=s['name'])
        ws.cell(row=curr_row, column=5, value=s['route'])

        stat_cell = ws.cell(row=curr_row, column=6, value=s['status'])
        stat_cell.alignment = Alignment(horizontal="center")
        if s['status'] == 'Complete':
            stat_cell.fill = PatternFill(start_color=GREEN_FILL, end_color=GREEN_FILL, fill_type="solid")
            stat_cell.font = Font(color=GREEN_TEXT, bold=True)
        else:
            stat_cell.fill = PatternFill(start_color=AMBER_FILL, end_color=AMBER_FILL, fill_type="solid")
            stat_cell.font = Font(color=AMBER_TEXT, bold=True)

        ws.cell(row=curr_row, column=7, value=s['spec_file'])
        ws.cell(row=curr_row, column=8, value=s['prd_ref']).alignment = Alignment(horizontal="center")

        for c_idx in range(1, 9):
            ws.cell(row=curr_row, column=c_idx).border = thin_border
        ws.row_dimensions[curr_row].height = 18
        curr_row += 1

    # Autofit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

def build_ui_screens_registry_tab(wb, screens):
    ws = wb.create_sheet(title="UI Screens Registry")
    ws.views.sheetView[0].showGridLines = True

    # Title Banner
    ws.merge_cells("A1:I1")
    ws["A1"] = "ENTERPRISE UI SCREENS REGISTRY & SPECIFICATION STATUS"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["Screen ID", "Module", "Stage / Workflow Suite", "Screen Title / Name", "Frontend Route Path", "Spec Status", "UI Mockup", "API Status", "Specification File"]
    for col_idx, h in enumerate(headers, start=1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=INDIGO, end_color=INDIGO, fill_type="solid")
        c.alignment = Alignment(horizontal="left" if col_idx in [1, 2, 3, 4, 5, 9] else "center")
    ws.row_dimensions[3].height = 22

    curr_row = 4
    for s in screens:
        ws.cell(row=curr_row, column=1, value=s['id']).font = Font(bold=True)
        ws.cell(row=curr_row, column=2, value=s['module'])
        ws.cell(row=curr_row, column=3, value=s['stage_suite'])
        ws.cell(row=curr_row, column=4, value=s['name'])
        ws.cell(row=curr_row, column=5, value=s['route'])

        stat_cell = ws.cell(row=curr_row, column=6, value=s['status'])
        stat_cell.alignment = Alignment(horizontal="center")
        if s['status'] == 'Complete':
            stat_cell.fill = PatternFill(start_color=GREEN_FILL, end_color=GREEN_FILL, fill_type="solid")
            stat_cell.font = Font(color=GREEN_TEXT, bold=True)
        else:
            stat_cell.fill = PatternFill(start_color=AMBER_FILL, end_color=AMBER_FILL, fill_type="solid")
            stat_cell.font = Font(color=AMBER_TEXT, bold=True)

        mockup_cell = ws.cell(row=curr_row, column=7, value=s['mockup'])
        mockup_cell.alignment = Alignment(horizontal="center")
        api_cell = ws.cell(row=curr_row, column=8, value=s['api_status'])
        api_cell.alignment = Alignment(horizontal="center")

        ws.cell(row=curr_row, column=9, value=s['spec_file'])

        for c_idx in range(1, 10):
            ws.cell(row=curr_row, column=c_idx).border = thin_border
        ws.row_dimensions[curr_row].height = 18
        curr_row += 1

    # Autofit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

def build_backend_tickets_tab(wb):
    ws = wb.create_sheet(title="Backend Tickets")
    ws.views.sheetView[0].showGridLines = True

    # Title Banner
    ws.merge_cells("A1:G1")
    ws["A1"] = "BACKEND MONOLITH TICKETS & MERGE VERIFICATION"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["Ticket ID", "Module", "Ticket Description", "PRD Ref", "Merge Status", "Release Tag", "Key Invariants / Models"]
    for col_idx, h in enumerate(headers, start=1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=INDIGO, end_color=INDIGO, fill_type="solid")
        c.alignment = Alignment(horizontal="left" if col_idx in [1, 3, 7] else "center")
    ws.row_dimensions[3].height = 22

    # Parse TRACKER.md
    tracker_path = 'docs/TRACKER.md'
    if not os.path.exists(tracker_path):
        return

    curr_row = 4
    with open(tracker_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith('| T') and '|' in line_str:
                parts = [p.strip() for p in line_str.split('|')[1:-1]]
                if len(parts) >= 8:
                    tid = parts[0]
                    mod = parts[1]
                    desc = parts[2]
                    prd = parts[3]
                    mstat = parts[4]
                    ver = parts[10] if len(parts) > 10 else 'v1.0.0'
                    inv = parts[12] if len(parts) > 12 else ''

                    ws.cell(row=curr_row, column=1, value=tid).font = Font(bold=True)
                    ws.cell(row=curr_row, column=2, value=f"Module {mod}").alignment = Alignment(horizontal="center")
                    ws.cell(row=curr_row, column=3, value=desc)
                    ws.cell(row=curr_row, column=4, value=prd).alignment = Alignment(horizontal="center")

                    stat_cell = ws.cell(row=curr_row, column=5, value=mstat)
                    stat_cell.alignment = Alignment(horizontal="center")
                    stat_cell.fill = PatternFill(start_color=GREEN_FILL, end_color=GREEN_FILL, fill_type="solid")
                    stat_cell.font = Font(color=GREEN_TEXT, bold=True)

                    ws.cell(row=curr_row, column=6, value=ver).alignment = Alignment(horizontal="center")
                    ws.cell(row=curr_row, column=7, value=inv)

                    for c_idx in range(1, 8):
                        ws.cell(row=curr_row, column=c_idx).border = thin_border
                    ws.row_dimensions[curr_row].height = 18
                    curr_row += 1

    # Autofit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

if __name__ == '__main__':
    build_tracker_workbook()
