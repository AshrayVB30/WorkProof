from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import os

class ReportGenerator:
    """
    Generates audit-ready PDF reports for user sessions.
    """
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)


    def generate_pdf(self, session_data, filename=None):
        """
        Creates a PDF report comparing Reference Data vs User Input.
        """
        if filename is None:
            filename = f"report_{session_data.get('session_id', 'unknown')}.pdf"
            
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "WorkProof Accuracy Report")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Web Reference vs User Input Comparison")
        c.line(50, height - 75, width - 50, height - 75)
        
        # Summary Info & Metrics
        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Session Summary")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(70, y, f"Session ID: {session_data.get('session_id')}")
        c.drawString(300, y, f"Timestamp: {session_data.get('timestamp', 'N/A')}")
        y -= 15
        c.drawString(70, y, f"Time Spent: {session_data.get('time_spent')}")
        
        # Metrics Highlight
        accuracy = session_data.get('accuracy', 0)
        errors = session_data.get('error_count', 0)
        total = session_data.get('total_fields', 0)
        correct = session_data.get('correct_fields', 0)
        
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(70, y, f"Overall Accuracy: {accuracy}%")
        c.drawString(250, y, f"Correct Matches: {correct}/{total}")
        c.drawString(450, y, f"Mismatches: {errors}")
        y -= 10
        c.line(70, y, width - 70, y)
        y -= 40
        
        # Detailed Comparison Table
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Detailed Field Comparison")
        y -= 25
        
        # Table Header
        data = [["Field Name", "Reference (Web)", "User Input", "Result"]]
        
        # Field results
        field_results = session_data.get('field_results', [])
        for res in field_results:
            status = "MATCH ✅" if res.get('is_correct') else ("MISMATCH ❌" if res.get('has_both') else "PENDING")
            data.append([
                res.get('field', ''),
                str(res.get('reference', ''))[:40],
                str(res.get('user', ''))[:40],
                status
            ])
            
        # Create Table
        t = Table(data, colWidths=[120, 160, 160, 80])
        
        # Table Style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left align field names
        ])
        
        # Add conditional coloring for results
        for i, res in enumerate(field_results):
            if res.get('is_correct'):
                style.add('TEXTCOLOR', (3, i+1), (3, i+1), colors.green)
            elif res.get('has_both'):
                style.add('TEXTCOLOR', (3, i+1), (3, i+1), colors.red)
        
        t.setStyle(style)
        
        # Wrap table and draw it (handles page breaks better if we used platypus SimpleDocTemplate)
        # But for this simple canvas implementation, we'll just check height
        table_height = t.wrap(0, 0)[1]
        if y - table_height < 50:
            c.showPage()
            y = height - 50
            
        t.drawOn(c, 50, y - table_height)
        y -= (table_height + 40)
        
        # Screen Monitor Screenshot (if available)
        if session_data.get('screenshot_path') and os.path.exists(session_data['screenshot_path']):
            if y < 200:
                c.showPage()
                y = height - 50
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Session Screenshot")
            y -= 15
            try:
                img_height = min(250, y - 50)
                c.drawImage(
                    os.path.abspath(session_data['screenshot_path']), 
                    50, y - img_height, 
                    width=500, 
                    height=img_height, 
                    preserveAspectRatio=True
                )
            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(70, y - 20, f"[Error loading screenshot: {str(e)}]")

        c.save()
        return filepath

        c.save()
        return filepath

