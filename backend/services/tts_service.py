import os
import re
import asyncio
import threading
import edge_tts
import pygame
import time
import glob

class TTSService:
    def __init__(self, voice: str = "es-CO-SalomeNeural"):
        self.voice = voice
        self.temp_folder = os.path.join(os.getcwd(), 'backend', 'data', 'temp_audio')
        os.makedirs(self.temp_folder, exist_ok=True)
        
        # Limpiar residuos al arrancar
        self._limpiar_carpeta_temp()
        
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _limpiar_carpeta_temp(self):
        """Elimina mp3s antiguos de la carpeta temporal."""
        try:
            archivos_mp3 = glob.glob(os.path.join(self.temp_folder, '*.mp3'))
            for archivo in archivos_mp3:
                try:
                    os.remove(archivo)
                except Exception:
                    pass
        except Exception as e:
            print(f"[TTS] Error al limpiar carpeta temp: {e}")

    def _limpiar_markdown(self, texto: str) -> str:
        """Elimina caracteres especiales de Markdown (*, #, _, etc.) para evitar que el TTS los lea."""
        # Remueve asteriscos, numerales, guiones de lista, corchetes, paréntesis y backticks
        texto_limpio = re.sub(r'[\*\#\_\~\[\]\(\)\-\`\>]', ' ', texto)
        # Normaliza múltiples espacios
        return " ".join(texto_limpio.split())

    async def _generar_audio_async(self, texto: str, ruta_salida: str):
        # Voz de Gonzalo (Colombia) ajustada en +40Hz para efecto de voz de niño
        communicate = edge_tts.Communicate(texto, self.voice, pitch="-1Hz", rate="+20%")
        await communicate.save(ruta_salida)

    def hablar(self, texto: str) -> bool:
        if not texto or not texto.strip():
            return False

        # 1. Limpiar caracteres de Markdown (asteriscos, viñetas, etc.) antes de sintetizar
        texto_para_audio = self._limpiar_markdown(texto)
        if not texto_para_audio.strip():
            return False

        # 2. Limpieza de mp3s viejos
        self._limpiar_carpeta_temp()

        nombre_archivo = f'respuesta_{int(time.time())}.mp3'
        ruta_mp3 = os.path.join(self.temp_folder, nombre_archivo)

        try:
            # 3. Generación del archivo con bucle seguro
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._generar_audio_async(texto_para_audio, ruta_mp3))
            loop.close()

            # 4. Reproducción desacoplada en hilo secundario
            hilo_reproduccion = threading.Thread(target=self._reproducir_en_hilo, args=(ruta_mp3,))
            hilo_reproduccion.daemon = True
            hilo_reproduccion.start()
            return True

        except Exception as e:
            print(f"[TTS ERROR] Fallo al procesar la voz: {e}")
            return False

    def _reproducir_en_hilo(self, ruta_audio: str):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass
                
            pygame.mixer.music.load(ruta_audio)
            pygame.mixer.music.play()

            # Esperar a que termine de hablar
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass

            if os.path.exists(ruta_audio):
                try:
                    os.remove(ruta_audio)
                except Exception:
                    pass

        except Exception as e:
            print(f"[TTS ERROR] Error en reproducción de audio: {e}")

    def detener_audio(self):
        """Detiene inmediatamente la voz actual (Barge-in)."""
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
                print("🛑 Audio de Luminito interrumpido.")
            return True
        except Exception as e:
            print(f"[TTS ERROR] Error al detener audio: {e}")
            return False