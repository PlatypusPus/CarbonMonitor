"""Presentation report from confirmed, calculated ledger entries."""

from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from models.ocr_draft import OCRDraft


def _text(value):
    return escape(str(value).replace('\u2014', ', '))


def _table(rows, widths):
    style = getSampleStyleSheet()['BodyText']
    style.fontSize, style.leading = 8, 11
    table = Table([[Paragraph(_text(cell), style) for cell in row] for row in rows],
                  colWidths=widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DCEDE3')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8F6')]),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#23734D')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return table


def generate_esg_pdf(db: Session) -> bytes:
    rows = db.execute(
        select(ActivityRecord, CalculatedEmission, Facility, EmissionFactor)
        .join(CalculatedEmission, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .join(Facility, Facility.id == ActivityRecord.facility_id)
        .join(EmissionFactor, EmissionFactor.id == CalculatedEmission.emission_factor_id)
        .where(ActivityRecord.confirmed_by_user.is_(True))
        .order_by(Facility.name, ActivityRecord.period_start)
    ).all()
    pending = db.query(OCRDraft).filter(OCRDraft.status == 'draft').count()
    missing = db.query(ActivityRecord).outerjoin(
        CalculatedEmission, CalculatedEmission.activity_record_id == ActivityRecord.id
    ).filter(ActivityRecord.confirmed_by_user.is_(True), CalculatedEmission.id.is_(None)).count()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title='CarbonTrace Emissions Report',
                            leftMargin=1.6*cm, rightMargin=1.6*cm,
                            topMargin=1.7*cm, bottomMargin=1.7*cm)
    styles = getSampleStyleSheet()
    elements = []

    def paragraph(text, style='BodyText'):
        elements.append(Paragraph(_text(text), styles[style]))

    def section(title):
        elements.append(Spacer(1, 0.35*cm))
        paragraph(title, 'Heading2')

    paragraph('CARBONTRACE', 'Heading3')
    paragraph('Emissions performance report', 'Title')
    paragraph(f'Generated {datetime.now(timezone.utc):%d %b %Y, %H:%M UTC}')
    paragraph('Presentation summary | Confirmed activity records | All available periods')
    section('1. Executive summary')
    if rows:
        start = min(row[0].period_start for row in rows)
        end = max(row[0].period_end for row in rows)
        paragraph(f'Reporting coverage: {start:%d %b %Y} to {end:%d %b %Y}.')
    else:
        paragraph('No confirmed, calculated records are available. Upload and confirm activity data to populate this report.')
    scopes = {scope: sum(c.co2e_kg for _, c, _, _ in rows if c.scope == scope) for scope in (1, 2)}
    total = sum(scopes.values())
    elements.append(_table([
        ['Measure', 'Result'],
        ['Total recorded emissions', f'{total:,.2f} kg CO2e ({total/1000:,.3f} t CO2e)'],
        ['Scope 1: direct fuel emissions', f'{scopes[1]:,.2f} kg CO2e' if any(c.scope == 1 for _, c, _, _ in rows) else 'Not provided'],
        ['Scope 2: purchased electricity', f'{scopes[2]:,.2f} kg CO2e' if any(c.scope == 2 for _, c, _, _ in rows) else 'Not provided'],
        ['Coverage', f'{len(rows)} records across {len({f.id for _, _, f, _ in rows})} facilities'],
    ], [doc.width*0.5, doc.width*0.5]))
    section('2. Facility comparison')
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[2].id].append(row)
    facility_rows = [['Facility', 'Coverage / records', 'Emissions kg CO2e', 'Share']]
    for group in grouped.values():
        amount = sum(c.co2e_kg for _, c, _, _ in group)
        first = min(a.period_start for a, _, _, _ in group)
        last = max(a.period_end for a, _, _, _ in group)
        facility_rows.append([group[0][2].name,
                              f'{first:%b %Y} to {last:%b %Y}; {len(group)} records',
                              f'{amount:,.2f}', f'{amount/total*100:.1f}%' if total else '0.0%'])
    if grouped:
        elements.append(_table(facility_rows, [doc.width*x for x in (.32, .32, .23, .13)]))
    paragraph('Compare coverage before comparing totals. Different reporting periods or record counts do not establish relative efficiency.')
    section('3. Activity and calculation detail')
    detail = [['Facility / period', 'Activity', 'Quantity', 'Factor', 'kg CO2e']]
    for activity, calc, facility, factor in rows:
        detail.append([f'{facility.name}; {activity.period_start:%b %Y}', activity.activity_type,
                       f'{activity.quantity:,.2f} {activity.unit}', f'{factor.factor_value:g}',
                       f'{calc.co2e_kg:,.2f}'])
    if rows:
        elements.append(_table(detail, [doc.width*x for x in (.34, .15, .19, .12, .20)]))
    section('4. Methodology and data quality')
    sources = db.scalars(select(OCRDraft.source_filename).where(
        OCRDraft.activity_record_id.in_([activity.id for activity, _, _, _ in rows]),
        OCRDraft.status == 'confirmed',
    ).distinct()).all()
    if sources:
        paragraph('Source workbooks or uploads: ' + ', '.join(sorted(sources)) + '.')
    paragraph('A scope marked Not provided has no calculated records. Missing data is not a measured zero; total recorded emissions excludes unreported activity.')
    paragraph('Emissions (kg CO2e) = activity quantity x the recorded emission factor. Tonnes CO2e = kg CO2e / 1,000. Totals use stored values before display rounding.')
    factors = {factor.id: factor for _, _, _, factor in rows}
    for factor in factors.values():
        region = factor.region or 'global'
        paragraph(f'{factor.activity_type}: {factor.factor_value:g} {factor.unit}; region {region}; valid from {factor.valid_from:%d %b %Y}.')
    paragraph(f'Excluded from totals: {pending} pending drafts and {missing} confirmed records without calculations. Scope 3 is outside this report.')
    paragraph('Excel imports currently treat saved Mescom Units as kWh. Solar generation and exports are not deducted. Confirm the meter unit basis and approved factors before external reporting; seeded factors are demonstration placeholders.')
    if any(f.name.startswith('Demo Facility ') for _, _, f, _ in rows):
        paragraph("Demonstration dataset: one institute's real meter history is divided into three separately named demo facilities. These partitions do not represent measurements from three independent physical sites.")
    paragraph('Anomaly detection requires at least 20 readings per facility and activity group and an explicit detection run. An absence of flags is not evidence that all readings are normal.')
    paragraph('This document is a project presentation summary, not an independently verified ESG disclosure or a complete BRSR filing.')

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#52635A'))
        canvas.drawString(doc.leftMargin, 0.9*cm, 'CarbonTrace | Emissions summary')
        canvas.drawRightString(A4[0]-doc.rightMargin, 0.9*cm, f'Page {document.page}')
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
