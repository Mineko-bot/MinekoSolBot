import os
import math
import time
import random
import asyncio
import logging
import aiofiles
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext, ContextTypes
from telegram.error import TimedOut, BadRequest

logging.basicConfig(level=logging.ERROR)
load_dotenv('.env')

TOKEN = os.getenv('TOKEN', '{{ENV_VAR}}')
CHANNELID = int(os.getenv('TG_CHANNEL_ID', '{{ENV_VAR}}'))

SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.devnet.solana.com')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
config = {}

bot = Bot(token=TOKEN)

user_last_start_time = {}
START_COMMAND_COOLDOWN = 3
MAX_START_COMMAND_COOLDOWN = 30
user_spam_count = {}
user_notified = {}

async def load_config():
    global config
    try:
        async with aiofiles.open(CONFIG_FILE, 'r') as f:
            config = json.loads(await f.read())
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        config = {
            "jackpot_share": 0.8,
            "team_share": 0.2,
            "game_modes": {
                "mineko": {
                    "grid_size": 8,
                    "mines": 18
                }
            }
        }

async def config_reload_task():
    while True:
        await load_config()
        await asyncio.sleep(60)

async def setup_database():
    {{DB_OPERATION}}

async def private_chat_only(update: Update, context: CallbackContext):
    return update.effective_chat.type == 'private'

async def increment_referral_count(referrer_id):
    {{DB_OPERATION}}

async def get_referral_info(user_id):
    {{DB_OPERATION}}
    return 0, 0.0

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
    await asyncio.sleep(2)
    referrer_id = context.args[0] if context.args else None

    solana_wallet = '{{DB_OPERATION}}'
    if not solana_wallet:
        solana_wallet = 'mock_solana_wallet_address'
        {{DB_OPERATION}}
        if referrer_id:
            try:
                referrer_id_int = int(referrer_id)
                {{DB_OPERATION}}
                if False:
                    referrer_id_int = None
            except ValueError:
                referrer_id_int = None
            if referrer_id_int:
                await increment_referral_count(referrer_id_int)

    sol_balance = 0.0
    sol_formatted = f"{math.floor(sol_balance * 1000) / 1000:.3f}"
    spl_balance = 0.0
    spl_formatted = f"{math.floor(spl_balance * 1000) / 1000:.1f}"
    entry_fee = 0.05
    jackpot_share = config.get('jackpot_share', 0.8)
    team_share = config.get('team_share', 0.2)
    jackpot_wallet = '{{ENV_VAR}}'
    jackpot_balance = 0.0
    jackpot_balance_formatted = f"{math.floor(jackpot_balance * 1000*0.5) / 1000:.3f}"
    jackpot_balance_mines = 0.0
    jackpot_balance_mines_formatted = f"{math.floor(jackpot_balance_mines * 1000*0.5) / 1000:.1f}"

    welcome_message = (
        f"😺 *Mineko’s Pixel Adventure!* 😺\n\n"
        f"Meet Mineko, a pixel cat prowling a glitching {config['game_modes']['mineko']['grid_size']}x{config['game_modes']['mineko']['grid_size']} grid in a forgotten digital realm. Hidden beneath are {config['game_modes']['mineko']['mines']} * *Boomlings*—sneaky bombs planted by rogue code! Help her paw through the tiles to uncover pixel gems.\n\n"
        f"🎮 *How It Works:*\n"
        f"• Tap a paw print (🐾) to flag (📍) a suspected Boomling\n"
        f"• Tap again to reveal: numbers hint at nearby Boomlings, blanks clear safe tiles\n"
        f"• Clear all safe tiles to win big!\n\n"
        f"*•••••• Sol Jackpot: {jackpot_balance_formatted} Sol*\n"
        f"*••• Token Jackpot: {jackpot_balance_mines_formatted} Mineko*\n\n"
        f"💰 *Your Balance:*\n"
        f"• *SOL:* {sol_formatted} \n"
        f"• *MINEKO:* {spl_formatted} \n"
        f"• *Wallet:* `mock_wallet_address`\n\n"
        f"*CA:* ``\n"
        f"✨ *Join for {entry_fee} SOL ({jackpot_share*100}% to jackpot)*"
    )

    keyboard = [
        [InlineKeyboardButton("Play with SOL 💣 ", callback_data='mineko_mode_sol')],
        [InlineKeyboardButton("BNB/SUI Coming Soon", callback_data='bnb_coming_soon')],
        [InlineKeyboardButton("How to Play?", callback_data='info'), InlineKeyboardButton("Wallet", callback_data='wallet')],
        [InlineKeyboardButton("Referral", callback_data='refer')],
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

async def create_grid(size=None, mines=None):
    size = size or config['game_modes']['mineko']['grid_size']
    mines = mines or config['game_modes']['mineko']['mines']
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
                f"In a pixelated realm, Mineko’s tail twitches as she prowls an {config['game_modes']['mineko']['grid_size']}x{config['game_modes']['mineko']['grid_size']} grid hiding {config['game_modes']['mineko']['mines']} *Boomlings*—glitchy bombs left by rogue code. One wrong paw means BOOM!\n\n"
                f"1. *Tap a paw print* (🐾) to flag (📍) a tile Mineko sniffs as a Boomling\n"
                f"2. *Tap again* to reveal:\n"
                f"   - *Numbers (1-8)*: Boomlings lurking nearby\n"
                f"   - *Blank*: Safe tile, clears more safe spots\n"
                f"   - *💣 Boomling*: Oh no, Mineko’s in trouble!\n"
                f"3. *Goal*: Clear all safe tiles to snag pixel gems and win!\n"
                f"4. *Entry*: 0.05 SOL\n"
                f"5. *Win*: The displayed jackpot wallet amounts!(50% of total wallet balances)\n\n"
                f"*Referrals:*\n"
                f"• Earn 10% of your referrals’ entry fees in SOL\n\n"
                f"Guide Mineko’s paws to outsmart the Boomlings!\n"
                f"*NOTE:* Mineko is an extremely difficult game to win."
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
            solana_wallet = '{{DB_OPERATION}}'
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
                balance = 0.0
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

                {{DB_OPERATION}}
                payment_result = {'success': True, 'result': 'mock_tx_id', 'error': None}
                if not payment_result["success"]:
                    await context.bot.delete_message(
                        chat_id=processing_message.chat_id,
                        message_id=processing_message.message_id
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Failed to send SOL to jackpot: {payment_result['error']}"
                    )
                    return

                await context.bot.delete_message(
                    chat_id=processing_message.chat_id,
                    message_id=processing_message.message_id
                )

                grid, display_grid, mine_positions = await create_grid()
                context.user_data['mineko_grid'] = grid
                context.user_data['mineko_display'] = display_grid
                context.user_data['mineko_mines'] = mine_positions
                context.user_data['mineko_revealed'] = 0
                context.user_data['chain'] = 'sol'

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"😺 *Mineko’s Adventure Begins!* 😺\n\n{config['game_modes']['mineko']['grid_size']}x{config['game_modes']['mineko']['grid_size']} grid with {config['game_modes']['mineko']['mines']} Boomlings\nTap a paw print (🐾) to flag, tap again to reveal!\nPaid {entry_fee} SOL",
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

        elif query.data in ['bnb_coming_soon', 'sui_coming_soon']:
            await query.answer(text="This feature is coming soon!", show_alert=True)

        elif query.data.startswith('mineko_'):
            config_mode = config['game_modes']['mineko']
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
                    text=f"😺 *Mineko’s tail twitches!* 😺\n\n{config_mode['grid_size']}x{config_mode['grid_size']} grid with {config_mode['mines']} Boomlings\nFlagged a tile! Tap again to reveal.\n\n😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺😺",
                    reply_markup=await build_keyboard(display_grid, user_id),
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
                return

            def reveal_tiles(x, y):
                if (not 0 <= x < config_mode['grid_size'] or
                    not 0 <= y < config_mode['grid_size'] or
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
            total_safe = config_mode['grid_size'] * config_mode['grid_size'] - config_mode['mines']

            if revealed >= total_safe:
                solana_wallet = '{{DB_OPERATION}}'
                jackpot_balance = 0.0
                jackpot_spl_balance = 0.0
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
                payout_result = {'success': True, 'result': 'mock_tx_id', 'error': None}
                payout_spl_result = {'success': True, 'result': 'mock_tx_id', 'error': None}

                group_caption = (
                    f"🎉 *Mineko’s Big Win!* 🎉\n\n"
                    f"A player with wallet `mock_wallet_address` cleared the {config['game_modes']['mineko']['grid_size']}x{config['game_modes']['mineko']['grid_size']} grid and won:\n"
                    f"• {payout:.3f} SOL\n"
                    f"• {payout_spl:.3f} MINES\n\n"
                    f"Join the adventure and try your luck! 😺"
                )
                image_path = os.path.join(os.path.dirname(__file__), 'win.jpg')
                try:
                    with open(image_path, 'rb') as photo:
                        await context.bot.send_photo(
                            chat_id=CHANNELID,
                            photo=photo,
                            caption=group_caption,
                            parse_mode='Markdown'
                        )
                except FileNotFoundError:
                    logging.error(f"Image file {image_path} not found.")
                    await context.bot.send_message(
                        chat_id=CHANNELID,
                        text=group_caption,
                        parse_mode='Markdown'
                    )

                if payout_result["success"] and payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL + {payout_spl} MINES\n\n[TX1](https://solscan.io/tx/mock_tx_id) [TX2](https://solscan.io/tx/mock_tx_id)",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                elif payout_result["success"] and not payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL but {payout_spl} MINES not paid. Please contact support\n\n[TX1](https://solscan.io/tx/mock_tx_id)",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                elif not payout_result["success"] and payout_spl_result["success"]:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout confirmation: {payout:.3f} SOL not paid but {payout_spl} MINES paid. Please contact support\n\n[TX2](https://solscan.io/tx/mock_tx_id)",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"Payout failed: {payout_result['error']}",
                        parse_mode='Markdown'
                    )

                await start(update, context, user_id=user_id)
                return
            else:
                await query.edit_message_text(
                    text=f"😺 *Mineko purrs!* 😺\n\n{config_mode['grid_size']}x{config_mode['grid_size']} grid with {config_mode['mines']} Boomlings\nRevealed a tile! Keep going!\n\n😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼😼",
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
            private_key = '{{DB_OPERATION}}'
            if private_key:
                message = await query.edit_message_text(
                    f"YOUR SOLANA PRIVATE KEY: ||mock_private_key||\n\nThis message will disappear in 15 seconds",
                    parse_mode="MarkdownV2"
                )
                await asyncio.sleep(15)
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
            else:
                await query.edit_message_text("No Solana secret key found.")
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

        elif query.data == 'refer':
            referral_count, sol_rewards = await get_referral_info(user_id)
            referral_link = f"https://t.me/MinekoSolBot?start={user_id}"
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
            image_path = os.path.join(os.path.dirname(__file__), 'refer.jpg')
            try:
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=(
                            f"😺 *Mineko’s Referral Program* 😺\n\n"
                            f"• *Referral Link*: `{referral_link}`\n"
                            f"• *Referrals*: {referral_count}\n"
                            f"• *Earned SOL Rewards*: {sol_rewards:.3f} SOL\n\n"
                            f"Share your link to earn 10% of your referrals’ entry fees in SOL!"
                        ),
                        parse_mode='Markdown'
                    )
            except FileNotFoundError:
                logging.error(f"Image file {image_path} not found.")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"😺 *Mineko’s Referral Program* 😺\n\n"
                        f"• *Referral Link*: `{referral_link}`\n"
                        f"• *Referrals*: {referral_count}\n"
                        f"• *Earned SOL Rewards*: {sol_rewards:.3f} SOL\n\n"
                        f"Share your link to earn 10% of your referrals’ entry fees in SOL!"
                    ),
                    parse_mode='Markdown'
                )
            await start(update, context, user_id=user_id)

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
            wallet_address = 'mock_solana_wallet_address'
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