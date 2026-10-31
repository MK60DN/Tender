from pathlib import Path
from pypdf import PdfReader
import re, shutil, json

root = Path(r'D:\Tender\external_data\curriculum_standards')
hs = root / 'high_school_2017_2020'
out = root / 'normalized'
out.mkdir(exist_ok=True)

files = list(hs.rglob('*.pdf'))
numbered = {}
for p in files:
    m = re.match(r'(\d+)\.', p.name)
    if m:
        numbered.setdefault(int(m.group(1)), p)

hs_subjects = [
    'course_scheme','chinese','math','english','politics','history','geography',
    'physics','chemistry','biology','it','general_technology','arts','music',
    'fine_arts','pe_health','japanese','russian','german','french','spanish'
]
cs_subjects = [
    'course_scheme','morality_law','chinese','history','math','english','japanese',
    'russian','geography','science','physics','chemistry','biology',
    'information_technology','pe_health','art','labor'
]
compulsory = sorted(root.glob('compulsory_2022_*.pdf'))

items = []
for i, subject in enumerate(hs_subjects, 1):
    items.append((f'hs_{i:02d}_{subject}', numbered.get(i)))
for i, subject in enumerate(cs_subjects, 1):
    items.append((f'cs_{i:02d}_{subject}', compulsory[i-1] if i <= len(compulsory) else None))

rows = []
for stem, source in items:
    if not source:
        continue
    dst = out / (stem + '.pdf')
    shutil.copy2(source, dst)
    reader = PdfReader(str(source))
    text = '\n'.join((page.extract_text() or '') for page in reader.pages)
    (out / (stem + '.txt')).write_text(text, encoding='utf-8')
    rows.append({
        'stem': stem,
        'source': str(source),
        'pages': len(reader.pages),
        'chars': len(text),
        'first': (reader.pages[0].extract_text() or '')[:240].replace('\n', ' ')
    })

(out / 'probe.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('files', len(rows))
