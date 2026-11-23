import serial
import time
import subprocess
import os
import glob
import threading

MODO_DESARROLLO = True  
BAUDIOS = 115200
TIEMPO_ESPERA = 30       
TIEMPO_ADVERTENCIA = 15  

estado_sistema = {
    "pantalla_encendida": True,
    "ultima_deteccion": time.time()
}

def obtener_entorno_wayland():
    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = "wayland-0"
    env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
    return env

def encender_pantalla():
    estado_sistema["pantalla_encendida"] = True
    if MODO_DESARROLLO:
        print("\n[DESARROLLO] 💡 Encendiendo pantalla (Simulado)")
        return
    subprocess.run(["wlr-randr", "--output", "HDMI-A-1", "--on"], env=obtener_entorno_wayland(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def apagar_pantalla():
    estado_sistema["pantalla_encendida"] = False
    if MODO_DESARROLLO:
        print("\n[DESARROLLO] 🌙 Apagando pantalla (Simulado)")
        return
    subprocess.run(["wlr-randr", "--output", "HDMI-A-1", "--off"], env=obtener_entorno_wayland(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def buscar_puerto():
    puertos = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    return puertos[0] if puertos else None

# === MÉTODO NUEVO DE PROTECCIÓN DE ESTADO ===
def registrar_interaccion():
    """Actualiza el estado de forma segura cuando el usuario interactúa con la pantalla web."""
    estado_sistema["ultima_deteccion"] = time.time()
    if not estado_sistema["pantalla_encendida"]:
        encender_pantalla()

def _bucle_escucha_sensor():
    encender_pantalla()
    advertencia_mostrada = False
    
    while True:
        try:
            if MODO_DESARROLLO:
                time.sleep(5)
                continue

            puerto_actual = buscar_puerto()
            if not puerto_actual:
                time.sleep(3)
                continue

            with serial.Serial(puerto_actual, BAUDIOS, timeout=0.1) as conexion:
                estado_sistema["ultima_deteccion"] = time.time()
                while True:
                    ahora = time.time()
                    if conexion.in_waiting > 0:
                        if "WAKE_UP" in conexion.read_all().decode('utf-8', errors='ignore'):
                            registrar_interaccion()
                            advertencia_mostrada = False

                    if estado_sistema["pantalla_encendida"]:
                        tiempo_transcurrido = int(ahora - estado_sistema["ultima_deteccion"])
                        if tiempo_transcurrido >= TIEMPO_ADVERTENCIA and not advertencia_mostrada:
                            advertencia_mostrada = True
                        if tiempo_transcurrido >= TIEMPO_ESPERA:
                            apagar_pantalla()
                            advertencia_mostrada = False

                    time.sleep(0.1)
        except Exception:
            time.sleep(3)

def iniciar_servicio_pantalla():
    hilo = threading.Thread(target=_bucle_escucha_sensor, daemon=True)
    hilo.start()

if __name__ == "__main__":
    print("Iniciando prueba directa de display_service...")
    iniciar_servicio_pantalla()
    
    # Mantener el script vivo para ver los mensajes
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPrueba finalizada.")