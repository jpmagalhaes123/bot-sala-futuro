from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Configurações do reCAPTCHA (substitua com suas chaves)
RECAPTCHA_SECRET_KEY = "SUA_SECRET_KEY_AQUI"
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
        
        # 2. FORMATAR user COMO A PLATAFORMA EXIGE
        user = f"{ra}{digito}{estado}"
        
        # 3. URL DA API DE LOGIN 
        login_url = "https://saladofuturo.educacao.sp.gov.br/LoginCompletoToken"
        
        # 4. PAYLOAD CORRETO
        payload = {
            "user": user,
            "senha": senha
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://saladofuturo.educacao.sp.gov.br",
            "Referer": "https://saladofuturo.educacao.sp.gov.br/login-alunos"
        }
        
        # 5. FAZER LOGIN NA API OFICIAL
        response = requests.post(login_url, json=payload, headers=headers)
        
        # 6. DEBUG: LOGAR TUDO (você verá no Render)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text[:500]}...")
        print(f"Headers: {dict(response.headers)}")
        print(f"Cookies: {dict(response.cookies)}")
        
        # 7. VERIFICAR RESPOSTA
        if response.status_code == 200:
            # Verifica múltiplos indicadores de sucesso
            response_lower = response.text.lower()
            success_indicators = [
                "token" in response_lower,
                "dashboard" in response_lower,
                "inicio" in response_lower, 
                "success" in response_lower,
                "redirect" in response_lower,
                any('auth' in cookie.name.lower() for cookie in response.cookies),
                any('token' in cookie.name.lower() for cookie in response.cookies)
            ]
            
            if any(success_indicators):
                # Capturar token de várias fontes possíveis
                token = None
                
                # Tentar do JSON
                try:
                    json_data = response.json()
                    token = json_data.get("token") or json_data.get("access_token")
                except:
                    pass
                    
                # Tentar dos cookies
                if not token:
                    for cookie in response.cookies:
                        if 'token' in cookie.name.lower() or 'auth' in cookie.name.lower():
                            token = cookie.value
                            break
                
                # Tentar do header
                if not token:
                    auth_header = response.headers.get('Authorization', '')
                    if 'bearer' in auth_header.lower():
                        token = auth_header.replace('Bearer ', '').replace('bearer ', '')
                
                return jsonify({
                    "success": True,
                    "message": "Login realizado com sucesso!",
                    "token": token or "token_nao_encontrado_mas_login_ok",
                    "status_code": response.status_code,
                    "cookies": {c.name: c.value for c in response.cookies},
                    "response_sample": response.text[:500] + "..." if len(response.text) > 500 else response.text
                })
            
        # 8. SE CHEGOU AQUI, LOGIN FALHOU
        return jsonify({
            "success": False,
            "message": "Falha no login. Verifique suas credenciais.",
            "status_code": response.status_code,
            "response": response.text[:1000] + "..." if len(response.text) > 1000 else response.text
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
