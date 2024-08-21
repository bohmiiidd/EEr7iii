import openai
from flask import Flask, request, jsonify

# Initialize OpenAI API key
openai.api_key = 'YOUR_API_KEY_HERE'

app = Flask(__name__)

def get_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can use different engines based on your requirement
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    response_text = get_response(user_query)
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True)
