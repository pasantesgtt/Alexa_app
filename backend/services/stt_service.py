import os
from groq import Groq

class STTService:
    def __init__(self):
        # 1. Leer y separar las claves por coma desde la única variable
        claves_str = os.environ.get("GROQ_API_KEYS", "")
        claves_validas = [clave.strip() for clave in claves_str.split(",") if clave.strip()]
        
        self.clientes = [Groq(api_key=clave) for clave in claves_validas]
        self.indice_actual = 0
        
        print(f"¡Oído de Luminito activado (Groq Whisper) con {len(self.clientes)} claves en Round Robin por disponibilidad!")

    def transcribir_audio(self, ruta_audio: str) -> str:
        if not self.clientes:
            print("Error: No hay claves de Groq configuradas en GROQ_API_KEYS.")
            return ""

        intentos_maximos = len(self.clientes)
        
        # Leemos el archivo una sola vez en memoria para no tener que abrirlo en cada reintento
        try:
            with open(ruta_audio, "rb") as archivo_abierto:
                audio_data = archivo_abierto.read()
        except Exception as e:
            print(f"Error al leer el archivo de audio: {e}")
            return ""

        # Intentar con cada clave disponible hasta que una funcione
        for intento in range(intentos_maximos):
            cliente_actual = self.clientes[self.indice_actual]
            
            try:
                transcripcion = cliente_actual.audio.transcriptions.create(
                    file=(os.path.basename(ruta_audio), audio_data),
                    model="whisper-large-v3",
                    language="es",
                    temperature=0.0,
                    prompt = "Infibagué, alumbrado público, luminaria, luminarias LED, postes caídos, factura de energía, plazas de mercado, adjudicación de puesto, local, arrendamiento, contrato de uso administrativo, Rueda por Ibagué, bicicletas, estaciones, pieza gráfica, cubrimiento de evento, manual de imagen, PQRSD, peticiones, quejas, reclamos, sugerencias, denuncias, ventanilla única, Complejo Cultural Panóptico, museo, recorridos guiados, sala de música, auditorio, créditos de fomento, Inficréditos, microcrédito, MIPG, Sistema Integrado de Gestión, Oficina de Control Interno, auditorías, Oficina de Control Disciplinario, proceso disciplinario, falta disciplinaria, servidor público, sanción"
                )

                texto_final = transcripcion.text.strip()
                print(f"Groq escuchó (Clave {self.indice_actual + 1}): {texto_final}")
                
                # Avanzamos el índice para que la próxima consulta use la siguiente clave (Round Robin)
                self.indice_actual = (self.indice_actual + 1) % len(self.clientes)
                
                return texto_final

            except Exception as e:
                print(f"Fallo en STT con clave {self.indice_actual + 1} (Intento {intento + 1}/{intentos_maximos}): {e}")
                # Si hay error (ej. Rate Limit), saltamos a la siguiente clave inmediatamente
                self.indice_actual = (self.indice_actual + 1) % len(self.clientes)

        # Si el ciclo termina y no retornó nada, todas las claves fallaron
        print("Error crítico: Todas las claves de Groq fallaron o están sin saldo.")
        return ""