from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import taskmanager
import asyncio

TOKEN = "8882573760:AAHQ6PlNG3zg7yUwv51z-FnP9W9tt3JlFDE"

(
    ADD_TITLE,
    SEARCH,
    EDIT_TITLE,
    EDIT_LEVEL,
    SELECT_TASK,
) = range(5)


async def auto_delete(message, delay=10):
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except:
        pass


def main_menu():
    keyboard = [

        [
            InlineKeyboardButton(
                "➕ افزودن فعالیت",
                callback_data="add"
            ),

            InlineKeyboardButton(
                "📋 لیست فعالیت‌ها",
                callback_data="list"
            )
        ],

        [
            InlineKeyboardButton(
                "✅ انجام شده",
                callback_data="done_list"
            ),

            InlineKeyboardButton(
                "⏳ انجام نشده",
                callback_data="undone_list"
            )
        ],

        [
            InlineKeyboardButton(
                "🔍 جستجو",
                callback_data="search"
            ),

            InlineKeyboardButton(
                "📊 آمار",
                callback_data="stats"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف همه فعالیت‌ها",
                callback_data="delete_all"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ درباره ربات",
                callback_data="about"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


def get_user_id(update):
    return update.effective_user.id


async def save_message(context, message):
    if "messages" not in context.user_data:
        context.user_data["messages"] = []

    context.user_data["messages"].append(message.message_id)


async def delete_messages(update, context):
    ids = context.user_data.get("messages", [])

    for msg_id in ids:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=msg_id
            )
        except:
            pass

    context.user_data["messages"] = []

async def show_tasks(update, context, tasks, title="📋 لیست فعالیت‌ها", mode="all"):
    context.user_data["current_tasks"] = tasks
    context.user_data["current_mode"] = mode

    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    if len(tasks) == 0:
        await message.reply_text(
            "❌ هیچ فعالیتی وجود ندارد.",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    numbers = [
        "1️⃣","2️⃣","3️⃣","4️⃣","5️⃣",
        "6️⃣","7️⃣","8️⃣","9️⃣","🔟"
    ]

    text = f"✨ {title}\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    for i, task in enumerate(tasks):

        if task["level"] == "high":
            level = "🔴 زیاد"

        elif task["level"] == "medium":
            level = "🟠 متوسط"

        else:
            level = "🟢 کم"

        status = "✅ انجام شده" if task["done"] else "⏳ انجام نشده"

        number = numbers[i] if i < 10 else f"{i+1}."

        text += (
            f"{number} {task['title']}\n"
            f"┣ 🏷 اولویت : {level}\n"
            f"┣ {status}\n"
            f"┗ 📅 {task['created_at']}\n"
            "━━━━━━━━━━━━━━━━━━\n"
        )

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "یکی از گزینه‌های زیر را انتخاب کنید."

    keyboard = [

        [
            InlineKeyboardButton(
                "🎯 انتخاب فعالیت",
                callback_data="select_task"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 بازگشت به منو",
                callback_data="back_menu"
            )
        ]

    ]

    await message.reply_text(

        text,

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

    return ConversationHandler.END



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Welcome to Task Manager Bot\n\n"
        "Manage your daily activities easily.\n\n"
        "Choose an option:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "cancel_action":

        try:
            await query.message.delete()

            temp = context.user_data.get("temp_message")

            if temp:
                await context.bot.delete_message(
                    chat_id=query.message.chat.id,
                    message_id=temp
                )

        except:
            pass

        context.user_data.clear()

        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="🏠 منوی اصلی",
            reply_markup=main_menu()
        )

        return ConversationHandler.END



    elif data == "back_menu":

        await query.message.delete()

        await query.message.reply_text(
            "🏠 منوی اصلی",
            reply_markup=main_menu()
        )

        return ConversationHandler.END

    # ---------------- انتخاب اولویت ----------------

    if data.startswith("level_"):
        return await choose_level(update, context)
    if data in ["edit_high", "edit_medium", "edit_low"]:

        return await choose_edit_level(update, context)


    # ---------------- افزودن فعالیت ----------------

    elif data == "add":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🔙 لغو",

                    callback_data="cancel_action"

                )

            ]

        ]
        await delete_messages(update, context)
        msg = await query.message.reply_text(
            "📝 عنوان فعالیت را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await save_message(context, msg)
        context.user_data["temp_message"] = msg.message_id

        return ADD_TITLE


    elif data == "search":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🔙 لغو",

                    callback_data="cancel_action"

                )

            ]

        ]
        await delete_messages(update, context)
        msg = await query.message.reply_text(
            "🔍 کلمه مورد نظر برای جستجو را ارسال کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await save_message(context, msg)

        context.user_data["temp_message"] = msg.message_id

        return SEARCH



    # ---------------- حذف همه فعالیت ها ----------------

    elif data == "delete_all":

        tasks = taskmanager.show_all_tasks(

            get_user_id(update)

        )

        if len(tasks) == 0:
            message = await query.message.reply_text(

                "❌ هیچ فعالیتی برای حذف وجود ندارد."

            )

            await asyncio.sleep(3)

            await message.delete()

            return ConversationHandler.END

        keyboard = [

            [

                InlineKeyboardButton(

                    "✅ بله، حذف شود",

                    callback_data="confirm_delete_all"

                ),

                InlineKeyboardButton(

                    "❌ خیر",

                    callback_data="cancel_delete_all"

                )

            ]

        ]

        await query.message.reply_text(

            "⚠️ آیا مطمئن هستید؟\n"

            "تمام فعالیت‌ها حذف خواهند شد.",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )

        return ConversationHandler.END





    elif data == "confirm_delete_all":

        taskmanager.delete_all_tasks(

            get_user_id(update)

        )

        await query.message.delete()

        message = await query.message.reply_text(

            "✅ همه فعالیت‌ها حذف شدند."

        )

        await asyncio.sleep(3)

        await message.delete()

        return ConversationHandler.END


    elif data == "cancel_delete_all":

        await query.message.delete()

        await query.message.reply_text(
            "❎ حذف همه فعالیت‌ها لغو شد.",
            reply_markup=main_menu()
        )

        return ConversationHandler.END
    # ---------------- لیست فعالیت ها ----------------

    elif data == "list":

        tasks = taskmanager.show_all_tasks(

            get_user_id(update)

        )

        await query.message.delete()

        return await show_tasks(
            update,
            context,
            tasks,
            "🔄 لیست به‌روز شده",
            "all"
        )




    elif data.startswith("task_"):

        number = int(

            data.split("_")[1]

        )

        task = context.user_data["current_tasks"][number - 1]
        mode = context.user_data.get("current_mode", "all")

        keyboard = []

        if mode != "done":
            keyboard.append([
                InlineKeyboardButton(
                    "✅ انجام شد",
                    callback_data=f"done_{number}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=f"edit_{number}"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                "🗑 حذف",
                callback_data=f"delete_{number}"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                "🏠 منو",
                callback_data="back_menu"
            )
        ])

        await query.message.reply_text(

            f"📌 {task['title']}\n\n"

            "یکی از عملیات زیر را انتخاب کنید.",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )

        return ConversationHandler.END




    # ---------------- انجام شدن فعالیت ----------------

    elif data.startswith("done_") and data.split("_")[1].isdigit():

        index = int(data.split("_")[1])

        result = taskmanager.mark_task_done(

            get_user_id(update),

            index

        )

        if result == True:

            await query.answer(

                "✅ انجام شد",

                show_alert=False

            )

            # حذف پیام قبلی

            await query.message.delete()

            # گرفتن لیست جدید

            tasks = taskmanager.show_all_tasks(

                get_user_id(update)

            )

            # نمایش لیست جدید

            return await show_tasks(
                update,
                context,
                tasks,
                "🔄 لیست به‌روز شده",
                "all"
            )

            # منوی اصلی

            await query.message.reply_text(

                "🏠 منوی اصلی",

                reply_markup=main_menu()

            )



        elif result == "already":

            await query.answer(

                "این فعالیت قبلاً انجام شده است.",

            )



        else:

            await query.answer(

                "❌ خطا در انجام عملیات.",

            )

        return ConversationHandler.END
    # ---------------- حذف فعالیت ----------------

    elif data.startswith("delete_") and data.split("_")[1].isdigit():

        index = int(data.split("_")[1])

        keyboard = [

            [

                InlineKeyboardButton(

                    "✅ بله",

                    callback_data=f"confirm_delete_{index}"

                ),

                InlineKeyboardButton(

                    "❌ خیر",

                    callback_data="cancel_delete"

                )

            ]

        ]

        await query.message.reply_text(

            "❓ از حذف این فعالیت مطمئن هستید؟",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )

        return ConversationHandler.END
    # ---------------- ویرایش ----------------

    elif data.startswith("edit_") and data.split("_")[1].isdigit():

        index = int(data.split("_")[1])

        context.user_data["edit_index"] = index

        keyboard = [

            [

                InlineKeyboardButton(

                    "🔙 لغو",

                    callback_data="cancel_action"

                )

            ]

        ]
        await delete_messages(update, context)
        msg = await query.message.reply_text(
            "📝 عنوان جدید را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await save_message(context, msg)
        context.user_data["temp_message"] = msg.message_id

        return EDIT_TITLE





    elif data.startswith("confirm_delete_"):

        index = int(data.split("_")[2])

        result = taskmanager.delete_task(

            get_user_id(update),

            index

        )

        if result:

            await query.answer(

                "🗑 حذف شد"

            )

            # حذف پیام تایید حذف

            await query.message.delete()

            # گرفتن لیست جدید

            tasks = taskmanager.show_all_tasks(

                get_user_id(update)

            )

            return await show_tasks(
                update,
                context,
                tasks,
                "🔄 لیست به‌روز شده",
                "all"
            )



        else:

            await query.answer(

                "❌ حذف انجام نشد"

            )

        return ConversationHandler.END






    elif data == "cancel_delete":

        await query.edit_message_text(

            "❎ حذف لغو شد.",

            reply_markup=main_menu()

        )

        return ConversationHandler.END


    # ---------------- نمایش انجام شده ها ----------------

    elif data == "done_list":

        tasks = taskmanager.show_done_task(

            get_user_id(update)

        )

        await query.message.delete()

        return await show_tasks(
            update,
            context,
            tasks,
            "✅ فعالیت‌های انجام شده",
            "done"
        )




    elif data == "undone_list":

        tasks = taskmanager.show_undone_task(

            get_user_id(update)

        )
        await query.message.delete()
        return await show_tasks(
            update,
            context,
            tasks,
            "⏳ فعالیت‌های انجام نشده",
            "undone"
        )








    elif data == "select_task":

        tasks = context.user_data.get("current_tasks", [])

        if len(tasks) == 0:
            await query.answer(

                "❌ فعالیتی وجود ندارد."

            )

            return ConversationHandler.END

        keyboard = []

        emojis = [

            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣",

            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"

        ]

        for i in range(len(tasks)):

            if i < 10:

                text = emojis[i]


            else:

                text = str(i + 1)

            keyboard.append(

                [

                    InlineKeyboardButton(

                        text,

                        callback_data=f"task_{i + 1}"

                    )

                ]

            )

        keyboard.append(

            [

                InlineKeyboardButton(

                    "🏠 بازگشت به منو",

                    callback_data="back_menu"

                )

            ]

        )

        await query.message.reply_text(

            "👇 فعالیت مورد نظر را انتخاب کنید.",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )

        return ConversationHandler.END

    # ---------------- درباره ربات ----------------

    elif data == "about":

        await query.edit_message_text(

            "🤖 Task Manager Bot\n\n"

            "Created by:\n"
            "MatinAlinaghian\n\n"

            "Built with Python 🐍\n\n"

            "Created on:\n"
            "30 Tir 1405",

            reply_markup=main_menu()

        )

        return ConversationHandler.END

    # ---------------- آمار ----------------

    elif data == "stats":

        all_tasks = taskmanager.show_all_tasks(
            get_user_id(update)
        )

        total = len(all_tasks)

        if total == 0:
            await query.edit_message_text(

                "❌ هنوز فعالیتی ثبت نشده.",

                reply_markup=main_menu()

            )

            return ConversationHandler.END

        done = 0

        for task in all_tasks:

            if task["done"]:
                done += 1

        undone = total - done

        percent = (done / total) * 100

        await query.edit_message_text(

            "📊 آمار فعالیت‌ها\n\n"

            f"📌 کل فعالیت‌ها: {total}\n"

            f"✅ انجام شده: {done}\n"

            f"❌ انجام نشده: {undone}\n\n"

            f"📈 درصد انجام موفقیت: {percent:.1f}%",

            reply_markup=main_menu()

        )

        return ConversationHandler.END


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()

    if title == "":
        await update.message.reply_text(
            "❌ عنوان نمی‌تواند خالی باشد.\n\nدوباره وارد کنید:"
        )
        return ADD_TITLE

    context.user_data["title"] = title

    keyboard = [

        [
            InlineKeyboardButton(
                "🔴 زیاد",
                callback_data="level_high"
            )
        ],

        [
            InlineKeyboardButton(
                "🟠 متوسط",
                callback_data="level_medium"
            )
        ],

        [
            InlineKeyboardButton(
                "🟡 کم",
                callback_data="level_low"
            )
        ]

    ]

    await update.message.reply_text(

        f"📌 عنوان فعالیت:\n{title}\n\n"
        "اولویت را انتخاب کنید.",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

    return ADD_TITLE


async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    title = context.user_data.get("title")

    if title is None:
        await query.edit_message_text(
            "❌ اطلاعات فعالیت پیدا نشد."
        )

        return ConversationHandler.END

    if query.data == "level_high":

        level = "high"
        emoji = "🔴"

    elif query.data == "level_medium":

        level = "medium"
        emoji = "🟠"

    else:

        level = "low"
        emoji = "🟡"

    taskmanager.add_task(
        get_user_id(update),
        title,
        level
    )

    del context.user_data["title"]

    await query.message.reply_text(
        "✅ فعالیت ثبت شد."
    )

    tasks = taskmanager.show_all_tasks(
        get_user_id(update)
    )

    await show_tasks(
        update,
        context,
        tasks,
        "📋 لیست فعالیت‌ها",
        "all"
    )

    await query.message.reply_text(
        "🏠 منوی اصلی",
        reply_markup=main_menu()
    )

    return ConversationHandler.END


async def receive_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = update.message.text.strip()

    result = taskmanager.search_task(
        get_user_id(update),
        word
    )

    if len(result) == 0:
        await update.message.reply_text(

            "❌ فعالیتی پیدا نشد.",

            reply_markup=main_menu()

        )

        return ConversationHandler.END

    return await show_tasks(
        update,
        context,
        result,
        f"🔍 نتیجه جستجوی «{word}»",
        "search"
    )


async def receive_edit_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()

    if title == "":
        await update.message.reply_text(
            "❌ عنوان نمی‌تواند خالی باشد."
        )

        return EDIT_TITLE

    context.user_data["new_title"] = title

    keyboard = [

        [

            InlineKeyboardButton(
                "🔴 زیاد",
                callback_data="edit_high"
            )

        ],

        [

            InlineKeyboardButton(
                "🟠 متوسط",
                callback_data="edit_medium"
            )

        ],

        [

            InlineKeyboardButton(
                "🟡 کم",
                callback_data="edit_low"
            )

        ]

    ]

    await update.message.reply_text(

        "اولویت جدید را انتخاب کنید.",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )

    return EDIT_LEVEL


async def choose_edit_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    index = context.user_data["edit_index"]

    title = context.user_data["new_title"]

    if query.data == "edit_high":

        level = "high"
        emoji = "🔴"

    elif query.data == "edit_medium":

        level = "medium"
        emoji = "🟠"

    else:

        level = "low"
        emoji = "🟡"

    result = taskmanager.edit_task(
        get_user_id(update),
        index,
        title,
        level
    )

    context.user_data.clear()

    if result:

        await query.answer(
            "✏️ ویرایش شد"
        )

        # حذف پیام انتخاب اولویت
        await query.message.delete()

        tasks = taskmanager.show_all_tasks(
            get_user_id(update)
        )

        return await show_tasks(
            update,
            context,
            tasks,
            "🔄 لیست به‌روز شده",
            "all"
        )
    else:

        await query.edit_message_text(

            "❌ خطا در ویرایش.",

            reply_markup=main_menu()

        )

    return ConversationHandler.END

async def receive_task_number(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        number = int(update.message.text.strip())


    except ValueError:

        await update.message.reply_text(
            "❌ لطفاً فقط شماره فعالیت را وارد کنید."
        )

        return SELECT_TASK

    tasks = taskmanager.show_all_tasks(
        get_user_id(update)
    )

    if tasks is None:

        await update.message.reply_text(
            "❌ لیست فعالیت‌ها پیدا نشد."
        )

        return SELECT_TASK


    if number < 1 or number > len(tasks):

        await update.message.reply_text(
            "❌ شماره وارد شده اشتباه است."
        )

        return SELECT_TASK


    task = tasks[number - 1]


    await update.message.reply_text(

        f"📌 فعالیت انتخاب شده:\n\n"
        f"{task['title']}\n\n"
        "چه کاری می‌خواهید انجام دهید؟"

    )


    keyboard = [

        [
            InlineKeyboardButton(
                "✅ انجام شد",
                callback_data=f"done_{number}"
            )
        ],

        [
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=f"edit_{number}"
            )
        ],

        [
            InlineKeyboardButton(
                "🗑 حذف",
                callback_data=f"delete_{number}"
            )
        ]

    ]


    await update.message.reply_text(

        "انتخاب کنید:",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


    return ConversationHandler.END

application = ApplicationBuilder().token(TOKEN).build()

conversation = ConversationHandler(
    allow_reentry=True,

    entry_points=[
        CallbackQueryHandler(buttons)
    ],

    states={

        ADD_TITLE: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_title
            ),

            CallbackQueryHandler(
                choose_level,
                pattern="^level_(high|medium|low)$"
            ),

            CallbackQueryHandler(
                buttons,
                pattern="^cancel_action$"
            )

        ],

        SEARCH: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_search
            ),

            CallbackQueryHandler(
                buttons,
                pattern="^cancel_action$"
            )

        ],

        EDIT_TITLE: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_edit_title
            ),

            CallbackQueryHandler(
                buttons,
                pattern="^cancel_action$"
            )

        ],

        EDIT_LEVEL: [

            CallbackQueryHandler(
                choose_edit_level,
                pattern="^edit_(high|medium|low)$"
            )

        ],
        SELECT_TASK: [

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_task_number
            ),

            CallbackQueryHandler(
                buttons
            )

        ]


    },

    fallbacks=[
        CommandHandler("start", start)
    ]

)

application.add_handler(
    CommandHandler("start", start)
)

application.add_handler(conversation)


async def error_handler(update, context):
    print(
        f"ERROR: {context.error}"
    )


application.add_error_handler(
    error_handler
)
print("Bot Started...")

application.run_polling()
