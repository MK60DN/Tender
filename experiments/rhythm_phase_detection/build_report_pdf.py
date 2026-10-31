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

ROOT = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
OUT = ROOT / 'docs' / 'research' / 'Tender-Rhythm-Phase-Experiment-v1.0.pdf'
FONT = Path(r'D:\Tender\产品优化报告\fonts\Deng.ttf')
FONT_B = Path(r'D:\Tender\产品优化报告\fonts\Dengb.ttf')
pdfmetrics.registerFont(TTFont('Deng', str(FONT)))
pdfmetrics.registerFont(TTFont('DengB', str(FONT_B)))
data = json.loads((EXP / 'results.json').read_text(encoding='utf-8'))
s = data['summary']
styles = getSampleStyleSheet()
body = ParagraphStyle('body', fontName='Deng', fontSize=9, leading=14, alignment=TA_JUSTIFY, textColor=colors.HexColor('#1e3038'))
small = ParagraphStyle('small', parent=body, fontSize=7.7, leading=11, textColor=colors.HexColor('#60727a'))
h1 = ParagraphStyle('h1', fontName='DengB', fontSize=22, leading=30, textColor=colors.HexColor('#102e3b'), spaceAfter=10)
h2 = ParagraphStyle('h2', fontName='DengB', fontSize=13, leading=19, textColor=colors.HexColor('#16746b'), spaceBefore=8, spaceAfter=5)
center = ParagraphStyle('center', parent=body, alignment=TA_CENTER)

def table(rows, widths, accent='#16746b', font_size=7.2):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Deng'),('FONTSIZE',(0,0),(-1,-1),font_size),('LEADING',(0,0),(-1,-1),9.5),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(accent)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#cbd9dd')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7faf9')]),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    return t

story=[
    Paragraph('Tender 节律相位与周期证据实验报告 V1.0', h1),
    Paragraph('Rhythm Phase and Periodic Evidence — Synthetic Validation', center),
    Spacer(1, 7*mm),
    Paragraph('研究状态：合成检测器验证，不是真人周期诊断、教育效果或临床因果证据。', small),
    Spacer(1, 4*mm),
    Paragraph('研究问题', h2),
    Paragraph('系统能否在不把 7/28 天窗口误当成真实周期的前提下，从学习—创造序列中区分稳定周期、候选周期和无稳定周期，并识别吸收、整合、表达、校准与恢复相位？', body),
    Paragraph('实验设计', h2),
    Paragraph(f"随机种子 {data['seed']}；{data['days']} 天合成序列，周期分析窗口 {data['analysis_days']} 天。周期类别为 {', '.join(str(x) for x in data['true_periods'])} 天，每类 {data['n_per_period']} 条；非周期对照 {data['n_aperiodic']} 条；相位分类每类 {data['n_per_phase']} 条。检测使用每日学习—创造平衡、自相关峰值和置换零分布，并要求相位反转证据。", body),
    Paragraph('主要结果', h2),
]
summary_rows=[['指标','结果'],[
'周期检出率（稳定或候选）',f"{s['periodic_detection_rate']:.3f}"],[
'稳定周期率',f"{s['periodic_stable_rate']:.3f}"],[
'周期误差在容忍范围',f"{s['period_within_tolerance_rate']:.3f}"],[
'平均绝对周期误差',f"{s['period_mae_days']:.2f} 天"],[
'非周期稳定周期误报率',f"{s['aperiodic_stable_false_positive_rate']:.3f}"],[
'非周期候选周期率',f"{s['aperiodic_candidate_rate']:.3f}"],[
'相位分类准确率',f"{s['phase_accuracy']:.3f}"]]
story.append(table(summary_rows,[100*mm,45*mm],'#16746b',8.2))
story.append(Spacer(1,4*mm))
story.append(Paragraph('各类周期', h2))
rows=[['真实周期','检出率','稳定率','容忍范围内','平均绝对误差']]
for row in data['periodic_results']:
    mae='—' if row['mae_days_among_detected'] is None else f"{row['mae_days_among_detected']:.2f}"
    rows.append([f"{row['true_period_days']} 天",f"{row['detected_rate']:.3f}",f"{row['stable_rate']:.3f}",f"{row['within_tolerance_rate']:.3f}",mae])
story.append(table(rows,[31*mm,30*mm,30*mm,35*mm,35*mm],'#61558f',7.8))
story.append(PageBreak())
story.append(Paragraph('相位混淆矩阵', h2))
phases=['absorb','integrate','express','calibrate','recover']
rows=[['期望相位']+phases]
for expected in phases:
    rows.append([expected]+[str(data['phase_confusion'][expected].get(pred,0)) for pred in phases])
story.append(table(rows,[30*mm,24*mm,24*mm,24*mm,24*mm,24*mm],'#b07930',7.5))
story.append(Paragraph('解释', h2))
for text in [
    f"检测器在合成数据中检出 {s['periodic_detection_rate']:.1%} 的周期序列，其中 {s['periodic_stable_rate']:.1%} 达到稳定周期阈值。",
    f"非周期序列的稳定周期误报率为 {s['aperiodic_stable_false_positive_rate']:.1%}，候选周期率为 {s['aperiodic_candidate_rate']:.1%}；候选周期必须保持试探性，不能直接变成日程。",
    f"相位分类在受控合成场景中的准确率为 {s['phase_accuracy']:.1%}；恢复相位仍只能表示‘恢复或低活动’，不能推断休息、放弃或诊断。",
    '7/28 天窗口只承担短期观察和阶段控制。真实周期从 84 天事件序列中估计，并必须与随机波动基线比较。',
]:
    story.append(Paragraph('• '+text,body))
story.append(Paragraph('边界与下一步', h2))
story.append(Paragraph(data['boundary'],body))
story.append(Paragraph('下一步需要在获得授权、可撤回的真实纵向数据中预注册验证，并同时保留三类对照：无稳定周期假设、固定 7 天假设、开放周期搜索。产品界面不得把候选周期写成确定节律，也不得用周期解释人格、能力或临床状态。',body))
OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=15*mm,bottomMargin=14*mm,title='Tender Rhythm Phase Experiment V1.0',author='Tender Research Group')
doc.build(story)
(ROOT/'docs'/'research'/'Tender-Rhythm-Phase-Experiment-v1.0.md').write_text((EXP/'REPORT.md').read_text(encoding='utf-8'),encoding='utf-8')
print(OUT)
