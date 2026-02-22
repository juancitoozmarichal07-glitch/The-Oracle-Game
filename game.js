// ===================================================================
// THE ORACLE - JavaScript Mejorado
// Typewriter + Burbujas + Sistema Pulido + TEMPORIZADOR + SONIDOS
// ===================================================================

// --- CONFIGURACIÓN ---
const config = {
    questionsLimit: 20,
    typewriterSpeed: 20,
    backendURL: 'http://127.0.0.1:5000/api/oracle',
    suggestionsAfterQuestion: 2,
    hintsAfterQuestion: 5,
    maxHints: 2
};

// ===================================================================
// GENERADOR DE SONIDOS MEJORADO (Web Audio API)
// ===================================================================
const AudioContext = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;
let backgroundInterval = null;

// Inicializar audio (llamar desde un evento de usuario)
function initAudio() {
    if (audioCtx) return;
    try {
        audioCtx = new AudioContext();
        console.log('✅ Audio inicializado');
    } catch (e) {
        console.warn('❌ No se pudo inicializar audio:', e);
    }
}

// Reproducir sonido de forma robusta
function playSound(type) {
    if (!audioCtx) {
        initAudio();
        if (!audioCtx) return;
    }
    
    if (audioCtx.state === 'suspended') {
        audioCtx.resume().then(() => {
            generateSound(type);
        }).catch(e => console.warn('Error al reanudar audio:', e));
    } else {
        generateSound(type);
    }
}

// Generar sonidos mejorados
function generateSound(type) {
    if (!audioCtx) return;
    
    const now = audioCtx.currentTime;
    
    switch(type) {
        case 'button':
            const oscBtn = audioCtx.createOscillator();
            const gainBtn = audioCtx.createGain();
            oscBtn.connect(gainBtn);
            gainBtn.connect(audioCtx.destination);
            
            oscBtn.frequency.value = 800;
            gainBtn.gain.setValueAtTime(0.1, now);
            gainBtn.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
            
            oscBtn.start(now);
            oscBtn.stop(now + 0.08);
            break;
            
        case 'start':
            [400, 500, 600].forEach((freq, i) => {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.15, now + i * 0.1);
                gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.1 + 0.2);
                
                osc.start(now + i * 0.1);
                osc.stop(now + i * 0.1 + 0.2);
            });
            break;
            
        case 'victory':
            [262, 330, 392].forEach((freq, i) => {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 1.0);
                
                osc.start(now);
                osc.stop(now + 1.0);
            });
            
            setTimeout(() => {
                if (!audioCtx || audioCtx.state !== 'running') return;
                const osc2 = audioCtx.createOscillator();
                const gain2 = audioCtx.createGain();
                osc2.connect(gain2);
                gain2.connect(audioCtx.destination);
                osc2.frequency.value = 523;
                gain2.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
                osc2.start();
                osc2.stop(audioCtx.currentTime + 0.5);
            }, 800);
            break;
            
        case 'defeat':
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            
            osc.frequency.setValueAtTime(300, now);
            osc.frequency.exponentialRampToValueAtTime(150, now + 1.2);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
            
            osc.start(now);
            osc.stop(now + 1.2);
            break;
            
        case 'background':
            if (backgroundInterval) clearInterval(backgroundInterval);
            
            const playBackgroundNote = () => {
                if (!audioCtx || audioCtx.state !== 'running') return;
                
                const now = audioCtx.currentTime;
                
                const osc1 = audioCtx.createOscillator();
                const gain1 = audioCtx.createGain();
                osc1.connect(gain1);
                gain1.connect(audioCtx.destination);
                
                osc1.frequency.value = 220;
                gain1.gain.setValueAtTime(0.02, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 1.0);
                
                osc1.start(now);
                osc1.stop(now + 1.0);
                
                setTimeout(() => {
                    if (!audioCtx || audioCtx.state !== 'running') return;
                    const osc2 = audioCtx.createOscillator();
                    const gain2 = audioCtx.createGain();
                    osc2.connect(gain2);
                    gain2.connect(audioCtx.destination);
                    
                    osc2.frequency.value = 330;
                    gain2.gain.setValueAtTime(0.02, audioCtx.currentTime);
                    gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.8);
                    
                    osc2.start();
                    osc2.stop(audioCtx.currentTime + 0.8);
                }, 1200);
            };
            
            playBackgroundNote();
            backgroundInterval = setInterval(playBackgroundNote, 2500);
            break;
    }
}

function stopBackgroundMusic() {
    if (backgroundInterval) {
        clearInterval(backgroundInterval);
        backgroundInterval = null;
    }
}
// ===================================================================

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
    // Inicializar audio y reproducir sonidos de inicio
    if (!audioCtx) initAudio();
    playSound('start');
    playSound('background');
    
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
    playSound('button');
    
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
    playSound('button');
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
    playSound('button');
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
    playSound('button');
    el.suggestionsList.innerHTML = '';
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = suggestion;
        item.onclick = () => {
            playSound('button');
            el.questionInput.value = suggestion;
            closeSuggestionsPopup();
            el.questionInput.focus();
        };
        el.suggestionsList.appendChild(item);
    });
    el.suggestionsPopup.classList.remove('hidden');
}

function closeSuggestionsPopup() {
    playSound('button');
    el.suggestionsPopup.classList.add('hidden');
}

function openGuessPopup() {
    playSound('button');
    el.guessPopup.classList.remove('hidden');
    el.guessInput.value = '';
    el.guessInput.focus();
}

function closeGuessPopup() {
    playSound('button');
    el.guessPopup.classList.add('hidden');
}

async function confirmGuess() {
    playSound('button');
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
    stopBackgroundMusic();
    
    if (won) {
        playSound('victory');
        el.winMessage.textContent = `¡Correcto! El personaje era ${characterName}.`;
        showScreen('win');
    } else {
        playSound('defeat');
        el.loseMessage.textContent = `Has fallado. El personaje era ${characterName}.`;
        showScreen('lose');
    }
    
    state.isGameActive = false;
    stopTimer();
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
    senderName.textContent = sender === 'brain' ? ' Oráculo:' : (sender === 'player' ? ' Tú:' : ' Sistema:');
    
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
el.exitBtn.addEventListener('click', () => {
    playSound('button');
    window.close();
});
el.backBtn.addEventListener('click', () => {
    playSound('button');
    stopBackgroundMusic();
    location.reload();
});

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

console.log('🧠 THE ORACLE GAME - Versión Arcade con temporizador y sonidos');

// ===================================================================
// EFECTO DE APAGADO - EL ORÁCULO TE EXPULSA (Versión legible)
// ===================================================================

// Añadir estilos de animación (manteniendo el formato legible)
const shutdownStyle = document.createElement('style');
shutdownStyle.textContent = `
    .shutdown-effect {
        animation: shutdown 0.9s forwards;
    }
    
    @keyframes shutdown {
        0% { transform: scaleY(1); opacity: 1; }
        30% { transform: scaleY(0.1) scaleX(1.5); opacity: 1; }
        60% { transform: scaleY(0.01) scaleX(1.8); opacity: 0.5; }
        100% { transform: scaleY(0) scaleX(2); opacity: 0; }
    }
    
    /* Mismo formato legible que usaste antes */
    .farewell-message {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #111;
        border: 3px solid #ff00ff;
        box-shadow: 0 0 30px #ff00ff;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        width: 90%;
        max-width: 500px;
        z-index: 1000;
        animation: fadeIn 0.5s;
        font-family: Arial, sans-serif;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translate(-50%, -40%); }
        to { opacity: 1; transform: translate(-50%, -50%); }
    }
    
    .farewell-message h3 {
        color: #ff00ff;
        font-size: 1.2em;
        margin-bottom: 20px;
        font-weight: bold;
    }
    
    .farewell-message p {
        color: #fff;
        font-size: 0.95em;
        line-height: 1.6;
        margin: 15px 0;
    }
    
    .farewell-message .brain-icon {
        font-size: 60px;
        filter: drop-shadow(0 0 20px #ff00ff);
        margin-bottom: 10px;
    }
    
    .farewell-message .green-text {
        color: #0f0;
    }
    
    .farewell-message .quote {
        color: #888;
        font-size: 0.8em;
        margin-top: 20px;
        font-style: italic;
        border-top: 1px solid #333;
        padding-top: 15px;
    }
    
    .farewell-message button {
        background-color: #222;
        color: #0f0;
        border: 2px solid #0f0;
        padding: 12px 25px;
        margin: 10px 0 5px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.85em;
        font-weight: bold;
        text-transform: uppercase;
        transition: all 0.2s;
        width: 100%;
        max-width: 300px;
    }
    
    .farewell-message button:hover {
        background-color: #0f0;
        color: #000;
        box-shadow: 0 0 15px #0f0;
    }
    
    .farewell-message button.purple {
        border-color: #ff00ff;
        color: #ff00ff;
    }
    
    .farewell-message button.purple:hover {
        background-color: #ff00ff;
        color: #000;
        box-shadow: 0 0 15px #ff00ff;
    }
`;
document.head.appendChild(shutdownStyle);

// Reemplazar el event listener del botón de salir
if (el.exitBtn) {
    const oldBtn = el.exitBtn;
    const newBtn = oldBtn.cloneNode(true);
    oldBtn.parentNode.replaceChild(newBtn, oldBtn);
    el.exitBtn = newBtn;
    
    el.exitBtn.addEventListener('click', () => {
        playSound('button');
        // Efecto de apagado
        const screen = document.getElementById('arcade-screen');
        screen.classList.add('shutdown-effect');
        
        // Mensaje de despedida (mismo formato legible)
        const farewell = document.createElement('div');
        farewell.className = 'farewell-message';
        farewell.innerHTML = `
            <div class="brain-icon">🧠</div>
            <h3>EL ORÁCULO TE EXPULSA</h3>
            <p>Has presionado el botón de salida.<br><span class="green-text">No hay vuelta atrás.</span></p>
            <p style="color: #ff00ff; font-size: 1.1em;">Tu tiempo en este plano ha terminado.</p>
            <p>Si deseas volver a buscar conocimiento,<br>deberás invocar al Oráculo nuevamente<br>recargando la página.</p>
            <div class="quote">"El que abandona el templo del saber,<br>solo regresa si el cosmos lo permite"</div>
            <button class="purple" onclick="window.location.reload()">🔄 INVOCAR DE NUEVO</button>
        `;
        document.body.appendChild(farewell);
    });
}
