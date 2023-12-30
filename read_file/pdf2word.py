from pdf2docx import Converter
import argparse

parser = argparse.ArgumentParser(
    description="服务调用方法：python pdf2word.py --pdf_path 'xxx.pdf' --docx_path 'xxx.docx'")
parser.add_argument(
    "--pdf_path", type=str, required=True, help="要解析的 pdf 文件地址")
parser.add_argument(
    "--docx_path", type=str, required=True, help="解析后的 docx 文件输出地址")
args = parser.parse_args()

docx_dir = os.path.dirname(docx_path)
if not os.path.exists(docx_dir):
    os.makedirs(docx_dir)

# convert pdf to docx
cv = Converter(args.pdf_path)
cv.convert(args.docx_path)  # all pages by default
cv.close()
