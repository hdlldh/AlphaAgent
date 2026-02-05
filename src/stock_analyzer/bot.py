"""
Telegram bot for stock subscription management.

Provides commands for users to:
- Subscribe to stock analysis
- Unsubscribe from stocks
- List their subscriptions
"""

import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from stock_analyzer.exceptions import SubscriptionLimitError
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.models import Subscription, User
from stock_analyzer.storage import Storage

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram bot for managing stock subscriptions.

    Handles user commands:
    - /start - Register new user
    - /help - Show available commands
    - /subscribe <symbol> - Subscribe to stock
    - /unsubscribe <symbol> - Unsubscribe from stock
    - /list - List active subscriptions
    """

    def __init__(
        self,
        storage: Storage,
        token: str,
        fetcher: Optional[StockFetcher] = None,
        analyzer: Optional['Analyzer'] = None
    ):
        """
        Initialize Telegram bot.

        Args:
            storage: Storage instance for database operations
            token: Telegram bot token
            fetcher: Stock fetcher for symbol validation (creates if None)
            analyzer: Analyzer instance for on-demand analysis (optional)
        """
        self.storage = storage
        self.token = token
        self.fetcher = fetcher or StockFetcher()
        self.analyzer = analyzer

        # Build application
        self.application = (
            Application.builder()
            .token(token)
            .build()
        )

        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("list", self.list_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("about", self.about_command))

        logger.info("Telegram bot initialized")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command.

        Creates new user or updates last_active for existing user.
        """
        try:
            user_id = str(update.effective_user.id)
            username = update.effective_user.username or "unknown"

            # Check if user exists
            existing_user = self.storage.get_user(user_id)

            if not existing_user:
                # Create new user
                user = User(
                    user_id=user_id,
                    telegram_username=f"@{username}",
                    created_at=datetime.utcnow()
                )
                self.storage.add_user(user)
                logger.info(f"New user registered: {user_id}")

                await update.message.reply_text(
                    f"👋 Welcome to Stock Analyzer!\n\n"
                    f"I'll help you track stock market insights.\n\n"
                    f"Use /help to see available commands."
                )
            else:
                # Update last active
                self.storage.update_user_last_active(user_id)

                await update.message.reply_text(
                    f"👋 Welcome back!\n\n"
                    f"Use /help to see available commands."
                )

        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command.

        Shows all available commands and their usage.
        """
        help_text = """
📊 *Stock Analyzer Bot Commands*

*Subscription Management:*
/subscribe <symbol> - Subscribe to daily analysis for a stock
/unsubscribe <symbol> - Unsubscribe from a stock
/list - Show your active subscriptions

*Analysis:*
/analyze <symbol> - Get instant analysis for any stock
/history <symbol> [days] - View past insights for a stock

*Information:*
/stats - View your statistics and insights received
/about - Learn about this bot
/help - Show this help message

*Examples:*
`/subscribe AAPL` - Get daily insights for Apple
`/unsubscribe MSFT` - Stop receiving Microsoft insights
`/list` - See all your subscriptions
`/analyze TSLA` - Get instant analysis for Tesla
`/history AAPL` - View all Apple insights
`/history AAPL 7` - View Apple insights from last 7 days
`/stats` - View your personal statistics
`/about` - Learn more about the bot

*Limits:*
• Maximum 10 subscriptions per user
• You'll receive daily insights after market close
• On-demand analysis available anytime
        """

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /subscribe <symbol> command.

        Subscribes user to daily analysis for specified stock.
        """
        try:
            user_id = str(update.effective_user.id)

            # Validate arguments
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Usage: /subscribe <symbol>\n\n"
                    "Example: /subscribe AAPL"
                )
                return

            # Get and normalize symbol
            symbol = context.args[0].upper().strip()

            # Check subscription limit
            current_count = self.storage.get_subscription_count(user_id=user_id, active_only=True)
            if current_count >= 10:
                await update.message.reply_text(
                    f"❌ Subscription limit reached!\n\n"
                    f"You have {current_count}/10 subscriptions.\n"
                    f"Use /unsubscribe to remove a stock first."
                )
                return

            # Check if already subscribed
            existing_subs = self.storage.get_subscriptions(
                user_id=user_id,
                stock_symbol=symbol,
                active_only=True
            )
            if existing_subs:
                await update.message.reply_text(
                    f"ℹ️ You're already subscribed to {symbol}!"
                )
                return

            # Validate symbol
            try:
                is_valid = await self.fetcher.validate_symbol(symbol)
                if not is_valid:
                    await update.message.reply_text(
                        f"❌ Invalid stock symbol: {symbol}\n\n"
                        f"Please check the symbol and try again."
                    )
                    return
            except Exception as e:
                logger.warning(f"Symbol validation failed for {symbol}: {e}")
                await update.message.reply_text(
                    f"❌ Could not validate symbol: {symbol}\n\n"
                    f"There may be a network issue. Please try again later."
                )
                return

            # Add subscription
            subscription = Subscription(
                user_id=user_id,
                stock_symbol=symbol,
                subscription_date=datetime.utcnow()
            )
            self.storage.add_subscription(subscription)

            logger.info(f"User {user_id} subscribed to {symbol}")

            await update.message.reply_text(
                f"✅ Successfully subscribed to {symbol}!\n\n"
                f"You'll receive daily analysis insights after market close.\n\n"
                f"Subscriptions: {current_count + 1}/10"
            )

        except SubscriptionLimitError as e:
            await update.message.reply_text(
                f"❌ Subscription limit reached: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in subscribe_command: {e}")
            await update.message.reply_text(
                "❌ Failed to add subscription. Please try again later."
            )

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /unsubscribe <symbol> command.

        Unsubscribes user from daily analysis for specified stock.
        """
        try:
            user_id = str(update.effective_user.id)

            # Validate arguments
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Usage: /unsubscribe <symbol>\n\n"
                    "Example: /unsubscribe AAPL"
                )
                return

            # Get and normalize symbol
            symbol = context.args[0].upper().strip()

            # Check if subscribed
            existing_subs = self.storage.get_subscriptions(
                user_id=user_id,
                stock_symbol=symbol,
                active_only=True
            )

            if not existing_subs:
                await update.message.reply_text(
                    f"❌ You're not subscribed to {symbol}.\n\n"
                    f"Use /list to see your subscriptions."
                )
                return

            # Remove subscription
            self.storage.remove_subscription(user_id, symbol)

            logger.info(f"User {user_id} unsubscribed from {symbol}")

            # Get updated count
            remaining = self.storage.get_subscription_count(user_id=user_id, active_only=True)

            await update.message.reply_text(
                f"✅ Successfully unsubscribed from {symbol}!\n\n"
                f"Remaining subscriptions: {remaining}/10"
            )

        except Exception as e:
            logger.error(f"Error in unsubscribe_command: {e}")
            await update.message.reply_text(
                "❌ Failed to remove subscription. Please try again later."
            )

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /list command.

        Lists all active subscriptions for the user.
        """
        try:
            user_id = str(update.effective_user.id)

            # Get subscriptions
            subscriptions = self.storage.get_subscriptions(
                user_id=user_id,
                active_only=True
            )

            if not subscriptions:
                await update.message.reply_text(
                    "📭 You have no active subscriptions.\n\n"
                    "Use /subscribe <symbol> to start tracking a stock.\n\n"
                    "Example: /subscribe AAPL"
                )
                return

            # Build list message
            message_lines = [
                f"📊 *Your Subscriptions ({len(subscriptions)}/10)*\n"
            ]

            # Sort by symbol
            sorted_subs = sorted(subscriptions, key=lambda s: s.stock_symbol)

            for sub in sorted_subs:
                sub_date = sub.subscription_date.strftime("%Y-%m-%d") if sub.subscription_date else "N/A"
                message_lines.append(f"• {sub.stock_symbol} (since {sub_date})")

            message_lines.append(
                f"\nUse /unsubscribe <symbol> to remove a stock."
            )

            await update.message.reply_text(
                "\n".join(message_lines),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in list_command: {e}")
            await update.message.reply_text(
                "❌ Failed to fetch subscriptions. Please try again later."
            )

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /history <symbol> [days] command.

        Shows historical insights for a stock.
        Optional days parameter limits results to last N days.
        """
        try:
            # Validate arguments
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Usage: /history <symbol> [days]\n\n"
                    "Examples:\n"
                    "`/history AAPL` - All available insights\n"
                    "`/history AAPL 7` - Last 7 days only",
                    parse_mode="Markdown"
                )
                return

            # Parse arguments
            symbol = context.args[0].upper().strip()
            days = None

            if len(context.args) > 1:
                try:
                    days = int(context.args[1])
                    if days <= 0:
                        await update.message.reply_text(
                            "❌ Days must be a positive number."
                        )
                        return
                except ValueError:
                    await update.message.reply_text(
                        "❌ Invalid days parameter. Must be a number.\n\n"
                        "Example: /history AAPL 7"
                    )
                    return

            # Calculate date range if days specified
            start_date = None
            if days:
                from datetime import date, timedelta
                start_date = date.today() - timedelta(days=days)

            # Get insights
            insights = self.storage.get_insights(
                stock_symbol=symbol,
                start_date=start_date,
                limit=10  # Limit to 10 for Telegram display
            )

            if not insights:
                date_info = f" for the last {days} days" if days else ""
                await update.message.reply_text(
                    f"📭 No insights found for {symbol}{date_info}.\n\n"
                    f"This stock may not be in your subscriptions or no analysis has been run yet."
                )
                return

            # Format message
            date_info = f" (Last {days} days)" if days else ""
            message_lines = [
                f"📈 *Historical Insights for {symbol}{date_info}*\n"
            ]

            for i, insight in enumerate(insights, start=1):
                # Format date
                date_str = insight.analysis_date.strftime("%Y-%m-%d")

                # Truncate summary if too long
                summary = insight.summary
                if len(summary) > 200:
                    summary = summary[:197] + "..."

                # Build insight entry
                message_lines.append(f"*{i}. {date_str}* ({insight.confidence_level.upper()})")
                message_lines.append(summary)

                # Add trends if available
                if insight.trend_analysis:
                    trend = insight.trend_analysis
                    if len(trend) > 150:
                        trend = trend[:147] + "..."
                    message_lines.append(f"_Trend: {trend}_")

                message_lines.append("")  # Blank line

            # Add footer
            message_lines.append(
                f"_Showing {len(insights)} insights_\n"
                f"Use `/history {symbol} 7` to see last 7 days"
            )

            # Send message (handle Telegram's 4096 character limit)
            message = "\n".join(message_lines)
            if len(message) > 4096:
                # Split message
                message = "\n".join(message_lines[:len(message_lines)//2])
                message += f"\n\n_Message truncated. Use /history {symbol} 3 for fewer results._"

            await update.message.reply_text(
                message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in history_command: {e}")
            await update.message.reply_text(
                "❌ Failed to fetch history. Please try again later."
            )

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /analyze <symbol> command.

        Performs on-demand stock analysis and returns insight immediately.
        """
        try:
            # Check if analyzer is available
            if not self.analyzer:
                await update.message.reply_text(
                    "❌ On-demand analysis is not available.\n\n"
                    "This feature requires analyzer configuration."
                )
                return

            # Validate arguments
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Usage: /analyze <symbol>\n\n"
                    "Example: `/analyze AAPL`",
                    parse_mode="Markdown"
                )
                return

            # Get and normalize symbol
            symbol = context.args[0].upper().strip()

            # Send "analyzing..." message
            status_message = await update.message.reply_text(
                f"🔍 Analyzing {symbol}...\n\n"
                f"This may take a few seconds."
            )

            # Perform analysis
            try:
                insight = await self.analyzer.analyze_stock(symbol)

                # Delete status message
                await status_message.delete()

                # Format and send insight
                message_lines = [
                    f"📈 *Analysis for {symbol}*",
                    f"_Confidence: {insight.confidence_level.upper()}_\n",
                    f"*Summary:*",
                    insight.summary,
                    ""
                ]

                if insight.trend_analysis:
                    trend = insight.trend_analysis
                    if len(trend) > 200:
                        trend = trend[:197] + "..."
                    message_lines.append(f"*Trend:*")
                    message_lines.append(trend)
                    message_lines.append("")

                if insight.risk_factors:
                    message_lines.append("*Risks:*")
                    for risk in insight.risk_factors[:3]:  # Limit to 3
                        message_lines.append(f"• {risk}")
                    message_lines.append("")

                if insight.opportunities:
                    message_lines.append("*Opportunities:*")
                    for opp in insight.opportunities[:3]:  # Limit to 3
                        message_lines.append(f"• {opp}")
                    message_lines.append("")

                message_lines.append(
                    f"_Analysis date: {insight.analysis_date}_"
                )

                message = "\n".join(message_lines)

                # Handle Telegram's 4096 character limit
                if len(message) > 4096:
                    message = "\n".join(message_lines[:len(message_lines)//2])
                    message += "\n\n_Message truncated. Use /history for full details._"

                await update.message.reply_text(
                    message,
                    parse_mode="Markdown"
                )

            except Exception as analysis_error:
                # Delete status message
                try:
                    await status_message.delete()
                except:
                    pass

                error_msg = str(analysis_error)

                # Handle specific error types
                if "invalid" in error_msg.lower() or "not found" in error_msg.lower():
                    await update.message.reply_text(
                        f"❌ Invalid stock symbol: {symbol}\n\n"
                        f"Please check the symbol and try again."
                    )
                elif "data" in error_msg.lower() or "fetch" in error_msg.lower():
                    await update.message.reply_text(
                        f"❌ Could not fetch data for {symbol}.\n\n"
                        f"The stock may not be available or there's a temporary issue."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Analysis failed for {symbol}.\n\n"
                        f"Please try again later."
                    )

                logger.error(f"Analysis failed for {symbol}: {analysis_error}")

        except Exception as e:
            logger.error(f"Error in analyze_command: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /stats command - show user statistics.

        Displays:
        - Active subscriptions count
        - Total insights received
        - Last insight date
        - Most analyzed stocks
        """
        try:
            user_id = update.effective_user.id

            # Get user's subscriptions
            subscriptions = self.storage.get_subscriptions(user_id=user_id, active_only=True)

            if not subscriptions:
                await update.message.reply_text(
                    "📊 *Your Statistics*\n\n"
                    "You don't have any active subscriptions yet.\n\n"
                    "Use /subscribe <symbol> to start receiving insights!",
                    parse_mode="Markdown"
                )
                return

            # Get delivery statistics for this user
            conn = self.storage._get_connection()
            cursor = conn.cursor()

            # Total insights received
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM delivery_logs
                WHERE user_id = ? AND delivery_status = 'success'
                """,
                (user_id,)
            )
            total_insights = cursor.fetchone()[0]

            # Last insight date
            cursor.execute(
                """
                SELECT MAX(delivery_time)
                FROM delivery_logs
                WHERE user_id = ? AND delivery_status = 'success'
                """,
                (user_id,)
            )
            last_insight = cursor.fetchone()[0]

            # Most analyzed stocks for this user
            cursor.execute(
                """
                SELECT stock_symbol, COUNT(*) as count
                FROM delivery_logs
                WHERE user_id = ? AND delivery_status = 'success'
                GROUP BY stock_symbol
                ORDER BY count DESC
                LIMIT 3
                """,
                (user_id,)
            )
            top_stocks = cursor.fetchall()

            conn.close()

            # Format response
            response = "📊 *Your Statistics*\n\n"
            response += f"*Active Subscriptions:* {len(subscriptions)}\n"
            response += f"*Total Insights Received:* {total_insights}\n"

            if last_insight:
                response += f"*Last Insight:* {last_insight}\n"

            response += "\n*Your Subscribed Stocks:*\n"
            for sub in subscriptions:
                response += f"  • {sub.stock_symbol}\n"

            if top_stocks:
                response += "\n*Most Analyzed:*\n"
                for symbol, count in top_stocks:
                    response += f"  • {symbol}: {count} insights\n"

            response += "\nUse /history <symbol> to view past analyses!"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /about command - show bot information.

        Displays:
        - Bot description
        - Features
        - Version information
        - Contact/support
        """
        try:
            response = (
                "🤖 *Stock Analyzer Bot*\n\n"
                "*AI-Powered Stock Analysis*\n"
                "Get daily insights for your favorite stocks, powered by advanced AI.\n\n"
                "*✨ Features:*\n"
                "  • 📊 Daily automated analysis\n"
                "  • 🔔 Personalized alerts\n"
                "  • 💡 AI-generated insights\n"
                "  • 📈 Historical data access\n"
                "  • ⚡ On-demand analysis\n\n"
                "*🎯 How It Works:*\n"
                "1. Subscribe to stocks with /subscribe\n"
                "2. Receive daily insights automatically\n"
                "3. Query history anytime with /history\n"
                "4. Get instant analysis with /analyze\n\n"
                "*📚 Available Commands:*\n"
                "  /subscribe - Subscribe to a stock\n"
                "  /unsubscribe - Unsubscribe from a stock\n"
                "  /list - View your subscriptions\n"
                "  /analyze - Get instant analysis\n"
                "  /history - View past insights\n"
                "  /stats - View your statistics\n"
                "  /help - Show help message\n\n"
                "*🔧 Version:* 1.0.0 (MVP)\n"
                "*🏢 Provider:* AlphaAgent\n\n"
                "*📝 Note:* This bot provides informational insights only. "
                "Not financial advice. Always do your own research!\n\n"
                "Questions? Type /help for more information."
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in about_command: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )

    def run(self):
        """
        Start the bot with polling.

        Runs until interrupted (Ctrl+C).
        """
        logger.info("Starting Telegram bot polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def run_webhook(self, webhook_url: str, port: int = 8443):
        """
        Start the bot with webhook.

        Args:
            webhook_url: Public URL for webhook
            port: Port to listen on
        """
        logger.info(f"Starting Telegram bot webhook on {webhook_url}:{port}...")
        await self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=self.token,
            webhook_url=f"{webhook_url}/{self.token}"
        )
