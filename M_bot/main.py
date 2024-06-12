"""
This module contains the main functionality of the application.
"""
import os
import sqlite3
from datetime import date
from typing import Final

from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from M_bot.stats import generate_monthly_reports, generate_yearly_reports

load_dotenv()
TOKEN = os.getenv('TOKEN')

BOT_USERNAME: Final = '@multi_milosz_bot'


async def start_command(update: Update, _):
    """
    Handles the start command.
    """
    await update.message.reply_text("Hello! Thanks for using M bot")


async def help_command(update: Update, _):
    """
    Handles the help command.
    """
    help_text = """
    Available commands:
    - /start: Starts the bot
    - /help: Shows this help message
    - /expense: Adds a new expense
    - /delete_last_expense: Deletes the last expense
    - /monthly_report [month] [year]: Generates a monthly report
    - /yearly_report [year]: Generates a yearly report
    - /today_expenses: Shows today's expenses
    - /weekly_expenses: Shows this week's expenses
    - /monthly_expenses [month] [year]: Shows this month's expenses
    - /old_expense (patter like expense with date at the end): Adds an old expense
    - /expense_help: Shows help for the expense command
    """
    await update.message.reply_text(help_text)

async def expense_help(update: Update, _):
    """
    Handles the expense command.
    """
    await update.message.reply_text("Pattern for expenses - [command category name shared amount]\n"
                                    "-Available categories:\n"
                                    "   food, cosmetics, hc-housecleaning, eo-eating out, cravings, alcohol\n"
                                    "-Shared:\n"
                                    "   yes or no\n"
                                    "today_expenses, weekly_expenses, monthly_expenses\n"
                                    "monthly_report, yearly_report\n")


def add_expense(name: str, category: str, shared: str, amount: float):
    """
    Adds a new expense.
    """
    if amount <= 0:
        return "Amount must be greater than 0"
    category_mapping = {
        "food": "food",
        "cosmetics": "cosmetics",
        "hc": "house cleaning",
        "eo": "eating out",
        "cravings": "cravings",
        "alcohol": "alcohol"
    }
    category = category_mapping.get(category, category)
    try:
        c.execute("INSERT INTO expenses (name, category, shared, amount, date) VALUES (?, ?, ?, ?, ?)",
                  (name, category, shared, amount, date.today().strftime('%d.%m.%Y')))
        if shared.lower() == "yes":
            c.execute("INSERT INTO shared_expenses (name, category, shared, amount, date) VALUES (?, ?, ?, ?, ?)",
                      (name, category, shared, amount, date.today().strftime('%d.%m.%Y')))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        return "Something went wrong with adding new expense"


def add_old_expense(name: str, category: str, shared: str, amount: float, expense_date: str):
    """
    Adds an old expense.
    """
    category_mapping = {
        "food": "food",
        "cosmetics": "cosmetics",
        "hc": "house cleaning",
        "eo": "eating out",
        "cravings": "cravings",
        "alcohol": "alcohol"
    }
    category = category_mapping.get(category, category)
    try:
        c.execute("INSERT INTO expenses (name, category, shared, amount, date) VALUES (?, ?, ?, ?, ?)",
                  (name, category, shared, amount, expense_date))
        if shared.lower() == "yes":
            c.execute("INSERT INTO shared_expenses (name, category, shared, amount, date) VALUES (?, ?, ?, ?, ?)",
                      (name, category, shared, amount, expense_date))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        return "Something went wrong with adding new expense"


def generate_weekly_expenses() -> str:
    """
    Generates weekly expenses.
    """
    with conn:
        c.execute("""
            SELECT * FROM expenses
            WHERE date BETWEEN strftime('%d.%m.%Y', date('now', 'weekday 0', '-7 days')) AND strftime('%d.%m.%Y', date('now'))
        """)
        rows = c.fetchall()
        if not rows:
            return "No expenses this week"
        else:
            with open('weekly_expenses.txt', 'w', encoding='utf-8') as f:
                for row in rows:
                    f.write(str(row) + '\n')
            return 'weekly_expenses.txt'


def generate_monthly_expenses() -> str:
    """
    Generates monthly expenses.
    """
    with conn:
        c.execute("""
                    SELECT * FROM expenses
                    WHERE date BETWEEN strftime('%d.%m.%Y', date('now', 'start of month')) AND strftime('%d.%m.%Y', date('now'))
                """)
        rows = c.fetchall()
        if not rows:
            return "No expenses this month"
        else:
            with open('monthly_expenses.txt', 'w', encoding='utf-8') as f:
                for row in rows:
                    f.write(str(row) + '\n')
            return 'monthly_expenses.txt'


async def delete_last_expense(update: Update, _):
    """
    Deletes the last expense.
    """
    try:
        c.execute("DELETE FROM expenses WHERE rowid = (SELECT MAX(rowid) FROM expenses)")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        return await update.message.reply_text("Something went wrong with deleting the last expense")
    return await update.message.reply_text("The last expense has been deleted")


async def send_file(update: Update, _, filename: str):
    """
    Sends a file to the Telegram chat.
    """
    # Send the file to the Telegram chat
    with open(filename, 'rb') as f:
        await _.bot.send_document(chat_id=update.message.chat_id, document=InputFile(f))

    os.remove(filename)


async def monthly_report_command(update: Update, _):
    processed: str = update.message.text.lower()
    parts = processed.split()
    if len(parts) != 3:
        return await update.message.reply_text(
            "Please provide a month and a year in the format 'monthly_report month year'")
    try:
        month = int(parts[1])
        year = int(parts[2])
    except ValueError:
        return await update.message.reply_text("Month and year should be numbers")
    generate_monthly_reports(month, year)
    return await send_file(update, _, 'monthly_reports.docx') or "File sent successfully"


async def yearly_report_command(update: Update, _):
    processed: str = update.message.text.lower()
    year = processed.split()[1]
    generate_yearly_reports(year)
    return await send_file(update, _, '../yearly_reports.docx') or "File sent successfully"


async def today_expenses_command(update: Update, _):
    with conn:
        c.execute("SELECT * FROM expenses WHERE date = ?", (date.today().strftime('%d.%m.%Y'),))
        rows = c.fetchall()
        if not rows:
            return await update.message.reply_text("No expenses today")
        else:
            return await update.message.reply_text('\n'.join(map(str, rows)))


async def weekly_expenses_command(update: Update, _):
    filename = generate_weekly_expenses()
    if filename == "No expenses this week":
        return await update.message.reply_text(filename)
    else:
        return await send_file(update, _, filename) or "File sent successfully"


async def monthly_expenses_command(update: Update, _):
    filename = generate_monthly_expenses()
    if filename == "No expenses this month":
        return await update.message.reply_text(filename)
    else:
        return await send_file(update, _, filename) or "File sent successfully"


async def old_expense_command(update: Update, _):
    processed: str = update.message.text.lower()
    try:
        name = processed.split()[2:-3]
        name = ' '.join([str(elem) for elem in name])
        expense_date = processed.split()[-1]
        add_old_expense(name, processed.split()[1], processed.split()[-3], int(processed.split()[-2]), expense_date)
    except Exception as e:
        return await update.message.reply_text("Something went wrong with adding your old expense")
    return await update.message.reply_text("Your old expense has been added")


async def expense_command(update: Update, _):
    processed: str = update.message.text.lower()
    try:
        name = processed.split()[2:-2]
        name = ' '.join([str(elem) for elem in name])
        add_expense(name, processed.split()[1], processed.split()[-2], int(processed.split()[-1]))
    except:
        return await update.message.reply_text("Something went wrong with adding your expense")
    return await update.message.reply_text("Your expense has been added")


async def error(update: Update, _):
    """
    Handles the error.
    """
    print(f"Update {update} caused error {_.error}")


async def handle_message(update: Update, _):
    """
    Handles the message.
    """
    text: str = update.message.text

    # Check if the message is not a command
    if not text.startswith('/'):
        print(f"User ({update.message.chat.id}) said: '{text}'")
        await update.message.reply_text("I don't understand your command.")


if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
    conn = sqlite3.connect('data/expenses.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
               name text,
               category text,
               shared text,
               amount integer,
               date text)""")
    c.execute("""CREATE TABLE IF NOT EXISTS shared_expenses (
                    name text,
                    category text,
                    shared text,
                    amount integer,
                    date text)""")
    conn.commit()
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('expense', expense_command))
    app.add_handler(CommandHandler('delete_last_expense', delete_last_expense))
    app.add_handler(CommandHandler('monthly_report', monthly_report_command))
    app.add_handler(CommandHandler('yearly_report', yearly_report_command))
    app.add_handler(CommandHandler('today_expenses', today_expenses_command))
    app.add_handler(CommandHandler('weekly_expenses', weekly_expenses_command))
    app.add_handler(CommandHandler('monthly_expenses', monthly_expenses_command))
    app.add_handler(CommandHandler('old_expense', old_expense_command))
    app.add_handler(CommandHandler('expense_help', expense_help))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    print("Polling...")
    app.add_error_handler(error)

    app.run_polling(poll_interval=3)

    conn.close()
