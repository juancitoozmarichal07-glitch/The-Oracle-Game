// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v14.1 (Desbloqueo de Audio)    ==
// ===================================================================

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    suggestionCooldown: 15000,
    suggestionLimit: 5,
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
    apiError: "Mi mente está... nublada. No puedo procesar tu petición ahora.",
    incomprehensible: "No he podido comprender tu galimatías. Inténtalo de nuevo."
};
let state = {
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isAwaitingBrainResponse: false,
    conversationHistory: [],
    suggestionUses: 0,
    lastSuggestionTimestamp: 0,
    guessPopupPatience: 3,
    characterHistory: []
};

// --- CONEXIÓN CON A.L.E. ---
// La URL de tu backend "siempre despierto" en Render
const ALE_URL = 'https://oracle-game-pwa.onrender.com/execute';
async function callALE(datos_peticion) {
    datos_peticion.skillset_target = "oracle";
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos_peticion)
        });
        if (!response.ok) {
            const errorData = await response.json();
            console.error("Error de A.L.E.:", errorData);
            addMessageToChat(`Error del Motor: ${errorData.error || 'Fallo desconocido'}`, "brain");
            return { error: true };
        }
        return await response.json();
    } catch (error) {
        console.error("Error de Conexión con A.L.E.:", error);
        addMessageToChat("Error de Conexión: El motor A.L.E. parece estar desconectado.", "brain");
        return { error: true };
    }
}

// --- SELECTORES DEL DOM ---
const elements = {
    arcadeScreen: document.getElementById('arcade-screen'),
    screens: { title: document.getElementById('title-screen'), stage: document.getElementById('game-stage'), mainGame: document.getElementById('main-game-screen'), win: document.getElementById('win-screen'), lose: document.getElementById('lose-screen') },
    title: { layout: document.getElementById('title-layout'), introBrain: document.getElementById('intro-brain'), startButton: document.getElementById('start-button'), exitButton: document.getElementById('exit-button'), lightning: document.getElementById('lightning-overlay') },
    stage: { lights: document.getElementById('stage-lights'), content: document.getElementById('stage-content-container'), curtainLeft: document.getElementById('curtain-left'), curtainRight: document.getElementById('curtain-right'), brain: document.getElementById('stage-brain'), dialog: document.getElementById('stage-dialog'), menuButtons: document.getElementById('menu-buttons') },
    game: { chatHistory: document.getElementById('chat-history'), questionCounter: document.getElementById('question-counter'), input: document.getElementById('user-question-input'), askButton: document.getElementById('ask-button'), suggestionButton: document.getElementById('suggestion-button'), guessButton: document.getElementById('guess-button'), backToMenu: document.getElementById('back-to-menu-button') },
    popups: { guess: document.getElementById('guess-popup'), suggestion: document.getElementById('suggestion-popup') },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), brainIcon: document.getElementById('guess-popup-brain-icon'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { buttonsContainer: document.getElementById('suggestion-buttons-container') },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: { 
        applause: document.getElementById('applause-sound'),
        thunder: document.getElementById('thunder-sound'),
        materialize: document.getElementById('materialize-sound'),
        curtain: document.getElementById('curtain-sound'),
        typewriter: document.getElementById('typewriter-sound')
    }
};

// --- LÓGICA PRINCIPAL DEL JUEGO ---

function resetGameState() {
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isAwaitingBrainResponse = false;
    state.conversationHistory = [];
    state.suggestionUses = 0;
    state.lastSuggestionTimestamp = 0;
    elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.suggestionButton.textContent = `Sugerencia ${config.suggestionLimit}/${config.suggestionLimit}`;
}

async function startGame() {
    closeCurtains(async () => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');
        resetGameState();
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        addMessageToChat("Concibiendo un nuevo enigma del cosmos...", "brain");
        const respuesta = await callALE({ accion: "iniciar_juego" });
        if (respuesta.error) return;
        state.secretCharacter = respuesta.personaje_secreto;
        console.log("PERSONAJE CREADO POR A.L.E.:", state.secretCharacter);
        elements.game.chatHistory.innerHTML = '';
        state.isGameActive = true;
        addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
            elements.game.input.disabled = false;
            elements.game.askButton.disabled = false;
            elements.game.input.focus();
        });
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
    state.conversationHistory.push({ role: 'user', content: questionText });
    const respuesta = await callALE({ accion: "procesar_pregunta", pregunta: questionText });
    if (respuesta.error) {
        state.isAwaitingBrainResponse = false;
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        return;
    }
    const { respuesta: textoRespuesta, aclaracion } = respuesta;
    let fullResponse = textoRespuesta + (aclaracion ? `. ${aclaracion}` : '');
    addMessageToChat(fullResponse, 'brain');
    state.conversationHistory.push({ role: 'assistant', content: fullResponse });
    if (state.questionCount === 1 && elements.game.suggestionButton.disabled) {
        elements.game.suggestionButton.disabled = false;
        elements.game.guessButton.disabled = false;
    }
    state.isAwaitingBrainResponse = false;
    if (state.isGameActive) {
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.input.focus();
    }
    if (state.isGameActive && state.questionCount >= config.questionsLimit) endGame(false);
}

async function showSuggestions() {
    if (state.suggestionUses >= config.suggestionLimit) {
        addMessageToChat("Has agotado todas tus sugerencias para esta partida.", "brain");
        elements.game.suggestionButton.disabled = true;
        return;
    }
    const now = Date.now();
    if (now - state.lastSuggestionTimestamp < config.suggestionCooldown) {
        const timeLeft = Math.ceil((config.suggestionCooldown - (now - state.lastSuggestionTimestamp)) / 1000);
        addMessageToChat(`Debes esperar ${timeLeft} segundos para pedir otra sugerencia.`, "brain");
        return;
    }
    state.lastSuggestionTimestamp = now;
    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'El Oráculo está meditando...';
    elements.popups.suggestion.classList.remove('hidden');
    const respuesta = await callALE({ accion: "pedir_sugerencia", historial: state.conversationHistory });
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
                elements.game.suggestionButton.textContent = `Sugerencia ${remainingUses}/${config.suggestionLimit}`;
                if (remainingUses <= 0) {
                    elements.game.suggestionButton.disabled = true;
                }
            };
            container.appendChild(button);
        });
    } else {
        container.innerHTML = 'No hay sugerencias dignas en este momento.';
        setTimeout(() => { elements.popups.suggestion.classList.add('hidden'); }, 2000);
    }
}

function endGame(isWin) {
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');
    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.nombre}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        elements.endScreens.loseMessage.textContent = `Has fallado. El personaje era ${state.secretCharacter.nombre}. Una mente simple no puede comprender lo complejo.`;
        elements.screens.lose.classList.remove('hidden');
    }
}

function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : '👤';
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';
    const prefix = sender === 'brain' ? 'Oráculo: ' : 'Tú: ';
    const fullText = prefix + text;
    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
    typewriterEffect(textContainer, fullText, callback);
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
            case 0: message = phrases.guessPopup.strike3; break;
        }
        elements.guessPopup.instruction.textContent = message;
        setTimeout(() => {
            elements.guessPopup.content.classList.remove('shake');
            if (state.guessPopupPatience <= 0) {
                elements.popups.guess.classList.add('hidden');
                elements.game.guessButton.disabled = true;
                setTimeout(() => { if (state.isGameActive) elements.game.guessButton.disabled = false; }, config.guessButtonCooldown);
            }
        }, 500);
        return;
    }
    elements.popups.guess.classList.add('hidden');
    const isCorrect = guess.toLowerCase() === state.secretCharacter.nombre.toLowerCase();
    endGame(isCorrect);
}

// --- FUNCIONES VISUALES Y DE NAVEGACIÓN ---

// === NUEVA FUNCIÓN DE DESBLOQUEO DE AUDIO ===
function unlockAudio() {
    console.log("Intentando desbloquear el audio con la primera interacción...");
    Object.values(elements.sounds).forEach(sound => {
        if (sound) {
            sound.play().then(() => {
                sound.pause();
                sound.currentTime = 0;
            }).catch(e => {
                // Este error es esperado y normal si el navegador aún no lo permite.
            });
        }
    });
    // Una vez que se intenta, eliminamos el listener para no hacerlo más.
    document.body.removeEventListener('click', unlockAudio);
    document.body.removeEventListener('touchstart', unlockAudio);
    console.log("Listeners de desbloqueo de audio eliminados.");
}

function typewriterEffect(element, text, callback) {
    let i = 0;
    element.textContent = '';
    if (elements.sounds.typewriter) {
        elements.sounds.typewriter.currentTime = 0;
        elements.sounds.typewriter.play().catch(e => {}); // Catch por si el audio aún no está desbloqueado
    }
    const interval = setInterval(() => {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
        } else {
            clearInterval(interval);
            if (elements.sounds.typewriter) {
                elements.sounds.typewriter.pause();
            }
            if (callback) callback();
        }
    }, config.typewriterSpeed);
}

function runTitleSequence() {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.title.classList.remove('hidden');
    elements.title.layout.classList.add('hidden');
    elements.title.introBrain.classList.add('hidden');
    setTimeout(() => {
        if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {});
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
    }, 500);
    setTimeout(() => {
        if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {});
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
        if (elements.sounds.materialize) elements.sounds.materialize.play().catch(e => {});
        elements.title.introBrain.classList.remove('hidden');
        elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out';
    }, 1500);
    setTimeout(() => {
        elements.title.introBrain.classList.add('hidden');
        if (elements.sounds.thunder) elements.sounds.thunder.play().catch(e => {});
        elements.title.lightning.classList.add('flash-long');
        setTimeout(() => {
            elements.title.lightning.classList.remove('flash-long');
            elements.title.layout.classList.remove('hidden');
        }, 2000);
    }, 4000);
}

function showGameStage() {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.brain.classList.add('hidden');
    elements.stage.dialog.classList.add('hidden');
    elements.stage.lights.classList.remove('hidden');
    elements.stage.menuButtons.innerHTML = `
        <button class="menu-button button-green" data-action="play-alternativo">Modo Oráculo</button>
        <button class="menu-button button-grey" data-action="play-clasico">Modo Clásico (Próximamente)</button>
        <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
    `;
    elements.stage.menuButtons.classList.remove('hidden');
    elements.stage.curtainLeft.style.transition = 'width 1s ease-in-out';
    elements.stage.curtainRight.style.transition = 'width 1s ease-in-out';
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    setTimeout(() => {
        if (elements.sounds.applause) elements.sounds.applause.play().catch(e => {});
        openCurtains(null, 1);
    }, 1000);
    setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 2000);
    setTimeout(() => { elements.stage.brain.classList.remove('hidden'); }, 2200);
    setTimeout(() => {
        elements.stage.dialog.classList.remove('hidden');
        const randomWelcome = "El conocimiento aguarda al audaz. Elige tu camino.";
        typewriterEffect(elements.stage.dialog, randomWelcome);
    }, 2700);
}

function showChallengeScreen() {
    elements.stage.menuButtons.classList.add('hidden');
    closeCurtains(() => {
        elements.stage.dialog.classList.add('hidden');
        openCurtains(() => {
            elements.stage.dialog.classList.remove('hidden');
            elements.stage.menuButtons.innerHTML = `
                <button class="button-green" data-action="accept-challenge">Aceptar Reto</button>
                <button class="button-red" data-action="flee-challenge">Huir</button>
            `;
            elements.stage.menuButtons.classList.remove('hidden');
            typewriterEffect(elements.stage.dialog, phrases.challenge);
        }, 2.5);
    }, 1);
}

function closeCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    setTimeout(callback, speed * 1000 + 100);
}

function openCurtains(callback, speed = 1) {
    if (elements.sounds.curtain) elements.sounds.curtain.play().catch(e => {});
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '0%';
    elements.stage.curtainRight.style.width = '0%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}

// --- EVENT LISTENERS (PUNTO DE ENTRADA ÚNICO Y CENTRALIZADO) ---
document.addEventListener('DOMContentLoaded', () => {
    elements.title.startButton.addEventListener('click', showGameStage);
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.game.guessButton.addEventListener('click', showGuessPopup);
    elements.game.suggestionButton.addEventListener('click', showSuggestions);
    elements.game.backToMenu.addEventListener('click', () => closeCurtains(showGameStage, 1));
    elements.guessPopup.confirmButton.addEventListener('click', handleGuessAttempt);
    elements.guessPopup.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handleGuessAttempt(); });
    document.body.addEventListener('click', (e) => {
        if (e.target.dataset.close) {
            e.target.closest('.popup-overlay').classList.add('hidden');
        }
    });
    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'play-alternativo') showChallengeScreen();
        if (action === 'flee-to-title') closeCurtains(runTitleSequence, 1);
        if (action === 'accept-challenge') startGame();
        if (action === 'flee-challenge') showGameStage();
    });
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') { closeCurtains(showGameStage, 1); } 
            else if (action === 'main-menu') { runTitleSequence(); }
        });
    });

    // "Toque de Permiso": Desbloquea los sonidos con la primera interacción del usuario
    document.body.addEventListener('click', unlockAudio);
    document.body.addEventListener('touchstart', unlockAudio); // Para móviles

    runTitleSequence();
});
