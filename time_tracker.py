import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from datetime import datetime, timedelta
import os

class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TimeCrystal V1.0")
        self.task_name_var = tk.StringVar()

        self.setup_db()
        self.setup_ui()

        self.task_running = False
        self.task_start_time = None
        self.pause_start_time = None
        self.elapsed_time = timedelta()


    def setup_db(self):
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                             (id INTEGER PRIMARY KEY, task_name TEXT, start_time TEXT, end_time TEXT, total_time INTEGER)''')
        self.conn.commit()

    def setup_ui(self):
        self.setup_menu()

        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        

        ttk.Label(frame, text="Nom de la Tâche :").grid(column=1, row=1, sticky=tk.W)
        ttk.Entry(frame, width=25, textvariable=self.task_name_var).grid(column=2, row=1, sticky=(tk.W, tk.E))

        ttk.Button(frame, text="Démarrer Tâche", command=self.start_task).grid(column=2, row=2, sticky=tk.W)
        ttk.Button(frame, text="Pause/Reprendre Tâche", command=self.pause_resume_task).grid(column=3, row=2, sticky=tk.W)
        ttk.Button(frame, text="Arrêter Tâche", command=self.stop_task).grid(column=4, row=2, sticky=tk.W)

        self.elapsed_time_label = ttk.Label(frame, text="Temps Écoulé : ")
        self.elapsed_time_label.grid(column=1, row=3, columnspan=4, sticky=tk.W)
        self.elapsed_time_label.grid_remove()

        self.tasks_tree = ttk.Treeview(frame, columns=("id", "task", "start_time", "end_time", "total_time"), show='headings')
        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("task", text="Tâche")
        self.tasks_tree.heading("start_time", text="Heure de Début")
        self.tasks_tree.heading("end_time", text="Heure de Fin")
        self.tasks_tree.heading("total_time", text="Temps Total (s)")
        self.tasks_tree.grid(column=1, row=4, columnspan=4, sticky=(tk.W, tk.E))

        self.tasks_tree.column("id", width=30)  # Hide the ID column by making it small

        self.tasks_tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Supprimer la Tâche", command=self.delete_task)

        self.load_tasks()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Supprimer la base de données", command=self.delete_database)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)


    def start_task(self):
        if not self.task_running:
            self.task_running = True
            self.task_start_time = datetime.now()
            self.elapsed_time_label.grid()
            self.elapsed_time_label.config(text="Temps Écoulé : 0:00:00")
            self.update_elapsed_time()

    def pause_resume_task(self):
        if self.task_running:
            self.task_running = False
            self.pause_start_time = datetime.now()
        else:
            if self.pause_start_time:
                pause_duration = datetime.now() - self.pause_start_time
                self.task_start_time += pause_duration
                self.pause_start_time = None
            self.task_running = True
            self.update_elapsed_time()

    def stop_task(self):
        if self.task_running:
            self.task_running = False
            self.elapsed_time_label.grid_remove()

            task_name = self.task_name_var.get()
            start_time = self.task_start_time.strftime("%Y-%m-%d %H:%M:%S") if self.task_start_time else None
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_time = (datetime.now() - self.task_start_time).total_seconds() if self.task_start_time else 0

            existing_task = self.cursor.execute("SELECT id, total_time FROM tasks WHERE task_name=?", (task_name,)).fetchone()
            if existing_task:
                task_id, existing_total_time = existing_task
                new_total_time = existing_total_time + total_time
                self.cursor.execute("UPDATE tasks SET end_time=?, total_time=? WHERE id=?",
                                    (end_time, new_total_time, task_id))
            else:
                self.cursor.execute("INSERT INTO tasks (task_name, start_time, end_time, total_time) VALUES (?, ?, ?, ?)",
                                    (task_name, start_time, end_time, total_time))
            self.conn.commit()
            self.load_tasks()

    def update_elapsed_time(self):
        if self.task_running:
            current_time = datetime.now()
            self.elapsed_time = current_time - self.task_start_time
            elapsed_seconds = int(self.elapsed_time.total_seconds())
            elapsed_time_str = str(timedelta(seconds=elapsed_seconds))
            self.elapsed_time_label.config(text="Temps Écoulé : " + elapsed_time_str)
            self.root.after(1000, self.update_elapsed_time)

    def load_tasks(self):
        for row in self.tasks_tree.get_children():
            self.tasks_tree.delete(row)

        self.cursor.execute("SELECT id, task_name, start_time, end_time, total_time FROM tasks")
        for row in self.cursor.fetchall():
            row = (row[0], row[1], row[2], row[3], int(row[4]))
            self.tasks_tree.insert("", "end", values=row)

    def show_context_menu(self, event):
        selected_item = self.tasks_tree.identify_row(event.y)
        if selected_item:
            self.tasks_tree.selection_set(selected_item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_task(self):
        selected_item = self.tasks_tree.selection()[0]
        task_values = self.tasks_tree.item(selected_item, "values")
        task_id = task_values[0]

        print(f"Suppression de la tâche avec ID: {task_id}")  # Debugging information

        self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def delete_database(self):
        confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer la base de données ?")
        if confirm:
            self.conn.close()
            if os.path.exists('tasks.db'):
                os.remove('tasks.db')
                print("Fichier tasks.db supprimé.")
            else:
                print("Le fichier tasks.db n'existe pas.")
            self.setup_db()
            self.load_tasks()
            messagebox.showinfo("Info", "La base de données a été supprimée.")
                

if __name__ == "__main__":
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
