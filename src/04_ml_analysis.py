# author: Group 315 (Sarah Weber)
# date: 2020-01-22

"""Conducts feature selection and then data analysis for the UFC data.

Usage: src/04_ml_analysis.py --input_path=<input_path> --out_path=<out_path> --out_path_csv=<out_path_csv>

Options:

--input_path=<input_pathn>                      The path file for the inputs for train and test data
--out_path=<output_path>                         The path of the directory to save output of analysis
--out_path_csv=<output_path_csv>                 The path of the directory to save output to for csv files


Example: python src/04_ml_analysis.py --input_path=data/02_preprocessed/ --out_path=analysis/figures/ --out_path_csv=analysis/
"""

from docopt import docopt
import requests
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFE, RFECV
import warnings
warnings.simplefilter(action='ignore', category=Warning)
import altair as alt
from sklearn.metrics import classification_report
from sklearn.metrics import plot_confusion_matrix
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 28})

opt = docopt(__doc__)

def main(input_path, out_path, out_path_csv):
  """
  Takes in input paths to data and the output folders and conducts a RFE CV search
  to find the best features for a logisitic regression model.

  Parameters
  ----------
  input_path_Xtrain: str
      The directory path and file of X_train.csv
  input_path_ytrain: str
      The directory path and file of y_train.csv
  input_path_Xtest: str
      The directory path and file of X_test.csv
  input_path_yttest: str
      The directory path and file of y_test.csv
  out_type: str
      Type of file to write locally (script supports either feather or csv)
  out_path: str
      The path of the directory to save output of the analysis
  out_path_csv: str
        The path of the directory to save output to for csv files
            
  Returns
  -------
  none
        
  Examples
  -------
  >>> python src/04_ml_analysis.py --input_path=data/02_preprocessed/ --out_path=analysis/figures/ --out_path_csv=analysis/
  """

  #////////////////////////////////////
  # DATA IMPORTING
  #////////////////////////////////////
  # Import data from the data folder based on the output of 02_preprocess_data.R
  X_train = pd.read_csv(input_path + "X_train.csv")
  y_train = pd.read_csv(input_path+ "y_train.csv")
  X_test = pd.read_csv(input_path+ "X_test.csv")
  y_test = pd.read_csv(input_path+ "y_test.csv")
  
  # test to make sure the imported data has the correct number of columns and rows
  assert X_train.shape[1] == X_test.shape[1], "Test and train X data doesn't match"
  assert y_train.shape[1] == y_test.shape[1], "Test and train y data doesn't match"
  assert X_train.shape[0] == y_train.shape[0], "Train X and y files are not the same length"
  assert X_test.shape[0] == y_test.shape[0], "Test X and y files are not the same length"
  
  #////////////////////////////////////
  # FEATURE SELECTION
  # Conduct a grid search to find x number of important features
  #////////////////////////////////////
  lr = LogisticRegression(solver='liblinear')
  rfe_cv = RFECV(estimator = lr, cv=10)
  rfe_cv.fit(X_train, y_train)
  rfe_cv.support_

  #////////////////////////////////////
  # MODEL BUILDING
  #////////////////////////////////////
  # set up models for comparison on regular data and selected features
  lr_normal = LogisticRegression(solver='liblinear')
  lr_select = LogisticRegression(solver='liblinear')
  
  # Subset selected features for the train and test data
  X_train_sel = X_train.loc[:, rfe_cv.support_]
  X_test_sel = X_test.loc[:, rfe_cv.support_]

  # test to make sure the columns are equal for train and test sets
  assert X_train_sel.shape[1] == X_test_sel.shape[1], "Not applying RFE to both train and test sets"
  
  # Fit to a Linear Regression model 
  lr_normal.fit(X_train, y_train)
  lr_select.fit(X_train_sel, y_train)
  
  # Create lookup for proper titles of features
  label_encode = {'original_labels': ["ground_land", "ground_att", "clinch_landed", "clinch_att", "distance_landed", "distance_att", "leg_landed", 
  "leg_att", 'body_landed', 'body_att', 'head_landed', 'head_att', 'rev', 'pass', 'sub_att', 'td_pct', 'td_landed', 
  'td_att', 'total_str_landed', 'total_str_att', 'sig_str_att', 'sig_str_pct', 'sig_str_landed'],
   'description':['Number of strikes landed while on the ground',
  'Number of strikes attempted while on the ground',
  'Number of strikes landed while in the clinch',
  'Number of strikes attempted while in the clinch',
  'Number of strikes landed from a distance',
  'Number of strikes attempted from a distance',
  'Number of strikes to opponents leg landed',
  'Number of strikes to opponents leg attempted',
  'Number of strikes to opponents body landed',
  'Number of strikes to opponents body attempted',
  'Number of strikes to opponents head landed',
  'Number of strikes to opponents head attempted',
  'Number of grappling reversals achieved',
  'Number of guard passes achieved',
  'Number of submission attempts on opponent',
  'Percent of takedowns successfully completed',
  'Number of takedowns successfully completed',
  'Number of takedowns attempted on opponent',
  'Total strikes landed on opponent',
  'Total strikes attempted on opponent',
  'Total significant strikes attempted on opponent',
  'Percent of significant strikes landed on opponent',
  'Total significant strikes landed on opponent']
  }
  
  label_df = pd.DataFrame(data=label_encode)
  
  # Make current selected features into a dataframe and merge with proper titles
  feature_df = pd.DataFrame({'features': X_train_sel.columns.values.tolist()})
  
  merged_label_df = feature_df.merge(label_df, left_on='features', right_on='original_labels')

  # Create a dataframe of the selected features and weights
  feature_names = merged_label_df.iloc[:,2]
  weights = np.round_(lr_select.coef_.flatten(), decimals = 4)
  inds = np.argsort(weights)
  weight_df = pd.DataFrame({'Features': feature_names, 'Weights': weights})
  weight_df = weight_df.reindex(weight_df.Weights.abs().sort_values(ascending=False).index)
  
  # Final results of the model on training and test data with and without the feature selection
  train_score = round(lr_normal.score(X_train, y_train), 4)
  test_score = round(lr_normal.score(X_test, y_test), 4)
  train_sel_score = round(lr_select.score(X_train_sel, y_train), 4)
  test_sel_score = round(lr_select.score(X_test_sel, y_test), 4)

  train_scores = [train_score, train_sel_score]
  feature_sel = ["All Features", "Selected Features"]
  test_scores = [test_score, test_sel_score]
  results = pd.DataFrame({'Features': feature_sel, 
                          'Training Accuracy' : train_scores, 
                          'Validation Accuracy' : test_scores})
  
  # Test the the proper size csv is printing out
  assert len(results) == 2, "Results is not the right length"
  assert results.shape[1] == 3, "Results is not the right width"
  
  # Test weight_df csv is correct length
  assert len(weight_df) == rfe_cv.n_features_, "Weights is not the right length"
  assert weight_df.shape[1] == 2, "Weights is not the right width"
  
  #////////////////////////////////////
  # PLOTTING THE NUMBER OF FEATURES
  # Create a plot comparing the training error to test error for a given number of features.
  #////////////////////////////////////
  max_dict = {'n_features_to_select':[], 'Training Error':[],'Validation Error':[]}
  
  for i in range(1, len(X_train.columns)):
    
      # Prepare data for model fitting
      rfe = RFE(estimator = LogisticRegression(solver='liblinear'), n_features_to_select = i)
      rfe.fit(X_train, y_train)
      train_error = 1-rfe.score(X_train, y_train)
      valid_error = 1-rfe.score(X_test, y_test)
      max_dict['n_features_to_select'].append(i)    
      max_dict['Training Error'].append(train_error) 
      max_dict['Validation Error'].append(valid_error)

  # plot using altair   
  n_features_to_select_df = pd.DataFrame(max_dict)
  n_features_to_select_df = n_features_to_select_df.melt(id_vars='n_features_to_select',
                                   value_name='error') 
  plot = alt.Chart(n_features_to_select_df).mark_line().encode(
      alt.X('n_features_to_select:Q', title='Number of Features'),
      alt.Y('error:Q', title='Error Rate'),
      alt.Color('variable:N', legend=None)
  ).properties(
      title='Error vs Number of Features')
  
  # Add labels to plot
  text = plot.mark_text(dy=-10, dx=-40).encode(
      x=alt.X('max(n_features_to_select):Q'),
      y=alt.Y('error:Q', aggregate={'argmax': 'n_features_to_select'}),
      text=alt.Text('variable:N')
  )
    
  plot = text + plot
  
  # Confusion Matrix on the X test values
  
  size=22
  params = {'legend.fontsize': 'large',
            'figure.figsize': (13,12),
            'axes.labelsize': size,
            'axes.titlesize': size,
            'xtick.labelsize': size,
            'ytick.labelsize': size,
            'axes.titlepad': 25}
  plt.rcParams.update(params)

  disp = plot_confusion_matrix(lr_select, X_test_sel, y_test,
                             display_labels=['Blue wins', 'Red Wins', 'Blue Wins', 'Red Wins'],
                             cmap=plt.cm.Blues, 
                             values_format = 'd')
  disp.ax_.set_title('Confusion Matrix for Predicted Winner')
  
  #////////////////////////////////////
  # PRINT FILES
  # Files Outputting from analysis
  #////////////////////////////////////
  plt.savefig(out_path + "confusion_matrix.png", scale_factor=20)
  plot.save(out_path + "error.png", scale_factor=20)
  weight_df.to_csv(out_path_csv + "weights.csv", index = False)
  results.to_csv(out_path_csv + "results.csv", index = False)

if __name__ == "__main__":
  main(opt["--input_path"], opt["--out_path"], opt["--out_path_csv"])
