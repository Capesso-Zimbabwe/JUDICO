from datetime import datetime
import requests
from .models import DilisenseConfig

def get_dilisense_config():
    config = DilisenseConfig.objects.first()
    if not config:
        raise Exception("DILISense configuration not found. Please set up your API key in the admin.")
    return config
###########################################################################################################

# views.py
import requests
from django.http import HttpResponse, JsonResponse
from .models import DilisenseConfig

import requests
from django.http import JsonResponse
from django.shortcuts import render
from .models import DilisenseConfig

import requests
from django.shortcuts import render
from .models import DilisenseConfig

def check_individual(request):
    """
    View to handle searching individuals via DILISense checkIndividual endpoint.
    Filters results by source_type if specified (ALL, SANCTION, PEP, CRIMINAL).
    """
    # 1) Read query parameters from the GET request
    query = request.GET.get('query', '')  # e.g. "John Doe"
    source_type = request.GET.get('source_type', 'ALL')  # e.g. "PEP", "SANCTION", etc.
    
    # If no search term is provided, render the template without results
    if not query:
        return render(request, 'check_individual.html', {
            'error': "No search term provided."
        })
    
    # 2) Make sure we have a DilisenseConfig with an API key
    config = DilisenseConfig.objects.first()
    if not config:
        return render(request, 'check_individual.html', {
            'error': "DILISense API key not configured. Please set up DILISense configuration."
        })
    
    # 3) Prepare DILISense request (names= query)
    url = "https://api.dilisense.com/v1/checkIndividual"
    params = {
        "names": query,  # searching only the name fields
        # We do NOT add includes= source_type here, because we plan to filter afterwards
    }
    headers = {
        "x-api-key": config.api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # 4) Call DILISense
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()  # e.g. { 'total_hits': X, 'found_records': [...] }

        # 5) If there's an error or no 'found_records' in the data, handle it
        if 'found_records' not in results:
            return render(request, 'check_individual.html', {
                'error': "Invalid response from DILISense.",
                'results': None
            })
        
        # 6) Post-filter by source_type (if not 'ALL')
        if source_type != 'ALL':
            filtered = []
            for record in results['found_records']:
                # record['source_type'] might be "SANCTION", "PEP", "CRIMINAL", etc.
                if record.get('source_type', '').upper() == source_type.upper():
                    filtered.append(record)
            results['found_records'] = filtered
            # Update total_hits to reflect filtered records
            results['total_hits'] = len(filtered)



            # Save these results in the session for the PDF
        request.session['last_results'] = results
        request.session['last_query'] = query
        request.session['last_source_type'] = source_type

        
        
        # 7) Render results
        # If no matches remain after filtering, we can pass an error or let the template handle
        if results['total_hits'] == 0:
            return render(request, 'check_individual.html', {
                'error': "No records found for your search.",
                'results': results
            })
        
        
        
        return render(request, 'check_individual.html', {
            'results': results,
            'query': query,
            'source_type': source_type,
        })
    
    except requests.RequestException as e:
        # Handle network/HTTP errors
        return render(request, 'check_individual.html', {
            'error': f"Error communicating with DILISense: {str(e)}"
        })


###########################################################################################################
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponse

# Try to import WeasyPrint, fall back to ReportLab if not available
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    # Import ReportLab as fallback
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import io


def download_individual_report(request):
    """
    Generates a PDF from the last search results stored in session
    and returns it as a file download.
    """
    results = request.session.get('last_results')
    query = request.session.get('last_query', 'Unknown')
    source_type = request.session.get('last_source_type', 'ALL')

    if not results:
        # There's no stored data
        return HttpResponse("No data available for PDF.", status=400)

    # Optionally add a timestamp or any other info
    screening_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

    if WEASYPRINT_AVAILABLE:
        # Use WeasyPrint for HTML to PDF conversion
        html_string = render_to_string('pdf_template.html', {
            'results': results,
            'query': query,
            'source_type': source_type,
            'screening_time': screening_time,
        })
        pdf_file = HTML(string=html_string).write_pdf()
    else:
        # Use ReportLab as fallback
        pdf_file = _generate_pdf_with_reportlab(results, query, source_type, screening_time)

    # Return as downloadable file
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="DILISense_AML_report.pdf"'
    return response


def _generate_pdf_with_reportlab(results, query, source_type, screening_time):
    """
    Generate PDF using ReportLab as fallback when WeasyPrint is not available.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("DILISense AML Screening Report", title_style))
    story.append(Spacer(1, 12))
    
    # Report details
    details_data = [
        ['Query:', query],
        ['Source Type:', source_type],
        ['Screening Time:', screening_time],
    ]
    details_table = Table(details_data, colWidths=[2*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Results section
    if results and 'data' in results:
        story.append(Paragraph("Search Results:", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        for idx, result in enumerate(results['data'][:10], 1):  # Limit to first 10 results
            # Result header
            story.append(Paragraph(f"Result {idx}:", styles['Heading3']))
            
            # Result details
            result_data = []
            if 'name' in result:
                result_data.append(['Name:', str(result['name'])])
            if 'source' in result:
                result_data.append(['Source:', str(result['source'])])
            if 'match_strength' in result:
                result_data.append(['Match Strength:', str(result['match_strength'])])
            if 'categories' in result:
                categories = ', '.join(result['categories']) if isinstance(result['categories'], list) else str(result['categories'])
                result_data.append(['Categories:', categories])
            
            if result_data:
                result_table = Table(result_data, colWidths=[1.5*inch, 4.5*inch])
                result_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(result_table)
            story.append(Spacer(1, 12))
    else:
        story.append(Paragraph("No results found.", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


##########################################################################################################

def check_entity(search_all=None, names=None, fuzzy_search=None, includes=None):
    """
    Calls the DILISense checkEntity endpoint.
    """
    config = get_dilisense_config()
    url = "https://api.dilisense.com/v1/checkEntity"
    params = {}
    if search_all:
        params["search_all"] = search_all
    elif names:
        params["names"] = names
    if fuzzy_search:
        params["fuzzy_search"] = fuzzy_search
    if includes:
        params["includes"] = includes

    headers = {
        "x-api-key": config.api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def generate_entity_report(names, includes=None):
    """
    Calls the DILISense generateEntityReport endpoint.
    Returns a Base64 encoded PDF report.
    """
    config = get_dilisense_config()
    url = "https://api.dilisense.com/v1/generateEntityReport"
    params = {"names": names}
    if includes:
        params["includes"] = includes

    headers = {
        "x-api-key": config.api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def list_sources():
    """
    Calls the DILISense listSources endpoint.
    Returns the available sources as JSON.
    """
    config = get_dilisense_config()
    url = "https://api.dilisense.com/v1/listSources"
    headers = {
        "x-api-key": config.api_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
