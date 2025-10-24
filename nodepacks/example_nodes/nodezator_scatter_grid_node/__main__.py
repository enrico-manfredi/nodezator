import math
import matplotlib.pyplot as plt

def plot_grid_from_master(
    X_master,
    Y_master,
    pairs=None,
    rows=None,
    cols=None,
    sharex=False,
    sharey=False,
    titles=None,
    figsize=None,
    scatter_kwargs=None,
    savepath=None,
    show=False,
    block=True,
):
    """
    Plot multiple (x, y) series from two master lists-of-lists in an m x n grid.

    Tip: When running as a script, call with show=True to keep the figure open.
    """
    # Determine pairs
    if pairs is None:
        n = min(len(X_master), len(Y_master))
        pairs = [(i, i) for i in range(n)]
    if not pairs:
        raise ValueError("No (x_idx, y_idx) pairs specified or discoverable.")

    # Validate
    for k, (xi, yi) in enumerate(pairs):
        if not (0 <= xi < len(X_master)):
            raise IndexError(f"Pair {k}: x index {xi} out of range 0..{len(X_master)-1}.")
        if not (0 <= yi < len(Y_master)):
            raise IndexError(f"Pair {k}: y index {yi} out of range 0..{len(Y_master)-1}.")
        x = X_master[xi]
        y = Y_master[yi]
        if len(x) != len(y):
            raise ValueError(f"Pair {k}: length mismatch (x[{xi}]={len(x)} vs y[{yi}]={len(y)}).")

    # Grid shape
    total = len(pairs)
    if rows is None and cols is None:
        cols = math.ceil(math.sqrt(total))
        rows = math.ceil(total / cols)
    elif rows is None:
        rows = math.ceil(total / cols)
    elif cols is None:
        cols = math.ceil(total / rows)

    # Figure
    if figsize is None:
        figsize = (4 * cols, 3 * rows)
    fig, axes = plt.subplots(rows, cols, sharex=sharex, sharey=sharey, figsize=figsize)

    # Normalize axes to 2D list
    if rows == 1 and cols == 1:
        axes_grid = [[axes]]
    elif rows == 1:
        axes_grid = [list(axes)]
    elif cols == 1:
        axes_grid = [[ax] for ax in axes]
    else:
        axes_grid = axes

    scatter_kwargs = scatter_kwargs or {}

    # Plot
    for i, (xi, yi) in enumerate(pairs):
        r = i // cols
        c = i % cols
        ax = axes_grid[r][c]
        ax.scatter(X_master[xi], Y_master[yi], **scatter_kwargs)
        if titles:
            if len(titles) != total:
                raise ValueError("Length of 'titles' must match number of pairs.")
            ax.set_title(titles[i])
        else:
            ax.set_title(f"x[{xi}] vs y[{yi}]")
        ax.grid(True, linestyle="--", alpha=0.3)

    # Hide unused axes
    for j in range(total, rows * cols):
        r = j // cols
        c = j % cols
        axes_grid[r][c].set_visible(False)

    fig.tight_layout()

    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches="tight")

    if show:
        plt.show(block=block)

    return fig, axes

main_callable = plot_grid_from_master

if __name__ == "__main__":
    X_master = [[1,2,3,4], [0,1,4,9,16], [2,3,5,8], [0,1,2,3,4]]
    Y_master = [[2,3,5,8], [0,1,2,3,4], [1,2,3,4], [0,1,4,9,16]]
    plot_grid_from_master(X_master, Y_master, show=True)  # keeps window open
