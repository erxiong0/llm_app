# LLM Service
I try to make LLM as a private assistant and now it is just a copy version with preference like [GPT](https://chatgpt.com), [Deepseek](https://chat.deepseek.com/) and so on.  

I have realized some functions:  

  - *Historical Record* The left panel stores the user's historical questions. When a user clicks on a question, the right panel automatically jumps to the corresponding answer. Additionally, refreshing the webpage will not clear the historical records.

## A Simple Example  
Config your llm api in `/Users/erxiong/Downloads/chichi_lab/flask_demo/llm_tools`. If you use `moonshot-v1-8k`, you can input your api key in `/Users/erxiong/Downloads/chichi_lab/flask_demo/llm_tools/config/config.py` directly.  

```bash
export FLASK_API=app.py
flask run
```

```bash
$ flask run
  * Running on http://127.0.0.1:8080/ (Press CTRL+C to quit)
```

## Dependencies
- flask (3.1.0)  
- python (3.10.16)  
- openai (1.70.0)  
- flask_sqlalchemy (3.1.1)  
