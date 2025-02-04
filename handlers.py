import os
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from states import UserInfo
from utils import get_city_temp, get_food_calory, get_water_baseline, get_calory_baseline, get_workout_calory
from dotenv import load_dotenv

router = Router()
FOOD_API_KEY = os.getenv("FOOD_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_TOKEN")

calories_100 = []
users = {}

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот, который поможет следить за поддержанием здорового образа жизни.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/set_profile - Создание профиля\n"
        "/log_water - Сохранение количества выпитой за день воды\n"
        "/log_food - Сохранение потребленных калорий от съеденной за день еды\n"
        "/log_workout - Сохранение сожженных калорий за счет выполнения тренировок\n"
        "/check_progress - Отображение объема выпитой воды, количества потребленных и сожженых калорий"
    )

@router.message(Command("set_profile"))
async def process_name(message: Message, state: FSMContext):
    await message.reply("Как Вас зовут?")
    await state.set_state(UserInfo.Name)

@router.message(UserInfo.Name)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(Name=message.text)
    await message.reply("Какой у Вас вес? (в кг)")
    await state.set_state(UserInfo.Weight)

@router.message(UserInfo.Weight)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(Weight=int(message.text))
    await message.reply("Какой у Вас рост? (в см)")
    await state.set_state(UserInfo.Height)

@router.message(UserInfo.Height)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(Height=int(message.text))
    await message.reply("Сколько Вам лет?")
    await state.set_state(UserInfo.Age)

@router.message(UserInfo.Age)
async def process_activity_level(message: Message, state: FSMContext):
    await state.update_data(Age=int(message.text))
    await message.reply("Сколько минут активности у Вас в день?")
    await state.set_state(UserInfo.ActivityLevel)

@router.message(UserInfo.ActivityLevel)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(ActivityLevel=int(message.text))
    await message.reply("В каком городе Вы проживаете?")
    await state.set_state(UserInfo.City)

@router.message(UserInfo.City)
async def process_calorry_aim(message: Message, state: FSMContext):
    await state.update_data(City=message.text)
    await message.reply("Какая Ваша цель по калориям? Если согласны со значением калорий по умолчанию, поставьте 0.")
    await state.set_state(UserInfo.CaloryGoal)

@router.message(UserInfo.CaloryGoal)
async def process_user_info(message: Message, state: FSMContext):
    data = await state.get_data()

    name = data.get("Name")
    weight = data.get("Weight")
    height = data.get("Height")
    age = data.get("Age")
    activity_level = data.get("ActivityLevel")
    city = data.get("City")
    calory_aim = int(message.text)

    if calory_aim == 0:
        calory_aim = get_calory_baseline(weight, height, age, activity_level)
    await state.set_state(UserInfo.CaloryGoal)
    await state.update_data(CaloryAIm=calory_aim)
    await state.set_state(UserInfo.LoggedCalories)
    await state.update_data(LoggedCalories=calory_aim)

    city_temp = get_city_temp(city, 1, WEATHER_API_KEY)
    water_baseline = get_water_baseline(weight, activity_level, city_temp)

    await state.set_state(UserInfo.WaterGoal)
    await state.update_data(WaterGoal=water_baseline)
    await state.set_state(UserInfo.LoggedWater)
    await state.update_data(LoggedWater=water_baseline)

    await message.reply(f"Здравствуйте, {name}.\n"
                        f"Ваши биологические данные: возраст {age}, вес {weight}, рост {height}.\n"
                        f"Ваш уровень активности: {activity_level} минут в день. Ваш город проживания: {city}.\n"
                        f"Ваш план по калориям: {calory_aim} ккал. Ваша норма по воде -- {water_baseline} мл.")
    data = await state.get_data()

    data["BurnedCalories"] = 0
    data["LoggedCalories"] = 0
    data["LoggedWater"] = 0
    data["CaloryGoal"] = calory_aim

    global users
    users[message.from_user.id] = data

    await state.clear()

@router.message(Command("log_water"))
async def add_water(message: Message, state: FSMContext, command: CommandObject):
    command_args: str = command.args
    if not command_args.isdigit():
        await message.reply("Вы ввели некорректное значение выпитой воды. Значение должно быть числовым")
    else:
        if float(command_args) <= 0.0:
            await message.reply("Вы ввели некорректное значение выпитой воды. Значение должно быть больше нуля")
        else:
            global users
            users[message.from_user.id]['WaterGoal'] -= int(command_args)
            users[message.from_user.id]['LoggedWater'] += int(command_args)
            await message.reply(f"Суммарно за день выпито {users[message.from_user.id]['LoggedWater']} мл. До выполнения нормы осталось {users[message.from_user.id]['WaterGoal']} мл")

@router.message(Command("log_food"))
async def add_food(message: Message, state: FSMContext, command: CommandObject):
    command_args: str = command.args
    if not command_args.replace(" ", "").replace("-", "").isalpha():
        await message.reply("Вы ввели некорректный тип потребленной еды. Значение должно быть текстовым")
    else:
        cur_calory_100 = get_food_calory(command_args)
        await message.reply(f"Вы съели {command_args}, его калорийность -- {cur_calory_100} на 100 грамм. Сколько грамм Вы съели?")
        global calories_100
        calories_100.append(cur_calory_100)
        await state.set_state(UserInfo.LoggedCalories)

@router.message(UserInfo.LoggedCalories)
async def process_calorry_aim(message: Message, state: FSMContext):
    if not message.text.isdigit(): 
        await message.reply("Вы ввели некорректное значение граммовки еды. Значение должно быть числовым")
    else:
        if float(message.text) <= 0.0:
            await message.reply("Вы ввели некорректное значение граммовки еды. Значение должно быть больше нуля")
        else:
            global users
            users[message.from_user.id]['LoggedCalories'] += calories_100[-1] * float(message.text) / 100
            await message.reply(f"Записано {calories_100[-1] * float(message.text) / 100} калорий. До выполнения нормы осталось {users[message.from_user.id]['CaloryGoal']} калорий")
    await state.clear()

@router.message(Command("log_workout"))
async def add_workout(message: Message, state: FSMContext, command: CommandObject):
    command_args: str = command.args
    activity, activity_time = command_args.split()
    additional_water = 200 * (float(activity_time) // 30 if float(activity_time) // 30 != 0 else 1)

    global users
    calories_workout = get_workout_calory(activity, activity_time, FOOD_API_KEY)

    users[message.from_user.id]['WaterGoal'] += additional_water
    users[message.from_user.id]['BurnedCalories'] += calories_workout
    await message.reply(f"Активность {activity} в течение {activity_time} минут -- сожжено {calories_workout} ккал. Дополнительно: выпейте {additional_water} мл воды")

@router.message(Command("check_progress"))
async def get_check_progress(message: Message, state: FSMContext, command: CommandObject):
    global users

    water_goal = users[message.from_user.id]["WaterGoal"] + users[message.from_user.id]["LoggedWater"]
    logged_water =  users[message.from_user.id]["LoggedWater"]
    calories_burned = users[message.from_user.id]["BurnedCalories"]
    calory_goal = users[message.from_user.id]["CaloryGoal"]
    logged_calories = users[message.from_user.id]["LoggedCalories"]
    ost_water = users[message.from_user.id]["WaterGoal"]

    progress_name = "Прогресс:\n"
    water_name = "Вода:\n"
    water_aim = f"- Выпито: {logged_water} мл из {water_goal} мл\n"
    water_aim_2 = f"- Осталось: {ost_water} мл\n\n"
    calories_name = "Калории:\n"
    calories_aim = f"- Потреблено: {logged_calories} ккал из {calory_goal} ккал\n"
    calories_aim_2 = f"- Сожжено: {calories_burned} ккал\n"
    calories_aim_3 = f"- Баланс: {logged_calories - calories_burned} ккал"

    result_message = progress_name + water_name + water_aim + water_aim_2 +\
        calories_name + calories_aim + calories_aim_2 + calories_aim_3
    await message.reply(result_message)

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
