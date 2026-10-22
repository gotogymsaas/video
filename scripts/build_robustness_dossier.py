"""Audit front matter and bookmarked collection of the eight preprints."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader,PdfWriter
from scripts.build_robustness_papers import PAPERS,ROOT,DEST

def build():
 r=json.loads((ROOT/'docs/validation/robustness-v0.4.json').read_text());font=ROOT/'qaf_video/assets/fonts'
 pdfmetrics.registerFont(TTFont('Studio',str(font/'DejaVuSans.ttf')));pdfmetrics.registerFont(TTFont('StudioBold',str(font/'DejaVuSans-Bold.ttf')))
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyStudio',fontName='Studio',fontSize=10,leading=15,spaceAfter=8,textColor=colors.HexColor('#24313A')));styles.add(ParagraphStyle(name='TitleStudio',fontName='StudioBold',fontSize=30,leading=36,spaceAfter=20,textColor=colors.HexColor('#17375C')));styles.add(ParagraphStyle(name='HeadStudio',fontName='StudioBold',fontSize=16,leading=21,spaceAfter=14,textColor=colors.HexColor('#17375C')));styles.add(ParagraphStyle(name='TinyStudio',fontName='Studio',fontSize=8.5,leading=12,spaceAfter=5));styles.add(ParagraphStyle(name='TableStudio',fontName='Studio',fontSize=9,leading=13,spaceAfter=2))
 def para(text,style='BodyStudio'):return Paragraph(text,styles[style])
 def footer(canvas,doc):
  canvas.setStrokeColor(colors.HexColor('#0F8F86'));canvas.line(48,793,547,793);canvas.setFont('Studio',8);canvas.setFillColor(colors.HexColor('#53616C'));canvas.drawString(48,805,'GOTOGYM QUANTUM RESEARCH / ROBUSTECIMIENTO AUDIOVISUAL');canvas.drawString(48,31,'22 de octubre de 2026 / Propuestas metodológicas e implementación');canvas.drawRightString(547,31,str(doc.page))
 front=DEST/'Auditoria_Resumen_v04.pdf';doc=SimpleDocTemplate(str(front),pagesize=(595.276,841.89),rightMargin=48,leftMargin=48,topMargin=69,bottomMargin=53)
 story=[Spacer(1,20),para('Del diagnóstico<br/>a una plataforma<br/>reproducible.','TitleStudio'),para('Sistema audiovisual GoToGym Quantum Coach · versión 0.4','HeadStudio'),para('Juan Manuel Goenaga Castro<br/>22 de octubre de 2026'),Spacer(1,15)]
 metrics=[['8 propuestas','8 implementaciones'],[str(r['tests']['count'])+' pruebas aprobadas','2 formatos · 60 segundos']]
 table=Table([[para(c,'HeadStudio') for c in row] for row in metrics],colWidths=[249,249]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#EDF3F1')),('BOX',(0,0),(-1,-1),.6,colors.HexColor('#D1E1DD')),('LEFTPADDING',(0,0),(-1,-1),15),('TOPPADDING',(0,0),(-1,-1),17),('BOTTOMPADDING',(0,0),(-1,-1),10)]));story+=[table,Spacer(1,20)]
 v=r['voice'];audio=r['renders'][0]['audio_encoded']
 story+=[para(f"La narración principal aumenta su velocidad un <b>{v['speed_increase_percent']:.2f} %</b> respecto al primer montaje. Las once pausas insertadas pasan a <b>cero</b>. La pantalla original aparece completa dentro de un teléfono; el logo y los textos no se regeneran."),para(f"Las dos exportaciones tienen 1.800 cuadros a 30 fps. El AAC final mide <b>{audio['input_i']} LUFS</b> y <b>{audio['input_tp']} dBTP</b>. El proyecto y sus pruebas separan consistencia técnica de aprobación editorial."),para('Los artículos incluyen diagnóstico, modelo matemático QAF, código, controles, resultados acotados y protocolo de evaluación. Son prepublicaciones sin revisión por pares; no se reporta un estudio con participantes.'),para('Para abrir el estudio: descomprime la plataforma, instala Python 3.11+ y FFmpeg y ejecuta <b>python iniciar_estudio.py</b>. La instalación de modelos para generar guiones nuevos se documenta por separado.','TinyStudio'),PageBreak(),para('Ocho debilidades, ocho respuestas','TitleStudio')]
 summaries=[('Ritmo de voz','Lentitud, once descansos añadidos y obligación de llenar un minuto.','Voz continua y selección acotada de velocidad.'),('Pronunciación y subtítulos','Errores por idioma ocultables, cifras equivalentes y grupos huérfanos.','Control por frase, glosario de revisión, anclas reales y CPS.'),('Secuencia y sincronía','Manifiesto separado del montaje que se ejecutaba.','Una secuencia canónica y dependencias verificadas.'),('Fidelidad de pantalla','Teléfono vacío y riesgo de regenerar texto o recortar interfaz.','Captura completa, hash, homografía e inversa.'),('Composición y marca','Tarjetas pequeñas, texto fuera de ancho y encuadre por formato.','Tipografía mayor, tarjetas apiladas, cajas y salida SDR explícitas.'),('Mezcla sonora','Ganancias fijas y pasos sin movimiento observado.','Selección por stems, ducking y medida posterior al códec.'),('Evidencia y propiedad intelectual','Capacidades futuras confundibles con funciones probadas.','Fuentes y alcance por plano, atribución y separación de datos privados.'),('Operación y entrega','Scripts externos, doble encode y caché incompleta.','Motor integrado, salida atómica, caché por hash y lanzadores.')]
 rows=[]
 for p,(title,problem,fix) in zip(PAPERS,summaries):rows.append([para(p['id'],'TableStudio'),para('<b>'+title+'</b><br/>'+problem+'<br/><font color="#0F8F86">'+fix+'</font>','TableStudio')])
 table=Table(rows,colWidths=[44,454]);table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#D1E1DD')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story+=[table,Spacer(1,16),para('Alcance de finalización','HeadStudio'),para('Las ocho propuestas computacionales están implementadas. La película es un <b>animatic fotográfico</b> con cámara y gráficos animados. La naturalidad, el acento, la preferencia artística y la eficacia comercial conservan evaluación humana independiente. No se fabrican firmas de aprobación.'),para('QAF usa la región clásica identificable: estado diagonal normalizado, restricciones nativas y QUBO inspeccionable. Se conserva el comparador clásico, sin reclamar ventaja cuántica. Los antecedentes de Antoni Bancells y los modelos de terceros conservan atribución.','TinyStudio')]
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 writer=PdfWriter();writer.append(str(front),outline_item='Auditoría y resultados')
 for p in PAPERS:writer.append(str(DEST/'papers'/(p['id']+'_'+p['slug']+'.pdf')),outline_item=p['id']+' · '+p['title'])
 writer.add_metadata({'/Title':'Robustecimiento audiovisual QAF - ocho propuestas implementadas','/Author':'Juan Manuel Goenaga Castro','/Subject':'Auditoría, modelos matemáticos, código y validación acotada'})
 output=DEST/'Dossier_Cientifico_QAF_Audiovisual_v04.pdf'
 with output.open('wb') as f:writer.write(f)
 print(output);print('pages',len(PdfReader(output).pages));return output
if __name__=='__main__':build()
