from fpdf import FPDF
from src.domain.models import CBTEntry
import tempfile
import os
import matplotlib.pyplot as plt
import pandas as pd
from typing import List

class PDFGeneratorService:
    @staticmethod
    def _sanitize_text(text: str) -> str:
        replacements = {
            'ă': 'a', 'Ă': 'A', 'â': 'a', 'Â': 'A', 'î': 'i', 'Î': 'I',
            'ș': 's', 'Ș': 'S', 'ț': 't', 'Ț': 'T', 'ş': 's', 'Ş': 'S', 'ţ': 't', 'Ţ': 'T'
        }
        for search, replace in replacements.items():
            text = text.replace(search, replace)
        return text.encode('latin-1', errors='ignore').decode('latin-1')

    @staticmethod
    def _draw_arrow(pdf, x, y):
        # Draw a downward directional arrow to guide the user's flow
        pdf.set_draw_color(150, 150, 150)
        pdf.set_line_width(0.8)
        pdf.line(x, y, x, y + 8)
        pdf.line(x, y + 8, x - 3, y + 5)
        pdf.line(x, y + 8, x + 3, y + 5)

    @staticmethod
    def _generate_history_chart(history: List[CBTEntry], temp_path: str):
        # Prepare data
        dates = pd.to_datetime([entry.data_creare for entry in history], format="%d/%m/%Y %H:%M:%S")
        intensities = [entry.intensitate_emotie for entry in history]
        
        # Plot styling
        plt.figure(figsize=(8, 4))
        plt.plot(dates, intensities, marker='o', linestyle='-', color='#880e4f', linewidth=2, markersize=6)
        plt.title('Evoluția Intensității Emoționale', fontsize=14, color='#333333', pad=15)
        plt.xlabel('Timp', fontsize=10, color='#666666')
        plt.ylabel('Intensitate Emoție (0-10)', fontsize=10, color='#666666')
        plt.ylim(-0.5, 10.5)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save to file
        plt.savefig(temp_path, format='png', dpi=300)
        plt.close()

    @staticmethod
    def create_cbt_report(entry: CBTEntry, history: List[CBTEntry] = None) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Center coordinates for A4 (210mm wide)
        x_center = 105
        box_width = 170
        x_margin = (210 - box_width) / 2
        
        # Set margins for centered blocks
        pdf.set_left_margin(x_margin)
        pdf.set_right_margin(x_margin)
        
        # --- Title ---
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 15, txt="Jurnal CBT", ln=True, align="C")
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, txt=f"Data: {entry.data_creare}", ln=True, align="C")
        pdf.ln(8)
        
        emotii_str = ", ".join(entry.emotii) if entry.emotii else "-"
        
        sections = [
            {
                "title": "SITUATIE",
                "subtitle": "Ce s-a intamplat?",
                "content": PDFGeneratorService._sanitize_text(entry.situatie),
                "bg_color": (227, 242, 253),  # Light Blue
                "title_color": (13, 71, 161),
                "text_color": (30, 30, 30)
            },
            {
                "title": "GANDURI AUTOMATE",
                "subtitle": "Ce gandeam in acel moment?",
                "content": f"{PDFGeneratorService._sanitize_text(entry.ganduri)}\n\n[Cat de adevarate par: {entry.veridicitate_ganduri}/10]",
                "bg_color": (255, 249, 196),  # Light Yellow
                "title_color": (230, 81, 0),
                "text_color": (30, 30, 30)
            },
            {
                "title": "EMOTII",
                "subtitle": "Ce am simtit?",
                "content": f"{PDFGeneratorService._sanitize_text(emotii_str)}\n\n[Intensitate: {entry.intensitate_emotie}/10]",
                "bg_color": (252, 228, 236),  # Light Pink
                "title_color": (136, 14, 79),
                "text_color": (30, 30, 30)
            },
            {
                "title": "COMPORTAMENT",
                "subtitle": "Cum am reactionat?",
                "content": PDFGeneratorService._sanitize_text(entry.comportament),
                "bg_color": (232, 245, 233),  # Light Green
                "title_color": (27, 94, 32),
                "text_color": (30, 30, 30)
            }
        ]
        
        for i, sec in enumerate(sections):
            # Page break protection for boxes
            if pdf.get_y() > 230:
                pdf.add_page()
                
            pdf.set_fill_color(*sec["bg_color"])
            
            # Top padding for box
            pdf.cell(0, 4, txt="", ln=True, align="C", fill=True)
            
            # Title
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(*sec["title_color"])
            pdf.cell(0, 6, txt=sec["title"], ln=True, align="C", fill=True)
            
            # Subtitle
            pdf.set_font("Arial", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, txt=sec["subtitle"], ln=True, align="C", fill=True)
            
            # Middle padding
            pdf.cell(0, 3, txt="", ln=True, align="C", fill=True)
            
            # Content
            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(*sec["text_color"])
            pdf.multi_cell(0, 7, txt=sec["content"], align="C", fill=True)
            
            # Bottom padding for box
            pdf.cell(0, 6, txt="", ln=True, align="C", fill=True)
            
            # Draw connecting arrow between boxes (except after the last one)
            if i < len(sections) - 1:
                current_y = pdf.get_y() + 2
                PDFGeneratorService._draw_arrow(pdf, x_center, current_y)
                pdf.set_y(current_y + 12)
            else:
                pdf.ln(10)

        if history and len(history) > 1: # Require at least 2 points to draw a meaningful line
            # Add new page for the chart to ensure it fits well
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 10, txt="Evolutia Intensitatilor Emotionale", ln=True, align="C")
            pdf.ln(5)

            # Generate chart image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                temp_path = tmpfile.name
            
            try:
                PDFGeneratorService._generate_history_chart(history, temp_path)
                # Calculate image width to center it (A4 is 210mm wide)
                img_width = 160
                img_x = (210 - img_width) / 2
                pdf.image(temp_path, x=img_x, w=img_width)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        return pdf.output(dest="S").encode("latin-1")