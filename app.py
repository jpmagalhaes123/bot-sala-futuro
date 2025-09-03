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
        
        # 2. PRIMEIRO ACESSO PARA OBTER COOKIES
        session = requests.Session()
        login_page_url = "https://saladofuturo.educacao.sp.gov.br/login-alunos"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        # Primeira requisição para obter cookies
        print("Obtendo cookies iniciais...")
        response = session.get(login_page_url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "message": f"Erro ao acessar página de login: {response.status_code}"
            })
        
        # 3. FORMATA USER CORRETAMENTE
        user = f"{ra}{digito}{estado}"
        
        # 4. TENTAR LOGIN COM COOKIES
        login_url = "https://saladofuturo.educacao.sp.gov.br/LoginCompletoToken"
        payload = {
            "user": user,
            "senha": senha
        }
        
        # Headers para JSON
        headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/login-alunos",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        print(f"Tentando login com user: {user}")
        response = session.post(login_url, json=payload, headers=headers)
        
        # DEBUG CRUCIAL
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Sample: {response.text[:500]}...")
        print(f"Cookies: {dict(session.cookies)}")
        
        # 5. ANALISAR RESPOSTA
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                # É JSON - provavelmente sucesso
                try:
                    response_data = response.json()
                    if "token" in response_data:
                        return jsonify({
                            "success": True,
                            "message": "Login realizado com sucesso!",
                            "token": response_data["token"],
                            "data": response_data
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "message": "Login falhou - token não encontrado na resposta",
                            "response": response_data
                        })
                except:
                    # Não é JSON válido
                    pass
            
            # Se chegou aqui, é HTML ou resposta inesperada
            if "dashboard" in response.text or "inicio" in response.text:
                return jsonify({
                    "success": True,
                    "message": "Login realizado (redirecionamento detectado)",
                    "response_sample": response.text[:500] + "..."
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Resposta inesperada - página HTML retornada",
                    "response_sample": response.text[:500] + "..."
                })
        
        return jsonify({
            "success": False,
            "message": f"Erro HTTP {response.status_code}",
            "status_code": response.status_code
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

