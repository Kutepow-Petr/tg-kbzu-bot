import telebot
from telebot import types
from typing import Optional, Tuple
from User import User
from Product import Product
from databases.services.MealsDatabase import MealsDatabase
from databases.services.FoodDatabase import FoodDatabase
from utils.OpenFoodFacts import OpenFoodFacts
from utils.Statistic import Statistic

class FoodManager:
    def __init__(self, bot: telebot.TeleBot, meals_db: MealsDatabase, food_db:FoodDatabase):
        self.bot = bot
        self.meals_db = meals_db
        self.food_db = food_db
        self.users_meals = {}
        self.product_searcher = OpenFoodFacts()
        self._setup_handlers()



    def add_food_manually(self, chat_id: int, user: User):
        self.users_meals[chat_id] = [user,]
        message = self.bot.send_message(
            chat_id,
            f"<b>Добавление нового продукта</b>\n\n"
            f"Что нужно указать:\n"
            f"1️⃣ Название — как называется продукт\n"
            f"2️⃣ КБЖУ на 100г — 4 числа через пробел\n"
            f"3️⃣ Съеденное количество — в граммах\n\n"
            f"📊 Например:\n"
            f"  <em>творог\n"
            f"  121 17.2 5 3.4\n"
            f"  100</em>\n",
            parse_mode="html"
        )
        self.bot.register_next_step_handler(message, self.ask_adding_food)

    def ask_adding_food(self, message):
        chat_id = message.chat.id
        product, amount = self._parse_user_food(message.text)
        if product:
            self.users_meals[chat_id].extend([amount, product])
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
                types.InlineKeyboardButton("✅ Добавить", callback_data="add_food")
            )
            self.bot.send_message(
                chat_id,
                f"❓ <b>Добавить продукт?</b>\n\n"
                f"Название: {product.name}\n"
                f"Калорий: {product.calories} ккал\n"
                f"Белков: {product.proteins} г\n"
                f"Жиров: {product.fats} г\n"
                f"Углеводов: {product.carbs} г\n",
                parse_mode="html",
                reply_markup=markup
            )
        else:
            message = self.bot.send_message(
                chat_id,
                f"🤔 Не понял формат…\n"
                f"<b>Нужно:</b>\n"
                f"  Название — как называется продукт\n"
                f"  КБЖУ на 100г — 4 числа через пробел\n"
                f"  Съеденное количество — в граммах\n\n"
                f"✅ Правильно:\n"
                f"  <em>творог\n"
                f"  121 17.2 5 3.4\n"
                f"  100</em>\n"
                f"❌ Неправильно:\n"
                f"  (без названия)\n"
                f"  <em>121 17.2</em> (пропущены нутриенты)\n"
                f"  (без количества)\n"
                f"Попробуй еще раз!",
                parse_mode="html")
            self.bot.register_next_step_handler(message, self.ask_adding_food)

    def ask_to_delete_meal(self, chat_id, user_id):
        meals_per_day = self.meals_db.get_today_meals(user_id)
        if len(meals_per_day) == 0:
            self.bot.send_message(chat_id, "Сегодня вы ещё ничего не ели")
        else:
            markup = types.InlineKeyboardMarkup()
            for i, meal in enumerate(meals_per_day):
                markup.add(
                    types.InlineKeyboardButton(
                        f"{i + 1}. {meal[0].name}: {meal[1]} гр",
                        callback_data=f"delete_meal_{user_id}_{meal[2]}"
                    )
                )
            
            markup.add(
                types.InlineKeyboardButton(f"❌ Отмена", callback_data="cancel")
            )
            self.bot.send_message(chat_id, "Что удалить?", reply_markup=markup)

    def add_meal(self, message, user: User, amount: float, product: Product):
        chat_id = message.chat.id
        if self.meals_db.add_meal(user.user_id, product, amount):

            today_meals = self.meals_db.get_today_meals(user.user_id)

            self.bot.edit_message_text(
                f"✅ <b>Добавлено</b>\n"
                f"{Statistic.today(user, today_meals)}",
                chat_id,
                message.message_id,
                parse_mode="html"
            )
        else:
            self.bot.edit_message_text(
                f"⚠️ Не удалось сохранить приём пищи. Попробуй снова",
                chat_id,
                message.message_id,
            )
        del self.users_meals[chat_id]
        
    def search_food(self, message, user: User):
        chat_id = message.chat.id
        self.users_meals[chat_id] = [user,]
        product_name, amount = self._parse_user_meal(message.text)

        if product_name:
            self.users_meals[chat_id].extend([amount, []])
            message = self.bot.send_message(chat_id, "🔎 Ищу продукты…")
            self._search_food_in_database(message, product_name)
        else:
            self.bot.send_message(
                chat_id,
                f"🤔 Не понял формат…\n"
                f"<b>Нужно: название продукта + количество</b>\n"
                f"✅ Правильно:\n"
                f"  <em>творог, 200</em> или <em>рис отварной 150</em>\n"
                f"❌ Неправильно:\n"
                f"  <em>творог</em> (без количества)\n"
                f"  <em>200</em> (без названия)\n"
                f"Попробуйте еще раз!",
                parse_mode="html")
            
    def _search_food_in_database(self, message, product_name: str):
        chat_id = message.chat.id
        products = self.food_db.search(product_name)
        if len(products) == 0:
            self._search_food_in_internet(message, product_name)
        else:
            self.users_meals[chat_id][2] = products
            message_text, markup = self._show_products(chat_id)
            markup.row(
                types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
                types.InlineKeyboardButton("🔎 Найти ещё", callback_data=f"internet_search_{product_name}")
            )
            self.bot.edit_message_text(
                message_text,
                chat_id,
                message.message_id,
                reply_markup=markup,
                parse_mode="html"
            )

    def _search_food_in_internet(self, message, product_name: str):
        chat_id = message.chat.id
        products = self.product_searcher.search(product_name)
        if len(products) == 0:
            self.bot.edit_message_text(
                "🙁 Ничего не нашёл. Попробуй название попроще",
                chat_id,
                message.message_id)
            return
        else:
            self.users_meals[chat_id][2] = products
            message_text, markup = self._show_products(chat_id)
            markup.add(
                types.InlineKeyboardButton("❌ Отмена", callback_data="cancel")
            )
            self.bot.edit_message_text(
                message_text,
                chat_id,
                message.message_id,
                reply_markup=markup,
                parse_mode="html"
            )



    def _parse_user_food(self, text: str) -> Tuple[Optional[Product], Optional[float]]:
        lines = [line.strip() for line in text.strip().split("\n")]
        if len(lines) < 2:
            return None, None
        name_line, nutrients_line, amount_line = lines
        words = [word.capitalize() for word in name_line.strip().split()]
        product_name = ' '.join(words)
        if not product_name:
            return None, None
        
        nutrients = ()
        try:
            numbers = [float(num) for num in nutrients_line.split()]
            if len(numbers) != 4:
                return None, None
            calories, proteins, fats, carbs = numbers
            if all(0 <= n <= 1000 for n in numbers):
                nutrients = (calories, proteins, fats, carbs)
        except (ValueError, TypeError):
            return None, None
        
        product = Product(
            name=product_name,
            calories=nutrients[0],
            proteins=nutrients[1],
            fats=nutrients[2],
            carbs=nutrients[3]
        )
        
        amount_line = amount_line.replace(',', '.').strip()
        try:
            amount = float(amount_line)
            if 0 < amount <= 5000:
                return product, amount
        except ValueError:
            return None, None
    
    def _parse_user_meal(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        if not text:
            return None, None
        
        text = text.strip().replace(',', ' ')
        parts = text.split()
        
        if len(parts) < 2:
            return None, None
        
        try:
            amount = float(parts[-1])
            food_name = ' '.join(parts[:-1])
            return food_name, amount
            
        except ValueError:
            return None, None

    def _show_products(self, chat_id: int):
        text = f"Найдено продуктов: {len(self.users_meals[chat_id][2])}\nКалорий | Белков | Жиров | Углеводов\n\n"
        markup = types.InlineKeyboardMarkup()
        for i, product in enumerate(self.users_meals[chat_id][2]):
            name = product.name
            text += f"<b>{i + 1}. {name}</b>\n"
            text += f"{product.calories} ккал | "
            text += f"{product.proteins} г | "
            text += f"{product.fats} г | "
            text += f"{product.carbs} г\n\n"
            if len(name) > 35:
                name = name[:34] + "…"
            markup.add(
                types.InlineKeyboardButton(
                    f"{i + 1}. {name}",
                    callback_data=f"select_product_{i}"
                )
            )
        return text, markup
    
    def nutrients_per_month(self, chat_id: int, user: User):
        meals_per_mounth = self.meals_db.get_month_meals(user.user_id)
        
        try:
            graphics = Statistic.month(user, meals_per_mounth)
            for graph in graphics:
                self.bot.send_photo(
                    chat_id,
                    graph["image"],
                    graph["title"],
                    parse_mode="html"
                )
                graph["image"].close()
        except:
            self.bot.send_message(chat_id, "⚠️ Не удалось построить графики")



    def _setup_handlers(self):
        self.bot.register_callback_query_handler(
            self._food_addition_handler,
            func=lambda callback: callback.data == "add_food"
        )
        self.bot.register_callback_query_handler(
            self._internet_search_handler,
            func=lambda callback: callback.data.startswith("internet_search_")
        )
        self.bot.register_callback_query_handler(
            self._product_selection_handler,
            func=lambda callback: callback.data.startswith("select_product_")
        )
        self.bot.register_callback_query_handler(
            self._meal_removal_handler,
            func=lambda callback: callback.data.startswith("delete_meal_")
        )
        self.bot.register_callback_query_handler(
            self._cancellation_handler,
            func=lambda callback: callback.data == "cancel"
        )

    def _food_addition_handler(self, callback):
        chat_id = callback.message.chat.id
        if not self.food_db.add_product(self.users_meals[chat_id][2]):
            self.bot.send_message(chat_id, "⚠️ Не получилось сохранить продукт, чтобы найти его снова")
        self.add_meal(callback.message, *self.users_meals[chat_id])

    def _internet_search_handler(self, callback):
        _, _, product_name = callback.data.split('_')
        message = self.bot.edit_message_text(
            "🔎 Ищу продукты…",
            callback.message.chat.id,
            callback.message.message_id
        )
        self._search_food_in_internet(message, product_name)

    def _product_selection_handler(self, callback):
        chat_id = callback.message.chat.id
        _, _, i = callback.data.split("_")
        self.users_meals[chat_id][2] = self.users_meals[chat_id][2][int(i)]
        self.add_meal(callback.message, *self.users_meals[chat_id])

    def _meal_removal_handler(self, callback):
        _, _, user_id, time = callback.data.split("_")
        if self.meals_db.delete_meal(user_id, time):
            self.bot.edit_message_text(
                "✅ Удалено",
                callback.message.chat.id,
                callback.message.message_id
            )
        else:
            self.bot.edit_message_text(
                "⚠️ Что-то пошло не так…",
                callback.message.chat.id,
                callback.message.message_id
            )
        
    def _cancellation_handler(self, callback):
        self.bot.delete_message(callback.message.chat.id, callback.message.message_id)