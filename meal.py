import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

@st.cache_data
def load_data():
    df = pd.read_csv("meals_nutrion_dataset.csv")
    return df

df = load_data()

# ===============================
# Functions (same as your code)
# ===============================
def calculate_bmi(weight, height):
    return round(weight / (height ** 2), 2)

def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calorie_needs(weight, height, age, goal):
    bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
    if goal == "lose":
        return int(bmr * 1.2 - 500)
    elif goal == "gain":
        return int(bmr * 1.2 + 500)
    else:
        return int(bmr * 1.2)

def filter_meals(meal_type, diet, health_condition):
    filtered = df[df["meal_type"] == meal_type].copy()

    if diet == "veg":
        filtered = filtered[filtered["diet"] == "veg"]

    if health_condition != "none":
        filtered = filtered[~filtered["health"].str.contains(health_condition, case=False, na=False)]

    if filtered.empty:
        filtered = df[df["meal_type"] == meal_type]

    return filtered.to_dict(orient="records")

def choose_meals_for_slot(meal_type, target, diet, health_condition):
    options = filter_meals(meal_type, diet, health_condition)
    chosen, total = [], 0

    if diet == "non-veg" and meal_type in ["lunch", "dinner"]:
        nonveg_options = [m for m in options if m["diet"] == "non-veg"]
        if nonveg_options:
            first_choice = random.choice(nonveg_options)
            chosen.append(first_choice)
            total += first_choice["calories"]
            options.remove(first_choice)

    random.shuffle(options)
    while options and total < target * 0.7:
        choice = options.pop(0)
        chosen.append(choice)
        total += choice["calories"]

    if not chosen:
        fallback = df[df["meal_type"] == meal_type].sample(1).to_dict(orient="records")[0]
        chosen.append(fallback)

    return chosen

def suggest_balanced_meals(daily_calories, diet, health_condition):
    targets = {
        "breakfast": daily_calories * 0.25,
        "morning_snack": daily_calories * 0.1,
        "lunch": daily_calories * 0.3,
        "evening_snack": daily_calories * 0.1,
        "dinner": daily_calories * 0.25
    }

    plan = {}
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}

    for meal_type in targets:
        chosen = choose_meals_for_slot(meal_type, targets[meal_type], diet, health_condition)
        plan[meal_type] = chosen
        for meal in chosen:
            for key in totals:
                totals[key] += meal[key]

    return plan, totals

# ===============================
# Streamlit App
# ===============================
st.title("🍽️ Personalized Meal Planning DSS")

# User inputs
age = st.number_input("Enter your age (years):", min_value=1, max_value=120, value=25)
weight = st.number_input("Enter your weight (kg):", min_value=1.0, max_value=300.0, value=70.0)
height = st.number_input("Enter your height (meters):", min_value=0.5, max_value=2.5, value=1.75)
goal = st.selectbox("Fitness Goal:", ["lose", "gain", "maintain"])
diet = st.selectbox("Diet Type:", ["veg", "non-veg"])
health_condition = st.selectbox("Health Condition:", ["none", "diabetes", "hypertension"])

if st.button("Generate Meal Plan"):
    bmi = calculate_bmi(weight, height)
    bmi_cat = bmi_category(bmi)
    daily_calories = calorie_needs(weight, height, age, goal)
    plan, totals = suggest_balanced_meals(daily_calories, diet, health_condition)

    st.subheader("💡 Personalized Meal Plan")
    st.write(f"**BMI:** {bmi}")
    st.write(f"**BMI Category:** {bmi_cat}")
    st.write(f"**Daily Calorie Needs:** {daily_calories} kcal")

    for meal_type, chosen in plan.items():
        st.write(f"### {meal_type.replace('_', ' ').capitalize()}")
        for meal in chosen:
            st.write(f"- {meal['name']} ({meal['calories']} kcal, {meal['protein']}g protein, "
                     f"{meal['carbs']}g carbs, {meal['fat']}g fat, {meal['fiber']}g fiber)")

    st.write("### 🧮 Daily Totals")
    st.write(f"- Calories: {totals['calories']} kcal")
    st.write(f"- Protein: {totals['protein']} g")
    st.write(f"- Carbs: {totals['carbs']} g")
    st.write(f"- Fat: {totals['fat']} g")
    st.write(f"- Fiber: {totals['fiber']} g")

    st.write("### 🍩 Macronutrient Ratio")
    macros = [totals['protein'], totals['carbs'], totals['fat']]
    labels = ['Protein', 'Carbs', 'Fat']
    colors = ['#FFB703', '#219EBC', '#FB8500']

    fig, ax = plt.subplots()
    ax.pie(macros, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax.axis('equal')  # Equal aspect ratio ensures pie chart is circular
    st.pyplot(fig)