document.addEventListener('DOMContentLoaded', async () => {
    
    // ==========================================
    // 1. CONTROLADOR DE VIDEO AVATAR (ESTADOS EXACTOS)
    // ==========================================
    const RANGOS_VIDEO = {
        IDLE:      { start: 0.0, end: 1.70 }, // Termina de moverse y se congela suave
        LISTENING: { start: 2.0, end: 3.70 }, 
        THINKING:  { start: 4.0, end: 5.70 }, 
        SPEAKING:  { start: 5.9, end: 9.80 }  
    };

    class VideoAvatarController {
        constructor(videoElementId) {
            this.video = document.getElementById(videoElementId);
            this.estadoActual = 'IDLE';
            this.rangoActual = RANGOS_VIDEO.IDLE;

            if (this.video) {
                this._init();
            }
        }

        _init() {
            this.video.addEventListener('timeupdate', () => {
                if (this.video.currentTime >= this.rangoActual.end && !this.video.paused) {
                    this.video.pause();
                }
            });

            this.video.addEventListener('loadedmetadata', () => {
                this.cambiarEstado('IDLE');
            });

            if (this.video.readyState >= 1) {
                this.cambiarEstado('IDLE');
            }
        }

        cambiarEstado(nuevoEstado) {
            if (!this.video || !RANGOS_VIDEO[nuevoEstado]) return;

            this.estadoActual = nuevoEstado;
            this.rangoActual = RANGOS_VIDEO[nuevoEstado];
            
            this.video.currentTime = this.rangoActual.start;
            this.video.play().catch(e => console.warn("Esperando interacción para video:", e));
        }
    }
    const avatarController = new VideoAvatarController('video-avatar');

    // ==========================================
    // 2. REFERENCIAS AL DOM Y VARIABLES GLOBALES
    // ==========================================
    const botonMic = document.getElementById('boton-microfono');
    const iconoMicNormal = document.getElementById('icono-mic-normal');
    const iconoMicOndas = document.getElementById('icono-mic-ondas');
    const iconoMicSpinner = document.getElementById('icono-mic-spinner');
    const textoMic = document.getElementById('texto-instruccion-mic');
    
    const bloqueBotonesExtra = document.getElementById('bloque-botones-extra');
    const respuestaVozContenedor = document.getElementById('respuesta-voz-contenedor');
    const textoUsuarioVoz = document.getElementById('texto-usuario-voz');
    const textoRespuestaVoz = document.getElementById('texto-respuesta-voz');
    const btnVolverVoz = document.getElementById('btn-volver-voz');

    let estaGrabando = false;
    let micBloqueadoCooldown = false;
    let idConsultaActual = 0;
    let idEscribiendoActual = 0;
    let abortControllerActual = null;
    let reproductorAudioActual = null;

    let mediaRecorder;
    let audioChunks = [];

    // ==========================================
    // 3. CONFIGURACIÓN DEL MICRÓFONO
    // ==========================================
    navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
    }).then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };
        mediaRecorder.onstop = procesarGrabacion;
    }).catch(err => {
        if (textoMic) textoMic.innerHTML = '❌ Sin acceso al micrófono';
    });

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    function reproducirBeep(tipo) {
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const oscilador = audioCtx.createOscillator();
        const ganancia = audioCtx.createGain();
        oscilador.connect(ganancia);
        ganancia.connect(audioCtx.destination);
        oscilador.type = 'sine';
        if (tipo === 'inicio') {
            oscilador.frequency.value = 1200; 
            ganancia.gain.setValueAtTime(0.1, audioCtx.currentTime);
            ganancia.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
            oscilador.start(audioCtx.currentTime);
            oscilador.stop(audioCtx.currentTime + 0.15);
        } else if (tipo === 'fin') {
            oscilador.frequency.value = 800; 
            ganancia.gain.setValueAtTime(0.1, audioCtx.currentTime);
            ganancia.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
            oscilador.start(audioCtx.currentTime);
            oscilador.stop(audioCtx.currentTime + 0.15);
        }
    }

    function cambiarEstadoMic(estado) {
        if (!botonMic) return;
        if (estado === 'escuchando') {
            botonMic.classList.add('estado-hablando');
            botonMic.classList.remove('estado-procesando');
            if (iconoMicNormal) iconoMicNormal.classList.add('oculto');
            if (iconoMicOndas) iconoMicOndas.classList.remove('oculto');
            if (iconoMicSpinner) iconoMicSpinner.classList.add('oculto');
            if (textoMic) textoMic.innerHTML = '<strong>Escuchando...</strong> (Toca para terminar)';
            avatarController.cambiarEstado('LISTENING');
        } else if (estado === 'procesando') {
            botonMic.classList.remove('estado-hablando');
            botonMic.classList.add('estado-procesando');
            if (iconoMicNormal) iconoMicNormal.classList.add('oculto');
            if (iconoMicOndas) iconoMicOndas.classList.add('oculto');
            if (iconoMicSpinner) iconoMicSpinner.classList.remove('oculto');
            if (textoMic) textoMic.textContent = 'Procesando tu consulta...';
            avatarController.cambiarEstado('THINKING');
        } else {
            botonMic.classList.remove('estado-hablando', 'estado-procesando');
            if (iconoMicNormal) iconoMicNormal.classList.remove('oculto');
            if (iconoMicOndas) iconoMicOndas.classList.add('oculto');
            if (iconoMicSpinner) iconoMicSpinner.classList.add('oculto');
            if (textoMic) textoMic.innerHTML = 'Toca el micrófono para hablar';
        }
    }

    function detenerAnimacionTexto() {
        idEscribiendoActual++; 
    }

    function alternarGrabacionVoz() {
        if (micBloqueadoCooldown) return;

        if (!estaGrabando) {
            estaGrabando = true;
            idConsultaActual++;
            detenerAnimacionTexto();

            if (reproductorAudioActual) {
                reproductorAudioActual.pause();
                reproductorAudioActual = null;
            }
            if (abortControllerActual) {
                abortControllerActual.abort();
                abortControllerActual = null;
            }
            fetch('/api/chat/stop', { method: 'POST' }).catch(() => {});

            if (bloqueBotonesExtra) bloqueBotonesExtra.classList.add('oculto');
            if (respuestaVozContenedor) respuestaVozContenedor.classList.remove('oculto');
            if (btnVolverVoz) btnVolverVoz.classList.remove('oculto');
            
            const rightPanel = document.querySelector('.right-panel');
            if (rightPanel) rightPanel.classList.add('modo-chat');
            
            if (document.querySelector('.user-bubble')) document.querySelector('.user-bubble').style.display = 'block';
            if (textoUsuarioVoz) textoUsuarioVoz.textContent = "Te escucho, habla ahora...";
            if (textoRespuestaVoz) textoRespuestaVoz.textContent = "";

            cambiarEstadoMic('escuchando');
            reproducirBeep('inicio');
            
            if (mediaRecorder && mediaRecorder.state === "inactive") {
                audioChunks = [];
                mediaRecorder.start();
            }
        } else {
            estaGrabando = false;
            micBloqueadoCooldown = true;
            setTimeout(() => { micBloqueadoCooldown = false; }, 400);

            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                reproducirBeep('fin');
            }
        }
    }

    function salirDeModoVoz() {
        idConsultaActual++; 
        detenerAnimacionTexto();

        if (reproductorAudioActual) {
            reproductorAudioActual.pause();
            reproductorAudioActual = null;
        }
        if (abortControllerActual) {
            abortControllerActual.abort();
            abortControllerActual = null;
        }
        estaGrabando = false;
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
        
        if (bloqueBotonesExtra) bloqueBotonesExtra.classList.remove('oculto');
        if (respuestaVozContenedor) respuestaVozContenedor.classList.add('oculto');
        if (btnVolverVoz) btnVolverVoz.classList.add('oculto');
        
        const rightPanel = document.querySelector('.right-panel');
        if (rightPanel) rightPanel.classList.remove('modo-chat');
        
        if (textoRespuestaVoz) textoRespuestaVoz.textContent = '';
        if (textoUsuarioVoz) textoUsuarioVoz.textContent = '';
        if (document.querySelector('.user-bubble')) document.querySelector('.user-bubble').style.display = 'none';

        cambiarEstadoMic('inactivo');
        avatarController.cambiarEstado('IDLE');
    }

    if (botonMic) {
        botonMic.addEventListener('pointerdown', (e) => {
            e.preventDefault();
            alternarGrabacionVoz();
        });
    }

    if (btnVolverVoz) {
        btnVolverVoz.addEventListener('pointerdown', (e) => {
            e.preventDefault();
            salirDeModoVoz();
        });
    }

    // ==========================================
    // 4. FLUJO DE PROCESAMIENTO Y LLM
    // ==========================================
    async function procesarGrabacion() {
        const idEstaConsulta = idConsultaActual;
        if (estaGrabando) return;

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = []; 

        if (audioBlob.size < 12000) {
            if (idEstaConsulta === idConsultaActual && !estaGrabando) {
                cambiarEstadoMic('inactivo');
                avatarController.cambiarEstado('IDLE');
            }
            return;
        }

        cambiarEstadoMic('procesando');
        
        if (abortControllerActual) abortControllerActual.abort();
        abortControllerActual = new AbortController();

        const formData = new FormData();
        formData.append('audio', audioBlob, 'grabacion.webm');

        try {
            const resAudio = await fetch('/api/audio/transcribe', {
                method: 'POST', body: formData, signal: abortControllerActual.signal
            });

            if (!resAudio.ok) throw new Error("Error en STT");
            if (idEstaConsulta !== idConsultaActual || estaGrabando) return;

            const dataAudio = await resAudio.json();
            const textoTranscrito = dataAudio.texto ? dataAudio.texto.trim() : "";

            if (!textoTranscrito) {
                if (idEstaConsulta === idConsultaActual && !estaGrabando) {
                    if (textoUsuarioVoz) textoUsuarioVoz.textContent = '"..."';
                    if (textoRespuestaVoz) textoRespuestaVoz.textContent = "No logré escucharte bien. Por favor intenta de nuevo.";
                    cambiarEstadoMic('inactivo');
                    avatarController.cambiarEstado('IDLE');
                }
                return;
            }

            detenerAnimacionTexto(); 
            if (textoUsuarioVoz) textoUsuarioVoz.textContent = `"${textoTranscrito}"`;
            if (textoRespuestaVoz) textoRespuestaVoz.textContent = "Pensando...";
            
            const payload = { 
                pregunta: textoTranscrito, 
                session_id: "kiosko_panoptico_1",
                sede: "panoptico" 
            };

            const resChat = await fetch('/api/chat/preguntar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: abortControllerActual.signal
            });

            if (!resChat.ok) throw new Error("Error en conexión");
            if (idEstaConsulta !== idConsultaActual || estaGrabando) return;

            if (textoRespuestaVoz) {
                const lector = resChat.body.getReader();
                const decodificador = new TextDecoder('utf-8');
                let respuestaCompleta = "";
                
                idEscribiendoActual++;
                const idEsteMensaje = idEscribiendoActual;

                while (true) {
                    const { done, value } = await lector.read();
                    if (idEstaConsulta !== idConsultaActual || idEsteMensaje !== idEscribiendoActual || estaGrabando) break; 
                    if (done) break;
                    respuestaCompleta += decodificador.decode(value, { stream: true });
                }

                if (idEstaConsulta === idConsultaActual && idEsteMensaje === idEscribiendoActual && !estaGrabando && respuestaCompleta.trim()) {
                    try {
                        const resTTS = await fetch('/api/audio/hablar', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ texto: respuestaCompleta }),
                            signal: abortControllerActual.signal
                        });

                        if (!resTTS.ok) throw new Error("Error en TTS");

                        const blobAudio = await resTTS.blob();
                        const urlAudio = URL.createObjectURL(blobAudio);
                        const reproductor = new Audio(urlAudio);
                        reproductorAudioActual = reproductor;

                        reproductor.onplay = async () => {
                            avatarController.cambiarEstado('SPEAKING'); 
                            textoRespuestaVoz.textContent = "";
                            const tokens = respuestaCompleta.split(/(\s+)/);
                            const duracionMs = (reproductor.duration && !isNaN(reproductor.duration)) ? (reproductor.duration * 1000) : (tokens.length * 100);
                            const retrasoToken = Math.max(60, Math.min(220, duracionMs / tokens.length));

                            for (let i = 0; i < tokens.length; i++) {
                                if (idEstaConsulta !== idConsultaActual || idEsteMensaje !== idEscribiendoActual || estaGrabando) break;
                                textoRespuestaVoz.textContent += tokens[i];
                                
                                // AUTO-SCROLL hacia abajo apuntando a la clase limpia
                                const contenedorChat = document.querySelector('.contenedor-dialogo-limpio');
                                if (contenedorChat) contenedorChat.scrollTop = contenedorChat.scrollHeight;

                                if (tokens[i].trim().length > 0) {
                                    await new Promise(r => setTimeout(r, retrasoToken));
                                }
                            }
                        };

                        await new Promise((resolve) => {
                            reproductor.onended = () => {
                                URL.revokeObjectURL(urlAudio);
                                reproductorAudioActual = null;
                                avatarController.cambiarEstado('IDLE'); 
                                resolve();
                            };
                            reproductor.onerror = () => {
                                URL.revokeObjectURL(urlAudio);
                                reproductorAudioActual = null;
                                avatarController.cambiarEstado('IDLE');
                                resolve();
                            };
                            reproductor.play().catch(() => resolve());
                        });

                    } catch (eAudio) {
                        textoRespuestaVoz.textContent = respuestaCompleta;
                        avatarController.cambiarEstado('IDLE');
                    }
                }
            }
            
            if (idEstaConsulta === idConsultaActual && !estaGrabando) {
                cambiarEstadoMic('inactivo');
                if (textoMic) textoMic.innerHTML = 'Toca el micrófono para hablar';
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                if (idEstaConsulta === idConsultaActual && !estaGrabando) {
                    if (textoRespuestaVoz) textoRespuestaVoz.textContent = "Lo siento, tuve un problema conectando con mi cerebro.";
                    cambiarEstadoMic('inactivo');
                    avatarController.cambiarEstado('IDLE');
                }
            }
        }
    }

    // ==========================================
    // 5. TECLADO FÍSICO Y TEMPORIZADOR
    // ==========================================
    document.addEventListener('keydown', (e) => {
        if (e.repeat) return;
        if (e.code === 'Space') {
            e.preventDefault();
            alternarGrabacionVoz();
            return;
        }
        if (['Escape', 'ArrowLeft'].includes(e.key)) {
            salirDeModoVoz();
        }
    });

    let temporizadorInactividad;
    const TIEMPO_MAXIMO_INACTIVIDAD = 60000;

    function resetearInactividad() {
        clearTimeout(temporizadorInactividad);
        temporizadorInactividad = setTimeout(() => {
            salirDeModoVoz();
        }, TIEMPO_MAXIMO_INACTIVIDAD);
    }

    document.addEventListener('pointerdown', resetearInactividad);
    document.addEventListener('keydown', resetearInactividad);
    resetearInactividad();
});