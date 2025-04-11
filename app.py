from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import sys
import csv
import atexit
import logging  
from time import time 

sys.path.append('.')
from llm_tools.kimi_chat import Kimi
import markdown

# ------------------------ 日志配置（核心修复） ------------------------
app_logger = logging.getLogger('app_logger')
app_logger.setLevel(logging.INFO)
app_formatter = logging.Formatter('%(asctime)s - %(levelname)s - 耗时: %(elapsed_time)s 秒 - %(message)s')
app_file_handler = logging.FileHandler('log/app.log')
app_file_handler.setFormatter(app_formatter)
app_logger.addHandler(app_file_handler)
app_logger.addHandler(logging.StreamHandler())  # 控制台输出应用日志

# 2. Werkzeug服务器日志（使用默认格式，移除elapsed_time）
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
werkzeug_formatter = logging.Formatter('%(message)s')  # 使用原始格式
for handler in werkzeug_logger.handlers:
    handler.setFormatter(werkzeug_formatter)

# 3. 禁用Flask默认的调试日志干扰
logging.getLogger('flask').setLevel(logging.WARNING)

logger = app_logger  # 使用自定义的应用日志器


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

llm = Kimi()
db = SQLAlchemy(app)

csv_file = None
csv_writer = None
csv_file_path = './log/chat_history.csv'
initialized = False

if not os.path.exists('log'):
    os.makedirs('log')


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    is_bot = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)


@app.before_request
def initialize_resources():
    global initialized, csv_file, csv_writer
    if not initialized:
        db.create_all()
        file_exists = os.path.isfile(csv_file_path)
        csv_file = open(csv_file_path, mode='a', newline='', encoding='utf-8')
        fieldnames = ['user_input', 'ai_response', 'timestamp']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if not file_exists:
            csv_writer.writeheader()
        initialized = True


def get_ai_response(prompt):
    start_time = time()
    try:
        response = llm.get_response(prompt)
        elapsed_time = time() - start_time
        logger.info(f"大模型响应成功", extra={'elapsed_time': elapsed_time})
        return response
    except Exception as e:
        elapsed_time = time() - start_time
        logger.error(f"大模型请求失败: {str(e)}", extra={'elapsed_time': elapsed_time}, exc_info=True)
        return f"AI服务暂时不可用：{str(e)}"


def save_to_csv(user_input, ai_response):
    try:
        csv_writer.writerow({
            'user_input': user_input,
            'ai_response': ai_response,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        csv_file.flush()
    except Exception as e:
        logger.error(f"CSV写入失败: {str(e)}", exc_info=True)


@app.route('/')
def index():
    logger.info("用户访问首页", extra={'elapsed_time': 0})
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def handle_chat():
    start_time = time()
    user_input = request.json.get('message', '').strip()
    
    if not user_input:
        elapsed_time = time() - start_time
        logger.warning("用户发送空消息", extra={'elapsed_time': elapsed_time})
        return jsonify({'error': '请输入有效内容'}), 400

    logger.info(f"收到用户请求: {user_input}", extra={'elapsed_time': 0})
    
    try:
        user_msg = ChatMessage(content=user_input, is_bot=False)
        db.session.add(user_msg)
        ai_response = get_ai_response(user_input)
        bot_msg = ChatMessage(content=ai_response, is_bot=True)
        db.session.add(bot_msg)
        save_to_csv(user_input, ai_response)
        db.session.commit()
        
        response_data = {
            'user': user_input,
            'bot': markdown.markdown(ai_response),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        elapsed_time = time() - start_time
        logger.info(f"成功处理请求，返回响应: {response_data}", extra={'elapsed_time': elapsed_time})
        return jsonify(response_data)
    
    except Exception as e:
        db.session.rollback()
        elapsed_time = time() - start_time
        logger.error(f"聊天处理失败: {str(e)}", extra={'elapsed_time': elapsed_time}, exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500


@app.route('/history')
def get_chat_history():
    start_time = time()
    page = request.args.get('page', 1, type=int)
    
    try:
        messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        message_list = []
        for msg in messages.items:
            message_list.append({
                'id': msg.id,
                'content': markdown.markdown(msg.content) if msg.is_bot else msg.content,
                'is_bot': msg.is_bot,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        elapsed_time = time() - start_time
        logger.info(f"返回历史记录，页码: {page}，记录数: {len(message_list)}", 
                    extra={'elapsed_time': elapsed_time})
        return jsonify({
            'messages': message_list,
            'has_next': messages.has_next
        })
    
    except Exception as e:
        elapsed_time = time() - start_time
        logger.error(f"历史记录获取失败: {str(e)}", extra={'elapsed_time': elapsed_time}, exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500


@atexit.register
def cleanup_resources():
    global csv_file
    if csv_file and not csv_file.closed:
        csv_file.close()
        logger.info("CSV文件已关闭", extra={'elapsed_time': 0})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)