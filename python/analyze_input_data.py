import pandas as pd
import matplotlib.pyplot as plt


def main():
    df = pd.read_csv('./hdl_design/hdl_design.sim/input_driver_test/behav/xsim/output.csv')
    df = df.dropna()