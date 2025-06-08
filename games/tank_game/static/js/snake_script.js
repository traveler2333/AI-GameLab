document.addEventListener('DOMContentLoaded', () => {
    // Connects to the server that served this HTML file (main app on port 5000)
    const socket = io();

    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const gameOverScreen = document.getElementById('gameOverScreen');
    const finalScoreDisplay = document.getElementById('finalScore');
    const restartButton = document.getElementById('restartButtonSnake');

    // These should ideally be sent by the server on game init for consistency
    let GRID_SIZE = 20;
    let CANVAS_WIDTH = 400;
    let CANVAS_HEIGHT = 400;
    // Canvas dimensions will be set based on first state update from server

    function drawPixel(x, y, color) {
        ctx.fillStyle = color;
        ctx.fillRect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE -1 , GRID_SIZE -1);
    }

    function drawGame(gameState) {
        if (!gameState || !gameState.grid_size) { // Wait for server to send game constants
            console.log("Waiting for game state with grid info...");
            return;
        }

        // Update local constants if they differ (e.g. on first load)
        if (GRID_SIZE !== gameState.grid_size) GRID_SIZE = gameState.grid_size;
        const expectedCanvasWidth = gameState.grid_width * GRID_SIZE;
        const expectedCanvasHeight = gameState.grid_height * GRID_SIZE;

        if (canvas.width !== expectedCanvasWidth) canvas.width = expectedCanvasWidth;
        if (canvas.height !== expectedCanvasHeight) canvas.height = expectedCanvasHeight;


        ctx.fillStyle = '#ecf0f1';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (gameState.snake_body) {
            gameState.snake_body.forEach((segment, index) => {
                drawPixel(segment[0], segment[1], index === 0 ? '#2c3e50' : '#3498db');
            });
        }

        if (gameState.food_pos) {
            drawPixel(gameState.food_pos[0], gameState.food_pos[1], '#e74c3c');
        }

        scoreDisplay.textContent = `分数: ${gameState.score || 0}`;

        if (gameState.is_game_over) {
            finalScoreDisplay.textContent = gameState.score || 0;
            gameOverScreen.style.display = 'block';
        } else {
            gameOverScreen.style.display = 'none';
        }
    }

    socket.on('snake_update_state', (gameState) => {
        if(gameState){
             drawGame(gameState);
        } else {
            console.error("Received null or undefined gameState for snake");
        }
    });

    document.addEventListener('keydown', (event) => {
        let direction = null;
        switch (event.key.toLowerCase()) {
            case 'arrowup': case 'w': direction = 'UP'; break;
            case 'arrowdown': case 's': direction = 'DOWN'; break;
            case 'arrowleft': case 'a': direction = 'LEFT'; break;
            case 'arrowright': case 'd': direction = 'RIGHT'; break;
        }
        if (direction) {
            socket.emit('snake_change_direction', { direction });
            event.preventDefault();
        }
    });

    restartButton.addEventListener('click', () => {
        socket.emit('snake_start_game');
    });

    socket.on('connect', () => {
        console.log("Connected to main server for Snake game.");
        // Request the server to start/initialize the snake game for this client/session
        socket.emit('snake_start_game');
    });

    socket.on('disconnect', () => {
        console.log("Disconnected from main server (Snake game).");
    });
    socket.on('connect_error', (err) => {
        console.error("Connection error (Snake game):", err);
    });

    console.log("Snake game script loaded. Events bound.");
});
