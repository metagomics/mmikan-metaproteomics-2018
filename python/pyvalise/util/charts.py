#!/usr/bin/env python

"""Charting utilities. Consolidated here so that the rest of the codebase
isn't dependent on charting implementation (currently matplotlib)."""

import matplotlib
# so that I can run without X
matplotlib.use('Agg')
import logging
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from statsmodels.graphics import gofplots
import statsmodels.api as sm
from pyvalise.util import stats as pyptide_stats
from scipy.stats import gaussian_kde
from numpy import arange
from matplotlib import colors
import numpy as np
import matplotlib.mlab as mlab
from matplotlib.lines import Line2D
from scipy.stats import cumfreq
from mpl_toolkits.mplot3d import axes3d, Axes3D

DEFAULT_COLORMAP_NAME = 'viridis'


COLORMAP_REDBLUE = plt.get_cmap('winter')

DEFAULT_LOG_BASE = 10
ALPHA_FOR_MULTISCATTER = 0.85

DEFAULT_POINTSIZE = 1

DEFAULT_AXIS_TICK_FONTSIZE = 20

__author__ = "Damon May"
__copyright__ = "Copyright (c) 2012-2014 Damon May"
__license__ = ""
__version__ = ""

logger = logging.getLogger(__name__)

# default color sequence for lines and bars. If need more colors, add more colors
BASE_COLORS = ['#0000ff',  # blue
               '#ff0000',  # red
               '#00ff00',  # green
               '#888888',  # grey
               '#ff00ff',  # purple
               '#FFFF00',  # brown?
               '#222222',  # dark grey
               '#FFA500',  # orange
               ]
COLORS = []
for i in xrange(0, 20):
    COLORS.extend(BASE_COLORS)
LINESTYLES = []
while len(LINESTYLES) < len(COLORS):
    for linestyle in ['solid', 'dashed', 'dashdot', 'dotted']:
            LINESTYLES.extend([linestyle] * len(BASE_COLORS))

COLORMAP_BASECOLORS = colors.ListedColormap(BASE_COLORS)


BASE_MARKERS = []
for m in Line2D.markers:
    try:
        if len(m) == 1 and m != ' ':
            BASE_MARKERS.append(m)
    except TypeError:
        pass
MARKERS = []
for i in xrange(0, 10):
    MARKERS.extend(BASE_MARKERS)


DEFAULT_HIST_BINS = 40

# hack for printing numeric values on piechart segments
piechart_valuesum = 0


def write_pdf(figures, pdf_file):
    """write an iterable of figures to a PDF"""
    with PdfPages(pdf_file) as pdf:
        for plot in figures:
            plot.savefig(pdf, format='pdf')


def write_png(figure, png_file):
    """
    Write a figure to a .png
    :param figure:
    :param png_file:
    :return:
    """
    figure.savefig(png_file, format='png')


def hist(values, title=None, bins=DEFAULT_HIST_BINS, color=None,
         should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
         gaussian_mus=None, gaussian_sigmas=None, axis_tick_font_size=DEFAULT_AXIS_TICK_FONTSIZE,
         x_axis_limits=None):
    """trivial histogram."""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    if not color:
        color = 'black'

    myrange = [min(values), max(values)]
    rangesize = myrange[1] - myrange[0]
    myrange = [myrange[0] - rangesize / 20, myrange[1] + rangesize / 20]
    myhist = ax.hist(values,  # histtype = "stepfilled",
            color=color, range=myrange, bins=bins)
    if gaussian_mus and gaussian_sigmas:
        assert(len(gaussian_mus) == len(gaussian_sigmas))
        for i in xrange(0, len(gaussian_mus)):
            x = np.linspace(myrange[0], myrange[1])
            dx = myhist[1][1] - myhist[1][0]
            scale = len(values) * dx
            plt.plot(x, mlab.normpdf(x, gaussian_mus[i], gaussian_sigmas[i]) * scale)
    if title:
        ax.set_title(title)
    if x_axis_limits is not None:
        plt.xlim(x_axis_limits)
    set_chart_axis_tick_fontsize(ax, axis_tick_font_size)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    return figure

def multiboxplot(valueses, title=None, labels=None, show_outliers=True):
    """multiple boxplots side by side"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    ax.boxplot(valueses, showfliers=show_outliers)
    tick_locs = list()
    for i in xrange(0, len(valueses)):
        tick_locs.append(i + 1)

    if labels:
        plt.xticks(tick_locs, labels)

    if title:
        ax.set_title(title)
    return figure

def multiviolin_fromxy(xvals, yvals, title=None, minforplot=2):
    """Turn xy-pair data into violin plots"""
    xval_yvals_map = {}
    for i in xrange(0, len(xvals)):
        if not xvals[i] in xval_yvals_map:
            xval_yvals_map[xvals[i]] = []
        xval_yvals_map[xvals[i]].append(yvals[i])
    valueses = []
    labels = []

    for xval in sorted(xval_yvals_map.keys()):
        if len(xval_yvals_map[xval]) >= minforplot:
            labels.append(xval)
            valueses.append(xval_yvals_map[xval])
    return multiviolin(valueses, title, labels)


def multiviolin(valueses, title=None, labels=None, y_axis_limits=None,
                rotate_labels=False):
    """multiple violin plots side by side"""
    figure = plt.figure()

    ax = figure.add_subplot(1, 1, 1)

    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)

    _violin_plot(ax, valueses, range(len(valueses)))


    if labels:
        tick_xs = [x for x in xrange(0, len(labels))]
        locs, ticklabels = plt.xticks(tick_xs, labels)
        if rotate_labels:
            logger.debug("Rotating tick labels 90 degrees.")
            plt.setp(ticklabels, rotation=90)
            # also, shrink the chart vertically to make room
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.3, box.width, box.height * 0.6])

    if title:
        ax.set_title(title)
    return figure


def violin_plot(values, title=None, labels=None, y_axis_limits=None,
                rotate_labels=False):
    return multiviolin([values], title, labels, y_axis_limits, rotate_labels)


def _violin_plot(ax, data, pos, bp=True, color='y'):
    """
    create violin plots on an axis.
    Borrowed from here:
    http://pyinsci.blogspot.com/2009/09/violin-plot-with-matplotlib.html
    """
    dist = max(pos) - min(pos)
    w = min(0.15 * max(dist, 1.0), 0.5)
    for d, p in zip(data, pos):
        k = gaussian_kde(d)  # calculates the kernel density
        m = k.dataset.min()  # lower bound of violin
        M = k.dataset.max()  # upper bound of violin
        x = arange(m, M, (M - m) / 100.)  # support for violin
        v = k.evaluate(x)  # violin profile (density curve)
        v = v / v.max() * w  # scaling the violin to the available space
        ax.fill_betweenx(x, p, v + p, facecolor=color, alpha=0.3)
        ax.fill_betweenx(x, p, -v + p, facecolor=color, alpha=0.3)
    if bp:
        ax.boxplot(data, notch=0, positions=pos, vert=1)


def multihist(valueses, title=None, bins=DEFAULT_HIST_BINS, colors=None,
              legend_labels=None, legend_on_chart=False, histtype='bar',
              should_normalize=False, y_axis_limits=None):
    """histogram of multiple datasets.
    valueses: a list of lists of values"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    mymin = float("inf")
    mymax = 0
    for values in valueses:
        mymax = max(mymax, max(values))
        mymin = min(mymin, min(values))
    myrange = [mymin, mymax]
    rangesize = mymax - mymin
    myrange = [myrange[0] - rangesize / 20, myrange[1] + rangesize / 20]
    if not colors:
        colors = COLORS[0:len(valueses)]
    colorind = -1

    for values in valueses:
        colorind += 1
        weights = None
        if should_normalize:
            weights = np.ones_like(values)/float(len(values))
        ax.hist(values, color=colors[colorind], alpha=0.5, range=myrange, bins=bins, histtype=histtype,
                weights=weights)
    if legend_labels:
        add_legend_to_chart(ax, legend_on_chart=legend_on_chart, labels=legend_labels)
    if title:
        ax.set_title(title)
    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)
    return figure


def multihist_skinnybar(valueses, title=None, bins=DEFAULT_HIST_BINS, colors=None,
                        legend_labels=None, legend_on_chart=False, normed=False):
    """histogram of multiple datasets.
    valueses: a list of lists of values"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    if not colors:
        colors = COLORS[0:len(valueses)]

    ax.hist(valueses, bins=bins, color=colors, normed=normed)
    if legend_labels:
        add_legend_to_chart(ax, legend_on_chart=legend_on_chart, labels=legend_labels)
    if title:
        ax.set_title(title)
    return figure


def bar(values, labels, title=None, colors=None, rotate_labels=False, axis_limits=None):
    return multibar([values], labels, title=title, colors=colors, legend_labels=None,
                    rotate_labels=rotate_labels, axis_limits=axis_limits)


def multibar(valueses, labels, title='', colors=None,
             legend_labels=None, legend_on_chart=True, rotate_labels=False,
             axis_limits=None):
    """barchart of multiple datasets.
    valueses: a list of lists of values. Should have same cardinalities"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    if not colors:
        colors = COLORS[0:len(valueses)]
    ind = -1
    for values in valueses:
        ind += 1
        xvals = [0] * len(values)
        for xind in xrange(0, len(xvals)):
            xvals[xind] = 2 * xind * len(valueses) + ind
        ax.bar(xvals, values, color=colors[ind])
    if axis_limits is not None:
        plt.ylim(axis_limits)
    tick_xs = [0] * len(labels)
    for ind in xrange(0, len(tick_xs)):
        tick_xs[ind] = 2 * ind * len(valueses)
    locs, ticklabels = plt.xticks(tick_xs, labels)
    if rotate_labels:
        logger.debug("Rotating tick labels 90 degrees.")
        plt.setp(ticklabels, rotation=90)
        # also, shrink the chart vertically to make room
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.3, box.width, box.height * 0.6])
    if legend_labels:
        add_legend_to_chart(ax, legend_on_chart=legend_on_chart, labels=legend_labels, rotate_labels=rotate_labels)
    ax.set_title(title)
    return figure


def line_plot(x_values, y_values, title=None, lowess=False,
              xlabel=None, ylabel=None,
              should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
              y_axis_limits=None, x_axis_limits=None,
              xtick_positions=None, xtick_labels=None,
              n_x_axis_ticks=None):
    """trivial line plot"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    ax.plot(x_values, y_values)

    if lowess:
        lowess = sm.nonparametric.lowess(y_values, x_values, frac=0.1)
        ax.plot(lowess[:, 0], lowess[:, 1])
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if xtick_positions:
        assert (xtick_labels is not None)
        ax.set_xticks(xtick_positions)
        ax.set_xticklabels(xtick_labels)
    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)
    if x_axis_limits is not None:
        plt.xlim(x_axis_limits)
    return figure


def lineplot_peaks(x_values, y_values, ax=None, color="black", linestyle="solid",
                   title=None, linewidth=1.0):
    """
    Make a lineplot showing peaks at the defined x_values with y_value heights
    :param x_values:
    :param y_values:
    :param ax:
    :param color:
    :param title:
    :return:
    """
    x_valueses = []
    y_valueses = []
    for i in xrange(0, len(x_values)):
        x_valueses.append([x_values[i], x_values[i]])
        y_valueses.append([0.0, y_values[i]])
    colors = [color] * len(x_values)
    linestyles = [linestyle] * len(x_values)
    return multiline(x_valueses, y_valueses, ax=ax, title=title, colors=colors,
                     linestyles=linestyles, linewidth=linewidth)


def multiline(x_valueses, y_valueses, labels=None, title=None, colors=None,
              linestyles=None, legend_on_chart=False, xlabel=None, ylabel=None,
              should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
              diff_yaxis_scales=False, x_axis_limits=None, y_axis_limits=None,
              xtick_positions=None, xtick_labels=None,
              show_markers=False, markers=None,
              axis_tick_font_size=DEFAULT_AXIS_TICK_FONTSIZE,
              draw_1to1=False, ax=None, linewidth=1.0,
              n_x_axis_ticks=None):
    """

    :param x_valueses:
    :param y_valueses:
    :param labels:
    :param title:
    :param colors:
    :param linestyles:
    :param legend_on_chart:  legend on the chart, rather than off to right
    :param xlabel:
    :param ylabel:
    :param should_logx:
    :param should_logy:
    :param log_base:
    :param diff_yaxis_scales: use different y-axis scales. Only valid for len(y_valueses)==2
    :param x_axis_limits:
    :param y_axis_limits:
    :return:
    """
    if diff_yaxis_scales and len(y_valueses) != 2:
        raise Exception("multiline: diff_yaxis_scales only meaningful if two sets of values.")
    figure = None
    if ax is None:
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
    axes = [ax]
    if not colors:
        colors = COLORS[0:len(x_valueses)]
    if not markers:
        markers = MARKERS[0:len(x_valueses)]
    if not linestyles:
        linestyles = LINESTYLES[0:len(x_valueses)]

    for i in xrange(0, len(x_valueses)):
        x_values = x_valueses[i]
        y_values = y_valueses[i]
        color = colors[i]
        if diff_yaxis_scales and i == 1:
            ax = ax.twinx()
            axes.append(ax)
        marker = None
        if show_markers:
            marker = markers[i]
        if labels:
            lines = ax.plot(x_values, y_values, color=color, label=labels[i], marker=marker, linestyle=linestyles[i],
                            linewidth=linewidth)
        else:
            lines = ax.plot(x_values, y_values, color=color, linestyle=linestyles[i], marker=marker,
                            linewidth=linewidth)
        plt.setp(lines, linewidth=linewidth)
    if draw_1to1:
        min_xval = min(min(xval) for xval in x_valueses)
        max_xval = max(max(xval) for xval in x_valueses)
        min_yval = min(min(yval) for yval in y_valueses)
        max_yval = max(max(yval) for yval in y_valueses)
        values_1to1 = [max(min_xval,  min_yval), min(max_xval, max_yval)]
        # use copies of x and y values sets, because editing
        x_valueses = x_valueses[:]
        y_valueses = y_valueses[:]
        x_valueses.append(values_1to1)
        y_valueses.append(values_1to1)
        ax.plot(values_1to1, values_1to1, color='#666666', linestyle='dotted')
    set_chart_axis_tick_fontsize(ax, axis_tick_font_size)
    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)
    if x_axis_limits is not None:
        plt.xlim(x_axis_limits)
    if title:
        ax.set_title(title)
    # Now add the legend with some customizations.
    if labels:
        for ax in axes:
            add_legend_to_chart(ax, legend_on_chart=legend_on_chart)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if xtick_positions:
        assert(xtick_labels is not None)
        ax.set_xticks(xtick_positions)
        ax.set_xticklabels(xtick_labels)
    for ax in axes:
        ax.set_aspect(1./ax.get_data_ratio())
    if n_x_axis_ticks:
        plt.locator_params(axis='x', nticks=n_x_axis_ticks)
    return figure


def cdfs(valueses, xlabel='value', labels=None, title='CDF', n_bins=500):
    """
    Plot one or more cumulative density functions
    :param valueses:
    :param xlabel:
    :param labels:
    :param title:
    :param n_bins:
    :return:
    """
    x_valueses = []
    y_valueses = []
    logger.debug("cdfs")
    for values in valueses:
        freq = cumfreq(values, n_bins)
        x_values = [freq.lowerlimit + x * freq.binsize for x in xrange(0, n_bins)]
        y_values = freq.cumcount / len(values)
        logger.debug("binsize: %f" % freq.binsize)
        logger.debug("range: %f" % (freq.binsize * n_bins))
        logger.debug("y range: %f - %f" % (min(y_values), max(y_values)))
        x_valueses.append(x_values)
        y_valueses.append(y_values)

    return multiline(x_valueses, y_valueses,
                     title=title,
                     xlabel=xlabel,
                     ylabel='density',
                     labels=labels)


def multiscatter(x_valueses, y_valueses, title=None,
                 xlabel='', ylabel='', pointsize=DEFAULT_POINTSIZE, labels=None,
                 should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
                 legend_on_chart=False, colors=COLORS, rotate_labels=False,
                 draw_1to1=False):
    """
    Scatterplot multiple sets of values in different colors
    :param x_valueses:
    :param y_valueses:
    :param title:
    :param xlabel:
    :param ylabel:
    :param pointsize: If one value, use that value. If a list, use that list in order.
    :param colors:
    :param cmap:
    :param show_colorbar:
    :param should_logx:
    :param should_logy:
    :param log_base:
    :return:
    """
    assert(len(x_valueses) == len(y_valueses))

    for i in xrange(0, len(x_valueses)):
       assert(len(x_valueses[i]) == len(y_valueses[i]))
    if type(pointsize) == list:
        pointsizes = pointsize
        assert len(pointsizes) == len(x_valueses)
    else:
        pointsizes = [pointsize] * len(x_valueses)
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    if title:
        ax.set_title(title)
    logger.debug("len(x_valueses): %d" % len(x_valueses))

    for i in xrange(0, len(x_valueses)):
        logger.debug("multiscatter set %d, color %s" % (i, colors[i]))
        ax.scatter(x_valueses[i], y_valueses[i], s=pointsizes[i], facecolors=colors[i], edgecolors='none',
                   alpha=ALPHA_FOR_MULTISCATTER)
    if labels:
        add_legend_to_chart(ax, legend_on_chart=legend_on_chart, labels=labels, rotate_labels=rotate_labels)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if draw_1to1:
        lims = [
            np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
            np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
        ]
        ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0)
        ax.set_xlim(lims)
        ax.set_ylim(lims)
    ax.set_aspect(1./ax.get_data_ratio())
    return figure


def hexbin(x_values, y_values, title=None,
           xlabel='', ylabel='', gridsize=100, should_log_color=False,
           cmap=None, show_colorbar=True,
           should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
           x_axis_limits=None, y_axis_limits=None):
    """
    hexbin plot
    :param x_values:
    :param y_values:
    :param title:
    :param xlabel:
    :param ylabel:
    :param gridsize:
    :param should_log_color: log-transform the color scale?
    :param cmap:
    :param show_colorbar:
    :return:
    """
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    bins = None
    if should_log_color:
        bins = 'log'
    myhexbin = ax.hexbin(x_values, y_values, gridsize=gridsize, bins=bins,
                         cmap=cmap)
    if title:
        ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if show_colorbar:
        plt.colorbar(myhexbin)
    if x_axis_limits is not None:
        plt.xlim(x_axis_limits)
    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)
    return figure


def scatterplot(x_values, y_values, title=None, lowess=False,
                xlabel='', ylabel='', pointsize=1, draw_1to1 = False,
                colors=None, cmap=DEFAULT_COLORMAP_NAME, show_colorbar=False,
                should_logx=False, should_logy=False, log_base=DEFAULT_LOG_BASE,
                alpha=0.5, axis_tick_font_size=DEFAULT_AXIS_TICK_FONTSIZE,
                n_x_axis_ticks=None, x_axis_limits=None, y_axis_limits=None):
    """
    scatter plot
    :param x_values:
    :param y_values:
    :param title:
    :param lowess:
    :param xlabel:
    :param ylabel:
    :param pointsize:
    :param draw_1to1:
    :param colors:
    :param cmap:
    :param show_colorbar:
    :return:
    """
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    if colors is not None:
        myscatter = ax.scatter(x_values, y_values, s=pointsize, c=colors, cmap=cmap, edgecolors='none', alpha=alpha)
    else:
        myscatter = ax.scatter(x_values, y_values, s=pointsize, cmap=cmap, edgecolors='none', alpha=alpha)
    if draw_1to1:
        lims = [
            np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
            np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
        ]
        logger.debug("scatterplot setting both axis limits to %s" % str(lims))
        ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0)
        ax.set_xlim(lims)
        ax.set_ylim(lims)
    set_chart_axis_tick_fontsize(ax, axis_tick_font_size)
    if title:
        ax.set_title(title)
    if lowess:
        lowess = sm.nonparametric.lowess(y_values, x_values, frac=0.1)
        ax.plot(lowess[:, 0], lowess[:, 1])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if show_colorbar:
        plt.colorbar(myscatter)
    if n_x_axis_ticks:
        plt.locator_params(axis='x', nticks=n_x_axis_ticks)
    if x_axis_limits is not None:
        plt.xlim(x_axis_limits)
    if y_axis_limits is not None:
        plt.ylim(y_axis_limits)
    return figure


def qqplot_2samples(vals1, vals2, title=None,
                    xlabel='sample 1', ylabel='sample 2'):
    """qqplot of the distributions of two samples. The first is taken as
    the reference and the second is plotted against it"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    gofplots.qqplot(pyptide_stats.list_to_array(vals2),
                    pyptide_stats.get_scipy_distribution(pyptide_stats.list_to_array(vals1)),
                    line='45', ax=ax)
    if title:
        ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return figure


def pie(values, title=None, labels=None,
        colors=('b', 'g', 'r', 'c', 'm', 'y', 'k', 'w')):
    """trivial pie chart"""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    ax.pie(values, autopct='%.2f%%', labels=labels, colors=colors)
    if title:
        ax.set_title(title)
    return figure


def heatmap_direct(values_ndarray, xlabel=None, ylabel=None, title=None,
                   show_colorbar=True, colormap=None, width_proportion=1.0, height_proportion=1.0):
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    cax = ax.imshow(values_ndarray, cmap=colormap,
                   vmin=values_ndarray.min(), vmax=values_ndarray.max())
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if show_colorbar:
        figure.colorbar(cax)
#    # scale the heatmap's size
#    box = ax.get_position()
#    ax.set_position([box.x0 + box.width * (1.0 - width_proportion), box.y0 + box.height * (1.0 - height_proportion),
#                     box.width * width_proportion, box.height * height_proportion])
    return figure

def heatmap(values_ndarray, xtick_positions=None, xlabels=None,
            ytick_positions=None, ylabels=None, colormap='gray',
            xlabel=None, ylabel=None, title=None, show_colorbar=True,
            width_proportion=1.0, height_proportion=1.0):
    """heatmap. You want axis labels, you provide 'em."""
    figure = plt.figure()
    ax = figure.add_subplot(1, 1, 1)
    cax = ax.pcolor(values_ndarray, cmap=colormap, vmin=values_ndarray.min(), vmax=values_ndarray.max())
    if xtick_positions:
        assert(xlabels is not None)
        ax.set_xticks(xtick_positions)
        ax.set_xticklabels(xlabels)
    if ytick_positions:
        assert(ylabels is not None)
        ax.set_yticks(ytick_positions)
        ax.set_yticklabels(ylabels)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    if show_colorbar:
        figure.colorbar(cax)
    # scale the heatmap's size
    box = ax.get_position()
    ax.set_position([box.x0 + box.width * (1.0 - width_proportion), box.y0 + box.height * (1.0 - height_proportion),
                     box.width * width_proportion, box.height * height_proportion])

    return figure


def surface(x_values, y_values, z_values, title=None,
            xlabel=None, ylabel=None,
            should_logx=False, should_logy=False,
            log_base=DEFAULT_LOG_BASE):
    """3D surface plot"""
    figure = plt.figure()
    ax = figure.gca(projection='3d')
    ax.plot_surface(x_values, y_values, z_values)
    if should_logx:
        plt.xscale('log', basex=log_base)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return figure


def scatter3d(x_values, y_values, z_values, title=None,
                xlabel='', ylabel='', zlabel='', pointsize=1, alpha=0.5,
                colors=None, should_logx=False, should_logy=False, cmap=None,
              log_base=DEFAULT_LOG_BASE, show_colorbar=False, lines_coords=None):
    """
    3D scatterplot. Right now there's some special-purpose stuff in her for overlaying lines
    :param x_values:
    :param y_values:
    :param z_values:
    :param title:
    :param xlabel:
    :param ylabel:
    :param zlabel:
    :param pointsize:
    :param alpha:
    :param colors:
    :param should_logx:
    :param should_logy:
    :param cmap:
    :param log_base:
    :param show_colorbar:
    :param lines_coords:
    :return:
    """
    figure = plt.figure()
    ax = Axes3D(figure)
    #ax = figure.add_subplot(111, projection='3d')
    myscatter = None
    marker_args = dict(s=pointsize, alpha=alpha, cmap=cmap, linewidths=0,)
    if colors is not None:
        myscatter = Axes3D.scatter(ax, x_values, y_values, z_values, c=colors, **marker_args)
    else:
        myscatter = Axes3D.scatter(ax, x_values, y_values, z_values, **marker_args)
    if lines_coords is not None:
        for line_coords in lines_coords:
            Axes3D.plot(ax, [x[0] for x in line_coords],
                        [x[1] for x in line_coords],
                        zs=[x[2] for x in line_coords],
                        c='#888888', alpha=0.35, linewidth=0.3)

    if should_logx:
        plt.xscale('log', basex=log_base)
    if should_logy:
        plt.yscale('log', basey=log_base)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if zlabel:
        ax.set_zlabel(ylabel)
    if title:
        ax.set_title(title)
    if show_colorbar:
        plt.colorbar(myscatter)
    return figure


def add_legend_to_chart(ax, legend_on_chart=False, labels=None, rotate_labels=False):
    """
    add a legend to the chart. By default, overlapping the chart
    :param ax:
    :param legend_off_chart: move the legend entirely off.
    :return:
    """
    logger.debug("add_legend_to_chart")
    if legend_on_chart:
        logger.debug("Printing legend on chart")
        if labels:
            legend = ax.legend(labels, bbox_to_anchor=(1.1, 1.05), shadow=True, borderaxespad=0.)
        else:
            legend = ax.legend(bbox_to_anchor=(1.1, 1.05), shadow=True, borderaxespad=0.)
    else:
        logger.debug("Printing legend off chart")
        box = ax.get_position()
        scale_factor = 0.8
        if labels:
            MIN_SCALE_FACTOR = 0.5
            MAX_SCALE_FACTOR = 0.9
            MIN_LABELLEN = 4
            MAX_LABELLEN = 30
            labellen = max([len(label) for label in labels])
            scale_factor = MIN_SCALE_FACTOR + \
                           float(MAX_LABELLEN - labellen) / (MAX_LABELLEN - MIN_LABELLEN) * \
                           (MAX_SCALE_FACTOR - MIN_SCALE_FACTOR)
        ax.set_position([box.x0, box.y0 + box.height * (1 - scale_factor) / 2, box.width * scale_factor, box.height * scale_factor])
        set_chart_axis_tick_fontsize(ax, scale_factor * ax.get_xticklabels()[0].get_fontsize())
        if labels:
            legend = ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0.5))
        else:
            legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
    frame = legend.get_frame()
    frame.set_facecolor('0.90')

    if rotate_labels:
        locs, ticklabels = plt.xticks()
        logger.debug("Rotating tick labels 90 degrees.")
        plt.setp(ticklabels, rotation=90)

    for label in legend.get_lines():
        label.set_linewidth(1.5)  # the legend line width


def set_chart_axis_tick_fontsize(ax, fontsize):
    for item in (ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(fontsize)


def big_hist_line(big_hist_data, xlabel='', ylabel=None, title='', plot_proportion=False,
                  truncate_at_last_nonzero=False):
    """

    :param big_hist_data:
    :param xlabel:
    :param ylabel:
    :param title:
    :param plot_proportion:
    :return:
    """
    return big_hist_multiline([big_hist_data], xlabel=xlabel, ylabel=ylabel, title=title,
                              plot_proportion=plot_proportion,
                              truncate_at_last_nonzero=truncate_at_last_nonzero)


def big_hist_multiline(big_hist_datas, xlabel='', ylabel=None, title='', labels=None,
                       plot_proportion=False, truncate_at_last_nonzero=False):
    """
    Plot a multi-line plot from BigHistData data objects.
    Requires min_shown_value and max_shown_value are same for all the inputs
    :param big_hist_datas:
    :param xlabel:
    :param ylabel:
    :param title:
    :param labels:
    :param plot_proportion
    :return:
    """
    assert(len(set([big_hist_data.min_shown_value for big_hist_data in big_hist_datas])) == 1)
    assert(len(set([big_hist_data.max_shown_value for big_hist_data in big_hist_datas])) == 1)
    xvalues = big_hist_datas[0].generate_xvals()
    xvalueses = []
    yvalueses = []
    if not ylabel:
        if plot_proportion:
            ylabel = 'proportion'
        else:
            ylabel = 'count'
    for big_hist_data in big_hist_datas:
        xvalueses.append(xvalues)
        yvalues = big_hist_data.countdata
        if plot_proportion:
            yvalues = big_hist_data.generate_proportion_yvals()
        yvalueses.append(yvalues)
    if truncate_at_last_nonzero:
        last_bin = 0
        for yvalues in yvalueses:
            for i in xrange(last_bin, len(yvalues)):
                if yvalues[i] > 0:
                    last_bin = i
        logger.debug("big_hist_multiline truncated %d to %d." % (len(xvalueses[0]), last_bin))
        for i in xrange(0, len(xvalueses)):
            xvalueses[i] = xvalueses[i][0:last_bin+1]
            yvalueses[i] = yvalueses[i][0:last_bin+1]

    return multiline(xvalueses, yvalueses, title=title, xlabel=xlabel, ylabel=ylabel, labels=labels)


def big_hist_multihist_proportion(big_hist_datas, title='', labels=None,
                                  bins=None):
    """
    Plot a multi-line plot from BigHistData data objects.
    Requires min_shown_value and max_shown_value are same for all the inputs
    :param big_hist_datas:
    :param xlabel:
    :param ylabel:
    :param title:
    :param labels:
    :param plot_proportion
    :return:
    """
    assert(len(set([big_hist_data.min_shown_value for big_hist_data in big_hist_datas])) == 1)
    assert(len(set([big_hist_data.max_shown_value for big_hist_data in big_hist_datas])) == 1)
    values_forhist = big_hist_datas[0].generate_xvals()
    xvalueses = []
    for big_hist_data in big_hist_datas:
        yvals = big_hist_data.generate_proportion_yvals()
        xvalues = []
        for i in xrange(0, len(yvals)):
            n_thishist_thisval = int(1000 * yvals[i])
            xvalues.extend([values_forhist[i]] * n_thishist_thisval)
        xvalueses.append(xvalues)
    bins = DEFAULT_HIST_BINS
    if len(values_forhist) < bins:
        bins = len(values_forhist) + 5
    return multihist_skinnybar(xvalueses, title=title, bins=bins, legend_labels=labels, normed=True)


class BigHistData:
    """
    A data structure for storing count data for big datasets, to be plotted as a line or multiline plot
    """
    def __init__(self, max_shown_value, min_shown_value=0, binsize=1.0):
        assert(max_shown_value > min_shown_value)
        self.min_shown_value = min_shown_value
        self.max_shown_value = max_shown_value
        self.binsize = binsize
        self.n_bins = int((max_shown_value - min_shown_value + 1) / binsize) + 1
        self.countdata = [0] * self.n_bins
        self.min_real_value = float('inf')
        self.max_real_value = float('-inf')

    def add_value(self, value):
        bin_idx = self.calc_idx_for_value(value)
        #print("add_value, value=%f, bin=%d, binsize=%f, minval=%f" % (cropped_value, bin_idx, self.binsize, self.min_shown_value))
        self.countdata[bin_idx] += 1
        self.min_real_value = min(value, self.min_real_value)
        self.max_real_value = max(value, self.max_real_value)

    def get_count_for_value(self, value):
        return self.countdata[self.calc_idx_for_value(value)]

    def calc_idx_for_value(self, value):
        cropped_value = max(self.min_shown_value, min(value, self.max_shown_value))
        bin_idx = int((cropped_value - self.min_shown_value) / self.binsize)
        return bin_idx

    def generate_xvals(self):
        return [self.min_shown_value + self.binsize * bin_idx for bin_idx in xrange(0, self.n_bins)]

    def generate_proportion_yvals(self):
        value_sum = sum(self.countdata)
        proportion_yvals = self.countdata
        if value_sum > 0:
            proportion_yvals = [float(y) / value_sum for y in self.countdata]
        return proportion_yvals

    def print_min_max_real_values(self):
        print("min=%f, max=%f" % (self.min_real_value, self.max_real_value))

    def __str__(self):
        result = "BigHistData:\nmin=%f, max=%f\n" % (self.min_real_value, self.max_real_value)
        for i in xrange(0, len(self.countdata)):
            if i > 0:
                result = result + ","
            result = result + str(self.countdata[i])
        result = result + '\n'
        return result
