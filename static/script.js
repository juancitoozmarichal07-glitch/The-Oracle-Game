<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>The Oracle Game</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js')
                    .then(registration => console.log('[PWA] ServiceWorker registrado con éxito:', registration.scope))
                    .catch(error => console.log('[PWA] Fallo en el registro de ServiceWorker:', error));
            });
        }
    </script>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div id="arcade-screen">
        <!-- PANTALLA DE TÍTULO -->
        <div id="title-screen" class="screen">
            <div id="lightning-overlay"></div>
            <div id="intro-brain">🧠</div>
            <div id="title-layout" class="hidden">
                <div id="title-brain">🧠</div>
                <h1 id="game-title" data-text="THE ORACLE GAME">THE ORACLE GAME</h1>
                <div id="title-buttons">
                    <button id="start-button" class="button-green blink">PLAYER 1 START</button>
                    <button id="exit-button" class="button-red">SALIR</button>
                </div>
            </div>
        </div>

        <!-- ESCENA DEL TELÓN Y MENÚ -->
        <div id="game-stage" class="screen hidden">
           <div id="stage-lights">
                <div class="spotlight"></div>
                <div class="spotlight"></div>
            </div>
            <div id="stage-content-container">
                <div class="spotlight-container">
                    <div id="stage-brain">🧠</div>
                </div>
                <div id="stage-dialog"></div>
                <div id="menu-buttons"></div>
            </div>
            <div id="curtain-left" class="curtain"></div>
            <div id="curtain-right" class="curtain"></div>
        </div>

        <!-- PANTALLA DE JUEGO PRINCIPAL -->
        <div id="main-game-screen" class="screen hidden">
            <div class="game-header">
                <button id="back-to-menu-button">‹ MENÚ</button>
                <p id="question-counter">Pregunta: 0/20</p>
            </div>
            <div id="chat-history"></div>
            <div class="player-controls">
                <!-- Controles Modo Oráculo -->
                <div id="oracle-mode-controls">
                    <div class="input-area">
                        <input type="text" id="user-question-input" placeholder="Escribe tu pregunta...">
                        <button id="ask-button"><svg viewBox="0 0 24 24"><path d="M2,21L23,12L2,3V10L17,12L2,14V21Z" /></svg></button>
                    </div>
                    <div class="action-buttons">
                        <button id="clue-button" class="button-purple">Pista 3/3</button>
                        <button id="suggestion-button" class="button-green">Sugerencias 5/5</button>
                    </div>
                    <div class="action-buttons">
                         <button id="guess-button" class="button-red">¡Adivinar!</button>
                    </div>
                </div>
                <!-- Controles Modo Clásico -->
                <div id="classic-mode-controls" class="hidden">
                    <div class="classic-answer-buttons">
                        <button class="answer-btn" data-answer="Sí">Sí</button>
                        <button class="answer-btn" data-answer="No">No</button>
                        <button class="answer-btn" data-answer="No lo sé">No lo sé</button>
                        <button class="answer-btn" data-answer="Probablemente Sí">Prob. Sí</button>
                        <button class="answer-btn" data-answer="Probablemente No">Prob. No</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- PANTALLAS FINALES -->
        <div id="win-screen" class="end-screen screen hidden">
            <div class="end-screen-content">
                <h1>¡VICTORIA!</h1>
                <p id="win-message"></p>
                <div class="end-buttons">
                    <button class="end-screen-btn" data-action="play-again">Jugar de Nuevo</button>
                    <button class="end-screen-btn" data-action="main-menu">Menú Principal</button>
                </div>
            </div>
        </div>
        <div id="lose-screen" class="end-screen screen hidden">
            <div class="end-screen-content">
                <h1>DERROTA</h1>
                <p id="lose-message"></p>
                <div class="end-buttons">
                    <button class="end-screen-btn" data-action="play-again">Jugar de Nuevo</button>
                    <button class="end-screen-btn" data-action="main-menu">Menú Principal</button>
                </div>
            </div>
        </div>
    </div>

    <!-- POP-UPS -->
    <div id="popups-container">
        <div id="guess-popup" class="popup-overlay hidden">
            <div class="popup-content-guess">
                <div class="popup-header">
                    <div id="guess-popup-brain-icon">🧠</div>
                    <div id="guess-popup-dialog">
                        <p id="guess-popup-brain-text">Susurra tu respuesta al vacío...</p>
                    </div>
                </div>
                <div class="popup-body">
                    <h3 id="guess-popup-title">Tu Adivinanza Final</h3>
                    <p id="guess-popup-instruction">Escribe el nombre del ser que tú crees que estoy pensando.</p>
                    <input type="text" id="guess-input" placeholder="Escribe tu respuesta...">
                    <div class="popup-buttons">
                        <button id="confirm-guess-button" class="button-green">Confirmar</button>
                        <button data-close="guess-popup" class="button-red">Cancelar</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="clue-card-popup" class="popup-overlay hidden">
            <div id="clue-card">
                <div class="card-front">
                    <div class="card-symbol">?</div>
                </div>
                <div class="card-back">
                    <div class="card-header">Un Susurro del Cosmos</div>
                    <div id="clue-card-text"></div>
                    <button data-close="clue-card-popup" class="card-close-button">Cerrar</button>
                </div>
            </div>
        </div>

        <div id="suggestion-popup" class="popup-overlay hidden">
            <div class="popup-content">
                <h3>Sugerencias del Oráculo</h3>
                <div id="suggestion-buttons-container"></div>
                <div class="popup-buttons">
                    <button data-close="suggestion-popup" class="button-green">Cerrar</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- =================================================================== -->
    <!-- ===   DEFINICIÓN DE SONIDOS (RUTAS ABSOLUTAS PARA VERCEL)       === -->
    <!-- =================================================================== -->
    <audio id="badass-victory-sound" src="/sounds/badass victory.mp3" preload="auto"></audio>
    <audio id="boo-sound" src="/sounds/boo.mp3" preload="auto"></audio>
    <audio id="button-click-sound" src="/sounds/buttons.mp3" preload="auto"></audio>
    <audio id="curtain-sound" src="/sounds/curtain.mp3" preload="auto"></audio>
    <audio id="game-over-sound" src="/sounds/game over.mp3" preload="auto"></audio>
    <audio id="key-press-sound" src="/sounds/key-press.mp3" preload="auto"></audio>
    <audio id="lobby-sound" src="/sounds/lobby.mp3" preload="auto" loop></audio>
    <audio id="select-button-sound" src="/sounds/select button.mp3" preload="auto"></audio>
    <audio id="thunder-sound" src="/sounds/thunder.mp3" preload="auto"></audio>
    <audio id="typewriter-sound" src="/sounds/typewriter.mp3" preload="auto" loop></audio>
    <audio id="victory-normal-sound" src="/sounds/victory normal.mp3" preload="auto"></audio>
    <audio id="victory-voice-sound" src="/sounds/victory voice.mp3" preload="auto"></audio>

    <script src="/script.js"></script>
</body>
</html>
