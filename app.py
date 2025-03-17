
from flask import Flask, request, jsonify, render_template
import json
from hazm import Stemmer, stopwords_list, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch 



app = Flask(__name__)

# خواندن داده‌ها از فایل JSON
try:
    with open("faq_data.json", "r", encoding="utf-8") as json_file:
        faq_data = json.load(json_file)
except FileNotFoundError:
    print("خطا: فایل faq_data.json پیدا نشد.")
    exit()

# آماده‌سازی ابزارهای پردازش فارسی
stemmer = Stemmer()
stop_words = set(stopwords_list())

# پیش‌پردازش سوالات FAQ
faq_questions = [faq["question"] for faq in faq_data["faqs"]]

def preprocess_text(text):
    tokens = word_tokenize(text.lower())  # توکنایز کردن و تبدیل به حروف کوچک
    filtered_tokens = [word for word in tokens if word not in stop_words]  # حذف کلمات بی‌اهمیت
    return " ".join(filtered_tokens)  # تبدیل به متن

# پیش‌پردازش تمام سوالات FAQ
processed_questions = [preprocess_text(question) for question in faq_questions]

# بردار TF-IDF برای سوالات
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(processed_questions)

# بارگذاری مدل و توکنایزر
model_name = "HooshvareLab/gpt2-fa"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# تابع تولید پاسخ
def generate_gpt_response(input_text):
    # توکنایز کردن ورودی
    inputs = tokenizer.encode(input_text, return_tensors="pt")
    
    # تولید پاسخ
    outputs = model.generate(
        inputs,
        max_length=100,  # حداکثر طول پاسخ
        num_return_sequences=1,  # تعداد پاسخ‌های تولیدی
        no_repeat_ngram_size=2,  # جلوگیری از تکرار جملات
        temperature=0.7,  # کنترل خلاقیت مدل
        top_p=0.9,  # انتخاب کلمات با احتمال بالا
        top_k=50  # محدود کردن جستجو به 50 کلمه برتر
    )
    
    # تبدیل توکن‌ها به متن
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


# جستجوی پاسخ بر اساس TF-IDF و شباهت کسینوسی
def search_answer_advanced(user_question):
    user_question_processed = preprocess_text(user_question)  # پیش‌پردازش سوال کاربر
    user_vector = vectorizer.transform([user_question_processed])  # تبدیل سوال به بردار TF-IDF

    # محاسبه شباهت کسینوسی
    similarities = cosine_similarity(user_vector, tfidf_matrix)
    max_index = similarities.argmax()  # پیدا کردن بیشترین شباهت
    max_similarity = similarities[0, max_index]

    if max_similarity > 0.3:  # اگر شباهت بالا باشد
        return faq_data["faqs"][max_index]["response"]  # پاسخ FAQ بازگردانده شود
    elif max_similarity < 0.1:  # اگر شباهت خیلی پایین باشد
        return "متأسفم، نمی‌توانم به سوال شما پاسخ دهم."
    else:  # در غیر این صورت از مدل GPT-2 برای پاسخ داینامیک استفاده کن
        return generate_gpt_response(user_question)




# API دریافت پیشنهادات مشابه
@app.route('/suggestions', methods=['POST'])
def suggestions():
    user_input = request.json.get('input')
    if not user_input:
        return jsonify({"error": "لطفاً سوال خود را وارد کنید."}), 400
    
    suggestions = get_suggestions(user_input)  # اینجا پیشنهادات مشابه از تابع get_suggestions گرفته می‌شود
    return jsonify({"suggestions": suggestions})

# تابع برای پیدا کردن پیشنهادات مشابه
def get_suggestions(user_input):
    user_input_processed = preprocess_text(user_input)  # پیش‌پردازش ورودی کاربر
    user_vector = vectorizer.transform([user_input_processed])  # تبدیل به بردار TF-IDF
    similarities = cosine_similarity(user_vector, tfidf_matrix)  # شباهت کسینوسی
    sorted_indices = similarities.argsort()[0][::-1]  # مرتب‌سازی بر اساس شباهت
    suggestions = []

    for index in sorted_indices[:5]:  # نمایش ۵ پیشنهاد برتر
        suggestions.append(faq_data["faqs"][index]["question"])

    return suggestions


# API سوال و پاسخ
@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"answer": "لطفاً سوال خود را وارد کنید."}), 400
    
    answer = search_answer_advanced(user_question)
    return jsonify({"answer": answer})

# صفحه اصلی
@app.route('/')
def index():
    return render_template('index.html')




if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)