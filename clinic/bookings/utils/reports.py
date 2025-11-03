"""
Report generation utilities for PDF and CSV exports.
"""
import csv
from io import BytesIO
from datetime import datetime, date
from django.http import HttpResponse
from django.db.models import Count, Q
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import logging

from ..models import Booking, Patient, Service, Billing

logger = logging.getLogger(__name__)


def generate_appointments_pdf(start_date=None, end_date=None, status=None):
    """
    Generate PDF report of appointments within a date range.
    
    Args:
        start_date: Start date for filter (datetime.date)
        end_date: End date for filter (datetime.date)
        status: Optional status filter
        
    Returns:
        HttpResponse with PDF content
    """
    # Create response object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointments_report_{date.today()}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Add title
    title = Paragraph("Appointments Report", title_style)
    elements.append(title)
    
    # Add date range info
    date_info = f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    if start_date and end_date:
        date_info += f"<br/>Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
    if status:
        date_info += f"<br/>Status: {status}"
    
    date_para = Paragraph(date_info, styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Query appointments
    appointments = Booking.objects.select_related('service', 'created_by')
    
    if start_date:
        appointments = appointments.filter(date__gte=start_date)
    if end_date:
        appointments = appointments.filter(date__lte=end_date)
    if status:
        appointments = appointments.filter(status=status)
    
    appointments = appointments.order_by('-date', '-time')
    
    # Create table data
    data = [['Date', 'Time', 'Patient', 'Service', 'Status']]
    
    for appointment in appointments:
        data.append([
            appointment.date.strftime('%m/%d/%Y'),
            appointment.time.strftime('%I:%M %p'),
            appointment.patient_name,
            appointment.service.name,
            appointment.status
        ])
    
    # Create table
    if len(data) > 1:  # Has data beyond header
        table = Table(data, colWidths=[1*inch, 1*inch, 2*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(table)
    else:
        no_data = Paragraph("No appointments found for the selected criteria.", styles['Normal'])
        elements.append(no_data)
    
    # Add summary section
    elements.append(Spacer(1, 30))
    summary_title = Paragraph("<b>Summary</b>", styles['Heading2'])
    elements.append(summary_title)
    elements.append(Spacer(1, 10))
    
    total_count = appointments.count()
    confirmed_count = appointments.filter(status='Confirmed').count()
    pending_count = appointments.filter(status='Pending').count()
    completed_count = appointments.filter(status='Completed').count()
    
    summary_text = f"""
    Total Appointments: {total_count}<br/>
    Confirmed: {confirmed_count}<br/>
    Pending: {pending_count}<br/>
    Completed: {completed_count}
    """
    summary_para = Paragraph(summary_text, styles['Normal'])
    elements.append(summary_para)
    
    # Add footer
    elements.append(Spacer(1, 30))
    footer = Paragraph(
        "<i>Romualdez Skin and Eye Clinic - Confidential Report</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF content from buffer
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    logger.info(f"Appointments PDF report generated with {total_count} records")
    return response


def export_patients_csv():
    """
    Export all patients to CSV file.
    
    Returns:
        HttpResponse with CSV content
    """
    # Create response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="patients_export_{date.today()}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Patient ID',
        'First Name',
        'Last Name',
        'Email',
        'Phone',
        'Date of Birth',
        'Gender',
        'Address',
        'Registration Date',
        'Total Visits'
    ])
    
    # Query patients with visit counts
    patients = Patient.objects.annotate(
        total_visits=Count('booking', filter=Q(booking__status='Completed'))
    ).order_by('-created_at')
    
    # Write data rows
    for patient in patients:
        writer.writerow([
            patient.id,
            patient.first_name,
            patient.last_name,
            patient.email,
            patient.phone,
            patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
            patient.gender,
            patient.address or '',
            patient.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            patient.total_visits
        ])
    
    logger.info(f"Patients CSV export generated with {patients.count()} records")
    return response


def export_billing_csv(start_date=None, end_date=None):
    """
    Export billing records to CSV file.
    
    Args:
        start_date: Start date for filter (datetime.date)
        end_date: End date for filter (datetime.date)
        
    Returns:
        HttpResponse with CSV content
    """
    # Create response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="billing_export_{date.today()}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Billing ID',
        'Patient Name',
        'Patient Email',
        'Date',
        'Service Fee',
        'Medicine Fee',
        'Additional Fee',
        'Discount',
        'Total Amount',
        'Amount Paid',
        'Balance',
        'Payment Status'
    ])
    
    # Query billing records
    billings = Billing.objects.select_related('booking').order_by('-created_at')
    
    if start_date:
        billings = billings.filter(created_at__date__gte=start_date)
    if end_date:
        billings = billings.filter(created_at__date__lte=end_date)
    
    # Write data rows
    for billing in billings:
        writer.writerow([
            billing.id,
            billing.booking.patient_name,
            billing.booking.patient_email,
            billing.created_at.strftime('%Y-%m-%d'),
            f'{billing.service_fee:.2f}',
            f'{billing.medicine_fee:.2f}',
            f'{billing.additional_fee:.2f}',
            f'{billing.discount:.2f}',
            f'{billing.total_amount:.2f}',
            f'{billing.amount_paid:.2f}',
            f'{billing.balance:.2f}',
            'Paid' if billing.is_paid else 'Unpaid'
        ])
    
    logger.info(f"Billing CSV export generated with {billings.count()} records")
    return response


def generate_services_pdf():
    """
    Generate PDF report of all available services.
    
    Returns:
        HttpResponse with PDF content
    """
    # Create response object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="services_report_{date.today()}.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=1
    )
    
    title = Paragraph("Services Report", title_style)
    elements.append(title)
    
    date_info = f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    date_para = Paragraph(date_info, styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Query services
    services = Service.objects.annotate(
        total_bookings=Count('booking')
    ).order_by('name')
    
    # Create table data
    data = [['Service Name', 'Description', 'Price', 'Total Bookings']]
    
    for service in services:
        # Truncate description if too long
        description = service.description[:50] + '...' if len(service.description) > 50 else service.description
        
        data.append([
            service.name,
            description,
            f'₱{service.price:.2f}',
            str(service.total_bookings)
        ])
    
    # Create table
    if len(data) > 1:
        table = Table(data, colWidths=[2*inch, 3*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    logger.info(f"Services PDF report generated with {services.count()} services")
    return response
