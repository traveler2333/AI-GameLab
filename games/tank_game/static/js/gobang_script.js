document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const canvas = document.getElementById('gobangCanvas');
    const ctx = canvas.getContext('2d');
    const gameStatusDisplay = document.getElementById('gobangGameStatus');
    const restartButton = document.getElementById('gobangRestartButton');

    const BOARD_SIZE = 15; // Standard Gobang board size
    let CELL_SIZE = 30;   // Default, will be adjusted
    let boardData = [];   // Store the board matrix

    function setupCanvas() {
        const containerWidth = document.getElementById('gobangBoardContainer').offsetWidth;
        CELL_SIZE = Math.floor(containerWidth / (BOARD_SIZE)); // Adjust cell size to fit container
        canvas.width = CELL_SIZE * BOARD_SIZE;
        canvas.height = CELL_SIZE * BOARD_SIZE;
    }

    function drawBoardLines() {
        ctx.strokeStyle = '#543A1C'; // Darker lines for wood board
        ctx.lineWidth = 1;
        for (let i = 0; i < BOARD_SIZE + 1; i++) {
            // Draw vertical lines
            ctx.beginPath();
            ctx.moveTo(i * CELL_SIZE + CELL_SIZE/2, CELL_SIZE/2);
            ctx.lineTo(i * CELL_SIZE + CELL_SIZE/2, canvas.height - CELL_SIZE/2);
            ctx.stroke();
            // Draw horizontal lines
            ctx.beginPath();
            ctx.moveTo(CELL_SIZE/2, i * CELL_SIZE + CELL_SIZE/2);
            ctx.lineTo(canvas.width - CELL_SIZE/2, i * CELL_SIZE + CELL_SIZE/2);
            ctx.stroke();
        }

        // Star points (optional, for traditional look)
        const starPoints = [
            (3, 3), (11, 3), (3, 11), (11, 11), (7, 7) // For 15x15
        ];
         if (BOARD_SIZE === 15) { // Only for 15x15
            ctx.fillStyle = '#543A1C';
            starPoints.forEach(([r,c]) => {
                ctx.beginPath();
                ctx.arc(c * CELL_SIZE + CELL_SIZE/2, r * CELL_SIZE + CELL_SIZE/2, CELL_SIZE/6, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
    }

    function drawStone(row, col, player) {
        if (player === 0) return; // No stone
        const stoneRadius = CELL_SIZE / 2 * 0.85; // Make stones slightly smaller than cell
        const x = col * CELL_SIZE + CELL_SIZE / 2;
        const y = row * CELL_SIZE + CELL_SIZE / 2;

        ctx.beginPath();
        ctx.arc(x, y, stoneRadius, 0, 2 * Math.PI);
        ctx.fillStyle = (player === 1) ? 'black' : 'white';
        ctx.fill();
        // Optional: add a slight border to white stones for visibility
        if (player === 2) {
            ctx.strokeStyle = '#bbb';
            ctx.lineWidth = 0.5;
            ctx.stroke();
        }
    }

    function renderFullBoard(matrix) {
        if(!matrix || matrix.length === 0) return;
        boardData = matrix; // Store for click handling
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawBoardLines();
        for (let r = 0; r < BOARD_SIZE; r++) {
            for (let c = 0; c < BOARD_SIZE; c++) {
                drawStone(r, c, matrix[r][c]);
            }
        }
    }

    function updateGameDisplay(gameState) {
        if (!gameState) {
            console.error('Invalid gameState received for Gobang');
            return;
        }
        renderFullBoard(gameState.board);
        gameStatusDisplay.textContent = gameState.status_message || ' ';

        if (gameState.is_game_over || !gameState.is_player_turn) {
            canvas.style.cursor = 'default';
        } else {
            canvas.style.cursor = 'pointer';
        }
    }

    canvas.addEventListener('click', (event) => {
        if (!boardData || boardData.length === 0) return; // Board not ready

        // Check if it's player's turn from the last received game state
        // This is a client-side check; server will ultimately validate
        const currentStatusText = gameStatusDisplay.textContent;
        if (currentStatusText.includes("AI思考中") || currentStatusText.includes("获胜") || currentStatusText.includes("平局")) {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Calculate row and col based on click position, ensuring it's near an intersection
        const col = Math.floor(x / CELL_SIZE);
        const row = Math.floor(y / CELL_SIZE);

        // Validate click is on an intersection and cell is empty
        if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE) {
            if (boardData[row][col] === 0) {
                 console.log(`Player attempts move at: ${row}, ${col}`);
                 socket.emit('gobang_player_move', { row: row, col: col });
            } else {
                console.log("Cell already occupied.");
            }
        }
    });

    socket.on('gobang_update_state', updateGameDisplay);

    restartButton.addEventListener('click', () => {
        socket.emit('gobang_start_game');
    });

    socket.on('connect', () => {
        console.log('Connected to server for Gobang game.');
        setupCanvas(); // Setup canvas dimensions based on container
        socket.emit('gobang_start_game');
    });

    window.addEventListener('resize', () => {
        setupCanvas();
        // Request a state update to redraw board with new dimensions if needed
        // However, this might be complex if game state is not immediately available
        // For now, just re-render with existing data if available
        if (boardData && boardData.length > 0) {
            renderFullBoard(boardData);
        }
    });

    socket.on('disconnect', () => { gameStatusDisplay.textContent = "连接已断开"; });
    socket.on('connect_error', (err) => { gameStatusDisplay.textContent = "连接错误"; console.error("Connection error (Gobang game):", err);});

    console.log("Gobang game script loaded.");
});
