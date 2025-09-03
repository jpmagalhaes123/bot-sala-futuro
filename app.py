from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

app = Flask(__name__)
CORS(app)

# Configurações do Chrome para Render
def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executar em background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
    return chrome_options

@app.route('/login', methods=['POST', 'OPTIONS'])
def login_sala_futuro():
    driver = None
    try:
        if request.method == 'OPTIONS':
            return jsonify({"status": "ok"})
            
        data = request.json
        ra = data['ra']
        digito = data['digito']
        estado = data['estado']
        senha = data['senha']
        
        # Configurar Chrome com webdriver-manager
        chrome_options = setup_chrome_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 1. Acessar página de login
        print("Acessando página de login...")
        driver.get("https://saladofuturo.educacao.sp.gov.br/login-alunos")
        time.sleep(3)
        
        # 2. Preencher formulário
        print("Preenchendo formulário...")
        
        # Usar WebDriverWait para esperar elementos - MUITO IMPORTANTE
        wait = WebDriverWait(driver, 10)
        
        ra_input = wait.until(EC.presence_of_element_located((By.ID, "ra")))
        digito_input = driver.find_element(By.ID, "digito")
        estado_input = driver.find_element(By.ID, "estado")
        senha_input = driver.find_element(By.ID, "senha")
        
        ra_input.send_keys(ra)
        digito_input.send_keys(digito)
        estado_input.send_keys(estado)
        senha_input.send_keys(senha)
        
        # 3. Clicar no botão de login
        print("Clicando no botão de login...")
        login_button = driver.find_element(By.ID, "btn-login")
        login_button.click()
        
        # 4. Aguardar redirecionamento
        print("Aguardando redirecionamento...")
        time.sleep(5)
        
        # 5. Verificar se login foi bem-sucedido
        current_url = driver.current_url
        print(f"URL atual: {current_url}")
        
        if "dashboard" in current_url or "inicio" in current_url:
            # Login bem-sucedido - capturar token
            print("Login bem-sucedido! Capturando token...")
            
            # Tentar capturar token de várias fontes - ESSENCIAL
            token = None
            
            # Dos cookies
            cookies = driver.get_cookies()
            for cookie in cookies:
                if 'token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                    token = cookie['value']
                    break
            
            # Da localStorage
            if not token:
                try:
                    token = driver.execute_script("return localStorage.getItem('token');")
                except:
                    pass
            
            # Da sessionStorage
            if not token:
                try:
                    token = driver.execute_script("return sessionStorage.getItem('token');")
                except:
                    pass
            
            driver.quit()
            
            return jsonify({
                "success": True,
                "message": "Login realizado com sucesso!",
                "token": token or "token_nao_encontrado_mas_login_ok",
                "redirect_url": current_url
            })
        else:
            # Login falhou
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
                    "message": "Falha no login - verifique as credenciais",
                    "current_url": current_url
                })
            
    except Exception as e:
        if driver:
            driver.quit()
        return jsonify({
            "success": False,
            "message": f"Erro no processo: {str(e)}"
        })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "Server funcionando"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
