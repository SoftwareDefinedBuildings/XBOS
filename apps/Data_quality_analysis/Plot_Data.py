""" This script contains functions for displaying various plots.

Last modified: Feb 4 2019

Authors \n
@author Pranav Gupta <phgupta@ucdavis.edu>

"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


class Plot_Data:

    """ This class contains functions for displaying various plots.
   
    Attributes
    ----------
    count    : int
        Keeps track of the number of figures.

    """

    # Static variable to keep count of number of figures
    count = 1


    def __init__(self, figsize=(18,5)):
        """ Constructor.

        Parameters
        ----------
        figsize : tuple
            Size of figure.

        """
        self.figsize = figsize


    def correlation_plot(self, data):
        """ Create heatmap of Pearson's correlation coefficient.

        Parameters
        ----------
        data    : pd.DataFrame()
            Data to display.

        Returns
        -------
        matplotlib.figure
            Heatmap.

        """

        # CHECK: Add saved filename in result.json
        fig = plt.figure(Plot_Data.count)
        corr = data.corr()
        ax = sns.heatmap(corr)

        Plot_Data.count += 1
        return fig


    def baseline_projection_plot(self, y_true, y_pred, 
                                baseline_period, projection_period,
                                model_name, adj_r2,
                                data, input_col, output_col, model,
                                site):
        """ Create baseline and projection plots.

        Parameters
        ----------
        y_true              : pd.Series()
            Actual y values.
        y_pred              : np.ndarray
            Predicted y values.
        baseline_period     : list(str)
            Baseline period.
        projection_period   : list(str)
            Projection periods.
        model_name          : str
            Optimal model's name.
        adj_r2              : float
            Adjusted R2 score of optimal model.
        data                : pd.Dataframe()
            Data containing real values.
        input_col           : list(str)
            Predictor column(s).
        output_col          : str
            Target column.
        model               : func
            Optimal model.

        Returns
        -------
        matplotlib.figure
            Baseline plot

        """

        # Baseline and projection plots
        fig = plt.figure(Plot_Data.count)
        
        # Number of plots to display
        if projection_period:
            nrows = len(baseline_period) + len(projection_period) / 2
        else:
            nrows = len(baseline_period) / 2
        
        # Plot 1 - Baseline
        base_df = pd.DataFrame()
        base_df['y_true'] = y_true
        base_df['y_pred'] = y_pred
        ax1 = fig.add_subplot(nrows, 1, 1)
        base_df.plot(ax=ax1, figsize=self.figsize,
            title='Baseline Period ({}-{}). \nBest Model: {}. \nBaseline Adj R2: {}. \nSite: {}.'.format(baseline_period[0], baseline_period[1], 
                                                                                                            model_name, adj_r2, site))

        if projection_period:
            # Display projection plots
            num_plot = 2
            for i in range(0, len(projection_period), 2):
                ax = fig.add_subplot(nrows, 1, num_plot)
                period = (slice(projection_period[i], projection_period[i+1]))
                project_df = pd.DataFrame()
                
                try:    
                    project_df['y_true'] = data.loc[period, output_col]
                    project_df['y_pred'] = model.predict(data.loc[period, input_col])

                    # Set all negative values to zero since energy > 0
                    project_df['y_pred'][project_df['y_pred'] < 0] = 0

                    project_df.plot(ax=ax, figsize=self.figsize, title='Projection Period ({}-{})'.format(projection_period[i], 
                                                                                                        projection_period[i+1]))
                    num_plot += 1
                    fig.tight_layout()

                    Plot_Data.count += 1
                    return fig, project_df['y_true'], project_df['y_pred']
                except:
                    raise TypeError("If projecting into the future, please specify project_ind_col that has data available \
                                        in the future time period requested.")
           
        return fig, None, None


if __name__ == '__main__':
    obj = Plot_Data()