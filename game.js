// ===================================================================
// THE ORACLE - JavaScript Mejorado
// Typewriter + Burbujas + Sistema Pulido
// ===================================================================

// --- CONFIGURACIÓN ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 20, // Velocidad suave del typewriter (ms por carácter)
    backendURL: 'https://the-oracle-game.onrender.com/api/oracle',
    suggestionsAfterQuestion: 2,  // Sugerencias desde pregunta 2
    hintsAfterQuestion: 5,         // Pistas desde pregunta 5
    maxHints: 2                    // Máximo 2 pistas
};

// --- ESTADO ---
let state = {
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isWaitingResponse: false,
    hintsUsed: 0,
    askedQuestions: [],
    lastQuestion: null,
    incomprehensibleCount: 0  // Contador de preguntas no entendidas
};

// --- ELEMENTOS DOM ---
const el = {
    // Pantallas
    titleScreen: document.getElementById('title-screen'),
    gameScreen: document.getElementById('main-game-screen'),
    winScreen: document.getElementById('win-screen'),
    loseScreen: document.getElementById('lose-screen'),
    
    // Botones
    startBtn: document.getElementById('start-button'),
    exitBtn: document.getElementById('exit-button'),
    backBtn: document.getElementById('back-to-menu-button'),
    askBtn: document.getElementById('ask-button'),
    suggestionsBtn: document.getElementById('suggestions-btn'),
    hintsBtn: document.getElementById('hints-btn'),
    guessBtn: document.getElementById('guess-button'),
    
    // Inputs
    questionInput: document.getElementById('user-question-input'),
    chatHistory: document.getElementById('chat-history'),
    questionCounter: document.getElementById('question-counter'),
    
    // Pop-ups
    guessPopup: document.getElementById('guess-popup'),
    guessInput: document.getElementById('guess-input'),
    confirmGuess: document.getElementById('confirm-guess'),
    cancelGuess: document.getElementById('cancel-guess'),
    
    suggestionsPopup: document.getElementById('suggestions-popup'),
    suggestionsList: document.getElementById('suggestions-list'),
    closeSuggestions: document.getElementById('close-suggestions'),
    
    // Mensajes
    winMessage: document.getElementById('win-message'),
    loseMessage: document.getElementById('lose-message')
};


// ===================================================================
// FUNCIONES PRINCIPALES
// ===================================================================

async function startGame() {
    showScreen('game');
    resetGame();
    
    addMessageWithBubble('Concibiendo un nuevo enigma...', 'brain');
    
    try {
        const response = await fetch(config.backendURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'start' })
        });
        
        const data = await response.json();
        
        if (data.error) {
            addMessageWithBubble('Error al iniciar. Inténtalo de nuevo.', 'system');
            return;
        }
        
        state.secretCharacter = data.character;
        state.isGameActive = true;
        
        el.chatHistory.innerHTML = '';
        addMessageWithBubble('He concebido mi enigma. Comienza a preguntar.', 'brain', () => {
            // Activar solo input y botón de enviar al inicio
            el.questionInput.disabled = false;
            el.askBtn.disabled = false;
            el.questionInput.focus();
            // Botones desactivados al inicio
            updateButtonStates();
        });
        
    } catch (error) {
        console.error('Error:', error);
        addMessageWithBubble('Error de conexión con el backend. Verifica que esté ejecutándose.', 'system');
    }
}

async function askQuestion() {
    const question = el.questionInput.value.trim();
    if (!question || !state.isGameActive || state.isWaitingResponse) return;
    
    state.isWaitingResponse = true;
    el.questionInput.disabled = true;
    el.askBtn.disabled = true;
    
    // Mostrar pregunta del jugador INMEDIATAMENTE (sin typewriter)
    addMessageWithBubble(question, 'player', null, true);
    state.askedQuestions.push(question);
    el.questionInput.value = '';
    
    try {
        const response = await fetch(config.backendURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'ask',
                question: question,
                character: state.secretCharacter,
                question_count: state.questionCount,
                asked_questions: state.askedQuestions
            })
        });
        
        const data = await response.json();
        
        // Construir respuesta completa
        const fullAnswer = data.clarification 
            ? `${data.answer} ${data.clarification}` 
            : data.answer;
        
        // Verificar si fue pregunta incomprensible
        if (data.answer === 'No lo sé' && data.clarification && data.clarification.includes('reformula')) {
            state.incomprehensibleCount++;
            
            // Si ocurre 2 veces, ofrecer sugerencias
            if (state.incomprehensibleCount >= 2) {
                addMessageWithBubble(fullAnswer + ' ¿Necesitas sugerencias?', 'brain');
                state.incomprehensibleCount = 0;
            } else {
                addMessageWithBubble(fullAnswer, 'brain');
            }
        } else {
            // Respuesta normal con typewriter
            addMessageWithBubble(fullAnswer, 'brain');
            state.questionCount++;
            updateQuestionCounter();
            updateButtonStates();
            state.incomprehensibleCount = 0; // Resetear contador
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessageWithBubble('Error al procesar pregunta.', 'system');
    }
    
    state.isWaitingResponse = false;
    
    if (state.questionCount >= config.questionsLimit) {
        addMessageWithBubble('Has agotado tus preguntas. ¡Debes adivinar ahora!', 'system');
        el.questionInput.disabled = true;
        el.askBtn.disabled = true;
    } else if (state.isGameActive) {
        el.questionInput.disabled = false;
        el.askBtn.disabled = false;
        el.questionInput.focus();
    }
}

async function getSuggestions() {
    if (!state.isGameActive) return;
    
    try {
        const response = await fetch(config.backendURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'suggestions',
                character: state.secretCharacter,
                question_count: state.questionCount,
                asked_questions: state.askedQuestions
            })
        });
        
        const data = await response.json();
        
        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestionsPopup(data.suggestions);
        } else {
            addMessageWithBubble('No hay sugerencias disponibles en este momento.', 'system');
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessageWithBubble('Error al obtener sugerencias.', 'system');
    }
}

async function getHint() {
    if (!state.isGameActive) return;
    if (state.questionCount < config.hintsAfterQuestion) {
        addMessageWithBubble(`Las pistas están disponibles después de la pregunta ${config.hintsAfterQuestion}.`, 'system');
        return;
    }
    if (state.hintsUsed >= config.maxHints) {
        addMessageWithBubble('Ya has usado todas las pistas disponibles.', 'system');
        return;
    }
    
    try {
        const response = await fetch(config.backendURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'hint',
                character: state.secretCharacter,
                hint_level: state.hintsUsed + 1
            })
        });
        
        const data = await response.json();
        
        if (data.hint) {
            state.hintsUsed++;
            addMessageWithBubble(`🔮 PISTA ${state.hintsUsed}/${config.maxHints}: ${data.hint}`, 'system');
            updateButtonStates();
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessageWithBubble('Error al obtener pista.', 'system');
    }
}

function showSuggestionsPopup(suggestions) {
    el.suggestionsList.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = suggestion;
        item.onclick = () => {
            el.questionInput.value = suggestion;
            closeSuggestionsPopup();
            el.questionInput.focus();
        };
        el.suggestionsList.appendChild(item);
    });
    
    el.suggestionsPopup.classList.remove('hidden');
}

function closeSuggestionsPopup() {
    el.suggestionsPopup.classList.add('hidden');
}

function openGuessPopup() {
    el.guessPopup.classList.remove('hidden');
    el.guessInput.value = '';
    el.guessInput.focus();
}

function closeGuessPopup() {
    el.guessPopup.classList.add('hidden');
}

async function confirmGuess() {
    const guess = el.guessInput.value.trim();
    if (!guess) return;
    
    closeGuessPopup();
    
    try {
        const response = await fetch(config.backendURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'guess',
                guess: guess,
                character: state.secretCharacter
            })
        });
        
        const data = await response.json();
        endGame(data.correct, data.character);
        
    } catch (error) {
        addMessageWithBubble('Error al verificar adivinanza.', 'system');
    }
}

function endGame(won, characterName) {
    state.isGameActive = false;
    
    if (won) {
        el.winMessage.textContent = `¡Correcto! El personaje era ${characterName}.`;
        showScreen('win');
    } else {
        el.loseMessage.textContent = `Has fallado. El personaje era ${characterName}.`;
        showScreen('lose');
    }
}

function resetGame() {
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isWaitingResponse = false;
    state.hintsUsed = 0;
    state.askedQuestions = [];
    state.lastQuestion = null;
    state.incomprehensibleCount = 0;
    
    el.questionCounter.textContent = `0/${config.questionsLimit}`;
    el.chatHistory.innerHTML = '';
    el.questionInput.value = '';
    
    // TODOS los botones desactivados al inicio
    el.questionInput.disabled = true;
    el.askBtn.disabled = true;
    el.suggestionsBtn.disabled = true;
    el.hintsBtn.disabled = true;
    el.guessBtn.disabled = true;
}

function updateQuestionCounter() {
    el.questionCounter.textContent = `${state.questionCount}/${config.questionsLimit}`;
}

function updateButtonStates() {
    // Sugerencias: disponible desde pregunta 2
    if (state.questionCount >= config.suggestionsAfterQuestion) {
        el.suggestionsBtn.disabled = false;
    } else {
        el.suggestionsBtn.disabled = true;
    }
    
    // Pistas: disponible desde pregunta 5, máximo 2
    if (state.questionCount >= config.hintsAfterQuestion && state.hintsUsed < config.maxHints) {
        el.hintsBtn.disabled = false;
        el.hintsBtn.textContent = `PISTAS (${config.maxHints - state.hintsUsed})`;
    } else {
        el.hintsBtn.disabled = true;
        if (state.questionCount < config.hintsAfterQuestion) {
            const remaining = config.hintsAfterQuestion - state.questionCount;
            el.hintsBtn.textContent = `PISTAS (EN ${remaining})`;
        } else {
            el.hintsBtn.textContent = `PISTAS (0)`;
        }
    }
    
    // Adivinar: disponible cuando el juego está activo
    if (state.isGameActive) {
        el.guessBtn.disabled = false;
    }
}


// ===================================================================
// SISTEMA DE MENSAJES CON BURBUJAS Y TYPEWRITER
// ===================================================================

function addMessageWithBubble(text, sender, callback, skipTypewriter = false) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    
    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : (sender === 'player' ? '👤' : '⚙️');
    
    // Contenedor de la burbuja
    const bubbleContainer = document.createElement('div');
    bubbleContainer.style.flex = '1';
    
    // Nombre del emisor
    const senderName = document.createElement('div');
    senderName.className = 'message-sender';
    if (sender === 'brain') {
        senderName.textContent = ' Oráculo:';
        senderName.style.color = '#ff00ff';
    } else if (sender === 'player') {
        senderName.textContent = ' Tú:';
        senderName.style.color = '#0f0';
    } else {
        senderName.textContent = '⚙️ Sistema:';
        senderName.style.color = '#888';
    }
    
    // Burbuja de mensaje
    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';
    
    // Ensamblar
    bubbleContainer.appendChild(senderName);
    bubbleContainer.appendChild(messageBubble);
    messageLine.appendChild(avatar);
    messageLine.appendChild(bubbleContainer);
    el.chatHistory.appendChild(messageLine);
    scrollToBottom();
    
    // Aplicar typewriter solo para el Oráculo y si no se salta
    if (sender === 'brain' && !skipTypewriter) {
        typewriterEffect(messageBubble, text, callback);
    } else {
        // Mostrar inmediatamente para jugador y sistema
        messageBubble.textContent = text;
        if (callback) callback();
    }
}

function typewriterEffect(element, text, callback) {
    let i = 0;
    element.textContent = '';
    
    const interval = setInterval(() => {
        if (i >= text.length) {
            clearInterval(interval);
            if (callback) callback();
            return;
        }
        
        element.textContent += text[i++];
        scrollToBottom();
    }, config.typewriterSpeed);
}

function scrollToBottom() {
    el.chatHistory.scrollTop = el.chatHistory.scrollHeight;
}

function showScreen(screenName) {
    el.titleScreen.classList.add('hidden');
    el.gameScreen.classList.add('hidden');
    el.winScreen.classList.add('hidden');
    el.loseScreen.classList.add('hidden');
    
    switch(screenName) {
        case 'title':
            el.titleScreen.classList.remove('hidden');
            break;
        case 'game':
            el.gameScreen.classList.remove('hidden');
            break;
        case 'win':
            el.winScreen.classList.remove('hidden');
            break;
        case 'lose':
            el.loseScreen.classList.remove('hidden');
            break;
    }
}


// ===================================================================
// EVENT LISTENERS
// ===================================================================

el.startBtn.addEventListener('click', startGame);
el.exitBtn.addEventListener('click', () => window.close());
el.backBtn.addEventListener('click', () => location.reload());

el.askBtn.addEventListener('click', askQuestion);
el.questionInput.addEventListener('keyup', (e) => {
    if (e.key === 'Enter' && !el.askBtn.disabled) askQuestion();
});

el.suggestionsBtn.addEventListener('click', getSuggestions);
el.hintsBtn.addEventListener('click', getHint);
el.guessBtn.addEventListener('click', openGuessPopup);

el.confirmGuess.addEventListener('click', confirmGuess);
el.cancelGuess.addEventListener('click', closeGuessPopup);
el.closeSuggestions.addEventListener('click', closeSuggestionsPopup);

el.guessInput.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') confirmGuess();
});


// ===================================================================
// INICIALIZACIÓN
// ===================================================================

console.log('🧠 THE ORACLE - Juego Mejorado');
console.log('✅ Typewriter suave activado');
console.log('✅ Burbujas de diálogo implementadas');
console.log('✅ 20 personajes disponibles');
console.log('✅ Sistema robusto de respuestas');
