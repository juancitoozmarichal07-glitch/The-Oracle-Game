// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v13.1 ("El Depurador")          ==
// ===================================================================
// - CORREGIDO: Error fatal "addMessageToChat is not defined" moviendo la función.
// - CORREGIDO: Error fatal "Cannot read properties of undefined" añadiendo
//   el backToMenu a la lista de elements.

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    suggestionCooldown: 15000,
    guessButtonCooldown: 15000,
    suggestionLimit: 5,
};
const phrases = {
    challenge: "Tu humilde tarea será adivinar el ser, real o ficticio, que yo, el Gran Oráculo, he concebido. Tienes 20 preguntas.",
    guessPopup: {
        initial: "La hora de la verdad se acerca... Escribe al ser que crees que estoy pensando, mortal.",
        strike1: "No puedo adivinar el vacío. ¡Escribe un nombre!",
        strike2: "¿Intentas agotar mi paciencia? Escribe una respuesta o cancela.",
        strike3: "Has agotado mi paciencia. El privilegio de adivinar te ha sido revocado... por ahora."
    }
};
let state = {
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isAwaitingBrainResponse: false,
    suggestionUses: 0,
    lastSuggestionTimestamp: 0,
    guessPopupPatience: 3,
    currentGameMode: null
};

// --- CONEXIÓN CON A.L.E. ---
const ALE_URL = '/api/execute';

async function callALE(datos_peticion) {
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos_peticion)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Error desconocido del servidor." }));
            console.error("Error de A.L.E.:", errorData);
            addMessageToChat(`Error del Motor: ${errorData.error}`, "brain");
            return { error: true };
        }
        return await response.json();
    } catch (error) {
        console.error("Error de Conexión con A.L.E.:", error);
        addMessageToChat("Error de Conexión: El motor A.L.E. parece estar desconectado.", "brain");
        return { error: true };
    }
}

// --- SELECTORES DEL DOM (Completos y Corregidos) ---
const elements = {
    arcadeScreen: document.getElementById('arcade-screen'),
    screens: { title: document.getElementById('title-screen'), stage: document.getElementById('game-stage'), mainGame: document.getElementById('main-game-screen'), win: document.getElementById('win-screen'), lose: document.getElementById('lose-screen') },
    title: { layout: document.getElementById('title-layout'), introBrain: document.getElementById('intro-brain'), startButton: document.getElementById('start-button'), exitButton: document.getElementById('exit-button'), lightning: document.getElementById('lightning-overlay') },
    stage: { menuButtons: document.getElementById('menu-buttons'), dialog: document.getElementById('stage-dialog'), curtainLeft: document.getElementById('curtain-left'), curtainRight: document.getElementById('curtain-right') },
    game: {
        chatHistory: document.getElementById('chat-history'),
        questionCounter: document.getElementById('question-counter'),
        suggestionButton: document.getElementById('suggestion-button'),
        guessButton: document.getElementById('guess-button'),
        oracleControls: document.getElementById('oracle-mode-controls'),
        classicControls: document.getElementById('classic-mode-controls'),
        input: document.getElementById('user-question-input'),
        askButton: document.getElementById('ask-button'),
        backToMenu: document.getElementById('back-to-menu-button') // <-- ¡AÑADIDO EL ELEMENTO QUE FALTABA!
    },
    popups: { guess: document.getElementById('guess-popup'), suggestion: document.getElementById('suggestion-popup') },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { buttonsContainer: document.getElementById('suggestion-buttons-container') },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: { applause: document.getElementById('applause-sound'), thunder: document.getElementById('thunder-sound'), materialize: document.getElementById('materialize-sound'), curtain: document.getElementById('curtain-sound'), typewriter: document.getElementById('typewriter-sound') }
};

// --- LÓGICA DE MENSAJES (Movida al principio para estar siempre disponible) ---
function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : '👤';
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';
    const prefix = sender === 'brain' ? 'Oráculo: ' : 'Tú: ';
    const fullText = text ? prefix + text : prefix; // Previene "Oráculo: undefined"
    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
    typewriterEffect(textContainer, fullText, callback);
}

// --- LÓGICA DE AJUSTE DE PANTALLA ---
function adjustScreenHeight() { if (elements.arcadeScreen) { elements.arcadeScreen.style.height = `${window.innerHeight}px`; } }

// --- LÓGICA PRINCIPAL DEL JUEGO ---

function resetGameState() {
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isAwaitingBrainResponse = false;
    state.suggestionUses = 0;
    state.lastSuggestionTimestamp = 0;
    state.guessPopupPatience = 3;
    elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.suggestionButton.textContent = `Sugerencia ${config.suggestionLimit}/${config.suggestionLimit}`;
    elements.game.suggestionButton.classList.remove('button-cooldown');
    elements.game.guessButton.classList.remove('button-cooldown');
    elements.game.guessButton.textContent = "¡Adivinar!";
}

async function startGame(mode) {
    state.currentGameMode = mode;
    closeCurtains(async () => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');
        resetGameState();

        if (mode === 'oracle') {
            prepararInterfazModoOraculo();
            addMessageToChat("Concibiendo un nuevo enigma del cosmos...", "brain");
            const respuesta = await callALE({ skillset_target: "oracle", accion: "iniciar_juego" });
            if (respuesta.error) {
                addMessageToChat("No he podido concebir un enigma. Mi mente está en conflicto. Inténtalo de nuevo.", "brain");
                return;
            }
            state.secretCharacter = respuesta.personaje_secreto;
            console.log("PERSONAJE CREADO POR A.L.E.:", state.secretCharacter);
            elements.game.chatHistory.innerHTML = '';
            state.isGameActive = true;
            addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
                elements.game.input.disabled = false;
                elements.game.askButton.disabled = false;
                elements.game.input.focus();
            });
        } else if (mode === 'classic') {
            prepararInterfazModoClasico();
        }
    }, 1);
}

async function handlePlayerInput() {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    const questionText = elements.game.input.value.trim();
    if (questionText === '') return;

    state.isAwaitingBrainResponse = true;
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;
    addMessageToChat(questionText, 'player');
    elements.game.input.value = '';
    state.questionCount++;
    elements.game.questionCounter.textContent = `Pregunta: ${state.questionCount}/${config.questionsLimit}`;
    
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
    addMessageToChat(fullResponse, 'brain', () => {
        if (respuesta.game_over === true) {
            setTimeout(() => endGame(false, "patience"), 1000);
            return;
        }
        
        if (state.questionCount === 1 && elements.game.suggestionButton.disabled) {
            elements.game.suggestionButton.disabled = false;
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
    });
}

async function showSuggestions() {
    const now = Date.now();
    const timeLeft = Math.ceil((state.lastSuggestionTimestamp + config.suggestionCooldown - now) / 1000);
    if (timeLeft > 0) return;

    if (state.suggestionUses >= config.suggestionLimit) {
        addMessageToChat("Has agotado todas tus sugerencias para esta partida.", "brain");
        elements.game.suggestionButton.disabled = true;
        return;
    }

    state.lastSuggestionTimestamp = now;
    elements.game.suggestionButton.disabled = true;
    elements.game.suggestionButton.classList.add('button-cooldown');

    let countdown = Math.ceil(config.suggestionCooldown / 1000);
    elements.game.suggestionButton.textContent = `Espera ${countdown}s`;
    const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
            elements.game.suggestionButton.textContent = `Espera ${countdown}s`;
        } else {
            clearInterval(countdownInterval);
            elements.game.suggestionButton.disabled = false;
            elements.game.suggestionButton.classList.remove('button-cooldown');
            const remainingUses = config.suggestionLimit - state.suggestionUses;
            elements.game.suggestionButton.textContent = `Sugerencia ${remainingUses}/${config.suggestionLimit}`;
        }
    }, 1000);

    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'El Oráculo está meditando...';
    elements.popups.suggestion.classList.remove('hidden');

    const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_sugerencia" });

    if (!respuesta.error && respuesta.sugerencias && respuesta.sugerencias.length > 0) {
        container.innerHTML = '';
        respuesta.sugerencias.forEach(qText => {
            const button = document.createElement('button');
            button.className = 'suggestion-option-button';
            button.textContent = qText;
            button.onclick = () => {
                elements.game.input.value = qText;
                elements.game.input.focus();
                elements.popups.suggestion.classList.add('hidden');
                state.suggestionUses++;
                const remainingUses = config.suggestionLimit - state.suggestionUses;
                if (countdown <= 0) {
                     elements.game.suggestionButton.textContent = `Sugerencia ${remainingUses}/${config.suggestionLimit}`;
                }
                if (state.suggestionUses >= config.suggestionLimit) {
                    elements.game.suggestionButton.disabled = true;
                    elements.game.suggestionButton.textContent = "Sugerencias 0/5";
                    clearInterval(countdownInterval);
                }
            };
            container.appendChild(button);
        });
    } else {
        container.innerHTML = 'No hay sugerencias dignas en este momento.';
        setTimeout(() => { elements.popups.suggestion.classList.add('hidden'); }, 2000);
    }
}

function endGame(isWin, reason = "guess") {
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');

    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.nombre}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        let loseMessage = "";
        if (reason === "patience") {
            loseMessage = `El Oráculo ha agotado su paciencia cósmica. El personaje era ${state.secretCharacter.nombre}.`;
        } else if (reason === "guess_abuse") {
            loseMessage = `Has agotado la paciencia del Oráculo con tus intentos vacíos. El personaje era ${state.secretCharacter.nombre}.`;
        } else { // "questions" o "guess"
            loseMessage = `Has fallado. El personaje era ${state.secretCharacter.nombre}. Una mente simple no puede comprender lo complejo.`;
        }
        elements.endScreens.loseMessage.textContent = loseMessage;
        elements.screens.lose.classList.remove('hidden');
    }
}

function showGuessPopup() {
    state.guessPopupPatience = 3;
    elements.guessPopup.instruction.textContent = phrases.guessPopup.initial;
    elements.guessPopup.input.value = '';
    elements.popups.guess.classList.remove('hidden');
    elements.guessPopup.input.focus();
}

function handleGuessAttempt() {
    const guess = elements.guessPopup.input.value.trim();
    if (guess === '') {
        state.guessPopupPatience--;
        elements.guessPopup.content.classList.add('shake');
        let message = '';
        switch (state.guessPopupPatience) {
            case 2: message = phrases.guessPopup.strike1; break;
            case 1: message = phrases.guessPopup.strike2; break;
            case 0:
                message = phrases.guessPopup.strike3;
                setTimeout(() => {
                    elements.popups.guess.classList.add('hidden');
                    endGame(false, "guess_abuse");
                }, 1000);
                break;
        }
        elements.guessPopup.instruction.textContent = message;
        setTimeout(() => { elements.guessPopup.content.classList.remove('shake'); }, 500);
        return;
    }
    elements.popups.guess.classList.add('hidden');
    const isCorrect = guess.toLowerCase() === (state.secretCharacter?.nombre.toLowerCase() || '');
    endGame(isCorrect);
}

// --- FUNCIONES VISUALES Y DE NAVEGACIÓN ---

function unlockAudio() { Object.values(elements.sounds).forEach(sound => { if (sound) { sound.play().then(() => { sound.pause(); sound.currentTime = 0; }).catch(e => {}); } }); document.body.removeEventListener('click', unlockAudio); document.body.removeEventListener('touchstart', unlockAudio); }
function typewriterEffect(element, text, callback) { let i = 0; element.textContent = ''; if (elements.sounds.typewriter) { elements.sounds.typewriter.currentTime = 0; elements.sounds.typewriter.play().catch(e => {}); } const interval = setInterval(() => { if (i < text.length) { element.textContent += text.charAt(i); i++; } else { clearInterval(interval); if (elements.sounds.typewriter) { elements.sounds.typewriter.pause(); } if (callback) callback(); } }, config.typewriterSpeed); }
function runTitleSequence() { Object.values(elements.screens).forEach(s => s.classList.add('hidden')); elements.screens.title.classList.remove('hidden'); elements.title.layout.classList.add('hidden'); elements.title.introBrain.classList.add('hidden'); setTimeout(() => { if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {}); elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); }, 500); setTimeout(() => { if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {}); elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); if (elements.sounds.materialize) elements.sounds.materialize.play().catch(e => {}); elements.title.introBrain.classList.remove('hidden'); elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out'; }, 1500); setTimeout(() => { elements.title.introBrain.classList.add('hidden'); if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {}); elements.title.lightning.classList.add('flash-long'); setTimeout(() => { elements.title.lightning.classList.remove('flash-long'); elements.title.layout.classList.remove('hidden'); }, 2000); }, 4000); }
function showGameStage() { Object.values(elements.screens).forEach(s => s.classList.add('hidden')); elements.screens.stage.classList.remove('hidden'); const stage = document.getElementById('game-stage'); if(stage) { stage.querySelector('#stage-brain').classList.add('hidden'); stage.querySelector('#stage-dialog').classList.add('hidden'); stage.querySelector('#stage-lights').classList.remove('hidden'); stage.querySelector('#menu-buttons').innerHTML = `<button class="menu-button button-green" data-action="play-oracle">Modo Oráculo</button><button class="menu-button button-grey" data-action="play-classic">Modo Clásico</button><button class="menu-button button-red" data-action="flee-to-title">Huir</button>`; stage.querySelector('#menu-buttons').classList.remove('hidden'); stage.querySelector('#curtain-left').style.transition = 'width 1s ease-in-out'; stage.querySelector('#curtain-right').style.transition = 'width 1s ease-in-out'; stage.querySelector('#curtain-left').style.width = '50%'; stage.querySelector('#curtain-right').style.width = '50%'; setTimeout(() => { if (elements.sounds.applause) elements.sounds.applause.play().catch(e => {}); openCurtains(null, 1); }, 1000); setTimeout(() => { stage.querySelector('#stage-lights').classList.add('hidden'); }, 2000); setTimeout(() => { stage.querySelector('#stage-brain').classList.remove('hidden'); }, 2200); setTimeout(() => { stage.querySelector('#stage-dialog').classList.remove('hidden'); typewriterEffect(stage.querySelector('#stage-dialog'), "El conocimiento aguarda al audaz. Elige tu camino."); }, 2700); } }
function showChallengeScreen() { const stage = document.getElementById('game-stage'); if(stage) { stage.querySelector('#menu-buttons').classList.add('hidden'); closeCurtains(() => { stage.querySelector('#stage-dialog').classList.add('hidden'); openCurtains(() => { stage.querySelector('#stage-dialog').classList.remove('hidden'); stage.querySelector('#menu-buttons').innerHTML = `<button class="button-green" data-action="accept-challenge">Aceptar Reto</button><button class="button-red" data-action="flee-challenge">Huir</button>`; stage.querySelector('#menu-buttons').classList.remove('hidden'); typewriterEffect(stage.querySelector('#stage-dialog'), phrases.challenge); }, 2.5); }, 1); } }
function prepararInterfazModoOraculo() { elements.game.oracleControls.classList.remove('hidden'); elements.game.classicControls.classList.add('hidden'); elements.game.suggestionButton.classList.remove('hidden'); elements.game.guessButton.textContent = "¡Adivinar!"; elements.game.input.disabled = true; elements.game.askButton.disabled = true; }
function prepararInterfazModoClasico() { elements.game.oracleControls.classList.add('hidden'); elements.game.classicControls.classList.remove('hidden'); elements.game.suggestionButton.classList.add('hidden'); elements.game.guessButton.textContent = "¡Adivina ahora!"; addMessageToChat("Oráculo: Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas. Responde con sinceridad.", 'brain', () => { setTimeout(() => { addMessageToChat("Oráculo: ¿Tu personaje es un hombre?", 'brain'); }, 1000); }); }
function closeCurtains(callback, speed = 1) { const left = document.getElementById('curtain-left'); const right = document.getElementById('curtain-right'); if(left && right) { left.style.width = '50%'; right.style.width = '50%'; } setTimeout(callback, speed * 1000 + 100); }
function openCurtains(callback, speed = 1) { if (elements.sounds.curtain) elements.sounds.curtain.play().catch(e => {}); const left = document.getElementById('curtain-left'); const right = document.getElementById('curtain-right'); if(left && right) { left.style.width = '0%'; right.style.width = '0%'; } if (callback) setTimeout(callback, speed * 1000 + 100); }

// --- PUNTO DE ENTRADA ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Página cargada. Asignando eventos (v13.1 - El Depurador).");
    
    adjustScreenHeight();
    window.addEventListener('resize', adjustScreenHeight);

    elements.title.startButton.addEventListener('click', showGameStage);
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.game.guessButton.addEventListener('click', showGuessPopup);
    elements.guessPopup.confirmButton.addEventListener('click', handleGuessAttempt);
    elements.game.suggestionButton.addEventListener('click', showSuggestions);
    elements.game.backToMenu.addEventListener('click', () => closeCurtains(showGameStage, 1));
    
    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) { e.target.closest('.popup-overlay').classList.add('hidden'); } });

    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'play-oracle') showChallengeScreen();
        if (action === 'play-classic') startGame('classic');
        if (action === 'accept-challenge') startGame('oracle');
        if (action === 'flee-to-title' || action === 'flee-challenge') showGameStage();
    });

    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') { showGameStage(); } 
            else if (action === 'main-menu') { runTitleSequence(); }
        });
    });

    document.body.addEventListener('click', unlockAudio);
    document.body.addEventListener('touchstart', unlockAudio);

    runTitleSequence();
});
