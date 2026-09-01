from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import RetryAfter
import db
import core
import asyncio
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        ver = db.get_parameter("version")
        await update.message.reply_text(
            f"Hello {update.effective_user.first_name}! Vinted-Notifications is running under version {ver}.\n"
        )
    except Exception as e:
        logger.error(f"Error in hello command: {str(e)}", exc_info=True)
        try:
            await update.message.reply_text(
                "An error occurred. Please try again later."
            )
        except Exception as e2:
            logger.error(f"Error sending error message: {str(e2)}")


class LeRobot:
    def __init__(self, queue):
        from telegram import Bot
        from telegram.ext import (
            ApplicationBuilder,
            CallbackQueryHandler,
            CommandHandler,
        )

        try:

            self.bot = Bot(db.get_secret("telegram_token"))
            self.app = (
                ApplicationBuilder().token(db.get_secret("telegram_token")).build()
            )

            # Create the item queue to send to telegram
            self.new_items_queue = queue

            # Handler verify if bot is running
            self.app.add_handler(CommandHandler("hello", hello))
            # Keyword handlers
            self.app.add_handler(CommandHandler("add_query", self.add_query))
            self.app.add_handler(CommandHandler("remove_query", self.remove_query))
            self.app.add_handler(CommandHandler("queries", self.queries))
            # Allowlist handlers
            self.app.add_handler(
                CommandHandler("clear_allowlist", self.clear_allowlist)
            )
            self.app.add_handler(CommandHandler("add_country", self.add_country))
            self.app.add_handler(CommandHandler("remove_country", self.remove_country))
            self.app.add_handler(CommandHandler("allowlist", self.allowlist))
            # Buttons carried by each item notification
            self.app.add_handler(CallbackQueryHandler(self.handle_action))
            self.app.add_handler(CommandHandler("muted", self.muted))
            self.app.add_handler(CommandHandler("unmute_brand", self.unmute_brand))

            # TODO : Help command

            # TODO : Manage removals after current items have been processed.

            job_queue = self.app.job_queue
            # Set the commands
            job_queue.run_once(self.set_commands, when=1)
            # Every day we check for a new version
            job_queue.run_repeating(self.check_version, interval=86400, first=1)
            # Every second we check for new posts to send to telegram
            job_queue.run_once(self.check_telegram_queue, when=1)

            self.app.run_polling()
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}", exc_info=True)

    ### QUERIES ###

    # Add a query to the db
    async def add_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            query = context.args
            if not query:
                await update.message.reply_text("No query provided.")
                return

            # Split the message into name=query if it contains an equal sign before the url. Store them separately
            if "=http" in query[0]:
                name, url = query[0].split("=", 1)
            else:
                name = None
                url = query[0]
            # Process the query using the core function
            message, is_new_query = core.process_query(url, name)

            if is_new_query:
                # Create a string with all the keywords
                query_list = core.get_formatted_query_list()
                await update.message.reply_text(
                    f"{message} \nCurrent queries: \n{query_list}"
                )
            else:
                await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error adding query: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while adding the query. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    # Remove a query from the db
    async def remove_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            number = context.args
            if not number:
                await update.message.reply_text("No number provided.")
                return

            # Process the removal using the core function
            if number[0] != "all":
                number[0] = db.get_query_id_by_rowid(number[0])
            message, success = core.process_remove_query(str(number[0]))

            if success:
                if number[0] == "all":
                    await update.message.reply_text(message)
                else:
                    # Get the updated list of queries
                    query_list = core.get_formatted_query_list()
                    await update.message.reply_text(
                        f"{message} \nCurrent queries: \n{query_list}"
                    )
            else:
                await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error removing query: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while removing the query. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    # get all queries from the db
    async def queries(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            query_list = core.get_formatted_query_list()
            await update.message.reply_text(f"Current queries: \n{query_list}")
        except Exception as e:
            logger.error(f"Error retrieving queries: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while retrieving the queries. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    ### ALLOWLIST ###

    async def clear_allowlist(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            db.clear_allowlist()
            await update.message.reply_text(
                "Allowlist cleared. All countries are allowed."
            )
        except Exception as e:
            logger.error(f"Error clearing allowlist: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while clearing the allowlist. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    async def add_country(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            country = context.args
            if not country:
                await update.message.reply_text("No country provided")
                return

            # Process the country using the core function
            message, country_list = core.process_add_country(" ".join(country))

            await update.message.reply_text(
                f"{message} Current allowlist: {country_list}"
            )
        except Exception as e:
            logger.error(f"Error adding country to allowlist: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while adding the country to the allowlist. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    async def remove_country(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            country = context.args
            if not country:
                await update.message.reply_text("No country provided")
                return

            # Process the country using the core function
            message, country_list = core.process_remove_country(" ".join(country))

            await update.message.reply_text(
                f"{message} Current allowlist: {country_list}"
            )
        except Exception as e:
            logger.error(
                f"Error removing country from allowlist: {str(e)}", exc_info=True
            )
            try:
                await update.message.reply_text(
                    "An error occurred while removing the country from the allowlist. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    async def allowlist(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            if db.get_allowlist() == 0:
                await update.message.reply_text(
                    "No allowlist set. All countries are allowed."
                )
            else:
                await update.message.reply_text(
                    f"Current allowlist: {db.get_allowlist()}"
                )
        except Exception as e:
            logger.error(f"Error retrieving allowlist: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text(
                    "An error occurred while retrieving the allowlist. Please try again later."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")


    async def handle_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Act on a button pressed under an item notification.

        The button only carries an item id, since callback data is limited to
        64 bytes: what to mute is looked up in the notification log.
        """
        query = update.callback_query
        try:
            action, _, item_id = (query.data or "").partition(":")
            logged = db.get_logged_item(item_id)
            if not logged:
                await query.answer("Item no longer known", show_alert=True)
                return

            if action == "mute_brand":
                brand = logged.get("brand")
                if not brand:
                    await query.answer("No brand recorded for this item")
                    return
                added = db.ignore_brand(brand)
                await query.answer(
                    f"{brand} muted" if added else f"{brand} was already muted"
                )
            elif action == "mute_seller":
                seller = logged.get("seller_id")
                if not seller:
                    await query.answer("No seller recorded for this item")
                    return
                name = logged.get("seller_name") or seller
                added = db.ignore_seller(seller, logged.get("seller_name"))
                await query.answer(
                    f"{name} muted" if added else f"{name} was already muted"
                )
            else:
                await query.answer()
        except Exception as e:
            logger.error(f"Error handling action: {str(e)}", exc_info=True)
            try:
                await query.answer("Something went wrong")
            except Exception:
                pass

    async def muted(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List what is currently muted, so it can be undone."""
        try:
            lists = db.get_ignored_lists()
            lines = []
            if lists["brands"]:
                lines.append("Muted brands:")
                lines += [f"  {brand}" for brand, _ in lists["brands"]]
            if lists["sellers"]:
                lines.append("Muted sellers:")
                lines += [
                    f"  {name or seller_id}" for seller_id, name, _ in lists["sellers"]
                ]
            if not lines:
                lines = ["Nothing is muted."]
            else:
                lines.append("")
                lines.append("Use /unmute_brand <name> to undo.")
            await update.message.reply_text("\n".join(lines))
        except Exception as e:
            logger.error(f"Error listing muted entries: {str(e)}", exc_info=True)

    async def unmute_brand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Undo a muted brand."""
        try:
            brand = " ".join(context.args).strip()
            if not brand:
                await update.message.reply_text("No brand provided.")
                return
            removed = db.unignore_brand(brand)
            await update.message.reply_text(
                f"{brand} is no longer muted" if removed else f"{brand} was not muted"
            )
        except Exception as e:
            logger.error(f"Error unmuting brand: {str(e)}", exc_info=True)

    ### TELEGRAM SPECIFIC FUNCTIONS ###

    async def send_new_post(
        self, content, url, text, buy_url=None, buy_text=None, silent=False,
        item_id=None
    ):
        try:
            async with self.bot:
                chat_ID = str(db.get_secret("telegram_chat_id"))
                buttons = [[InlineKeyboardButton(text=text, url=url)]]
                if buy_url and buy_text:
                    buttons.append([InlineKeyboardButton(text=buy_text, url=buy_url)])
                if item_id is not None:
                    # Acting where the notification is read beats going to the
                    # settings page to describe an item you just saw.
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text="🔇 Brand", callback_data=f"mute_brand:{item_id}"
                            ),
                            InlineKeyboardButton(
                                text="🔇 Seller", callback_data=f"mute_seller:{item_id}"
                            ),
                        ]
                    )
                await self.bot.send_message(
                    chat_ID,
                    content,
                    parse_mode="HTML",
                    disable_notification=silent,
                    read_timeout=40,
                    write_timeout=40,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        except RetryAfter as e:
            retry_after = e.retry_after
            logger.error(
                f"Flood control exceeded. Retrying in {retry_after + 2} seconds"
            )
            await asyncio.sleep(retry_after + 2)
            # Retry sending the message
            await self.send_new_post(
                content, url, text, buy_url, buy_text, silent, item_id
            )
        except Exception as e:
            logger.error(f"Error sending new post: {str(e)}", exc_info=True)

    async def check_version(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            # get latest version from the repository
            should_update, VER, latest_version, url = core.check_version()

            if not should_update:
                await self.send_new_post(
                    f"Version {latest_version} is now available. Please update the bot.",
                    url,
                    "Open Github",
                )
        except Exception as e:
            logger.error(f"Error checking for new version: {str(e)}", exc_info=True)

    async def check_telegram_queue(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            while 1:
                if not self.new_items_queue.empty():
                    (
                        content,
                        url,
                        text,
                        buy_url,
                        buy_text,
                        silent,
                        item_id,
                    ) = self.new_items_queue.get()
                    await self.send_new_post(
                        content, url, text, buy_url, buy_text, silent, item_id
                    )
                else:
                    await asyncio.sleep(0.1)
                    pass
        except Exception as e:
            logger.error(f"Error checking telegram queue: {str(e)}", exc_info=True)

    async def set_commands(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            await self.bot.set_my_commands(
                [
                    ("hello", "Verify if bot is running"),
                    ("add_query", "Add a keyword to the bot"),
                    ("remove_query", "Remove a keyword from the bot"),
                    ("queries", "List all queries"),
                    ("clear_allowlist", "Clear the allowlist"),
                    ("add_country", "Add a country to the allowlist"),
                    ("remove_country", "Remove a country from the allowlist"),
                    ("allowlist", "List all countries in the allowlist"),
                    ("muted", "List muted brands and sellers"),
                    ("unmute_brand", "Stop muting a brand"),
                ]
            )
            logger.info("Bot commands set successfully")
        except Exception as e:
            logger.error(f"Error setting bot commands: {str(e)}", exc_info=True)
