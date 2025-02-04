from aiogram.fsm.state import State, StatesGroup

class UserInfo(StatesGroup):
    Name = State()
    Weight = State()
    Height = State()
    Age = State()
    ActivityLevel = State()
    City = State()
    WaterGoal = State()
    CaloryGoal = State()
    LoggedWater = State()
    LoggedCalories = State()
    BurnedCalories = State()
