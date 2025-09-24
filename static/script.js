// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v16.0 (Definitiva Unificada)  ==
// ===================================================================
// - Implementa COMPLETAMENTE el Modo Clásico (Akinator).
// - Es 100% compatible con el oracle.py v11 (paciencia, game_over, etc.).
// - Unifica toda la lógica en un solo archivo robusto.

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

// --- CONEXIÓN CON A.L.E. (Backend) ---
const ALE_URL = '/execute';

async function callALE(datos_peticion) {
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos_peticion)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Error desconocido del servidor." }));
            addMessageToChat(`Error del Motor: ${errorData.error || 'Fallo de comunicación.'}`, "brain");
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
    stage: { dialog: document.getElementById('stage-dialog'), menuButtons: document.getElementById('menu-buttons'), curtainLeft: document.getElementById('curtain-left'), curtainRight: document.getElementById('curtain-right') },
    game: {
        chatHistory: document.getElementById('chat-history'),
        questionCounter: document.getElementById('question-counter'),
        input: document.getElementById('user-question-input'),
        askButton: document.getElementById('ask-button'),
        suggestionButton: document.getElementById('suggestion-button'),
        guessButton: document.getElementById('guess-button'),
        backToMenu: document.getElementById('back-to-menu-button'),
        oracleControls: document.getElementById('oracle-mode-controls'),
        classicControls: document.getElementById('classic-mode-controls')
    },
    popups: { guess: document.getElementById('guess-popup'), suggestion: document.getElementById('suggestion-popup') },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
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
    state.suggestionUses = 0;
    state.lastSuggestionTimestamp = 0;
    state.guessPopupPatience = 3;
    state.currentGameMode = null;
    elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.suggestionButton.textContent = `Sugerencia ${config.suggestionLimit}/${config.suggestionLimit}`;
    elements.game.suggestionButton.classList.remove('button-cooldown');
    elements.game.guessButton.classList.remove('button-cooldown');
}

async function startGame(mode) {
    state.currentGameMode = mode;
    closeCurtains(async () => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');
        resetGameState();
        if (mode === 'oracle') await prepararInterfazModoOraculo();
        else if (mode === 'classic') await prepararInterfazModoClasico();
    }, 1);
}

// --- LÓGICA MODO ORÁCULO ---

async function prepararInterfazModoOraculo() {
    elements.game.oracleControls.classList.remove('hidden');
    elements.game.classicControls.classList.add('hidden');
    elements.game.suggestionButton.classList.remove('hidden');
    elements.game.guessButton.classList.remove('hidden');
    elements.game.questionCounter.classList.remove('hidden');
    addMessageToChat("Oráculo: Concibiendo un nuevo enigma del cosmos...", "brain");
    const respuesta = await callALE({ skillset_target: "oracle", accion: "iniciar_juego" });
    if (respuesta.error) {
        addMessageToChat("Oráculo: No he podido concebir un enigma. Inténtalo de nuevo.", "brain");
        return;
    }
    state.secretCharacter = respuesta.personaje_secreto;
    elements.game.chatHistory.innerHTML = '';
    state.isGameActive = true;
    addMessageToChat(`Oráculo: He concebido mi enigma. Comienza.`, 'brain', () => {
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.input.focus();
    });
}

async function handlePlayerInput() {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    const questionText = elements.game.input.value.trim();
    if (questionText === '') return;
    state.isAwaitingBrainResponse = true;
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;
    addMessageToChat(`Tú: ${questionText}`, 'player');
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
    addMessageToChat(fullResponse, 'brain');
    if (respuesta.game_over === true) {
        setTimeout(() => endGame(false, "patience"), 1500);
        return;
    }
    if (state.questionCount === 1) {
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
                }, 1500);
                break;
        }
        elements.guessPopup.instruction.textContent = message;
        setTimeout(() => elements.guessPopup.content.classList.remove('shake'), 500);
        return;
    }
    elements.popups.guess.classList.add('hidden');
    const isCorrect = guess.toLowerCase() === (state.secretCharacter?.nombre.toLowerCase() || '');
    endGame(isCorrect);
}

// --- LÓGICA MODO CLÁSICO (AKINATOR) ---

async function prepararInterfazModoClasico() {
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.remove('hidden');
    elements.game.suggestionButton.classList.add('hidden');
    elements.game.guessButton.classList.add('hidden');
    elements.game.questionCounter.classList.add('hidden');
    addMessageToChat("Oráculo: Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas.", 'brain');
    const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
    if (respuesta && !respuesta.error && respuesta.siguiente_pregunta) {
        state.isGameActive = true;
        addMessageToChat(`Oráculo: ${respuesta.siguiente_pregunta}`, 'brain');
    } else {
        addMessageToChat("Oráculo: Mi mente está confusa para este modo. Vuelve al menú.", 'brain');
    }
}

async function handleClassicAnswer(answer) {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    state.isAwaitingBrainResponse = true;
    addMessageToChat(`Tú: ${answer}`, 'player');
    const respuesta = await callALE({
        skillset_target: "akinator",
        accion: "procesar_respuesta_jugador",
        respuesta: answer
    });
    state.isAwaitingBrainResponse = false;
    if (respuesta && !respuesta.error) {
        if (respuesta.siguiente_pregunta) {
            addMessageToChat(`Oráculo: ${respuesta.siguiente_pregunta}`, 'brain');
        } else if (respuesta.personaje_adivinado) {
            addMessageToChat(`Oráculo: Estoy listo para adivinar... ¿Estás pensando en... **${respuesta.personaje_adivinado}**?`, 'brain');
            state.isGameActive = false;
        }
    } else {
        addMessageToChat("Oráculo: No he podido procesar tu respuesta.", 'brain');
    }
}

// --- FUNCIONES COMUNES Y VISUALES ---

function endGame(isWin, reason = "guess") {
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');
    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.nombre}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        let loseMessage = "";
        switch (reason) {
            case "patience":
                loseMessage = `El Oráculo ha agotado su paciencia cósmica. El personaje era ${state.secretCharacter.nombre}.`;
                break;
            case "guess_abuse":
                loseMessage = `Has agotado la paciencia del Oráculo con tus intentos vacíos. El personaje era ${state.secretCharacter.nombre}.`;
                break;
            case "questions":
                loseMessage = `Has agotado tus preguntas. El personaje era ${state.secretCharacter.nombre}. Una mente simple no puede comprender lo complejo.`;
                break;
            default:
                loseMessage = `Has fallado. El personaje era ${state.secretCharacter.nombre}. Una mente simple no puede comprender lo complejo.`;
                break;
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
    avatar.textContent = sender === 'brain' ? '🧠' : '👤';
    const textContainer = document.createElement('div');
    textContainer.className = 'message-text-container';
    const prefix = sender === 'brain' ? 'Oráculo: ' : 'Tú: ';
    const fullText = prefix + text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Reemplaza ** con <strong>
    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
    typewriterEffect(textContainer, fullText, callback);
}

function typewriterEffect(element, text, callback) {
    let i = 0;
    element.innerHTML = ''; // Usamos innerHTML para que las etiquetas <strong> funcionen
    if (elements.sounds.typewriter) {
        elements.sounds.typewriter.currentTime = 0;
        elements.sounds.typewriter.play().catch(e => {});
    }
    const interval = setInterval(() => {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
        } else {
            clearInterval(interval);
            if (elements.sounds.typewriter) elements.sounds.typewriter.pause();
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
    elements.stage.menuButtons.innerHTML = `
        <button class="menu-button button-green" data-action="play-oracle">Modo Oráculo</button>
        <button class="menu-button button-green" data-action="play-classic">Modo Clásico</button>
        <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
    `;
    openCurtains(() => {
        typewriterEffect(elements.stage.dialog, "El conocimiento aguarda al audaz. Elige tu camino.");
    }, 1);
}

function showChallengeScreen() {
    elements.stage.menuButtons.innerHTML = `
        <button class="button-green" data-action="accept-challenge">Aceptar Reto</button>
        <button class="button-red" data-action="flee-challenge">Huir</button>
    `;
    typewriterEffect(elements.stage.dialog, phrases.challenge);
}

function closeCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}

function openCurtains(callback, speed = 1) {
    if (elements.sounds.curtain) elements.sounds.curtain.play().catch(e => {});
    elements.stage.curtainLeft.style.width = '0%';
    elements.stage.curtainRight.style.width = '0%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}

function adjustScreenHeight() {
    const arcadeScreen = elements.arcadeScreen;
    if (arcadeScreen) arcadeScreen.style.height = `${window.innerHeight}px`;
}

// --- PUNTO DE ENTRADA Y LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Página cargada. Asignando eventos (v16.0 - Definitiva Unificada).");

    adjustScreenHeight();
    window.addEventListener('resize', adjustScreenHeight);

    elements.title.startButton.addEventListener('click', showGameStage);
    elements.title.exitButton.addEventListener('click', () => elements.arcadeScreen.classList.add('shutdown-effect'));
    elements.game.backToMenu.addEventListener('click', () => closeCurtains(showGameStage, 1));

    elements.stage.menuButtons.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'play-oracle') showChallengeScreen();
        else if (action === 'play-classic') startGame('classic');
        else if (action === 'accept-challenge') startGame('oracle');
        else if (action === 'flee-to-title') runTitleSequence();
        else if (action === 'flee-challenge') showGameStage();
    });

    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.game.guessButton.addEventListener('click', showGuessPopup);
    elements.guessPopup.confirmButton.addEventListener('click', handleGuessAttempt);
    // elements.game.suggestionButton.addEventListener('click', showSuggestions); // Si tienes la función, descomenta

    document.querySelectorAll('.classic-answer-buttons .answer-btn').forEach(button => {
        button.addEventListener('click', () => {
            const answer = button.dataset.answer;
            handleClassicAnswer(answer);
        });
    });

    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) e.target.closest('.popup-overlay').classList.add('hidden'); });
    
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') showGameStage();
            else if (action === 'main-menu') runTitleSequence();
        });
    });

    runTitleSequence();
});
