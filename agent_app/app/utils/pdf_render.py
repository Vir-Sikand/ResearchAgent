import base64, fitz
def pdf_to_images_b64(pdf_path: str, dpi: int = 300):
    doc = fitz.open(pdf_path)
    images = []
    zoom = dpi / 72.0
    for i in range(len(doc)):
        pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        images.append("data:image/png;base64," + base64.b64encode(pix.tobytes("png")).decode())
    return images
