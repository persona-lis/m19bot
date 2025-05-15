from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.exception_factory import VKAPIError
from colorama import init, Fore, Style
init(autoreset=True)  # Инициализация colorama, чтобы цвет сбрасывался после строки



BOT_TOKEN = "vk1.a._jxR-GVP8nf_sbVzF-oJ7c6fX_GtJCtygYo7rWwkKEGV3XBCxwq_M0pIQ58F9sxA9jC0YrNBfEqo88YIfosV6DFP-YNIAsOFBctnvFznBebMvrJJYMEF5g2_sTmftT9FTUVR2SU3QMVCxEc6LpBI3rz2hUX7Dgkawgihj5mBjvnh8VkbAUK056TMQ0KagvNbJ9sx4s7882ArFEzQ20IvvQ"
GROUP_CHAT_ID = 2000000001  # сюда отправлять объявления

bot = Bot(token=BOT_TOKEN)

# --- Клавиатуры ---
main_keyboard = (
    Keyboard(inline=True)
    .add(Text("Продам"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("Куплю"), color=KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("Сотрудничество"), color=KeyboardButtonColor.SECONDARY)
    .add(Text("Предложить новость"), color=KeyboardButtonColor.SECONDARY)
)

categories_keyboard = (
    Keyboard(inline=True)
    .add(Text("Автомобиль"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("Недвижимость"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Аксессуар"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("Бизнес"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Отмена"), color=KeyboardButtonColor.NEGATIVE)
)

real_estate_keyboard = (
    Keyboard(inline=True)
    .add(Text("Дом"), color=KeyboardButtonColor.PRIMARY)
    .add(Text("Квартира"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Бизнес-объект"), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
)

extra_info_keyboard = (
    Keyboard(inline=True)
    .add(Text("Не указывать"), color=KeyboardButtonColor.NEGATIVE)
)

# --- Хранилище состояний ---
user_states = {}

def reset_user_state(user_id: int):
    user_states[user_id] = {
        "action": None,
        "category": None,
        "real_estate_type": None,
        "title": None,
        "price": None,
        "extra_info": None,
        "awaiting_title": False,
        "awaiting_price": False,
        "awaiting_extra_info": False
    }

# --- Хэндлеры ---

@bot.on.message(text="/start")
async def start_handler(message: Message):
    reset_user_state(message.from_id)
    await message.answer(
        "👋 Приветствую! Я бот-поддержки.\nТут ты можешь выбрать, по какой причине хочешь обратиться и подождать ответа от Агентов Редакции.\nНажми на кнопки ниже для выбора.",
        keyboard=main_keyboard
    )


@bot.on.message(text=["Продам", "Куплю"])
async def action_handler(message: Message):
    user_id = message.from_id
    reset_user_state(user_id)
    user_states[user_id]["action"] = message.text
    await message.answer(
        f"Вы выбрали: {message.text}. Выберите категорию:",
        keyboard=categories_keyboard
    )

@bot.on.message(text="Сотрудничество")
async def cooperation_handler(message: Message):
    reset_user_state(message.from_id)
    await message.answer(
        "Спасибо за интерес к сотрудничеству! Расскажите о желаемом сотрудничестве, например конкурсе или рекламном посте.\nОповестили Модератора Редакции M19, ожидайте ответа.",
    )

@bot.on.message(text="Предложить новость")
async def editor_handler(message: Message):
    reset_user_state(message.from_id)
    await message.answer(
        "Отправьте интересную новость связанную с Матрешкой. Благодарим за контент!\nОповестили Агентов Редакции М19, ожидайте ответа.",
    )

@bot.on.message(text="Отмена")
async def cancel_handler(message: Message):
    reset_user_state(message.from_id)
    await message.answer("Отменено. Главное меню:", keyboard=main_keyboard)

@bot.on.message(text="Назад")
async def back_handler(message: Message):
    user_id = message.from_id
    state = user_states.get(user_id)
    if state and state["category"] == "Недвижимость":
        await message.answer("Выберите тип недвижимости:", keyboard=real_estate_keyboard)
    else:
        await message.answer("Главное меню:", keyboard=main_keyboard)

@bot.on.message(text=["Автомобиль", "Недвижимость", "Аксессуар", "Бизнес"])
async def category_handler(message: Message):
    user_id = message.from_id
    state = user_states.get(user_id)
    if not state or not state["action"]:
        await message.answer("Сначала выберите действие (Продам/Куплю).", keyboard=main_keyboard)
        return

    category = message.text
    user_states[user_id]["category"] = category

    if category == "Недвижимость":
        await message.answer("Выберите тип недвижимости:", keyboard=real_estate_keyboard)
    else:
        await message.answer("Введите название имущества (например, модель авто, название аксессуара и т.д.):")
        user_states[user_id]["awaiting_title"] = True

@bot.on.message(text=["Дом", "Квартира", "Бизнес-объект"])
async def real_estate_type_handler(message: Message):
    user_id = message.from_id
    user_states[user_id]["real_estate_type"] = message.text
    await message.answer("Введите название объекта:")
    user_states[user_id]["awaiting_title"] = True

@bot.on.message(text="Не указывать")
async def skip_extra_info_handler(message: Message):
    user_id = message.from_id
    user_states[user_id]["extra_info"] = ""
    user_states[user_id]["awaiting_extra_info"] = False
    await send_announcement(user_id, message)

@bot.on.message()
async def text_handler(message: Message):
    user_id = message.from_id
    state = user_states.get(user_id)

    if not state:
        await message.answer("Напишите /start чтобы начать работу с ботом.", keyboard=main_keyboard)
        return

    # Ждём название
    if state.get("awaiting_title"):
        user_states[user_id]["title"] = message.text
        user_states[user_id]["awaiting_title"] = False
        await message.answer("Укажите цену (цифрами, например: 400000):")
        user_states[user_id]["awaiting_price"] = True
        return

    # Ждём цену
    if state.get("awaiting_price"):
        price_text = message.text.replace(" ", "").replace("К", "000").replace("к", "000").replace("K", "000").replace("k", "000")
        if not price_text.isdigit():
            await message.answer(
                "Введите цену цифрами, например: 400000\nЕсли договорная, то напишите здесь любую сумму и укажите в доп. информации."
            )
            return
        user_states[user_id]["price"] = price_text
        user_states[user_id]["awaiting_price"] = False

        if state["category"] != "Недвижимость":
            await message.answer(
                "Укажите дополнительную информацию (можно оставить пустым):",
                keyboard=extra_info_keyboard
            )
            user_states[user_id]["awaiting_extra_info"] = True
        else:
            # Для недвижимости отправляем объявление сразу (т.к. доп. инфо пока не запрашиваем)
            await send_announcement(user_id, message)
        return

    # Ждём доп. информацию
    if state.get("awaiting_extra_info"):
        user_states[user_id]["extra_info"] = message.text
        user_states[user_id]["awaiting_extra_info"] = False
        await send_announcement(user_id, message)
        return

    await message.answer("Пожалуйста, выберите действие из меню или используйте /start для начала.", keyboard=main_keyboard)

# --- Функция безопасной отправки с ловлей ошибок ---
async def safe_send(peer_id, **kwargs):
    try:
        await bot.api.messages.send(peer_id=peer_id, random_id=0, **kwargs)
    except VKAPIError as e:
        # Игнорируем ошибку 901 - пользователь запретил сообщения
        if e.code == 901:
            print(f"VKAPIError 901: Нельзя отправлять сообщения пользователю {peer_id}")
        else:
            print(f"VKAPIError {e.code}: {e}")

async def send_announcement(user_id: int, message: Message):
    state = user_states[user_id]

    action = state["action"]
    title = state["title"]
    price = state["price"]
    extra = state.get("extra_info", "").strip()
    category = state["category"]
    real_estate_type = state.get("real_estate_type", "")

    announcement = f"🆕 {action} "

    if category == "Недвижимость" and real_estate_type:
        announcement += f"{real_estate_type} «{title}»\n"
    else:
        announcement += f"{category} «{title}»\n"

    announcement += f"\n🪙 Цена - {price}\n"

    if extra and extra.lower() != "не указывать":
        announcement += f"\nℹ Дополнительно: {extra}\n"

    announcement += f"\n📞 Связь - https://vk.com/id{user_id}"

    await safe_send(
        peer_id=GROUP_CHAT_ID,
        message=announcement,
        keyboard=main_keyboard.get_json()  # обязательно в json
    )
    await message.answer("Объявление отправлено! Спасибо.", keyboard=main_keyboard)
    reset_user_state(user_id)

if __name__ == "__main__":
    print(Fore.GREEN + f"Запускаю бота...")
    bot.run_forever()
