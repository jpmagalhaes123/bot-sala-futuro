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
import threading

app = Flask(__name__)
CORS(app)

# Configurações do Chrome otimizadas
def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    return chrome_options

def login_process(ra, digito, estado, senha):
    """Função separada para o processo de login"""
    driver = None
    try:
        chrome_options = setup_chrome_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Executar script para evitar detecção
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Acessando página de login...")
        driver.get("https://saladofuturo.educacao.sp.gov.br/login-alunos")
        
        # Wait otimizado
        wait = WebDriverWait(driver, 10)
        
        print("Preenchendo formulário...")
        ra_input = wait.until(EC.presence_of_element_located((By.ID, "ra")))
        digito_input = driver.find_element(By.ID, "digito")
        estado_input = driver.find_element(By.ID, "estado")
        senha_input = driver.find_element(By.ID, "senha")
        
        # Preencher campos um por um com delay
        ra_input.send_keys(ra)
        time.sleep(0.5)
        digito_input.send_keys(digito)
        time.sleep(0.5)
        estado_input.send_keys(estado)
        time.sleep(0.5)
        senha_input.send_keys(senha)
        time.sleep(1)
        
        print("Clicando no botão de login...")
        login_button = driver.find_element(By.ID, "btn-login")
        login_button.click()
        
        # Wait reduzido
        time.sleep(3)
        
        current_url = driver.current_url
        print(f"URL atual: {current_url}")
        
        if "dashboard" in current_url or "inicio" in current_url:
            # Login bem-sucedido
            token = None
            cookies = driver.get_cookies()
            
            for cookie in cookies:
                if any(key in cookie['name'].lower() for key in ['token', 'auth', 'session']):
                    token = cookie['value']
                    break
            
            driver.quit()
            return {
                "success": True,
                "message": "Login realizado com sucesso!",
                "token": token or "token_capturado",
                "redirect_url": current_url
            }
        else:
            driver.quit()
            return {
                "success": False,
                "message": "Falha no login - URL não redirecionou para dashboard"
            }
            
    except Exception as e:
        if driver:
            driver.quit()
        return {
            "success": False,
            "message": f"Erro: {str(e)}"
        }

@app.route('/login', methods=['POST', 'OPTIONS'])
def login_sala_futuro():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    try:
        data = request.json
        ra = data.get('ra', '')
        digito = data.get('digito', '')
        estado = data.get('estado', '')
        senha = data.get('senha', '')
        
        # Processo rápido com timeout
        result = login_process(ra, digito, estado, senha)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro no servidor: {str(e)}"
        })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "Server funcionando"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
