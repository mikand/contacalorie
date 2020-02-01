import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4, cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


import locale
locale.setlocale(locale.LC_ALL, 'it_IT.utf8')
import calendar


class HourReport(object):
    def __init__(self, month, year):
        self.month = month
        self.year = year
        self.workplaces = []
        self.worked_hours = []

    @property
    def vacations(self):
        return [w for w in self.workplaces if ('ferie' in w.lower() or 'permesso' in w.lower())]

    @property
    def illnesses(self):
        return [w for w in self.workplaces if 'malattia' in w.lower()]

    @property
    def real_workplaces(self):
        return [w for w in self.workplaces if w not in (self.vacations + self.illnesses)]

    def get_worked_hours(self, day, workplace):
        if workplace not in (self.vacations + self.illnesses):
            for f in self.vacations:
                wh = self.get_worked_hours(day, f)
                if wh is not None:
                    return 'FERIE'
            for f in self.illnesses:
                wh = self.get_worked_hours(day, f)
                if wh is not None:
                    return 'MALATTIA'
                
        for (d, p, sh, sm, eh, em) in self.worked_hours:
            if d == day and p == workplace:
                return (sh, sm, eh, em)
        return None


def hour(h, m):
    sm = str(m)
    if len(sm) == 1:
        sm = "0" + sm
    return '%d:%s' % (h, sm)

def get_hm(mins):
    return "%.2f" % (mins / 60)

def build_pdf_report(report, show_hours=False):
    styleSheet = getSampleStyleSheet()

    def center(s, bold=False):
        if bold:
            s = "<b>%s</b>" % s
        return Paragraph('<para align=center spaceb=3>%s</para>' % s,
                         styleSheet["BodyText"])

    small_style = ParagraphStyle('small',
                                 fontSize = 8,
                                 leading = 8,
                                 fontName="Helvetica")
    def small(s):
        return Paragraph(s, small_style)

    def build_header(report):
        res = [['Giorno', ''], ['', '']]
        for wp in report.real_workplaces:
            res[0] += [wp, '', '']
            res[1] += ['Orario', '', 'Tot. Ore']
        res[0] += ['', 'Tot.']
        res[1] += ['', '']
        return res

    def build_table():
        first_day, ndays = calendar.monthrange(report.year, report.month)
        data= build_header(report)

        wd = first_day
        total_minutes = 0
        for d in range(1, ndays+1):
            day = calendar.day_name[wd]
            wd = (wd + 1) % 7
            r = [str(d), day.capitalize()]

            total_minutes_today = 0

            for wp in report.real_workplaces:
                wt = report.get_worked_hours(d, wp)
                if wt is None:
                    r += ['', '', '']
                elif wt == 'FERIE':
                    r += ['', '', '']
                elif wt == 'MALATTIA':
                    r += ['', '', '']
                else:
                    (sh, sm, eh, em) = wt
                    wm = ((eh - sh) * 60) + (em - sm)
                    if show_hours:
                        r += [hour(sh, sm), hour(eh, em), get_hm(wm)]
                    else:
                        r += ['', '', get_hm(wm)]
                    total_minutes_today += wm

            vacation = False
            r.append('')
            for wp in report.vacations + report.illnesses:
                wt = report.get_worked_hours(d, wp)
                if wt is not None:
                    r.append(wp)
                    vacation = True
                    break
                    
            if not vacation:
                total_minutes += total_minutes_today
                r.append(get_hm(total_minutes_today))

            data.append(r)

        r = [''] * (3*len(report.real_workplaces) + 4)
        data.append(list(r))
        r[0] = "Totale del mese:"
        r[-1] = get_hm(total_minutes)
        data.append(r)

        style = [('SPAN', (0,0), (1,1)),

                 ('BOX',(0,0),(-3,-3),2,colors.black),
                 ('GRID',(0,0),(-3,-3),0.5,colors.black),
                 ('GRID',(0,2),(-3,1),1.5,colors.black),


                 ('SPAN', (-1,0), (-1,1)),
                 ('BOX',(-1,0),(-1,-3),2,colors.black),
                 ('GRID',(-1,0),(-1,-3),0.5,colors.black),
                 ('GRID',(-1,2),(-1,1),1.5,colors.black),

                 ('VALIGN',(0,0),(-1,-1), 'MIDDLE'),
                 ('ALIGN',(0,0),(-1,-1), 'CENTER'),
                 ('FONTSIZE', (0,0),(-1,-1), 8),
                 ('LEADING', (0,0),(-1,-1), 8),

                 ('FONT', (0,0), (-3, 1), 'Helvetica-Bold'),
                 ('FONT', (-1,0), (-1, 1), 'Helvetica-Bold'),

                 ('SPAN', (0,-1), (-3, -1)),
                 ('BOX',(0,-1), (-3, -1), 2, colors.black),
                 ('ALIGN',(0,-1),(-3,-1), 'RIGHT'),
                 ('BOX',(-1,-1), (-1, -1), 2, colors.black),
        ]
        idx = 2
        for wp in report.real_workplaces:
            style.append(('SPAN', (idx,0), (idx+2,0)))
            style.append(('SPAN', (idx,1), (idx+1,1)))
            style.append(('GRID',(idx,0),(idx-1,-3), 1.5, colors.black))

            idx += 3

        t = Table(data,style=style)
        return t

    output = io.BytesIO()
    doc = SimpleDocTemplate(output,
                            rightMargin=50,
                            leftMargin=50,
                            topMargin=15,
                            bottomMargin=15,
                            pagesize=landscape(A4))

    header = center('Rilevazione mensile di Gianna Dusini per il mese di %s %d' \
                    % (calendar.month_name[report.month].capitalize(), report.year),
                    bold=True)
    footer = center('Per cortesia, retribuire le ore effettivamente prestate. Grazie.',
                    bold=True)

    elements = []
    elements.append(header)
    elements.append(Spacer(width=0, height=0.2 * cm) )
    elements.append(build_table())
    elements.append(footer)

    # write the document
    doc.build(elements)

    output.seek(0)
    return output


if __name__ == "__main__":
    test = HourReport(1, 2008)
    test.workplaces = ["Comune Cles", "GSH"]
    test.worked_hours = [(1, "Comune Cles", 16, 30, 17, 30),
                         (1, "GSH", 17, 45, 21, 00),
                         (3, "GSH", 18, 45, 21, 00)]

    build_pdf_report(test)
