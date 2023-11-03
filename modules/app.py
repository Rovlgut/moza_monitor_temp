import os
import re
import matplotlib

from tkinter import Tk, Frame, ttk, filedialog, StringVar,  messagebox, LabelFrame
from tkinter.constants import *
from datetime import datetime, timedelta
from threading import Thread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent, FileSystemEventHandler

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
        self.geometry("630x500")
        self.title('Moza мониторинг температуры')
        self.iconbitmap(self.icon)

        # Variables       
        self.dates = StringVar()
        self.time_from = StringVar()
        self.time_to = StringVar()

        self.plot_status = StringVar()
        self.monitor_status = StringVar()

        self.__init_window()

        self.thread_plot = PlotThread(target=self.monitor_loop, name="Plot", args=[], daemon=True)
        self.thread_plot.add_status_var(self.plot_status)
        self.thread_plot.add_app(self)
        self.thread_plot_running = False

        self.thread_monitor = MonitorThread(target=self.monitor_loop, name="Monitor", args=[], daemon=True)
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
        # default_path = os.path.join(os.environ['LOCALAPPDATA'], 'MOZA Pit House\\Motor_Temprature_Log.log')
        default_path = os.path.join(os.getcwd(), 'Motor_Temprature_Log.log')
        self.entry_file_path.insert(END, default_path)
        self.entry_file_path.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=5, pady=5, columnspan=5)
        column_frame_buttons += 5  # next column
        
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

        self.combobox_dates = ttk.Combobox(self.frame_buttons, values=self.dates_list, textvariable=self.dates,
                                            state="readonly", width=10)
        self.combobox_dates.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5), sticky="w")
        column_frame_buttons += 1  # next column

        self.label_time_from = ttk.Label(self.frame_buttons, text="C")
        self.label_time_from.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5))
        column_frame_buttons += 1  # next column

        self.entry_time_from = ttk.Entry(self.frame_buttons, width=10)
        # self.entry_time_from.insert(END, '00:00')
        self.entry_time_from.insert(END, '18:00')
        self.entry_time_from.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=5, pady=5)
        column_frame_buttons += 1  # next column

        self.label_time_to = ttk.Label(self.frame_buttons, text="По")
        self.label_time_to.grid(row=row_frame_buttons, column=column_frame_buttons, pady=(5, 5), padx=(5, 5))
        column_frame_buttons += 1  # next column

        self.entry_time_to = ttk.Entry(self.frame_buttons, width=10)
        # self.entry_time_to.insert(END, '23:59')
        self.entry_time_to.insert(END, '22:00')
        self.entry_time_to.grid(row=row_frame_buttons, column=column_frame_buttons, sticky="ew", padx=5, pady=5)
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
        self.combobox_dates.config(values=self.dates_list)
        self.combobox_dates.set(self.dates_list[0])

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

        plot_date = self.dates.get()
        plot_time_from = self.entry_time_from.get()
        plot_time_to = self.entry_time_to.get()

        if plot_time_from[1] == ':': plot_time_from = '0' + plot_time_from
        if plot_time_to[1] == ':': plot_time_to = '0' + plot_time_to

        try:
            logger.info(f"date and time from: {plot_date} {plot_time_from}")
            logger.info(f"date and time to: {plot_date} {plot_time_to}")
            plot_dt_from = datetime.fromisoformat(f"{plot_date} {plot_time_from}")
            plot_dt_to = datetime.fromisoformat(f"{plot_date} {plot_time_to}")
        except ValueError as e:
            logger.exception(e)
            logger.info("For script not valid date")
            self.plot_status.set("Не верная дата")
            messagebox.showerror(title="Ошибка", message=f"Не верная дата.\nФормат времени HH:MM.\nДиапазон 00:00 - 23:59")
            return False


        filtered_data = []
        for row in self.log_data:
            if plot_dt_to > row['datetime'] > plot_dt_from:
                filtered_data.append(row)

        self.filtered_log_data = filtered_data
        return True
        
    def populate_live_data(self):

        date_now = datetime.now().astimezone()
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
        wait_time = 2
        while self.running_monitor:          
            sleep(wait_time)

            stamp = os.stat(file_path).st_mtime
            if stamp != _cached_stamp:
                _cached_stamp = stamp
                self.update_data(file_path)

    def start_observer(self):

        if self.observer != None and self.observer.is_alive():
            logger.info("Monitor already running")
            return
        
        
        self.populate_live_data()
        self.running_monitor = True
        self.button_monitor.configure(text='Остановить', command=self.stop_observer)

        
        file_path = self.entry_file_path.get()
        file_path = os.path.dirname(file_path)
        self.draw_plot(self.live_data)

        event_handler = Handler(file_path, self)
        # event_handler = MyHandler()
        self.observer = Observer()   
        logger.info(f'start watching file {file_path!r}')     
        self.observer.schedule(event_handler, file_path, recursive=False)
        self.observer.start()

    def stop_observer(self):
        self.observer.stop()
        self.observer.join()
        self.running_monitor = False
        self.button_monitor.configure(text='Отслеживать', command=self.stop_observer)

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


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print('file changed', event)        

class Handler(FileSystemEventHandler):

        def __init__(self, src_path, app):
            FileSystemEventHandler.__init__(self)
            self.file_path = src_path
            self.app: App = app

        def on_modified(self, event):
            logger.info(f"modified file {event.src_path!r}")
            with open(event.src_path, 'r', encoding='utf-8') as file:
                log_file = file.readlines()
            
            last_line = log_file[-1]
            self.app.live_data.append({
                "datetime": datetime.fromisoformat(last_line[:19]),
                "controller_temp": float(re.search(r"控制器温度\[([\d\.]+)°C\]", last_line).group(1)),
                "mos_temp": float(re.search(r"MOS温度\[([\d\.]+)°C\]", last_line).group(1)),
                "motor_stator_temp": float(re.search(r"电机定子温度\[([\d\.]+)°C\]", last_line).group(1)),
            })
            if self.app.live_data[0]['controller_temp'] == None:
                self.app.live_data.pop(0)
            
            self.app.update_plot_data(extract_data(self.app.live_data)) 
  
        def error_message(self, exc_value):
            # self.update_status("error")
            err_type = exc_value.__class__.__name__
            messagebox.showerror(title="Ошибка", message=f"Ошибка в скрипте!\n\n{err_type}: {exc_value}")

class PlotThread(Thread):

    def __init__(self, *args, **kwargs):
        self.__args, self.__kwargs = args, kwargs
        super().__init__(*args, **kwargs)
        self.app = None
        self.status_var = None

    def run(self) -> None:
        self.update_status("Активный")
        super().run()
        self.update_status("Не активно")
        logger.info("Stop monitor...")

    def clone(self):
        new_thread = PlotThread(*self.__args, **self.__kwargs)
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