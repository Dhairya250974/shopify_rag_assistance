import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from pipeline import RAGPipeline

load_dotenv()

app = Flask(__name__, template_folder='templates')
pipeline = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'No question'}), 400
    try:
        result = pipeline.query(question, top_k=5)
        return jsonify({
            'answer':      result['answer'],
            'sources':     result['sources'],
            'latency_ms':  result['latency_ms'],
            'model':       result['model'],
            'chunks_used': result['chunks_used'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Loading RAG pipeline...")
    pipeline = RAGPipeline()
    print("Pipeline ready! Open: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
