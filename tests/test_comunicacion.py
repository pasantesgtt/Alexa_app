
from backend.services.api_gateway import Api_gateway

def probar():
    brain = Api_gateway()
    session_id = "sesion_demo_quiosco"
    pregunta = "¿Quien eres?"
    
    print(f"-> Enviando pregunta desde luminito_app: '{pregunta}'\n")
    print("Luminito responde: ", end="", flush=True)
    
    # Consumir el generador en streaming
    for fragmento in brain.consultar_cerebro_stream(session_id, pregunta):
        print(fragmento, end="", flush=True)
        
    print("\n\n-> Transmisión finalizada con éxito.")

if __name__ == "__main__":
    probar()