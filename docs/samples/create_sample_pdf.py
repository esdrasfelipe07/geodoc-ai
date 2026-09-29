from pathlib import Path


def generate_sample_pdf(output_path: Path):
    """
    Generates a valid, readable PDF file containing sample geophysical survey text.
    """
    text_content = (
        "RELATORIO TECNICO DE GEOFISICA - BACIA DE SANTOS\\n"
        "Campo de Exploracao: Bloco BS-500 | Poco: 1-GEO-01-SPS\\n"
        "Data: 15/08/2026 | Equipe de Sismica e Geologia\\n\\n"
        "1. RESUMO EXECUTIVO\\n"
        "O presente levantamento sismico 3D teve como objetivo identificar anomalias de amplitude e "
        "mapear os horizontes refletores na secao pos-sal e carbonatos do pre-sal.\\n\\n"
        "2. DADOS ESTRATIGRAFICOS E VELOCIDADES INTERVALARES\\n"
        "- Formacao Superior (0 - 2100m): Folhelhos e arenitos turbiditicos. Velocidade sismica: 2200 a 2800 m/s.\\n"
        "- Camada de Sal (2100m - 4800m): Evaporitos espessos (halita e anidrita). Velocidade sismica: 4500 m/s.\\n"
        "- Reservatorio Carbonatico (4800m - 5300m): Rocha-reservatorio microbial. Porosidade media de 19%, "
        "com alta saturacao de hidrocarbonetos (oleo leve de 29 graus API).\\n\\n"
        "3. CONCLUSAO E RECOMENDACOES\\n"
        "Os dados sismicos de reflexao e os perfis de pocos confirmam o fechamento estrutural e o alto "
        "potencial prospectivo da area investigada."
    )

    # PDF binary stream structure
    stream_data = f"BT /F1 11 Tf 50 720 Td 14 TL ({text_content}) Tj ET".encode("latin1")
    stream_len = len(stream_data)

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    offsets = []

    def add_object(obj_num: int, content: bytes):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_num} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    # Obj 1: Catalog
    add_object(1, b"<</Type/Catalog/Pages 2 0 R>>")
    # Obj 2: Pages
    add_object(2, b"<</Type/Pages/Count 1/Kids[3 0 R]>>")
    # Obj 3: Page
    add_object(3, b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>")
    # Obj 4: Contents
    add_object(4, f"<</Length {stream_len}>>\nstream\n".encode("ascii") + stream_data + b"\nendstream")
    # Obj 5: Font
    add_object(5, b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<</Size {len(offsets) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf)


if __name__ == "__main__":
    out = Path("/home/esdrasfelipe/ProjetoIA/docs/samples/relatorio_geofisico_exemplo.pdf")
    generate_sample_pdf(out)
    print(f"Sample PDF written to {out}")
