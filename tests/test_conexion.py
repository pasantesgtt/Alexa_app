import time
import serial
import serial.tools.list_ports

BAUDIOS = 115200

def encontrar_puerto():
    puertos = list(serial.tools.list_ports.comports())
    if not puertos:
        return None
    
    print("Puertos serie detectados en tu equipo:")
    for p in puertos:
        print(f"  • {p.device}: {p.description}")
    
    # Toma el primer puerto serie disponible
    return puertos[0].device

puerto = encontrar_puerto()

if not puerto:
    print("\n❌ No se detectó ningún puerto COM / USB conectado.")
    print("Asegúrate de conectar el microcontrolador por cable USB a la laptop.")
    exit(1)

print(f"\n🔌 Intentando conectar a {puerto} a {BAUDIOS} baudios...")

try:
    with serial.Serial(puerto, BAUDIOS, timeout=0.5) as con:
        print(f"✅ Conexión establecida con {puerto}.")
        print("Pasa la mano frente a la cúpula / sensor PIR para probar lecturas...")
        print("-" * 50)
        
        while True:
            if con.in_waiting > 0:
                linea = con.readline().decode('utf-8', errors='ignore').strip()
                if linea:
                    print(f"[{time.strftime('%H:%M:%S')}] 📡 Recibido del sensor: '{linea}'")
            time.sleep(0.05)

except serial.SerialException as e:
    print(f"\n❌ Error abriendo {puerto}: {e}")
    print("Tip: Verifica que el Monitor Serie de Arduino IDE u otro programa no tenga tomado el puerto.")
except KeyboardInterrupt:
    print("\nLectura detenida por el usuario.")