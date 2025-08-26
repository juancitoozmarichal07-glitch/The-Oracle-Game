// ============================================
// == CONFIGURACIÓN Y ESTADO DEL JUEGO     ==
// ============================================
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    huracubonadaChance: 0.10,
    suggestionLimit: 5,
    guessButtonCooldown: 15000
};

const welcomePhrases = [
    "El conocimiento aguarda al audaz. Elige tu camino.",
    "Otro mortal buscando respuestas... Demuestra que eres digno.",
    "Mi mente abarca el cosmos. ¿Podrá la tuya resolver un simple enigma?",
    "Las respuestas que buscas están aquí. Si sabes cómo preguntar."
];

const characterNames = [
    "Iron Man", "Batman", "Goku", "Spider-Man", "Wonder Woman", "Darth Vader",
    "Harry Potter", "Superman", "Joker", "Thanos", "Gandalf", "Luke Skywalker",
    "Ellen Ripley", "Sarah Connor", "Kratos", "Master Chief", "Lara Croft"
];

const phrases = {
    challenge: "Tu humilde tarea será adivinar el personaje que yo, el Gran Oráculo, he concebido. Tienes 20 preguntas. No las desperdicies.",
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
    currentMode: 'alternativo',
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isAwaitingBrainResponse: false,
    conversationHistory: [],
    guessPopupPatience: 3,
    suggestionUses: 0,
    lastClickTime: 0
};

// ============================================
// == SELECTORES DE ELEMENTOS DEL DOM      ==
// ============================================
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

// ============================================
// == LÓGICA DE API (VERSIÓN PÚBLICA SIMPLE) ==
// ============================================
async function callHuggingFaceAPI(prompt) {
    // URL de una API pública que no requiere clave para este modelo
    const PUBLIC_API_URL = 'https://api.deepinfra.com/v1/openai/chat/completions';

    // El formato de la petición es un poco diferente
    const requestBody = {
        model: "mistralai/Mistral-7B-Instruct-v0.1",
        messages: [{ role: "user", content: prompt }]
    };

    try {
        const response = await fetch(PUBLIC_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error en la API pública:", errorText);
            return phrases.apiError;
        }
        
        const data = await response.json();
        // La respuesta viene en un formato diferente, la extraemos
        const responseOnly = data.choices[0].message.content;
        return responseOnly.trim();

    } catch (error) {
        console.error('Error de Conexión con la API pública:', error);
        return phrases.apiError;
    }
}


// ============================================
// == EL RESTO DEL CÓDIGO (SIN CAMBIOS)    ==
// ============================================
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

function resetGameState() {
    state.questionCount = 0;
    state.isGameActive = false;
    state.isAwaitingBrainResponse = false;
    state.secretCharacter = null;
    state.conversationHistory = [];
    state.suggestionUses = 0;
    elements.game.questionCounter.textContent = `Pregunta: 0/${config.questionsLimit}`;
    elements.game.chatHistory.innerHTML = '';
    elements.game.input.value = '';
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.suggestionButton.textContent = `Sugerencia (${config.suggestionLimit}/${config.suggestionLimit})`;
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

async function startGame() {
    resetGameState();
    elements.screens.stage.classList.add('hidden');
    elements.screens.mainGame.classList.remove('hidden');
    
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    elements.game.backToMenu.disabled = true;
    addMessageToChat("Concibiendo un nuevo enigma del cosmos...", "brain");

    const success = await fetchDynamicCharacter();
    if (!success) {
        addMessageToChat(phrases.apiError, "brain");
        elements.game.backToMenu.disabled = false; 
        return;
    }

    state.isGameActive = true;
    elements.game.chatHistory.innerHTML = '';
    addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.suggestionButton.disabled = false;
        elements.game.guessButton.disabled = false;
        elements.game.backToMenu.disabled = false;
        elements.game.input.focus();
    });
}

async function fetchDynamicCharacter() {
    const characterName = characterNames[Math.floor(Math.random() * characterNames.length)];
    
    const dossierPrompt = `
### TAREA ###
Crea un dossier en formato JSON para el personaje: "${characterName}".

### REGLAS ESTRICTAS ###
1.  Tu respuesta DEBE ser ÚNICAMENTE el objeto JSON.
2.  NO incluyas texto antes o después del JSON.
3.  El JSON debe tener entre 5 y 8 claves relevantes para el personaje.
4.  Usa valores booleanos (true/false), strings o arrays de strings.

### EJEMPLO DE FORMATO DE RESPUESTA ###
{
  "nombre": "Batman",
  "es_humano": true,
  "universo": "DC",
  "rol": "héroe",
  "habilidad_principal": "intelecto y tecnología",
  "identidad_secreta": "Bruce Wayne"
}
`;
    
    const dossierRaw = await callHuggingFaceAPI(dossierPrompt);
    try {
        const jsonMatch = dossierRaw.match(/\{[\s\S]*\}/);
        if (!jsonMatch) throw new Error("No se encontró JSON en la respuesta.");
        
        const dossierJSON = JSON.parse(jsonMatch[0]);
        state.secretCharacter = { name: characterName, dossier: dossierJSON };
        console.log("Personaje concebido:", state.secretCharacter);
        return true;
    } catch (error) {
        console.error("Error al parsear el dossier:", dossierRaw, error);
        return false;
    }
}

function getSystemPrompt(dossier) {
    const dossierString = JSON.stringify(dossier, null, 2);
    return `### ROL Y REGLAS ABSOLUTAS ###\nEres El Oráculo. Tu única tarea es responder preguntas sobre un personaje secreto basándote ESTRICTAMENTE en el DOSSIER DE VERDAD proporcionado. Tu respuesta DEBE SER SIEMPRE un objeto JSON válido con el formato: {"respuesta": "...", "aclaracion": "..."}. NO PUEDES DEVOLVER NADA MÁS QUE ESE JSON. Sin texto introductorio, sin explicaciones, solo el JSON.\n\n### LÓGICA DE RESPUESTA (ORDEN DE PRIORIDAD) ###\n1.  **PREGUNTA INVÁLIDA:** Si la pregunta no es una pregunta de Sí/No (ej: "¿De qué color es?"), responde con: {"respuesta": "Infracción", "aclaracion": "Solo respondo a cuestiones de Sí o No. Reformula tu interrogante."}\n2.  **EVIDENCIA DIRECTA:** Si el DOSSIER contiene la respuesta, responde con "Sí" o "No". La aclaración puede estar vacía. Ej: {"respuesta": "Sí", "aclaracion": ""}\n3.  **SIN EVIDENCIA:** Si es imposible saber la respuesta desde el DOSSIER, responde con "Dato Ausente". Ej: {"respuesta": "Dato Ausente", "aclaracion": "Esa información es irrelevante o se encuentra más allá de mi conocimiento."}\n4.  **PISTA CRÍPTICA (OPCIONAL):** En los casos de "Sí", "No" o "Dato Ausente", puedes añadir una 'aclaracion' corta y enigmática si lo crees útil, pero no es obligatorio.\n\n### DOSSIER DE VERDAD ###\n${dossierString}`;
}

function endGame(isWin) {
    state.isGameActive = false;
    elements.screens.mainGame.classList.add('hidden');
    if (isWin) {
        elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.name}. Tu mente es... aceptable.`;
        elements.screens.win.classList.remove('hidden');
    } else {
        elements.endScreens.loseMessage.textContent = `Has fallado. El personaje era ${state.secretCharacter.name}. Una mente simple no puede comprender lo complejo.`;
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

async function handlePlayerInput() {
    if (!state.isGameActive || state.isAwaitingBrainResponse) return;
    const questionText = elements.game.input.value.trim();
    if (questionText === '') return;

    state.isAwaitingBrainResponse = true;
    elements.game.input.value = '';
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;

    addMessageToChat(questionText, 'player');
    state.conversationHistory.push(`Humano: ${questionText}`);

    state.questionCount++;
    elements.game.questionCounter.textContent = `Pregunta: ${state.questionCount}/${config.questionsLimit}`;

    const systemPrompt = getSystemPrompt(state.secretCharacter.dossier);
    const cleanHistory = state.conversationHistory.join('\n');
    const fullPrompt = `${systemPrompt}\n\n### HISTORIAL DE CHAT ###\n${cleanHistory}\n\n### PREGUNTA ACTUAL ###\n${questionText}\n\n### TU RESPUESTA JSON ###\n`;
    
    const brainResponseRaw = await callHuggingFaceAPI(fullPrompt);

    try {
        const brainResponseJSON = JSON.parse(brainResponseRaw);
        const { respuesta, aclaracion } = brainResponseJSON;

        let fullResponse = respuesta;
        if (aclaracion && aclaracion.trim() !== "") {
            fullResponse += `. ${aclaracion}`;
        }
        addMessageToChat(fullResponse, 'brain');
        state.conversationHistory.push(`Oráculo: ${fullResponse}`);
    } catch (error) {
        console.error("Error al parsear la respuesta de la IA:", brainResponseRaw, error);
        addMessageToChat(phrases.incomprehensible, 'brain');
    } finally {
        state.isAwaitingBrainResponse = false;
        elements.game.input.disabled = false;
        elements.game.askButton.disabled = false;
        elements.game.input.focus();
    }

    if (state.isGameActive && state.questionCount >= config.questionsLimit) {
        endGame(false);
    }
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
                setTimeout(() => { elements.game.guessButton.disabled = false; }, config.guessButtonCooldown);
            }
        }, 500);
        return;
    }
    elements.popups.guess.classList.add('hidden');
    const isCorrect = guess.toLowerCase() === state.secretCharacter.name.toLowerCase();
    endGame(isCorrect);
}

async function showSuggestions() {
    if (state.suggestionUses >= config.suggestionLimit) {
        addMessageToChat("Has agotado tus sugerencias para esta partida.", "brain");
        return;
    }

    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'Pensando en preguntas dignas...';
    elements.popups.suggestion.classList.remove('hidden');

    const suggestionPrompt = `Basado en este historial de chat, y sabiendo que el personaje secreto es ${state.secretCharacter.name}, genera 3 preguntas de SÍ/NO cortas y estratégicas que un jugador podría hacer. REGLAS: NO reveles el nombre del personaje. Las preguntas deben ser inteligentes y tener en cuenta las preguntas ya hechas. Formato: Solo las preguntas, cada una en una nueva línea. Sin numeración ni texto introductorio. Ejemplo: "¿Tu personaje pertenece al universo Marvel?"\n\nHISTORIAL:\n${state.conversationHistory.join('\n')}`;

    const suggestionsText = await callHuggingFaceAPI(suggestionPrompt);
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
        state.suggestionUses++;
        const remaining = config.suggestionLimit - state.suggestionUses;
        elements.game.suggestionButton.textContent = `Sugerencia (${remaining}/${config.suggestionLimit})`;
        if (remaining <= 0) {
            elements.game.suggestionButton.disabled = true;
        }
    } else {
        container.innerHTML = 'No hay sugerencias dignas en este momento.';
    }
}

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
