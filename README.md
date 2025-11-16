EchoVerse – AI Powered Intelligent Chatbot
Real-Time Web • Voice • Vision • OCR • Documents • Memory • Multi-Language

EchoVerse is a multimodal AI chatbot built using Google Gemini 2.5 Flash, Flask, SerpAPI, OCR, and Text-to-Speech.
It behaves like a mini ChatGPT with extra capabilities like real-time search, document Q&A, image understanding, voice replies, personality modes, and memory.

🚀 Features
✅ 1. Natural AI Chat (Gemini 2.5 Flash)

Human-like conversation

Multi-language support (English, Hindi, Hinglish, Spanish, French)

Auto contextual memory

✅ 2. Real-Time Web Search (SerpAPI)

Fetches latest live news, sports, facts, trends

Confidence scoring + fallback answers
![image-1](image-1.png)

✅ 3. Document Understanding

Supports PDF, DOCX, TXT

Summaries, explanations & Q/A

5-point summary generator

Content stored for follow-up questions

✅ 4. Image Understanding + OCR

Extracts text using Pytesseract

Gemini explains or summarizes image content

✅ 5. Voice Output (pyttsx3)

Speaks out chatbot replies

Offline and lightweight

✅ 6. Personalities

Fun

Professional

Developer

Educational

Motivational

✅ 7. Multi-Language Mode

AI replies in selected language

Voice output also supports multi-language

✅ 8. Memory System

JSON-based memory

Stores user preferences

✅ 9. Beautiful Frontend

HTML, CSS, JavaScript

ChatGPT-style UI

Theme toggle

Sidebar

File upload buttons

🧠 Technologies Used
AI & NLP

Google Gemini 2.5 Flash

google-generativeai

Backend

Flask (Python)

python-dotenv

Web Requests

Requests

BeautifulSoup

OCR & Vision

Pytesseract

Pillow

Document Processing

PyPDF2

docx2txt

Text-to-Speech

pyttsx3

Optional (Database)

pymongo

🔐 Environment Variables (.env file)

Create a .env file in your project:

GOOGLE_API_KEY=your_gemini_api_key
SERPAPI_KEY=your_serpapi_key


Make sure never to upload .env to GitHub.

Add this to your .gitignore:

.env

🏗️ Project Architecture

Frontend → HTML/CSS/JS

Backend → Flask REST API

AI Engine → Gemini Flash

Web Search → SerpAPI

Memory Storage → JSON / MongoDB

OCR Engine → Tesseract

TTS Engine → pyttsx3

How to Run the Project

Clone repository:

git clone https://github.com/YourUsername/YourRepoName.git


Navigate to folder:

cd echoverse


Create virtual environment:

python -m venv venv


Activate environment:

Windows:

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Create .env file and add your API keys.

Run server:

python app.py


Open the frontend:

http://localhost:5000

📂 Folder Structure
/echoverse
│── app.py
│── static/
│── templates/
│── utils/
│── memory.json
│── requirements.txt
│── README.md
│── .env   (not uploaded)

🎯 Project Strengths

Real-time AI chat + search

Document + Image understanding

Voice output

Custom personalities

Multi-language mode

Clean UI

Strong backend architecture

🧩 Challenges Solved

Combining Gemini + SerpAPI

Handling low-quality OCR images

Avoiding TTS interference with chat

Frontend responsive design

Memory management

🏁 Conclusion

EchoVerse is a fully functional, multimodal AI chatbot that integrates:

✔ AI + OCR + Voice + Real-Time Web Search
✔ Document Intelligence
✔ Personality Modes
✔ Memory
✔ Beautiful Custom UI

It works like a mini ChatGPT with additional smart features and complete customizable code.
