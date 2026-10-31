from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(r'D:\Tender\Tender-GitHub-Release')
EXP = ROOT / 'experiments' / 'golden_bias_regulation'
OUT = ROOT / 'docs' / 'research' / 'Tender-Golden-Bias-Experiment-v1.0.pdf'
FONT = Path(r'D:\Tender\产品优化报告\fonts\Deng.ttf')
FONT_B = Path(r'D:\Tender\产品优化报告\fonts\Dengb.ttf')
pdfmetrics.registerFont(TTFont('Deng', str(FONT)))
pdfmetrics.registerFont(TTFont('DengB', str(FONT_B)))

data = json.loads((EXP / 'results.json').read_text(encoding='utf-8'))
styles = getSampleStyleSheet()
body = ParagraphStyle('body', fontName='Deng', fontSize=9.5, leading=15, alignment=TA_JUSTIFY, textColor=colors.HexColor('#1e3038'))
h1 = ParagraphStyle('h1', fontName='DengB', fontSize=24, leading=32, textColor=colors.HexColor('#102e3b'), spaceAfter=12)
h2 = ParagraphStyle('h2', fontName='DengB', fontSize=14, leading=21, textColor=colors.HexColor('#16746b'), spaceBefore=10, spaceAfter=6)
small = ParagraphStyle('small', fontName='Deng', fontSize=8.2, leading=12, textColor=colors.HexColor('#60727a'))
center = ParagraphStyle('center', parent=body, alignment=TA_CENTER)
story = [Paragraph('Tender 动态黄金比偏置律实验报告 V1.0', h1), Paragraph('Dynamic Golden-Bias Regulation — Synthetic Multi-Arm Experiment', center), Spacer(1, 8*mm), Paragraph('研究状态：合成机制实验，不是真人教育或临床因果研究。', small), Spacer(1, 5*mm)]
story.append(Paragraph('研究问题', h2))
story.append(Paragraph('在不将黄金比变成每日 KPI 的前提下，带滞回和阶段目标的动态偏置带，能否比不调节、固定 50:50 或固定阈值更好地平衡学习、创造、校准和用户负担？', body))
story.append(Paragraph('实验设计', h2))
for line in [
    f"种子：{data['seed']}；每个实验臂 {data['n_per_arm']} 名合成学习者；{data['days']} 天。",
    '四个实验臂：不调节、固定 50:50、固定 38.2/61.8 阈值、动态黄金比偏置带。',
    '主要指标：行动恢复、创造后校准、处于弹性带内的时间比例。',
    '次要指标：知识、分支、新异可持续性、提示负担、疲劳。',
    '配对 bootstrap 用于估计动态规则相对其他实验臂的差异置信区间。',
]:
    story.append(Paragraph('• ' + line, body))
story.append(Paragraph('主要结果', h2))
metrics = ['action_recovery','knowledge','novelty_sustain','post_creation_calibration','band_inside','burden','fatigue']
headers = ['实验臂','恢复','知识','新异','创造后校准','在带内','提示负担','疲劳']
rows = [headers]
for arm in data['arms']:
    s = data['summaries'][arm]
    rows.append([arm] + [f"{s[m]['mean']:.3f}" if m not in {'burden'} else f"{s[m]['mean']:.1f}" for m in metrics])
table = Table(rows, colWidths=[32*mm,18*mm,18*mm,18*mm,22*mm,18*mm,20*mm,18*mm], repeatRows=1)
table.setStyle(TableStyle([
    ('FONTNAME',(0,0),(-1,-1),'Deng'),('FONTSIZE',(0,0),(-1,-1),7.2),('LEADING',(0,0),(-1,-1),10),
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16746b')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd9dd')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f7faf9')]),
]))
story.append(table)
story.append(Paragraph('配对差异与假设检验', h2))
rows2 = [['对照','指标','平均差异','95% CI','CI 排除 0']]
for control in ['no_regulation','fixed_50','fixed_band']:
    for metric in metrics:
        item = data['pairwise_vs_dynamic_golden'][control][metric]
        rows2.append([control, metric, f"{item['mean_difference']:.3f}", f"[{item['ci95'][0]:.3f}, {item['ci95'][1]:.3f}]", '是' if item['synthetic_significant_95'] else '否'])
table2 = Table(rows2, colWidths=[30*mm,46*mm,23*mm,35*mm,20*mm], repeatRows=1)
table2.setStyle(TableStyle([
    ('FONTNAME',(0,0),(-1,-1),'Deng'),('FONTSIZE',(0,0),(-1,-1),7.1),('LEADING',(0,0),(-1,-1),9.5),
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#61558f')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#d7dadd')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f5f4f8')]),
]))
story.append(table2)
story.append(Paragraph('结论', h2))
for line in [
    'H1 得到支持：动态黄金比相对不调节提高了处于弹性带内的时间。',
    'H2 部分得到支持：动态规则比固定 50:50 少约一半提示，并保持相近行动恢复。',
    'H3 未得到支持：动态规则的校准略低于固定阈值，新异没有显著优势；不能声称全面优于简单规则。',
    '因此应把动态黄金比定位为“负担感知的偏置带”，而不是新的每日绩效指标。',
]:
    story.append(Paragraph('• ' + line, body))
story.append(Paragraph('研究边界与下一步', h2))
story.append(Paragraph(data['boundary'], body))
story.append(Paragraph('下一步应进行预注册真人研究，比较动态偏置带、固定 50:50 和简单阈值；主要终点应包含行动恢复、创造后校准、在带时间、用户负担和退出率。任何结论都必须保留不确定性和反证空间。', body))
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=15*mm, title='Tender Golden-Bias Experiment V1.0')
doc.build(story)
(ROOT / 'docs' / 'research' / 'Tender-Golden-Bias-Experiment-v1.0.md').write_text((EXP / 'REPORT.md').read_text(encoding='utf-8'), encoding='utf-8')
print(OUT)