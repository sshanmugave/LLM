from pathlib import Path
from typing import Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.config import OUTPUT_DIR
from app.database import get_connection, get_crs

def create_excel_export(output_filename: str = "Flyover_3D_Master_Model.xlsx") -> Path:
    """
    Generates a master-grade 7-sheet Excel workbook tailored for 2D to 3D BIM/CAD modeling:
    1. 3D_Pier_Master_Catalog (Spatial coordinates, skew angles, pier cap & shaft dimensions)
    2. 3D_Footing_Polygons (All 483 footing corner coordinates ordered for 3D extrusion)
    3. Superstructure_3D_Deck (Section 1-1 & Section 2-2 widths, slopes, barrier, slab)
    4. Span_&_Longitudinal_Profile (Span sequence, bearing offsets, expansion joints)
    5. Geotechnical_Subsurface_3D (BH-20 to BH-30 soil layers, SPT N, embedment depth Df)
    6. Materials_&_Engineering_Specs (Concrete grades M15-M55, design codes, drawing register)
    7. Executive_Summary_&_Insights (AI/Civil expert generated 3D modeling guidelines)
    """
    conn = get_connection()
    cursor = conn.cursor()
    crs_info = get_crs()
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove blank default sheet
    
    # Professional Styling Tokens
    font_family = "Segoe UI"
    header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    header_navy = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_slate = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_teal = PatternFill(start_color="134E5E", end_color="134E5E", fill_type="solid")
    
    title_font = Font(name=font_family, size=14, bold=True, color="1F4E78")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="595959")
    
    status_verified_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
    status_verified_font = Font(name=font_family, size=10, color="155724", bold=True)
    status_review_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    status_review_font = Font(name=font_family, size=10, color="856404", bold=True)
    status_unverified_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
    status_unverified_font = Font(name=font_family, size=10, color="721C24", bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    def apply_header_styles(ws, headers, fill=header_navy):
        ws.append(headers)
        ws.freeze_panes = "A2"
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws.auto_filter.ref = ws.dimensions

    def autofit_columns(ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if cell.row == 1:
                    max_len = max(max_len, len(val_str) + 3)
                else:
                    max_len = max(max_len, min(len(val_str), 45))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # -------------------------------------------------------------
    # Sheet 1: 3D_Pier_Master_Catalog
    # -------------------------------------------------------------
    ws_piers = wb.create_sheet(title="3D_Pier_Master_Catalog")
    pier_headers = [
        "Carriageway", "Pier ID", "Corner Points Range", "Insertion Easting (X)",
        "Insertion Northing (Y)", "Latitude (WGS84)", "Longitude (WGS84)",
        "Skew Angle (deg)", "Span Dist Prev (m)", "Typical Span (m)",
        "Footing Length (m)", "Footing Width (m)", "Pier Cap Width (mm)",
        "Pier Cap Center Depth (mm)", "Pier Cap Tip Depth (mm)", "Pier Cap Cantilever (mm)",
        "Pier Shaft Width (mm)", "Pier Shaft Thickness (mm)", "Pedestal Height (mm)",
        "Bearing Offset (mm)", "Source CAD", "Status", "Engineering Notes"
    ]
    apply_header_styles(ws_piers, pier_headers, header_navy)
    
    cursor.execute("""
        SELECT carriageway, pier_id, point_range, centre_easting, centre_northing,
               latitude, longitude, skew_angle_deg, distance_from_previous, span_length,
               footing_length, footing_width, pier_cap_width, pier_cap_center_depth,
               pier_cap_tip_depth, pier_cap_cantilever, pier_shaft_width,
               pier_shaft_thickness, pedestal_height, bearing_offset,
               source_pdfs, status, notes
        FROM piers
        ORDER BY carriageway, sequence_order, id
    """)
    for r_idx, row in enumerate(cursor.fetchall(), start=2):
        row_data = list(row)
        ws_piers.append(row_data)
        for c_idx in range(1, len(row_data) + 1):
            cell = ws_piers.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            # Coordinates
            if c_idx in [4, 5] and cell.value is not None:
                cell.number_format = '#,##0.000'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [6, 7] and cell.value is not None:
                cell.number_format = '0.00000000'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [8, 9, 10, 11, 12] and cell.value is not None:
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in range(13, 21) and cell.value is not None:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 22: # Status
                st = str(cell.value).upper()
                if "VERIFIED" in st:
                    cell.fill = status_verified_fill
                    cell.font = status_verified_font
                elif "UNVERIFIED" in st:
                    cell.fill = status_unverified_fill
                    cell.font = status_unverified_font
                else:
                    cell.fill = status_review_fill
                    cell.font = status_review_font
    autofit_columns(ws_piers)

    # -------------------------------------------------------------
    # Sheet 2: 3D_Footing_Polygons
    # -------------------------------------------------------------
    ws_points = wb.create_sheet(title="3D_Footing_Polygons")
    point_headers = [
        "Carriageway", "Pier ID", "Corner Point ID", "Easting (X)", "Northing (Y)",
        "Source CAD Drawing", "Sheet Number", "Status", "Verification Notes"
    ]
    apply_header_styles(ws_points, point_headers, header_slate)
    
    cursor.execute("""
        SELECT carriageway, pier_id, point_id, easting, northing,
               source_pdf, source_page, status, notes
        FROM corner_points
        ORDER BY carriageway, pier_id, point_id
    """)
    for r_idx, row in enumerate(cursor.fetchall(), start=2):
        row_data = list(row)
        ws_points.append(row_data)
        for c_idx in range(1, len(row_data) + 1):
            cell = ws_points.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if c_idx in [4, 5]:
                cell.number_format = '#,##0.000'
                cell.alignment = Alignment(horizontal="right")
    autofit_columns(ws_points)

    # -------------------------------------------------------------
    # Sheet 3: Superstructure_3D_Deck
    # -------------------------------------------------------------
    ws_deck = wb.create_sheet(title="Superstructure_3D_Deck")
    deck_headers = [
        "Section Name", "Description & Usage", "Carriageway Deck Width (mm)",
        "Roadway Width (mm)", "Median Gap (mm)", "Deck Slab Thk (mm)",
        "Wearing Coat Thk (mm)", "Cross Slope (%)", "Crash Barrier Width (mm)",
        "Curb Height (mm)", "Girder Configuration", "Girder Depth (mm)",
        "Concrete Grade", "CAD Drawing Scale"
    ]
    apply_header_styles(ws_deck, deck_headers, header_teal)
    
    cursor.execute("""
        SELECT section_name, description, carriageway_deck_width, roadway_width,
               median_gap, deck_slab_thk, wearing_coat_thk, cross_slope_pct,
               crash_barrier_width, curb_height, girder_type, girder_depth,
               concrete_grade, scale
        FROM deck_sections
        ORDER BY id
    """)
    for r_idx, row in enumerate(cursor.fetchall(), start=2):
        row_data = list(row)
        ws_deck.append(row_data)
        for c_idx in range(1, len(row_data) + 1):
            cell = ws_deck.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if c_idx in [3, 4, 5, 6, 7, 9, 10, 12]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 8:
                cell.number_format = '0.00%'
                cell.alignment = Alignment(horizontal="right")
    autofit_columns(ws_deck)

    # -------------------------------------------------------------
    # Sheet 4: Span_&_Longitudinal_Profile
    # -------------------------------------------------------------
    ws_spans = wb.create_sheet(title="Span_&_Longitudinal_Profile")
    span_headers = [
        "Span Index", "Carriageway", "From Pier", "To Pier",
        "Span Length (m)", "Clear Span (m)", "Bearing Offset Pier CL (mm)",
        "Expansion Joint Type", "Approach Slab Present", "Deck Structural System"
    ]
    apply_header_styles(ws_spans, span_headers, header_navy)
    
    # Query distinct spans along Main Carriageway and Loops
    cursor.execute("""
        SELECT carriageway, pier_id, span_length, bearing_offset, sequence_order
        FROM piers
        ORDER BY carriageway, sequence_order
    """)
    all_piers_rows = cursor.fetchall()
    
    span_idx = 1
    for i in range(len(all_piers_rows) - 1):
        p1 = all_piers_rows[i]
        p2 = all_piers_rows[i + 1]
        if p1["carriageway"] == p2["carriageway"]:
            c_len = (p1["span_length"] or 30000.0) / 1000.0
            clear_l = c_len - 1.5 if c_len == 30.0 else c_len - 1.3
            exp_jt = "Expansion Joint at Pier" if "A1" in p1["pier_id"] or "A2" in p2["pier_id"] or p1["pier_id"] in ["P4", "P10"] else "Continuous Deck Girder"
            appr = "Yes (Approach Slab 3.5m)" if "A1" in p1["pier_id"] or "A2" in p2["pier_id"] else "No"
            
            row_span = [
                f"SPAN-{span_idx:02d}", p1["carriageway"], p1["pier_id"], p2["pier_id"],
                c_len, clear_l, int(p1["bearing_offset"] or 750), exp_jt, appr,
                "Precast Prestressed Concrete (PSC) I-Girder + M55 RC Deck"
            ]
            ws_spans.append(row_span)
            r_row = ws_spans.max_row
            for c_idx in range(1, len(row_span) + 1):
                cell = ws_spans.cell(row=r_row, column=c_idx)
                cell.border = thin_border
                if c_idx in [5, 6]:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal="right")
                elif c_idx == 7:
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(horizontal="right")
            span_idx += 1
    autofit_columns(ws_spans)

    # -------------------------------------------------------------
    # Sheet 5: Geotechnical_Subsurface_3D
    # -------------------------------------------------------------
    ws_geo = wb.create_sheet(title="Geotechnical_Subsurface_3D")
    geo_headers = [
        "Borehole ID", "Location / Chainage", "Depth From (m)", "Depth To (m)",
        "Layer Thickness (m)", "Soil Strata Classification", "SPT 'N' Value",
        "Water Table Depth (m)", "Design Foundation Depth Df (m)", "Source CAD Sheet"
    ]
    apply_header_styles(ws_geo, geo_headers, header_slate)
    
    cursor.execute("""
        SELECT borehole_id, chainage, depth_from, depth_to,
               (depth_to - depth_from) AS layer_thk, strata_description,
               spt_n_value, water_table_m, foundation_depth_df, sheet_number
        FROM borehole_logs
        ORDER BY borehole_id, depth_from
    """)
    for r_idx, row in enumerate(cursor.fetchall(), start=2):
        row_data = list(row)
        ws_geo.append(row_data)
        for c_idx in range(1, len(row_data) + 1):
            cell = ws_geo.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if c_idx in [3, 4, 5, 8, 9]:
                cell.number_format = '0.00'
                cell.alignment = Alignment(horizontal="right")
    autofit_columns(ws_geo)

    # -------------------------------------------------------------
    # Sheet 6: Materials_&_Engineering_Specs
    # -------------------------------------------------------------
    ws_specs = wb.create_sheet(title="Materials_&_Engineering_Specs")
    
    ws_specs.cell(row=1, column=1, value="PROJECT ENGINEERING SPECIFICATIONS & MATERIAL MATRIX").font = title_font
    ws_specs.cell(row=2, column=1, value="Source Drawings: O24087-C-RP-MB-GA-8330 (Rev RC) & O24087-C-RP-MB-NU-8390 (Rev C)").font = subtitle_font
    
    specs_data = [
        ["Component Type", "Structural Element", "Specified Material Grade", "Governing Standard / Code", "Notes for 3D BIM Modeling"],
        ["Superstructure", "Precast PSC Girders", "Concrete Grade M55", "IRC:112-2020", "Prestressed concrete I-girders (4 per carriageway)"],
        ["Superstructure", "Cast-in-situ Deck Slab", "Concrete Grade M55", "IRC:112-2020", "300 mm thickness, cast continuous across spans"],
        ["Superstructure", "Wearing Coat", "Bituminous Concrete / Mastic", "MoRTH Section 500", "54 mm specified thickness"],
        ["Superstructure", "Crash Barrier", "Concrete Grade M40", "IRC:5-2015", "Reinforced concrete crash barrier, 525 mm base width"],
        ["Substructure", "Pier Shafts & Abutments", "Concrete Grade M40", "IRC:112-2020", "5000 mm x 2500 mm flared solid pier shaft"],
        ["Substructure", "Pier Caps & Pedestals", "Concrete Grade M35", "IRC:112-2020", "13600 mm transverse cantilever pier cap"],
        ["Foundation", "Open Footings / Pile Caps", "Concrete Grade M35", "IRC:78-2014", "Footing depths verified at Df = 2.50m below OGL"],
        ["Foundation", "PCC Leveling Course", "Concrete Grade M15", "MoRTH Section 1500", "150 mm thick blinding layer under footings"],
        ["Reinforcement", "High-Yield Rebar", "Steel Grade Fe500D", "IS:1786", "Thermo-Mechanically Treated (TMT) rebar"],
        ["Bearings", "Elastomeric Bearing Pads", "Elastomeric Type", "IRC:83 (Part II)", "Spaced 750 mm from pier CL on MCW, 650 mm on Loops"],
        ["Expansion Joints", "Strip Seal / Modular", "Compression / Strip Seal", "IRC:SP:69", "Located at Abutment A1, P4, P10, and Abutment A2"]
    ]
    
    for r_idx, srow in enumerate(specs_data, start=4):
        ws_specs.append(srow)
        for c_idx in range(1, len(srow) + 1):
            cell = ws_specs.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if r_idx == 4:
                cell.font = header_font
                cell.fill = header_navy
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                if c_idx == 3:
                    cell.font = Font(name=font_family, size=10, bold=True, color="1F4E78")
    autofit_columns(ws_specs)

    # -------------------------------------------------------------
    # Sheet 7: Executive_Summary_&_Insights
    # -------------------------------------------------------------
    ws_ai = wb.create_sheet(title="Executive_Summary_&_Insights")
    
    ws_ai.cell(row=1, column=1, value="AI & CIVIL ENGINEERING EXECUTIVE BRIEF FOR 3D MODELING TEAM").font = title_font
    ws_ai.cell(row=2, column=1, value="Automated drawing understanding, structural typology analysis, and 3D modeling guidelines.").font = subtitle_font
    
    ai_headers = ["Domain / Category", "Insight Module Title", "Technical Brief & 3D Conversion Rules", "Generated By"]
    ws_ai.cell(row=4, column=1).value = ""
    ws_ai.append(ai_headers)
    hdr_row = 5
    for c_idx in range(1, len(ai_headers) + 1):
        cell = ws_ai.cell(row=hdr_row, column=c_idx)
        cell.font = header_font
        cell.fill = header_teal
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        
    cursor.execute("SELECT category, title, content, generated_by FROM executive_insights ORDER BY id")
    for r_idx, row in enumerate(cursor.fetchall(), start=6):
        row_data = list(row)
        ws_ai.append(row_data)
        for c_idx in range(1, len(row_data) + 1):
            cell = ws_ai.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if c_idx == 3:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            elif c_idx in [1, 2, 4]:
                cell.alignment = Alignment(vertical="top")
                if c_idx == 2:
                    cell.font = Font(name=font_family, size=10, bold=True, color="1F4E78")
                    
    autofit_columns(ws_ai)
    ws_ai.column_dimensions['C'].width = 85  # Wider column for detailed insights

    conn.close()
    
    # Save workbook to output directory
    output_path = OUTPUT_DIR / output_filename
    wb.save(output_path)
    return output_path
