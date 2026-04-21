# ============================================================================
# 脚本作用：遍历指定文件夹中的所有 Excel 文件，提取所有单元格文本内容，
#          去重后保存为 docs.txt，供 Vanna 训练使用。
# 使用方法：python extract_excel_to_txt.py
# ============================================================================
import os
import pandas as pd
from pathlib import Path

# 配置：存放 Excel 文件的文件夹路径（可修改）
EXCEL_FOLDER = "/workspaces/telecompass/backend/training_data/excel_files"
OUTPUT_FILE = "/workspaces/telecompass/backend/training_data/docs.txt"

def extract_text_from_excel(file_path):
    """从单个 Excel 文件中提取所有单元格文本（去重）"""
    texts = set()
    try:
        # 读取所有 sheet
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, dtype=str)
            # 遍历每个单元格，过滤空值和 NaN
            for col in df.columns:
                for cell in df[col]:
                    if pd.notna(cell) and str(cell).strip():
                        texts.add(str(cell).strip())
    except Exception as e:
        print(f"读取文件 {file_path} 出错: {e}")
    return texts

def main():
    excel_dir = Path(EXCEL_FOLDER)
    if not excel_dir.exists():
        print(f"错误：文件夹 {EXCEL_FOLDER} 不存在，请先创建并放入 Excel 文件。")
        return
    
    all_texts = set()
    # 遍历所有 Excel 文件（支持 .xlsx, .xls）
    for excel_file in excel_dir.glob("*.[xls][sx]*"):
        print(f"正在处理: {excel_file.name}")
        texts = extract_text_from_excel(excel_file)
        all_texts.update(texts)
        print(f"  提取到 {len(texts)} 条文本")
    
    if not all_texts:
        print("未提取到任何文本，请检查 Excel 文件内容。")
        return
    
    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for text in sorted(all_texts):
            f.write(text + "\n")
    
    print(f"✅ 完成！共提取 {len(all_texts)} 条文本，已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()