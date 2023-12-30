from docx import Document
import json
import argparse

parser = argparse.ArgumentParser(
    description="服务调用方法：python word2list.py --docx_path 'xxx.docx' --output_path 'xxx.json' --max_length 500")
parser.add_argument(
    "--docx_path", type=str, required=True, help="docx 文件地址")
parser.add_argument(
    "--output_path", type=str, required=True, help="结果输出地址")
parser.add_argument(
    "--max_length", default=500, type=int, help="切片大小")
args = parser.parse_args()

docx = Document(docx_path)
max_length = args.max_length

result = []
current_text = ""
num_toolong = 0

for paragraph in docx.paragraphs:
    section = paragraph.text.strip()
    if not current_text or len(current_text) + len(section) <= max_length:
        current_text += section
    else:
        # 否则，将当前文本作为一个段落添加到结果中，并重新开始新的段落
        result.append(current_text)
        if len(current_text) > max_length:
            num_toolong += 1
        current_text = section

output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open(args.output_path, "w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)

print("finish")
