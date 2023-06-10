import PDV as sub
from interface import tk, ttk, Button

name = input("Qual o nome da loja?\n-> ")

root = tk.Tk()
root.geometry("500x310")
root.iconbitmap(default=r"assets/PDV.ico")
root.wm_title("Ponto de Vendas")
style = ttk.Style(root)
style.theme_use("clam")  # ou "alt", "default", e "classic"

sys = sub.System(root, name)

# Montagem do menu principal
main_menu_buttons = [
    Button("Cadastro", lambda: signup_menu_state.show_state()),
    Button("Financeiro", lambda: finances_menu_state.show_state()),
    Button("Encerrar", root.destroy),
]
main_menu_state = sys.add_state(f"{sys.data.name}", f"Bem vindo ao {sys.data.name}. O que deseja "
                                                    f"fazer?",
                                main_menu_buttons)

# Montagem do menu de cadastro
signup_menu_buttons = [
    Button("Cadastro de Item", sys.load_data),
    Button("Voltar ao menu principal.", main_menu_state.show_state),
]
signup_menu_state = sys.add_state("Cadastro", "Qual cadastro deseja realizar?", signup_menu_buttons)


# Montagem do menu de finanças
finances_menu_buttons = [
    Button("Abrir Nota Fiscal", sys.create_nf),
    Button("Voltar ao menu principal.", main_menu_state.show_state),
]
finances_menu_state = sys.add_state("Finanças", "Qual operação deseja realizar?", finances_menu_buttons)

# Run the interface
sys.run()
print("\n"*10)