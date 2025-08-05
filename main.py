import tkinter as tk
from src.gui.login import LoginWindow
from src.database.database import Database

if __name__ == "__main__":
    # Ruta a la base de datos
    #RUTA_BD = 'ZKTimeNet.db'
    RUTA_BD  = r'C:\Program Files (x86)\ZKTimeNet3.0\ZKTimeNet.db'
    # Crear instancia de la base de datos
    db = Database(db_path=RUTA_BD)

    # Iniciar la aplicación
    login_window = LoginWindow(db)
    login_window.mainloop()
