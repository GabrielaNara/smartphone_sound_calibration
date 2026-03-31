import pandas as pd
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

path_ = os.getcwd() 
path_ = path_.split("\\src")[0]

############################################################################################
#############################              INPUT            ################################
############################################################################################

# CHOOSE INPUT
location = 'p2' 
sensor_number = 'sensorB-m10' #in the example: "sensorB-m10" for p2, "sensorA-m2" or "sensorA-m4" for p1
device_model_reference = "reference iphone15" #ADD THE model of reference device, 
                                                    #in this example: "Class1 SLM1" and "reference iphone15"

# DEFAULT PARAMETERS
descriptor = "LAeq" #CHOOSE BETWEEN "1Khz" or "Laeq"
dataset = "/dataset" # Folder with the measurements file
df_TABLE =  pd.read_excel(path_ + "/input.xlsx",sheet_name="mobile_sensors") # PRE-CALIBRATION VALUES AND DEVICE MODEL  

############################################################################################
######################                  PROCESSING              ############################
############################################################################################

df = pd.read_excel(path_ +f"/outputs/frequency_domain_by_sensor/frequency_{sensor_number}_.xlsx") 

# adding device_model information
df['device_model'] = df['device'].map(
    df_TABLE.set_index('device')['device_model'])
df.insert(1, 'device_model', df.pop('device_model'))
df.loc[df['device'] == sensor_number, 'device_model'] = device_model_reference

#applying bias
df['sensor - ref'] = df['LAeq(1s)'] - df.loc[df['device'] == sensor_number, 'LAeq(1s)'].iloc[0]

def generate_report(df, sensor_number, path_):

    row = df[df['device'] == sensor_number].iloc[0]

    figA = os.path.join(path_, "outputs", "frequency_domain_by_sensor",f"frequency_{sensor_number}.png")
    figB = os.path.join(path_, "outputs", "time_series_by_sensor",f"time_serie_{sensor_number}_{row['measurement']}.png")
    

    # =========================
    # DOCUMENT
    # =========================
    doc = SimpleDocTemplate(
        os.path.join(path_, f"outputs/report_{sensor_number}.pdf"),
        pagesize=A4,
        leftMargin=60,
        rightMargin=60,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # =========================
    # Estyles
    # =========================
    title_style = ParagraphStyle(
        'title',
        parent=styles['Title'],
        alignment=0,
        fontSize=16,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'subtitle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=6
    )
    
    section_style = ParagraphStyle(
        'section',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=6,
        spaceAfter=4
    )

    elements = []

    # =========================
    # HEADER
    # =========================
    elements.append(Paragraph("<b>MEASUREMENT REPORT</b>", title_style))
    elements.append(Paragraph("by @gabrielanara", subtitle_style))

    # =========================
    # GENERAL INFO
    # =========================
    info_data = [
        [
            Paragraph(f"<b>Fix_Sensor:</b> {row['device']}", styles['Normal']),
            "","" 
        ],
        [    
            Paragraph(f"<b>Location:</b> {row['measurement']}", styles['Normal']),
            Paragraph(f"<b>Date:</b> {str(row['Date']).split(' ')[0]}", styles['Normal']),
        ],
        [
            Paragraph(f"<b>Lat,Long:</b> {row['x']:.6f}, {row['y']:.6f}", styles['Normal']),
            Paragraph(f"<b>Duration:</b> {row['duracao']} s", styles['Normal']),
            Paragraph(f"<b>Start:</b> {row['Time']}", styles['Normal']),
        ]
    ]
    
    info_table = Table(info_data, colWidths=[180, 130, 130])

    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # =========================
    # DATA SUMMARY
    # =========================
    elements.append(Paragraph("<b>Data Summary</b>", section_style))

    cols = ['device', 'device_model','duracao',  'Time', 'LAeq(1s)','leq_1000', 'sensor - ref']
    table_data = [cols]

    for _, r in df.iterrows():
        table_data.append([
            r['device'],
            r['device_model'],
            r['duracao'],
            r['Time'],
            f"{float(r['LAeq(1s)']):.2f}" if pd.notnull(r['LAeq(1s)']) else "",
            f"{float(r['leq_1000']):.2f}" if pd.notnull(r['leq_1000']) else "",
            f"{float(r['sensor - ref']):.2f}" if pd.notnull(r['sensor - ref']) else ""
        ])

    table_all = Table(table_data, colWidths=[70,100, 40, 50, 50, 50,70])
   
    table_all.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    elements.append(table_all)
    elements.append(Spacer(1, 12))

    # =========================
    # FIG A
    # =========================
    elements.append(Paragraph("<b>Frequency domain</b>", section_style))
    if os.path.exists(figA):
        elements.append(Image(figA, width=440, height=220))

    elements.append(Spacer(1, 2))

    # =========================
    # FIG B
    # =========================
    elements.append(Paragraph(f"<b>Time series -- sensor {sensor_number} -- location {location}</b>", section_style))
    if os.path.exists(figB):
        elements.append(Image(figB, width=440, height=220))

    # =========================
    # BUILD
    # =========================
    doc.build(elements)
    
generate_report(df, sensor_number=sensor_number, path_=path_)    