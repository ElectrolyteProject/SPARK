from time import sleep
import openai

# 从LLM获取输出
# 定义LLM的初始prompt
class ChatGPTChemicalAssistant:
    def __init__(self,api_key,model):
        self.client = openai.OpenAI(api_key=api_key)
        self.api_key=api_key
        self.model = model

    def generate_answer(self,prompt,retries=3, delay=8):
        self.client = openai.OpenAI(api_key=self.api_key,base_url="your_url")
        for attempt in range(retries):
            try:
                chat_response = self.client.chat.completions.create(
                    model=self.model,
                    stream=False,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant with expertise in chemistry. Your task is to extract and generate key chemical knowledge from the provided text, focusing on the values, conditions,numbers and their interrelationships, and generate the data in JSON format according to the specified keywords."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8
                )
                answer = chat_response.choices[0].message.content        
                return answer
            
            except openai.APIConnectionError as e:
                print(f"Attempt {attempt + 1} failed with connection error: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    sleep(delay)
                else:
                    print("All retry attempts failed. Please check your network connection and try again later.")
                    return None
                
            except openai.InternalServerError as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    sleep(delay)
                else:
                    print("All retry attempts failed. Please check your API settings or try again later.")
                    return None

    def generate_answer_qwen(self,prompt,retries=3, delay=8):
        self.client = openai.OpenAI(api_key=self.api_key, base_url = "your-base-url")
        for attempt in range(retries):
            try:
                chat_response = self.client.chat.completions.create(
                    model=self.model,
                    stream=False,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant with expertise in chemistry. Your task is to extract and generate key chemical knowledge from the provided text, focusing on the values, conditions,numbers and their interrelationships, and generate the data in JSON format according to the specified keywords."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8
                )
                answer = chat_response.choices[0].message.content        
                return answer
            
            except openai.APITimeoutError as e:
                print(f"Attempt {attempt + 1} failed with connection error: {e}")
                print(f"API timed out: {e}")
            
            except openai.APIConnectionError as e:
                print(f"Attempt {attempt + 1} failed with connection error: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    sleep(delay)
                else:
                    print("All retry attempts failed. Please check your network connection and try again later.")
                    return None
                
            except openai.InternalServerError as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    sleep(delay)
                else:
                    print("All retry attempts failed. Please check your API settings or try again later.")
                    return None

