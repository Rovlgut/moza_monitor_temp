import re
import matplotlib.pyplot as plt
from datetime import datetime

from modules.log_util import logger


def plot_figure(data, inside: bool = False):

    plot_data = extract_data(data)

    X = plot_data['X']
    Y1 = plot_data['Y1']
    Y2 = plot_data['Y2']
    Y3 = plot_data['Y3']

    max_Y1 = plot_data['max_Y1']
    max_Y2 = plot_data['max_Y2']
    max_Y3 = plot_data['max_Y3']
    # print(f"Max Y1: {max_Y1}")
    # print(f"Max Y2: {max_Y2}")
    # print(f"Max Y3: {max_Y3}")

    # fig, ax = plt.subplots(num="График температуры", layout="constrained")
    # fig, ax = plt.subplots(num="График температуры")
    # fig.set_figwidth(10)
    # fig.set_figheight(5)
    # line1, = ax.plot(X, Y1, 'b', label=f'Контролер темп. (max: {max_Y1})')
    # line2, = ax.plot(X, Y2, 'r', label=f'MOSFET темп. (max: {max_Y2})')
    # line3, = ax.plot(X, Y3, 'g', label=f'Мотор статор темп. (max: {max_Y3})')
    # ax.grid(axis='y')
    # ax.legend()
    # # fig.tight_layout()
    # fig.subplots_adjust(left=0.05, bottom=0.07, right=0.99, top=0.99, wspace=0, hspace=0)
    # # plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    fig = plt.figure()

    ax = fig.add_subplot(111)
    line1, = ax.plot(X, Y1, 'b', label=f'Контролер темп. (max: {max_Y1})')
    line2, = ax.plot(X, Y2, 'r', label=f'MOSFET темп. (max: {max_Y2})')
    line3, = ax.plot(X, Y3, 'g', label=f'Мотор статор темп. (max: {max_Y3})')
    fig.subplots_adjust(left=0.07, bottom=0.07, right=0.99, top=0.99, wspace=0, hspace=0)
    ax.autoscale()
    ax.grid(axis='y')
    ax.legend()

    if not inside:
        plt.show()
    return fig, (line1, line2, line3)

def extract_data(data):

    X = [row['datetime'] for row in data]
    Y1 = [row['controller_temp'] for row in data]
    Y2 = [row['mos_temp'] for row in data]
    Y3 = [row['motor_stator_temp'] for row in data]
    
    max_Y1 = ''
    max_Y2 = ''
    max_Y3 = ''

    try:
        # max_Y1 = max(Y1)
        # max_Y2 = max(Y2)
        # max_Y3 = max(Y3)
        max_Y1 = max([y for y in Y1 if y is not None])
        max_Y2 = max([y for y in Y2 if y is not None])
        max_Y3 = max([y for y in Y3 if y is not None])
    except ValueError as e:
        logger.info("No data for max")
    except TypeError as e:
        logger.info("No data for max")
        # logger.exception(e)
    
    return {
        'X': X,
        'Y1': Y1,
        'Y2': Y2,
        'Y3': Y3,
        'max_Y1': max_Y1,
        'max_Y2': max_Y2,
        'max_Y3': max_Y3
    }
    

