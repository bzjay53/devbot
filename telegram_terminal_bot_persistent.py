#!/usr/bin/env python3
import os
import asyncio
import subprocess
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import paramiko
from io import StringIO

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SSH_HOST = os.getenv('SSH_HOST', 'localhost')
SSH_PORT = int(os.getenv('SSH_PORT', 22))
SSH_USERNAME = os.getenv('SSH_USERNAME', 'root')
SSH_PASSWORD = os.getenv('SSH_PASSWORD', '')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')
MAX_OUTPUT_LENGTH = int(os.getenv('MAX_OUTPUT_LENGTH', 4000))
CLAUDE_CODE_PATH = os.getenv('CLAUDE_CODE_PATH', '/usr/local/bin/claude')
WORKING_DIR = os.getenv('WORKING_DIR', '/root/christmas-trading')

# Session Management
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.ssh_clients = {}
        self.last_activity = {}
        self.session_active = {}
        self.monitoring_thread = None
        
    def create_session(self, user_id):
        """Create a new persistent session"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'start_time': datetime.now(),
                'commands_count': 0,
                'current_dir': WORKING_DIR
            }
            self.session_active[user_id] = True
            self.last_activity[user_id] = time.time()
            
            # Create SSH connection for this user
            if self.connect_ssh(user_id):
                return True
        return False
    
    def connect_ssh(self, user_id):
        """Establish SSH connection for a user"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if SSH_PASSWORD:
                client.connect(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)
            else:
                client.connect(SSH_HOST, SSH_PORT, SSH_USERNAME)
            
            self.ssh_clients[user_id] = client
            
            # Open persistent shell channel
            shell = client.invoke_shell()
            self.sessions[user_id]['shell'] = shell
            
            # Set working directory
            shell.send(f'cd {WORKING_DIR}\n')
            time.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"SSH connection error for user {user_id}: {e}")
            return False
    
    def execute_command(self, user_id, command):
        """Execute command in user's session"""
        if user_id not in self.session_active or not self.session_active[user_id]:
            return "Session not active. Use /start to begin a new session."
        
        self.last_activity[user_id] = time.time()
        self.sessions[user_id]['commands_count'] += 1
        
        try:
            shell = self.sessions[user_id]['shell']
            
            # Send command
            shell.send(command + '\n')
            
            # Wait for output
            time.sleep(0.5)
            output = ''
            
            while shell.recv_ready():
                chunk = shell.recv(4096).decode('utf-8')
                output += chunk
                if len(output) > MAX_OUTPUT_LENGTH:
                    output = output[:MAX_OUTPUT_LENGTH] + "\n... (output truncated)"
                    break
            
            return output if output else "Command executed (no output)"
            
        except Exception as e:
            # Try to reconnect
            if self.connect_ssh(user_id):
                return self.execute_command(user_id, command)
            return f"Session error: {e}"
    
    def stop_session(self, user_id):
        """Stop a user's session"""
        if user_id in self.session_active:
            self.session_active[user_id] = False
            
            # Close SSH connection
            if user_id in self.ssh_clients:
                self.ssh_clients[user_id].close()
                del self.ssh_clients[user_id]
            
            # Clear session data
            if user_id in self.sessions:
                session_info = self.sessions[user_id]
                duration = datetime.now() - session_info['start_time']
                del self.sessions[user_id]
                
                return {
                    'duration': duration,
                    'commands_count': session_info['commands_count']
                }
        return None
    
    def get_session_info(self, user_id):
        """Get session information"""
        if user_id in self.sessions and self.session_active.get(user_id, False):
            session = self.sessions[user_id]
            duration = datetime.now() - session['start_time']
            last_active = int(time.time() - self.last_activity[user_id])
            
            return {
                'active': True,
                'duration': duration,
                'commands_count': session['commands_count'],
                'last_activity': last_active,
                'current_dir': session['current_dir']
            }
        return {'active': False}

# Global session manager
session_manager = SessionManager()

def is_authorized(user_id):
    """Check if user is authorized"""
    return str(user_id) in ALLOWED_USERS or not ALLOWED_USERS[0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler - creates persistent session"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized access")
        return
    
    # Create session
    if session_manager.create_session(user_id):
        keyboard = [
            [InlineKeyboardButton("📟 Session Info", callback_data='session_info')],
            [InlineKeyboardButton("🚀 Quick Commands", callback_data='quick_commands')],
            [InlineKeyboardButton("🤖 Claude Code", callback_data='claude_menu')],
            [InlineKeyboardButton("🛑 Stop Session (/stop)", callback_data='stop_session')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🖥️ *Persistent Terminal Session Started*\n\n"
            "✅ Your session is now active and will remain open.\n"
            "📝 Send any command to execute.\n"
            "🛑 Use /stop to end the session.\n\n"
            "⏰ You'll receive activity reminders every 10 minutes.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Start monitoring job for this user
        context.job_queue.run_repeating(
            session_monitor,
            interval=600,  # 10 minutes
            first=600,
            data=user_id,
            name=f"monitor_{user_id}"
        )
    else:
        await update.message.reply_text("Failed to create session. Please try again.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop command handler - ends session"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized access")
        return
    
    # Stop monitoring job
    jobs = context.job_queue.get_jobs_by_name(f"monitor_{user_id}")
    for job in jobs:
        job.schedule_removal()
    
    # Stop session
    session_info = session_manager.stop_session(user_id)
    
    if session_info:
        await update.message.reply_text(
            f"🛑 *Session Ended*\n\n"
            f"⏱️ Duration: {session_info['duration']}\n"
            f"📊 Commands executed: {session_info['commands_count']}\n\n"
            f"Use /start to begin a new session.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("No active session found.")

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text commands"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized access")
        return
    
    # Check if session is active
    session_info = session_manager.get_session_info(user_id)
    if not session_info['active']:
        await update.message.reply_text(
            "No active session. Use /start to begin a new session."
        )
        return
    
    command = update.message.text
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Execute command
    result = session_manager.execute_command(user_id, command)
    
    # Format and send result
    response = f"```bash\n$ {command}\n{result}\n```"
    
    # Split long messages
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096], parse_mode='Markdown')
    else:
        await update.message.reply_text(response, parse_mode='Markdown')

async def session_monitor(context: ContextTypes.DEFAULT_TYPE):
    """Monitor session activity - runs every 10 minutes"""
    user_id = context.job.data
    session_info = session_manager.get_session_info(user_id)
    
    if session_info['active']:
        duration_minutes = int(session_info['duration'].total_seconds() / 60)
        
        keyboard = [
            [InlineKeyboardButton("📟 Session Info", callback_data='session_info')],
            [InlineKeyboardButton("🚀 Continue Working", callback_data='continue')],
            [InlineKeyboardButton("🛑 Stop Session", callback_data='stop_session')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⏰ *Session Activity Reminder*\n\n"
                 f"Your session is still active!\n"
                 f"⏱️ Duration: {duration_minutes} minutes\n"
                 f"📊 Commands: {session_info['commands_count']}\n"
                 f"💤 Idle for: {session_info['last_activity']} seconds\n\n"
                 f"Session will remain open until you use /stop",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_authorized(user_id):
        await query.answer("Unauthorized", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'session_info':
        session_info = session_manager.get_session_info(user_id)
        if session_info['active']:
            duration_minutes = int(session_info['duration'].total_seconds() / 60)
            await query.message.reply_text(
                f"📊 *Session Information*\n\n"
                f"✅ Status: Active\n"
                f"⏱️ Duration: {duration_minutes} minutes\n"
                f"📝 Commands: {session_info['commands_count']}\n"
                f"💤 Last activity: {session_info['last_activity']}s ago\n"
                f"📁 Current dir: {session_info['current_dir']}",
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text("No active session.")
    
    elif query.data == 'stop_session':
        # Trigger stop command
        await stop(query, context)
    
    elif query.data == 'continue':
        await query.message.reply_text(
            "👍 Session continues running.\n"
            "Send any command to execute."
        )
    
    elif query.data == 'quick_commands':
        keyboard = [
            [InlineKeyboardButton("📁 List Files", callback_data='cmd_ls')],
            [InlineKeyboardButton("🔄 Git Status", callback_data='cmd_git_status')],
            [InlineKeyboardButton("📊 Process List", callback_data='cmd_ps')],
            [InlineKeyboardButton("💾 Disk Usage", callback_data='cmd_df')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("Select a command:", reply_markup=reply_markup)
    
    elif query.data.startswith('cmd_'):
        commands = {
            'cmd_ls': 'ls -la',
            'cmd_git_status': 'git status',
            'cmd_ps': 'ps aux | head -20',
            'cmd_df': 'df -h'
        }
        
        cmd = commands.get(query.data, '')
        if cmd:
            result = session_manager.execute_command(user_id, cmd)
            await query.message.reply_text(
                f"```bash\n$ {cmd}\n{result}\n```",
                parse_mode='Markdown'
            )
    
    elif query.data == 'claude_menu':
        keyboard = [
            [InlineKeyboardButton("💭 Ask Claude", callback_data='claude_ask')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "Send a message starting with 'claude' to ask Claude Code.\n"
            "Example: `claude explain this code`",
            reply_markup=reply_markup
        )

async def claude_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Claude Code commands"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized access")
        return
    
    # Check session
    session_info = session_manager.get_session_info(user_id)
    if not session_info['active']:
        await update.message.reply_text(
            "No active session. Use /start to begin a new session."
        )
        return
    
    # Get the Claude query
    if context.args:
        query = ' '.join(context.args)
    else:
        await update.message.reply_text("Please provide a query for Claude Code")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Execute Claude command
    claude_cmd = f'{CLAUDE_CODE_PATH} "{query}"'
    result = session_manager.execute_command(user_id, claude_cmd)
    
    # Send result
    response = f"🤖 *Claude Code Response:*\n```\n{result}\n```"
    
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096], parse_mode='Markdown')
    else:
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Main function"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("claude", claude_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    print("🤖 Persistent Telegram Terminal Bot started...")
    print("Sessions will remain active until explicitly stopped with /stop")
    app.run_polling()

if __name__ == "__main__":
    main()