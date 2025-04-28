import os
import math
import time
import random
import asyncio
import logging
import aiomysql
import warnings
import threading
import json
import aiofiles
import datetime
from balance import get_balance
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
import telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext, ContextTypes
from telegram.error import TimedOut, BadRequest
from transfer import send_sol, send_sol_e
from spl_balance import get_solana_token_amount
from sendSPL import send_spl

warnings.simplefilter("ignore")
load_dotenv('.env')
logging.basicConfig(level=logging.ERROR)

# Load environment variables
TOKEN = {{ENV_VAR}}
CHANNELID = {{ENV_VAR}}

# Blockchain configurations
SOLANA_RPC_URL = {{ENV_VAR}}
solana_client = AsyncClient(SOLANA_RPC_URL)

# Jackpot wallets
JACKPOT_SOLANA = {{PAYMENT_INFO}}

# Config file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
config = {}

# Telegram bot initialization
bot = Bot(token=TOKEN)

user_last_start_time = {}
START_COMMAND_COOLDOWN = 3
MAX_START_COMMAND_COOLDOWN = 30
user_spam_count = {}
user_notified = {}

GAME_MODES = {
    "mineko": {"grid_size": 8, "mines": 15}
}

async def load_config():
    """Load or reload the config from config.json."""
    global config
    try:
        async with aiofiles.open(CONFIG_FILE, 'r') as f:
            config = json.loads(await f.read())
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        config = {
            "conversion_rates": {"usd_to_sol": 130},
            "entry_fee_usd": 5,
            "jackpot_share": 0.8,
            "team_share": 0.2
        }

async def config_reload_task():
    """Periodically reload the config file."""
    while True:
        await load_config()
        await asyncio.sleep(60)

async def setup_database():
    """Set up the database."""
    {{DB_OPERATION}}

async def private_chat_only(update: Update, context: CallbackContext):
    return update.effective_chat.type == 'private'

async def create_start_task(update: Update, context: CallbackContext) -> None:
    if not await private_chat_only(update, context):
        return

    user_id = update.effective_user.id
    current_time = time.time()

    if user_id in user_last_start_time and (current_time - user_last_start_time[user_id]) < START_COMMAND_COOLDOWN:
        user_spam_count[user_id] = user_spam_count.get(user_id, 0) + 1
        cooldown_time = min(START_COMMAND_COOLDOWN + (user_spam_count[user_id] * 3), MAX_START_COMMAND_COOLDOWN)
        if user_id not in user_notified:
            user_notified[user_id] = True
            await update.message.reply_text(f"Please wait {cooldown_time} seconds before trying again.")
        return
    else:
        user_spam_count[user_id] = 0
        user_notified[user_id] = False

    user_last_start_time[user_id] = current_time
    asyncio.create_task(start(update, context, user_id))

async def start(update: Update, context: Application, user_id: int = None) -> None:
    if not await private_chat_only(update, context):
        return

    user_id = user_id or update.effective_user.id

    await asyncio.sleep(2.5)

    solana_wallet = {{DB_OPERATION}}
    if not solana_wallet:
        solana_wallet = {{PAYMENT_INFO}}
        {{DB_OPERATION}}

    sol_balance = await asyncio.shield(get_balance(solana_wallet))
    sol_formatted = f"{math.floor(sol_balance * 1000) / 1000:.3f}"
    spl_balance = await asyncio.shield(get_solana_token_amount(solana_wallet))
    spl_formatted = f"{math.floor(spl_balance * 1000) / 1000:.1f}"
    entry_fee = 0.05
    jackpot_share = config.get('jackpot_share', 0.8)
    team_share = config.get('team_share', 0.2)
    jackpot_wallet = JACKPOT_SOLANA
    jackpot_balance = await get_balance(jackpot_wallet)
    jackpot_balance_formatted = f"{math.floor(jackpot_balance * 1000*0.5) / 1000:.3f}"
    jackpot_balance_mines = await get_solana_token_amount(jackpot_wallet)
    jackpot_balance_mines_formatted = f"{math.floor(jackpot_balance_mines * 1000*0.5) / 1000:.1f}"

    welcome_message = (
        f"😺 *Mineko’s Pixel Adventure!* 😺\n\n"
        f"Meet Mineko, a pixel cat prowling a glitching 8x8 grid in a forgotten digital realm. Hidden beneath are 20 *Boomlings*—sneaky bombs planted by rogue code! Help her paw through the tiles to uncover pixel gems.\n\n"
        f"🎮 *How It Works:*\n"
        f"• Tap a paw print (🐾) to flag (📍) a suspected Boomling\n"
        f"• Tap again to reveal: numbers hint at nearby Boomlings, blanks clear safe tiles\n"
        f"• Clear all safe tiles to win big!\n\n"
        f"*•••••• Sol Jackpot: {jackpot_balance_formatted} Sol*\n"
        f"*••• Token Jackpot: {jackpot_balance_mines_formatted} Mines*\n\n"
        f"💰 *Your Balance:*\n"
        f"• *SOL:* {sol_formatted} \n"
        f"• *MINES:* {spl_formatted} \n"
        f"• *Solana:* `{solana_wallet}`\n\n"
        f"✨ *Join for {entry_fee} SOL ({jackpot_share*100}% to jackpot)*"
    )

    keyboard = [
        [InlineKeyboardButton("Play with SOL 💣 ", callback_data='mineko_mode_sol')],
        [InlineKeyboardButton("BNB Coming Soon", callback_data='bnb_coming_soon')],
        [InlineKeyboardButton("SUI Coming Soon", callback_data='sui_coming_soon')],
        [InlineKeyboardButton("How to Play?", callback_data='info'), InlineKeyboardButton("Wallet", callback_data='wallet')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    image_path = os.path.join(os.path.dirname(__file__), 'start_menu.jpg')

    try:
        if update.message:
            with open(image_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=welcome_message,
                    reply_markup=reply_markup,
                    parse_mode="markdown"
                )
        elif update.callback_query:
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=welcome_message,
                    reply_markup=reply_markup,
                    parse_mode="markdown"
                )
        else:
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=welcome_message,
                    reply_markup=reply_markup,
                    parse_mode="markdown"
                )
    except FileNotFoundError:
        logging.error(f"Image file {image_path} not found.")
        if update.message:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="markdown")
        elif update.callback_query:
            await context.bot.send_message(chat_id=user_id, text=welcome_message, reply_markup=reply_markup, parse_mode="markdown")
        else:
            await context.bot.send_message(chat_id=user_id, text=welcome_message, reply_markup=reply_markup, parse_mode="markdown")

async def create_grid(size=8, mines=5):
    """Create a Mineko grid with Boomlings."""
    grid = [[0 for _ in range(size)] for _ in range(size)]
    mine_positions = set()
    
    while len(mine_positions) < mines:
        x = random.randint(0, size-1)
        y = random.randint(0, size-1)
        if (x, y) not in mine_positions:
            mine_positions.add((x, y))
            grid[x][y] = '💣'
    
    for mine_x, mine_y in mine_positions:
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_x, new_y = mine_x + dx, mine_y + dy
                if (0 <= new_x < size and 0 <= new_y < size and 
                    grid[new_x][new_y] != '💣'):
                    grid[new_x][new_y] += 1
    
    display_grid = [['🐾' for _ in range(size)] for _ in range(size)]
    return grid, display_grid, mine_positions

async def build_keyboard(display_grid, user_id, game_over=False):
    """Build the Mineko game keyboard with fixed-width buttons."""
    keyboard = []
    for i in range(len(display_grid)):
        row = []
        for j in range(len(display_grid[0])):
            button_text = display_grid[i][j]
            if button_text == 0:
                button_text = ' '
            button_text = str(button_text)
            padded_text = button_text + '\u200B' * (3 - len(button_text))
            callback_data = "noop" if game_over else f"mineko_{user_id},{i},{j}" if display_grid[i][j] in ['🐾', '📍'] else "noop"
            row.append(InlineKeyboardButton(padded_text, callback_data=callback_data))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def button(update: Update, context: Application) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    async def handle_query():
        if query.data == 'info':
            entry_fee_usd = config.get('entry_fee_usd', 5)
            jackpot_share = config.get('jackpot_share', 0.8)
            team_share = config.get('team_share', 0.2)

            for attempt in range(3):
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                    break
                except (TimedOut, BadRequest) as e:
                    logging.warning(f"Attempt {attempt + 1} to delete start menu failed: {e}")
                    if attempt == 2:
                        logging.error(f"Failed to delete start menu after 3 attempts.")
                    await asyncio.sleep(1)

            how_to_play_message = (
                f"😺 *Mineko’s Guide to Boomling Hunting* 😺\n\n"
                f"In a pixelated realm, Mineko’s tail twitches as she prowls an 8x8 grid hiding 20 *Boomlings*—glitchy bombs left by rogue code. One wrong paw means BOOM!\n\n"
                f"1. *Tap a paw print* (🐾) to flag (📍) a tile Mineko sniffs as a Boomling\n"
                f"2. *Tap again* to reveal:\n"
                f"   - *Numbers (1-8)*: Boomlings lurking nearby\n"
                f"   - *Blank*: Safe tile, clears more safe spots\n"
                f"   - *💣 Boomling*: Oh no, Mineko’s in trouble!\n"
                f"3. *Goal*: Clear all safe tiles to snag pixel gems and win!\n"
                f"4. *Entry*: ${entry_fee_usd} ({jackpot_share*100}% to jackpot, {team_share*100}% to team)\n"
                f"5. *Win*: Grab 50% of the jackpot wallet!\n\n"
                f"Guide Mineko’s paws to outsmart the Boomlings!"
            )
            image_path = os.path.join(os.path.dirname(__file__), 'how_to_play.jpg')

            try:
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=how_to_play_message,
                        parse_mode='Markdown'
                    )
            except FileNotFoundError:
                logging.error(f"Image file {image_path} not found.")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=how_to_play_message,
                    parse_mode='Markdown'
                )

            await asyncio.sleep(3)
            await context.bot.send_message(
                chat_id=user_id,
                text="😺 Mineko’s ready to pounce again!",
                parse_mode='Markdown'
            )
            await start(update, context, user_id=user_id)

        elif query.data == 'mineko_mode_sol':
            solana_wallet = {{DB_OPERATION}}
            entry_fee = 0.05
            jackpot_share = config.get('jackpot_share', 0.8)
            team_share = config.get('team_share', 0.2)

            for attempt in range(3):
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                    break
                except (TimedOut, BadRequest) as e:
                    logging.warning(f"Attempt {attempt + 1} to delete initial message failed: {e}")
                    if attempt == 2:
                        logging.error(f"Failed to delete initial message after 3 attempts.")
                    await asyncio.sleep(1)

            processing_message = await context.bot.send_message(
                chat_id=user_id,
                text="😺 Mineko’s preparing the grid, please wait...\n\n(This may take up to 15 seconds. Do not start a new game else you will forfeit your current entry)"
            )

            try:
                balance = await get_balance(solana_wallet)
                if balance < entry_fee:
                    await context.bot.delete_message(
                        chat_id=processing_message.chat_id,
                        message_id=processing_message.message_id
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Insufficient SOL balance ({balance:.3f} SOL). Need {entry_fee:.3f} SOL."
                    )
                    return
                jackpot_result = {{PAYMENT_OPERATION}}
                
                if not jackpot_result["success"]:
                    await context.bot.delete_message(
                        chat_id=processing_message.chat_id,
                        message_id=processing_message.message_id
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Failed to send SOL to jackpot: {jackpot_result['error']}"
                    )
                    return

                await context.bot.delete_message(
                    chat_id=processing_message.chat_id,
                    message_id=processing_message.message_id
                )

                config_mode = GAME_MODES["mineko"]
                grid, display_grid, mine_positions = await create_grid(config_mode["grid_size"], config_mode["mines"])
                context.user_data['mineko_grid'] = grid
                context.user_data['mineko_display'] = display_grid
                context.user_data['mineko_mines'] = mine_positions
                context.user_data['mineko_revealed'] = 0
                context.user_data['chain'] = 'sol'

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"😺 *Mineko’s Adventure Begins!* 😺\n\n8x8 grid with 20 Boomlings\nTap a paw print (🐾) to flag, tap again to reveal!\nPaid {entry_fee} SOL",
                    reply_markup=await build_keyboard(display_grid, user_id),
                    parse_mode='Markdown'
                )

            except Exception as e:
                await context.bot.delete_message(
                    chat_id=processing_message.chat_id,
                    message_id=processing_message.message_id
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"An error occurred during payment processing: {str(e)}"
                )
                logging.error(f"Payment processing error: {e}")

        elif query##

        elif query.data in ['bnb_coming_soon', 'sui_coming_soon']:
            await query.answer(text="This feature is coming soon!", show_alert=True)

        elif query.data.startswith('mineko_'):
            config_mode = GAME_MODES["mineko"]
            _, coords = query.data.split('_', 1)
            row, col = map(int, coords.split(',')[1:])
            
            grid = context.user_data.get('mineko_grid')
            display_grid = context.user_data.get('mineko_display')
            mine_positions = context.user_data.get('mineko_mines')
            revealed = context.user_data.get('mineko_revealed', 0)
            chain = context.user_data.get('chain')

            if not all([grid, display_grid, mine_positions, chain]):
                await query.edit_message_text("Game not found! Use /start to begin.")
                await start(update, context, user_id=user_id)
                return

            if display_grid[row][col] == '🐾':
                display_grid[row][col] = '📍'
                await query.edit_message_text(
                    text=f"😺 *Mineko’s tail twitches!* 😺\n\n8x8 grid with 20 Boomlings\nFlagged a tile! Tap again to reveal.\n\n😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺",
                    reply_markup=await-build_keyboard(display_grid, user_id),
                    parse_mode='Markdown'
                )
                return
            elif display_grid[row][col] != '📍':
                return

            if (row, col) in mine_positions:
                for mine_x, mine_y in mine_positions:
                    display_grid[mine_x][mine_y] = '💣'
                await query.edit_message_text(
                    f"💣 *Meow!* Mineko pawed a Boomling!\nGame Over!\n\n😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿😿",
                    reply_markup=await build_keyboard(display_grid, user_id, game_over=True),
                    parse_mode='Markdown'
                )
                context.user_data.clear()
                await start(update, context, user_id=user_id)

            def reveal_tiles(x, y):
                if (not 0 <= x < config_mode["grid_size"] or 
                    not 0 <= y < config_mode["grid_size"] or 
                    display_grid[x][y] not in ['🐾', '📍']):
                    return
                
                display_grid[x][y] = ' ' if grid[x][y] == 0 else str(grid[x][y])
                nonlocal revealed
                revealed += 1
                
                if grid[x][y] == 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            reveal_tiles(x + dx, y + dy)

            reveal_tiles(row, col)
            context.user_data['mineko_revealed'] = revealed
            total_safe = config_mode["grid_size"] * config_mode["grid_size"] - config_mode["mines"]

            if revealed >= total_safe:
                solana_wallet = {{DB_OPERATION}}
                jackpot_balance = await get_balance(JACKPOT_SOLANA)
                jackpot_spl_balance = await get_solana_token_amount(JACKPOT_SOLANA)
                payout = jackpot_balance * 0.5
                payout_spl = jackpot_spl_balance * 0.5

                message = f"🎉 *Purr-fect!* Mineko cleared the grid and snagged the gems!\nPayout: {payout:.3f} SOL + {payout_spl:.3f} MINES from jackpot!\n\n😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻😻"

                await query.edit_message_text(
                    message,
                    reply_markup=await build_keyboard(display_grid, user_id, game_over=True),
                    parse_mode='Markdown'
                )
                context.user_data.clear()
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"Processing prize(s): {payout:.3f} SOL + {payout_spl:.1f} MINES:\n\nPlease wait...",
                    parse_mode='Markdown'
                )
                payout_result = {{PAYMENT_OPERATION}}
                payout_spl_result = {{PAYMENT_OPERATION}}
                if payout_result["success"] and payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL + {payout_spl} MINES\n\n[TX1](https://solscan.io/tx/{{TX_ID}}) [TX2](https://solscan.io/tx/{{TX_ID}})",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                elif payout_result["success"] and not payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL but {payout_spl} MINES not paid. Please contact support\n\n[TX1](https://solscan.io/tx/{{TX_ID}})",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                elif not payout_result["success"] and payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL not paid but {payout_spl} MINES paid. Please contact support\n\n[TX2](https://solscan.io/tx/{{TX_ID}})",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout failed: {{ERROR}}",
                        parse_mode='Markdown'
                    )

                await start(update, context, user_id=user_id)
            else:
                await query.edit_message_text(
                    text=f"😺 *Mineko purrs!* 😺\n\n8x8 grid with 20 Boomlings\nRevealed a tile! Keep going!\n\n😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼",
                    reply_markup=await build_keyboard(display_grid, user_id),
                    parse_mode='Markdown'
                )

        elif query.data == 'wallet':
            for attempt in range(3):
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                    break
                except (TimedOut, BadRequest) as e:
                    logging.warning(f"Attempt {attempt + 1} to delete start menu failed: {e}")
                    if attempt == 2:
                        logging.error(f"Failed to delete start menu after 3 attempts.")
                    await asyncio.sleep(1)

            keyboard = [
                [InlineKeyboardButton("Solana Secret Key", callback_data='secret_key_sol')],
                [InlineKeyboardButton("Import Wallet", callback_data='import_wallet')],
                [InlineKeyboardButton("Cancel", callback_data='cancel_button')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id,
                text="😺 *Mineko’s Wallet Options* 😺\n\nChoose an action for your Solana wallet:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif query.data == 'secret_key_sol':
            await query.edit_message_text("Private key retrieval disabled.")
            await start(update, context, user_id=user_id)

        elif query.data == 'import_wallet':
            for attempt in range(3):
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                    break
                except (TimedOut, BadRequest) as e:
                    logging.warning(f"Attempt {attempt + 1} to delete wallet menu failed: {e}")
                    if attempt == 2:
                        logging.error(f"Failed to delete wallet menu after 3 attempts.")
                    await asyncio.sleep(1)

            keyboard = [
                [InlineKeyboardButton("Solana", callback_data='import_solana')],
                [InlineKeyboardButton("Cancel", callback_data='cancel_button')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id,
                text="😺 *Mineko’s Wallet Import* 😺\n\nWhich wallet would you like to import?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif query.data == 'import_solana':
            await query.edit_message_text("Please reply with your Solana private key to import your wallet")
            handler = MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda update, context: import_wallet(update, context, user_id, handler, "solana")
            )
            context.application.add_handler(handler)

        elif query.data == 'cancel_button':
            for attempt in range(3):
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                    break
                except (TimedOut, BadRequest) as e:
                    logging.warning(f"Attempt {attempt + 1} to delete menu failed: {e}")
                    if attempt == 2:
                        logging.error(f"Failed to delete menu after 3 attempts.")
                    await asyncio.sleep(1)
            await start(update, context, user_id=user_id)

    asyncio.create_task(handle_query())

async def import_wallet(update: Update, context: Application, user_id: int, handler: MessageHandler, chain: str) -> None:
    if update.message.chat.type != "private" or update.message.from_user.id != user_id:
        return

    private_key = update.message.text.strip()
    try:
        if chain == "solana":
            wallet_address = {{PAYMENT_INFO}}
            {{DB_OPERATION}}
            await update.message.reply_text(f"Your Solana wallet {wallet_address} has been successfully imported!")
    except ValueError:
        await update.message.reply_text(f"Invalid {chain.upper()} private key format.")
        return

    try:
        await context.bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete message: {e}")

    context.application.remove_handler(handler)
    await start(update, context)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", create_start_task))
    application.add_handler(CallbackQueryHandler(button))
    threading.Thread(target=async_init, daemon=True).start()
    asyncio.ensure_future(load_config())
    asyncio.ensure_future(config_reload_task())
    print("Polling")
    application.run_polling()

def async_init():
    print("DB Setup")
    asyncio.run(setup_database())

if __name__ == '__main__':
    main()