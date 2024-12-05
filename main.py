import os
import re
import json
from datetime import datetime
from collections import defaultdict
from time import sleep,time
from pdfretrieve import list_files_in_directory, retrieve,retrieve_from_documents
from modelchat import ChatGPTChemicalAssistant

# openai
api_key = "your_api_key"
model = "your_model"

assistant = ChatGPTChemicalAssistant(api_key,model)

# 从JSON文件中提取PDF链接
def extract_pdf_links(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return list(set(item['pdf_link'] for item in data))

# 分批处理链接
def batch_process_links(pdf_links, batch_size=10):
    for i in range(0, len(pdf_links), batch_size):
        yield pdf_links[i:i + batch_size]

# 合并检索结果
def merge_documents(input_data):
    # 合并检索结果，将同一篇文献检索到的内容放在一起

    # 使用 defaultdict 来合并相同 Document 的内容
    merged_data = defaultdict(list)
    for entry in input_data:
        document = entry['Document']
        paragraph = entry['Paragraph'].replace('\n', ' ').strip()
        merged_data[document].append(paragraph)

    # 将合并的数据转换为所需格式，并去掉段落中的空格和换行符
    result = [{'Document': doc, 'Paragraphs': ' '.join(paras)} for doc, paras in merged_data.items()]

    # 将结果写入新的JSON文件
    # with open(output_file, 'w', encoding='utf-8') as f:
    #    json.dump(result, f, ensure_ascii=False, indent=4)

    return result


def find_documents(input_data, target_document):

    # 使用 defaultdict 来合并相同 Document 的内容
    merged_data = defaultdict(list)
    for entry in input_data:
        document = entry['Document']
        paragraph = entry['Paragraph'].replace('\n', ' ').strip()
        merged_data[document].append(paragraph)

    # 查找特定 Document 的段落
    if target_document in merged_data:
        result = ' '.join(merged_data[target_document])
    else:
        result = f"Document '{target_document}' not found."

    return result


def save_to_json_file(title, json_str, file_path='output_0905.json'):
    try:
        # 将JSON字符串解析为Python对象
        new_data = json.loads(json_str)
        
        # 如果文件存在，则读取文件中的内容
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
        
        # 如果键已经存在于文件中，则将新数据追加到现有数据中
        if title in existing_data:
            existing_data[title].extend(new_data)
        else:
            existing_data[title] = new_data
        
        # 将合并后的数据写回到JSON文件中
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        print(f"数据已成功写入或更新到JSON文件 '{file_path}'")
    except Exception as e:
        print(f"保存{title}结果时发生错误：{e}")
        print("生成的json数据内容如下：")
        print(json_str)

def save_pdf_batch_to_txt(pdf_batch, output_file='processed_data.txt'):
    """
    将处理过的pdf_batch内容存入一个txt文件，记录处理过的文件  
    :param pdf_batch: 需要保存的PDF文件路径列表
    :param output_file: 输出的txt文件路径
    """
    try:
        with open(output_file, 'a', encoding='utf-8') as file:
            for pdf_path in pdf_batch:
                file.write(pdf_path + '\n')  # 每个文件路径写入一行
        print(f"PDF batch successfully saved to {output_file}")
    except Exception as e:
        print(f"Error writing to file {output_file}: {e}")


# 对话LLM获取第一轮的对话结果
def generate_initial_json(relevant_text):
    prompt = """I will provide a text. Please read it carefully and extract all the information related to the specified keywords. Ensure that you identify and include **all relevant details from the entire TEXT**, especially focusing on the conditions, values, and numbers. **Complete extraction and thoroughness are crucial.** Pay attention to all parts of the document to avoid missing any relevant information.

Keywords list:
1. Polymer: "Polymers are large molecules composed of repeating structural units called monomers, covalently bonded together"
2. Monomer: "Polymerization monomer is a molecule that forms polymers"
3. Salt: "Ionic salt used in electrolyte solutions"
4. Initiator: "Chemical or physical initiators for polymerization reactions"
5. Polymerization:"Polymerization parameters include temperature, time, and activation energy."
6. Experiment Method: "Detailed Experimental methodologies for polymer and electrolyte synthesis,usually contains reactants,step-by-step operations,conditons and results,etc"
7. Mechanism: "A polymerization mechanism is the detailed step-by-step process through which monomers chemically react to form a polymer."
8. Conductivity: "Measurement and analysis of ionic conductivity in polymers.There are multiple values at different conditions;ensure to extract all of them."
9. Molecular Weight: The sum of the atomic weights of all atoms of the Polymer. It is typically measured in atomic mass units (amu) or Daltons (Da), where 1 amu is defined as one-twelfth the mass of a carbon-12 atom.
10. Transference Number: "Methods to determine ionic transference numbers in electrolytes"
11. Electrochemical Window: "Electrochemical stability window of polymer electrolytes"
12. Critical Current Density: "Determination of critical current density in electrolytes"
13. Tensile Strength: "Evaluation of tensile strength in polymer materials"
14. Glass Transition Temperature (Tg): "The temperature at which a polymer changes from a hard and glassy state to a soft and rubbery state, affecting the polymer's mechanical properties and ion transport"

Please ensure to comprehensively extract all information related to each keyword. **All of them are important, so you can't miss one.** Your JSON should include all details aside by the EXAMPLE, especially those regarding different conditions, values.

Now you know what these keywords' basic meanings and their difference, based on the provided text, ensure you have extracted all information from the entire document and carefully generate the JSON format data.

Ensure that the content is original to the TEXT and DOES NOT COPY the provided Example JSON content.
**Only generate the key showed in the JSON example.** 
If the key is a list type, it means there could be multiple values, so ensure to extract ALL of them. If the key is a single dictionary, it means there should be only one value, so provide the most relevant one.
If you find there is no relevant data after carefully reading the text and you cant infer its value,you must output "N/A" for the key in the JSON example data,dont delete the key from the JSON data.


TEXT:
{relevant_text}


Example JSON structure:
```json
[
  {{
     "Polymer": 
      {{
        "Name": "Poly[bis-(methoxytriethoxy) phosphazene] (PPZ)",
        "Concentration": {{
            "Value": ,
            "Unit": "M"//or "wt%","Molar ratios (O)" or other units
          }},
        "Molecular_weight":{{
            "Value": ,
            "Unit":"kDa"
          }},
        "Component":{{
                        "Composition": "PVHF, SN, Zn(OTF)2",
                        "Weight_Ratio": "90:5:5",
                        "Molar_Ratio":"53.9:1.5:1"
                    }}
      }},
    "Monomers": [
      {{
          "Name": "bis-(methoxytriethoxy) phosphazene",
          "SMILE": "CO-P(OCCOCCOCCOC)(OCCOCCOCCOC)-N",//conclude by your self
          "CAS": "19915-75-2"
      }},
      {{...
      }}
    ],
    "Salts": [
      {{
        "Name": "Zinc trifluoromethanesulfonate (Zn(OTF)2)",
        "SMILES": "C(F)(F)(F)S(=O)(=O)[O-].[Zn+2].[O-]S(=O)(=O)C(F)(F)F",
        "CAS": "54010-75-2"
      }},
      {{...
      }}
    ],
    "Initiators": [
      {{
        "Name": "2,2'-Azobis(2-methylpropionitrile) (AIBN)",
        "Description":"Description of Initiators",
        "SMILES": "CC(C)(C#N)N=NC(C)(C)C#N",
        "CAS": "78-67-1",
        "Concentration": {{
            "Value": ,
            "Unit": "M"
          }}
      }}
    ],
    "Polymerization": [
    {{
      "Temperature":
      {{
        "Value": 25,
        "Unit": "°C"
      }},
      "Time":
      {{
        "Value": 3,
        "Unit": "h"
      }},
      "Activation_energy":
            {{
            "Descricption":"Descricption of which reaction's 'Activation_energy'"
            "Value": "Activation_Energy.Value",
            "Unit":"eV"
          }}
    }}
    ],
    "Experiment_Methods": "Poly bis-(methoxytriethoxy) phosphazene (PPZ) was prepared via a phosphonitrilic chloride trimer (HCCP) melt bulk polymerization process. HCCP was sealed into a vacuum glass tube and heat it at 260 °C for 36 h to ...(just for example and please elaborate carefully all the details about 'Experiment_Methods' here)",
    "Mechanism": "Specific reaction mechanism",
    "Conductivity":[
      {{
        "Ion": "Ion_Name",
        "Value": 0.001,
         "Unit": "S cm−1",
        "Temperature":{{
            "Value": "Temperature.Value",
            "Unit": "°C"
          }}
      }},
      {{//...other Temperature or other Ion,list all multiple values.
        "Ion": "Ion_Name",
        "Value": "N/A",
         "Unit": "N/A",
        "Temperature":{{
            "Value": ,
            "Unit": "°C"
          }}
      }},
      {{//more value about "Conductivity"
        ...//same as above
      }}
    ]
    ,
    "Transference_Number": {{
            "Value": ,
            "Unit":"N/A",
            "Temperature":
            {{
            "Value": 0.1,
            "Unit":"°C"
            }}
          }},
    "Electrochemical_Window": {{
            "Value": ,
            "Unit":"V",
            "Temperature":
            {{
            "Value": 0.1,
            "Unit":"°C"
            }}
          }},
    "Critical_Current_Density": {{
            "Value": "N/A",
            "Unit":"MPa"
          }},
    "Tensile_Strength": {{
            "Value": ,
            "Unit":""
          }},
    "Glass_transition_temperature":[{{
            "Name":"Material Name"
            "Value": "N/A",
            "Unit":"°C"
          }}]
  }}
]
```
"""
  
    response = assistant.generate_answer(prompt.format(relevant_text=relevant_text))
    try:
        json_str = re.search(r'```json(.*?)```', response, re.DOTALL).group(1).strip() #LLM生成的json数据
    except Exception as e:
        print(e)
        json_str = [
  {
     "Polymer": 
      {
        "Name": "",
        "Concentration": {
            "Value": "",
            "Unit": "M"
          },
        "Molecular_weight":{
            "Value": '',
            "Unit":"kDa"
          },
        "Component":{
                        "Composition": "",
                        "Weight_Ratio": "",
                        "Molar_Ratio":""
                    }
      },
    "Monomers": [
      {
          "Name": "",
          "SMILE": "",
          "CAS": ""
      }
    ],
    "Salts": [
      {
        "Name": "",
        "SMILES": "",
        "CAS": ""
      },
    ],
    "Initiators": [
      {
        "Name": "",
        "Description":"",
        "SMILES": "",
        "CAS": "",
        "Concentration": {
            "Value": "",
            "Unit": "M"
          }
      }
    ],
    "Polymerization": [
    {
      "Temperature":
      {
        "Value": "",
        "Unit": "°C"
      },
      "Time":
      {
        "Value": "",
        "Unit": "h"
      },
      "Activation_energy":
            {
            "Descricption":"",
            "Value": "",
            "Unit":"eV"
          }
    }
    ],
    "Experiment_Methods": "",
    "Mechanism": "",
    "Conductivity":[
      {
        "Ion": "Ion_Name",
        "Value": "",
         "Unit": "S cm−1",
        "Temperature":{
            "Value": "Temperature.Value",
            "Unit": "°C"
          }
      },
      {
        "Ion": "",
        "Value": "",
        "Unit": "",
        "Temperature":{
            "Value": "",
            "Unit": "°C"
          }
      },
    ]
    ,
    "Transference_Number": {
            "Value": "",
            "Unit":"N/A",
            "Temperature":
            {
            "Value": "",
            "Unit":"°C"
            }
          },
    "Electrochemical_Window": {
            "Value": "",
            "Unit":"V",
            "Temperature":
            {
            "Value": "",
            "Unit":"°C"
            }
          },
    "Critical_Current_Density": {
            "Value": "N/A",
            "Unit":"MPa"
          },
    "Tensile_Strength": {
            "Value": '',
            "Unit":""
          },
    "Glass_transition_temperature":[{
            "Name":"",
            "Value": "N/A",
            "Unit":"°C"
          }]
  }
]

    return json_str

# 对话LLM获取更加全面的json内容
def complete_json_data(relevant_text, json_str):
    prompt_for_complete = """I will provide a text and a JSON data. Please read TEXT carefully and complte  the JSON data.
Ensure that you identify and include all relevant details from the entire TEXT. Complete extraction and thoroughness are crucial. 
Pay attention to all parts of the document to avoid missing any relevant information.
Your work is to do finish the below tasks perfectly:
Add 'CAS','SMILES' for key 'Monomers','Salts','Initiators',please pay attention to complete them with your own knowledge and the given TEXT.If you dont know it,please infer it by its 'Name'.
Complete the data of 'Polymer','Monomers','Salts' and 'Initiators' according to the TEXT . The 'N/A' data you should dig them in the given TEXT,such as Polymer's"Weight_Ratio" or "Molar_Ratio".
If there are some 'Name' are just abbreviate,please change it to the full name of chemical standard.

For the json data ,If the key is a list type, it means there could be multiple values,you could to extract **ALL** of them. If the key is a single dictionary, it means there should be only one value, so provide the most relevant one. 
Your output must be the correct json format and dont write comments.
Your json format must strictly follow the same as the json data,dont change or add,delete keys. But 'CAS','SMILES',more list values are allowed.  

TEXT:
{relevant_text}

JSON data:
```json
{json_data}
```"""
    
    response = assistant.generate_answer(prompt_for_complete.format(relevant_text=relevant_text, json_data=json_str))
    json_str = re.search(r'```json(.*?)```', response, re.DOTALL).group(1).strip() #LLM生成的json数据
    return json_str

def complete_json_data_specical(relevant_text, json_str):
    prompt_for_complete = """I will provide a text and a JSON data. Please read TEXT carefully and complte  the JSON data.
Ensure that you identify and include all relevant details from the entire TEXT. Complete extraction and thoroughness are crucial. 
Pay attention to all parts of the document to avoid missing any relevant information.
Your work is to do finish the below tasks perfectly:
Pay special attention to ** Find all relevant data about "Conductivity", add them as the same format data on the old JSON data ** All relevant results must be given, and your output is a complete JSON data with everything.

For the json data ,If the key is a list type, it means there could be multiple values,you could to extract **ALL** of them. If the key is a single dictionary, it means there should be only one value, so provide the most relevant one. 
Your output must be the correct json format and dont write comments.
Your json format must strictly follow the same as the json data,dont change or add,delete keys. But 'CAS','SMILES',more list values are allowed.  

TEXT:
{relevant_text}

JSON data:
```json
{json_data}
```"""
    
    response = assistant.generate_answer(prompt_for_complete.format(relevant_text=relevant_text, json_data=json_str))
    json_str = re.search(r'```json(.*?)```', response, re.DOTALL).group(1).strip() #LLM生成的json数据
    return json_str



conductivity_queries = [
    "The ion conductivity value measured for the polymer electrolyte in the study, including specific experimental conditions and results",
    "Detailed measurement results of ionic conductivity in the electrolyte solution, covering various experimental setups and findings",
    "Comprehensive data on the ionic conductivity of the polymer electrolyte, including measurement techniques and values",
    "The ionic conductivity value of the electrolyte at various temperatures as reported in the research, along with experimental conditions",
    "Measured conductivity values for the polymer in the study, including specific conditions and contexts in which measurements were taken",
    "Results of conductivity measurements in the polymer electrolyte, with a focus on different temperatures and experimental conditions",
    "Ionic conductivity values reported at different temperatures, including experimental setups and specific findings",
    "Electrolyte solution conductivity value and detailed measurement data from the study, covering various experimental conditions",
    "Experimental results of measured ionic conductivity, including specific methodologies and conditions used in the study",
    "Ion conductivity of the polymer electrolyte and its value as detailed in the study, including specific experimental setups and results"
]

conductivity_keywords =[
    "conductivity",
    "ion conductivity value",
    "ionic conductivity measurement",
    "ionic conductivity data",
    "ionic conductivity of the electrolyte",
    "conductivity value in polymer",
    "conductivity measurement result",
    "electrolyte conductivity value",
    "measured ionic conductivity",
    "polymer electrolyte ion conductivity"
]
    


if __name__ == "__main__":
#    json_file = 'articles.json'  
#    pdf_links = extract_pdf_links(json_file)
    batch_size = 5
    max_total = 450  # 设置最大处理的总数

    total_processed = 0
    batch_counter = 0  # 用于计数当前处理到第几个batch
    pdf_paths = list_files_in_directory("your_dictionary")

    for pdf_batch in batch_process_links(pdf_paths, batch_size):
        if total_processed >= max_total:
            break
        
        # 开始时间
        start_time = time()

        save_pdf_batch_to_txt(pdf_batch)

        batch_counter += 1  # 每处理一个batch，计数器加1
        
        # 跳过batch
        # if batch_counter <= 12:
        #     continue

        # 修改成并行
        current_batch_size = min(batch_size, max_total - total_processed)
        # retrieved_index_data = retrieve(pdf_batch[:current_batch_size])
        retrieved_index_data = retrieve_from_documents(pdf_batch[:current_batch_size])
        paragraphs_data = merge_documents(retrieved_index_data)
     

#        keywords_retrieved_data = retrieve(pdf_batch[:current_batch_size],keywords=conductivity_queries,keystatements=conductivity_queries)
    

        for entry in paragraphs_data:
            if total_processed >= max_total:
                break
            title = entry['Document']
            relevant_text = entry['Paragraphs']
            json_str = generate_initial_json(relevant_text)
            #print(relevant_text)
#            print(f"生成初始数据：{json_str}")
            json_str = complete_json_data(relevant_text,json_str)
            json_str = complete_json_data_specical(relevant_text,json_str)
            print(f"Document: {entry['Document']} has been processed")
            # print(f"Paragraphs: {entry['Paragraphs']}")
            save_to_json_file(title,json_str)
            total_processed += 1
            # for counting
            print(f"{total_processed}") 

        # 记录结束时间
        end_time = time()
        batch_time = end_time - start_time
        print(f"Batch processed in {batch_time:.2f} seconds.")
        print(datetime.now())
        # 等待避免超出API速率限制
        sleep(3)