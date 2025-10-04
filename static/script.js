// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v37.1 (Listo para Vercel)      ==
// ===================================================================
// - ¡ÚNICO CAMBIO! La URL de la API está configurada para Vercel.
// - Mantiene la intro épica, los sonidos de reacción y todas las mejoras.

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    suggestionCooldown: 15000,
    suggestionLimit: 5,
    clueCooldown: 20000,
    clueLimit: 3,
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
    clueUses: 0,
    lastClueTimestamp: 0,
    guessPopupPatience: 3,
    currentGameMode: null
};

// --- CONEXIÓN CON A.L.E. (¡CONFIGURADO PARA VERCEL!) ---
const ALE_URL = '/api/execute';

async function callALE(datos_peticion) {
    try {
        const response = await fetch(ALE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos_peticion)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const errorMessage = errorData ? errorData.error : "Fallo de comunicación.";
            addMessageToChat(`Error del Motor: ${errorMessage}`, "brain");
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
    game: {
        chatHistory: document.getElementById('chat-history'),
        questionCounter: document.getElementById('question-counter'),
        input: document.getElementById('user-question-input'),
        askButton: document.getElementById('ask-button'),
        clueButton: document.getElementById('clue-button'),
        suggestionButton: document.getElementById('suggestion-button'),
        guessButton: document.getElementById('guess-button'),
        backToMenu: document.getElementById('back-to-menu-button'),
        oracleControls: document.getElementById('oracle-mode-controls'),
        classicControls: document.getElementById('classic-mode-controls')
    },
    popups: { 
        guess: document.getElementById('guess-popup'), 
        suggestion: document.getElementById('suggestion-popup'),
        clueCard: document.getElementById('clue-card-popup')
    },
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), instruction: document.getElementById('guess-popup-instruction'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { buttonsContainer: document.getElementById('suggestion-buttons-container') },
    clueCard: { card: document.getElementById('clue-card'), text: document.getElementById('clue-card-text') },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: { 
        badassVictory: document.getElementById('badass-victory-sound'),
        boo: document.getElementById('boo-sound'),
        buttonClick: document.getElementById('button-click-sound'),
        curtain: document.getElementById('curtain-sound'),
        gameOver: document.getElementById('game-over-sound'),
        keyPress: document.getElementById('key-press-sound'),
        lobby: document.getElementById('lobby-sound'),
        selectButton: document.getElementById('select-button-sound'),
        thunder: document.getElementById('thunder-sound'),
        typewriter: document.getElementById('typewriter-sound'),
        victoryNormal: document.getElementById('victory-normal-sound'),
        victoryVoice: document.getElementById('victory-voice-sound')
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
    state.clueUses = 0;
    state.lastClueTimestamp = 0;
    state.guessPopupPatience = 3;
    state.currentGameMode = null;
    if (elements.game.questionCounter) elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    if (elements.game.chatHistory) elements.game.chatHistory.innerHTML = '';
    if (elements.game.input) elements.game.input.value = '';
    if (elements.game.clueButton) {
        elements.game.clueButton.disabled = true;
        elements.game.clueButton.textContent = `Pista ${config.clueLimit}/${config.clueLimit}`;
        elements.game.clueButton.classList.remove('button-cooldown');
    }
    if (elements.game.suggestionButton) {
        elements.game.suggestionButton.disabled = true;
        elements.game.suggestionButton.textContent = `Sugerencias ${config.suggestionLimit}/${config.suggestionLimit}`;
        elements.game.suggestionButton.classList.remove('button-cooldown');
    }
    if (elements.game.guessButton) {
        elements.game.guessButton.disabled = true;
        elements.game.guessButton.classList.remove('button-cooldown');
    }
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
    elements.game.questionCounter.classList.remove('hidden');
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
    addMessageToChat(fullResponse, 'brain');
    if (respuesta.game_over === true) {
        setTimeout(() => endGame(false, "patience"), 1500);
        return;
    }
    if (state.questionCount === 1) {
        elements.game.clueButton.disabled = false;
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

// --- LÓGICA MODO CLÁSICO ---

async function prepararInterfazModoClasico() {
    elements.game.oracleControls.classList.add('hidden');
    elements.game.classicControls.classList.remove('hidden');
    elements.game.questionCounter.classList.add('hidden');
    addMessageToChat("Has elegido el Camino del Clásico. Piensa en un personaje. Yo haré las preguntas.", 'brain');
    const respuesta = await callALE({ skillset_target: "akinator", accion: "iniciar_juego_clasico" });
    if (respuesta && !respuesta.error && respuesta.siguiente_pregunta) {
        state.isGameActive = true;
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
        if (respuesta.siguiente_pregunta) {
            addMessageToChat(respuesta.siguiente_pregunta, 'brain');
        } else if (respuesta.personaje_adivinado) {
            if (elements.sounds.badassVictory) elements.sounds.badassVictory.play().catch(e => {});
            addMessageToChat(`Estoy listo para adivinar... ¿Estás pensando en... **${respuesta.personaje_adivinado}**?`, 'brain');
            state.isGameActive = false;
        }
    } else {
        addMessageToChat("No he podido procesar tu respuesta.", 'brain');
    }
}

// --- LÓGICA DE AYUDAS (PISTA Y SUGERENCIAS) ---

async function showClue() {
    const now = Date.now();
    if (now - state.lastClueTimestamp < config.clueCooldown) return;
    if (state.clueUses >= config.clueLimit) {
        addMessageToChat("Has agotado todas tus pistas.", "brain");
        elements.game.clueButton.disabled = true;
        return;
    }
    state.lastClueTimestamp = now;
    elements.game.clueButton.disabled = true;
    elements.game.clueButton.classList.add('button-cooldown');
    let countdown = Math.ceil(config.clueCooldown / 1000);
    elements.game.clueButton.textContent = `Espera ${countdown}s`;
    const interval = setInterval(() => {
        countdown--;
        if (countdown > 0) elements.game.clueButton.textContent = `Espera ${countdown}s`;
        else {
            clearInterval(interval);
            elements.game.clueButton.disabled = false;
            elements.game.clueButton.classList.remove('button-cooldown');
            elements.game.clueButton.textContent = `Pista ${config.clueLimit - state.clueUses}/${config.clueLimit}`;
        }
    }, 1000);

    elements.clueCard.text.textContent = "El Oráculo medita...";
    elements.clueCard.card.classList.remove('is-flipped');
    elements.popups.clueCard.classList.remove('hidden');

    const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_pista" });
    state.clueUses++;
    elements.game.clueButton.textContent = `Pista ${config.clueLimit - state.clueUses}/${config.clueLimit}`;
    if (state.clueUses >= config.clueLimit) elements.game.clueButton.disabled = true;

    if (respuesta && !respuesta.error && respuesta.pista) {
        elements.clueCard.text.textContent = respuesta.pista;
    } else {
        elements.clueCard.text.textContent = "Los susurros cósmicos son confusos en este momento.";
    }
    setTimeout(() => elements.clueCard.card.classList.add('is-flipped'), 100);
}

async function showSuggestions() {
    const now = Date.now();
    if (now - state.lastSuggestionTimestamp < config.suggestionCooldown) return;
    if (state.suggestionUses >= config.suggestionLimit) {
        addMessageToChat("Has agotado todas tus sugerencias.", "brain");
        elements.game.suggestionButton.disabled = true;
        return;
    }
    state.lastSuggestionTimestamp = now;
    elements.game.suggestionButton.disabled = true;
    elements.game.suggestionButton.classList.add('button-cooldown');
    let countdown = Math.ceil(config.suggestionCooldown / 1000);
    elements.game.suggestionButton.textContent = `Espera ${countdown}s`;
    const interval = setInterval(() => {
        countdown--;
        if (countdown > 0) elements.game.suggestionButton.textContent = `Espera ${countdown}s`;
        else {
            clearInterval(interval);
            elements.game.suggestionButton.disabled = false;
            elements.game.suggestionButton.classList.remove('button-cooldown');
            elements.game.suggestionButton.textContent = `Sugerencias ${config.suggestionLimit - state.suggestionUses}/${config.suggestionLimit}`;
        }
    }, 1000);

    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'El Oráculo está meditando...';
    elements.popups.suggestion.classList.remove('hidden');

    const respuesta = await callALE({ skillset_target: "oracle", accion: "pedir_sugerencias" });
    if (respuesta && !respuesta.error && respuesta.sugerencias && respuesta.sugerencias.length > 0) {
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
                elements.game.suggestionButton.textContent = `Sugerencias ${config.suggestionLimit - state.suggestionUses}/${config.suggestionLimit}`;
                if (state.suggestionUses >= config.suggestionLimit) elements.game.suggestionButton.disabled = true;
            };
            container.appendChild(button);
        });
    } else {
        container.innerHTML = 'No hay sugerencias dignas en este momento.';
        setTimeout(() => { elements.popups.suggestion.classList.add('hidden'); }, 2000);
    }
}

// --- FUNCIONES COMUNES Y VISUALES ---

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

function endGame(isWin, reason = "guess") {
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');
    if (isWin) {
        if (elements.sounds.victoryVoice) elements.sounds.victoryVoice.play().catch(e => {});
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.nombre}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        if (elements.sounds.gameOver) elements.sounds.gameOver.play().catch(e => {});
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

function typewriterEffect(element, text, callback) {
    let i = 0;
    const processedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    element.innerHTML = '';
    if (elements.sounds.typewriter) {
        elements.sounds.typewriter.currentTime = 0;
        elements.sounds.typewriter.play().catch(e => {});
    }
    const interval = setInterval(() => {
        if (i < processedText.length) {
            element.innerHTML += processedText.charAt(i);
            i++;
        } else {
            clearInterval(interval);
            if (elements.sounds.typewriter) elements.sounds.typewriter.pause();
            if (callback) callback();
        }
    }, config.typewriterSpeed);
}

function unlockAudio() {
    Object.values(elements.sounds).forEach(sound => {
        if (sound) {
            sound.play().then(() => { sound.pause(); sound.currentTime = 0; }).catch(e => {});
        }
    });
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
    if (elements.sounds.curtain) {
        elements.sounds.curtain.currentTime = 0;
        elements.sounds.curtain.play().catch(e => {});
    }
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
        if (elements.sounds.thunder) {
            elements.sounds.thunder.currentTime = 0;
            elements.sounds.thunder.play().catch(e => {});
        }
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
    }, 500);
    setTimeout(() => {
        if (elements.sounds.thunder) {
            elements.sounds.thunder.currentTime = 0;
            elements.sounds.thunder.play().catch(e => {});
        }
        elements.title.lightning.classList.add('flash');
        setTimeout(() => elements.title.lightning.classList.remove('flash'), 500);
    }, 1500);
    setTimeout(() => {
        elements.title.introBrain.classList.remove('hidden');
        elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out';
    }, 2000);
    setTimeout(() => {
        elements.title.introBrain.classList.add('hidden');
        if (elements.sounds.thunder) {
            elements.sounds.thunder.currentTime = 0;
            elements.sounds.thunder.play().catch(e => {});
        }
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
    elements.stage.menuButtons.innerHTML = '';
    setTimeout(() => {
        if (elements.sounds.lobby) elements.sounds.lobby.play().catch(e => {});
        openCurtains(() => {
            if (elements.sounds.lobby) { elements.sounds.lobby.pause(); elements.sounds.lobby.currentTime = 0; }
            elements.stage.dialog.classList.remove('hidden');
            typewriterEffect(elements.stage.dialog, "¡¡¡SILENCIO!!!", () => {
                setTimeout(() => {
                    typewriterEffect(elements.stage.dialog, "El espectáculo ha comenzado. Muy bien, mortal... elige tu desafío, o márchate de mi presencia.", () => {
                        elements.stage.menuButtons.innerHTML = `
                            <button class="menu-button button-green" data-action="play-oracle">Modo Oráculo</button>
                            <button class="menu-button button-green" data-action="play-classic">Modo Clásico</button>
                            <button class="menu-button button-red" data-action="flee-to-title">Huir</button>
                        `;
                        elements.stage.menuButtons.classList.remove('hidden');
                    });
                }, 1000);
            });
        }, 2.5);
    }, 500);
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

// --- PUNTO DE ENTRADA ---
document.addEventListener('DOMContentLoaded', () => {
    adjustScreenHeight();
    window.addEventListener('resize', adjustScreenHeight);

    document.body.addEventListener('mouseover', (e) => {
        const button = e.target.closest('button');
        if (button && !button.disabled) {
            if (elements.sounds.selectButton) {
                elements.sounds.selectButton.currentTime = 0;
                elements.sounds.selectButton.play().catch(err => {});
            }
        }
    });

    document.body.addEventListener('mousedown', (e) => {
        const button = e.target.closest('button');
        if (button && !button.disabled) {
            if (elements.sounds.buttonClick) {
                elements.sounds.buttonClick.currentTime = 0;
                elements.sounds.buttonClick.play().catch(err => {});
            }
        }
    });

    document.body.addEventListener('click', (e) => {
        const target = e.target;
        const action = target.dataset.action;
        if (action) {
            if (action === 'play-oracle' || action === 'play-classic' || action === 'accept-challenge') {
                if (elements.sounds.victoryNormal) {
                    elements.sounds.victoryNormal.currentTime = 0;
                    elements.sounds.victoryNormal.play().catch(err => {});
                }
            } else if (action === 'flee-to-title' || action === 'flee-challenge') {
                if (elements.sounds.boo) {
                    elements.sounds.boo.currentTime = 0;
                    elements.sounds.boo.play().catch(err => {});
                }
            }
            if (action === 'play-oracle') showChallengeScreen();
            else if (action === 'play-classic') startGame('classic');
            else if (action === 'accept-challenge') startGame('oracle');
            else if (action === 'flee-to-title') runTitleSequence();
            else if (action === 'flee-challenge') showGameStage();
        }
        if (target.id === 'start-button') showGameStage();
        if (target.id === 'exit-button') elements.arcadeScreen.classList.add('shutdown-effect');
        if (target.id === 'ask-button') handlePlayerInput();
        if (target.id === 'clue-button') showClue();
        if (target.id === 'suggestion-button') showSuggestions();
        if (target.id === 'guess-button') showGuessPopup();
        if (target.id === 'confirm-guess-button') handleGuessAttempt();
        if (target.id === 'back-to-menu-button') closeCurtains(showGameStage, 1);
        if (target.closest('.end-buttons')) {
            const endAction = target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (endAction === 'play-again') showGameStage();
            else if (endAction === 'main-menu') runTitleSequence();
        }
        if (target.closest('.classic-answer-buttons')) {
            const answer = target.dataset.answer;
            if (answer) handleClassicAnswer(answer);
        }
        if (target.dataset.close) {
            target.closest('.popup-overlay').classList.add('hidden');
        }
    });

    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    document.body.addEventListener('click', unlockAudio, { once: true });
    document.body.addEventListener('touchstart', unlockAudio, { once: true });

    runTitleSequence();
});
