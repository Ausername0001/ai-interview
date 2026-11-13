
# backend/resume_parser.py

from io import BytesIO
from pathlib import Path

import fitz
from docx import Document


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def parse_resume(filename: str, file_bytes: bytes) -> str:
    """
    解析 PDF 或 DOCX 简历，返回文本内容。
    """

    if not file_bytes:
        raise ValueError("上传的简历文件为空")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("简历文件不能超过10MB")

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        text = parse_pdf(file_bytes)

    elif extension == ".docx":
        text = parse_docx(file_bytes)

    else:
        raise ValueError("目前只支持 PDF 和 DOCX 格式")

    text = text.strip()

    if not text:
        raise ValueError(
            "没有从简历中提取到文字，请检查文件是否为扫描版PDF"
        )

    return text


def parse_pdf(file_bytes: bytes) -> str:
    """解析 PDF 文件"""

    result = []

    with fitz.open(
        stream=file_bytes,
        filetype="pdf"
    ) as pdf:

        for page in pdf:
            page_text = page.get_text("text")

            if page_text.strip():
                result.append(page_text)

    return "\n".join(result)


def parse_docx(file_bytes: bytes) -> str:
    """解析 Word 文件"""

    document = Document(BytesIO(file_bytes))

    result = []

    # 提取段落
    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:
            result.append(text)

    # 提取表格
    for table in document.tables:

        for row in table.rows:

            cells = [
                cell.text.strip()
                for cell in row.cells
            ]

            result.append(" | ".join(cells))

    return "\n".join(result)
