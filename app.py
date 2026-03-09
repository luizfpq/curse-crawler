import os
import json
import subprocess
import sys
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Configurações de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FOLDER = os.path.join(BASE_DIR, 'json')
CRAWLERS_FOLDER = os.path.join(BASE_DIR, 'crawlers')

def load_all_json_data():
    all_courses = []
    if not os.path.exists(JSON_FOLDER):
        return all_courses

    for filename in os.listdir(JSON_FOLDER):
        if filename.endswith('.json'):
            file_path = os.path.join(JSON_FOLDER, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                    origin = "IFRS" if "ifrs" in filename.lower() else "IFSP"
                    
                    if origin == "IFRS" and isinstance(data, list):
                        for item in data:
                            all_courses.append({
                                "title": item.get("title", ""),
                                "campus": item.get("campus", "").split('(')[0].strip(),
                                "level": item.get("level", "").replace('\n', '').strip(),
                                "details": item.get("duration", "Duração não informada"),
                                "modality": item.get("modality", "Presencial"),
                                "url": item.get("url"),
                                "origin": "IFRS",
                                "color": "border-green-500"
                            })
                    
                    elif origin == "IFSP" and isinstance(data, dict):
                        for category, courses in data.items():
                            current_campus = "Campus não especificado"
                            for item in courses:
                                name = item.get("name", "")
                                url = item.get("url")

                                # Lógica para capturar o campus nos separadores do IFSP
                                if not url and "Campus" in name:
                                    current_campus = name.replace("Campus ", "").strip()
                                    continue

                                if url and "VOLTAR AO TOPO" not in name.upper():
                                    display_campus = current_campus
                                    # Fallback para links onde o nome do campus é o próprio link
                                    if current_campus == "Campus não especificado" and len(name.split()) < 3:
                                        display_campus = name

                                    all_courses.append({
                                        "title": name,
                                        "campus": display_campus,
                                        "level": category,
                                        "details": "Veja detalhes no link oficial",
                                        "modality": "EaD" if "EAD" in category.upper() else "Presencial",
                                        "url": url,
                                        "origin": "IFSP",
                                        "color": "border-blue-500"
                                    })
            except Exception as e:
                print(f"Erro ao ler {filename}: {e}")
                
    return all_courses

@app.route('/api/courses')
def get_courses():
    return jsonify(load_all_json_data())

@app.route('/api/update')
def run_updates():
    if not os.path.exists(CRAWLERS_FOLDER):
        return jsonify({"error": "Pasta crawlers não encontrada"}), 404
        
    scripts = [f for f in os.listdir(CRAWLERS_FOLDER) if f.endswith('.py')]
    results = []
    
    python_executable = sys.executable

    for script in scripts:
        script_path = os.path.join(CRAWLERS_FOLDER, script)
        try:
            process = subprocess.run([python_executable, script_path], 
                                     capture_output=True, 
                                     text=True, 
                                     cwd=BASE_DIR)
            
            if process.returncode == 0:
                results.append({"script": script, "status": "Sucesso"})
            else:
                results.append({"script": script, "status": "Erro", "error": process.stderr})
        except Exception as e:
            results.append({"script": script, "status": "Falha Crítica", "error": str(e)})

    return jsonify({"summary": results})

@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "Arquivo index.html não encontrado na raiz do projeto.", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)