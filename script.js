// ===================================================================
// == THE ORACLE GAME - SCRIPT.JS - v2.1 (PRUEBAS LOCALES)          ==
// ===================================================================

// --- CONFIGURACIÓN Y ESTADO ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    suggestionLimit: 5,
    guessButtonCooldown: 15000
};
const welcomePhrases = [
    "El conocimiento aguarda al audaz. Elige tu camino.",
    "Otro mortal buscando respuestas... Demuestra que eres digno.",
    "Mi mente abarca el cosmos. ¿Podrá la tuya resolver un simple enigma?",
    "Las respuestas que buscas están aquí. Si sabes cómo preguntar."
];
const phrases = {
    challenge: "Tu humilde tarea será adivinar el ser, real o ficticio, que yo, el Gran Oráculo, he concebido. Tienes 20 preguntas.",
    guessPopup: {
        initial: "Susurra tu respuesta al vacío...",
        strike1: "El vacío no responde si no le hablas. Escribe algo.",
        strike2: "Mi paciencia tiene límites. ¿Intentas adivinar o malgastar mi tiempo?",
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
    guessPopupPatience: 3,
    suggestionUses: 0,
    lastClickTime: 0
};


// --- CONEXIÓN CON EL CEREBRO ---

// ¡¡ATENCIÓN!! Esta dirección es para probar en local con Pydroid.
const brainLocation = 'http://127.0.0.1:5000/ask';
// Para la versión online, deberías usar la dirección de Render:
// const brainLocation = 'https://the-oracle-game.onrender.com/ask';

async function callOracleAPI(prompt) {
    try {
        const response = await fetch(brainLocation, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        if (!response.ok) {
            const errorData = await response.json();
            return `Error del Oráculo: ${errorData.error || 'Fallo desconocido'}`;
        }
        const data = await response.json();
        return data[0]?.generated_text || phrases.incomprehensible;
    } catch (error) {
        console.error("Error de Conexión:", error);
        return "Error de Conexión: El Oráculo parece estar desconectado. Asegúrate de que el backend.py esté en ejecución.";
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
    guessPopup: { content: document.querySelector('#guess-popup .popup-content-guess'), brainText: document.getElementById('guess-popup-brain-text'), input: document.getElementById('guess-input'), confirmButton: document.getElementById('confirm-guess-button') },
    suggestionPopup: { buttonsContainer: document.getElementById('suggestion-buttons-container') },
    endScreens: { winMessage: document.getElementById('win-message'), loseMessage: document.getElementById('lose-message') },
    sounds: { applause: document.getElementById('applause-sound') }
};


// --- LÓGICA PRINCIPAL DEL JUEGO ---

function resetGameState() {
    state = { ...state, questionCount: 0, secretCharacter: null, isGameActive: false, isAwaitingBrainResponse: false, conversationHistory: [], suggestionUses: 0 };
    elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.suggestionButton.textContent = `Sugerencia (${config.suggestionLimit}/${config.suggestionLimit})`;
}

// =================================================
// == FUNCIÓN STARTGAME v3.0 (A PRUEBA DE CORTINAS) ==
// =================================================
async function startGame() {
    // 1. CIERRA LAS CORTINAS Y MUESTRA LA PANTALLA DE JUEGO INMEDIATAMENTE
    closeCurtains(() => {
        Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
        elements.screens.mainGame.classList.remove('hidden');
        
        // 2. MIENTRAS LAS CORTINAS SE CIERRAN, PREPARAMOS EL JUEGO
        resetGameState();
        elements.game.input.disabled = true;
        elements.game.askButton.disabled = true;
        addMessageToChat("Concibiendo un nuevo enigma del cosmos...", "brain");
    }, 1);

    // 3. AHORA, EN SEGUNDO PLANO, PEDIMOS EL PERSONAJE A LA IA
    // La llamada original era "Crea un dossier", que el backend no entendía.
    const dossierRaw = await callOracleAPI("CREATE_CHARACTER"); // <-- ¡CORRECCIÓN APLICADA AQUÍ!

    // 4. PROCESAMOS LA RESPUESTA DE LA IA (CON EL CÓDIGO ROBUSTO QUE YA TENÍAMOS)
    try {
        // Esta expresión regular busca el primer objeto JSON que encuentre en la respuesta.
        const jsonMatch = dossierRaw.match(/\{[\s\S]*\}/);
        if (!jsonMatch) throw new Error("No se encontró un objeto JSON en la respuesta de la IA.");
        
        const dossierJSON = JSON.parse(jsonMatch[0]);
        state.secretCharacter = dossierJSON;
        
        // Guardamos el último dossier en el almacenamiento local para facilitar la depuración.
        localStorage.setItem('lastDossier', JSON.stringify(state.secretCharacter));
        console.log("PERSONAJE CREADO CON ÉXITO:", state.secretCharacter);

        // 5. UNA VEZ TENEMOS EL PERSONAJE, ACTUALIZAMOS LA PANTALLA Y ACTIVAMOS LOS CONTROLES
        elements.game.chatHistory.innerHTML = ''; 
        state.isGameActive = true;
        addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
            elements.game.input.disabled = false;
            elements.game.askButton.disabled = false;
            elements.game.suggestionButton.disabled = false;
            elements.game.guessButton.disabled = false;
            elements.game.input.focus();
        });

    } catch (error) {
        console.error("ERROR AL PROCESAR PERSONAJE:", error, "Respuesta recibida:", dossierRaw);
        elements.game.chatHistory.innerHTML = '';
        addMessageToChat(phrases.apiError, 'brain');
        // Si hay un error, la función termina aquí para no dejar el juego en un estado inconsistente.
        return; 
    }
}


async function handlePlayerInput() {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    const questionText = elements.game.input.value.trim();
    if (questionText === '') return;

    state.isAwaitingBrainResponse = true;
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;
    addMessageToChat(questionText, 'player');

    const systemPrompt = `Tu dossier de verdad es: ${JSON.stringify(state.secretCharacter)}`;
    // ¡ESTE ES EL BLOQUE CORRECTO!
// Construimos el prompt en el formato que el backend espera: dossier|historial|pregunta
const dossierString = JSON.stringify(state.secretCharacter.dossier);
const historyString = state.conversationHistory.map(m => `${m.role}: ${m.content}`).join('\n');
const fullPrompt = `${dossierString}|${historyString}|${questionText}`;

    state.questionCount++;
    elements.game.questionCounter.textContent = `Pregunta: ${state.questionCount}/${config.questionsLimit}`;
    const brainResponseRaw = await callOracleAPI(fullPrompt);
    state.conversationHistory.push({ role: 'user', content: questionText });

    try {
        const jsonMatch = brainResponseRaw.match(/\{[\s\S]*\}/);
        if (!jsonMatch) throw new Error("Respuesta no es JSON.");
        const brainResponseJSON = JSON.parse(jsonMatch[0]);
        const { respuesta, aclaracion } = brainResponseJSON;
        let fullResponse = respuesta + (aclaracion ? `. ${aclaracion}` : '');
        addMessageToChat(fullResponse, 'brain');
        state.conversationHistory.push({ role: 'assistant', content: fullResponse });
    } catch (error) {
        addMessageToChat(brainResponseRaw, 'brain'); // Si no es JSON, muestra la respuesta tal cual
        state.conversationHistory.push({ role: 'assistant', content: brainResponseRaw });
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
        addMessageToChat("Has agotado tus sugerencias para esta partida.", "brain");
        return;
    }

    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'Pensando en preguntas dignas...';
    elements.popups.suggestion.classList.remove('hidden');

    const suggestionPrompt = `
        Basado en este historial de chat, y sabiendo que el personaje secreto es ${state.secretCharacter.nombre}, genera 3 preguntas de SÍ/NO cortas y estratégicas que un jugador podría hacer.
        REGLAS:
        - NO reveles el nombre del personaje.
        - Las preguntas deben ser inteligentes y tener en cuenta las preguntas ya hechas.
        - Formato: Solo las preguntas, cada una en una nueva línea. Sin numeración ni texto introductorio.
        - Ejemplo: "¿Tu personaje pertenece al universo Marvel?"

        HISTORIAL:
        ${state.conversationHistory.map(m => `${m.role}: ${m.content}`).join('\n')}
    `;

    const suggestionsText = await callOracleAPI(suggestionPrompt);
    const suggestions = suggestionsText.split('\n').filter(s => s.trim() !== '' && s.includes('?'));
    container.innerHTML = '';

    if (suggestions.length > 0) {
        suggestions.forEach(qText => {
            const button = document.createElement('button');
            button.className = 'suggestion-option-button';
            button.textContent = qText;
            button.onclick = () => {
                elements.game.input.value = qText;
                elements.popups.suggestion.classList.add('hidden');
                handlePlayerInput();
            };
            container.appendChild(button);
        });
    } else {
        container.innerHTML = 'No hay sugerencias dignas en este momento.';
    }
    
    state.suggestionUses++;
    const remaining = config.suggestionLimit - state.suggestionUses;
    elements.game.suggestionButton.textContent = `Sugerencia (${remaining}/${config.suggestionLimit})`;
    if (remaining <= 0) {
        elements.game.suggestionButton.disabled = true;
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
    const prefix = sender === 'brain' ? 'Cerebro: ' : 'Tú: ';
    const fullText = prefix + text;
    messageLine.appendChild(avatar);
    messageLine.appendChild(textContainer);
    elements.game.chatHistory.appendChild(messageLine);
    elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight;
    typewriterEffect(textContainer, fullText, callback);
}

function showGuessPopup() {
    state.guessPopupPatience = 3;
    elements.guessPopup.brainText.textContent = phrases.guessPopup.initial;
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
        elements.guessPopup.brainText.textContent = message;
        setTimeout(() => {
            elements.guessPopup.content.classList.remove('shake');
            if (state.guessPopupPatience <= 0) {
                elements.popups.guess.classList.add('hidden');
                elements.game.guessButton.disabled = true;
                setTimeout(() => {
                    elements.game.guessButton.disabled = false;
                }, config.guessButtonCooldown);
            }
        }, 500);
        return;
    }
    elements.popups.guess.classList.add('hidden');
    const isCorrect = guess.toLowerCase() === state.secretCharacter.nombre.toLowerCase();
    endGame(isCorrect);
}


// --- FUNCIONES VISUALES Y DE NAVEGACIÓN (SIN CAMBIOS) ---

function typewriterEffect(element, text, callback) {
    let i = 0;
    element.textContent = '';
    const interval = setInterval(() => {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
        } else {
            clearInterval(interval);
            if (callback) callback();
        }
    }, config.typewriterSpeed);
}

function runTitleSequence() {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.title.classList.remove('hidden');
    elements.title.layout.classList.add('hidden');
    elements.title.introBrain.classList.add('hidden');
    setTimeout(() => { elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); }, 500);
    setTimeout(() => { elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); elements.title.introBrain.classList.remove('hidden'); elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out'; }, 1500);
    setTimeout(() => { elements.title.introBrain.classList.add('hidden'); elements.title.lightning.classList.add('flash-long'); setTimeout(() => { elements.title.lightning.classList.remove('flash-long'); elements.title.layout.classList.remove('hidden'); }, 2000); }, 4000);
}

function showGameStage() {
    Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
    elements.screens.stage.classList.remove('hidden');
    elements.stage.brain.classList.add('hidden');
    elements.stage.dialog.classList.add('hidden');
    elements.stage.lights.classList.remove('hidden');
    elements.stage.menuButtons.innerHTML = `
        <button class="menu-button button-green" data-mode="alternativo">Modo Alternativo</button>
        <button class="menu-button button-grey" data-mode="clasico">Modo Clásico (Próximamente)</button>
        <button id="flee-to-title-button" class="menu-button button-red">Huir</button>
    `;
    elements.stage.menuButtons.classList.add('hidden');
    document.querySelectorAll('#menu-buttons button').forEach(btn => btn.disabled = true);
    elements.stage.curtainLeft.style.transition = 'width 1s ease-in-out';
    elements.stage.curtainRight.style.transition = 'width 1s ease-in-out';
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    setTimeout(() => { if (elements.sounds.applause) elements.sounds.applause.play().catch(e => console.log("Error de audio:", e)); openCurtains(null, 1); }, 1000);
    setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 2000);
    setTimeout(() => { elements.stage.brain.classList.remove('hidden'); }, 2200);
    setTimeout(() => {
        elements.stage.dialog.classList.remove('hidden');
        elements.stage.menuButtons.classList.remove('hidden');
        const randomWelcome = welcomePhrases[Math.floor(Math.random() * welcomePhrases.length)];
        typewriterEffect(elements.stage.dialog, randomWelcome, () => {
            document.querySelector('button[data-mode="alternativo"]').disabled = false;
            document.querySelector('button[data-mode="clasico"]').disabled = false;
            document.getElementById('flee-to-title-button').disabled = false;
            document.querySelector('button[data-mode="alternativo"]').onclick = (e) => selectGameMode(e.target.dataset.mode);
            document.getElementById('flee-to-title-button').addEventListener('click', () => closeCurtains(runTitleSequence, 1));
        });
    }, 2700);
}

function selectGameMode(mode) {
    state.currentMode = mode;
    if (mode === 'alternativo') {
        elements.stage.menuButtons.classList.add('hidden');
        closeCurtains(() => {
            elements.stage.dialog.classList.add('hidden');
            openCurtains(() => {
                elements.stage.dialog.classList.remove('hidden');
                elements.stage.menuButtons.innerHTML = `
                    <button id="accept-challenge" class="button-green">Aceptar Reto</button>
                    <button id="flee-challenge" class="button-red">Huir</button>
                `;
                elements.stage.menuButtons.classList.remove('hidden');
                document.querySelectorAll('#menu-buttons button').forEach(btn => btn.disabled = true);
                typewriterEffect(elements.stage.dialog, phrases.challenge, () => {
                    const acceptBtn = document.getElementById('accept-challenge');
                    const fleeBtn = document.getElementById('flee-challenge');
                    acceptBtn.disabled = false;
                    fleeBtn.disabled = false;
                    acceptBtn.onclick = () => closeCurtains(startGame, 1);
                    fleeBtn.onclick = () => showGameStage();
                });
            }, 2.5);
        }, 1);
    }
}

function closeCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '50%';
    elements.stage.curtainRight.style.width = '50%';
    setTimeout(callback, speed * 1000 + 100);
}

function openCurtains(callback, speed = 1) {
    elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`;
    elements.stage.curtainLeft.style.width = '0%';
    elements.stage.curtainRight.style.width = '0%';
    if (callback) setTimeout(callback, speed * 1000 + 100);
}


// --- EVENT LISTENERS (PUNTO DE ENTRADA) ---
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
    document.querySelectorAll('.end-buttons button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            Object.values(elements.screens).forEach(s => s.classList.add('hidden'));
            if (action === 'play-again') { closeCurtains(showGameStage, 1); } 
            else if (action === 'main-menu') { runTitleSequence(); }
        });
    });
    document.body.addEventListener('click', (e) => {
        if (e.target.dataset.close) { e.target.closest('.popup-overlay').classList.add('hidden'); }
    });
    runTitleSequence();
});
