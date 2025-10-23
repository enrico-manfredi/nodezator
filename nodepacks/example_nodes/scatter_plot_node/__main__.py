"""
Node: scatter_plot
Description: Plot two numeric series of the same length on a scatter plot using matplotlib.
"""

import matplotlib.pyplot as plt


def scatter_plot(
    x_series: list = [0, 1, 2, 3],
    y_series: list = [0, 1, 4, 9],
    title: str = "Scatter Plot",
    xlabel: str = "X",
    ylabel: str = "Y",
    color: str = "blue",
    marker: str = "o"
) -> None:
    """
    Display a scatter plot of x_series vs y_series.

    Parameters
    ----------
    x_series : list of numbers
        X values.
    y_series : list of numbers
        Y values; must be same length as x_series.
    title : str
        Title of the plot.
    xlabel, ylabel : str
        Axis labels.
    color : str
        Matplotlib color specifier.
    marker : str
        Matplotlib marker style.

    Returns
    -------
    None
        Displays a matplotlib window.
    """
    # basic validation
    if not hasattr(x_series, "__len__") or not hasattr(y_series, "__len__"):
        raise TypeError("x_series and y_series must be sequences (lists, tuples, etc.)")

    if len(x_series) != len(y_series):
        raise ValueError(f"Input series must have equal length. Got {len(x_series)} and {len(y_series)}")

    if len(x_series) == 0:
        raise ValueError("Input series are empty; nothing to plot.")

    # create the figure
    fig, ax = plt.subplots()
    ax.scatter(x_series, y_series, c=color, marker=marker)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)

    # display the plot
    plt.show()


# Required for Nodezator to recognize this function as a node
main_callable = scatter_plot
