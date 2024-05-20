import fitz

pdf_file_path = "D:\kdt_0900_isy\project\oneLabServer\\test\pdf\\test3.pdf"
doc = fitz.open(pdf_file_path)
for i, page in enumerate(doc):
    img = page.get_pixmap()
    img.save(f"./image/{i}.png")
