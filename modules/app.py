import os
import re
import matplotlib
import base64

from tkinter import Tk, Frame, ttk, filedialog, StringVar,  messagebox, PhotoImage
from tkinter.constants import *
from datetime import datetime, timedelta
from threading import Thread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from time import sleep

from modules.log_util import logger
from modules.plot import plot_figure, extract_data

matplotlib.use('Agg')

FONT=("Arial", 12)

class App(Tk):

    log_data: list = []
    filtered_log_data: list = []
    live_data: list = []
    dates_list: list = []
    plot_canvas = None
    plot_toolbar = None
    fig = None
    lines = None
    running_monitor: bool = False
    observer = None
    icon = "moza.ico"

    def __init__(self, *args, **kwargs) -> None:
        Tk.__init__(self, *args, **kwargs)
        self.geometry("650x500")
        self.title('Moza мониторинг температуры')
        icon_decode = base64.b64decode(icon_png)
        icon = PhotoImage(data=icon_decode)
        self.iconphoto(True, icon)

        # Variables       
        self.date_from = StringVar()
        self.date_to = StringVar()
        self.time_from = StringVar()
        self.time_to = StringVar()

        self.plot_status = StringVar()
        self.monitor_status = StringVar()

        self.__init_window()

        self.thread_monitor = MonitorThread(name="Monitor", args=[], daemon=True)
        self.thread_monitor.add_status_var(self.monitor_status)
        self.thread_monitor.add_app(self)
        
        
    def __init_window(self):

        logger.info("Initializing window ...")

        # For grid placement
        row_start = 0  # First row
        column_start = 0  # From first column

        # Row 1
        row = row_start  # next row
        column = column_start  # back to first column
        
        # Frame for buttons and entry
        self.frame_buttons = Frame(self)
        self.frame_buttons.grid(row=row, column=column, sticky='ew')
        column += 1   # next column with span

        #region #### Frame grid for buttons and entry
        # Row 1
        row_frame_buttons = 0  # next row
        column_frame_buttons = 0  # back to first column
        
        self.label_file_path = ttk.Label(self.frame_buttons, text="Путь к логу")
        self.label_file_path.grid(row=row_frame_buttons, column=column_frame_buttons, padx=5, pady=5)
        column_frame_buttons += 1  # next column

        self.entry_file_path = ttk.Entry(self.frame_buttons, width=60)
        default_path = os.path.join(os.environ['LOCALAPPDATA'], 'MOZA Pit House\\Motor_Temprature_Log.log')
        # default_path = os.path.join(os.getcwd(), 'Motor_Temprature_Log.log')
        self.entry_file_path.insert(END, default_path)
        self.entry_file_path.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=5, pady=5, columnspan=7)
        column_frame_buttons += 7  # next column
        
        self.button_open_file = ttk.Button(self.frame_buttons, text='Выбрать', command=self.open_file)
        self.button_open_file.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="e", padx=5, pady=5)
        column_frame_buttons += 1  # next column
 
        self.button_open_file = ttk.Button(self.frame_buttons, text='Открыть', command=self.read_file)
        self.button_open_file.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="e", padx=5, pady=5)
        column_frame_buttons += 1  # next column

        #### Next row
        row_frame_buttons += 1  # add row
        column_frame_buttons = 0  # back to first column

        self.label_dates = ttk.Label(self.frame_buttons, text="День")
        self.label_dates.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5))
        column_frame_buttons += 1  # next column

        self.combobox_date_from = ttk.Combobox(self.frame_buttons, values=self.dates_list, textvariable=self.date_from,
                                            state="readonly", width=10)
        self.combobox_date_from.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 0), sticky="w")
        column_frame_buttons += 1  # next column
        
        self.label_date_separate = ttk.Label(self.frame_buttons, text="-")
        self.label_date_separate.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(0, 0), padx=(0, 0))
        column_frame_buttons += 1  # next column

        self.combobox_date_to = ttk.Combobox(self.frame_buttons, values=self.dates_list, textvariable=self.date_to,
                                            state="readonly", width=10)
        self.combobox_date_to.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(0, 5), sticky="w")
        column_frame_buttons += 1  # next column
        
        self.label_time_from = ttk.Label(self.frame_buttons, text="Время")
        self.label_time_from.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5))
        column_frame_buttons += 1  # next column

        time_now = datetime.now()
        time_from = time_now - timedelta(hours=3)
        self.entry_time_from = ttk.Entry(self.frame_buttons, width=10)
        self.entry_time_from.insert(END, time_from.strftime("%H:%M"))
        # self.entry_time_from.insert(END, '00:00')
        # self.entry_time_from.insert(END, '18:00')
        self.entry_time_from.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=(5, 0), pady=5)
        column_frame_buttons += 1  # next column

        self.label_time_to = ttk.Label(self.frame_buttons, text="-")
        self.label_time_to.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(0, 0), padx=(0, 0))
        column_frame_buttons += 1  # next column

        self.entry_time_to = ttk.Entry(self.frame_buttons, width=10)
        self.entry_time_to.insert(END, time_now.strftime("%H:%M"))
        # self.entry_time_to.insert(END, '23:59')
        # self.entry_time_to.insert(END, '22:00')
        self.entry_time_to.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=(0, 5), pady=5)
        column_frame_buttons += 1  # next column

        self.button_plot = ttk.Button(self.frame_buttons, text='Построить', command=self.start_plot)
        self.button_plot.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="e", padx=5, pady=5)
        column_frame_buttons += 1  # next column
        
        # self.button_plot = ttk.Button(self.frame_buttons, text='Update', command=self.update_plot)
        # self.button_plot.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="e", padx=5, pady=5)
        # column_frame_buttons += 1  # next column
        
        #### Next row
        row_frame_buttons += 1  # add row
        column_frame_buttons = 0  # back to first column
        
        self.button_monitor = ttk.Button(self.frame_buttons, text='Отслеживать', command=self.start_monitor)
        self.button_monitor.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="e", padx=5, pady=5)
        column_frame_buttons += 1  # next column
        
        self.label_monitor_status = ttk.Label(self.frame_buttons, textvariable=self.monitor_status, text="")
        self.label_monitor_status.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5))
        column_frame_buttons += 1  # next column

        #endregion
        
        #### Next row
        row += 1  # add row
        column = 0  # back to first column

        # Frame for plot and toolbar
        self.frame_plot = Frame(self)
        self.frame_plot.grid(row=row, column=column, columnspan=1, sticky='news')
        column += 1  # next column with span

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.frame_plot.rowconfigure(0, weight=1)
        self.frame_plot.columnconfigure(0, weight=1)

        #### Next row
        row += 1  # add row
        column = 0  # back to first column

        self.frame_plot_toolbar = Frame(self)
        self.frame_plot_toolbar.grid(row=row, column=column, columnspan=1, sticky='news')
        column += 1  # next column with span

        logger.info("Initializing window complete.")
    
    def close_and_quit(self):
        self.destroy()

    def open_file(self):
        logger.info("Open file")
        filetypes = (
            ('Log файл', '*.log'),
            ('Все файлы', '*.*')
        )
        base_file_path = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=filetypes)
        # if os.path.dirname(os.path.realpath(base_file_path)) == os.getcwd():
        #     base_file_path = os.path.basename(base_file_path) # set path only to current folder, remove full path
        self.entry_file_path.delete(0, END)
        self.entry_file_path.insert(0, base_file_path)
        logger.info(f"File path: '{base_file_path}'")

    def read_file(self):

        file_path = self.entry_file_path.get()
        
        if not file_path:
            logger.info("Empty file path")
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            log_file = file.readlines()

        log_raw_data = []
        date_set = set()
        for i, line in enumerate(log_file):
            date_set.add(datetime.fromisoformat(line[:10]))
            log_raw_data.append({
                "datetime": datetime.fromisoformat(line[:19]),
                "controller_temp": float(re.search(r"控制器温度\[([\d\.]+)°C\]", line).group(1)),
                "mos_temp": float(re.search(r"MOS温度\[([\d\.]+)°C\]", line).group(1)),
                "motor_stator_temp": float(re.search(r"电机定子温度\[([\d\.]+)°C\]", line).group(1)),
            })
            if i-1 < 0: continue
            line_datetime = datetime.fromisoformat(log_file[i][:19])
            prev_line_datetime = datetime.fromisoformat(log_file[i-1][:19])
            diff = line_datetime - prev_line_datetime
            if diff.total_seconds() > 600:
                log_raw_data.insert(-1, {
                    "datetime": prev_line_datetime + (diff / 2),
                    "controller_temp": None,
                    "mos_temp": None,
                    "motor_stator_temp": None,
                })


        date_list = sorted(date_set)
        date_str_list = list(map(lambda d: d.strftime("%Y-%m-%d"), date_list))

        self.log_data = log_raw_data
        self.dates_list = date_str_list
        self.update_cb_values()
    
    def update_cb_values(self):
        self.combobox_date_from.config(values=self.dates_list)
        self.combobox_date_from.set(self.dates_list[-1])
        self.combobox_date_to.config(values=self.dates_list)
        self.combobox_date_to.set(self.dates_list[-1])

    def start_plot(self):
        if not self.valid_datetime():
            return
        if not self.filtered_log_data:
            logger.info("No data for range")
            messagebox.showinfo(title="Нет данных", message="Нет данных за данный период")
            return

        # self.thread_plot = self.thread_plot.clone()
        # self.thread_plot.start()
        # self.thread_plot_open = True
        
        # if self.plot_canvas:
        #     logger.info("self.plot_canvas.destroy()")
        #     self.plot_canvas.destroy()
        #     # self.plot_canvas.get_tk_widget().pack_forget()        
        # if self.plot_toolbar: 
        #     logger.info("self.plot_toolbar.destroy()")
        #     self.plot_toolbar.destroy()
        #     # self.plot_toolbar.pack_forget()

        if self.fig == None:
            # self.clear_plot()
            # fig, lines = plot_figure(self.filtered_log_data, inside=True)
            # self.fig = fig
            # self.lines = lines
            # canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
            # # self.plot_canvas.get_tk_widget().pack(fill="both", expand=1)
            # self.plot_canvas = canvas.get_tk_widget()
            # self.plot_canvas.pack(side=TOP, fill=BOTH, expand=1)
            # # self.plot_canvas.draw()
            # self.plot_toolbar = NavigationToolbar2Tk(canvas, self.frame_plot_toolbar)
            self.draw_plot(self.filtered_log_data)
        else:
            self.update_plot()
    
        # self.plot_toolbar.update()
        # self.plot_toolbar.pack(side=TOP, fill=BOTH, expand=1)
        # canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        # canvas._tkcanvas.pack()
        # else:
        #     self.fig.set_data()

        self.thread_plot_open = False
    
    def draw_plot(self, plot_data):
        self.clear_plot()
        fig, lines = plot_figure(plot_data, inside=True)
        self.fig = fig
        self.lines = lines
        canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
        # self.plot_canvas.get_tk_widget().pack(fill="both", expand=1)
        self.plot_canvas = canvas.get_tk_widget()
        self.plot_canvas.pack(side=TOP, fill=BOTH, expand=1)
        # self.plot_canvas.draw()
        self.plot_toolbar = NavigationToolbar2Tk(canvas, self.frame_plot_toolbar)

    def clear_plot(self):
        if self.plot_canvas:
            logger.info("Clear canvas self.plot_canvas.destroy()")
            self.plot_canvas.destroy()
        if self.plot_toolbar: 
            logger.info("Clear toolbar self.plot_toolbar.destroy()")
            self.plot_toolbar.destroy()

    def update_plot(self):        
        if not self.valid_datetime():
            return
        if not self.filtered_log_data:
            logger.info("No data for range")
            messagebox.showinfo(title="Нет данных", message="Нет данных за данный период")
            return
        plot_data = extract_data(self.filtered_log_data)

        self.update_plot_data(plot_data)

        # X = plot_data['X']
        # Y1 = plot_data['Y1']
        # Y2 = plot_data['Y2']
        # Y3 = plot_data['Y3']

        # max_Y1 = max(plot_data['Y1'])
        # max_Y2 = max(plot_data['Y2'])
        # max_Y3 = max(plot_data['Y3'])

        # line1 = self.lines[0]
        # line2 = self.lines[1]
        # line3 = self.lines[2]
        # line1.set_data(X, Y1)
        # line2.set_data(X, Y2)
        # line3.set_data(X, Y3)
        # label1 = f'Контролер темп. (max: {max_Y1})'
        # label2 = f'MOSFET темп. (max: {max_Y2})'
        # label3 = f'Мотор статор темп. (max: {max_Y3})'
        # ax = self.fig.gca()
        # ax.relim()
        # ax.autoscale()
        # ax.legend((label1, label2, label3))
        # self.fig.canvas.draw()
        # self.fig.canvas.flush_events()

    def update_plot_live(self, data):
        plot_data = extract_data(self.live_data)
        self.update_plot_data(plot_data)

    def update_plot_data(self, plot_data):

        X = plot_data['X']
        Y1 = plot_data['Y1']
        Y2 = plot_data['Y2']
        Y3 = plot_data['Y3']

        max_Y1 = plot_data['max_Y1']
        max_Y2 = plot_data['max_Y2']
        max_Y3 = plot_data['max_Y3']

 
            
        line1 = self.lines[0]
        line2 = self.lines[1]
        line3 = self.lines[2]
        line1.set_data(X, Y1)
        line2.set_data(X, Y2)
        line3.set_data(X, Y3)
        label1 = f'Контролер темп. (max: {max_Y1})'
        label2 = f'MOSFET темп. (max: {max_Y2})'
        label3 = f'Мотор статор темп. (max: {max_Y3})'
        ax = self.fig.gca()
        ax.relim()
        ax.autoscale()
        ax.legend((label1, label2, label3))
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def valid_datetime(self):
        logger.info("Getting date and time")

        plot_date_from = self.date_from.get()
        plot_date_to = self.date_to.get()
        if not plot_date_from or not plot_date_to:
            logger.info("No date. Not open file")
            messagebox.showerror(title="Ошибка", message=f"Не задан день.\nСначала надо открыть файл.")
            return False
        plot_time_from = self.entry_time_from.get()
        plot_time_to = self.entry_time_to.get()

        if plot_time_from[1] == ':': plot_time_from = '0' + plot_time_from
        if plot_time_to[1] == ':': plot_time_to = '0' + plot_time_to

        try:
            logger.info(f"date and time from: {plot_date_from} {plot_time_from}")
            logger.info(f"date and time to: {plot_date_to} {plot_time_to}")
            plot_dt_from = datetime.fromisoformat(f"{plot_date_from} {plot_time_from}")
            plot_dt_to = datetime.fromisoformat(f"{plot_date_to} {plot_time_to}")
        except ValueError as e:
            logger.exception(e)
            logger.info("For script not valid date")
            self.monitor_status.set("Неверная дата")
            messagebox.showerror(title="Ошибка", message=f"Не верная дата.\nФормат времени HH:MM.\nДиапазон 00:00 - 23:59")
            return False

        if plot_dt_from > plot_dt_to:
            logger.info("Not valid date range. From > to.")
            self.monitor_status.set("Неверная дата")
            messagebox.showerror(title="Ошибка", message=f"Не верная дата.\nДата ОТ опережает дату ДО.")
            return False

        filtered_data = []
        for row in self.log_data:
            if plot_dt_to > row['datetime'] > plot_dt_from:
                filtered_data.append(row)

        self.filtered_log_data = filtered_data
        return True
        
    def populate_live_data(self):

        date_now = datetime.now()
        date_now = date_now.replace(second=30, microsecond=0)
        delta_from = date_now - timedelta(minutes=30)

        
        def datetime_range(start, end, delta):
            current = start
            while current < end:
                yield current
                current += delta

        for date in datetime_range(delta_from, date_now, timedelta(seconds=30)):
            self.live_data.append({
                "datetime": date,
                "controller_temp": None,
                "mos_temp": None,
                "motor_stator_temp": None,
            })
        
        import json
        with open('live_data', 'w') as f:
            json.dump(self.live_data, f, indent=4, default=str)

    def start_monitor(self):
        if self.thread_monitor.is_alive():
            logger.info("Monitor already running")
            return
        self.populate_live_data()
        self.running_monitor = True
        self.button_monitor.configure(text='Остановить', command=self.stop_monitor)

        self.thread_monitor = self.thread_monitor.clone()
        self.thread_monitor.start()

    def stop_monitor(self):
        logger.info("monitor stopping")
        # self.running_monitor = False
        logger.debug("self.running_monitor = False")
        self.button_monitor.configure(text='Отслеживать', command=self.start_monitor)
        logger.debug("button_monitor.configure")
        self.thread_monitor.stop()
        logger.debug("after thread_monitor.stop()")
        # self.thread_monitor.join()
        logger.debug("after thread_monitor.join()")

    def monitor_loop(self):

        file_path = self.entry_file_path.get()
        self.draw_plot(self.live_data)
        _cached_stamp = os.stat(file_path).st_mtime
        wait_time = 5
        while self.running_monitor:          
            sleep(wait_time)

            stamp = os.stat(file_path).st_mtime
            if stamp != _cached_stamp:
                _cached_stamp = stamp
                self.update_data(file_path)

    def update_data(self, file_path):
        logger.info(f"modified file")

        with open(file_path, 'r', encoding='utf-8') as file:
            log_file = file.readlines()
        
        last_line = log_file[-1]
        self.live_data.append({
            "datetime": datetime.fromisoformat(last_line[:19]),
            "controller_temp": float(re.search(r"控制器温度\[([\d\.]+)°C\]", last_line).group(1)),
            "mos_temp": float(re.search(r"MOS温度\[([\d\.]+)°C\]", last_line).group(1)),
            "motor_stator_temp": float(re.search(r"电机定子温度\[([\d\.]+)°C\]", last_line).group(1)),
        })
        if self.live_data[0]['controller_temp'] == None:
            self.live_data.pop(0)
            
        self.update_plot_data(extract_data(self.live_data)) 


class MonitorThread(Thread):

    def __init__(self, *args, **kwargs):
        self.__args, self.__kwargs = args, kwargs
        super().__init__(*args, **kwargs)
        self.app = None
        self.status_var = None
        self.running_monitor = False

    def run(self) -> None:
        self.update_status("Активный")
        self.running_monitor = True
        # super().run()
        self.monitor_loop()
        self.update_status("Не активно")
        logger.info("Stop monitor...")

    def stop(self):
        logger.info("self.app.running_monitor = False")
        self.running_monitor = False

    def clone(self):
        new_thread = MonitorThread(*self.__args, **self.__kwargs)
        new_thread.add_status_var(self.status_var)
        new_thread.add_app(self.app)
        return new_thread

    def add_status_var(self, var: StringVar):
        self.status_var = var

    def add_app(self, app: App):
        self.app = app

    def update_status(self, status:str):
        self.status_var.set(status)
    
    def error_message(self, exc_value):
        self.update_status("error")
        err_type = exc_value.__class__.__name__
        messagebox.showerror(title="Ошибка", message=f"Ошибка в скрипте {self.name}!\n\n{err_type}: {exc_value}")



    def monitor_loop(self):
        logger.info("start minitor loop")
        file_path = self.app.entry_file_path.get()
        self.app.draw_plot(self.app.live_data)
        _cached_stamp = os.stat(file_path).st_mtime
        wait_time = 2
        while self.running_monitor:          
            sleep(wait_time)

            stamp = os.stat(file_path).st_mtime
            if stamp != _cached_stamp:
                _cached_stamp = stamp
                self.app.update_data(file_path)
        logger.info("end while loop")

icon_png = b'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'
