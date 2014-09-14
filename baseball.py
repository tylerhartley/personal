# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # Baseball salary analysis
# ## Flow
# 1. Increase in total league salary over time As compared to a variety of market metrics
# 2. Team salary graph over time. Point out notable teams. Compare both %spending and #rank
# 3. The big question - does money buy wins?
#     1. All year plot of wins (or win%) vs %spending. Draw conclusions
#     2. Plot of Slope of line from year to year with 95% CI error bars
#     3. dStd over time - has the spending of money become more or less diverse?
# 4. Assuming we see a minimal correlation between money and success, what is our hypothesis? Of late - 6 yr team ownership. Plot wins vs salary but color/size dots based on team avg age.

# <codecell>

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import datetime
import matplotlib
import statsmodels.api as sm
#import wolframalpha as wa

# <codecell>

# Some payroll data from http://www.baseballchronology.com/Baseball/Years/1977
try:
    xl_file = pd.ExcelFile(r'C:\Users\Tyler\Google Drive\DOCUMENTS\Blog Data\BaseballStats.xlsx')
except:
    xl_file = pd.ExcelFile(r'C:\Users\thartley\Desktop\BaseballStats.xlsx')
salaries = xl_file.parse(sheetname='Salaries')
allstats = xl_file.parse(sheetname='Statistics')

allstats.Team = allstats.Team.map(lambda x: x.replace(u'\xa0', u" ")) #ascii issue; thanks, excel
allstats.Playoffs.fillna('None', inplace=True)
allstats.Playoffs = allstats.Playoffs.map(lambda x: x.replace(u'\xa0', u" "))


allstats = pd.merge(allstats, salaries, how='left')
# let's play with a subset of data anyways
stats = allstats.reindex(columns=['Team', 'Year', 'W', 'L', 'Salary', 'Playoffs'])
stats.columns = [c.lower() for c in stats.columns]
del salaries # clear up some mem
del allstats # clear up some mem

# <codecell>

# Clean up salary data because, again, Excel is the worst.
def to_float(x):
    try:
        return float(x)    
    except:
        return float(x.replace(',','').strip())
    
stats.salary = stats.salary.map(to_float)

# <codecell>

# Fix the weird MLB name issues
def team_groups(name):
    # Edge cases - 
    # 1. Anaheim/LA/Etc Angels
    # 2. Devil Rays vs Rays
    # 3. Miami/Florida Marlins
    if 'Angels' in name:
        return 'Los Angeles Angels'
    elif 'Tampa Bay' in name:
        return 'Tampa Bay Rays'
    elif 'Marlins' in name:
        return 'Miami Marlins'
    else:
        return name

stats.team = stats.team.map(team_groups)

# <codecell>

# Let's just look at years where we have salary info
stats = stats[stats.year > 1976].reset_index(drop=True)

# <codecell>

league_salary = stats.groupby('year').salary.sum()
league_salary.index = league_salary.index.map(lambda x: datetime.datetime(x, 1, 1, 0, 0, 0))

# <headingcell level=1>

# Total League Salary

# <codecell>

try:
    ff = pd.ExcelFile(r'C:\Users\thartley\Documents\Dropbox\prices.xlsx')
except:
    ff = pd.ExcelFile('C:\Users\Tyler\Documents\My Dropbox\prices.xlsx')
    nd = pd.ExcelFile(r'C:\Users\Tyler\Desktop\nasdaq.xlsx')
                      
incomes = ff.parse('household')
incomes = incomes[incomes.year > 1976].sort(columns='year').reset_index(drop=True)

textbooks = ff.parse('textbooks')
#textbooks = pd.DataFrame([textbooks.ix[i] for i in range(0, len(textbooks), 12)])
textbooks['year'] = textbooks.month.map(lambda x: x.year)
textbooks = textbooks[textbooks.year > 1976].reset_index(drop=True)

nasdaq = nd.parse('table (2)').sort(columns='Date')
nasdaq.index = nasdaq.Date
nasdaq = nasdaq.Close

nominal = incomes.nominal
nominal.index = incomes.year.map(lambda x: datetime.datetime(x, 1, 1, 0, 0, 0))
textbook = textbooks.CPI
textbook.index = textbooks.month

# <codecell>

fig = plt.figure(figsize=(12,8))
plt.rc('font', size=16)
cm = plt.get_cmap('Blues')
ax = fig.add_subplot(111, axisbg='#E0E0E0')
linewidth=3
alpha = 0.8
num_lines = 4

(nominal/nominal[0]).plot(color=cm(2./num_lines), linewidth=linewidth, label='Median US Income', alpha=alpha)
(textbook/textbook[0]).plot(color=cm(3./num_lines), linewidth=linewidth, style='--', label='College Textbooks', alpha=alpha)
(nasdaq/nasdaq[0]).plot(color=cm(4./num_lines), linewidth=linewidth, label='NASDAQ', alpha=alpha)
(league_salary/float(league_salary[0])).plot(color='g', linewidth=4, marker='', label='MLB Salaries')

#http://www.etforecasts.com/products/ES_pcww1203.htm
leg = plt.legend(loc='upper left')
ax.grid(axis='y', linewidth=2, ls='-', color='#ffffff')
ax.grid(axis='x')
ax.set_axisbelow(True)

#ax.tick_params(labelsize=16)
ax.set_xlabel('Year', fontsize=20)
ax.set_ylabel('Fold Change', fontsize=20)

ax.set_title("Total MLB Salaries since 1977 CBA", 
             fontdict={'size':24, 'fontweight':'bold'})
#ax.set_position([0, 0.2, 1, 0.8])

ax.text(80, -15.0, 'Source: stuff\nmorestuff\n   Even more stuffff')
plt.tight_layout()
plt.savefig(r'C:\Users\Tyler\Desktop\foo.png', dpi=300)

# <headingcell level=1>

# Team Salary over Time

# <codecell>

# Find the team rank in salary for each year
def add_rank(group):
    group['rank_salary'] = group.salary.rank(ascending=False)
    return group
stats = stats.groupby('year').apply(add_rank)

# Compute the number of standard deviations above the mean
def add_median(group):
    group['std_salary'] = (group.salary - group.salary.mean())/group.salary.std()
    return group
stats = stats.groupby('year').apply(add_median)

# Compute the MAD (median absolute deviation)
def add_mad(group):
    median = group.salary.median()
    mad = (group.salary - median).abs().median()*1.4826
    group['mad_salary'] = (group.salary - median)/mad
    return group
stats = stats.groupby('year').apply(add_mad)

# <codecell>

byteam = stats.groupby('team')

# <codecell>

plt.rc('font', size=16)
cm = plt.get_cmap('Blues')
fig = plt.figure(figsize=(14,9))
ax = fig.add_subplot(111, axisbg='#E0E0E0')

for i, g in byteam:
    kwargs = {'color':cm(0.8), 'zorder':1,
            'alpha':0.4, 'linewidth':3,
            'label':None
            }
    if 'Yankees' in i:
        kwargs = {'color':'k', 'zorder':3,
            'alpha':1, 'linewidth':4,
            'label':'Yankees'
            }
        label = 'Yankees'
    if 'Red Sox' in i:
        kwargs = {'color':'r', 'zorder':2,
            'alpha':1, 'linewidth':4,
            'label':'Red Sox'
            }
    if 'Oakland' in i:
        kwargs = {'color':'#005C5C', 'zorder':2,
            'alpha':1, 'linewidth':4,
            'label':'A\'s'
            }
    
    plt.plot(g.year, g.mad_salary, **kwargs)
    
ax.grid(axis='y', linewidth=2, ls='-', color='#ffffff')
ax.set_axisbelow(True)
ax.set_xlabel('Year', fontsize=20)
ax.set_ylabel('# Deviations from the Median', fontsize=20)
formatter = matplotlib.ticker.FormatStrFormatter('%0.0f')
ax.yaxis.set_major_formatter(formatter)
ax.set_title("Per-Team Salary since 1977", fontdict={'size':24, 'fontweight':'bold'})
ax.legend(loc='upper left')

#plt.savefig(r'C:\Users\Tyler\Desktop\foo.png', dpi=300)

# <headingcell level=1>

# 3. Wins vs Cost

# <codecell>

# Find the team rank in salary for each year
def add_rank(group):
    group['rank_salary'] = group.salary.rank(ascending=False)
    return group
stats = stats.groupby('year').apply(add_rank)

# Compute the number of standard deviations above the mean
def add_median(group):
    group['std_salary'] = (group.salary - group.salary.mean())/group.salary.std()
    return group
stats = stats.groupby('year').apply(add_median)

# Compute the MAD (median absolute deviation)
def add_mad(group):
    median = group.salary.median()
    mad = (group.salary - median).abs().median()*1.4826
    group['mad_salary'] = (group.salary - median)/mad
    return group
stats = stats.groupby('year').apply(add_mad)

# Add Win%
stats['wpct'] = stats.w.astype(float)/(stats.w + stats.l)

# <codecell>

metric = 'mad_salary'
step = 10
for start_year in range(1975, 2014, step):

    decade = stats[(stats.year >= start_year) & (stats.year < start_year+step)]
    x = decade[metric].as_matrix()
    x = sm.add_constant(x)
    est = sm.OLS(decade['wpct'], x)

    res = est.fit()
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.scatter(decade[metric], decade.wpct, s=40, alpha=0.5)
    
    #decade.plot(x=metric, y='w', kind='scatter', ax=ax, )
    team = decade[decade.team.str.contains('Athletics')]
    plt.scatter(team[metric], team.wpct, c='y', s=80)
    
    #decade[decade.team.str.contains('Athletics')].plot(x=metric, y='w', color='y', style='.', markersize=30, ax=ax)
    team = decade[decade.team.str.contains('Yankees')]
    plt.scatter(team[metric], team.wpct, c='k', s=80)

    fakedata = np.arange(decade[metric].min(), decade[metric].max(), 0.2)
    fakedata = sm.add_constant(fakedata)
    y_hat = res.predict(fakedata)
    plt.plot(fakedata[:,1], y_hat, c='r')
    plt.title("%s to %s = %0.3f"%(start_year, start_year+step-1, res.params[1]))
    
    #res.summary()
    

# <headingcell level=2>

# Bar graph of average wins for each quartile

# <codecell>

stats['quartile'] = pd.qcut(stats.mad_salary, q=[0, .25, .5, .75, 1.], labels=['1', '2', '3', '4'])
quartiles = stats.groupby('quartile')

# <codecell>

from statsmodels.stats.multicomp import MultiComparison
salarydata = MultiComparison(stats.w, stats.quartile)
res = salarydata.tukeyhsd()
#out = res.plot_simultaneous('1')

# <codecell>

stats[stats.year > 1994].boxplot(column='wpct', by='quartile', notch=True)

# <codecell>

f,(ax,ax2) = plt.subplots(2,1,sharex=True)
ax = quartiles.wpct.mean().plot(kind='bar')
ax.set_ylim([0.4, 0.6])

d = .015 # how big to make the diagonal lines in axes coordinates
# arguments to pass plot, just so we don't keep repeating them
kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
ax.plot((-d,+d),(-d,+d), **kwargs)      # top-left diagonal
ax.plot((1-d,1+d),(-d,+d), **kwargs)    # top-right diagonal

kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
ax2.plot((-d,+d),(1-d,1+d), **kwargs)   # bottom-left diagonal
ax2.plot((1-d,1+d),(1-d,1+d), **kwargs) # bottom-right diagonal

# <codecell>

quartiles.wpct.mean() * 2

# <codecell>

width

# <codecell>

ind + margin

# <codecell>

import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(8,6))
gs = gridspec.GridSpec(2,1, height_ratios=[6,1])
ax = plt.subplot(gs[0])
ax2 = plt.subplot(gs[1])

margin = 0.1
width = 1.-2*margin
ind = np.arange(4)
xdata = ind + margin

yl = .0
d = .015 # how big to make the diagonal lines in axes coordinates
# arguments to pass plot, just so we don't keep repeating them
kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
ax.plot((yl-d,yl+d),(-d,+d), **kwargs)      # top-left diagonal
ax.plot((1-d,1+d),(-d,+d), **kwargs)    # top-right diagonal
ax.set_xticks(np.arange(-0.2, 4.))

kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
ax2.plot((-d,+d),(1-d*6,1+d*6), **kwargs)   # bottom-left diagonal, multiply by same ratio used in gridspec height
ax2.plot((1-d,1+d),(1-d*6,1+d*6), **kwargs) # bottom-right diagonal,  multiply by same ratio used in gridspec height


pts = quartiles.wpct.mean()
# plot the same data on both axes
ax.bar(xdata, pts, width, yerr=quartiles.wpct.std())
ax2.bar(xdata, pts, width)



# zoom-in / limit the view to different portions of the data
ax.set_ylim(.4,.6) # outliers only
ax2.set_ylim(0,.04) # most of the data

"""
# hide the spines between ax and ax2
ax.spines['bottom'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax.xaxis.tick_top()
ax.tick_params(labeltop='off') # don't put tick labels at the top
ax2.xaxis.tick_bottom()

ax2.set_yticks([0.0])
ax2.set_xticks(ind+0.5)
ax2.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
"""

#plt.tight_layout()

# <codecell>

quartiles.playoffs.agg(lambda x: np.mean(x > 0)).plot(kind='bar')

# <headingcell level=1>

# Heatmap of wins vs cost

# <codecell>

def renum_playoffs(playoff):
    if 'None' in playoff:
        return 0
    if 'NLWC' in playoff or 'ALWC' in playoff or 'LDS' in playoff:
        return 1
    elif 'ALCS' in playoff or 'NLCS' in playoff:
        return 2
    elif 'Lost WS' in playoff:
        return 3
    elif 'Won' in playoff:
        return 4
    
stats.playoffs = stats.playoffs.map(renum_playoffs)

# <codecell>

fig = plt.figure(figsize=(10,8))
#plt.imshow(heatmap, extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], aspect='auto', 
           #interpolation='None')
#fig = plt.figure()
c = stats.playoffs > 3
out = plt.hexbin(stats.std_salary, stats.wpct, C=c, gridsize=15, cmap=plt.cm.YlOrRd, reduce_C_function=np.sum)
plt.axis('normal')
plt.colorbar()
plt.title("Number of WS Winners")
plt.xlabel("Std from the mean")
plt.ylabel("Win Percenage")

# <headingcell level=1>

# Percent of teams in each std group to make playoffs/win WS

# <codecell>

# find num of teams in each bin group
al, locs = np.histogram(stats.std_salary, bins=range(-2,5))
po, locs = np.histogram(stats[stats.playoffs > 0].std_salary, bins=range(-2,5))

plt.bar(locs[:-1]-.5, np.array(po).astype(float)/al, 0.8)

# <headingcell level=2>

# Percent of teams in each quartile to make playoffs/win WS

# <codecell>

stats.std_salary.quantile(.25)

# <codecell>

import IPython
ip=IPython.get_ipython()
ip.config.ProfileDir

# <codecell>

groups = [[1.04, 0.96],
          [1.69, 4.02]]
for a, b in enumerate(groups):
    print a
    print b

# <codecell>

plt.figure(figsize=(7,7), dpi=300)

groups = [1.04, 0.96, 2.2]
group_labels = ["G1", "G2", "G3"]
num_items = len(group_labels)
# This needs to be a numpy range for xdata calculations
# to work.
ind = np.arange(num_items)

# Bar graphs expect a total width of "1.0" per group
# Thus, you should make the sum of the two margins
# plus the sum of the width for each entry equal 1.0.
# One way of doing that is shown below. You can make
# The margins smaller if they're still too big.
margin = 0.05
width = (1.-2.*margin)

s = plt.subplot(1,1,1)
#for num, vals in enumerate(groups):
#print "plotting: ", groups
# The position of the xdata must be calculated for each of the two data series
xdata = ind+margin
# Removing the "align=center" feature will left align graphs, which is what
# this method of calculating positions assumes
gene_rects = plt.bar(xdata, groups, width)


# You should no longer need to manually set the plot limit since everything 
# is scaled to one.
# Also the ticks should be much simpler now that each group of bars extends from
# 0.0 to 1.0, 1.0 to 2.0, and so forth and, thus, are centered at 0.5, 1.5, etc.
s.set_xticks(ind+0.5)
s.set_xticklabels(group_labels)

# <codecell>

import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(8,6))
gs = gridspec.GridSpec(2,1, height_ratios=[6,1])
ax = plt.subplot(gs[0])
ax2 = plt.subplot(gs[1])

margin = 0.1
width = 1.-2*margin
ind = np.arange(4)
xdata = ind + margin

pts = quartiles.wpct.mean()
# plot the same data on both axes

ax2.bar(xdata, pts, width)

# zoom-in / limit the view to different portions of the data

ax2.set_ylim(0,.04) # most of the data

# hide the spines between ax and ax2

ax2.spines['top'].set_visible(False)

ax2.xaxis.tick_bottom()

ax2.set_yticks([0.0])
ax2.set_xticks(ind+0.5)
ax2.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
#ax.set_xticks(ind+width/2); ax2.set_xticks(ind+width/2)



# <codecell>

