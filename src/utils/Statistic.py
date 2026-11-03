import matplotlib.pyplot as plt
import io
import matplotlib
matplotlib.use('Agg')
from User import User
from Product import Product

class Statistic:
    @staticmethod
    def today(user: User, meals: list[Product, float]):
        try:
            totals = Statistic._get_daily_totals(meals)

            return ("Статистика за день:\n\n"
                f"К:  {Statistic._progress_bar(totals["calories"], user.calories)}"
                f"Б:  {Statistic._progress_bar(totals["proteins"], user.proteins)}"
                f"Ж: {Statistic._progress_bar(totals["fats"], user.fats)}"
                f"У:  {Statistic._progress_bar(totals["carbs"], user.carbs)}")
        except:
            return "⚠️ Не удалось загрузить статистику за день"
    
    @staticmethod
    def month(user: User, meals_per_mounth: list[Product, float, str]):
        month, day, i = "", "", -1

        dates, calories_data, proteins_data, fats_data, carbs_data = [], [], [], [], []
        for meal in meals_per_mounth:
            product, amount, date = meal
            amount /= 100
            _, next_month, next_day = date.split("-")
            if day != next_day:
                day = next_day
                if month != next_month:
                    month = next_month
                    dates.append(f"{day}.{month}")
                else:
                    dates.append(day)
                i += 1
                calories_data.insert(i, product.calories * amount)
                proteins_data.insert(i, product.proteins * amount)
                fats_data.insert(i, product.fats * amount)
                carbs_data.insert(i, product.carbs * amount)
            else:
                calories_data[i] += product.calories * amount
                proteins_data[i] += product.proteins * amount
                fats_data[i] += product.fats * amount
                carbs_data[i] += product.carbs * amount
        dates.reverse()
        calories_data.reverse()
        proteins_data.reverse()
        fats_data.reverse()
        carbs_data.reverse()

        graphics = []
        plt.plot(dates, calories_data, marker="o", color="blue", linewidth=2)
        plt.axhline(y=user.calories, color="blue", linestyle="--")
        plt.xlabel("Дата", fontsize=12)
        plt.ylabel("Килокалории", fontsize=12)
        buffer_1 = io.BytesIO()
        plt.savefig(buffer_1, format="png")
        plt.close()
        buffer_1.seek(0)
        graphics.append({
            "image": buffer_1,
            "title": "📊 <b>Калории за месяц</b>\n\n"
                            f"• Среднедневные калории: {(sum(calories_data)/len(calories_data)):.0f} ккал\n"
                            f"• Макс. калорий в день: {max(calories_data):.0f} ккал\n"
                            f"• Мин. калорий в день: {min(calories_data):.0f} ккал"
        })

        plt.plot(dates, proteins_data, label="Белки", marker="o", color="red", linewidth=2)
        plt.axhline(y=user.proteins, color="red", linestyle="--")
        plt.plot(dates, fats_data, label="Жиры", marker="o", color="orange", linewidth=2)
        plt.axhline(y=user.fats, color="orange", linestyle="--")
        plt.plot(dates, carbs_data, label="Углеводы", marker="o", color="black", linewidth=2)
        plt.axhline(y=user.carbs, color="black", linestyle="--")
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Граммы', fontsize=12)
        plt.legend()
        buffer_2 = io.BytesIO()
        plt.savefig(buffer_2, format='png', dpi=100)
        plt.close()
        buffer_2.seek(0)
        graphics.append({
            "image": buffer_2,
            "title": "📊 <b>Нутриенты за месяц</b>\n"
                            "🔴 Белки | 🟡 Жиры | ⚫️ Углеводы"
        })
        return graphics



    @staticmethod
    def _get_daily_totals(meals: list[Product, float]) -> dict:
        totals = {
            'calories': 0,
            'proteins': 0,
            'fats': 0,
            'carbs': 0
        }
        
        for product, amount, _ in meals:
            amount /= 100
            totals['calories'] += round(product.calories * amount, 1)
            totals['proteins'] += round(product.proteins * amount, 1)
            totals['fats'] += round(product.fats * amount, 1)
            totals['carbs'] += round(product.carbs * amount, 1)
        return totals

    @staticmethod
    def _progress_bar(value: float, norm: float) -> str:
        res = ""
        WIDTH = 11

        ratio = value / norm
        length = round(WIDTH * ratio)

        if length <= WIDTH:
            res += "🟩" * length + "⬛️" * (WIDTH - length)
        else:
            res += "🟥" * min(length - WIDTH, WIDTH) + "🟩" * (WIDTH - min(length - WIDTH, WIDTH))

        res += f"{round(ratio * 100)}%\n"
        return res