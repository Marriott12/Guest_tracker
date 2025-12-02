"""
Export views for Guest Tracker
Handles CSV, Excel, and PDF exports
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

from .models import Event, Guest, Invitation, RSVP, CheckInLog


@login_required
def export_guest_list_csv(request, event_id):
    """Export guest list to CSV"""
    event = get_object_or_404(Event, id=event_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="guest_list_{event.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Rank', 'Institution', 'RSVP Status', 'Plus Ones', 'Table', 'Seat', 'Checked In'])
    
    for invitation in event.invitations.select_related('guest').all():
        rsvp = getattr(invitation, 'rsvp', None)
        rsvp_status = rsvp.response if rsvp else 'No Response'
        plus_ones = rsvp.plus_ones if rsvp else 0
        
        writer.writerow([
            invitation.guest.full_name,
            invitation.guest.email,
            invitation.guest.phone or '',
            invitation.guest.rank or '',
            invitation.guest.institution or '',
            rsvp_status,
            plus_ones,
            invitation.table_number or '',
            invitation.seat_number or '',
            'Yes' if invitation.checked_in else 'No'
        ])
    
    return response


@login_required
def export_guest_list_excel(request, event_id):
    """Export guest list to Excel with formatting"""
    event = get_object_or_404(Event, id=event_id)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Guest List"
    
    # Header styling
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    # Headers
    headers = ['Name', 'Email', 'Phone', 'Rank', 'Institution', 'RSVP Status', 'Plus Ones', 'Table', 'Seat', 'Checked In']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Data rows
    for row_num, invitation in enumerate(event.invitations.select_related('guest').all(), 2):
        rsvp = getattr(invitation, 'rsvp', None)
        rsvp_status = rsvp.response if rsvp else 'No Response'
        plus_ones = rsvp.plus_ones if rsvp else 0
        
        data = [
            invitation.guest.full_name,
            invitation.guest.email,
            invitation.guest.phone or '',
            invitation.guest.rank or '',
            invitation.guest.institution or '',
            rsvp_status,
            plus_ones,
            invitation.table_number or '',
            invitation.seat_number or '',
            'Yes' if invitation.checked_in else 'No'
        ]
        
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            
            # Color code RSVP status
            if col_num == 6:  # RSVP Status column
                if value == 'yes':
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif value == 'no':
                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                elif value == 'maybe':
                    cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            
            # Color code check-in status
            if col_num == 10:  # Checked In column
                if value == 'Yes':
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    cell.font = Font(bold=True, color="006100")
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="guest_list_{event.name}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    
    return response


@login_required
def export_checkin_log_csv(request, event_id):
    """Export check-in log to CSV"""
    event = get_object_or_404(Event, id=event_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="checkin_log_{event.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Guest Name', 'Email', 'Check-In Time', 'Table', 'Seat'])
    
    for invitation in event.invitations.filter(checked_in=True).select_related('guest').order_by('check_in_time'):
        writer.writerow([
            invitation.guest.full_name,
            invitation.guest.email,
            invitation.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if invitation.check_in_time else '',
            invitation.table_number or '',
            invitation.seat_number or ''
        ])
    
    return response


@login_required
def export_rsvp_report_csv(request, event_id):
    """Export RSVP report to CSV"""
    event = get_object_or_404(Event, id=event_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rsvp_report_{event.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Guest Name', 'Email', 'RSVP Status', 'Plus Ones', 'Dietary Restrictions', 'Notes', 'Responded At'])
    
    for invitation in event.invitations.select_related('guest').all():
        rsvp = getattr(invitation, 'rsvp', None)
        if rsvp:
            writer.writerow([
                invitation.guest.full_name,
                invitation.guest.email,
                rsvp.response,
                rsvp.plus_ones,
                rsvp.dietary_restrictions or '',
                rsvp.notes or '',
                rsvp.responded_at.strftime('%Y-%m-%d %H:%M:%S') if rsvp.responded_at else ''
            ])
        else:
            writer.writerow([
                invitation.guest.full_name,
                invitation.guest.email,
                'No Response',
                0,
                '',
                '',
                ''
            ])
    
    return response


@login_required
def export_seating_chart_pdf(request, event_id):
    """Export seating chart to PDF"""
    event = get_object_or_404(Event, id=event_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="seating_chart_{event.name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0066CC'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    title = Paragraph(f"Seating Chart - {event.name}", title_style)
    elements.append(title)
    
    subtitle = Paragraph(f"{event.date.strftime('%B %d, %Y at %I:%M %p')} - {event.location}", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    # Get all tables
    tables = {}
    for invitation in event.invitations.filter(table_number__isnull=False).select_related('guest'):
        table_num = invitation.table_number
        if table_num not in tables:
            tables[table_num] = []
        tables[table_num].append(invitation)
    
    # Create table for each table number
    for table_num in sorted(tables.keys(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x)):
        # Table header
        table_title = Paragraph(f"<b>Table {table_num}</b>", styles['Heading2'])
        elements.append(table_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Guest list for this table
        data = [['Seat', 'Guest Name', 'Rank', 'RSVP', 'Checked In']]
        
        for invitation in sorted(tables[table_num], key=lambda x: x.seat_number or ''):
            rsvp = getattr(invitation, 'rsvp', None)
            rsvp_status = rsvp.response if rsvp else 'No Response'
            
            data.append([
                invitation.seat_number or '',
                invitation.guest.full_name,
                invitation.guest.rank or '',
                rsvp_status.upper(),
                '✓' if invitation.checked_in else ''
            ])
        
        # Create and style table
        t = Table(data, colWidths=[0.8*inch, 3*inch, 1.5*inch, 1.2*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response
