// ========================================================================
// == THE ORACLE GAME - SCRIPT.JS - v25.0 (Partidas Personalizadas)    ==
// ========================================================================
// - IMPLEMENTADO: Sistema de creación de partidas personalizadas (Custom Lobbies).
// - NUEVO: El anfitrión configura límite de preguntas y tiempo de ronda.
// - NUEVO: Pantalla de elección de rol dinámica una vez que el invitado se une.
// - MEJORADO: El servidor (Cartero v2.0) ahora gestiona estados de partida complejos.

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    // Los valores por defecto se sobreescriben con la config de la partida
    questionsLimit: 20, 
    roundTime: 45, // Tiempo por ronda en segundos (a implementar en el futuro)
    typewriterSpeed: 45,
    challengeGraceTime: 20000,
    suggestionLimit: 5,
    suggestionStart: 5
};
const phrases = {
    challengeOracle: "Tu humilde tarea será adivinar el ser, real o ficticio, que yo, el Gran Oráculo, he concebido en mi mente. Tienes {limit} preguntas para desvelar mi enigma. Úsalas con sabiduría. ¿Aceptas este desafío a tu intelecto?",
    challengeClassic: "Concentra tu mente mortal. Piensa en un ser, real o ficticio. Yo haré {limit} preguntas para leer tus pensamientos, y tú solo podrás responderme 'Sí', 'No' y sus variantes. No intentes engañarme. ¿Estás listo?",
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
    graceTimer: null,
    // Nuevo estado para la configuración de la partida
    gameConfig: {} 
};

// --- CONEXIÓN CON SERVIDORES (VERSIÓN PARA PRODUCCIÓN EN VERCEL) ---
const ALE_URL = 'https://889fe04e-996f-4127-afa0-24c10385465d-00-1wd8ak7x1x36.janeway.replit.dev/api/execute';
const REPLIT_URL = 'https://ff849e56-b6b6-4619-8495-996867c9bc5c-00-1rg9nfq7thllg.picard.replit.dev/';


// --- SELECTORES DEL DOM (Ampliados para Partidas Personalizadas) ---
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
        dueloOraculoInput: document.getElementById('duelo-oraculo-input'),
        dueloOraculoSendBtn: document.getElementById('duelo-oraculo-send-btn')
    },
    popups: { 
        guess: document.getElementById('guess-popup'), 
        suggestion: document.getElementById('suggestion-popup'),
        customGame: document.getElementById('custom-game-popup')
    },
    guessPopup: {
        brainText: document.getElementById('guess-popup-brain-text'),
        input: document.getElementById('guess-input'), 
        confirmButton: document.getElementById('confirm-guess-button')
    },
    suggestionPopup: { 
        buttonsContainer: document.getElementById('suggestion-buttons-container') 
    },
    customGamePopup: {
        limitPreguntas: document.getElementById('limit-preguntas'),
        tiempoRonda: document.getElementById('tiempo-ronda'),
        confirmButton: document.getElementById('confirm-create-game-btn')
    },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: {}
};

// ===================================================================
// ===         LÓGICA MULTIJUGADOR (Partidas Personalizadas)       ===
// ===================================================================

function conectarAlServidorDeDuelo() {
    if (state.socket) return; // Evitar reconexiones
    try {
        state.socket = io(REPLIT_URL);
        console.log("Intentando conectar al servidor de duelo en Replit...");

        state.socket.on('connect', () => {
            console.log("✅ ¡Conectado al servidor de duelo! ID de Socket:", state.socket.id);
        });

        // El anfitrión recibe la confirmación y el ID de la sala
        state.socket.on('partida_creada', (data) => {
            state.id_sala = data.id_sala;
            const linkDuelo = `${window.location.origin}${window.location.pathname}?duelo=${state.id_sala}`;
            
            elements.popups.customGame.classList.add('hidden');
            showStageScreen(false); // Mostramos el telón sin animación de apertura
            
            typewriterEffect(elements.stage.dialog, `¡Duelo creado! Comparte este link con tu oponente: <br><br><input type="text" value="${linkDuelo}" style="width: 100%; text-align: center; font-size: 0.7em;" readonly onclick="this.select()"><br><br>Esperando al otro jugador...`);
            elements.stage.menuButtons.innerHTML = `<button class="button-red" data-action="flee-to-title">Cancelar Duelo</button>`;
            elements.stage.menuButtons.classList.remove('hidden');
        });

        // Ambos jugadores reciben la notificación para elegir rol
        state.socket.on('invitado_unido_elegir_roles', () => {
            typewriterEffect(elements.stage.dialog, "¡Tu oponente se ha unido! El cosmos aguarda vuestra decisión. ¿Quién será el Oráculo? El primero en reclamar el poder lo obtendrá.");
            elements.stage.menuButtons.innerHTML = `<button class="menu-button button-purple" data-action="claim-role-oracle">¡Yo seré el Oráculo!</button>`;
            elements.stage.menuButtons.classList.remove('hidden');
        });

        // Ambos jugadores reciben su rol asignado y la configuración
        state.socket.on('partida_lista', (data) => {
            state.rol_jugador = data.rol;
            state.gameConfig = data.config; // Guardamos la configuración de la partida
            config.questionsLimit = parseInt(state.gameConfig.limite_preguntas, 10); // Actualizamos el límite de preguntas
            
            startGame('duelo_1v1');
        });
        
        state.socket.on('pregunta_recibida', (data) => {
            if (state.rol_jugador === 'oraculo') {
                addMessageToChat(data.pregunta, 'player');
                // Habilitamos los controles del Oráculo humano
                elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = false);
                elements.game.dueloOraculoInput.disabled = false;
            }
        });

        state.socket.on('respuesta_recibida', (data) => {
            if (state.rol_jugador === 'adivino') {
                addMessageToChat(data.respuesta, 'brain');
                // Habilitamos los controles del Adivino
                elements.game.input.disabled = false;
                elements.game.askButton.disabled = false;
                elements.game.input.focus();
            }
        });
        
        state.socket.on('error_sala', (data) => {
            alert(data.mensaje);
            window.location.href = window.location.origin + window.location.pathname; // Volver a la página principal
        });

    } catch (e) {
        console.error("Error al cargar o conectar con Socket.IO.", e);
        alert("No se pudo conectar con el servidor multijugador. Por favor, recarga la página.");
    }
}

function iniciarCreacionPartida() {
    // En lugar de crear la partida directamente, mostramos el pop-up de configuración
    elements.popups.customGame.classList.remove('hidden');
}

function confirmarCreacionPartida() {
    const configPartida = {
        limite_preguntas: elements.customGamePopup.limitPreguntas.value,
        tiempo_ronda: elements.customGamePopup.tiempoRonda.value
    };
    
    state.socket.emit('crear_partida_personalizada', { config: configPartida });
    
    // Ocultamos el pop-up y mostramos un mensaje de espera
    elements.popups.customGame.classList.add('hidden');
    typewriterEffect(elements.stage.dialog, "Forjando un nuevo universo para vuestro duelo...");
    elements.stage.menuButtons.classList.add('hidden');
}

function unirseAPartida(id_duelo) {
    state.id_sala = id_duelo;
    
    // Mostramos la pantalla del telón con un mensaje de "uniendo"
    showStageScreen(false);
    typewriterEffect(elements.stage.dialog, `Conectando al duelo ${id_duelo}... Un momento.`);
    elements.stage.menuButtons.classList.add('hidden');

    // Nos aseguramos de estar conectados antes de unirnos
    if (state.socket && state.socket.connected) {
        state.socket.emit('unirse_a_partida', { id_sala: id_duelo });
    } else {
        // Si no estamos conectados, esperamos al evento 'connect' y luego nos unimos
        state.socket.once('connect', () => {
            state.socket.emit('unirse_a_partida', { id_sala: id_duelo });
        });
    }
}

function reclamarRolOraculo() {
    elements.stage.menuButtons.classList.add('hidden');
    typewriterEffect(elements.stage.dialog, "Reclamando el manto del Oráculo... Esperando la confirmación del cosmos.");
    state.socket.emit('elegir_rol', { id_sala: state.id_sala, rol: 'oraculo' });
}


// ===================================================================
// ===           LÓGICA DEL JUEGO (Adaptada para Config)           ===
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
    elements.header.questionCounter.textContent = `0/${config.questionsLimit}`; // Usa el límite de la config
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
        
        // Actualizamos el contador de preguntas con el valor de la configuración
        elements.header.questionCounter.textContent = `0/${config.questionsLimit}`;

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
    elements.header.questionCounter.classList.remove('hidden'); // Mostramos el contador

    if (state.rol_jugador === 'adivino') {
        elements.game.oracleControls.classList.remove('hidden');
        elements.game.suggestionButton.classList.add('hidden'); // Ocultamos sugerencias en duelo por ahora
        elements.game.guessButton.classList.remove('hidden'); // El adivino puede adivinar
        addMessageToChat("Eres el Adivino. Tu oponente es el Oráculo. Tienes " + config.questionsLimit + " preguntas. Haz la primera.", 'system');
    } else if (state.rol_jugador === 'oraculo') {
        elements.game.dueloOraculoControls.classList.remove('hidden');
        addMessageToChat("Eres el Oráculo. Tu oponente tiene " + config.questionsLimit + " preguntas para adivinar. Espera su primera pregunta.", 'system');
        // Deshabilitamos los controles hasta que llegue una pregunta
        elements.game.dueloOraculoControls.querySelectorAll('button').forEach(b => b.disabled = true);
        elements.game.dueloOraculoInput.disabled = true;
    }
}

async function handlePlayerInput() {
    if (state.isAwaitingBrainResponse || !state.isGameActive) return;

    if (state.currentGameMode === 'duelo_1v1') {
        if (state.rol_jugador !== 'adivino') return;
        const questionText = elements.game.input.value.trim();
        if (questionText === '') return;
        
        addMessageToChat(questionText, 'player');
        state.questionCount++;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
        
        state.socket.emit('enviar_pregunta', { id_sala: state.id_sala, pregunta: questionText });
        
        elements.game.input.value = '';
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        
        if (state.questionCount >= config.questionsLimit) {
            // Lógica de fin de juego por preguntas agotadas
            // (Se podría implementar un evento de socket 'fin_por_preguntas')
        }

    } else { // Lógica para modos vs IA
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
        
        if (state.questionCount >= config.suggestionStart) {
            elements.game.suggestionButton.disabled = false;
        }
        if (state.questionCount >= 1) {
            elements.game.guessButton.disabled = false;
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

    // Conectamos al servidor de duelo en cuanto carga la página
    conectarAlServidorDeDuelo();

    // Verificamos si la URL contiene un link de duelo para unirse directamente
    const urlParams = new URLSearchParams(window.location.search);
    const id_duelo = urlParams.get('duelo');
    if (id_duelo) {
        unirseAPartida(id_duelo);
    } else {
        runTitleSequence();
    }

    // --- LISTENERS PRINCIPALES ---
    elements.title.startButton.addEventListener('click', () => showStageScreen(true));
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    
    elements.header.backToMenu.addEventListener('click', () => {
        // Esto ahora es un reseteo forzado, ideal para salir de cualquier estado
        window.location.href = window.location.origin + window.location.pathname;
    });

    // Listener para el pop-up de creación de partida
    elements.customGamePopup.confirmButton.addEventListener('click', confirmarCreacionPartida);
    
    // Listener para los botones de respuesta del Oráculo humano
    elements.game.dueloOraculoControls.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.answer) {
            handleDueloOraculoResponse(e.target.dataset.answer);
        }
    });
    elements.game.dueloOraculoSendBtn.addEventListener('click', () => {
        const customResponse = elements.game.dueloOraculoInput.value.trim();
        if (customResponse) {
            handleDueloOraculoResponse(customResponse);
        }
    });
    elements.game.dueloOraculoInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            const customResponse = elements.game.dueloOraculoInput.value.trim();
            if (customResponse) {
                handleDueloOraculoResponse(customResponse);
            }
        }
    });

    // Listener para los botones del menú principal y submenús
    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (!action) return;

        // Acciones del menú principal
        if (action === 'show-single-player') showSinglePlayerMenu();
        if (action === 'show-multiplayer') showMultiplayerMenu();
        if (action === 'flee-to-title') runTitleSequence();

        // Acciones del submenú de 1 Jugador
        if (action === 'show-challenge-oracle') showChallengeScreen('oracle_ia');
        if (action === 'show-challenge-classic') showChallengeScreen('classic_ia');
        if (action === 'back-to-main-menu') showMainMenu();
        
        // Acciones del submenú Multijugador
        if (action === 'create-1v1-game') iniciarCreacionPartida();
        // if (action === 'create-1vN-game') { /* Lógica futura para 1 vs Varios */ }

        // Acciones de los desafíos
        if (action === 'accept-challenge-oracle') startGame('oracle_ia');
        if (action === 'accept-challenge-classic') handleAcceptClassicChallenge();
        if (action === 'flee-challenge-oracle') showSinglePlayerMenu(phrases.menuOracle.fleeChallengeOracle);
        if (action === 'flee-challenge-classic') showSinglePlayerMenu(phrases.menuOracle.fleeChallengeOracle); // Reutilizamos frase
        
        // Acciones del Modo Clásico (Tiempo para pensar)
        if (action === 'classic-ready') {
            clearTimeout(state.graceTimer);
            startGame('classic_ia');
        }
        if (action === 'classic-need-time') {
            clearTimeout(state.graceTimer);
            showSinglePlayerMenu(phrases.menuOracle.classicStillNeedsTime);
        }

        // Acciones del Duelo 1 vs 1
        if (action === 'claim-role-oracle') reclamarRolOraculo();
    });

    // Listeners para los botones de respuesta del Modo Clásico (vs IA)
    elements.game.classicControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('answer-btn')) {
            handleClassicAnswer(e.target.dataset.answer);
        }
    });

    // Listeners para popups y fin de juego (sin cambios)
    elements.game.guessButton.addEventListener('click', showGuessPopup);
    elements.game.suggestionButton.addEventListener('click', showSuggestionPopup);
    elements.guessPopup.confirmButton.addEventListener('click', confirmGuess);
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action === 'play-again') showStageScreen(true);
            else if (action === 'main-menu') runTitleSequence();
        });
    });
    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) e.target.closest('.popup-overlay').classList.add('hidden'); });
    document.body.addEventListener('click', unlockAudio, { once: true });
    document.body.addEventListener('touchstart', unlockAudio, { once:true });
});


// ===================================================================
// ===               FUNCIONES DE NAVEGACIÓN Y UI                  ===
// ===================================================================

function showStageScreen(withCurtain) {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.brain.classList.remove('hidden');
    elements.stage.dialog.classList.remove('hidden');
    elements.stage.menuButtons.classList.add('hidden');

    const showFinalMenu = () => {
        showMainMenu(phrases.menuOracle.main);
    };

    if (withCurtain) {
        elements.stage.lights.classList.remove('hidden');
        elements.stage.curtainLeft.style.transition = 'none';
        elements.stage.curtainRight.style.transition = 'none';
        elements.stage.curtainLeft.style.width = '50%';
        elements.stage.curtainRight.style.width = '50%';
        
        setTimeout(() => {
            openCurtains(() => {
                setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 1000);
                setTimeout(showFinalMenu, 500);
            }, 1);
        }, 500);
    } else {
        elements.stage.curtainLeft.style.width = '0%';
        elements.stage.curtainRight.style.width = '0%';
        elements.stage.lights.classList.add('hidden');
        showFinalMenu();
    }
}

function showMainMenu(dialogText) {
    const menuHTML = `
        <button class="menu-button button-green" data-action="show-single-player">1 Jugador</button>
        <button class="menu-button button-purple" data-action="show-multiplayer">Multijugador</button>
        <div style="height: 15px;"></div>
        <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
    `;
    typewriterEffect(elements.stage.dialog, dialogText, () => {
        elements.stage.menuButtons.innerHTML = menuHTML;
        elements.stage.menuButtons.classList.remove('hidden');
    });
}

function showSinglePlayerMenu(dialogText = phrases.menuOracle.singlePlayer) {
    const menuHTML = `
        <button class="menu-button button-green" data-action="show-challenge-oracle">Modo Oráculo</button>
        <button class="menu-button button-green" data-action="show-challenge-classic">Modo Clásico</button>
        <div style="height: 15px;"></div>
        <button class="menu-button button-red" data-action="back-to-main-menu">Volver</button>
    `;
    typewriterEffect(elements.stage.dialog, dialogText, () => {
        elements.stage.menuButtons.innerHTML = menuHTML;
        elements.stage.menuButtons.classList.remove('hidden');
    });
}

function showMultiplayerMenu(dialogText = phrases.menuOracle.multiplayer) {
    const menuHTML = `
        <button class="menu-button button-purple" data-action="create-1v1-game">Duelo 1 vs 1</button>
        <button class="menu-button button-grey" data-action="create-1vN-game" disabled>CPU vs Varios (Próximamente)</button>
        <div style="height: 15px;"></div>
        <button class="menu-button button-red" data-action="back-to-main-menu">Volver</button>
    `;
     typewriterEffect(elements.stage.dialog, dialogText, () => {
        elements.stage.menuButtons.innerHTML = menuHTML;
        elements.stage.menuButtons.classList.remove('hidden');
    });
}

function showChallengeScreen(mode) {
    elements.stage.menuButtons.classList.add('hidden');
    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        openCurtains(() => {
            elements.stage.dialog.classList.remove('hidden');
            let challengeText, acceptAction, fleeAction;
            if (mode === 'oracle_ia') {
                challengeText = phrases.challengeOracle.replace('{limit}', config.questionsLimit);
                acceptAction = 'accept-challenge-oracle';
                fleeAction = 'flee-challenge-oracle';
            } else { // classic_ia
                challengeText = phrases.challengeClassic.replace('{limit}', config.questionsLimit);
                acceptAction = 'accept-challenge-classic';
                fleeAction = 'flee-challenge-classic';
            }
            elements.stage.menuButtons.innerHTML = `
                <button class="button-green" data-action="${acceptAction}">Aceptar Reto</button>
                <button class="button-red" data-action="${fleeAction}">Huir</button>
            `;
            typewriterEffect(elements.stage.dialog, challengeText, () => {
                elements.stage.menuButtons.classList.remove('hidden');
            });
        }, 2.5);
    }, 1);
}

function handleAcceptClassicChallenge() {
    elements.stage.menuButtons.classList.add('hidden');
    typewriterEffect(elements.stage.dialog, phrases.menuOracle.classicGraceTime, () => {
        elements.stage.menuButtons.innerHTML = `
            <button class="button-green" data-action="classic-ready">Estoy Listo</button>
            <button class="button-red" data-action="classic-need-time">Necesito más tiempo</button>
        `;
        elements.stage.menuButtons.classList.remove('hidden');
        
        state.graceTimer = setTimeout(() => {
            showSinglePlayerMenu(phrases.menuOracle.classicStillNeedsTime);
        }, config.challengeGraceTime);
    });
}

// ===================================================================
// ===        FUNCIONES DE JUEGO, POPUPS Y UTILIDADES              ===
// ===================================================================
// (El resto de las funciones como callALE, prepararInterfaz, addMessageToChat, 
//  typewriterEffect, popups, timers, endGame, etc., se mantienen aquí sin cambios)

// ... (Aquí iría todo el resto del código que ya teníamos, como callALE, prepararInterfazModoOraculoIA, etc.)
// Para mantener la respuesta concisa, no lo repito, pero debe estar aquí.
// Las funciones importantes que deben estar aquí son:
// - callALE
// - prepararInterfazModoOraculoIA
// - prepararInterfazModoClasicoIA
// - handleClassicAnswer
// - showGuessPopup, confirmGuess
// - showSuggestionPopup, handleSuggestion
// - startTimer, stopTimer
// - endGame
// - addMessageToChat, typewriterEffect
// - unlockAudio, adjustScreenHeight
// - closeCurtains, openCurtains
// - runTitleSequence
// ... y cualquier otra función auxiliar que ya existiera.

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
        addMessageToChat(`Mi conexión con el cosmos ha sido interrumpida. No puedo procesar tu petición.`, 'system');
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
    
    state.secretCharacter = "¡Secreto!"; // Ya no recibimos el dossier
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

    addMessageToChat("Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas.", 'brain');
    
    const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
    if (respuesta && !respuesta.error && respuesta.siguiente_pregunta) {
        state.isGameActive = true;
        state.questionCount++;
        elements.header.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
        addMessageToChat(respuesta.siguiente_pregunta, 'brain');
    } else {
        addMessageToChat("Mi mente está confusa para este modo. Vuelve al menú.", 'brain');
    }
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
            // Aquí podrías añadir botones de Sí/No para confirmar la adivinanza
            state.isGameActive = false;
        } else if (respuesta.accion === "Rendirse") {
            addMessageToChat(respuesta.texto, 'brain');
            state.isGameActive = false;
        }
    } else {
        addMessageToChat("No he podido procesar tu respuesta.", 'brain');
    }

    if (state.questionCount >= config.questionsLimit && state.isGameActive) {
        // Lógica para cuando el Oráculo se queda sin preguntas
    }
}

function showGuessPopup() {
    elements.popups.guess.classList.remove('hidden');
    elements.guessPopup.brainText.textContent = phrases.guessPopup.initial;
    elements.guessPopup.input.focus();
}

function confirmGuess() {
    const guess = elements.guessPopup.input.value.trim();
    if (guess === '') {
        elements.guessPopup.brainText.textContent = phrases.guessPopup.strike1;
        return;
    }
    // Lógica para verificar la adivinanza (requiere una llamada a ALE)
    console.log("Adivinanza del jugador:", guess);
    elements.popups.guess.classList.add('hidden');
    elements.guessPopup.input.value = '';
    // Aquí iría la llamada a ALE para verificar y luego llamar a endGame(true) o endGame(false)
}

async function showSuggestionPopup() {
    const btn = elements.game.suggestionButton;
    if (state.suggestionUses <= 0) return;

    btn.disabled = true;
    const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_sugerencia" });

    if (respuesta && !respuesta.error && respuesta.sugerencias) {
        state.suggestionUses--;
        btn.textContent = `Sugerencia (${state.suggestionUses})`;
        
        const container = elements.suggestionPopup.buttonsContainer;
        container.innerHTML = '';
        respuesta.sugerencias.forEach(sug => {
            const sugBtn = document.createElement('button');
            sugBtn.className = 'suggestion-option-button';
            sugBtn.textContent = sug;
            sugBtn.onclick = () => {
                elements.game.input.value = sug;
                elements.popups.suggestion.classList.add('hidden');
                handlePlayerInput();
            };
            container.appendChild(sugBtn);
        });
        elements.popups.suggestion.classList.remove('hidden');
    } else {
        addMessageToChat("El cosmos no me ofrece ninguna visión clara en este momento.", 'system');
    }
    
    setTimeout(() => {
        if (state.isGameActive) btn.disabled = false;
    }, 5000); // Cooldown para evitar spam
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
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    
    // Para obtener el nombre del personaje en caso de derrota, necesitaríamos una llamada a ALE
    const secretName = state.secretCharacter || "el enigma";

    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${secretName}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        let loseMessage = "";
        switch (reason) {
            case "questions": loseMessage = `Has agotado tus ${config.questionsLimit} preguntas. El personaje era ${secretName}.`; break;
            default: loseMessage = `Has fallado. El personaje era ${secretName}.`; break;
        }
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
    
    const interval = setInterval(() => {
        if (i < processedText.length) {
            element.innerHTML += processedText.charAt(i);
            i++;
            elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
        } else {
            clearInterval(interval);
            if (callback) callback();
        }
    }, config.typewriterSpeed);
}

function unlockAudio() { /* Lógica de audio eliminada por simplicidad */ }

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
    elements.title.introBrain.classList.remove('hidden');
    elements.title.introBrain.style.animation = 'none'; // Resetea la animación
    
    setTimeout(() => {
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
    }, 500);
    setTimeout(() => {
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
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
