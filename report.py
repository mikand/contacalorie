#!/usr/bin/env python

import io

from reportlab.pdfgen import canvas

from calorie import format_date_italian

point = 1
inch = 72

def make_pdf_file(appartamento, costo, date):
    """Build the cost notice. `date` is a (start, end) pair of date objects."""
    date = tuple(format_date_italian(d) for d in date)
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=(8.5 * inch, 11 * inch))
    c.setStrokeColorRGB(0,0,0)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica", 22 * point)
    v = 10 * inch
    c.drawString(1 * inch, v, "Ripartizione costi gas %s" % appartamento)
    v -= 40 * point
    c.setFont("Helvetica", 12 * point)
    c.drawString(1 * inch, v, "Il costo da pagare per il periodo dal %s al %s (comprensivo di uso cucina +" % date)
    v -= 12 * point
    c.drawString(1 * inch, v, "acqua calda sanitaria + riscaldamento) e' di euro %.2f." % \
                 float(costo))
    v -= 40 * point
    c.drawString(1 * inch, v, "Distinti Saluti,")
    v -= 22 * point
    c.drawString(1 * inch, v, "Micheli Carlo")

    c.showPage()
    c.save()

    output.seek(0)
    return output
