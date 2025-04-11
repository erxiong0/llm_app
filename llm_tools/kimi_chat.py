from openai import OpenAI
import sys
sys.path.append('..')
from llm_tools.config.config import kimi_api_key
import time

class Kimi:
    def __init__(self):  # 修复方法名 __init__
        self.client = OpenAI(
            api_key=kimi_api_key,
            base_url="https://api.moonshot.cn/v1",
        )
        self.model_name = "moonshot-v1-8k"
        self.messages = []  # 初始化 messages 属性
        self.limit = 15
    
    def _query_process(self, query: str, role: str):
        if len(self.messages) >= self.limit:
            self.messages = self.messages[-(self.limit-3):]
        
        self.messages.append({"role": role, "content": query})
        return self.messages
    
    def get_response(self, query: str):
        self._query_process(query, 'user')  
        
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            temperature=0.1,
        )
        res = completion.choices[0].message.content
        self._query_process(res, 'assistant')  
        
        return res


if __name__ == "__main__":
    llm = Kimi()
    t1 = time.time()
    prompt = "介绍一下数学家 Cauchy"
    res = llm.get_response(prompt)
    print(time.time() - t1)
    print(res)