from __future__ import annotations
import tkinter.filedialog
from collections import Counter
from functools import partial

import pandas as pd
from interface import *
from pdv_utils import *


class Product:
    def __init__(self, barcode: str, name: str, value: float):
        self.barcode: str = barcode.strip()
        self.name: str = name
        self.price: float = value

    def update_price(self, new_price: float):
        self.price = new_price


class NF:
    def __init__(self, client_name: str, client_cpf: str = ""):
        self.client_name = client_name
        self.client_cpf = client_cpf
        self.cart: list[Product] = []
        self.total = 0

    def add_to_cart(self, product: Product):
        self.cart.append(product)
        self.total += product.price

    def remove_from_cart(self, barcode):
        tgt_i = -1
        for i, prod in enumerate(self.cart):
            if prod.barcode == barcode:
                tgt_i = i
                break

        if tgt_i >= 0:
            prod = self.cart.pop(tgt_i)
            self.total -= prod.price


class Pdv:
    def __init__(self, name: str):
        self.name: str = name.strip().title()
        self.products: dict[str:Product] = {}
        self.nfs: list[NF] = []
        self.vault = 0
        self.current_cart = 0

        self.save_name = ""
        self.has_save = False

    def open_cart(self, client_name="-", client_cpf="-"):
        self.nfs.append(NF(client_name, client_cpf))

    def get_product(self, barcode: str):
        return self.products[barcode]

    def close_cart(self):
        if len(self.nfs) == self.current_cart + 1:
            self.current_cart += 1


class InputForm:
    def __init__(self, w_root: tk.Toplevel | tk.Tk, d_root: Pdv, title: str, fields: dict, callback):
        self.window_root: tk.Toplevel | tk.Tk = w_root
        self.data_root: Pdv = d_root
        self.title: str = title
        self.fields: dict[str, str] = fields
        self.inputs: list[tk.Entry] = []
        self.is_filled: bool = False
        self.icon_path: str = ""
        self.callback = callback

    def create_widgets(self, save_txt: str | None = "Salvar"):
        self.window_root.title(self.title.split(' ')[0])

        if self.icon_path:
            self.window_root.iconbitmap(self.icon_path)

        title_label = ttk.Label(self.window_root, text=self.title, font=("Arial", 16))
        title_label.pack(pady=10)

        for i, data in enumerate(self.fields.items()):
            field_name, field_value = data
            frame = ttk.Frame(self.window_root)
            frame.pack(pady=5)
            label = ttk.Label(frame, text=field_name, font=("Arial", 12))
            label.pack(side="left", padx=10)
            if isinstance(field_value, list):
                input_field = ttk.Combobox(frame, font=("Arial", 12), values=field_value, state="readonly")
            else:
                input_field = ttk.Entry(frame, font=("Arial", 12))
            self.inputs.append(input_field)
            input_field.pack(side="right", padx=10)

        for i, field in enumerate(self.inputs):
            if i < len(self.fields.items()) - 1:
                field.bind("<Return>", self.focus_next)
            else:
                field.bind("<Return>", lambda x: self.save_inputs())

        # Create save button
        if save_txt is not None:
            save_button = ttk.Button(self.window_root, text=save_txt, command=self.save_inputs)
            save_button.pack(pady=10)

        self.inputs[0].focus()
        self.window_root.update()

    def focus_next(self, event):
        self.inputs[self.inputs.index(event.widget) + 1].focus_set()

    @abstractmethod
    def show_form(self):
        raise NotImplementedError("O método deve estar implementado na classe herdeira.")

    def get_fields(self) -> list[str]:
        fields = []
        if self.is_filled:
            for field_data in tuple(self.fields.values()):
                if field_data == "":
                    raise EmptyField
                else:
                    fields.append(field_data)

        return fields

    def save_inputs(self):
        for i, input_field in enumerate(list(self.fields.keys())):
            self.fields[input_field] = self.inputs[i].get()
        self.is_filled = True
        if self.callback is not None:
            self.callback()

        self.window_root.withdraw()
        try:
            self.window_root.after(100, self.window_root.destroy)
            return 0
        except tk.TclError:
            return -1


class CreateNF(InputForm):
    def __init__(self, window_root: tk.Toplevel, data_root: Pdv):
        fields = {
            "Nome do cliente:": "none",
            "CPF:": "",
        }
        super().__init__(window_root, data_root, "Criação de nota", fields, self.create)

    def show_form(self):
        self.create_widgets(None)

    def create(self):
        try:
            client_name, cpf = self.get_fields()
        except EmptyField:
            client_name = "-"
            cpf = "-"

        self.data_root.open_cart(client_name.title(), cpf)

        popup_info(f"Agora o cliente {client_name} pode fazer suas compras.")

        ShowCart(self.data_root).show()


class ShowCart:
    def __init__(self, data: Pdv):
        self.current_cart = data.nfs[data.current_cart].cart
        self.itens_amount = 0

        window = tk.Toplevel()
        window.title("Carrinho de compras")
        window.geometry("400x700")

        self.root = window
        self.main_frame: ScrollableFrame | None = None
        self.total_frame: ttk.Label | None = None
        self.data: Pdv = data

        frame = ttk.Frame(window)
        frame.pack(side="top")
        ttk.Label(frame, text="Código:", font=("Arial", 12)).pack(side="left", padx=10)
        self.entry = ttk.Entry(frame, font=("Arial", 12))
        self.entry.pack(side="right")
        self.entry.bind("<Return>", lambda entry: self.add_product())

        self.update()

    def add_product(self):
        try:
            barcode = self.entry.get()
            if barcode.startswith("-"):
                self.data.nfs[self.data.current_cart].remove_from_cart(barcode[1:])
            else:
                self.data.nfs[self.data.current_cart].add_to_cart(self.data.get_product(barcode))
        except KeyError:
            popup_warning("Produto não cadastrado!")

        self.entry.delete(0, tk.END)
        self.update()

    def update(self):
        self.entry.focus_force()

        if self.main_frame is not None:
            self.itens_amount = len(self.current_cart)
            self.main_frame.destroy()
            self.total_frame.destroy()

        p_info = []
        for p, count in Counter(self.current_cart).items():
            p_info.append(f"{count}x {p.name}:".ljust(20, "_") + f" R$ {p.price:.2f}".rjust(20, "_"))

        if self.itens_amount != 0:
            self.main_frame = ScrollableFrame(self.root,
                                              title=f"Carrinho de {self.data.nfs[self.data.current_cart].client_name}")
            self.main_frame.pack(fill="both", expand=True)

            for item in p_info:
                label = tk.Label(self.main_frame.scrollable_frame, text=item, font=("Courier", 11))
                self.main_frame.add_item(label)
        else:
            self.main_frame = ScrollableFrame(self.root, title="Não há itens no carrinho.")
            self.main_frame.pack(fill="both", expand=True)

        self.total_frame = ttk.Frame(self.root)
        self.total_frame.pack(side="bottom", padx=10, fill="x")
        ttk.Label(self.total_frame, text=f"Total: R$ {self.data.nfs[self.data.current_cart].total:.2f}",
                  font=("Courier", 12)).pack(side="left")
        ttk.Button(self.total_frame, text="Encerrar Compra", command=self.end_cart).pack(side="right")

        return self

    def end_cart(self):
        popup_info(f"Compras efetuadas! Valor total: R$ {self.data.nfs[self.data.current_cart].total:.2f}")
        self.data.close_cart()
        self.root.destroy()

    def show(self):
        self.root.mainloop()


class System(Interface):
    def __init__(self, root: tk.Tk, name: str):
        """
        Descreve um sistema. É o ponto de entrada do sistema, todas as operações são realizados sob o esse escopo.

        Os sistemas armazenam as pessoas e os bancos, além de manusear as operações que as envolvem.
        """
        super().__init__(root)

        self.nf: CreateNF | None = None
        self.data: Pdv = Pdv(name)

    def load_data(self):
        save_path = tkinter.filedialog.askopenfilename(defaultextension='pcsv', initialdir="/saves",
                                                       title="Selecione um arquivo de produtos.")
        if save_path[-5:] == ".pcsv":
            save = pd.read_csv(save_path).astype(str)
            for i, product in save.iterrows():
                name, price, code = product.values
                self.data.products[code] = Product(code, name, float(price))

            popup_info("Dados carregados.")
        else:
            if popup_retry('Selecione um arquivo válido.'):
                self.load_data()

    def create_nf(self):
        self.nf = CreateNF(tk.Toplevel(), self.data)
        self.nf.show_form()