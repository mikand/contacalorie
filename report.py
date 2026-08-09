#!/usr/bin/env python

import io

from reportlab.pdfgen import canvas

from calorie import format_date_italian

point = 1
inch = 72

def make_pdf_file(apartment, cost, period):
    """Build the cost notice. `period` is a (start, end) pair of date objects.

    Everything drawn on the page is Italian: this is the letter the resident
    receives.
    """
    period = tuple(format_date_italian(d) for d in period)
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=(8.5 * inch, 11 * inch))
    c.setStrokeColorRGB(0,0,0)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica", 22 * point)
    v = 10 * inch
    c.drawString(1 * inch, v, "Ripartizione costi gas %s" % apartment)
    v -= 40 * point
    c.setFont("Helvetica", 12 * point)
    c.drawString(1 * inch, v, "Il costo da pagare per il periodo dal %s al %s (comprensivo di uso cucina +" % period)
    v -= 12 * point
    c.drawString(1 * inch, v, "acqua calda sanitaria + riscaldamento) e' di euro %.2f." % \
                 float(cost))
    v -= 40 * point
    c.drawString(1 * inch, v, "Distinti Saluti,")
    v -= 22 * point
    c.drawString(1 * inch, v, "Micheli Carlo")

    c.showPage()
    c.save()

    output.seek(0)
    return output
