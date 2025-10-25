// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v24.3 (Duelo de Oráculos)       ==
// ===================================================================
// - MEJORADO: El jugador-Oráculo en 1vs1 ahora tiene una interfaz morada.
// - AÑADIDO: El jugador-Oráculo puede escribir respuestas personalizadas.
// - Mantiene todas las funcionalidades anteriores, incluyendo sugerencias.

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    challengeGraceTime: 20000,
    suggestionLimit: 5,
    suggestionStart: 5
};
const phrases = {
    challengeOracle: "Tu humilde tarea será adivinar el ser, real o ficticio, que yo, el Gran Oráculo, he concebido en mi mente. Tienes 20 preguntas para desvelar mi enigma. Úsalas con sabiduría. ¿Aceptas este desafío a tu intelecto?",
    challengeClassic: "Concentra tu mente mortal. Piensa en un ser, real o ficticio. Yo haré 20 preguntas para leer tus pensamientos, y tú solo podrás responderme 'Sí', 'No' y sus variantes. No intentes engañarme. ¿Estás listo?",
    guessPopup: {
        initial: "Susurra tu respuesta al vacío...",
        strike1: "No puedo adivinar el vacío. ¡Escribe un nombre!",
        strike2: "¿Intentas agotar mi paciencia? Escribe una respuesta o cancela.",
        strike3: "Has agotado mi paciencia. El privilegio de adivinar te ha sido revocado... por ahora."
    },
    menuOracle: {
        main: "Una elección audaz. El telón se alza. Veamos qué camino eliges.",
        singlePlayer: "¿Un desafío solitario? Pretendes enfrentarte a la infinidad de mi mente sin ayuda... Interesante.",
        multiplayer: "Ah, buscas la compañía de otros mortales. ¿Para colaborar, o para traicionaros mutuamente? El tiempo lo dirá.",
        playOracle: "Así que quieres probar mi poder... Bien. Escucha con atención.",
        playClassic: "Prefieres que yo adivine, ¿eh? Muy bien. Prepárate.",
        backToMenu: "¿Dudas? La incertidumbre es el primer paso hacia la ignorancia. Elige de nuevo.",
        fleeChallengeOracle: "Lo sabía. La verdadera sabiduría requiere coraje, no solo curiosidad. Vuelve cuando estés preparado.",
        classicGraceTime: "Te concederé un breve instante... 20 segundos de mi tiempo cósmico para que ordenes tus pensamientos. El reloj ha comenzado a correr.",
        classicStillNeedsTime: "Suficiente. La indecisión es una plaga. Vuelve cuando seas digno de mi atención."
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
    rol_jugador: null,
    graceTimer: null
};

// --- CONEXIÓN CON SERVIDORES ---
const ALE_URL = 'http://127.0.0.1:5000/api/execute';
const REPLIT_URL = 'https://ff849e56-b6b6-4619-8495-996867c9bc5c-00-1rg9nfq7thllg.picard.replit.dev/';

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
        dueloOraculoControls: document.getElementById('duelo-oraculo-controls'),
        // NUEVOS SELECTORES PARA EL ORÁCULO HUMANO
        dueloOraculoInput: document.getElementById('duelo-oraculo-input'),
        dueloOraculoSendBtn: document.getElementById('duelo-oraculo-send-btn')
    },
    popups: { 
        guess: document.getElementById('guess-popup'), 
        suggestion: document.getElementById('suggestion-popup') 
    },
    guessPopup: {
        brainText: document.getElementById('guess-popup-brain-text'),
        input: document.getElementById('guess-input'), 
        confirmButton: document.getElementById('confirm-guess-button')
    },
    suggestionPopup: { 
        buttonsContainer: document.getElementById('suggestion-buttons-container') 
    },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: {}
};

// ===================================================================
// ===                LÓGICA MULTIJUGADOR                          ===
// ===================================================================

function conectarAlServidorDeDuelo() {
    try {
        state.socket = io(REPLIT_URL);
        console.log("Intentando conectar al servidor de duelo en Replit...");

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
            startGame('duelo_1v1');
        });
        
        state.socket.on('pregunta_recibida', (data) => {
            if (state.rol_jugador === 'oraculo') {
                addMessageToChat(data.pregunta, 'player');
                // Habilitamos todos los controles del Oráculo
                elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = false);
                elements.game.dueloOraculoInput.disabled = false;
                elements.game.dueloOraculoInput.focus();
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
        console.error("Error al cargar la librería de Socket.IO.", e);
    }
}

function iniciarCreacionDuelo() {
    state.rol_jugador = 'oraculo';
    state.socket.emit('crear_duelo', { rol: state.rol_jugador });
    typewriterEffect(elements.stage.dialog, "Creando duelo en el cosmos...");
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
// ===           LÓGICA DEL JUEGO                                  ===
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
    clearTimeout(state.graceTimer);
    elements.header.timer.textContent = "00:00";
    elements.header.questionCounter.textContent = `0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;

    // Limpiamos el tema del oráculo al resetear
    document.body.classList.remove('duelo-oraculo-theme');
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
    elements.header.questionCounter.classList.remove('hidden'); // Lo mostramos para el duelo

    if (state.rol_jugador === 'adivino') {
        elements.game.oracleControls.classList.remove('hidden');
        elements.game.suggestionButton.classList.add('hidden');
        elements.game.guessButton.classList.remove('hidden'); // El adivino puede adivinar
        addMessageToChat("Eres el Adivino. Tu oponente es el Oráculo. Haz tu primera pregunta.", 'system');
    } else if (state.rol_jugador === 'oraculo') {
        document.body.classList.add('duelo-oraculo-theme'); // APLICAMOS EL TEMA MORADO
        elements.game.dueloOraculoControls.classList.remove('hidden');
        addMessageToChat("Eres el Oráculo. Tu oponente es el Adivino. Espera su pregunta.", 'system');
        // Deshabilitamos todos los controles hasta que llegue una pregunta
        elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
        elements.game.dueloOraculoInput.disabled = true;
    }
}

async function handlePlayerInput() {
    if (state.currentGameMode === 'duelo_1v1') {
        const questionText = elements.game.input.value.trim();
        if (questionText === '') return;
        
        addMessageToChat(questionText, 'player');
        state.socket.emit('enviar_pregunta', { id_sala: state.id_sala, pregunta: questionText });
        
        elements.game.input.value = '';
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
    } else {
        if (!state.isGameActive || state.isAwaitingBrainResponse) return;
        const questionText = elements.game.input.value.trim();
        if (questionText === '') return;
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

        if (respuesta.castigo === 'ninguno') {
             state.questionCount++;
             elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
        }
        
        if (state.questionCount >= 1) {
            elements.game.guessButton.disabled = false;
        }
        if (state.questionCount >= config.suggestionStart && state.suggestionUses > 0) {
            elements.game.suggestionButton.disabled = false;
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

// MODIFICADO: Ahora es una función genérica para enviar cualquier respuesta
function handleDueloOraculoResponse(respuesta) {
    addMessageToChat(respuesta, 'brain');
    state.socket.emit('enviar_respuesta', { id_sala: state.id_sala, respuesta: respuesta });
    // Deshabilitamos todos los controles de nuevo
    elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
    elements.game.dueloOraculoInput.disabled = true;
    elements.game.dueloOraculoInput.value = '';
}

// ===================================================================
// ===                PUNTO DE ENTRADA Y NAVEGACIÓN                ===
// ===================================================================

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

    elements.title.startButton.addEventListener('click', () => showGameStage(true));
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.header.backToMenu.addEventListener('click', () => {
        window.location.href = window.location.origin + window.location.pathname;
    });
    
    // --- EVENT LISTENER DEL MENÚ PRINCIPAL ---
    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        clearTimeout(state.graceTimer); 
        elements.stage.menuButtons.classList.add('hidden');

        switch(action) {
            case 'show-single-player':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.singlePlayer, () => {
                    elements.stage.menuButtons.innerHTML = `
                        <button class="menu-button button-green" data-action="play-oracle">Modo Oráculo (vs IA)</button>
                        <button class="menu-button button-green" data-action="play-classic">Modo Clásico (vs IA)</button>
                        <div style="height: 15px;"></div>
                        <button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>
                    `;
                    elements.stage.menuButtons.classList.remove('hidden');
                });
                break;
            case 'show-multiplayer':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.multiplayer, () => {
                    elements.stage.menuButtons.innerHTML = `
                        <button class="menu-button button-purple" data-action="create-duel-1v1">1 vs 1</button>
                        <button class="menu-button button-purple" data-action="create-duel-varios" disabled>1 vs Varios (Próximamente)</button>
                        <button class="menu-button button-purple" data-action="cpu-vs-varios" disabled>CPU vs Varios (Próximamente)</button>
                        <div style="height: 15px;"></div>
                        <button class="menu-button button-red" data-action="back-to-main-menu">‹ Volver</button>
                    `;
                    elements.stage.menuButtons.classList.remove('hidden');
                });
                break;
            case 'back-to-main-menu':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu, () => {
                    showGameStage(false);
                 });
                break;
            case 'play-oracle':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.playOracle, () => {
                    showChallengeScreen('oracle');
                });
                break;
            case 'play-classic':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.playClassic, () => {
                    showChallengeScreen('classic');
                 });
                break;
            case 'accept-challenge-oracle':
                startGame('oracle_ia');
                break;
            case 'accept-challenge-classic':
                startGame('classic_ia');
                break;
            case 'flee-to-title':
                runTitleSequence();
                break;
            case 'flee-challenge-oracle':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.fleeChallengeOracle, () => {
                    setTimeout(() => showGameStage(false), 1200);
                 });
                break;
            case 'flee-challenge-classic':
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.classicGraceTime, () => {
                    elements.stage.menuButtons.innerHTML = `
                        <button class="button-green" data-action="accept-challenge-classic">Estoy Listo</button>
                        <button class="button-red" data-action="flee-challenge-classic-final">Necesito aún más tiempo</button>
                    `;
                    elements.stage.menuButtons.classList.remove('hidden');
                    state.graceTimer = setTimeout(() => {
                        document.querySelector('[data-action="flee-challenge-classic-final"]').click();
                    }, config.challengeGraceTime);
                });
                break;
            case 'flee-challenge-classic-final':
                 typewriterEffect(elements.stage.dialog, phrases.menuOracle.classicStillNeedsTime, () => {
                    setTimeout(() => showGameStage(false), 1200);
                 });
                break;
            case 'create-duel-1v1':
                iniciarCreacionDuelo();
                break;
        }
    });

    // --- EVENT LISTENERS DEL JUEGO ---
    elements.game.suggestionButton.addEventListener('click', handleSuggestion);
    
    elements.game.guessButton.addEventListener('click', () => {
        elements.popups.guess.classList.remove('hidden');
        elements.guessPopup.input.focus();
        elements.guessPopup.brainText.textContent = phrases.guessPopup.initial;
        state.guessPopupPatience = 3;
    });

    elements.guessPopup.confirmButton.addEventListener('click', handleGuess);
    elements.guessPopup.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handleGuess(); });
    
    elements.game.classicControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('answer-btn')) {
            handleClassicAnswer(e.target.dataset.answer);
        }
    });

    // MODIFICADO: Ahora el contenedor de controles del oráculo maneja tanto botones como el input personalizado
    elements.game.dueloOraculoControls.addEventListener('click', (e) => {
        // Si se hace clic en un botón de respuesta rápida
        if (e.target.classList.contains('answer-btn')) {
            handleDueloOraculoResponse(e.target.dataset.answer);
        }
        // Si se hace clic en el botón de enviar del input personalizado
        if (e.target.id === 'duelo-oraculo-send-btn' || e.target.closest('#duelo-oraculo-send-btn')) {
            const customResponse = elements.game.dueloOraculoInput.value.trim();
            if (customResponse) {
                handleDueloOraculoResponse(customResponse);
            }
        }
    });
    // Añadimos listener para la tecla Enter en el input personalizado
    elements.game.dueloOraculoInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            const customResponse = elements.game.dueloOraculoInput.value.trim();
            if (customResponse) {
                handleDueloOraculoResponse(customResponse);
            }
        }
    });


    // --- OTROS EVENT LISTENERS ---
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') showGameStage(true);
            else if (action === 'main-menu') runTitleSequence();
        });
    });
    document.body.addEventListener('click', (e) => { 
        if (e.target.dataset.close) {
            e.target.closest('.popup-overlay').classList.add('hidden');
        }
    });
});

// ===================================================================
// ===                FUNCIONES DE JUEGO Y LÓGICA IA               ===
// ===================================================================

function handleGuess() {
    const guessText = elements.guessPopup.input.value.trim();
    if (guessText === '') {
        state.guessPopupPatience--;
        let patiencePhrase = phrases.guessPopup.strike1;
        if (state.guessPopupPatience === 1) patiencePhrase = phrases.guessPopup.strike2;
        elements.guessPopup.brainText.textContent = patiencePhrase;

        if (state.guessPopupPatience <= 0) {
            elements.guessPopup.brainText.textContent = phrases.guessPopup.strike3;
            setTimeout(() => {
                elements.popups.guess.classList.add('hidden');
                endGame(false, 'guess_abuse');
            }, 2000);
        }
        return;
    }

    elements.popups.guess.classList.add('hidden');
    addMessageToChat(`Mi adivinanza es... ${guessText}`, 'player');

    // En un duelo 1vs1, la lógica de victoria la decide el Oráculo humano.
    // Aquí solo manejamos la victoria contra la IA.
    if (state.currentGameMode === 'oracle_ia') {
        const normalizedGuess = guessText.toLowerCase().trim();
        const normalizedSecret = state.secretCharacter.nombre.toLowerCase().trim();

        if (normalizedGuess === normalizedSecret) {
            endGame(true);
        } else {
            addMessageToChat("No, ese no es el ser que he concebido. Sigue intentando.", 'brain');
        }
    }
    // Si es un duelo, el Oráculo humano verá la adivinanza y decidirá cómo responder.
    // Podríamos implementar un sistema de "confirmar victoria" en el futuro.

    elements.guessPopup.input.value = '';
}

async function handleSuggestion() {
    if (state.suggestionUses <= 0) return;

    elements.game.suggestionButton.disabled = true;
    addMessageToChat("El Oráculo sondea el cosmos en busca de una pista...", 'system');

    const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_sugerencia" });

    if (respuesta && !respuesta.error && respuesta.sugerencias) {
        state.suggestionUses--;
        elements.game.suggestionButton.textContent = `Sugerencia (${state.suggestionUses})`;
        
        const container = elements.suggestionPopup.buttonsContainer;
        container.innerHTML = ''; // Limpiamos sugerencias anteriores
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
        addMessageToChat("El cosmos permanece en silencio. No hay sugerencias por ahora.", 'brain');
    }
    
    if (state.suggestionUses > 0) {
        elements.game.suggestionButton.disabled = false;
    }
}

async function callALE(payload) {
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }
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
    addMessageToChat("Iniciando modo Clásico... Mi primera pregunta es:", 'system', async () => {
        const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
        if (respuesta && !respuesta.error && respuesta.siguiente_pregunta) {
            state.isGameActive = true;
            state.questionCount = 1;
            elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
            addMessageToChat(respuesta.siguiente_pregunta, 'brain');
        } else {
            addMessageToChat("Mi mente está confusa para este modo. Vuelve al menú.", 'brain');
        }
    });
}

async function handleClassicAnswer(answer) {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    state.isAwaitingBrainResponse = true;
    addMessageToChat(answer, 'player');

    const respuesta = await callALE({
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: answer
    });
    state.isAwaitingBrainResponse = false;
    if (respuesta && !respuesta.error) {
        if (respuesta.accion === "Preguntar") {
            state.questionCount++;
            elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
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

function stopTimer() {
    clearInterval(state.gameTimerInterval);
}

function endGame(isWin, reason = "guess") {
    stopTimer();
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');
    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.nombre}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        let loseMessage = "";
        switch (reason) {
            case "patience": loseMessage = `El Oráculo ha agotado su paciencia cósmica. El personaje era ${state.secretCharacter.nombre}.`; break;
            case "guess_abuse": loseMessage = `Has agotado la paciencia del Oráculo. El personaje era ${state.secretCharacter.nombre}.`; break;
            case "questions": loseMessage = `Has agotado tus preguntas. El personaje era ${state.secretCharacter.nombre}.`; break;
            default: loseMessage = `Has fallado. El personaje era ${state.secretCharacter.nombre}.`; break;
        }
        elements.endScreens.loseMessage.textContent = loseMessage;
        elements.screens.lose.classList.remove('hidden');
    }
}

// ===================================================================
// ===            FUNCIONES DE UI, EFECTOS Y ANIMACIONES           ===
// ===================================================================

function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : (sender === 'player' ? '👤' : '⚙️');
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';
    
    let prefix = '';
    if (sender === 'brain') prefix = 'Oráculo: ';
    else if (sender === 'player') prefix = 'Tú: ';
    
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
            if (element.id === 'stage-dialog') {
                 element.scrollTop = element.scrollHeight;
            } else {
                 elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
            }
        } else {
            clearInterval(interval);
            if (callback) callback();
        }
    }, config.typewriterSpeed);
}

function adjustScreenHeight() {
    if (elements.arcadeScreen) elements.arcadeScreen.style.height = `${window.innerHeight}px`;
}

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
    const menuPrincipalHTML = `
        <button class="menu-button button-green" data-action="show-single-player">1 Jugador</button>
        <button class="menu-button button-purple" data-action="show-multiplayer">Cooperativo</button>
        <div style="height: 15px;"></div>
        <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
    `;
    elements.stage.menuButtons.innerHTML = menuPrincipalHTML;

    const showFinalContent = () => {
        typewriterEffect(elements.stage.dialog, phrases.menuOracle.backToMenu, () => {
            elements.stage.menuButtons.classList.remove('hidden');
        });
    };

    if (withCurtain) {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.stage.classList.remove('hidden');
        elements.stage.brain.classList.remove('hidden');
        elements.stage.dialog.classList.add('hidden');
        elements.stage.menuButtons.classList.add('hidden');
        elements.stage.lights.classList.remove('hidden');
        elements.stage.curtainLeft.style.transition = 'none';
        elements.stage.curtainRight.style.transition = 'none';
        elements.stage.curtainLeft.style.width = '50%';
        elements.stage.curtainRight.style.width = '50%';
        elements.stage.curtainLeft.offsetHeight; 

        setTimeout(() => {
            openCurtains(() => {
                setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 1000);
                typewriterEffect(elements.stage.dialog, phrases.menuOracle.main, () => {
                     elements.stage.menuButtons.classList.remove('hidden');
                });
            }, 1);
        }, 500);
    } else {
        openCurtains(showFinalContent);
    }
}

function showChallengeScreen(mode) {
    let challengeText, acceptAction, fleeAction;

    if (mode === 'oracle') {
        challengeText = phrases.challengeOracle;
        acceptAction = 'accept-challenge-oracle';
        fleeAction = 'flee-challenge-oracle';
    } else { // classic
        challengeText = phrases.challengeClassic;
        acceptAction = 'accept-challenge-classic';
        fleeAction = 'flee-challenge-classic';
    }

    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        openCurtains(() => {
            elements.stage.menuButtons.innerHTML = `
                <button class="button-green" data-action="${acceptAction}">${mode === 'oracle' ? 'Aceptar Reto' : 'Estoy Listo'}</button>
                <button class="button-red" data-action="${fleeAction}">${mode === 'oracle' ? 'Huir' : 'Necesito Tiempo'}</button>
            `;
            typewriterEffect(elements.stage.dialog, challengeText, () => {
                elements.stage.menuButtons.classList.remove('hidden');
            });
        }, 1.5);
    }, 1);
}
