from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# وضعیت‌ها
ADDING_NAMES, ADDING_COSTS = range(2)

# دیتا موقت
participants = []
expenses = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, expenses
    participants = []
    expenses = {}
    await update.message.reply_text(
        "سلام! 👋 برای شروع اسم شرکت‌کننده‌ها رو یکی یکی بفرست. وقتی تموم شد، کلمه 'تمام' رو بفرست."
    )
    return ADDING_NAMES

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants
    name = update.message.text.strip()
    if name == "تمام":
        if not participants:
            await update.message.reply_text("هیچ اسمی وارد نکردی. لطفاً حداقل یک اسم بده.")
            return ADDING_NAMES
        await update.message.reply_text("حالا به ترتیب هزینه‌ی هر نفر رو بفرست.")
        return ADDING_COSTS
    participants.append(name)
    await update.message.reply_text(f"اسم '{name}' اضافه شد. اسم بعدی؟ (یا 'تمام')")

    return ADDING_NAMES

async def add_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, expenses
    try:
        cost = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return ADDING_COSTS

    name = participants[len(expenses)]
    expenses[name] = cost

    if len(expenses) < len(participants):
        next_name = participants[len(expenses)]
        await update.message.reply_text(f"هزینه‌ی پرداخت شده توسط {next_name} رو بفرست:")
        return ADDING_COSTS
    else:
        # همه هزینه‌ها وارد شدن
        result_text, file_path = calculate_settlements()
        await update.message.reply_text(result_text)
        # ارسال فایل فاکتور
        with open(file_path, 'rb') as f:
            await update.message.reply_document(document=InputFile(f), filename="settlement.txt")
        return ConversationHandler.END

def calculate_settlements():
    total = sum(expenses.values())
    share = total / len(participants)

    balances = {name: round(expenses[name] - share, 2) for name in participants}

    debtors = [(name, -balance) for name, balance in balances.items() if balance < 0]
    creditors = [(name, balance) for name, balance in balances.items() if balance > 0]

    debtors.sort(key=lambda x: x[1])
    creditors.sort(key=lambda x: x[1])

    text = f"💰 هزینه کل: {total:.0f} تومان\n🧮 سهم هر نفر: {share:.0f} تومان\n\n"
    text += "🔻 تسویه حساب:\n"

    file_content = text  # محتوای فایل فاکتور

    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt_amount = debtors[i]
        creditor, credit_amount = creditors[j]

        payment = min(debt_amount, credit_amount)
        line = f"👉 {debtor} باید {payment:.0f} تومان به {creditor} پرداخت کند.\n"
        text += line
        file_content += line

        debtors[i] = (debtor, debt_amount - payment)
        creditors[j] = (creditor, credit_amount - payment)

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    # ذخیره فایل
    file_path = "settlement.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    return text, file_path

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرآیند لغو شد. ❌")
    return ConversationHandler.END

def main():
    # اینجا توکن رباتت رو جایگزین کن
    TOKEN = "7640915414:AAFo5mLiAJUzrr6Ee_jkYfYs8mewafSS6oQ"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ADDING_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADDING_COSTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_cost)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
