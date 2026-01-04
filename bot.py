import telebot
import os

TOKEN = os.environ.get('TOKEN', "8566096823:AAEzu-4uwv40pMzJroyCI_WJ1-bgOODePlM")
bot = telebot.TeleBot(TOKEN)

users = {}

REGIONS = {
    "Иркутская (Усть-Кут)": {"rk": 1.7, "north": 80},
    "Чукотка": {"rk": 2.0, "north": 100},
    "ЯНАО": {"rk": 1.8, "north": 80},
    "Другой": {"rk": 1.0, "north": 0}
}

def rub(num):
    return f"{int(num):,} ₽".replace(",", " ")

@bot.message_handler(commands=['start'])
def start(msg):
    users[msg.from_user.id] = {'step': 'region'}
    
    markup = telebot.types.ReplyKeyboardMarkup(True, True)
    for r in REGIONS: markup.add(r)
    
    bot.send_message(
        msg.chat.id,
        "🛠 <b>ZPCheck PRO</b>\nВыбери регион:",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(commands=['test'])
def test(msg):
    # Твои данные за апрель
    salary = 26900
    hours = 300
    days = 30
    per_diem = 3850
    actual = 215482
    region = REGIONS["Иркутская (Усть-Кут)"]
    
    # Расчёт
    hour_rate = salary / 176
    salary_hours = hour_rate * hours
    per_diem_total = per_diem * days
    per_diem_tax = max(0, per_diem - 700) * days
    
    base_law = salary_hours + per_diem_tax
    rk = base_law * (region['rk'] - 1)
    north = base_law * (region['north'] / 100)
    
    gross = salary_hours + per_diem_total + rk + north
    ndfl = (salary_hours + per_diem_tax + rk + north) * 0.13
    net_law = gross - ndfl
    
    # Как у них
    net_actual = actual
    gross_actual = net_actual / 0.87
    salary_with_coeff = gross_actual - per_diem_total
    base_buh = salary_with_coeff / (1 + (region['rk'] - 1) + (region['north'] / 100))
    
    report = f"""
🧪 <b>ТВОИ ДАННЫЕ ЗА АПРЕЛЬ 2025</b>

<b>По закону должно быть:</b>
• База для коэффициентов: {rub(base_law)}
• На руки: {rub(net_law)}

<b>Как начислили бухгалтерия:</b>
• База у них: {rub(base_buh)}
• Начислили: {rub(actual)}

🚨 <b>ВЫВОД:</b>
Они завышают базу в <b>{base_buh/base_law:.1f} раза</b>!

💸 <b>Отпускные за 20 дней:</b>
• По их начислениям: {rub((actual / 29.3) * 20)}
• По закону: {rub((net_law / 29.3) * 20)}
• Разница: {rub(((actual - net_law) / 29.3) * 20)}
"""
    
    bot.send_message(msg.chat.id, report, parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle(msg):
    uid = msg.from_user.id
    if uid not in users: users[uid] = {'step': 'region'}
    
    s = users[uid]
    step = s.get('step', 'region')
    
    # Шаг 1: Регион
    if step == 'region':
        if msg.text not in REGIONS: return
        s['region'] = msg.text
        s['region_data'] = REGIONS[msg.text]
        s['step'] = 'salary'
        bot.send_message(uid, f"📍 {msg.text}\nВведи оклад:", parse_mode='HTML')
    
    # Шаг 2: Оклад
    elif step == 'salary':
        try: s['salary'] = float(msg.text.replace(' ', ''))
        except: return
        s['step'] = 'hours'
        bot.send_message(uid, f"💰 {rub(s['salary'])}\nЧасов?", parse_mode='HTML')
    
    # Шаг 3: Часы
    elif step == 'hours':
        try: s['hours'] = float(msg.text)
        except: return
        s['step'] = 'days'
        bot.send_message(uid, f"⏰ {s['hours']} ч.\nДней?", parse_mode='HTML')
    
    # Шаг 4: Дни
    elif step == 'days':
        try: s['days'] = float(msg.text)
        except: return
        s['step'] = 'per_diem'
        bot.send_message(uid, f"📅 {s['days']} дн.\nНадбавка за день?", parse_mode='HTML')
    
    # Шаг 5: Надбавка
    elif step == 'per_diem':
        try: s['per_diem'] = float(msg.text.replace(' ', ''))
        except: return
        s['step'] = 'actual'
        bot.send_message(uid, f"💵 {rub(s['per_diem'])}/день\nСколько начислили?", parse_mode='HTML')
    
    # Шаг 6: Расчёт
    elif step == 'actual':
        try: actual = float(msg.text.replace(' ', ''))
        except: return
        
        salary = s['salary']
        hours = s['hours']
        days = s['days']
        per_diem = s['per_diem']
        region = s['region_data']
        
        # По закону
        hour_rate = salary / 176
        salary_hours = hour_rate * hours
        per_diem_total = per_diem * days
        per_diem_tax = max(0, per_diem - 700) * days
        
        base_law = salary_hours + per_diem_tax
        rk = base_law * (region['rk'] - 1)
        north = base_law * (region['north'] / 100)
        
        gross = salary_hours + per_diem_total + rk + north
        ndfl = (salary_hours + per_diem_tax + rk + north) * 0.13
        net_law = gross - ndfl
        
        # Как у них
        net_actual = actual
        gross_actual = net_actual / 0.87
        salary_with_coeff = gross_actual - per_diem_total
        base_buh = salary_with_coeff / (1 + (region['rk'] - 1) + (region['north'] / 100))
        
        report = f"""
🧮 <b>РАСЧЁТ:</b>

<b>По закону:</b>
• База: {rub(base_law)}
• На руки: {rub(net_law)}

<b>Их расчёт:</b>
• База: {rub(base_buh)}
• Начислили: {rub(actual)}

<b>Разница в базе:</b> {rub(base_buh - base_law)}
Завышают в {base_buh/base_law:.1f} раза!
"""
        
        bot.send_message(uid, report, parse_mode='HTML')
        users.pop(uid, None)

print("🤖 Бот запущен!")
bot.polling(none_stop=True)
