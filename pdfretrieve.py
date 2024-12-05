import json
import os
import re
import requests
import fitz
import nltk
import fitz  # PyMuPDF
from collections import defaultdict
from semanticsearch import SemanticSearch
from textindex import TextIndexer
import concurrent.futures


query_keywords = [
        "Monomer",
        "Salt",
        "Initiator",
        "Molar Ratio",
        "stoichiometry",
        "molecules",
        "reaction ratio",
        "Temperature",
        "Time",
        "method",
        "Experiment method",
        "Mechanism",
        "Conductivity",
        "Ionic",
        "Ionic Conductivity",
        "Transference Number",
        "Electrochemical Window",
        "Critical Current Density",
        "Tensile Strength",
        "Glass transition temperature",
        "Polymer",
        "Polymerization",
        "Activation Energy",
        "Molecular Weight"
    ]

query_statements = [
        "Explore the significance and function of individual monomers during the formation of polymer chains, including the types of monomers and their reactivity in various polymerization processes.",
        "Investigate how varying salt concentrations influence the electrical conductivity of polymer-based electrolytes, considering factors such as ion mobility, ion pairing, and the overall ionic strength of the solution.",
        "Examine the role of initiators in polymerization reactions, detailing how they start the polymerization process, the types of initiators used (thermal, photochemical, etc.), and their impact on polymer growth and properties.",
        "Study the effect of temperature on the rate of polymerization reactions, including the Arrhenius equation, activation energy, and the kinetic parameters that determine how temperature variations influence polymer growth.",
        "Analyze how different reaction times affect the structure and properties of polymers, focusing on molecular weight distribution, degree of polymerization, and any structural changes that occur over time.",
        "Review the experimental techniques used to measure the conductivity of polymers, including methods such as impedance spectroscopy, four-point probe measurements, and other relevant electrochemical techniques.",
        "Delve into the various mechanisms involved in polymerization reactions, such as free radical, ionic, coordination, and step-growth polymerization, discussing the specific steps and intermediates involved in each mechanism.",
        "Discuss the procedures and equipment used to measure ionic conductivity in polymer materials at a specific temperature, covering the principles behind these measurements and the interpretation of the results.",
        "Explain the methods used to determine the transference number of ions in polymer electrolytes, including techniques like electrochemical polarization and potentiostatic methods, and their significance in electrolyte performance.",
        "Highlight the significance of the electrochemical window in the context of battery materials, focusing on how it defines the voltage range for stable operation and its impact on battery efficiency and safety.",
        "Investigate how to determine the critical current density of materials used in batteries and other applications, considering factors like thermal stability, electrochemical reactions, and material composition.",
        "Detail the methods used to measure the tensile strength of polymer materials, including standardized test procedures, equipment used, and the interpretation of stress-strain data.",
        "In this study, the polymerization reaction was conducted under specific conditions to investigate the effects on the resulting polymer properties. The reaction temperature was maintained at 25 °C, and the reaction time was set to 3 hours. The activation energy for the polymerization process was determined to be 10.1 eV. These parameters were chosen based on preliminary experiments to optimize the polymer yield and quality."
        "The synthesized polymers exhibited excellent thermal stability and mechanical strength.",
        "The choice of monomer significantly influenced the polymerization kinetics and the properties of the final polymer.",
        "Adding an ionic salt to the electrolyte solution improved its ionic conductivity.",
        "Benzoyl peroxide was used as the chemical initiator to start the polymerization reaction.",
        "The polymerization was conducted at 60 °C for 4 hours, with an activation energy of 80 kJ/mol.",
        "The proposed mechanism for the polymerization reaction involves a free-radical pathway.",
        "The ionic conductivity of the polymer electrolyte was measured to be 1.2 mS/cm at room temperature.",
        "The polymer had a number-average molecular weight (Mn) of 50,000 g/mol and a weight-average molecular weight (Mw) of 120,000 g/mol.",
        "The transference number of lithium ions in the electrolyte was determined using the steady-state current method.",
        "The polymer electrolyte exhibited an electrochemical stability window from 0 to 4.5 V.",    
        "Critical current density was found to be 1.5 mA/cm², beyond which dendrite formation occurred.",    
        "The tensile strength of the polymer film was measured to be 75 MPa, indicating its suitability for structural applications.",
        "The glass transition temperature (Tg) of the polymer was 150 °C, as determined by differential scanning calorimetry (DSC).",
        "The activation energy for ion transport in the polymer was calculated to be 0.25 eV."
        "Types of monomers in polymerization",
        "Characteristics of polymerization monomers",
        "Ionic salts in electrolyte solutions",
        "Types of salts used in electrolytes",
        "Chemical initiators for polymerization",
        "Initiators in polymer chemistry",
        "Optimal temperature for polymer synthesis",
        "Temperature conditions for polymerization",
        "Polymerization reaction time",
        "Time required for complete polymerization",
        "Experimental methods for polymer synthesis",
        "Electrolyte synthesis methodologies",
        "Polymerization reaction mechanisms",
        "Pathways of polymerization reactions",
        "Measuring ionic conductivity in polymers",
        "Analysis of polymer ionic conductivity",
        "Determining ionic transference numbers",
        "Methods to measure transference numbers in electrolytes",
        "Electrochemical stability of polymer electrolytes",
        "Polymer electrolytes electrochemical window",
        "Measuring critical current density in electrolytes",
        "Determination of critical current density",
        "Evaluating tensile strength of polymers",
        "Tensile strength in polymer materials"
    ]


def get_pdf_text_from_url(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_data = response.content
        doc = fitz.open(stream=pdf_data, filetype='pdf')
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        return text
    except requests.exceptions.RequestException as e:
        print(f"Request failed for URL {pdf_url}: {e}")
    except Exception as e:
        print(f"Error processing PDF from URL {pdf_url}: {e}")
    return None  # Return None if there is an error

def process_pdf(pdf_link):
    text = get_pdf_text_from_url(pdf_link)
    title = pdf_link
    text = remove_footer(text)
    text = remove_ref(text)
    return (title, text)

# 从pdf文件解析
def process_pdf_file(file_path):
    """Process a PDF file to extract its title and text."""
    try:
        # 打开 PDF 文件
        doc = fitz.open(file_path)
        text = ""
        # 提取 PDF 中的每一页文本
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text += page.get_text()
        doc.close()
        # 使用文件名作为标题
        title = file_path.split("/")[-1].replace(".pdf", "")
        return (title, text)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

def remove_footer(text):
    if text is None:
        return ''
    patterns = [
        r'Article\nhttps:\/\/doi\.org\/10\.\d{4}\/[a-z0-9\-]+',  # 匹配DOI链接
        r'https:\/\/doi\.org\/10\.\d{4}\/[a-z0-9\-]+'
        r'www\.nature\.com'
        r'Nature Communications\| *\(\d{4}\) \d{2}:\d{4}',        # 匹配期刊名称和期号
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    return text

def remove_ref(text):
    if text is None:
        return ''
    ref_positions = [m.start() for m in re.finditer(r'\breference', text, re.IGNORECASE)]
    
    for ref_start in ref_positions:
        # 提取参考文献开始后的5000个字符
        snippet = text[ref_start:min(ref_start + 5000, len(text)-1)]

        if all(tag in snippet for tag in ['1.', '2.', '3.']):
            return text[:ref_start]
    
    return text

def process_all_pdfs(pdf_links):
    documents = []
    for pdf_link in pdf_links:
        title, text = process_pdf(pdf_link)
        if text:
            if text=='':
                print(print(f"PDF from URL got None."))
            documents.append((title, text))
            print(f"PDF from URL {pdf_link} has been added.")
        else:
            print(f"Skipping PDF from URL {pdf_link} due to previous error.")
    return documents

def process_all_pdfs_file(pdf_paths):
    """处理PDF文件路径列表，返回文件名和文本的元组列表。"""
    documents = []
    for pdf_path in pdf_paths:
        title, text = process_pdf_file(pdf_path)
        if text:
            if text == '':
                print(f"PDF {pdf_path} got empty content.")
            documents.append((title, text))
            print(f"PDF {pdf_path} has been added.")
        else:
            print(f"Skipping PDF {pdf_path} due to previous error.")
    return documents

def extract_paragraphs(json_file, output_txt):
    with open(json_file, 'r', encoding='utf-8') as f:
        search_results = json.load(f)
    
    with open(output_txt, 'w', encoding='utf-8') as f:
        for result in search_results:
            paragraph = result['Paragraph']
            f.write(paragraph + '\n\n')


def list_files_in_directory(directory_path):
    """
    读取文件夹下所有文件（保持扩展名不变），并返回文件路径列表。
    """
    file_list = []
    try:
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # 获取文件的完整路径
                file_path = os.path.join(root, file)
                file_list.append(file_path)
        return file_list
    except Exception as e:
        print(f"Error reading files in directory {directory_path}: {e}")
        return []

# retrieve from url
def retrieve(pdf_links,keywords = query_keywords,keystatements = query_statements):

    documents = process_all_pdfs(pdf_links)

    # 创建索引
    indexer = TextIndexer("indexdir")
    indexer.create_index(documents)

    # 获取索引的文档
    indexed_documents = indexer.get_documents()

    grouped_documents = defaultdict(list)
    for doc in indexed_documents:
        grouped_documents[doc['title']].append(doc)

    search_results = []
    seen_paragraphs = set()

    # 串行执行查询
    searcher = SemanticSearch()

    for title, documents in grouped_documents.items():
        try:
            searcher.add_documents(documents)
        except ValueError as e:
            print(f"Error processing documents for {title}: {e}")
            continue

        for query_str in keywords:
            result_set0 = searcher.search(query_str, method='bm25')
            for result in result_set0:
                paragraph = result['paragraph']
                if paragraph not in seen_paragraphs:
                    seen_paragraphs.add(paragraph)
                    search_results.append({
                        "Document": result['title'],
                        "Paragraph": paragraph
                    })

        for query_str in keystatements:
            result_set0 = searcher.search(query_str, method='semantic')
            for result in result_set0:
                paragraph = result['paragraph']
                if paragraph not in seen_paragraphs:
                    seen_paragraphs.add(paragraph)
                    search_results.append({
                        "Document": result['title'],
                        "Paragraph": paragraph
                    })
    return search_results

def retrieve_from_documents(pdf_paths,keywords = query_keywords,keystatements = query_statements):

    documents = process_all_pdfs_file(pdf_paths)

    # 创建索引
    indexer = TextIndexer("indexdir")
    indexer.create_index(documents)

    # 获取索引的文档
    indexed_documents = indexer.get_documents()

    grouped_documents = defaultdict(list)
    for doc in indexed_documents:
        grouped_documents[doc['title']].append(doc)

    search_results = []
    seen_paragraphs = set()

    # 串行执行查询
    searcher = SemanticSearch()

    for title, documents in grouped_documents.items():
        try:
            searcher.add_documents(documents)
        except ValueError as e:
            print(f"Error processing documents for {title}: {e}")
            continue

    
        # 使用并行处理
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 对 keywords 并行执行 bm25 搜索
            future_bm25 = [executor.submit(lambda query: searcher.search(query, method='bm25'), query_str) for query_str in keywords]
            
            # 对 keystatements 并行执行语义搜索
            future_semantic = [executor.submit(lambda query: searcher.search(query, method='semantic'), query_str) for query_str in keystatements]
            
            # 获取所有的 bm25 搜索结果
            for future in concurrent.futures.as_completed(future_bm25):
                result_set0 = future.result()
                for result in result_set0:
                    paragraph = result['paragraph']
                    if paragraph not in seen_paragraphs:
                        seen_paragraphs.add(paragraph)
                        search_results.append({
                            "Document": result['title'],
                            "Paragraph": paragraph
                        })
            
            # 获取所有的语义搜索结果
            for future in concurrent.futures.as_completed(future_semantic):
                result_set0 = future.result()
                for result in result_set0:
                    paragraph = result['paragraph']
                    if paragraph not in seen_paragraphs:
                        seen_paragraphs.add(paragraph)
                        search_results.append({
                            "Document": result['title'],
                            "Paragraph": paragraph
                        })

    return search_results