# Mineko’s Pixel Adventure

**Mineko’s Pixel Adventure** is a Telegram bot game where players guide Mineko, a pixel cat, through a Minesweeper-inspired 8x8 grid to uncover pixel gems while avoiding 18 hidden "Boomlings" (mines). Built with Python and integrated with the Solana blockchain, the game features engaging gameplay, a referral program, and wallet management. Below is a brief overview of the game’s core functionalities.

## Game Features

### Core Gameplay
- **Objective**: Navigate an 8x8 grid to reveal all safe tiles while avoiding 18 Boomlings.
- **Mechanics**:
  - Tap a paw print (`🐾`) to flag (`📍`) a suspected Boomling.
  - Tap again to reveal tiles: numbers indicate nearby Boomlings, blanks clear safe areas, and Boomlings (`💣`) end the game.
  - Clear all safe tiles to win 50% of the Solana (SOL) and Mineko token jackpot.
- **Entry Fee**: 0.05 SOL per game
- **Interaction**: Players use Telegram inline buttons for a seamless experience, with image-based menus for the start screen and instructions.

### Referral Program
- **How It Works**: Players can share a unique referral link (e.g., `https://t.me/MinekoSolBot?start={user_id}`) to invite others.
- **Rewards**: Earn 10% of each referral’s entry fee in SOL, tracked and credited automatically.
- **Tracking**: View referral count and earned SOL rewards via the "Referral" menu.
- **Implementation**: Referrals are stored in a database, and rewards are sent to the referrer’s Solana wallet after each referred player’s entry.

### Wallet Management
- **Solana Wallet**:
  - New players receive a generated Solana wallet, or they can import an existing one using a private key.
  - Wallet balances (SOL and Mineko tokens) are displayed in the start menu.
- **Private Key Access**: Players can view their Solana private key (displayed briefly and auto-deleted for security).
- **Import Wallet**: Import an existing Solana wallet by providing a private key, validated for correct format.

### Blockchain Integration
- **Solana Transactions**: Entry fees and payouts are processed on the Solana blockchain, with transactions for SOL and Mineko tokens.
- **Jackpot**: The jackpot accumulates from entry fees, with winners receiving 50% of the SOL and Mineko token pools.
- **Balance Checks**: Real-time balance queries for player and jackpot wallets, displayed in the game interface.

### Additional Features
- **Dynamic Configuration**: Game settings (grid size, mine count, jackpot share) are loaded from a `config.json` file, reloaded every 60 seconds.
- **Cooldown System**: Prevents spamming of the `/start` command with a 3-second minimum cooldown, increasing up to 30 seconds for repeated attempts.
- **Error Handling**: Robust handling for Telegram API errors (e.g., message deletion retries) and payment processing issues.
- **How to Play**: A detailed guide with an image, accessible via the "How to Play?" button, explains gameplay and referral benefits.

## Notes
- This code includes a referral system and database operations for tracking users, wallets, and rewards.
- Sensitive operations (e.g., private key management, payments) should be secured in a production environment.
- The game is designed for private Telegram chats to ensure user privacy and security.

---
*Mineko’s Pixel Adventure combines classic Minesweeper fun with blockchain rewards and social incentives, making it an engaging experience for Telegram users.*
