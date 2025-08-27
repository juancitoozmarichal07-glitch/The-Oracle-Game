// ============================================
// == SCRIPT.JS - VERSIÓN FINAL (CON BACKEND) ==
// ============================================
// Hecho por Manus para ti. ¡A disfrutar!

// ============================================
// == CONFIGURACIÓN Y ESTADO DEL JUEGO     ==
// ============================================
const config = {
    questionsLimit: 20,
    typewriterSpeed: 45,
    huracubonadaChance: 0.10,
    suggestionLimit: 5,
    guessButtonCooldown: 15000,
    winsToUnlockClassic: 3 // ¡Añadido para que funcione el desbloqueo!
};

const banPhrases = [
    "¿No sabes leer? Me sorprende tu habilidad para ser tan desobediente.",
    "La definición de la locura es hacer lo mismo una y otra vez esperando resultados diferentes.",
    "Mi decisión es final. Tu insistencia es simplemente... patética.",
    "¿Crees que un simple clic puede anular mi veredicto? Qué tierno."
];

const welcomePhrases = [
    "El conocimiento aguarda al audaz. Elige tu camino.",
    "Otro mortal buscando respuestas... Demuestra que eres digno.",
    "Mi mente abarca el cosmos. ¿Podrá la tuya resolver un simple enigma?",
    "Las respuestas que buscas están aquí. Si sabes cómo preguntar."
];

let state = {
    currentMode: 'alternativo',
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isAwaitingBrainResponse: false,
    conversationHistory: [],
    guessPopupPatience: 3,
    suggestionUses: 0,
    isBanned: false,
    totalWins: 0,
    classicUnlocked: false,
    lastClickTime: 0
};

// ============================================
// == BANCO DE PERSONAJES Y FRASES         ==
// ============================================
const phrases = {
    challenge: "Tu humilde tarea será adivinar el personaje que yo, el Gran Oráculo, he concebido. Tienes 20 preguntas. No las desperdicies.",
    guessPopup: {
        initial: "Susurra tu respuesta al vacío...",
        strike1: "El vacío no responde si no le hablas. Escribe algo.",
        strike2: "Mi paciencia tiene límites. ¿Intentas adivinar o malgastar mi tiempo?",
        strike3: "Has agotado mi paciencia. El privilegio de adivinar te ha sido revocado... por ahora."
    },
    apiError: "Mi mente está... nublada. No puedo procesar tu petición ahora."
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
// == GESTIÓN DE DATOS LOCALES (localStorage) ==
// ============================================
function savePlayerData() {
    const playerData = { isBanned: state.isBanned, totalWins: state.totalWins, classicUnlocked: state.classicUnlocked };
    localStorage.setItem('oracleGameData', JSON.stringify(playerData));
}

function loadPlayerData() {
    const savedData = localStorage.getItem('oracleGameData');
    if (savedData) {
        const playerData = JSON.parse(savedData);
        state.isBanned = playerData.isBanned || false;
        state.totalWins = playerData.totalWins || 0;
        state.classicUnlocked = playerData.classicUnlocked || false;
    }
}

// ============================================
// == FUNCIONES DE NAVEGACIÓN Y VISUALES   ==
// ============================================
function typewriterEffect(element, text, callback) { let i = 0; element.textContent = ''; const interval = setInterval(() => { if (i < text.length) { element.textContent += text.charAt(i); i++; } else { clearInterval(interval); if (callback) callback(); } }, config.typewriterSpeed); }
function runTitleSequence() { Object.values(elements.screens).forEach(s => s.classList.add('hidden')); elements.screens.title.classList.remove('hidden'); elements.title.layout.classList.add('hidden'); elements.title.introBrain.classList.add('hidden'); setTimeout(() => { elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); }, 500); setTimeout(() => { elements.title.lightning.classList.add('flash'); setTimeout(() => elements.title.lightning.classList.remove('flash'), 500); elements.title.introBrain.classList.remove('hidden'); elements.title.introBrain.style.animation = 'materialize 2s forwards ease-out'; }, 1500); setTimeout(() => { elements.title.introBrain.classList.add('hidden'); elements.title.lightning.classList.add('flash-long'); setTimeout(() => { elements.title.lightning.classList.remove('flash-long'); elements.title.layout.classList.remove('hidden'); }, 2000); }, 4000); }
function showGameStage() { Object.values(elements.screens).forEach(s => s.classList.add('hidden')); elements.screens.stage.classList.remove('hidden'); elements.stage.brain.classList.add('hidden'); elements.stage.dialog.classList.add('hidden'); elements.stage.lights.classList.remove('hidden'); elements.stage.menuButtons.innerHTML = `<button class="menu-button button-green" data-mode="alternativo">Modo Alternativo</button><button class="menu-button button-grey" data-mode="clasico">Modo Clásico</button><button id="flee-to-title-button" class="menu-button button-red">Huir</button>`; elements.stage.menuButtons.classList.add('hidden'); document.querySelectorAll('#menu-buttons button').forEach(btn => btn.disabled = true); elements.stage.curtainLeft.style.transition = 'width 1s ease-in-out'; elements.stage.curtainRight.style.transition = 'width 1s ease-in-out'; elements.stage.curtainLeft.style.width = '50%'; elements.stage.curtainRight.style.width = '50%'; setTimeout(() => { if(elements.sounds.applause) elements.sounds.applause.play().catch(e => console.log("Error de audio:", e)); openCurtains(null, 1); }, 1000); setTimeout(() => { elements.stage.lights.classList.add('hidden'); }, 2000); setTimeout(() => { elements.stage.brain.classList.remove('hidden'); }, 2200); setTimeout(() => { elements.stage.dialog.classList.remove('hidden'); elements.stage.menuButtons.classList.remove('hidden'); const randomWelcome = welcomePhrases[Math.floor(Math.random() * welcomePhrases.length)]; typewriterEffect(elements.stage.dialog, randomWelcome, () => { updateMenuButtonsState(); document.getElementById('flee-to-title-button').addEventListener('click', () => closeCurtains(runTitleSequence, 1)); }); }, 2700); }
function updateMenuButtonsState() { const altModeButton = document.querySelector('button[data-mode="alternativo"]'); const classicModeButton = document.querySelector('button[data-mode="clasico"]'); if (state.isBanned) { altModeButton.disabled = true; altModeButton.textContent = "BANEADO"; altModeButton.className = 'menu-button button-grey'; altModeButton.onclick = () => { const randomInsult = banPhrases[Math.floor(Math.random() * banPhrases.length)]; typewriterEffect(elements.stage.dialog, randomInsult); }; } else { altModeButton.disabled = false; altModeButton.textContent = "Modo Alternativo"; altModeButton.className = 'menu-button button-green'; altModeButton.onclick = (e) => selectGameMode(e.target.dataset.mode); } if (state.classicUnlocked) { classicModeButton.disabled = false; classicModeButton.textContent = "Modo Clásico"; classicModeButton.className = 'menu-button button-green'; } else { classicModeButton.disabled = true; classicModeButton.textContent = `CLÁSICO (${state.totalWins}/${config.winsToUnlockClassic} Victorias)`; classicModeButton.className = 'menu-button button-grey'; } }
function closeCurtains(callback, speed = 1) { elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`; elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`; elements.stage.curtainLeft.style.width = '50%'; elements.stage.curtainRight.style.width = '50%'; setTimeout(callback, speed * 1000 + 100); }
function openCurtains(callback, speed = 1) { elements.stage.curtainLeft.style.transition = `width ${speed}s ease-in-out`; elements.stage.curtainRight.style.transition = `width ${speed}s ease-in-out`; elements.stage.curtainLeft.style.width = '0%'; elements.stage.curtainRight.style.width = '0%'; if (callback) setTimeout(callback, speed * 1000 + 100); }

// ============================================
// == LÓGICA DE API (CONECTADA AL BACKEND)   ==
// ============================================
async function callOracleAPI(prompt) {
    const brainLocation = 'http://127.0.0.1:5000/ask';
    try {
        const response = await fetch(brainLocation, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await response.json();
        if (!response.ok) {
            return `Error del Oráculo: ${data.error || 'Fallo desconocido'}`;
        }
        const generatedText = data[0]?.generated_text || "No he podido generar una respuesta.";
        return generatedText.trim();
    } catch (error) {
        return "Error de Conexión: El Oráculo parece estar desconectado. Asegúrate de que el archivo 'backend.py' esté en ejecución.";
    }
}

// ============================================
// == LÓGICA PRINCIPAL DEL JUEGO (ADAPTADA) ==
// ============================================
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
    state.currentMode = mode; if (mode === 'alternativo') { elements.stage.menuButtons.classList.add('hidden'); closeCurtains(() => { elements.stage.dialog.classList.add('hidden'); openCurtains(() => { elements.stage.dialog.classList.remove('hidden'); elements.stage.menuButtons.innerHTML = `<button id="accept-challenge" class="button-green">Aceptar Reto</button><button id="flee-challenge" class="button-red">Huir</button>`; elements.stage.menuButtons.classList.remove('hidden'); document.querySelectorAll('#menu-buttons button').forEach(btn => btn.disabled = true); typewriterEffect(elements.stage.dialog, phrases.challenge, () => { const acceptBtn = document.getElementById('accept-challenge'); const fleeBtn = document.getElementById('flee-challenge'); acceptBtn.disabled = false; fleeBtn.disabled = false; acceptBtn.onclick = () => closeCurtains(startGame, 1); fleeBtn.onclick = () => showGameStage(); }); }, 2.5); }, 1); }
}

async function startGame() {
    resetGameState();
    elements.screens.stage.classList.add('hidden');
    elements.screens.mainGame.classList.remove('hidden');
    
    elements.game.input.disabled = true;
    elements.game.askButton.disabled = true;
    elements.game.suggestionButton.disabled = true;
    elements.game.guessButton.disabled = true;
    addMessageToChat("Concibiendo un nuevo enigma del cosmos...", "brain");

    const dossierPrompt = `TAREA: Eres un Oráculo. Elige en secreto UNO de los siguientes personajes: "Iron Man", "Batman", "Goku", "Spider-Man", "Wonder Woman", "Darth Vader", "Harry Potter". NO reveles tu elección.
    Luego, crea un dossier para ese personaje en formato JSON. El JSON debe tener entre 5 y 8 claves relevantes.
    REGLAS ESTRICTAS: Tu respuesta DEBE ser ÚNICAMENTE el objeto JSON. Sin texto antes ni después.
    EJEMPLO DE RESPUESTA PERFECTA:
    {
      "nombre": "Batman",
      "es_humano": true,
      "universo": "DC",
      "rol": "héroe",
      "habilidad_principal": "intelecto y tecnología",
      "identidad_secreta": "Bruce Wayne"
    }`;

    const dossierRaw = await callOracleAPI(dossierPrompt);
    
    try {
        const jsonMatch = dossierRaw.match(/\{[\s\S]*\}/);
        if (!jsonMatch) throw new Error("No se encontró JSON en la respuesta.");
        
        const dossierJSON = JSON.parse(jsonMatch[0]);
        state.secretCharacter = { name: dossierJSON.nombre, dossier: dossierJSON };
        console.log("Personaje concebido por el backend:", state.secretCharacter);

        state.isGameActive = true;
        elements.game.chatHistory.innerHTML = '';
        const systemPrompt = getSystemPrompt(state.secretCharacter.dossier);
        state.conversationHistory.push({ role: 'system', content: systemPrompt });
        addMessageToChat(`He concebido mi enigma. Comienza.`, 'brain', () => {
            elements.game.input.disabled = false;
            elements.game.askButton.disabled = false;
            elements.game.suggestionButton.disabled = false;
            elements.game.guessButton.disabled = false;
            elements.game.input.focus();
        });

    } catch (error) {
        console.error("Error al procesar el personaje del backend:", dossierRaw, error);
        elements.game.chatHistory.innerHTML = '';
        addMessageToChat(dossierRaw, 'brain');
    }
}

function getSystemPrompt(dossier, isHuracubonada = false) {
    const dossierString = JSON.stringify(dossier, null, 2); if (isHuracubonada) { return `Eres El Oráculo. Tu personaje secreto es ${dossier.name}. IGNORA LA PREGUNTA DEL USUARIO. En su lugar, responde con una "Huracubonada": una frase poética, críptica y filosófica sobre el personaje, sin revelar datos directos. La frase debe ser una única cadena de texto, sin formato JSON. Ejemplo: "La venganza es una sombra que se viste de murciélago para danzar con la noche."`; } return `Eres El Oráculo, un genio enigmático. Tu personaje secreto es ${dossier.name}. Tu única fuente de verdad es el siguiente DOSSIER JSON. No puedes inventar ni suponer nada que no esté explícitamente en él. REGLAS DE RESPUESTA (Orden de Prioridad): 1. PREGUNTA IRRELEVANTE: Si la pregunta del usuario es un saludo, un insulto o no busca información para adivinar, responde con: \`{ "respuesta": "Infracción", "aclaracion": "Tu pregunta es un sinsentido en un entorno de verdad absoluta. No te dediques a la charlatanería." }\`. 2. EVIDENCIA DIRECTA: Si el DOSSIER contiene la respuesta exacta (verdadera o falsa), responde con: \`{ "respuesta": "Sí" }\` o \`{ "respuesta": "No" }\`. NO AÑADAS ACLARACIÓN. 3. EVIDENCIA IMPLÍCITA (DEDUCCIÓN): Si el DOSSIER no tiene la respuesta directa, pero puedes deducirla lógicamente, responde con: \`{ "respuesta": "Probablemente" }\` o \`{ "respuesta": "Probablemente no" }\`, y en "aclaracion" añade una pista críptica basada en el DOSSIER. La pista debe orientar, no revelar. 4. SIN EVIDENCIA: Si es imposible saber la respuesta desde el DOSSIER, responde con: \`{ "respuesta": "Dato Ausente", "aclaracion": "Esa información es irrelevante o se encuentra más allá de mi conocimiento actual." }\`. Tu respuesta DEBE ser siempre un objeto JSON válido. # DOSSIER DE VERDAD ABSOLUTA \`\`\`json ${dossierString} \`\`\``;
}

function endGame(isWin) {
    state.isGameActive = false; elements.screens.mainGame.classList.add('hidden'); if (isWin) { elements.endScreens.winMessage.textContent = `¡Correcto! El personaje era ${state.secretCharacter.name}. Tu mente es... aceptable.`; elements.screens.win.classList.remove('hidden'); state.totalWins++; if (state.totalWins >= config.winsToUnlockClassic) { state.classicUnlocked = true; } savePlayerData(); } else { elements.endScreens.loseMessage.textContent = `Has fallado. El personaje era ${state.secretCharacter.name}. Una mente simple no puede comprender lo complejo.`; elements.screens.lose.classList.remove('hidden'); }
}

function addMessageToChat(text, sender, callback) {
    const messageLine = document.createElement('div'); messageLine.className = `message-line message-line-${sender}`; const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = sender === 'brain' ? '🧠' : '👤'; const textContainer = document.createElement('div'); textContainer.className = 'message-text-container'; const prefix = sender === 'brain' ? 'Cerebro: ' : 'Tú: '; const fullText = prefix + text; messageLine.appendChild(avatar); messageLine.appendChild(textContainer); elements.game.chatHistory.appendChild(messageLine); elements.game.chatHistory.scrollTop = elements.game.chatHistory.scrollHeight; typewriterEffect(textContainer, fullText, callback);
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

    const isHuracubonada = Math.random() < config.huracubonadaChance;
    const systemPrompt = getSystemPrompt(state.secretCharacter.dossier, isHuracubonada);
    
    const apiHistory = [
        { role: 'system', content: systemPrompt },
        ...state.conversationHistory.slice(-6), // Usamos las últimas 6 interacciones para no sobrecargar
        { role: 'user', content: questionText }
    ];

    const fullPrompt = apiHistory.map(m => `${m.role}: ${m.content}`).join('\n\n');

    state.questionCount++;
    elements.game.questionCounter.textContent = `Pregunta: ${state.questionCount}/${config.questionsLimit}`;

    const brainResponseRaw = await callOracleAPI(fullPrompt);

    state.conversationHistory.push({ role: 'user', content: questionText });

    if (isHuracubonada) {
        addMessageToChat(brainResponseRaw, 'brain');
        state.conversationHistory.push({ role: 'assistant', content: brainResponseRaw });
    } else {
        try {
            const jsonMatch = brainResponseRaw.match(/\{[\s\S]*\}/);
            if (!jsonMatch) throw new Error("No se encontró JSON en la respuesta.");
            const brainResponseJSON = JSON.parse(jsonMatch[0]);
            const { respuesta, aclaracion } = brainResponseJSON;

            let fullResponse = respuesta;
            if (aclaracion && (respuesta.toLowerCase().includes("probablemente") || respuesta.toLowerCase().includes("dato ausente"))) {
                fullResponse += `. ${aclaracion}`;
            }
            addMessageToChat(fullResponse, 'brain');
            state.conversationHistory.push({ role: 'assistant', content: brainResponseRaw });
        } catch (error) {
            console.error("Error al parsear la respuesta de la IA:", brainResponseRaw, error);
            addMessageToChat(brainResponseRaw, 'brain');
        }
    }

    state.isAwaitingBrainResponse = false;
    elements.game.input.disabled = false;
    elements.game.askButton.disabled = false;
    elements.game.input.focus();

    if (state.questionCount >= config.questionsLimit && state.isGameActive) {
        endGame(false);
    }
}

function showGuessPopup() {
    state.guessPopupPatience = 3; elements.guessPopup.brainText.textContent = phrases.guessPopup.initial; elements.guessPopup.input.value = ''; elements.popups.guess.classList.remove('hidden'); elements.guessPopup.input.focus();
}

function handleGuessAttempt() {
    const guess = elements.guessPopup.input.value.trim(); if (guess === '') { state.guessPopupPatience--; elements.guessPopup.content.classList.add('shake'); let message = ''; switch (state.guessPopupPatience) { case 2: message = phrases.guessPopup.strike1; break; case 1: message = phrases.guessPopup.strike2; break; case 0: message = phrases.guessPopup.strike3; break; } elements.guessPopup.brainText.textContent = message; setTimeout(() => { elements.guessPopup.content.classList.remove('shake'); if (state.guessPopupPatience <= 0) { elements.popups.guess.classList.add('hidden'); elements.game.guessButton.disabled = true; setTimeout(() => { elements.game.guessButton.disabled = false; }, config.guessButtonCooldown); } }, 500); return; } elements.popups.guess.classList.add('hidden'); const isCorrect = guess.toLowerCase() === state.secretCharacter.name.toLowerCase(); endGame(isCorrect);
}

async function showSuggestions() {
    if (state.suggestionUses >= config.suggestionLimit) { addMessageToChat("Has agotado tus sugerencias para esta partida.", "brain"); return; }
    const container = elements.suggestionPopup.buttonsContainer;
    container.innerHTML = 'Pensando en preguntas dignas...';
    elements.popups.suggestion.classList.remove('hidden');

    const suggestionPrompt = `Basado en este historial de chat, y sabiendo que el personaje secreto es ${state.secretCharacter.name}, genera 3 preguntas de SÍ/NO cortas y estratégicas que un jugador podría hacer. REGLAS: - NO reveles el nombre del personaje. - Las preguntas deben ser inteligentes y tener en cuenta las preguntas ya hechas. - Formato: Solo las preguntas, cada una en una nueva línea. Sin numeración ni texto introductorio. - Ejemplo: "¿Tu personaje pertenece al universo Marvel?" HISTORIAL: ${state.conversationHistory.map(m => `${m.role}: ${m.content}`).join('\n')}`;
    
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

// ============================================
// == INICIALIZACIÓN DEL JUEGO             ==
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    loadPlayerData();
    elements.title.startButton.addEventListener('click', showGameStage);
    elements.title.exitButton.addEventListener('click', () => { elements.arcadeScreen.classList.add('shutdown-effect'); });
    elements.game.askButton.addEventListener('click', handlePlayerInput);
    elements.game.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handlePlayerInput(); });
    elements.game.guessButton.addEventListener('click', showGuessPopup);
    elements.game.suggestionButton.addEventListener('click', showSuggestions);
    elements.game.backToMenu.addEventListener('click', () => closeCurtains(showGameStage, 1));
    elements.guessPopup.confirmButton.addEventListener('click', handleGuessAttempt);
    elements.guessPopup.input.addEventListener('keyup', (e) => { if (e.key === 'Enter') handleGuessAttempt(); });
    document.querySelectorAll('.end-buttons button').forEach(btn => { btn.addEventListener('click', (e) => { const action = e.target.dataset.action; Object.values(elements.screens).forEach(s => s.classList.add('hidden')); if (action === 'play-again') { closeCurtains(showGameStage, 1); } else if (action === 'main-menu') { runTitleSequence(); } }); });
    document.body.addEventListener('click', (e) => { if (e.target.dataset.close) { e.target.closest('.popup-overlay').classList.add('hidden'); } });
    
    runTitleSequence();
});
