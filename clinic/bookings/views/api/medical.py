"""
API endpoints for medical records management
Handles retrieval of medical records for admin interface
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ...models import MedicalRecord


@login_required
@require_http_methods(["GET"])
def api_get_medical_records(request):
    """Get all medical records with patient information"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        records = MedicalRecord.objects.select_related(
            'patient__user',
            'created_by'
        ).order_by('-visit_date')
        
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'patient_id': record.patient.id,
                'patient_name': record.patient.user.get_full_name() or record.patient.user.username,
                'visit_date': record.visit_date.strftime('%Y-%m-%d %H:%M'),
                'chief_complaint': record.chief_complaint,
                'diagnosis': record.diagnosis or 'N/A',
                'treatment_plan': record.treatment_plan or 'N/A',
                'created_by': record.created_by.get_full_name() if record.created_by else 'System',
            })
        
        return JsonResponse({
            'success': True,
            'records': records_data,
            'count': len(records_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
