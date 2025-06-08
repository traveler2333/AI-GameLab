document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const wordDisplay = document.getElementById('wordDisplay');
    const guessedLettersDisplaySpan = document.querySelector('#guessedLettersDisplay span');
    const letterInput = document.getElementById('letterInput');
    const guessButton = document.getElementById('guessButton');
    const hangmanRestartButton = document.getElementById('hangmanRestartButton');
    const gameStatusDisplay = document.getElementById('gameStatusDisplay');
    const hangmanErrorsLeftSpan = document.getElementById('hangmanErrorsLeft');

    function updateUI(gameState) {
        if (!gameState) {
            console.error('Invalid gameState received for Hangman');
            return;
        }

        wordDisplay.textContent = gameState.display_word ? gameState.display_word.join(' ') : '';
        guessedLettersDisplaySpan.textContent = gameState.guessed_letters ? Array.from(gameState.guessed_letters).join(', ') : '';

        if (typeof gameState.max_wrong_guesses !== 'undefined' && typeof gameState.wrong_guesses_count !== 'undefined') {
            hangmanErrorsLeftSpan.textContent = gameState.max_wrong_guesses - gameState.wrong_guesses_count;
        } else {
            hangmanErrorsLeftSpan.textContent = '-'; // Default if data missing
        }


        gameStatusDisplay.classList.remove('won', 'lost'); // Clear previous status classes
        switch (gameState.game_status) {
            case 'playing':
                gameStatusDisplay.textContent = '游戏进行中...';
                letterInput.disabled = false;
                guessButton.disabled = false;
                break;
            case 'won':
                gameStatusDisplay.textContent = '恭喜你，猜对了！ 🎉';
                gameStatusDisplay.classList.add('won');
                letterInput.disabled = true;
                guessButton.disabled = true;
                break;
            case 'lost':
                gameStatusDisplay.textContent = `游戏结束！正确的单词是: ${gameState.secret_word || ''}`;
                gameStatusDisplay.classList.add('lost');
                letterInput.disabled = true;
                guessButton.disabled = true;
                break;
            default:
                gameStatusDisplay.textContent = '';
                letterInput.disabled = true;
                guessButton.disabled = true;
        }
    }

    guessButton.addEventListener('click', () => {
        const letter = letterInput.value.trim().toUpperCase();
        if (letter && letter.length === 1 && letter.match(/[A-Z]/i)) {
            socket.emit('hangman_guess_letter', { letter: letter });
        }
        letterInput.value = '';
        letterInput.focus();
    });

    letterInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            guessButton.click();
        }
    });

    socket.on('hangman_update_state', updateUI);

    hangmanRestartButton.addEventListener('click', () => {
        socket.emit('hangman_start_game');
    });

    socket.on('connect', () => {
        console.log('Connected to server for Hangman game.');
        socket.emit('hangman_start_game'); // Initialize game on connection
    });

    socket.on('disconnect', () => {
        console.log("Disconnected from server (Hangman game).");
        gameStatusDisplay.textContent = "连接已断开";
        letterInput.disabled = true;
        guessButton.disabled = true;
    });
    socket.on('connect_error', (err) => {
        console.error("Connection error (Hangman game):", err);
        gameStatusDisplay.textContent = "连接错误";
        letterInput.disabled = true;
        guessButton.disabled = true;
    });
    console.log("Hangman game script loaded.");
});
