document.addEventListener('DOMContentLoaded', () => {
    const gameCards = document.querySelectorAll('.game-card');
    gameCards.forEach(card => {
        card.addEventListener('click', () => {
            const gameType = card.getAttribute('data-game');
            let gameUrl = '';
            switch (gameType) {
                case 'tank':
                    gameUrl = '/tank_game_page'; // Actual page for the tank game
                    break;
                case 'snake':
                    gameUrl = '/snake_game_page';
                    break;
                case 'memory':
                    gameUrl = '/memory_game_page';
                    break;
                case 'hangman':
                    gameUrl = '/hangman_game_page';
                    break;
                case 'gobang':
                    gameUrl = '/gobang_game_page';
                    break;
                default:
                    console.error('Unknown game type:', gameType);
                    return;
            }
            window.location.href = gameUrl;
        });
    });
});
