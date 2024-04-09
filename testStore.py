import tkinter as tk
from tkinter import ttk, Menu, Toplevel, messagebox
import mysql.connector
import styles
from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import random
import datetime

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="magazine"
)
mycursor = mydb.cursor()

root = tk.Tk()
root.title("Магазин")
root.geometry("1000x700")

order = []
total_price = 0
pickup_points = ["Пункт выдачи 1", "Пункт выдачи 2", "Пункт выдачи 3"]
selected_pickup = tk.StringVar(value=pickup_points[0])

def get_products():
    mycursor.execute("SELECT id, photo, name, description, manufacturer, price FROM products")
    products = mycursor.fetchall()

    for idx, product in enumerate(products):
        img = Image.open(product[1])
        img = img.resize((100, 100), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)

        product_frame = ttk.Frame(root, padding=10)
        product_frame.grid(row=0, column=idx, padx=10)

        label = ttk.Label(product_frame, image=img)
        label.image = img
        label.grid(row=0, column=0)

        ttk.Label(product_frame, text=f"Название: {product[2]}").grid(row=1, column=0)
        ttk.Label(product_frame, text=f"Описание: {product[3]}").grid(row=2, column=0)
        ttk.Label(product_frame, text=f"Цена: {product[5]}").grid(row=3, column=0)

        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(label="Добавить к заказу", command=lambda prod=product: add_to_order(prod))
        label.bind("<Button-3>", lambda e, context_menu=context_menu: context_menu.post(e.x_root, e.y_root))


def add_to_order(product):
    global total_price, order
    order.append(product)
    total_price += product[5]
    update_order_button()


def remove_from_order(product):
    global total_price, order
    order.remove(product)
    total_price -= product[5]
    update_order_window()



def save_order_to_db():
    global total_price
    order_date = datetime.datetime.now().strftime("%Y-%m-%d")
    pickup_point = selected_pickup.get()
    status = "Новый"

    sql = "INSERT INTO orders (total_price, pickup_point, status) VALUES (%s, %s, %s)"
    val = (total_price, pickup_point, status)
    mycursor.execute(sql, val)
    mydb.commit()

    order_id = mycursor.lastrowid

    order_number = f"ORD-{order_id}"
    sql_update = "UPDATE orders SET order_number = %s WHERE order_id = %s"
    val_update = (order_number, order_id)
    mycursor.execute(sql_update, val_update)
    mydb.commit()

    messagebox.showinfo("Сохранено", f"Заказ успешно сохранен в базе данных. Номер заказа: {order_number}")


def save_order():
    global order
    save_order_to_db()
    order_date = datetime.datetime.now().strftime("%Y-%m-%d")
    order_number = generate_order_code()
    pickup_code = generate_order_code()
    delivery_time = get_delivery_time(len(order))

    pdf_filename = f"order_{order_number}.pdf"
    pdfmetrics.registerFont(TTFont('Roboto-Regular', 'C:/store/Roboto-Regular.ttf'))
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Roboto-Regular'

    pdf = SimpleDocTemplate(pdf_filename, pagesize=letter)

    order_data = [
        Paragraph(f"Дата заказа: {order_date}", styles['Normal']),
        Paragraph(f"Номер заказа: {order_number}", styles['Normal']),
        Paragraph(f"Сумма заказа: {total_price} руб.", styles['Normal']),
        Paragraph(f"Пункт выдачи: {selected_pickup.get()}", styles['Normal']),
        Paragraph(f"<b>Код получения:</b> {pickup_code}", styles['Normal']),
        Paragraph(f"Срок доставки: {delivery_time}", styles['Normal']),
        Paragraph("Состав заказа:", styles['Normal'])
    ]
    for product in order:
        order_data.append(Paragraph(f"{product[2]} - {product[3]}", styles['Normal']))

    pdf.build(order_data)

    messagebox.showinfo("Сохранено", f"Заказ сохранен в файле {pdf_filename}")


save_order_btn = ttk.Button(root, text="Сохранить", command=save_order)

def update_order_button():
    global save_order_btn

    if order:
        view_order_btn.grid(row=len(order) + 2, column=0, pady=10)
        save_order_btn.grid(row=len(order) + 3, column=0, pady=10)
    else:
        view_order_btn.grid_remove()
        save_order_btn.grid_remove()


def update_order_window():
    global total_price_label, pickup_combobox, save_order_btn

    for widget in order_window.winfo_children():
        widget.destroy()

    for idx, product in enumerate(order):
        img = Image.open(product[1])
        img = img.resize((100, 100), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)

        product_frame = ttk.Frame(order_window, padding=10)
        product_frame.grid(row=idx, column=0)

        label = ttk.Label(product_frame, image=img)
        label.image = img
        label.grid(row=0, column=0)

        ttk.Label(product_frame, text=f"Название: {product[2]}").grid(row=1, column=0)
        ttk.Label(product_frame, text=f"Описание: {product[3]}").grid(row=2, column=0)
        ttk.Label(product_frame, text=f"Цена: {product[5]}").grid(row=3, column=0)

        remove_btn = ttk.Button(product_frame, text="Удалить", command=lambda prod=product: remove_from_order(prod))
        remove_btn.grid(row=4, column=0, pady=5)

    total_price_label = ttk.Label(order_window, text=f"Общая стоимость: {total_price}")
    total_price_label.grid(row=len(order) + 1, column=0, pady=10)

    ttk.Label(order_window, text="Выберите пункт выдачи:").grid(row=len(order) + 2, column=0, pady=5)
    pickup_combobox = ttk.Combobox(order_window, textvariable=selected_pickup, values=pickup_points, state="readonly")
    pickup_combobox.grid(row=len(order) + 3, column=0, pady=5)

    save_order_btn = ttk.Button(order_window, text="Сохранить", command=save_order)
    save_order_btn.grid(row=len(order) + 4, column=0, pady=10)

def generate_order_code():
    return f"{random.randint(100, 999)}"


def get_delivery_time(order_length):
    return "3 дня" if order_length >= 3 else "6 дней"

def view_order():
    global order_window
    order_window = Toplevel(root)
    order_window.title("Заказы")
    order_window.geometry("700x800")

    update_order_window()


get_products()

view_order_btn = ttk.Button(root, text="Просмотр заказа", command=view_order)

update_order_button()

root.mainloop()