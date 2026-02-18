// ===================================================================
// THE ORACLE - JavaScript Mejorado
// Typewriter + Burbujas + Sistema Pulido + TEMPORIZADOR
// ===================================================================

// --- CONFIGURACIÓN ---
const config = {
const config = {
    questionsLimit: 20,
    typewriterSpeed: 20, // Velocidad suave del typewriter (ms por carácter)
    backendURL: 'https://the-oracle-game.onrender.com/api/oracle',
    suggestionsAfterQuestion: 2,  // Sugerencias desde pregunta 2
    hintsAfterQuestion: 5,         // Pistas desde pregunta 5
    maxHints: 2                    // Máximo 2 pistas
};

En game.js

// --- ESTADO ---
let state = {
    questionCount: 0,
    secretCharacter: null,
    isGameActive: false,
    isWaitingResponse: false,
    hintsUsed: 0,
    askedQuestions: [],
    lastQuestion: null,
    incomprehensibleCount: 0,
    timerInterval: null,
    timerSeconds: 0
};

// --- ELEMENTOS DOM ---
const el = {
    titleScreen: document.getElementById('title-screen'),
    gameScreen: document.getElementById('main-game-screen'),
    winScreen: document.getElementById('win-screen'),
    loseScreen: document.getElementById('lose-screen'),
    
    startBtn: document.getElementById('start-button'),
    exitBtn: document.getElementById('exit-button'),
    backBtn: document.getElementById('back-to-menu-button'),
    askBtn: document.getElementById('ask-button'),
    suggestionsBtn: document.getElementById('suggestions-btn'),
    hintsBtn: document.getElementById('hints-btn'),
    guessBtn: document.getElementById('guess-button'),
    
    questionInput: document.getElementById('user-question-input'),
    chatHistory: document.getElementById('chat-history'),
    questionCounter: document.getElementById('question-counter'),
    timerDisplay: document.getElementById('timer-display'),
    
    guessPopup: document.getElementById('guess-popup'),
    guessInput: document.getElementById('guess-input'),
    confirmGuess: document.getElementById('confirm-guess'),
    cancelGuess: document.getElementById('cancel-guess'),
    
    suggestionsPopup: document.getElementById('suggestions-popup'),
    suggestionsList: document.getElementById('suggestions-list'),
    closeSuggestions: document.getElementById('close-suggestions'),
    
    winMessage: document.getElementById('win-message'),
    loseMessage: document.getElementById('lose-message')
};

// === FUNCIONES DEL TEMPORIZADOR ===
function startTimer() {
    state.timerSeconds = 0;
    updateTimerDisplay();
    
    if (state.timerInterval) clearInterval(state.timerInterval);
    
    state.timerInterval = setInterval(() => {
        state.timerSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
}

function updateTimerDisplay() {
    if (el.timerDisplay) {
        const minutes = Math.floor(state.timerSeconds / 60);
        const seconds = state.timerSeconds % 60;
        el.timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// === FUNCIONES PRINCIPALES ===
async function startGame() {
    showScreen('game');
    resetGame();
    startTimer();
    
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
            el.questionInput.disabled = false;
            el.askBtn.disabled = false;
            el.questionInput.focus();
            updateButtonStates();
        });
        
    } catch (error) {
        console.error('Error:', error);
        addMessageWithBubble('Error de conexión con el backend.', 'system');
    }
}

async function askQuestion() {
    const question = el.questionInput.value.trim();
    if (!question || !state.isGameActive || state.isWaitingResponse) return;
    
    state.isWaitingResponse = true;
    el.questionInput.disabled = true;
    el.askBtn.disabled = true;
    
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
        const fullAnswer = data.clarification ? `${data.answer} ${data.clarification}` : data.answer;
        
        if (data.answer === 'No lo sé' && data.clarification && data.clarification.includes('reformula')) {
            state.incomprehensibleCount++;
            if (state.incomprehensibleCount >= 2) {
                addMessageWithBubble(fullAnswer + ' ¿Necesitas sugerencias?', 'brain');
                state.incomprehensibleCount = 0;
            } else {
                addMessageWithBubble(fullAnswer, 'brain');
            }
        } else {
            addMessageWithBubble(fullAnswer, 'brain');
            state.questionCount++;
            updateQuestionCounter();
            updateButtonStates();
            state.incomprehensibleCount = 0;
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
    stopTimer();
    
    if (won) {
        el.winMessage.textContent = `¡Correcto! El personaje era ${characterName}.`;
        showScreen('win');
    } else {
        el.loseMessage.textContent = `Has fallado. El personaje era ${characterName}.`;
        showScreen('lose');
    }
}

function resetGame() {
    stopTimer();
    state.questionCount = 0;
    state.secretCharacter = null;
    state.isGameActive = false;
    state.isWaitingResponse = false;
    state.hintsUsed = 0;
    state.askedQuestions = [];
    state.lastQuestion = null;
    state.incomprehensibleCount = 0;
    state.timerSeconds = 0;
    
    if (el.timerDisplay) el.timerDisplay.textContent = '00:00';
    el.questionCounter.textContent = `0/${config.questionsLimit}`;
    el.chatHistory.innerHTML = '';
    el.questionInput.value = '';
    
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
    el.suggestionsBtn.disabled = state.questionCount < config.suggestionsAfterQuestion;
    
    if (state.questionCount >= config.hintsAfterQuestion && state.hintsUsed < config.maxHints) {
        el.hintsBtn.disabled = false;
        el.hintsBtn.textContent = `PISTAS (${config.maxHints - state.hintsUsed})`;
    } else {
        el.hintsBtn.disabled = true;
        el.hintsBtn.textContent = state.questionCount < config.hintsAfterQuestion 
            ? `PISTAS (EN ${config.hintsAfterQuestion - state.questionCount})` 
            : 'PISTAS (0)';
    }
    
    el.guessBtn.disabled = !state.isGameActive;
}

// === SISTEMA DE MENSAJES ===
function addMessageWithBubble(text, sender, callback, skipTypewriter = false) {
    const messageLine = document.createElement('div');
    messageLine.className = `message-line message-line-${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'brain' ? '🧠' : (sender === 'player' ? '👤' : '⚙️');
    
    const bubbleContainer = document.createElement('div');
    bubbleContainer.style.flex = '1';
    
    const senderName = document.createElement('div');
    senderName.className = 'message-sender';
    senderName.style.color = sender === 'brain' ? '#ff00ff' : (sender === 'player' ? '#0f0' : '#888');
    senderName.textContent = sender === 'brain' ? ' Oráculo:' : (sender === 'player' ? ' Tú:' : '⚙️ Sistema:');
    
    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';
    
    bubbleContainer.appendChild(senderName);
    bubbleContainer.appendChild(messageBubble);
    messageLine.appendChild(avatar);
    messageLine.appendChild(bubbleContainer);
    el.chatHistory.appendChild(messageLine);
    scrollToBottom();
    
    if (sender === 'brain' && !skipTypewriter) {
        typewriterEffect(messageBubble, text, callback);
    } else {
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
    el[`${screenName}Screen`].classList.remove('hidden');
}

// === EVENT LISTENERS ===
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
el.guessInput.addEventListener('keyup', (e) => e.key === 'Enter' && confirmGuess());

console.log('🧠 THE ORACLE GAME - Versión Arcade con temporizador');
