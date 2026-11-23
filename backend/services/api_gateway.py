import os
import requests

class Api_gateway:
    def __init__(self):
        # Leemos la variable directamente del entorno (.env)
        # Por defecto apunta a la VM remota si no encuentra la variable
        self.base_url = os.getenv("LUMINITO_IA_URL", "http://192.168.1.100:8000/api/v1/preguntar-stream")
        self.timeout = (
            float(os.getenv("TIMEOUT_CONNECT", 10.0)), 
            float(os.getenv("TIMEOUT_READ", 30.0))
        )

    def consultar_cerebro_stream(self, session_id: str, pregunta: str, sede: str):
        payload = {
            "session_id": session_id,
            "pregunta": pregunta,
            "sede": sede  # <-- Se lo mandamos a Luminito_ia
        }
        
        try:
            with requests.post(self.base_url, json=payload, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        yield chunk
        except requests.exceptions.RequestException as e:
            yield f"[Error crítico: No se pudo conectar con el cerebro en {self.base_url}]"