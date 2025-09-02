from flask import Flask, request, jsonify
from flask_cors import CORS  # ← ADICIONE ESTA LINHA
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os

app = Flask(__name__)
CORS(app)  # ← ADICIONE ESTA LINHA (ISSO RESOLVE O CORS!)

@app.route('/login', methods=['POST', 'OPTIONS'])  # ← ADICIONE OPTIONS
def login_sala_futuro():
    try:
        # Resposta para pré-requisições CORS
        if request.method == 'OPTIONS':
            response = jsonify({"status": "ok"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', '*')
            response.headers.add('Access-Control-Allow-Methods', '*')
            return response
            
        # Receber dados do formulário
        data = request.json
        ra = data['ra']
        digito = data['digito']
        estado = data['estado']
        senha = data['senha']
        
        # Configurar Chrome para Render
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Fazer login na plataforma oficial
        driver.get("https://saladofuturo.educacao.sp.gov.br")
        time.sleep(3)
        
        # Preencher formulário (ajuste os seletores se necessário)
        driver.find_element(By.ID, "ra").send_keys(ra)
        driver.find_element(By.ID, "digito").send_keys(digito)
        driver.find_element(By.ID, "estado").send_keys(estado)
        driver.find_element(By.ID, "senha").send_keys(senha)
        driver.find_element(By.ID, "btn-login").click()
        
        time.sleep(5)
        
        # Verificar se login foi bem-sucedido
        if "dashboard" in driver.current_url or "tarefas" in driver.current_url:
            # Capturar cookies para obter token
            cookies = driver.get_cookies()
            token_cookie = next((c for c in cookies if 'token' in c['name'] or 'auth' in c['name']), None)
            
            # Se não encontrou token, tenta capturar da localStorage
            if not token_cookie:
                try:
                    token_js = driver.execute_script("return localStorage.getItem('token');")
                    if token_js:
                        token_cookie = {'value': token_js}
                except:
                    pass
            
            driver.quit()
            
            if token_cookie:
                return jsonify({
                    "success": True,
                    "token": token_cookie['value'],
                    "message": "Login realizado com sucesso"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Login realizado mas token não encontrado"
                })
        else:
            # Capturar possível erro de login
            page_source = driver.page_source
            driver.quit()
            
            if "senha incorreta" in page_source.lower():
                return jsonify({
                    "success": False,
                    "message": "Senha incorreta"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Falha no login - verifique as credenciais"
                })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "Server is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
