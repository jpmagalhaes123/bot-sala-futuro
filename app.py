from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# SUAS CHAVES reCAPTCHA (REAIS)
RECAPTCHA_SECRET_KEY = "6LckPrwrAAAAAO836Q2t6ZSxgGkznWpYX_0eRJ5K"
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

def verify_recaptcha(recaptcha_token):
    """Verifica se o reCAPTCHA é válido"""
    payload = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_token
    }
    response = requests.post(RECAPTCHA_VERIFY_URL, data=payload)
    result = response.json()
    return result.get('success', False)

@app.route('/login', methods=['POST', 'OPTIONS'])
@app.route('/login', methods=['POST', 'OPTIONS'])
@app.route('/login', methods=['POST', 'OPTIONS'])
def login_sala_futuro():
    try:
        if request.method == 'OPTIONS':
            return jsonify({"status": "ok"})
            
        data = request.json
        ra = data['ra']
        digito = data['digito']
        estado = data['estado']
        senha = data['senha']
        recaptcha_token = data.get('recaptcha_token', '')
        
        # 1. VALIDAR CAPTCHA
        if not verify_recaptcha(recaptcha_token):
            return jsonify({
                "success": False,
                "message": "Falha na verificação do reCAPTCHA. Tente novamente."
            })
        
        # 2. TESTAR DIFERENTES ENDPOINTS
        endpoints = [
            "https://saladofuturo.educacao.sp.gov.br/api/auth/login",
            "https://saladofuturo.educacao.sp.gov.br/api/login",
            "https://saladofuturo.educacao.sp.gov.br/auth/login",
            "https://saladofuturo.educacao.sp.gov.br/LoginCompletoToken"
        ]
        
        user = f"{ra}{digito}{estado}"
        payload = {"user": user, "senha": senha}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/login-alunos",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # 3. TESTAR TODOS OS ENDPOINTS
        for endpoint in endpoints:
            try:
                print(f"Testando endpoint: {endpoint}")
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Response: {response.text[:200]}...")
                
                if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                    response_data = response.json()
                    if "token" in response_data:
                        return jsonify({
                            "success": True,
                            "message": f"Login via {endpoint}",
                            "token": response_data["token"],
                            "endpoint": endpoint
                        })
                
            except Exception as e:
                print(f"Erro no endpoint {endpoint}: {str(e)}")
                continue
        
        # 4. SE NENHUM FUNCIONOU, RETORNAR ERRO
        return jsonify({
            "success": False,
            "message": "Nenhum endpoint funcionou. A plataforma pode ter mudado a API.",
            "user_format": user,
            "tested_endpoints": endpoints
        })
            
    except Exception as e:
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


