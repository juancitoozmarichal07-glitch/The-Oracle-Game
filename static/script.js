// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v24.1 (Lobby de Duelo)         ==
// ===================================================================
// - AÑADIDO: Pop-up de configuración para partidas 1 vs 1.
// - AÑADIDO: Lógica para enviar reglas personalizadas al servidor.
// - CORREGIDO: Manejadores de eventos para todos los botones.

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20, // Límite por defecto, se puede sobreescribir por las reglas del duelo
    typewriterSpeed: 45,
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
    isAwaitingBrainResponse: false,
    suggestionUses: config.suggestionLimit,
    lastSuggestionTimestamp: 0,
    guessPopupPatience: 3,
    currentGameMode: null, 
    gameTimerInterval: null,
    gameTime: 0,
    socket: null,
    id_sala: null,
    rol_jugador: null
};

// --- CONEXIÓN CON SERVIDORES ---
const ALE_URL = 'http://127.0.0.1:5000/api/execute';
// IMPORTANTE: Cuando despliegues tu Replit, cambia esta URL
const REPLIT_URL = 'https://tu-proyecto-cooperativo.replit.dev/'; // <-- URL DE EJEMPLO

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
        dueloConfig: document.getElementById('duelo-config-popup')
    },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { container: document.getElementById('suggestion-popup'), content: document.querySelector('#suggestion-popup .popup-content'), buttonsContainer: document.getElementById('suggestion-buttons-container') },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: {}
};

// ===================================================================
// ===                LÓGICA MULTIJUGADOR                          ===
// ===================================================================

function conectarAlServidorDeDuelo() {
    try {
        state.socket = io(REPLIT_URL);
        console.log("Intentando conectar al servidor de duelo...");

        state.socket.on('connect', () => {
            console.log("✅ ¡Conectado al servidor de duelo! ID de Socket:", state.socket.id);
        });

        state.socket.on('duelo_creado', (data) => {
            state.id_sala = data.id_sala;
            const linkDuelo = `${window.location.origin}${window.location.pathname}?duelo=${state.id_sala}`;
            
            elements.stage.dialog.classList.remove('hidden');
            typewriterEffect(elements.stage.dialog, `¡Duelo creado! Comparte este link con tu amigo: <br><br><input type="text" value="${linkDuelo}" style="width: 100%; text-align: center;" readonly onclick="this.select()"><br><br>Esperando oponente...`);
            elements.stage.menuButtons.classList.add('hidden');
        });

        state.socket.on('partida_lista', (data) => {
            if (state.rol_jugador === null) {
                state.rol_jugador = data.rol_invitado;
            }
            // Aquí recibiremos las reglas del juego y configuraremos el estado
            console.log("Partida lista, reglas recibidas:", data.reglas);
            config.questionsLimit = data.reglas.limitePreguntas || 20;
            // Guardar más reglas si es necesario...
            
            startGame('duelo_1v1');
        });
        
        state.socket.on('pregunta_recibida', (data) => {
            if (state.rol_jugador === 'oraculo') {
                addMessageToChat(data.pregunta, 'player');
                elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = false);
            }
        });

        state.socket.on('respuesta_recibida', (data) => {
            if (state.rol_jugador === 'adivino') {
                addMessageToChat(data.respuesta, 'brain');
                elements.game.input.disabled = false;
                elements.game.askButton.disabled = false;
                elements.game.input.focus();
            }
        });
        
        state.socket.on('error_sala', (data) => {
            alert(data.mensaje);
            window.location.href = window.location.origin + window.location.pathname;
        });

    } catch (e) {
        console.error("Error al cargar la librería de Socket.IO. Asegúrate de que la URL del servidor es correcta y está online.", e);
        alert("No se pudo conectar con el servidor multijugador.");
    }
}

function iniciarCreacionDuelo(opciones) {
    // Guardamos el rol que el anfitrión quiere, si no es aleatorio
    if (opciones.rolSeleccionado !== 'aleatorio') {
        state.rol_jugador = opciones.rolSeleccionado;
    }
    
    // Enviamos las reglas y el rol al servidor
    state.socket.emit('crear_duelo', { 
        reglas: opciones.reglas,
        rolAnfitrion: opciones.rolSeleccionado 
    });
    
    typewriterEffect(elements.stage.dialog, "Creando duelo personalizado en el cosmos...");
    elements.stage.menuButtons.classList.add('hidden');
}


function unirseADuelo(id_duelo) {
    state.id_sala = id_duelo;
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.dialog.classList.remove('hidden');
    typewriterEffect(elements.stage.dialog, "Conectando al duelo...");
    elements.stage.menuButtons.classList.add('hidden');
    openCurtains(() => {
        state.socket.emit('unirse_a_duelo', { id_sala: id_duelo });
    });
}
// ===================================================================
// ===           LÓGICA DEL JUEGO Y NAVEGACIÓN (Continuación)      ===
// ===================================================================

// (Esta es la continuación de la PARTE 1)

function unirseADuelo(id_duelo) {
    state.id_sala = id_duelo;
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.dialog.classList.remove('hidden');
    typewriterEffect(elements.stage.dialog, "Conectando al duelo...");
    elements.stage.menuButtons.classList.add('hidden');
    openCurtains(() => {
        state.socket.emit('unirse_a_duelo', { id_sala: id_duelo });
    });
}

// ===================================================================
// ===           LÓGICA DEL JUEGO Y NAVEGACIÓN                     ===
// ===================================================================

function resetGameState() {
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isAwaitingBrainResponse = false;
    state.suggestionUses = config.suggestionLimit;
    state.lastSuggestionTimestamp = 0;
    state.guessPopupPatience = 3;
    state.gameTime = 0;
    
    clearInterval(state.gameTimerInterval);
    elements.header.timer.textContent = "00:00";
    elements.header.questionCounter.textContent = `0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
}

async function startGame(mode) {
    state.currentGameMode = mode;
    closeCurtains(async () => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');
        resetGameState();
        
        if (mode === 'oracle_ia') {
            await prepararInterfazModoOraculoIA();
        } else if (mode === 'classic_ia') {
            await prepararInterfazModoClasicoIA();
        } else if (mode === 'duelo_1v1') {
            prepararInterfazDuelo();
        }
        
        startTimer();
    }, 1);
}

function prepararInterfazDuelo() {
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.add('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.header.questionCounter.classList.remove('hidden'); // Asegurarse de que sea visible

    if (state.rol_jugador === 'adivino') {
        elements.game.oracleControls.classList.remove('hidden');
        elements.game.suggestionButton.classList.add('hidden'); // Sin sugerencias en duelo
        elements.game.guessButton.classList.remove('hidden'); // Botón de adivinar sí
        addMessageToChat("Eres el Adivino. Tu oponente es el Oráculo. Haz tu primera pregunta.", 'system');
    } else if (state.rol_jugador === 'oraculo') {
        elements.game.dueloOraculoControls.classList.remove('hidden');
        addMessageToChat("Eres el Oráculo. Tu oponente es el Adivino. Espera su pregunta.", 'system');
        elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
    }
}

async function handlePlayerInput() {
    const questionText = elements.game.input.value.trim();
    if (questionText === '') return;

    if (state.currentGameMode === 'duelo_1v1') {
        addMessageToChat(questionText, 'player');
        state.socket.emit('enviar_pregunta', { id_sala: state.id_sala, pregunta: questionText });
        elements.game.input.value = '';
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
    } else { // Modo Oráculo vs IA
        if (!state.isGameActive || state.isAwaitingBrainResponse) return;
        state.isAwaitingBrainResponse = true;
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        
        addMessageToChat(questionText, 'player');
        elements.game.input.value = '';
        
        const respuesta = await callALE({ skillset_target: "oracle", accion: "procesar_pregunta", pregunta: questionText });
        
        state.isAwaitingBrainResponse = false;
        if (!respuesta || respuesta.error) {
            if (state.isGameActive) {
                elements.game.input.disabled = false;
                elements.game.askButton.disabled = false;
            }
            return;
        }

        const fullResponse = `${respuesta.respuesta || ''} ${respuesta.aclaracion || ''}`.trim();
        addMessageToChat(fullResponse, 'brain');

        if (respuesta.castigo === 'ninguno' || respuesta.castigo === 'penalizacion_leve') {
             state.questionCount++;
             elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
        }
        
        if (state.isGameActive) {
            elements.game.input.disabled = false;
            elements.game.askButton.disabled = false;
            elements.game.input.focus();
        }

        if (state.isGameActive && state.questionCount >= config.questionsLimit) {
            endGame(false, "questions");
        }
    }
}

function handleDueloOraculoResponse(respuesta) {
    addMessageToChat(respuesta, 'brain');
    state.socket.emit('enviar_respuesta', { id_sala: state.id_sala, respuesta: respuesta });
    elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
}

document.addEventListener('DOMContentLoaded', () => {
    adjustScreenHeight();
    window.addEventListener('resize', adjustScreenHeight);

    // Descomentar cuando la URL del servidor de Replit esté lista
    // conectarAlServidorDeDuelo(); 

    const urlParams = new URLSearchParams(window.location.search);
    const id_duelo = urlParams.get('duelo');
    if (id_duelo) {
        // Descomentar cuando la URL del servidor de Replit esté lista
        // unirseADuelo(id_duelo);
        console.log("Funcionalidad de unirse a duelo desactivada hasta configurar servidor.");
        runTitleSequence(); // Por ahora, solo inicia el juego normal
    } else {
        runTitleSequence();
    }

    elements.title.startButton.addEventListener('click', () => showGameStage(true));
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.header.backToMenu.addEventListener('click', () => {
        window.location.href = window.location.origin + window.location.pathname;
    });
    
    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (!action) return;
        elements.stage.menuButtons.classList.add('hidden');

        switch(action) {
            case 'show-single-player':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.singlePlayer, () => {
                    elements.stage.menuButtons.innerHTML = `<button class="menu-button button-green" data-action="play-oracle">Modo Oráculo (vs IA)</button><button class="menu-button button-green" data-action="play-classic">Modo Clásico (vs IA)</button><div style="height: 15px;"></div><button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>`;
                    elements.stage.menuButtons.classList.remove('hidden');
                });
                break;
            case 'show-multiplayer':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.multiplayer, () => {
                    elements.stage.menuButtons.innerHTML = `<button class="menu-button button-purple" data-action="create-duel-1v1">1 vs 1</button><button class="menu-button button-purple" data-action="create-duel-varios" disabled>1 vs Varios (Próx)</button><div style="height: 15px;"></div><button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>`;
                    elements.stage.menuButtons.classList.remove('hidden');
                });
                break;
            case 'back-to-main-menu':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu, () => {
                    showFinalMenu();
                 });
                break;
            case 'play-oracle':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.playOracle, showChallengeScreen);
                break;
            case 'play-classic':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.playClassic, () => startGame('classic_ia'));
                break;
            case 'accept-challenge':
                startGame('oracle_ia');
                break;
            case 'flee-to-title':
                runTitleSequence();
                break;
            case 'flee-challenge':
                 showGameStage(false);
                break;
            case 'create-duel-1v1':
                // Descomentar cuando el servidor esté listo
                // if (!state.socket || !state.socket.connected) {
                //     alert("No se pudo conectar al servidor multijugador. Revisa la URL y si está online.");
                //     showGameStage(false);
                //     return;
                // }
                elements.popups.dueloConfig.classList.remove('hidden');
                break;
        }
    });
    
    elements.game.dueloOraculoControls.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') handleDueloOraculoResponse(e.target.dataset.answer);
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

    // --- Lógica para el Pop-up de Configuración de Duelo ---
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
        // Descomentar cuando el servidor esté listo
        // iniciarCreacionDuelo({ reglas, rolSeleccionado });
        console.log("Creación de duelo desactivada. Opciones elegidas:", { reglas, rolSeleccionado });
        alert("La creación de duelos está desactivada hasta que el servidor esté configurado.");
        showGameStage(false);
    });

    // --- MANEJADORES PARA LOS BOTONES DE ACCIÓN DEL MODO ORÁCULO ---
    elements.game.guessButton.addEventListener('click', () => {
        elements.popups.guess.classList.remove('hidden');
        elements.guessPopup.input.focus();
    });
    elements.guessPopup.confirmButton.addEventListener('click', async () => {
        const guessText = elements.guessPopup.input.value.trim();
        if (guessText === '') return;
        elements.popups.guess.classList.add('hidden');
        const respuesta = await callALE({
            skillset_target: "oracle",
            accion: "verificar_adivinanza",
            adivinanza: guessText
        });
        endGame(respuesta.resultado === "victoria", "guess", respuesta.personaje_secreto);
    });
    elements.game.suggestionButton.addEventListener('click', async () => {
        elements.game.suggestionButton.disabled = true;
        elements.game.suggestionButton.textContent = "Pensando...";
        const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_sugerencia" });
        elements.game.suggestionButton.disabled = false;
        state.suggestionUses--;
        elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
        if (respuesta && respuesta.sugerencias && respuesta.sugerencias.length > 0) {
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
        if (state.suggestionUses <= 0) elements.game.suggestionButton.disabled = true;
    });

    // --- MANEJADOR DE RESPUESTAS PARA EL MODO CLÁSICO (AKINATOR) ---
    elements.game.classicControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('answer-btn')) {
            handleClassicAnswer(e.target.dataset.answer);
        }
    });
});

async function callALE(payload) {
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`Error del servidor: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Error al llamar a A.L.E.:", error);
        addMessageToChat(`Error de conexión con el cerebro. ${error.message}`, 'system');
        return { error: true };
    }
}

async function prepararInterfazModoOraculoIA() {
    elements.game.oracleControls.classList.remove('hidden');
    elements.game.classicControls.classList.add('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.game.suggestionButton.classList.remove('hidden');
    elements.game.guessButton.classList.remove('hidden');
    elements.header.questionCounter.classList.remove('hidden');
    addMessageToChat("Concibiendo un nuevo enigma...", "brain");
    const respuesta = await callALE({ skillset_target: "oracle", accion: "iniciar_juego" });
    if (respuesta.error) return;
    state.secretCharacter = respuesta.personaje_secreto;
    elements.game.chatHistory.innerHTML = '';
    state.isGameActive = true;
    addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.suggestionButton.disabled = false;
        elements.game.guessButton.disabled = false;
        elements.game.input.focus();
    });
}

async function prepararInterfazModoClasicoIA() {
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.remove('hidden');
    elements.game.dueloOraculoControls.classList.add('hidden');
    elements.game.suggestionButton.classList.add('hidden');
    elements.game.guessButton.classList.add('hidden');
    elements.header.questionCounter.classList.remove('hidden');
    addMessageToChat("Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas.", 'brain');
    const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
    if (respuesta && !respuesta.error && respuesta.siguiente_pregunta) {
        state.isGameActive = true;
        addMessageToChat(respuesta.siguiente_pregunta, 'brain');
    } else {
        addMessageToChat("Mi mente está confusa. Vuelve al menú.", 'brain');
    }
}

async function handleClassicAnswer(answer) {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    state.isAwaitingBrainResponse = true;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = true);
    addMessageToChat(answer, 'player');
    const respuesta = await callALE({
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: answer
    });
    state.isAwaitingBrainResponse = false;
    elements.game.classicControls.querySelectorAll('button').forEach(btn => btn.disabled = false);
    if (respuesta && !respuesta.error) {
        if (respuesta.accion === "Preguntar") {
            addMessageToChat(respuesta.texto, 'brain');
        } else if (respuesta.accion === "Adivinar") {
            addMessageToChat(`Estoy listo para adivinar... ¿Estás pensando en... **${respuesta.texto}**?`, 'brain');
            state.isGameActive = false;
        } else if (respuesta.accion === "Rendirse") {
            addMessageToChat(respuesta.texto, 'brain');
            state.isGameActive = false;
        }
    } else {
        addMessageToChat("No he podido procesar tu respuesta.", 'brain');
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

function endGame(isWin, reason = "guess", character) {
    stopTimer();
    state.isGameActive = false;
    const characterName = character ? character.nombre : (state.secretCharacter ? state.secretCharacter.nombre : "un misterio");
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${characterName}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        let loseMessage = `Has fallado. El personaje era ${characterName}.`;
        if (reason === "questions") loseMessage = `Has agotado tus preguntas. El personaje era ${characterName}.`;
        elements.endScreens.loseMessage.textContent = loseMessage;
        elements.screens.lose.classList.remove('hidden');
    }
}

function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : (sender === 'player' ? '👤' : '⚙️');
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';
    let prefix = '';
    if (sender === 'brain') prefix = 'Oráculo: '; else if (sender === 'player') prefix = 'Tú: ';
    const fullText = prefix + text;
    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
    typewriterEffect(textContainer, fullText, callback);
}

function typewriterEffect(element, text, callback) {
    let i = 0;
    const processedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    element.innerHTML = '';
    element.classList.remove('hidden');
    const interval = setInterval(() => {
        if (i < processedText.length) {
            element.innerHTML += processedText.charAt(i);
            i++;
            if (element.id === 'stage-dialog') element.scrollTop = element.scrollHeight;
            else elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
        } else {
            clearInterval(interval);
if (callback) callback();
        }
    }, config.typewriterSpeed);
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
            <button class="menu-button button-purple" data-action="show-multiplayer">Cooperativo</button>
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
        showFinalMenu();
        typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu);
    }
}

function showChallengeScreen() {
    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        openCurtains(() => {
            elements.stage.menuButtons.innerHTML = `
                <button class="button-green" data-action="accept-challenge">Aceptar Reto</button>
                <button class="button-red" data-action="flee-challenge">Huir</button>
            `;
            typewriterEffect(elements.stage.dialog, phrases.challenge, () => {
                elements.stage.menuButtons.classList.remove('hidden');
            });
        }, 2.5);
    }, 1);
}
