from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from datetime import datetime

class PDFService:
    def generate_insurance_report(self, data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()

        # Attempt to load the Sentry logo from the Next.js public directory.
        # Path: backend/services/pdf_service.py -> ... -> sentry/public/sentry_logo_png.png
        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "sentry", "public", "sentry_logo_png.png")
        )
        logo_img = None
        if os.path.exists(logo_path):
            try:
                # Let ReportLab infer natural size and then constrain while preserving aspect ratio
                logo_img = Image(logo_path)
                logo_img._restrictSize(1.4 * inch, 0.5 * inch)
                logo_img.hAlign = 'LEFT'
            except Exception as e:
                print(f"Logo load failed in PDF service: {e}")
        else:
            print(f"Logo file not found at: {logo_path}")
        
        # Custom Styles
        # Header Styles (White text for dark background)
        header_title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.white,
            alignment=2,  # Right align
            spaceAfter=2
        )
        
        header_subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#cccccc'),
            alignment=2,  # Right align
        )
        
        brand_style = ParagraphStyle(
            'BrandLabel',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.white,
            spaceBefore=0,
            spaceAfter=0,
            alignment=0 # Left align
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50'),
            borderPadding=5,
            borderColor=colors.HexColor('#d4af37'),
            borderWidth=0,
            borderBottomWidth=1
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 14

        # --- Header ---
        # Full-width dark bar
        
        # Left Side: Logo + Brand
        left_content = []
        if logo_img:
            left_content.append(logo_img)
        else:
            left_content.append(Paragraph("S", brand_style)) # Fallback
            
        left_content.append(Spacer(1, 5))
        left_content.append(Paragraph("SENTRY", brand_style))
        
        # Right Side: Title + Date + Subtitle
        right_content = []
        right_content.append(Paragraph("Agricultural Insurance Proposal", header_title_style))
        right_content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", header_subtitle_style))
        right_content.append(Paragraph("Wildlife Conservation Risk & Actuarial Insights", header_subtitle_style))

        # Create Header Table
        # Widths: Left (Logo area) approx 2 inch, Right (Title area) approx 5.5 inch
        # Total width is roughly page width - margins (8.5 - 2*1 = 6.5 inch usable? No, margins are 72pt=1inch)
        # Page width 8.5 inch. Margins 1 inch each side. Usable width = 6.5 inch.
        
        header_table = Table([[left_content, right_content]], colWidths=[2.0 * inch, 4.5 * inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 25))

        # --- Farmer / Location Details ---
        story.append(Paragraph("Farm & Location Details", heading_style))
        
        # Reverse Geocoding
        location_str = f"{data.get('lat', 0):.4f}, {data.get('lon', 0):.4f}"
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="sentry_pdf_service")
            location = geolocator.reverse(f"{data.get('lat', 0)}, {data.get('lon', 0)}", language='en')
            if location and location.address:
                address = location.raw.get('address', {})
                city = address.get('city') or address.get('town') or address.get('village') or address.get('county')
                state = address.get('state') or address.get('region')
                country = address.get('country')
                parts = [p for p in [city, state, country] if p]
                if parts:
                    location_str = ", ".join(parts) + f" ({location_str})"
        except Exception as e:
            print(f"Geocoding failed in PDF service: {e}")

        location_data = [
            ["Farm Name:", data.get('farmName', 'N/A')],
            ["Location:", location_str],
            ["Total Area:", f"{data.get('areaKm2', 0)} km²"],
            ["Crop Type:", data.get('cropType', 'Mixed')]
        ]
        
        t = Table(location_data, colWidths=[1.5*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#555555')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # --- Field Visualization ---
        if 'polygon' in data and data['polygon']:
            story.append(Paragraph("Field Boundary Analysis", heading_style))
            story.append(Paragraph("The following visualization represents the geofenced area used for satellite analysis and risk assessment.", normal_style))
            story.append(Spacer(1, 10))
            
            # Try to get Satellite Image first
            poly_img = None
            try:
                from backend.utils.gee_satellite import get_gee_instance
                gee = get_gee_instance()
                sat_img_bytes = gee.get_satellite_image(data['polygon'])
                if sat_img_bytes:
                    poly_img = BytesIO(sat_img_bytes)
            except Exception as e:
                print(f"Failed to get satellite image for PDF: {e}")
            
            # Fallback to Polygon Drawing if satellite image fails
            if not poly_img:
                poly_img = self.create_polygon_image(data['polygon'])

            if poly_img:
                img = Image(poly_img, width=5*inch, height=3.5*inch)
                story.append(img)
            story.append(Spacer(1, 20))

        # --- Gemini Location Analysis ---
        # If we have the polygon image (preferably satellite), we can try to get Gemini analysis
        if 'polygon' in data and data['polygon'] and poly_img:
            try:
                # Check if we have Gemini service available
                from backend.services.gemini_service import GeminiService
                gemini = GeminiService()
                
                # Reset buffer position for reading
                poly_img.seek(0)
                image_bytes = poly_img.getvalue()
                
                prompt = f"Analyze this satellite image of an agricultural area at {location_str}. Identify the specific crops grown and the agricultural landscape features. Return a concise 1-sentence description."
                
                analysis_result = gemini.analyze_image_with_search(image_bytes, prompt)
                
                if analysis_result and 'text' in analysis_result:
                    story.append(PageBreak())
                    story.append(Paragraph("AI-Powered Location Analysis", heading_style))
                    story.append(Paragraph(analysis_result['text'], normal_style))
                    
                    # Add Citations if available
                    if 'grounding_metadata' in analysis_result:
                        metadata = analysis_result['grounding_metadata']
                        if 'sources' in metadata and metadata['sources']:
                            story.append(Spacer(1, 10))
                            story.append(Paragraph("<b>Sources:</b>", normal_style))
                            for source in metadata['sources']:
                                title = source.get('title', 'Source')
                                uri = source.get('uri', '#')
                                # Create a link
                                link_text = f'<a href="{uri}" color="blue">{title}</a>'
                                story.append(Paragraph(f"• {link_text}", normal_style))
                                
                    story.append(Spacer(1, 20))
            except Exception as e:
                print(f"Gemini analysis skipped: {e}")
                pass

        # --- Risk Assessment ---
        story.append(Paragraph("Risk Assessment Summary", heading_style))
        
        risk_score = data.get('risk_score', 0)
        risk_level = "Low"
        risk_color = colors.green
        if risk_score > 75: 
            risk_level = "High"
            risk_color = colors.red
        elif risk_score > 50: 
            risk_level = "Medium"
            risk_color = colors.orange

        story.append(Paragraph(f"Composite Risk Score: <b>{risk_score}/100</b> ({risk_level} Risk)", normal_style))
        story.append(Paragraph("This score is calculated using our proprietary multi-factor actuarial model, incorporating satellite vegetation indices (NDVI), historical weather volatility, and soil moisture analytics.", normal_style))
        story.append(Spacer(1, 15))

        # --- Insurance Quote ---
        story.append(Paragraph("Insurance Policy Proposal", heading_style))
        
        quote_data = [
            ["Policy Type", data.get('policy_type', 'Standard')],
            ["Coverage Period", data.get('coverage_period', '12 Months')],
            ["Maximum Coverage", f"KES {data.get('max_coverage', 0):,}"],
            ["Deductible", f"KES {data.get('deductible', 0):,}"],
            ["Annual Premium", f"KES {data.get('premium', 0):,}"]
        ]
        
        q_table = Table(quote_data, colWidths=[2*inch, 3*inch])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#333333')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
            # Highlight Premium
            ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#fff8e1')),
            ('TEXTCOLOR', (1,4), (1,4), colors.HexColor('#d4af37')),
            ('FONTNAME', (1,4), (1,4), 'Helvetica-Bold'),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 20))

        # --- Risk Factors Chart ---
        if 'factors' in data and data['factors']:
            story.append(Paragraph("Key Risk Factors", heading_style))
            
            # Prepare data for chart
            factors = data['factors']
            # Take top 5 factors
            factors = factors[:5]
            
            # Create a simple bar chart using ReportLab drawing
            drawing = Drawing(400, 150)
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 20
            bc.height = 100
            bc.width = 300
            
            # Extract values and normalize/clamp to keep bars within bounds
            values = []
            for f in factors:
                try:
                    v = float(f.get('value', 0))
                except Exception:
                    v = 0.5
                values.append(v)

            # If values look like percentages (>1), scale to 0-1
            if any(v > 1 for v in values):
                values = [max(0.0, v / 100.0) for v in values]

            max_val = max(values) if values else 1.0
            bc.data = [values]
            bc.categoryAxis.categoryNames = [f.get('name', '')[:10] for f in factors]  # Truncate names
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(1.0, max_val * 1.1)  # Add headroom to prevent overflow
            bc.bars[0].fillColor = colors.HexColor('#d4af37')
            
            drawing.add(bc)
            story.append(drawing)
            story.append(Spacer(1, 30))
            
            # Factor Details Table
            factor_data = [["Risk Factor", "Impact Level", "Value"]]
            for f in factors:
                factor_data.append([f.get('name', 'N/A'), f.get('impact', 'N/A'), f.get('value', 'N/A')])
                
            f_table = Table(factor_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#333333')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            story.append(f_table)

        # --- Recommended Actions ---
        if 'recommended_actions' in data and data['recommended_actions']:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Recommended Mitigation Actions", heading_style))
            for action in data['recommended_actions']:
                story.append(Paragraph(f"• {action}", normal_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def create_polygon_image(self, polygon_data):
        """
        Generates a PNG image of the polygon using matplotlib.
        polygon_data: List of dicts {'lat': float, 'lng': float}
        """
        try:
            lats = [p['lat'] for p in polygon_data]
            lngs = [p['lng'] for p in polygon_data]
            
            # Close the polygon if not closed
            if lats[0] != lats[-1] or lngs[0] != lngs[-1]:
                lats.append(lats[0])
                lngs.append(lngs[0])

            plt.figure(figsize=(5, 3.5))
            plt.plot(lngs, lats, color='#d4af37', linewidth=2)
            plt.fill(lngs, lats, color='#d4af37', alpha=0.2)
            
            # Add some padding
            margin = 0.001
            plt.xlim(min(lngs) - margin, max(lngs) + margin)
            plt.ylim(min(lats) - margin, max(lats) + margin)
            
            plt.axis('off') # Hide axis
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, transparent=True)
            plt.close()
            img_buffer.seek(0)
            return img_buffer
        except Exception as e:
            print(f"Error generating polygon image: {e}")
            return None
