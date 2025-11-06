// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v26.0 (Modo Clásico Integrado) ==
// ===================================================================
// - COMPLETADO: Lógica para el Modo Clásico (Akinator) totalmente funcional.
// - MEJORADO: La función handleClassicAnswer ahora procesa preguntas y adivinanzas.
// - MANTIENE: Toda la funcionalidad del Modo Oráculo y Duelo 1v1.
// ===================================================================

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45, // Más rápido para una mejor experiencia de juego
    suggestionCooldown: 15000,
    suggestionLimit: 5,
    suggestionStart: 5,
    guessButtonCooldown: 15000
};

const phrases = {
    challenge: "Tu humilde tarea será adivinar el ser, real o ficticio, que yo, el Gran Oráculo, he concebido. Tienes 20 preguntas.",
    guessPopup: {
        initial: "La hora de la verdad se acerca... Escribe al ser que crees que estoy pensando, mortal.",
        strike1: "No puedo adivinar el vacío. ¡Escribe un nombre!",
        strike2: "¿Intentas agotar mi paciencia? Escribe una respuesta o cancela.",
        strike3: "Has agotado mi paciencia. El privilegio de adivinar te ha sido revocado... por ahora."
    },
    menuOracle: {
        main: "Una elección audaz. El telón se alza. Veamos qué camino eliges.",
        singlePlayer: "¿Un desafío solitario? Pretendes enfrentarte a la infinidad de mi mente sin ayuda... Interesante.",
        multiplayer: "Ah, buscas la compañía de otros mortales. ¿Para colaborar, o para traicionaros mutuamente? El tiempo lo dirá.",
        playOracle: "Así que quieres probar mi poder... Prepárate. He concebido un enigma que doblegará tu intelecto.",
        playClassic: "Prefieres que yo adivine, ¿eh? Muy bien. Piensa en tu personaje, mortal. Intentaré no aburrirme.",
        backToMenu: "¿Dudas? La incertidumbre es el primer paso hacia la ignorancia. Elige de nuevo."
    }
};

let state = {
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isAwaitingStartSignal: false,
    suggestionUses: config.suggestionLimit,
    lastSuggestionTimestamp: 0,
    guessPopupPatience: 3,
    currentGameMode: null,
    gameTimerInterval: null,
    gameTime: 0,
    socket: null,
    id_sala: null,
    rol_jugador: null,
    oponente_personaje: null,
};

// ===================================================================
// ===================================================================
// ==    CONEXIÓN CON SERVIDORES (Vercel + Render Architecture)   ==
// ===================================================================

// La URL de nuestra API de Python desplegada en Render.
// ¡IMPORTANTE! Pega aquí la URL exacta que te dio Render para tu Web Service.
const ALE_URL = '/api/execute';

// El servidor cooperativo de Replit no cambia.
const REPLIT_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:8080'
    : 'https://ce254311-0432-4d98-9904-395645c74498-00-37ujzri44dfx3.riker.replit.dev/';

console.log(`[CONFIG] URL del motor IA (ALE) establecida en: ${ALE_URL}`);
console.log(`[CONFIG] URL del servidor Cooperativo establecida en: ${REPLIT_URL}`);
// --- SELECTORES DEL DOM ---
const elements = {
    arcadeScreen: document.getElementById('arcade-screen'),
    screens: { title: document.getElementById('title-screen'), stage: document.getElementById('game-stage'), mainGame: document.getElementById('main-game-screen'), win: document.getElementById('win-screen'), lose: document.getElementById('lose-screen') },
    header: {
        container: document.querySelector('.game-header'),
        timer: document.getElementById('timer'),
        questionCounter: document.getElementById('question-counter'),
        backToMenu: document.getElementById('back-to-menu-button')
    },
    title: { layout: document.getElementById('title-layout'), introBrain: document.getElementById('intro-brain'), startButton: document.getElementById('start-button'), exitButton: document.getElementById('exit-button'), lightning: document.getElementById('lightning-overlay') },
    stage: { lights: document.getElementById('stage-lights'), content: document.getElementById('stage-content-container'), curtainLeft: document.getElementById('curtain-left'), curtainRight: document.getElementById('curtain-right'), brain: document.getElementById('stage-brain'), dialog: document.getElementById('stage-dialog'), menuButtons: document.getElementById('menu-buttons') },
    game: {
        chatHistory: document.getElementById('chat-history'),
        input: document.getElementById('user-question-input'),
        askButton: document.getElementById('ask-button'),
        suggestionButton: document.getElementById('suggestion-button'),
        guessButton: document.getElementById('guess-button'),
        oracleControls: document.getElementById('oracle-mode-controls'),
        classicControls: document.getElementById('classic-mode-controls'),
        dueloOraculoControls: document.getElementById('duelo-oraculo-controls')
    },
    popups: {
        guess: document.getElementById('guess-popup'),
        suggestion: document.getElementById('suggestion-popup'),
        dueloConfig: document.getElementById('duelo-config-popup'),
        customAnswer: document.getElementById('custom-answer-popup')
    },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { container: document.getElementById('suggestion-popup'), content: document.querySelector('#suggestion-popup .popup-content'), buttonsContainer: document.getElementById('suggestion-buttons-container') },
    customAnswer: {
        input: document.getElementById('custom-answer-input'),
        confirmButton: document.getElementById('confirm-custom-answer-button')
    },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: {}
};

// ===================================================================
// ===                LÓGICA MULTIJUGADOR (SIN CAMBIOS)            ===
// ===================================================================

function conectarAlServidorDeDuelo() {
    try {
        state.socket = io(REPLIT_URL, {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });
        console.log("Intentando conectar al servidor de duelo en:", REPLIT_URL);

        state.socket.on('connect', () => {
            console.log("✅ ¡Conectado al servidor de duelo! ID de Socket:", state.socket.id);
        });

        state.socket.on('duelo_creado', (data) => {
            state.id_sala = data.id_sala;
            const linkDuelo = `${window.location.origin}${window.location.pathname}?duelo=${state.id_sala}`;
            const dialogText = `¡Duelo creado! Comparte este link con tu amigo: <br><br><input type="text" value="${linkDuelo}" style="width: 100%; text-align: center;" readonly onclick="this.select()"><br><br>Esperando oponente...`;
            typewriterEffect(elements.stage.dialog, dialogText);
            elements.stage.menuButtons.classList.add('hidden');
        });

        state.socket.on('partida_iniciada', (data) => {
            console.log("✅ Partida iniciada por el servidor. Configurando rol:", data.rol);
            state.rol_jugador = data.rol;
            config.questionsLimit = data.reglas.limitePreguntas || 20;
            startGame('duelo_1v1');
        });

        state.socket.on('pregunta_recibida', (data) => {
            addMessageToChat(data.pregunta, 'brain');
            state.questionCount++;
            elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            if (state.rol_jugador === 'oraculo') {
                elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = false);
            }
        });

        state.socket.on('respuesta_recibida', (data) => {
            addMessageToChat(data.respuesta, 'brain');
            if (state.rol_jugador === 'adivino') {
                if (state.questionCount < config.questionsLimit) {
                    elements.game.input.disabled = false;
                    elements.game.askButton.disabled = false;
                    elements.game.input.focus();
                } else {
                    addMessageToChat("Has agotado tus preguntas. ¡Debes adivinar!", "system");
                    elements.game.guessButton.disabled = false;
                }
            }
        });

        state.socket.on('adivinanza_recibida', (data) => {
            if (state.rol_jugador === 'oraculo') {
                const esCorrecto = confirm(`Tu oponente cree que el personaje es: "${data.adivinanza}". ¿Es correcto?`);
                state.socket.emit('resultado_adivinanza', {
                    id_sala: state.id_sala,
                    resultado: esCorrecto ? 'victoria' : 'derrota',
                    personaje: esCorrecto ? data.adivinanza : state.oponente_personaje
                });
            }
        });

        state.socket.on('fin_del_juego', (data) => {
            const ganoElAdivino = data.resultado === 'victoria';
            const esVictoriaParaMi = (state.rol_jugador === 'adivino') ? ganoElAdivino : !ganoElAdivino;
            endGame(esVictoriaParaMi, "guess_multiplayer", data.personaje);
        });

        state.socket.on('error_sala', (data) => {
            alert(data.mensaje);
            window.location.href = window.location.origin + window.location.pathname;
        });

        state.socket.on('oponente_desconectado', (data) => {
            if (state.isGameActive) {
                alert(data.mensaje);
                endGame(false, "disconnect");
            }
        });

    } catch (e) {
        console.error("Error al inicializar Socket.IO:", e);
        // No hacer nada si el servidor no está disponible, para que el modo single player funcione.
    }
}


function iniciarCreacionDuelo(opciones) {
    if (!state.socket || !state.socket.connected) {
        alert("No se pudo conectar al servidor multijugador. Revisa la URL y si está online.");
        showGameStage(false);
        return;
    }

    state.socket.emit('crear_duelo', {
        reglas: opciones.reglas,
        rolAnfitrion: opciones.rolSeleccionado
    });

    typewriterEffect(elements.stage.dialog, "Creando duelo personalizado en el cosmos...");
    elements.stage.menuButtons.classList.add('hidden');
}


function unirseADuelo(id_duelo) {
    if (!state.socket || !state.socket.connected) {
        setTimeout(() => unirseADuelo(id_duelo), 1000);
        return;
    }

    state.id_sala = id_duelo;
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    elements.stage.dialog.innerHTML = "Conectando al servidor de duelos...";
    elements.stage.dialog.classList.remove('hidden');
    elements.stage.menuButtons.classList.add('hidden');
    state.socket.emit('unirse_a_duelo', { id_sala: id_duelo });
}


// ===================================================================
// ==         LÓGICA PRINCIPAL DEL JUEGO (INICIO Y RESET)         ==
// ===================================================================

// --- REEMPLAZA ESTA FUNCIÓN EN SCRIPT.JS ---

function resetGameState() {
    // Restablece todas las variables de estado del juego a sus valores iniciales.
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isAwaitingBrainResponse = false;
    state.suggestionUses = config.suggestionLimit;
    state.lastSuggestionTimestamp = 0;
    state.guessPopupPatience = 3;
    state.gameTime = 0;
    state.rol_jugador = null;
    state.id_sala = null;
    state.oponente_personaje = null;
    state.isSecondChance = false; // ¡Importante! Reseteamos el estado de segunda oportunidad.
    
    // Limpia el temporizador y las clases de la interfaz.
    clearInterval(state.gameTimerInterval);
    document.body.classList.remove('rol-adivino', 'rol-oraculo');
    elements.header.timer.textContent = "00:00";
    elements.header.questionCounter.textContent = `0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;

    // --- ¡NUEVA LÓGICA DE LIMPIEZA PROFUNDA! ---
    // Exorcizamos los eventos "onclick" fantasmas de los pop-ups.
    const confirmGuessPopup = document.getElementById('confirm-guess-popup');
    if (confirmGuessPopup) {
        document.getElementById('confirm-guess-yes').onclick = null;
        document.getElementById('confirm-guess-no').onclick = null;
        confirmGuessPopup.classList.add('hidden');
    }
    const clarificationPopup = document.getElementById('clarification-popup');
    if (clarificationPopup) {
        document.getElementById('send-with-clarification').onclick = null;
        document.getElementById('send-without-clarification').onclick = null;
        clarificationPopup.classList.add('hidden');
    }
    // --- FIN DE LA NUEVA LÓGICA ---
}


async function startGame(mode) {
    state.currentGameMode = mode;

    closeCurtains(async () => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');

        resetGameState();
        state.isGameActive = true;

        // Lógica de preparación de interfaz
        if (mode === 'duelo_1v1') {
            prepararInterfazDuelo();
        } else if (mode === 'oracle_ia') {
            await prepararInterfazModoOraculoIA();
        } else if (mode === 'classic_ia') {
            await prepararInterfazModoClasicoIA(); // ¡MODIFICADO! Ahora es una función asíncrona
        }

        startTimer();
    }, 1);
}
// ===================================================================
// == SCRIPT.JS - PARTE 2/2 (Lógica de Modos de Juego y UI)         ==
// ===================================================================

function prepararInterfazDuelo() {
    document.body.classList.remove('rol-adivino', 'rol-oraculo');
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.add('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.header.questionCounter.classList.remove('hidden');
    elements.header.questionCounter.textContent = `0/${config.questionsLimit}`;

    if (state.rol_jugador === 'adivino') {
        document.body.classList.add('rol-adivino');
        elements.game.oracleControls.classList.remove('hidden');
        elements.game.suggestionButton.classList.add('hidden');
        elements.game.guessButton.classList.remove('hidden');
        elements.game.guessButton.disabled = false;
        addMessageToChat("Eres el Adivino. Tu oponente es el Oráculo. Haz tu primera pregunta.", 'system');
    } else if (state.rol_jugador === 'oraculo') {
        document.body.classList.add('rol-oraculo');
        state.oponente_personaje = prompt("Eres el Oráculo. Piensa en un ser, real o ficticio, y escribe su nombre aquí. Tu oponente no lo verá.");
        if (!state.oponente_personaje || state.oponente_personaje.trim() === "") {
            alert("Debes elegir un personaje. La página se recargará.");
            window.location.reload();
            return;
        }
        elements.game.dueloOraculoControls.classList.remove('hidden');
        addMessageToChat(`Eres el Oráculo. Has elegido a "${state.oponente_personaje}". Espera la pregunta de tu oponente.`, 'system');
        elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
    }
}

async function handlePlayerInput() {
    const inputText = elements.game.input.value.trim();
    if (inputText === '' || !state.isGameActive || state.isAwaitingBrainResponse) return;

    // --- LÓGICA PARA EL INICIO DEL MODO CLÁSICO ---
    if (state.currentGameMode === 'classic_ia' && state.isAwaitingStartSignal) {
        const startWords = ['listo', 'ya', 'comienza', 'dale', 'ok', 'empieza'];
        if (startWords.includes(inputText.toLowerCase())) {
            state.isAwaitingStartSignal = false;
            addMessageToChat(inputText, 'player');
            elements.game.input.value = '';
            elements.game.input.disabled = true;
            elements.game.askButton.disabled = true;

            addMessageToChat("Excelente. Mi mente se agudiza... Aquí voy.", 'brain', async () => {
                const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
                
                elements.game.oracleControls.classList.add('hidden');
                elements.game.classicControls.classList.remove('hidden');
                elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);
                elements.header.questionCounter.classList.remove('hidden');
                elements.header.questionCounter.textContent = `1/${config.questionsLimit}`;
                state.questionCount = 1;

                if (respuesta && respuesta.accion === "Preguntar") {
                    addMessageToChat(respuesta.texto, 'brain');
                } else {
                    addMessageToChat("Mi mente se ha atascado al empezar. Intenta reiniciar el juego.", 'brain');
                }
            });
        } else {
            addMessageToChat("No entiendo esa señal. Por favor, escribe 'Listo' cuando estés preparado.", 'system');
            elements.game.input.value = '';
        }
        return; 
    }

    // Lógica para Duelo 1v1
    if (state.currentGameMode === 'duelo_1v1' && state.rol_jugador === 'adivino') {
        addMessageToChat(inputText, 'player');
        state.socket.emit('enviar_pregunta', { id_sala: state.id_sala, pregunta: inputText });
        elements.game.input.value = '';
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        return;
    } 
    
    // Lógica para Oráculo vs IA
    if (state.currentGameMode === 'oracle_ia') {
        state.isAwaitingBrainResponse = true;
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        
        addMessageToChat(inputText, 'player');
        elements.game.input.value = '';

        // --- LÍNEAS DE PRUEBA PARA DEPURACIÓN ---
        console.log("--- DEBUGGING PAYLOAD ---");
        console.log("Enviando la pregunta:", inputText);
        console.log("Enviando el dossier:", state.secretCharacter);
        // ------------------------------------

        const respuesta = await callALE({ 
            skillset_target: "oracle", 
            accion: "procesar_pregunta", 
            pregunta: inputText,
            dossier_personaje: state.secretCharacter,
            memoria: state.memoria_largo_plazo || {} 
        });
        
        state.isAwaitingBrainResponse = false;

        if (!respuesta || respuesta.error) {
            addMessageToChat("El Oráculo parece distraído. Inténtalo de nuevo.", 'system');
        } else {
            if (respuesta.castigo === 'meta_pregunta') {
                addMessageToChat(respuesta.respuesta, 'brain');
            } else {
                const fullResponse = `${respuesta.respuesta} ${respuesta.aclaracion || ''}`.trim();
                addMessageToChat(fullResponse, 'brain');
                
                if (respuesta.respuesta === "Sí." || respuesta.respuesta === "No.") {
                    if (!state.memoria_largo_plazo) state.memoria_largo_plazo = {};
                    state.memoria_largo_plazo[inputText] = respuesta.respuesta;
                }

                state.questionCount++;
                elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            }
        }

        if (state.isGameActive) {
            elements.game.input.disabled = false;
            elements.game.askButton.disabled = false;
            elements.game.input.focus();
        }

        if (state.isGameActive && state.questionCount >= config.questionsLimit) {
            addMessageToChat("Has agotado tus preguntas. ¡Debes adivinar!", "system");
            elements.game.input.disabled = true;
            elements.game.askButton.disabled = true;
        }
        return;
    }
}



function handleDueloOraculoResponse(respuesta) {
    state.socket.emit('enviar_respuesta', { id_sala: state.id_sala, respuesta: respuesta });
    elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
}

document.addEventListener('DOMContentLoaded', () => {
    adjustScreenHeight();
    window.addEventListener('resize', adjustScreenHeight);
    conectarAlServidorDeDuelo();

    const urlParams = new URLSearchParams(window.location.search);
    const id_duelo = urlParams.get('duelo');
    if (id_duelo) {
        unirseADuelo(id_duelo);
    } else {
        runTitleSequence();
    }

    // --- MANEJADORES DE EVENTOS GLOBALES ---
    elements.title.startButton.addEventListener('click', () => showGameStage(true));
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.header.backToMenu.addEventListener('click', () => {
        window.location.href = window.location.origin + window.location.pathname;
    });

    // --- NAVEGACIÓN POR MENÚS ---
    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (!action) return;
        elements.stage.menuButtons.classList.add('hidden');

        const menuActions = {
            'show-single-player': () => typewriterEffect(elements.stage.dialog, phrases.menuOracle.singlePlayer, () => {
                // ¡SOLUCIÓN BLINDADA! Usamos onclick directamente en los botones.
                elements.stage.menuButtons.innerHTML = `<button class="menu-button button-green" onclick="showChallengeScreen()">Modo Oráculo (vs IA)</button><button class="menu-button button-green" onclick="showClassicChallengeScreen()">Modo Clásico (vs IA)</button><div style="height: 15px;"></div><button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>`;
                elements.stage.menuButtons.classList.remove('hidden');
            }),
            'show-multiplayer': () => typewriterEffect(elements.stage.dialog, phrases.menuOracle.multiplayer, () => {
                elements.stage.menuButtons.innerHTML = `<button class="menu-button button-purple" data-action="create-duel-1v1">1 vs 1</button><button class="menu-button button-purple" data-action="create-duel-varios" disabled>1 vs Varios (Próx)</button><div style="height: 15px;"></div><button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>`;
                elements.stage.menuButtons.classList.remove('hidden');
            }),
            'back-to-main-menu': () => typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu, showFinalMenu),
            
            // Las acciones de los botones de desafío SÍ las mantenemos aquí.
            'accept-challenge': () => startGame('oracle_ia'),
            'accept-classic-challenge': () => startGame('classic_ia'),

            // --- OTRAS ACCIONES ---
            'flee-to-title': runTitleSequence,
            'flee-challenge': () => showGameStage(false),
            'create-duel-1v1': () => elements.popups.dueloConfig.classList.remove('hidden')
        };

        // El listener principal sigue funcionando para las acciones que no están en onclick.
        if (menuActions[action]) {
            menuActions[action]();
        }
    });

    // --- MANEJADORES DE CONTROLES DE JUEGO Y POP-UPS ---

    // --- MANEJADORES DE CONTROLES DE JUEGO Y POP-UPS ---

    elements.game.dueloOraculoControls.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.answer) {
            handleDueloOraculoResponse(e.target.dataset.answer);
        }
    });
    
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') showGameStage(true);
            else if (action === 'main-menu') runTitleSequence();
        });
    });
    
    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) e.target.closest('.popup-overlay').classList.add('hidden'); });
    
    // Configuración de Duelo
    const dueloConfigPopup = document.getElementById('duelo-config-popup');
    dueloConfigPopup.querySelector('#rol-selector').addEventListener('click', (e) => {
        if (e.target.classList.contains('rol-btn')) {
            dueloConfigPopup.querySelectorAll('.rol-btn').forEach(btn => btn.classList.remove('selected'));
            e.target.classList.add('selected');
        }
    });
    dueloConfigPopup.addEventListener('click', (e) => {
        if (e.target.classList.contains('stepper-btn')) {
            const targetInput = document.getElementById(e.target.dataset.target);
            const op = e.target.dataset.op;
            const step = parseInt(targetInput.step) || 1;
            let value = parseInt(targetInput.value);
            if (op === 'plus') value += step;
            else value -= step;
            const min = parseInt(targetInput.min);
            const max = parseInt(targetInput.max);
            if (value >= min && value <= max) targetInput.value = value;
        }
    });
    document.getElementById('confirm-duelo-button').addEventListener('click', () => {
        const reglas = {
            limitePreguntas: parseInt(document.getElementById('limite-preguntas-input').value),
            intentosAdivinar: parseInt(document.getElementById('intentos-adivinar-input').value)
        };
        const rolSeleccionado = document.querySelector('#rol-selector .rol-btn.selected').dataset.rol;
        dueloConfigPopup.classList.add('hidden');
        iniciarCreacionDuelo({ reglas, rolSeleccionado });
    });
    
    // Pop-up de Adivinar (Modo Oráculo)
    elements.game.guessButton.addEventListener('click', () => {
        elements.popups.guess.classList.remove('hidden');
        elements.guessPopup.input.focus();
    });
    elements.guessPopup.confirmButton.addEventListener('click', async () => {
        const guessText = elements.guessPopup.input.value.trim();
        if (guessText === '') return;
        elements.popups.guess.classList.add('hidden');
        if (state.currentGameMode === 'duelo_1v1') {
            state.socket.emit('enviar_adivinanza', { id_sala: state.id_sala, adivinanza: guessText });
            addMessageToChat(`Has intentado adivinar: ${guessText}. Esperando veredicto del Oráculo.`, 'system');
        } else {
            const respuesta = await callALE({
                skillset_target: "oracle",
                accion: "verificar_adivinanza",
                adivinanza: guessText,
                dossier_personaje: state.secretCharacter // Enviamos el dossier para la verificación
            });
            endGame(respuesta.resultado === "victoria", "guess", respuesta.personaje_secreto);
        }
    });
    
    // Pop-up de Sugerencia (Modo Oráculo) - VERSIÓN BLINDADA
    elements.game.suggestionButton.addEventListener('click', async () => {
        // --- PASO 1: VERIFICACIÓN DE BLOQUEO ---
        // Si ya se está esperando una respuesta del cerebro, no hacemos NADA.
        if (state.isAwaitingBrainResponse) {
            console.log("BLOQUEADO: Ya se está procesando una petición. Se ignora el clic duplicado.");
            return; 
        }

        // --- PASO 2: ACTIVAR EL BLOQUEO ---
        // Levantamos la bandera para bloquear clics futuros y actualizamos la UI.
        state.isAwaitingBrainResponse = true; 
        elements.game.suggestionButton.disabled = true;
        elements.game.suggestionButton.textContent = "Pensando...";

        try { // Usamos try...finally para asegurarnos de que el bloqueo SIEMPRE se libere.
            const respuesta = await callALE({ 
                skillset_target: "oracle", 
                accion: "pedir_sugerencia",
                dossier_personaje: state.secretCharacter,
                memoria: state.memoria_largo_plazo || {}
            });

            if (respuesta && respuesta.sugerencias && respuesta.sugerencias.length > 0) {
                state.suggestionUses--; // Solo descontamos si hay éxito
                const container = elements.suggestionPopup.buttonsContainer;
                container.innerHTML = '';
                respuesta.sugerencias.forEach(sug => {
                    const btn = document.createElement('button');
                    btn.className = 'suggestion-option-button';
                    btn.textContent = sug;
                    btn.onclick = () => {
                        elements.game.input.value = sug;
                        elements.popups.suggestion.classList.add('hidden');
                        elements.game.input.focus();
                    };
                    container.appendChild(btn);
                });
                elements.popups.suggestion.classList.remove('hidden');
            } else {
                addMessageToChat("El Oráculo no puede ofrecer sugerencias en este momento.", "system");
            }

        } catch (error) {
            console.error("Error al pedir sugerencia:", error);
            addMessageToChat("Hubo un error de conexión al pedir la sugerencia.", "system");
        } finally {
            // --- PASO 3: LIBERAR EL BLOQUEO ---
            // Haya éxito o fracaso, bajamos la bandera y actualizamos la UI.
            state.isAwaitingBrainResponse = false; 
            elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
            if (state.suggestionUses > 0 && state.isGameActive) {
                elements.game.suggestionButton.disabled = false;
            }
        }
    });

    
    // Pop-up de Respuesta Mística (Duelo)
    document.getElementById('custom-answer-button').addEventListener('click', () => {
        elements.popups.customAnswer.classList.remove('hidden');
        elements.customAnswer.input.focus();
    });
    elements.customAnswer.confirmButton.addEventListener('click', () => {
        const customAnswerText = elements.customAnswer.input.value.trim();
        if (customAnswerText === '') return;
        handleDueloOraculoResponse(customAnswerText);
        elements.customAnswer.input.value = '';
        elements.popups.customAnswer.classList.add('hidden');
    });
    
    // Modo Clásico (vs IA) - CON LÓGICA DE ACLARACIÓN
    elements.game.classicControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('answer-btn')) {
            const answer = e.target.dataset.answer;
            const ambiguousAnswers = ["Probablemente Sí", "Probablemente No", "No lo sé"];
            
            if (ambiguousAnswers.includes(answer)) {
                const popup = document.getElementById('clarification-popup');
                document.getElementById('clarification-base-answer').textContent = answer;
                const input = document.getElementById('clarification-input');
                input.value = '';
                popup.classList.remove('hidden');
                input.focus();
                
                document.getElementById('send-with-clarification').onclick = () => {
                    const clarificationText = input.value.trim();
                    const fullAnswer = clarificationText ? `${answer}. ${clarificationText}` : answer;
                    handleClassicAnswer(fullAnswer);
                    popup.classList.add('hidden');
                };
                
                document.getElementById('send-without-clarification').onclick = () => {
                    handleClassicAnswer(answer);
                    popup.classList.add('hidden');
                };
                
            } else {
                handleClassicAnswer(answer);
            }
        }
    });
    // --- MANEJADORES DE CONTROLES DE JUEGO Y POP-UPS ---
    elements.game.dueloOraculoControls.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.answer) {
            handleDueloOraculoResponse(e.target.dataset.answer);
        }
    });

    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') showGameStage(true);
            else if (action === 'main-menu') runTitleSequence();
        });
    });

    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) e.target.closest('.popup-overlay').classList.add('hidden'); });

    dueloConfigPopup.addEventListener('click', (e) => {
        if (e.target.classList.contains('stepper-btn')) {
            const targetInput = document.getElementById(e.target.dataset.target);
            const op = e.target.dataset.op;
            const step = parseInt(targetInput.step) || 1;
            let value = parseInt(targetInput.value);
            if (op === 'plus') value += step; else value -= step;
            const min = parseInt(targetInput.min);
            const max = parseInt(targetInput.max);
            if (value >= min && value <= max) targetInput.value = value;
        }
    });
    document.getElementById('confirm-duelo-button').addEventListener('click', () => {
        const reglas = {
            limitePreguntas: parseInt(document.getElementById('limite-preguntas-input').value),
            intentosAdivinar: parseInt(document.getElementById('intentos-adivinar-input').value)
        };
        const rolSeleccionado = document.querySelector('#rol-selector .rol-btn.selected').dataset.rol;
        dueloConfigPopup.classList.add('hidden');
        iniciarCreacionDuelo({ reglas, rolSeleccionado });
    });

    // Pop-up de Adivinar (Modo Oráculo)
    elements.game.guessButton.addEventListener('click', () => {
        elements.popups.guess.classList.remove('hidden');
        elements.guessPopup.input.focus();
    });
    elements.guessPopup.confirmButton.addEventListener('click', async () => {
        const guessText = elements.guessPopup.input.value.trim();
        if (guessText === '') return;
        elements.popups.guess.classList.add('hidden');
        if (state.currentGameMode === 'duelo_1v1') {
            state.socket.emit('enviar_adivinanza', { id_sala: state.id_sala, adivinanza: guessText });
            addMessageToChat(`Has intentado adivinar: ${guessText}. Esperando veredicto del Oráculo.`, 'system');
        } else {
            const respuesta = await callALE({ skillset_target: "oracle", accion: "verificar_adivinanza", adivinanza: guessText });
            endGame(respuesta.resultado === "victoria", "guess", respuesta.personaje_secreto);
        }
    });

    // Pop-up de Respuesta Mística (Duelo)
    document.getElementById('custom-answer-button').addEventListener('click', () => {
        elements.popups.customAnswer.classList.remove('hidden');
        elements.customAnswer.input.focus();
    });
    elements.customAnswer.confirmButton.addEventListener('click', () => {
        const customAnswerText = elements.customAnswer.input.value.trim();
        if (customAnswerText === '') return;
        handleDueloOraculoResponse(customAnswerText);
        elements.customAnswer.input.value = '';
        elements.popups.customAnswer.classList.add('hidden');
    });

    // ¡MODIFICADO! Manejador para los botones del Modo Clásico
// --- REEMPLAZA ESTA SECCIÓN EN SCRIPT.JS ---

    // Modo Clásico (vs IA) - CON LÓGICA DE ACLARACIÓN
    elements.game.classicControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('answer-btn')) {
            const answer = e.target.dataset.answer;
            const ambiguousAnswers = ["Probablemente Sí", "Probablemente No", "No lo sé"];

            if (ambiguousAnswers.includes(answer)) {
                // Es una respuesta ambigua, mostramos el pop-up
                const popup = document.getElementById('clarification-popup');
                document.getElementById('clarification-base-answer').textContent = answer;
                const input = document.getElementById('clarification-input');
                input.value = ''; // Limpiamos el input
                popup.classList.remove('hidden');
                input.focus();

                // Manejador para enviar CON aclaración
                document.getElementById('send-with-clarification').onclick = () => {
                    const clarificationText = input.value.trim();
                    const fullAnswer = clarificationText ? `${answer}. ${clarificationText}` : answer;
                    handleClassicAnswer(fullAnswer);
                    popup.classList.add('hidden');
                };

                // Manejador para enviar SIN aclaración
                document.getElementById('send-without-clarification').onclick = () => {
                    handleClassicAnswer(answer);
                    popup.classList.add('hidden');
                };

            } else {
                // Es una respuesta directa (Sí/No), la manejamos como siempre
                handleClassicAnswer(answer);
            }
        }
    });

}); // <-- ¡ESTA ES LA LLAVE CRUCIAL QUE PROBABLEMENTE FALTA!

async function callALE(payload) {
    try {
        const response = await fetch(ALE_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error al llamar a A.L.E.:", error);
        addMessageToChat(`Error de conexión con el cerebro. ${error.message}`, 'system');
        return { error: true };
    }
}

// Reemplaza esta función en tu script.js

async function prepararInterfazModoOraculoIA() {
    elements.game.oracleControls.classList.remove('hidden');
    elements.game.classicControls.classList.add('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.game.suggestionButton.classList.remove('hidden');
    elements.game.guessButton.classList.remove('hidden');
    elements.header.questionCounter.classList.remove('hidden');
    addMessageToChat("Concibiendo un nuevo enigma...", "brain");

    // La llamada a la API no cambia
    const respuesta = await callALE({ skillset_target: "oracle", accion: "iniciar_juego" });

    // --- ¡AQUÍ ESTÁ LA CORRECCIÓN CLAVE! ---
    // Verificamos si la respuesta es válida y si contiene el personaje secreto
    if (!respuesta || respuesta.error || !respuesta.personaje_secreto) {
        addMessageToChat("El Oráculo no responde. Las estrellas guardan silencio. Por favor, vuelve al menú.", "system");
        state.isGameActive = false;
        return;
    }

    // Guardamos el personaje secreto en el estado del frontend
    state.secretCharacter = respuesta.personaje_secreto;
    
    // Limpiamos el historial y mostramos el mensaje de inicio
    elements.game.chatHistory.innerHTML = '';
    addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.suggestionButton.disabled = false;
        elements.game.guessButton.disabled = false;
        elements.game.input.focus();
    });
}

// ¡COMPLETADO! Lógica para iniciar el Modo Clásico
// --- REEMPLAZA ESTA FUNCIÓN EN SCRIPT.JS ---

// --- REEMPLAZA ESTA FUNCIÓN EN SCRIPT.JS ---

async function prepararInterfazModoClasicoIA() {
    // Prepara la interfaz básica
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.remove('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.game.suggestionButton.classList.add('hidden');
    elements.game.guessButton.classList.add('hidden');
    elements.header.questionCounter.classList.remove('hidden');
    
    // Muestra un mensaje de carga mientras espera la primera pregunta
    addMessageToChat("Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas.", 'brain');
    
    // Llama al backend para obtener la primera pregunta
    const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });

    if (respuesta && respuesta.accion === "Preguntar") {
        addMessageToChat(respuesta.texto, 'brain');
        state.questionCount = 1;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
    } else {
        addMessageToChat("Mi mente está confusa. Vuelve al menú e inténtalo de nuevo.", 'brain');
        elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = true);
    }
}



// =================================================================================
// == ¡NUEVO BLOQUE DE CÓDIGO PARA EL MODO CLÁSICO ORGÁNICO! ==
// Reemplaza tu antigua función handleClassicAnswer con este bloque completo.
// =================================================================================

/**
 * Maneja la respuesta del jugador en el Modo Clásico.
 * Si la respuesta es ambigua ("Probablemente Sí/No"), abre un pop-up para que el jugador aclare.
 * @param {string} answer - La respuesta seleccionada por el jugador desde el botón.
 */
// =================================================================================
// == ¡NUEVO BLOQUE DE CÓDIGO PARA EL MODO CLÁSICO ORGÁNICO! ==
// Contiene la lógica para manejar las respuestas y las aclaraciones del jugador.
// =================================================================================

/**
// =================================================================================
// == ¡VERSIÓN FINAL DE LA LÓGICA DE ACLARACIONES! ==
// Muestra la respuesta completa del jugador en una sola línea en el chat.
// =================================================================================

/**
 * Maneja la respuesta del jugador en el Modo Clásico.
 * Construye y muestra la respuesta completa con aclaración en una sola línea.
 * @param {string} answer - La respuesta seleccionada por el jugador.**/
 
async function handleClassicAnswer(answer) {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    state.isAwaitingBrainResponse = true;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = true);
    addMessageToChat(answer, 'player');

    const payload = {
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: answer,
        estado_juego: {
            es_segunda_oportunidad: state.isSecondChance || false,
            limite_preguntas: config.questionsLimit
        }
    };

    const respuesta = await callALE(payload);
    state.isAwaitingBrainResponse = false;

    if (!respuesta || respuesta.error || !respuesta.accion) {
        addMessageToChat("Mi mente se ha nublado... No puedo continuar. Has ganado esta vez.", 'brain');
        endGame(true, "classic_lose");
        return;
    }

    let esAdivinanzaDisfrazada = false;
    let nombrePersonajeAdivinado = "";

    if (respuesta.accion === "Preguntar") {
        const match = respuesta.texto.match(/¿(?:tu personaje es|es)\s+([A-ZÁÉÍÓÚ][\w\s.'-]*?)\?/i);
        if (match && match[1]) {
            const possibleName = match[1].trim();
            const commonWords = ['un ', 'una ', 'el ', 'la ', 'de '];
            if (!commonWords.some(word => possibleName.toLowerCase().startsWith(word)) && possibleName.length < 50) {
                esAdivinanzaDisfrazada = true;
                nombrePersonajeAdivinado = possibleName;
            }
        }
    }

    if (respuesta.accion !== "Adivinar" && !esAdivinanzaDisfrazada) {
        elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);
    }

    if (respuesta.accion === "Adivinar" || esAdivinanzaDisfrazada) {
        const characterName = esAdivinanzaDisfrazada ? nombrePersonajeAdivinado : respuesta.texto;
        if (esAdivinanzaDisfrazada) {
            addMessageToChat(`He llegado a una conclusión... Creo que estás pensando en... **${characterName}**.`, 'brain');
        }
        document.getElementById('confirm-guess-character').textContent = characterName;
        const popup = document.getElementById('confirm-guess-popup');
        popup.classList.remove('hidden');
        document.getElementById('confirm-guess-yes').onclick = () => {
            popup.classList.add('hidden');
            addMessageToChat(`¡He acertado! Sabía que era ${characterName}.`, 'brain');
            endGame(false, "classic_win");
        };
        document.getElementById('confirm-guess-no').onclick = () => {
            popup.classList.add('hidden');
            if (state.isSecondChance) {
                addMessageToChat(`¡Vaya! He fallado de nuevo. Me rindo. Tú ganas.`, 'brain');
                endGame(true, "classic_lose");
            } else {
                state.isSecondChance = true;
                const preguntasExtra = Math.floor(Math.random() * 6) + 5;
                config.questionsLimit += preguntasExtra;
                addMessageToChat(`¡Maldición! Estaba seguro. De acuerdo, me concentraré más. Ahora tengo ${config.questionsLimit} preguntas en total.`, 'brain');
                elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
                elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);
                handleClassicAnswer(`No, no es ${characterName}`);
            }
        };

    } else if (respuesta.accion === "Preguntar") {
        addMessageToChat(respuesta.texto, 'brain');
        state.questionCount++;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;

    // --- ¡NUEVA LÓGICA PARA MANEJAR EL COMENTARIO! ---
    } else if (respuesta.accion === "Comentar_y_Preguntar") {
        // Primero muestra el comentario...
        addMessageToChat(respuesta.comentario, 'brain', () => {
            // ...y una vez que termina de escribirse, muestra la pregunta.
            // Usamos un pequeño delay para que no se sientan pegados.
            setTimeout(() => {
                addMessageToChat(respuesta.pregunta, 'brain');
                state.questionCount++;
                elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            }, 300); // 300ms de pausa
        });

    } else if (respuesta.accion === "Rendirse") {
        addMessageToChat(respuesta.texto, 'brain');
        endGame(true, "classic_lose");
    }
}

/* Abre un pop-up para que el jugador elabore su respuesta.
 * (Esta función no necesita cambios, es la misma de antes)
 * @returns {Promise<string|null>}
 */
 
function openClarificationPopup() {
    return new Promise((resolve, reject) => {
        const popup = elements.popups.customAnswer;
        const input = elements.customAnswer.input;
        const confirmBtn = elements.customAnswer.confirmButton;
        const cancelBtn = popup.querySelector('[data-close="custom-answer-popup"]');

        popup.querySelector('h3').textContent = "Aclara tu Respuesta";
        popup.querySelector('p').textContent = "Tu respuesta es ambigua. Dale al Oráculo una pista más detallada para guiar su mente.";
        input.value = '';

        popup.classList.remove('hidden');
        input.focus();

        const onConfirm = () => {
            cleanup();
            resolve(input.value.trim() || null);
        };

        const onCancel = () => {
            cleanup();
            reject(new Error("Popup Canceled"));
        };
        
        const onKeyup = (e) => {
            if (e.key === 'Enter') onConfirm();
        };

        const cleanup = () => {
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            input.removeEventListener('keyup', onKeyup);
            popup.classList.add('hidden');
        };

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        input.addEventListener('keyup', onKeyup);
    });
}

/**
 * Encapsula la lógica de enviar la respuesta al backend.
 * (Esta función no necesita cambios, es la misma de antes)
 * @param {string} finalAnswer - La respuesta final a enviar.
 */
async function sendAnswerToAkinator(finalAnswer) {
    state.isAwaitingBrainResponse = true;
    
    const respuesta = await callALE({
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: finalAnswer
    });

    handleAkinatorResponse(respuesta);
}

/**
 * Abre un pop-up para que el jugador elabore su respuesta.
 * Reutiliza la estructura del pop-up de "Respuesta Mística".
 * Devuelve una Promesa que se resuelve con el texto del jugador o se rechaza si se cancela.
 * @returns {Promise<string|null>}
 */
function openClarificationPopup() {
    return new Promise((resolve, reject) => {
        const popup = elements.popups.customAnswer;
        const input = elements.customAnswer.input;
        const confirmBtn = elements.customAnswer.confirmButton;
        const cancelBtn = popup.querySelector('[data-close="custom-answer-popup"]');

        // Modificamos los textos del pop-up para este contexto
        popup.querySelector('h3').textContent = "Aclara tu Respuesta";
        popup.querySelector('p').textContent = "Tu respuesta es ambigua. Dale al Oráculo una pista más detallada para guiar su mente.";
        input.value = '';

        popup.classList.remove('hidden');
        input.focus();

        const onConfirm = () => {
            cleanup();
            resolve(input.value.trim() || null); // Resuelve con el texto o null si está vacío
        };

        const onCancel = () => {
            cleanup();
            reject(new Error("Popup Canceled")); // Rechaza la promesa
        };
        
        const onKeyup = (e) => {
            if (e.key === 'Enter') onConfirm();
        };

        // Función para limpiar los listeners y ocultar el pop-up
        const cleanup = () => {
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            input.removeEventListener('keyup', onKeyup);
            popup.classList.add('hidden');
        };

        // Añadimos los listeners
        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
        input.addEventListener('keyup', onKeyup);
    });
}

/**
 * Encapsula la lógica de enviar la respuesta al backend y esperar la reacción de la IA.
 * @param {string} finalAnswer - La respuesta final (simple o con aclaración) a enviar.
 */
async function sendAnswerToAkinator(finalAnswer) {
    state.isAwaitingBrainResponse = true;
    
    const respuesta = await callALE({
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: finalAnswer
    });

    // Llama a la función que ya tienes para manejar la respuesta de la IA
    // (la que muestra la siguiente pregunta, la adivinanza, o la rendición).
    handleAkinatorResponse(respuesta);
}
// ¡NUEVO! Función centralizada para manejar las respuestas de Akinator
function handleAkinatorResponse(respuesta) {
    state.isAwaitingBrainResponse = false;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);

    if (respuesta && !respuesta.error) {
        state.questionCount++;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;

        if (respuesta.accion === "Preguntar") {
            if (state.questionCount >= config.questionsLimit) {
                 addMessageToChat("He agotado mis preguntas... debo arriesgarme.", 'brain');
                 // Aquí podrías forzar una adivinanza, pero por ahora terminamos el juego.
                 endGame(true, 'classic_timeout'); // El jugador gana porque la IA se quedó sin preguntas
            } else {
                addMessageToChat(respuesta.texto, 'brain');
            }
        } else if (respuesta.accion === "Adivinar") {
            addMessageToChat(`Estoy listo para adivinar... ¿Estás pensando en... **${respuesta.texto}**?`, 'brain');
            state.isAwaitingBrainResponse = 'confirmation'; // Marcador especial para la próxima respuesta
        } else if (respuesta.accion === "Rendirse") {
            addMessageToChat(respuesta.texto, 'brain');
            endGame(true, 'classic_giveup'); // El jugador gana porque la IA se rindió
        }
    } else {
        addMessageToChat("No he podido procesar tu respuesta. Mi mente está confusa.", 'brain');
        elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);
    }
}


function startTimer() {
    clearInterval(state.gameTimerInterval);
    state.gameTime = 0;
    state.gameTimerInterval = setInterval(() => {
        state.gameTime++;
        const minutes = Math.floor(state.gameTime / 60).toString().padStart(2, '0');
        const seconds = (state.gameTime % 60).toString().padStart(2, '0');
        elements.header.timer.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

function stopTimer() { clearInterval(state.gameTimerInterval); }

// ¡MODIFICADO! La función endGame ahora maneja los nuevos resultados del Modo Clásico
function endGame(isWin, reason = "guess", character) {
    stopTimer();
    state.isGameActive = false;
    const characterName = (typeof character === 'object' && character !== null) ? character.nombre : (character || (state.secretCharacter ? state.secretCharacter.nombre : "un misterio"));
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    
    let message;
    if (isWin) { // El jugador gana
        switch(reason) {
            case 'classic_lose':
                message = "¡Ganas! La IA no ha adivinado tu personaje.";
                break;
            case 'classic_timeout':
                message = "¡Ganas! La IA se ha quedado sin preguntas.";
                break;
            case 'classic_giveup':
                message = "¡Ganas! La IA se ha rendido.";
                break;
            default: // Victoria en Modo Oráculo
                 message = `¡Correcto! El personaje era ${characterName}. Tu mente es... aceptable.`;
        }
        elements.endScreens.winMessage.textContent = message;
        elements.screens.win.classList.remove('hidden');
    } else { // El jugador pierde (o la IA gana)
        switch(reason) {
            case 'classic_win':
                message = "¡Derrota! La IA ha adivinado tu personaje.";
                break;
            case 'disconnect':
                message = "Tu oponente se ha desconectado. La partida ha terminado.";
                break;
            default: // Derrota en Modo Oráculo
                let loseReason = reason === "questions" ? "Has agotado tus preguntas." : "Has fallado.";
                message = `${loseReason} El personaje era ${characterName}.`;
        }
        elements.endScreens.loseMessage.textContent = message;
        elements.screens.lose.classList.remove('hidden');
    }
}

// =================================================================================
// == ¡FUNCIÓN MODIFICADA PARA MOSTRAR ACLARACIONES! ==
// Reemplaza tu antigua función addMessageToChat con esta nueva versión.
// =================================================================================

/**
 * Añade un mensaje al historial del chat con el efecto de máquina de escribir.
 * ¡NUEVO!: Ahora formatea las respuestas del jugador para mostrar las aclaraciones en línea.
 * @param {string} text - El contenido del mensaje.
 * @param {string} sender - 'player', 'brain', o 'system'.
 * @param {function} [callback] - Una función a ejecutar cuando el typewriter termina.
 */

function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    let avatarIcon = '⚙️';
    let fullText = text;

    if (sender === 'player') {
        avatarIcon = '👤';
        // ¡CORRECCIÓN! Nos aseguramos de que el texto se construya correctamente.
        fullText = `Tú: ${text}`; 
    } else if (sender === 'brain') {
        avatarIcon = '🧠';
        fullText = `Oráculo: ${text}`;
    }
    
    avatar.textContent = avatarIcon;

    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';

    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;

    typewriterEffect(textContainer, fullText, callback);
}

const typewriterIntervals = {};

function typewriterEffect(element, text, callback) {
    // Generamos un ID único para cada elemento que usa el typewriter
    const elementId = element.id || (element.id = `typewriter-target-${Math.random()}`);

    // Si ya hay un typewriter escribiendo en este elemento, lo cancelamos limpiamente.
    if (typewriterIntervals[elementId]) {
        clearInterval(typewriterIntervals[elementId]);
    }

    element.innerHTML = ''; // Limpiamos el contenido anterior
    element.classList.remove('hidden');
    let i = 0;

    function write() {
        // Condición de parada: si ya hemos escrito todo el texto
        if (i >= text.length) {
            clearInterval(typewriterIntervals[elementId]); // Detenemos el intervalo
            delete typewriterIntervals[elementId]; // Lo eliminamos del gestor
            if (callback) callback(); // Ejecutamos el callback si existe
            return;
        }

        // Lógica para manejar etiquetas HTML dentro del texto (para negritas, etc.)
        if (text[i] === '<') {
            const closingTagIndex = text.indexOf('>', i);
            if (closingTagIndex !== -1) {
                element.innerHTML += text.substring(i, closingTagIndex + 1);
                i = closingTagIndex + 1;
            } else {
                element.innerHTML += text[i++];
            }
        } else {
            // Escribimos el siguiente carácter
            element.innerHTML += text[i++];
        }

        // Auto-scroll para mantener el último mensaje visible
        if (elements.game.chatHistory) {
            elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
        }
    }

    // Iniciamos el intervalo y guardamos su ID en nuestro gestor
    typewriterIntervals[elementId] = setInterval(write, config.typewriterSpeed);
}


function adjustScreenHeight() { if (elements.arcadeScreen) elements.arcadeScreen.style.height = `${window.innerHeight}px`; }

function closeCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}

function openCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '0%';
    elements.stage.curtainRight.style.width = '0%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}

function runTitleSequence() {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.title.classList.remove('hidden');
    elements.title.layout.classList.add('hidden');
    elements.title.introBrain.classList.add('hidden');
    setTimeout(() => {
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
    }, 500);
    setTimeout(() => {
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
        elements.title.introBrain.classList.remove('hidden');
        elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out';
    }, 1500);
    setTimeout(() => {
        elements.title.introBrain.classList.add('hidden');
        elements.title.lightning.classList.add('flash-long');
        setTimeout(() => {
            elements.title.lightning.classList.remove('flash-long');
            elements.title.layout.classList.remove('hidden');
        }, 2000);
    }, 4000);
}

function showGameStage(withCurtain = true) {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.brain.classList.remove('hidden');
    elements.stage.dialog.classList.add('hidden');
    elements.stage.menuButtons.classList.add('hidden');
    
    const showFinalMenu = () => {
        const menuPrincipalHTML = `
            <button class="menu-button button-green" data-action="show-single-player">1 Jugador</button>
            <button class="menu-button button-purple" data-action="show-multiplayer">Multijugador</button>
            <div style="height: 15px;"></div>
            <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
        `;
        elements.stage.menuButtons.innerHTML = menuPrincipalHTML;
        elements.stage.menuButtons.classList.remove('hidden');
    };

    if (withCurtain) {
        elements.stage.lights.classList.remove('hidden');
        elements.stage.curtainLeft.style.transition = 'none';
        elements.stage.curtainRight.style.transition = 'none';
        elements.stage.curtainLeft.style.width = '50%';
        elements.stage.curtainRight.style.width = '50%';
        elements.stage.curtainLeft.offsetHeight; 

        setTimeout(() => {
            openCurtains(() => {
                setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 1000);
                setTimeout(() => {
                    typewriterEffect(elements.stage.dialog, phrases.menuOracle.main, showFinalMenu);
                }, 500);
            }, 1);
        }, 500);
    } else {
        typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu, showFinalMenu);
    }
}

// Pega esta nueva función en tu script.js

// Reemplaza o crea esta función en script.js
function showClassicChallengeScreen() {
    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        elements.stage.menuButtons.classList.add('hidden');
        openCurtains(() => {
            const challengeText = "Has elegido desafiar mi intelecto. Tu tarea es simple: piensa en un personaje y manténlo en tu mente. Yo, a través de una serie de preguntas precisas, desvelaré su identidad.";
            typewriterEffect(elements.stage.dialog, challengeText, () => {
                // ¡CAMBIO CLAVE! Usamos onclick para llamar a startGame directamente.
                elements.stage.menuButtons.innerHTML = `
                    <button class="menu-button button-green" onclick="startGame('classic_ia')">Aceptar Desafío</button>
                    <button class="menu-button button-red" onclick="showGameStage(false)">Huir</button>
                `;
                elements.stage.menuButtons.classList.remove('hidden');
            });
        }, 1);
    }, 1);
}



// --- ¡NUEVA FUNCIÓN PARA EL DESAFÍO DEL MODO CLÁSICO! ---
async function handleClassicAnswer(answer) {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    state.isAwaitingBrainResponse = true;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = true);
    addMessageToChat(answer, 'player');

    const payload = {
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: answer,
        estado_juego: {
            es_segunda_oportunidad: state.isSecondChance || false,
            limite_preguntas: config.questionsLimit
        }
    };

    const respuesta = await callALE(payload);
    
    // --- ¡AQUÍ EMPIEZA LA LÓGICA DEL SUPERVISOR! ---

    if (!respuesta || respuesta.error || !respuesta.accion) {
        state.isAwaitingBrainResponse = false;
        addMessageToChat("Mi mente se ha nublado... No puedo continuar. Has ganado esta vez.", 'brain');
        endGame(true, "classic_lose");
        return;
    }

    // Si la IA intenta adivinar, primero la supervisamos.
    if (respuesta.accion === "Adivinar") {
        const guessText = respuesta.texto;
        
        // Lista de palabras "prohibidas" que indican una categoría, no un nombre.
        const badGuessKeywords = ['humano', 'personaje', 'alguien', 'un ', 'una ', 'de ', 'dentro', 'con '];
        
        // Comprobamos si la adivinanza es "mala" (corta, en minúsculas, o contiene palabras prohibidas).
        const isBadGuess = (guessText.length < 3) || (guessText.toLowerCase() === guessText && !guessText.includes(' ')) || badGuessKeywords.some(keyword => guessText.toLowerCase().includes(keyword));

        if (isBadGuess) {
            // ¡ADIVINANZA RECHAZADA!
            console.warn(`SUPERVISOR: Adivinanza rechazada ('${guessText}'). Forzando a la IA a reintentar.`);
            addMessageToChat(`(El Oráculo murmura algo ininteligible sobre '${guessText}'... y parece que se corrige a sí mismo.)`, 'system');
            
            // "Castigamos" a la IA y la forzamos a jugar de nuevo.
            // Le decimos que su adivinanza fue incorrecta y le damos una nueva instrucción.
            handleClassicAnswer(`No, no es '${guessText}'. Eso no es un nombre, es una descripción. Intenta adivinar un nombre propio la próxima vez.`);
            return; // Detenemos la ejecución aquí.
        } else {
            // La adivinanza parece un nombre propio. Procedemos a mostrar el pop-up de confirmación.
            handleAkinatorGuess(guessText);
        }
    } else {
        // Si la acción no es "Adivinar", la procesamos normalmente.
        handleAkinatorResponse(respuesta);
    }
}

// --- ¡NUEVA FUNCIÓN DE AYUDA PARA MANEJAR LA ADIVINANZA! ---
// (Pega esta función justo debajo de handleClassicAnswer)
function handleAkinatorGuess(characterName) {
    addMessageToChat(`He llegado a una conclusión... Creo que estás pensando en... **${characterName}**.`, 'brain');
    
    const popup = document.getElementById('confirm-guess-popup');
    document.getElementById('confirm-guess-character').textContent = characterName;
    popup.classList.remove('hidden');

    document.getElementById('confirm-guess-yes').onclick = () => {
        popup.classList.add('hidden');
        addMessageToChat(`¡He acertado! Sabía que era ${characterName}.`, 'brain');
        endGame(false, "classic_win");
    };

    document.getElementById('confirm-guess-no').onclick = () => {
        popup.classList.add('hidden');
        if (state.isSecondChance) {
            addMessageToChat(`¡Vaya! He fallado de nuevo. Me rindo. Tú ganas.`, 'brain');
            endGame(true, "classic_lose");
        } else {
            state.isSecondChance = true;
            const preguntasExtra = Math.floor(Math.random() * 3) + 3; // Menos preguntas extra
            config.questionsLimit += preguntasExtra;
            addMessageToChat(`¡Maldición! Estaba seguro. De acuerdo, me concentraré más. Ahora tengo ${config.questionsLimit} preguntas en total.`, 'brain');
            elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            // Forzamos el siguiente turno con la corrección.
            handleClassicAnswer(`No, no es ${characterName}`);
        }
    };
}

// --- ¡FUNCIÓN MODIFICADA PARA PROCESAR OTRAS RESPUESTAS! ---
// (Reemplaza tu función handleAkinatorResponse actual por esta)
function handleAkinatorResponse(respuesta) {
    state.isAwaitingBrainResponse = false;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);

    if (respuesta.accion === "Preguntar") {
        addMessageToChat(respuesta.texto, 'brain');
        state.questionCount++;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
    } else if (respuesta.accion === "Comentar_y_Preguntar") {
        addMessageToChat(respuesta.comentario, 'brain', () => {
            setTimeout(() => {
                addMessageToChat(respuesta.pregunta, 'brain');
                state.questionCount++;
                elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            }, 300);
        });
    } else if (respuesta.accion === "Rendirse") {
        addMessageToChat(respuesta.texto, 'brain');
        endGame(true, "classic_lose");
    }
}


// Reemplaza esta función en script.js
function showChallengeScreen() {
    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        elements.stage.menuButtons.classList.add('hidden');
        openCurtains(() => {
            typewriterEffect(elements.stage.dialog, phrases.challenge, () => {
                // ¡CAMBIO CLAVE! Usamos onclick para llamar a startGame directamente.
                elements.stage.menuButtons.innerHTML = `
                    <button class="menu-button button-green" onclick="startGame('oracle_ia')">Aceptar Reto</button>
                    <button class="menu-button button-red" onclick="showGameStage(false)">Huir</button>
                `;
                elements.stage.menuButtons.classList.remove('hidden');
            });
        }, 1);
    }, 1);
}

