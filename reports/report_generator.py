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
        Creates a simplified PDF report with session info, data entry input, and reference image.
        """
        if filename is None:
            filename = f"report_{session_data.get('session_id', 'unknown')}.pdf"
            
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "WorkProof Audit Report")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Data Entry Session Report")
        c.line(50, height - 75, width - 50, height - 75)
        
        # Session Info
        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Session Information")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(70, y, f"Session ID: {session_data.get('session_id')}")
        y -= 15
        c.drawString(70, y, f"Timestamp: {session_data.get('timestamp', 'N/A')}")
        y -= 15
        c.drawString(70, y, f"Time Spent: {session_data.get('time_spent')}")
        y -= 30
        
        # Data Entry Input
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Data Entry Input")
        y -= 20
        c.setFont("Helvetica", 9)
        
        # Define categories for organized display
        categories = {
            "Customer Information": ["Customer ID", "First Name", "Last Name", "Age", "Gender", 
                                    "Address", "City", "Contact Number", "Email"],
            "Account Information": ["Account Type", "Account Balance", "Date Of Account Opening", 
                                   "Last Transaction Date", "Branch ID", "Transaction ID"],
            "Transaction Information": ["Transaction Date", "Transaction Type", "Transaction Amount", 
                                       "Account Balance After Transaction"],
            "Loan Information": ["Loan ID", "Loan Amount", "Loan Type", "Interest Rate", 
                                "Loan Term", "Approval/Rejection Date", "Loan Status", "Anomaly"],
            "Credit Card Information": ["Card ID", "Card Type", "Credit Limit", "Credit Card Balance", 
                                       "Minimum Payment Due", "Payment Due Date", 
                                       "Last Credit Card Payment Date", "Rewards Points"],
            "Feedback Information": ["Feedback ID", "Feedback Date", "Feedback Type", 
                                    "Resolution Status", "Resolution Date"]
        }
        
        form_data = session_data.get('form_data', {})
        
        for category, field_names in categories.items():
            # Check if we need a new page
            if y < 100:
                c.showPage()
                y = height - 50
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"[{category}]")
            y -= 18
            c.setFont("Helvetica", 9)
            
            for field_name in field_names:
                # Check if we need a new page
                if y < 80:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 9)
                
                value = form_data.get(field_name, "")
                
                # Display field name and value on the same line with proper alignment
                c.setFont("Helvetica", 9)
                c.drawString(70, y, f"{field_name}:")
                
                if value and str(value).strip():
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont("Helvetica-Bold", 9)
                    # Align values at a fixed position (250 pixels from left)
                    c.drawString(250, y, f"{str(value)[:60]}")
                    c.setFont("Helvetica", 9)
                else:
                    c.setFillColorRGB(0.6, 0.6, 0.6)
                    c.setFont("Helvetica-Oblique", 8)
                    c.drawString(250, y, "(No data entered)")
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont("Helvetica", 9)
                
                y -= 14
            
            y -= 8
        
        # Reference Image
        if session_data.get('reference_path') and os.path.exists(session_data['reference_path']):
            if y < 300:
                c.showPage()
                y = height - 50
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Reference Image")
            y -= 15
            try:
                img_height = min(250, y - 50)
                c.drawImage(
                    os.path.abspath(session_data['reference_path']), 
                    50, y - img_height, 
                    width=500, 
                    height=img_height, 
                    preserveAspectRatio=True
                )
            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(70, y - 20, f"[Error loading image: {str(e)}]")

        c.save()
        return filepath

