from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

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
        
        # FORMATAR user COMO A PLATAFORMA EXIGE: RA + Digito + Estado
        user = f"{ra}{digito}{estado}"
        
        # URL CORRETA DA API DE LOGIN (descoberta por você!)
        login_url = "https://saladofuturo.educacao.sp.gov.br/LoginCompletoToken"
        
        # PAYLOAD CORRETO (descoberto por você!)
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
        
        # FAZER LOGIN NA API OFICIAL
        response = requests.post(login_url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            # Tenta parsear a resposta como JSON
            try:
                response_data = response.json()
                
                # Verifica se login foi bem-sucedido
                if "token" in response_data or "success" in response_data:
                    return jsonify({
                        "success": True,
                        "message": "Login realizado com sucesso!",
                        "token": response_data.get("token", "token_recebido"),
                        "dados": response_data
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Login falhou - credenciais incorretas",
                        "resposta_servidor": response_data
                    })
                    
            except ValueError:
                # Se não for JSON, verifica se há texto indicando sucesso
                if "dashboard" in response.text or "inicio" in response.text:
                    return jsonify({
                        "success": True,
                        "message": "Login realizado (redirecionamento detectado)",
                        "resposta": response.text[:200] + "..." if len(response.text) > 200 else response.text
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Resposta inesperada do servidor",
                        "resposta": response.text[:500] + "..." if len(response.text) > 500 else response.text
                    })
                    
        else:
            return jsonify({
                "success": False,
                "message": f"Erro HTTP {response.status_code}",
                "detalhes": response.text
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

