document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const gameBoardDiv = document.getElementById('memoryGameBoard');
    const movesSpan = document.getElementById('memoryMoves');
    const restartButton = document.getElementById('memoryRestartButton');

    // SYMBOLS are sent by server as part of boardData, no need to define here.
    // GRID_SIZE might also be inferred from boardData.length or sent by server.

    function renderBoard(boardData) {
        if (!boardData || !Array.isArray(boardData.cards)) {
            console.error('Invalid board data received:', boardData);
            gameBoardDiv.innerHTML = '<p>Error loading game board.</p>';
            return;
        }

        gameBoardDiv.innerHTML = ''; // Clear previous board

        // Determine grid columns (e.g. 4 for 16 cards, 5 for 20/25 cards)
        const numCards = boardData.cards.length;
        let columns = 4; // Default
        if (numCards === 20) columns = 5;
        else if (numCards === 24 || numCards === 30) columns = 6; // Example for larger boards
        // Adjust grid style dynamically if needed, or ensure CSS supports it
        // gameBoardDiv.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;


        boardData.cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.classList.add('card');
            cardDiv.dataset.id = card.id;

            const cardContent = document.createElement('div');
            cardContent.classList.add('card-content');
            cardContent.textContent = card.symbol;

            if (card.is_flipped || card.is_matched) {
                cardDiv.classList.add('flipped');
                cardContent.style.display = 'block';
            } else {
                cardContent.style.display = 'none';
            }

            if (card.is_matched) {
                cardDiv.classList.add('matched');
            }

            cardDiv.appendChild(cardContent);

            // Add click listener only if card is not matched and board is not locked
            // (server-side 'lock_board' prevents backend logic, this is for UI)
            if (!card.is_matched && !boardData.lock_board) {
                cardDiv.addEventListener('click', () => {
                    // Only allow flipping if it's not already part of the currently selected pair
                    // or if it's not already matched. Server handles ultimate truth.
                    if (!cardDiv.classList.contains('flipped') || boardData.flipped_indices.length < 2) {
                         socket.emit('memory_flip_card', { card_id: card.id });
                    }
                });
            } else if (boardData.lock_board && !card.is_matched && !card.is_flipped) {
                // If board is locked, non-flipped, non-matched cards should not be clickable temporarily
                cardDiv.style.cursor = 'default';
            }


            gameBoardDiv.appendChild(cardDiv);
        });
    }

    socket.on('memory_update_state', (gameState) => {
        if (gameState && gameState.board) {
            renderBoard(gameState.board); // Pass the board part of the state which includes cards and lock_board
            movesSpan.textContent = gameState.moves || 0;
            if (gameState.is_over && gameState.matches_found * 2 === gameState.board.cards.length) {
                // Small delay to allow last match to show before alert
                setTimeout(() => {
                    alert('恭喜！你已完成所有匹配！ (Congratulations! You matched all pairs!)');
                }, 600); // After flip animation
            }
        } else {
            console.error('Received invalid game state for memory game:', gameState);
        }
    });

    restartButton.addEventListener('click', () => {
        socket.emit('memory_start_game');
    });

    socket.on('connect', () => {
        console.log('Connected to server for Memory game.');
        socket.emit('memory_start_game'); // Initialize game on connection
    });

    socket.on('disconnect', () => {
        console.log("Disconnected from server (Memory game).");
    });
    socket.on('connect_error', (err) => {
        console.error("Connection error (Memory game):", err);
    });
    console.log("Memory game script loaded.");
});
