import os
import telebot
import time
from flask import Flask, request

TOKEN = os.environ.get('TOKEN', "8566096823:AAEzu-4uwv40pMzJroyCI_WJ1-bgOODePlM")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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
    for r in REGIONS:
        markup.add(r)
    
    bot.send_message(
        msg.chat.id,
        "🛠 <b>ZPCheck PRO</b>\nВыбери регион:",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(commands=['test'])
def test(msg):
    salary = 26900
    hours = 300
    days = 30
    per_diem = 3850
    actual = 215482
    region = REGIONS["Иркутская (Усть-Кут)"]
    
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
    
    net_actual = actual
    gross_actual = net_actual / 0.87
    salary_with_coeff = gross_actual - per_diem_total
    base_buh = salary_with_coeff / (1 + (region['rk'] - 1) + (region['north'] / 100))
    
    report = f"""
🧪 <b>ТВОИ ДАННЫЕ ЗА АПРЕЛЬ:</b>

<b>По закону:</b>
• База: {rub(base_law)}
• На руки: {rub(net_law)}

<b>Их расчёт:</b>
• База: {rub(base_buh)}
• Начислили: {rub(actual)}

🚨 <b>Завышают базу в {base_buh/base_law:.1f} раза!</b>
"""
    
    bot.send_message(msg.chat.id, report, parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle(msg):
    uid = msg.from_user.id
    if uid not in users:
        users[uid] = {'step': 'region'}
    
    s = users[uid]
    step = s.get('step', 'region')
    
    if step == 'region':
        if msg.text not in REGIONS:
            return
        s['region'] = msg.text
        s['region_data'] = REGIONS[msg.text]
        s['step'] = 'salary'
        bot.send_message(uid, f"📍 {msg.text}\nВведи оклад:", parse_mode='HTML')
    
    elif step == 'salary':
        try:
            s['salary'] = float(msg.text.replace(' ', ''))
        except:
            return
        s['step'] = 'hours'
        bot.send_message(uid, f"💰 {rub(s['salary'])}\nЧасов?", parse_mode='HTML')
    
    elif step == 'hours':
        try:
            s['hours'] = float(msg.text)
        except:
            return
        s['step'] = 'days'
        bot.send_message(uid, f"⏰ {s['hours']} ч.\nДней?", parse_mode='HTML')
    
    elif step == 'days':
        try:
            s['days'] = float(msg.text)
        except:
            return
        s['step'] = 'per_diem'
        bot.send_message(uid, f"📅 {s['days']} дн.\nНадбавка за день?", parse_mode='HTML')
    
    elif step == 'per_diem':
        try:
            s['per_diem'] = float(msg.text.replace(' ', ''))
        except:
            return
        s['step'] = 'actual'
        bot.send_message(uid, f"💵 {rub(s['per_diem'])}/день\nСколько начислили?", parse_mode='HTML')
    
    elif step == 'actual':
        try:
            actual = float(msg.text.replace(' ', ''))
        except:
            return
        
        salary = s['salary']
        hours = s['hours']
        days = s['days']
        per_diem = s['per_diem']
        region = s['region_data']
        
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

@app.route('/')
def home():
    return "Бот работает! Отправь /start в Telegram"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return ''

if __name__ == '__main__':
    print("🤖 Бот запускается...")
    print("⏳ Ждём 5 секунд...")
    time.sleep(5)
    
    # Удаляем старый вебхук если есть
    bot.remove_webhook()
    time.sleep(2)
    
    # Flask должен запуститься на порту 10000 (требование Render)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
