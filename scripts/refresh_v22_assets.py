from pathlib import Path
import hashlib, json, shutil
root=Path(r"D:\Tender\Tender-GitHub-Release")
for rel in ["docs/whitepaper/Tender-Whitepaper-v2.2.pdf","docs/product/Tender-Product-Manual-v7.2.pdf","docs/product/Tender-User-Guide-v7.2.pdf","docs/teaching/Tender-Teaching-Manual-v6.2.pdf"]:
    src=root/rel; shutil.copy2(src, root/"site/assets/docs"/src.name)
p=root/"docs/product/VERSION.json"; data=json.loads(p.read_text(encoding="utf-8")); product=root/"docs/product/Tender-Product-Manual-v7.2.pdf"; user=root/"docs/product/Tender-User-Guide-v7.2.pdf"; white=root/"docs/whitepaper/Tender-Whitepaper-v2.2.pdf"; teach=root/"docs/teaching/Tender-Teaching-Manual-v6.2.pdf"
data["pdf_bytes"]=product.stat().st_size; data["sha256"]=hashlib.sha256(product.read_bytes()).hexdigest()
data["user_guide"]["pdf_bytes"]=user.stat().st_size; data["user_guide"]["sha256"]=hashlib.sha256(user.read_bytes()).hexdigest()
data["project_whitepaper"]["pdf_bytes"]=white.stat().st_size; data["project_whitepaper"]["pdf_sha256"]=hashlib.sha256(white.read_bytes()).hexdigest()
data["teaching_manual"]["pdf_bytes"]=teach.stat().st_size; data["teaching_manual"]["sha256"]=hashlib.sha256(teach.read_bytes()).hexdigest()
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("assets and hashes refreshed")
