import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb

from ..utils import fit_transforms, apply_transforms


def visualize_variable_relationships(data, quantitative_vars, category_vars=None, joint_viz_type='scatter',
                                     pair_viz_type='scatter', factor_viz_type='strip', pair_diag_type='kde',
                                     fig_size=16):
    """
    Generates plots showing the relationship between several variables.
    """
    if quantitative_vars is None or len(quantitative_vars) == 0:
        raise Exception('Must provide at least one quantitative variable.')

    # compare the continuous variable distributions using a violin plot
    sub_data = data[quantitative_vars]
    fig, ax = plt.subplots(1, 1, figsize=(fig_size, fig_size * 3 / 4))
    sb.violinplot(data=sub_data, ax=ax)
    fig.tight_layout()

    # if categorical variables were provided, visualize the quantitative distributions by category
    if category_vars is not None:
        fig, ax = plt.subplots(len(quantitative_vars), len(category_vars), figsize=(fig_size, fig_size * 3 / 4))
        if len(quantitative_vars) == 1:
            if len(category_vars) == 1:
                sb.violinplot(x=quantitative_vars[0], y=category_vars[0], data=data, ax=ax)
            else:
                for i, cat in enumerate(category_vars):
                    sb.violinplot(x=quantitative_vars[0], y=cat, data=data, ax=ax[i])
        else:
            for i, var in enumerate(quantitative_vars):
                if len(category_vars) == 1:
                    sb.violinplot(x=var, y=category_vars[0], data=data, ax=ax[i])
                else:
                    for j, cat in enumerate(category_vars):
                        sb.violinplot(x=var, y=cat, data=data, ax=ax[i, j])
        fig.tight_layout()

    # generate plots to directly compare the variables
    if category_vars is None:
        if len(quantitative_vars) == 2:
            sb.jointplot(x=quantitative_vars[0], y=quantitative_vars[1], data=data, kind=joint_viz_type, size=fig_size)
        else:
            sb.pairplot(data=data, vars=quantitative_vars, kind=pair_viz_type,
                        diag_kind=pair_diag_type, size=fig_size / len(quantitative_vars))
    else:
        if len(quantitative_vars) == 1:
            if len(category_vars) == 1:
                sb.factorplot(x=category_vars[0], y=quantitative_vars[0],
                              data=data, kind=factor_viz_type, size=fig_size)
            else:
                sb.factorplot(x=category_vars[0], y=quantitative_vars[0], hue=category_vars[1],
                              data=data, kind=factor_viz_type, size=fig_size)
        elif len(quantitative_vars) == 2:
            if len(category_vars) == 1:
                sb.lmplot(x=quantitative_vars[0], y=quantitative_vars[1],
                          data=data, row=category_vars[0], size=fig_size)
            else:
                sb.lmplot(x=quantitative_vars[0], y=quantitative_vars[1], data=data,
                          col=category_vars[0], row=category_vars[1], size=fig_size)
        else:
            sb.pairplot(data=data, hue=category_vars[0], vars=quantitative_vars, kind=pair_viz_type,
                        diag_kind=pair_diag_type, size=fig_size / len(quantitative_vars))


def visualize_feature_distributions(data, viz_type='hist', bins=None, grid_size=4, fig_size=20):
    """
    Generates feature distribution plots (histogram or kde) for each feature.
    """
    if viz_type == 'hist':
        hist = True
        kde = False
    elif viz_type == 'kde':
        hist = False
        kde = True
    elif viz_type == 'both':
        hist = True
        kde = True
    else:
        raise Exception('Visualization type not supported.')

    # replace NaN values with 0 to prevent exceptions in the lower level API calls
    data = data.fillna(0)

    n_features = len(data.columns)
    plot_size = grid_size ** 2
    n_plots = n_features / plot_size if n_features % plot_size == 0 else n_features / plot_size + 1

    for i in range(n_plots):
        fig, ax = plt.subplots(grid_size, grid_size, figsize=(fig_size, fig_size / 2))
        for j in range(plot_size):
            index = (i * plot_size) + j
            if index < n_features:
                if type(data.iloc[0, index]) is str:
                    sb.countplot(x=data.columns[index], data=data, ax=ax[j / grid_size, j % grid_size])
                else:
                    sb.distplot(a=data.iloc[:, index], bins=bins, hist=hist, kde=kde, label=data.columns[index],
                                ax=ax[j / grid_size, j % grid_size], kde_kws={"shade": True})
        fig.tight_layout()


def visualize_correlations(data, annotate=False, fig_size=16):
    """
    Generates a correlation matrix heat map.
    """
    corr = data.corr()

    if annotate:
        corr = np.round(corr, 2)

    # generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    fig, ax = plt.subplots(figsize=(fig_size, fig_size * 3 / 4))
    colormap = sb.blend_palette(sb.color_palette('coolwarm'), as_cmap=True)
    sb.heatmap(corr, mask=mask, cmap=colormap, annot=annotate)
    fig.tight_layout()


def visualize_sequential_relationships(data, time='index', smooth_method=None, window=1, grid_size=4, fig_size=20):
    """
    Generates line plots to visualize sequential data.  Assumes the data frame index is time series.
    """
    # replace NaN values with 0 to prevent exceptions in the lower level API calls
    data = data.fillna(0)

    if time is not 'index':
        data = data.reset_index()
        data = data.set_index(time)

    data.index.name = None
    n_features = len(data.columns)
    plot_size = grid_size ** 2
    n_plots = n_features / plot_size if n_features % plot_size == 0 else n_features / plot_size + 1

    for i in range(n_plots):
        fig, ax = plt.subplots(grid_size, grid_size, sharex=True, figsize=(fig_size, fig_size / 2))
        for j in range(plot_size):
            index = (i * plot_size) + j
            if index < n_features:
                if type(data.iloc[0, index]) is not str:
                    if smooth_method == 'mean':
                        data.iloc[:, index] = pd.rolling_mean(data.iloc[:, index], window)
                    elif smooth_method == 'var':
                        data.iloc[:, index] = pd.rolling_var(data.iloc[:, index], window)
                    elif smooth_method == 'skew':
                        data.iloc[:, index] = pd.rolling_skew(data.iloc[:, index], window)
                    elif smooth_method == 'kurt':
                        data.iloc[:, index] = pd.rolling_kurt(data.iloc[:, index], window)

                    data.iloc[:, index].plot(ax=ax[j / grid_size, j % grid_size], kind='line',
                                             legend=False, title=data.columns[index])
        fig.tight_layout()


def visualize_transforms(X, transforms, y=None, model_type=None, n_components=2, scatter_size=50, fig_size=16):
    """
    Generates plots to visualize the data transformed by a linear or manifold algorithm.
    """
    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)

    if model_type == 'classification':
        class_count = np.count_nonzero(np.unique(y))
        colors = sb.color_palette('hls', class_count)

        for i in range(n_components - 1):
            fig, ax = plt.subplots(figsize=(fig_size, fig_size * 3 / 4))
            for j in range(class_count):
                ax.scatter(X[y == j, i], X[y == j, i + 1], s=scatter_size, c=colors[j], label=j)
            ax.set_title('Components ' + str(i + 1) + ' and ' + str(i + 2))
            ax.legend()
            fig.tight_layout()
    elif model_type == 'regression':
        for i in range(n_components - 1):
            fig, ax = plt.subplots(figsize=(fig_size, fig_size * 3 / 4))
            sc = ax.scatter(X[:, i], X[:, i + 1], s=scatter_size, c=y, cmap='Blues')
            ax.set_title('Components ' + str(i + 1) + ' and ' + str(i + 2))
            ax.legend()
            fig.colorbar(sc)
            fig.tight_layout()
    else:
        for i in range(n_components - 1):
            fig, ax = plt.subplots(figsize=(fig_size, fig_size * 3 / 4))
            ax.scatter(X[:, i], X[:, i + 1], s=scatter_size)
            ax.set_title('Components ' + str(i + 1) + ' and ' + str(i + 2))
            ax.legend()
            fig.tight_layout()


def visualize_feature_importance(feature_importance, feature_names, n_features=30, fig_size=16):
    """
    Generates a feature importance plot.
    """
    feature_importance = 100.0 * (feature_importance / feature_importance.max())
    importance = feature_importance[0:n_features] if len(feature_names) > n_features else feature_importance
    sorted_idx = np.argsort(feature_importance)
    pos = np.arange(sorted_idx.shape[0])

    fig, ax = plt.subplots(figsize=(fig_size, fig_size * 3 / 4))
    ax.set_title('Variable Importance')
    ax.barh(pos, importance[sorted_idx], align='center')
    ax.set_yticks(pos)
    ax.set_yticklabels(feature_names[sorted_idx])
    ax.set_xlabel('Relative Importance')

    fig.tight_layout()
